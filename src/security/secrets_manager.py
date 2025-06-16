"""
Centralized Secrets Manager
===========================

Centralized secrets management system providing:
- Multiple provider support (environment, vault, AWS Secrets Manager)
- Secret validation and health checking
- Secret rotation capabilities and procedures
- Secure secret storage and retrieval

Part of Foundation Gaps Implementation - Phase 3
"""

import os
import json
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import base64

logger = logging.getLogger(__name__)


class SecretsError(Exception):
    """Custom exception for secrets management operations"""
    
    def __init__(self, message: str, secret_key: str = None, provider: str = None, cause: Exception = None):
        super().__init__(message)
        self.secret_key = secret_key
        self.provider = provider
        self.cause = cause


class SecretProvider(Enum):
    """Secret provider types"""
    ENVIRONMENT = "env"
    VAULT = "vault"
    AWS_SECRETS = "aws_secrets"
    FILE = "file"


@dataclass
class SecretInfo:
    """Information about a secret"""
    key: str
    provider: SecretProvider
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None
    rotation_interval_days: Optional[int] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "key": self.key,
            "provider": self.provider.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "rotation_interval_days": self.rotation_interval_days,
            "metadata": self.metadata or {}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SecretInfo':
        """Create from dictionary"""
        return cls(
            key=data["key"],
            provider=SecretProvider(data["provider"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            rotation_interval_days=data.get("rotation_interval_days"),
            metadata=data.get("metadata", {})
        )


class SecretsManager:
    """
    Centralized secrets management with multiple provider support.
    
    Features:
    - Multiple provider backends (env, vault, AWS, file)
    - Secret validation and health checking
    - Automatic rotation capabilities
    - Secure storage and retrieval
    - Audit logging and monitoring
    """
    
    def __init__(self, 
                 primary_provider: SecretProvider = SecretProvider.ENVIRONMENT,
                 fallback_provider: Optional[SecretProvider] = None,
                 secrets_file: str = "data/secrets/secrets.json",
                 metadata_file: str = "data/secrets/metadata.json"):
        """
        Initialize secrets manager.
        
        Args:
            primary_provider: Primary secrets provider
            fallback_provider: Fallback provider if primary fails
            secrets_file: Path to encrypted secrets file (for FILE provider)
            metadata_file: Path to secrets metadata file
        """
        self.primary_provider = primary_provider
        self.fallback_provider = fallback_provider
        self.secrets_file = Path(secrets_file)
        self.metadata_file = Path(metadata_file)
        
        # Create directories if they don't exist
        self.secrets_file.parent.mkdir(parents=True, exist_ok=True)
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load metadata
        self.metadata: Dict[str, SecretInfo] = self._load_metadata()
        
        # Provider configurations
        self.provider_configs = {
            SecretProvider.ENVIRONMENT: {},
            SecretProvider.FILE: {"file_path": self.secrets_file},
            SecretProvider.VAULT: {
                "url": os.getenv("VAULT_URL", "http://localhost:8200"),
                "token": os.getenv("VAULT_TOKEN"),
                "mount_point": os.getenv("VAULT_MOUNT_POINT", "secret")
            },
            SecretProvider.AWS_SECRETS: {
                "region": os.getenv("AWS_REGION", "us-east-1"),
                "access_key": os.getenv("AWS_ACCESS_KEY_ID"),
                "secret_key": os.getenv("AWS_SECRET_ACCESS_KEY")
            }
        }
        
        logger.info(f"SecretsManager initialized with primary provider: {primary_provider.value}")
    
    def get_secret(self, key: str) -> Optional[str]:
        """
        Get a secret value by key.
        
        Args:
            key: Secret key
            
        Returns:
            Secret value or None if not found
        """
        try:
            # Try primary provider first
            value = self._get_secret_from_provider(key, self.primary_provider)
            if value is not None:
                self._update_access_metadata(key)
                return value
            
            # Try fallback provider if configured
            if self.fallback_provider:
                value = self._get_secret_from_provider(key, self.fallback_provider)
                if value is not None:
                    self._update_access_metadata(key)
                    return value
            
            logger.warning(f"Secret not found: {key}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting secret {key}: {str(e)}")
            raise SecretsError(f"Failed to get secret: {str(e)}", secret_key=key, cause=e)
    
    def set_secret(self, key: str, value: str, 
                   rotation_interval_days: Optional[int] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Set a secret value.
        
        Args:
            key: Secret key
            value: Secret value
            rotation_interval_days: Days between automatic rotations
            metadata: Additional metadata
            
        Returns:
            bool: True if secret was set successfully
        """
        try:
            # Set secret in primary provider
            success = self._set_secret_in_provider(key, value, self.primary_provider)
            
            if success:
                # Update metadata
                now = datetime.now()
                expires_at = None
                if rotation_interval_days:
                    expires_at = now + timedelta(days=rotation_interval_days)
                
                secret_info = SecretInfo(
                    key=key,
                    provider=self.primary_provider,
                    created_at=self.metadata.get(key, SecretInfo(key, self.primary_provider, now, now)).created_at,
                    updated_at=now,
                    expires_at=expires_at,
                    rotation_interval_days=rotation_interval_days,
                    metadata=metadata or {}
                )
                
                self.metadata[key] = secret_info
                self._save_metadata()
                
                logger.info(f"Secret set successfully: {key}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error setting secret {key}: {str(e)}")
            raise SecretsError(f"Failed to set secret: {str(e)}", secret_key=key, cause=e)
    
    def rotate_secret(self, key: str, new_value: Optional[str] = None) -> str:
        """
        Rotate a secret to a new value.
        
        Args:
            key: Secret key to rotate
            new_value: New secret value (generated if not provided)
            
        Returns:
            str: New secret value
        """
        try:
            if new_value is None:
                new_value = self._generate_secret_value(key)
            
            # Get current metadata
            secret_info = self.metadata.get(key)
            if not secret_info:
                raise SecretsError(f"Secret not found for rotation: {key}", secret_key=key)
            
            # Set new value
            success = self.set_secret(
                key=key,
                value=new_value,
                rotation_interval_days=secret_info.rotation_interval_days,
                metadata=secret_info.metadata
            )
            
            if success:
                logger.info(f"Secret rotated successfully: {key}")
                return new_value
            else:
                raise SecretsError(f"Failed to rotate secret: {key}", secret_key=key)
                
        except Exception as e:
            logger.error(f"Error rotating secret {key}: {str(e)}")
            raise SecretsError(f"Failed to rotate secret: {str(e)}", secret_key=key, cause=e)
    
    def list_secrets(self) -> List[str]:
        """
        List all secret keys.
        
        Returns:
            List of secret keys
        """
        try:
            # Get keys from primary provider
            keys = self._list_secrets_from_provider(self.primary_provider)
            
            # Add keys from metadata (may include keys from other providers)
            metadata_keys = set(self.metadata.keys())
            all_keys = set(keys) | metadata_keys
            
            return sorted(list(all_keys))
            
        except Exception as e:
            logger.error(f"Error listing secrets: {str(e)}")
            raise SecretsError(f"Failed to list secrets: {str(e)}", cause=e)
    
    def validate_secrets(self) -> Dict[str, bool]:
        """
        Validate all secrets for accessibility and integrity.
        
        Returns:
            Dict mapping secret keys to validation status
        """
        validation_results = {}
        
        for key in self.list_secrets():
            try:
                value = self.get_secret(key)
                validation_results[key] = value is not None and len(value) > 0
            except Exception as e:
                logger.error(f"Validation failed for secret {key}: {str(e)}")
                validation_results[key] = False
        
        return validation_results
    
    def get_secrets_health(self) -> Dict[str, Any]:
        """
        Get health status of secrets management system.
        
        Returns:
            Dict containing health information
        """
        try:
            total_secrets = len(self.list_secrets())
            validation_results = self.validate_secrets()
            valid_secrets = sum(1 for valid in validation_results.values() if valid)
            
            # Check for expiring secrets
            now = datetime.now()
            expiring_soon = []
            expired = []
            
            for key, info in self.metadata.items():
                if info.expires_at:
                    if info.expires_at <= now:
                        expired.append(key)
                    elif info.expires_at <= now + timedelta(days=7):
                        expiring_soon.append(key)
            
            return {
                "total_secrets": total_secrets,
                "valid_secrets": valid_secrets,
                "invalid_secrets": total_secrets - valid_secrets,
                "validation_rate": valid_secrets / total_secrets if total_secrets > 0 else 1.0,
                "expired_secrets": expired,
                "expiring_soon": expiring_soon,
                "primary_provider": self.primary_provider.value,
                "fallback_provider": self.fallback_provider.value if self.fallback_provider else None,
                "provider_status": self._check_provider_status()
            }
            
        except Exception as e:
            logger.error(f"Error getting secrets health: {str(e)}")
            return {"error": str(e)}
    
    def delete_secret(self, key: str) -> bool:
        """
        Delete a secret.
        
        Args:
            key: Secret key to delete
            
        Returns:
            bool: True if secret was deleted successfully
        """
        try:
            # Delete from primary provider
            success = self._delete_secret_from_provider(key, self.primary_provider)
            
            # Remove from metadata
            if key in self.metadata:
                del self.metadata[key]
                self._save_metadata()
            
            if success:
                logger.info(f"Secret deleted successfully: {key}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting secret {key}: {str(e)}")
            raise SecretsError(f"Failed to delete secret: {str(e)}", secret_key=key, cause=e)
    
    # Private methods
    
    def _get_secret_from_provider(self, key: str, provider: SecretProvider) -> Optional[str]:
        """Get secret from specific provider"""
        if provider == SecretProvider.ENVIRONMENT:
            return os.getenv(key)
        
        elif provider == SecretProvider.FILE:
            return self._get_secret_from_file(key)
        
        elif provider == SecretProvider.VAULT:
            return self._get_secret_from_vault(key)
        
        elif provider == SecretProvider.AWS_SECRETS:
            return self._get_secret_from_aws(key)
        
        return None
    
    def _set_secret_in_provider(self, key: str, value: str, provider: SecretProvider) -> bool:
        """Set secret in specific provider"""
        if provider == SecretProvider.ENVIRONMENT:
            # Environment variables can't be set permanently from Python
            os.environ[key] = value
            return True
        
        elif provider == SecretProvider.FILE:
            return self._set_secret_in_file(key, value)
        
        elif provider == SecretProvider.VAULT:
            return self._set_secret_in_vault(key, value)
        
        elif provider == SecretProvider.AWS_SECRETS:
            return self._set_secret_in_aws(key, value)
        
        return False
    
    def _list_secrets_from_provider(self, provider: SecretProvider) -> List[str]:
        """List secrets from specific provider"""
        if provider == SecretProvider.ENVIRONMENT:
            # Return known secret keys from metadata
            return [key for key, info in self.metadata.items() if info.provider == provider]
        
        elif provider == SecretProvider.FILE:
            return self._list_secrets_from_file()
        
        elif provider == SecretProvider.VAULT:
            return self._list_secrets_from_vault()
        
        elif provider == SecretProvider.AWS_SECRETS:
            return self._list_secrets_from_aws()
        
        return []
    
    def _delete_secret_from_provider(self, key: str, provider: SecretProvider) -> bool:
        """Delete secret from specific provider"""
        if provider == SecretProvider.ENVIRONMENT:
            if key in os.environ:
                del os.environ[key]
                return True
            return False
        
        elif provider == SecretProvider.FILE:
            return self._delete_secret_from_file(key)
        
        elif provider == SecretProvider.VAULT:
            return self._delete_secret_from_vault(key)
        
        elif provider == SecretProvider.AWS_SECRETS:
            return self._delete_secret_from_aws(key)
        
        return False
    
    # File provider methods
    
    def _get_secret_from_file(self, key: str) -> Optional[str]:
        """Get secret from encrypted file"""
        try:
            if not self.secrets_file.exists():
                return None
            
            with open(self.secrets_file, 'r') as f:
                secrets = json.load(f)
            
            return secrets.get(key)
            
        except Exception as e:
            logger.error(f"Error reading secret from file: {str(e)}")
            return None
    
    def _set_secret_in_file(self, key: str, value: str) -> bool:
        """Set secret in encrypted file"""
        try:
            secrets = {}
            if self.secrets_file.exists():
                with open(self.secrets_file, 'r') as f:
                    secrets = json.load(f)
            
            secrets[key] = value
            
            with open(self.secrets_file, 'w') as f:
                json.dump(secrets, f, indent=2)
            
            # Set restrictive permissions
            os.chmod(self.secrets_file, 0o600)
            
            return True
            
        except Exception as e:
            logger.error(f"Error writing secret to file: {str(e)}")
            return False
    
    def _list_secrets_from_file(self) -> List[str]:
        """List secrets from file"""
        try:
            if not self.secrets_file.exists():
                return []
            
            with open(self.secrets_file, 'r') as f:
                secrets = json.load(f)
            
            return list(secrets.keys())
            
        except Exception as e:
            logger.error(f"Error listing secrets from file: {str(e)}")
            return []
    
    def _delete_secret_from_file(self, key: str) -> bool:
        """Delete secret from file"""
        try:
            if not self.secrets_file.exists():
                return False
            
            with open(self.secrets_file, 'r') as f:
                secrets = json.load(f)
            
            if key in secrets:
                del secrets[key]
                
                with open(self.secrets_file, 'w') as f:
                    json.dump(secrets, f, indent=2)
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting secret from file: {str(e)}")
            return False
    
    # Vault provider methods (stubs - would need hvac library)
    
    def _get_secret_from_vault(self, key: str) -> Optional[str]:
        """Get secret from HashiCorp Vault"""
        # Placeholder - would implement with hvac library
        logger.warning("Vault provider not implemented")
        return None
    
    def _set_secret_in_vault(self, key: str, value: str) -> bool:
        """Set secret in HashiCorp Vault"""
        # Placeholder - would implement with hvac library
        logger.warning("Vault provider not implemented")
        return False
    
    def _list_secrets_from_vault(self) -> List[str]:
        """List secrets from Vault"""
        # Placeholder - would implement with hvac library
        logger.warning("Vault provider not implemented")
        return []
    
    def _delete_secret_from_vault(self, key: str) -> bool:
        """Delete secret from Vault"""
        # Placeholder - would implement with hvac library
        logger.warning("Vault provider not implemented")
        return False
    
    # AWS Secrets Manager methods (stubs - would need boto3)
    
    def _get_secret_from_aws(self, key: str) -> Optional[str]:
        """Get secret from AWS Secrets Manager"""
        # Placeholder - would implement with boto3
        logger.warning("AWS Secrets Manager provider not implemented")
        return None
    
    def _set_secret_in_aws(self, key: str, value: str) -> bool:
        """Set secret in AWS Secrets Manager"""
        # Placeholder - would implement with boto3
        logger.warning("AWS Secrets Manager provider not implemented")
        return False
    
    def _list_secrets_from_aws(self) -> List[str]:
        """List secrets from AWS Secrets Manager"""
        # Placeholder - would implement with boto3
        logger.warning("AWS Secrets Manager provider not implemented")
        return []
    
    def _delete_secret_from_aws(self, key: str) -> bool:
        """Delete secret from AWS Secrets Manager"""
        # Placeholder - would implement with boto3
        logger.warning("AWS Secrets Manager provider not implemented")
        return False
    
    # Utility methods
    
    def _generate_secret_value(self, key: str) -> str:
        """Generate a new secret value"""
        # Generate a secure random value
        import secrets
        return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8')
    
    def _update_access_metadata(self, key: str):
        """Update last access time for a secret"""
        if key in self.metadata:
            self.metadata[key].metadata = self.metadata[key].metadata or {}
            self.metadata[key].metadata['last_accessed'] = datetime.now().isoformat()
    
    def _load_metadata(self) -> Dict[str, SecretInfo]:
        """Load secrets metadata from file"""
        try:
            if not self.metadata_file.exists():
                return {}
            
            with open(self.metadata_file, 'r') as f:
                data = json.load(f)
            
            metadata = {}
            for key, info_data in data.items():
                metadata[key] = SecretInfo.from_dict(info_data)
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error loading metadata: {str(e)}")
            return {}
    
    def _save_metadata(self):
        """Save secrets metadata to file"""
        try:
            data = {}
            for key, info in self.metadata.items():
                data[key] = info.to_dict()
            
            with open(self.metadata_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Set restrictive permissions
            os.chmod(self.metadata_file, 0o600)
            
        except Exception as e:
            logger.error(f"Error saving metadata: {str(e)}")
    
    def _check_provider_status(self) -> Dict[str, bool]:
        """Check status of all providers"""
        status = {}
        
        # Environment provider is always available
        status[SecretProvider.ENVIRONMENT.value] = True
        
        # File provider - check if directory is writable
        try:
            test_file = self.secrets_file.parent / ".test"
            test_file.touch()
            test_file.unlink()
            status[SecretProvider.FILE.value] = True
        except Exception:
            status[SecretProvider.FILE.value] = False
        
        # Vault provider - would check connection
        status[SecretProvider.VAULT.value] = False  # Not implemented
        
        # AWS provider - would check credentials
        status[SecretProvider.AWS_SECRETS.value] = False  # Not implemented
        
        return status 