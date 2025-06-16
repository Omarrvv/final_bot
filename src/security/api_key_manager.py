"""
API Key Manager
===============

API key management and rotation system providing:
- API key rotation capabilities
- Key validation and health monitoring
- Key expiration status tracking
- Automated rotation scheduling

Part of Foundation Gaps Implementation - Phase 3
"""

import os
import json
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .secrets_manager import SecretsManager, SecretsError

logger = logging.getLogger(__name__)


class APIKeyError(Exception):
    """Custom exception for API key management operations"""
    
    def __init__(self, message: str, service: str = None, cause: Exception = None):
        super().__init__(message)
        self.service = service
        self.cause = cause


class KeyStatus(Enum):
    """API key status"""
    ACTIVE = "active"
    EXPIRED = "expired"
    EXPIRING_SOON = "expiring_soon"
    INVALID = "invalid"
    ROTATION_NEEDED = "rotation_needed"


@dataclass
class APIKeyInfo:
    """Information about an API key"""
    service: str
    key_name: str
    created_at: datetime
    last_rotated: datetime
    expires_at: Optional[datetime] = None
    rotation_interval_days: int = 90
    auto_rotation_enabled: bool = False
    validation_endpoint: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "service": self.service,
            "key_name": self.key_name,
            "created_at": self.created_at.isoformat(),
            "last_rotated": self.last_rotated.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "rotation_interval_days": self.rotation_interval_days,
            "auto_rotation_enabled": self.auto_rotation_enabled,
            "validation_endpoint": self.validation_endpoint,
            "metadata": self.metadata or {}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'APIKeyInfo':
        """Create from dictionary"""
        return cls(
            service=data["service"],
            key_name=data["key_name"],
            created_at=datetime.fromisoformat(data["created_at"]),
            last_rotated=datetime.fromisoformat(data["last_rotated"]),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            rotation_interval_days=data.get("rotation_interval_days", 90),
            auto_rotation_enabled=data.get("auto_rotation_enabled", False),
            validation_endpoint=data.get("validation_endpoint"),
            metadata=data.get("metadata", {})
        )


class APIKeyManager:
    """
    API key management and rotation system.
    
    Features:
    - API key rotation with service-specific handlers
    - Key validation and health monitoring
    - Automatic rotation scheduling
    - Key expiration tracking and alerts
    - Integration with secrets manager
    """
    
    def __init__(self, 
                 secrets_manager: SecretsManager,
                 config_file: str = "data/security/api_keys.json"):
        """
        Initialize API key manager.
        
        Args:
            secrets_manager: SecretsManager instance for storing keys
            config_file: Path to API key configuration file
        """
        self.secrets_manager = secrets_manager
        self.config_file = Path(config_file)
        
        # Create directory if it doesn't exist
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load API key configurations
        self.api_keys: Dict[str, APIKeyInfo] = self._load_api_key_configs()
        
        # Service-specific rotation handlers
        self.rotation_handlers: Dict[str, Callable] = {}
        self.validation_handlers: Dict[str, Callable] = {}
        
        # Auto-rotation scheduler
        self.scheduler_running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        
        # Callbacks
        self.on_rotation_success: Optional[Callable] = None
        self.on_rotation_failure: Optional[Callable] = None
        self.on_validation_failure: Optional[Callable] = None
        
        logger.info("APIKeyManager initialized")
    
    def register_service(self, 
                        service: str,
                        key_name: str,
                        rotation_interval_days: int = 90,
                        auto_rotation_enabled: bool = False,
                        validation_endpoint: Optional[str] = None,
                        rotation_handler: Optional[Callable] = None,
                        validation_handler: Optional[Callable] = None) -> None:
        """
        Register a service for API key management.
        
        Args:
            service: Service name
            key_name: Environment variable/secret name for the API key
            rotation_interval_days: Days between rotations
            auto_rotation_enabled: Enable automatic rotation
            validation_endpoint: Endpoint for key validation
            rotation_handler: Custom rotation function
            validation_handler: Custom validation function
        """
        now = datetime.now()
        
        api_key_info = APIKeyInfo(
            service=service,
            key_name=key_name,
            created_at=now,
            last_rotated=now,
            rotation_interval_days=rotation_interval_days,
            auto_rotation_enabled=auto_rotation_enabled,
            validation_endpoint=validation_endpoint
        )
        
        self.api_keys[service] = api_key_info
        
        # Register handlers
        if rotation_handler:
            self.rotation_handlers[service] = rotation_handler
        if validation_handler:
            self.validation_handlers[service] = validation_handler
        
        self._save_api_key_configs()
        
        logger.info(f"Registered service for API key management: {service}")
    
    def rotate_api_key(self, service: str, new_key: Optional[str] = None) -> bool:
        """
        Rotate API key for a service.
        
        Args:
            service: Service name
            new_key: New API key (if not provided, uses rotation handler)
            
        Returns:
            bool: True if rotation was successful
        """
        try:
            api_key_info = self.api_keys.get(service)
            if not api_key_info:
                raise APIKeyError(f"Service not registered: {service}", service=service)
            
            # Get new key
            if new_key is None:
                if service in self.rotation_handlers:
                    new_key = self.rotation_handlers[service]()
                else:
                    raise APIKeyError(f"No rotation handler or new key provided for service: {service}", 
                                    service=service)
            
            # Store new key in secrets manager
            success = self.secrets_manager.set_secret(
                key=api_key_info.key_name,
                value=new_key,
                rotation_interval_days=api_key_info.rotation_interval_days,
                metadata={
                    "service": service,
                    "rotated_at": datetime.now().isoformat(),
                    "rotation_type": "manual" if new_key else "automatic"
                }
            )
            
            if success:
                # Update API key info
                api_key_info.last_rotated = datetime.now()
                if api_key_info.rotation_interval_days:
                    api_key_info.expires_at = api_key_info.last_rotated + timedelta(
                        days=api_key_info.rotation_interval_days
                    )
                
                self._save_api_key_configs()
                
                logger.info(f"API key rotated successfully for service: {service}")
                
                # Call success callback
                if self.on_rotation_success:
                    try:
                        self.on_rotation_success(service, api_key_info)
                    except Exception as e:
                        logger.error(f"Error in rotation success callback: {str(e)}")
                
                return True
            else:
                raise APIKeyError(f"Failed to store new API key for service: {service}", service=service)
                
        except Exception as e:
            logger.error(f"Error rotating API key for {service}: {str(e)}")
            
            # Call failure callback
            if self.on_rotation_failure:
                try:
                    self.on_rotation_failure(service, e)
                except Exception as cb_error:
                    logger.error(f"Error in rotation failure callback: {str(cb_error)}")
            
            raise APIKeyError(f"Failed to rotate API key: {str(e)}", service=service, cause=e)
    
    def validate_api_keys(self) -> Dict[str, bool]:
        """
        Validate all registered API keys.
        
        Returns:
            Dict mapping service names to validation status
        """
        validation_results = {}
        
        for service, api_key_info in self.api_keys.items():
            try:
                # Get current key
                current_key = self.secrets_manager.get_secret(api_key_info.key_name)
                if not current_key:
                    validation_results[service] = False
                    continue
                
                # Use custom validation handler if available
                if service in self.validation_handlers:
                    validation_results[service] = self.validation_handlers[service](current_key)
                elif api_key_info.validation_endpoint:
                    validation_results[service] = self._validate_key_with_endpoint(
                        current_key, api_key_info.validation_endpoint
                    )
                else:
                    # Basic validation - key exists and is not empty
                    validation_results[service] = len(current_key.strip()) > 0
                
                # Call validation failure callback if needed
                if not validation_results[service] and self.on_validation_failure:
                    try:
                        self.on_validation_failure(service, api_key_info)
                    except Exception as e:
                        logger.error(f"Error in validation failure callback: {str(e)}")
                
            except Exception as e:
                logger.error(f"Error validating API key for {service}: {str(e)}")
                validation_results[service] = False
        
        return validation_results
    
    def get_key_expiration_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get expiration status for all API keys.
        
        Returns:
            Dict mapping service names to expiration information
        """
        now = datetime.now()
        expiration_status = {}
        
        for service, api_key_info in self.api_keys.items():
            status_info = {
                "status": KeyStatus.ACTIVE.value,
                "expires_at": api_key_info.expires_at.isoformat() if api_key_info.expires_at else None,
                "days_until_expiration": None,
                "last_rotated": api_key_info.last_rotated.isoformat(),
                "rotation_interval_days": api_key_info.rotation_interval_days
            }
            
            if api_key_info.expires_at:
                days_until_expiration = (api_key_info.expires_at - now).days
                status_info["days_until_expiration"] = days_until_expiration
                
                if api_key_info.expires_at <= now:
                    status_info["status"] = KeyStatus.EXPIRED.value
                elif days_until_expiration <= 7:
                    status_info["status"] = KeyStatus.EXPIRING_SOON.value
                elif days_until_expiration <= 30:
                    status_info["status"] = KeyStatus.ROTATION_NEEDED.value
            
            expiration_status[service] = status_info
        
        return expiration_status
    
    def schedule_key_rotation(self, service: str, interval_days: int) -> None:
        """
        Schedule automatic key rotation for a service.
        
        Args:
            service: Service name
            interval_days: Rotation interval in days
        """
        api_key_info = self.api_keys.get(service)
        if not api_key_info:
            raise APIKeyError(f"Service not registered: {service}", service=service)
        
        api_key_info.rotation_interval_days = interval_days
        api_key_info.auto_rotation_enabled = True
        api_key_info.expires_at = api_key_info.last_rotated + timedelta(days=interval_days)
        
        self._save_api_key_configs()
        
        logger.info(f"Scheduled automatic rotation for {service} every {interval_days} days")
    
    def start_auto_rotation_scheduler(self) -> None:
        """Start the automatic rotation scheduler."""
        if self.scheduler_running:
            logger.warning("Auto-rotation scheduler is already running")
            return
        
        self.scheduler_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("Auto-rotation scheduler started")
    
    def stop_auto_rotation_scheduler(self) -> None:
        """Stop the automatic rotation scheduler."""
        if not self.scheduler_running:
            logger.warning("Auto-rotation scheduler is not running")
            return
        
        self.scheduler_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=10)
        
        logger.info("Auto-rotation scheduler stopped")
    
    def get_api_key_stats(self) -> Dict[str, Any]:
        """
        Get API key management statistics.
        
        Returns:
            Dict containing statistics
        """
        total_keys = len(self.api_keys)
        auto_rotation_enabled = sum(1 for info in self.api_keys.values() if info.auto_rotation_enabled)
        
        validation_results = self.validate_api_keys()
        valid_keys = sum(1 for valid in validation_results.values() if valid)
        
        expiration_status = self.get_key_expiration_status()
        expired_keys = sum(1 for status in expiration_status.values() 
                          if status["status"] == KeyStatus.EXPIRED.value)
        expiring_soon = sum(1 for status in expiration_status.values() 
                           if status["status"] == KeyStatus.EXPIRING_SOON.value)
        
        return {
            "total_keys": total_keys,
            "valid_keys": valid_keys,
            "invalid_keys": total_keys - valid_keys,
            "expired_keys": expired_keys,
            "expiring_soon": expiring_soon,
            "auto_rotation_enabled": auto_rotation_enabled,
            "scheduler_running": self.scheduler_running,
            "validation_rate": valid_keys / total_keys if total_keys > 0 else 1.0
        }
    
    # Callback registration methods
    
    def set_rotation_success_callback(self, callback: Callable[[str, APIKeyInfo], None]) -> None:
        """Set callback for successful rotations."""
        self.on_rotation_success = callback
    
    def set_rotation_failure_callback(self, callback: Callable[[str, Exception], None]) -> None:
        """Set callback for failed rotations."""
        self.on_rotation_failure = callback
    
    def set_validation_failure_callback(self, callback: Callable[[str, APIKeyInfo], None]) -> None:
        """Set callback for validation failures."""
        self.on_validation_failure = callback
    
    # Private methods
    
    def _load_api_key_configs(self) -> Dict[str, APIKeyInfo]:
        """Load API key configurations from file"""
        try:
            if not self.config_file.exists():
                return {}
            
            with open(self.config_file, 'r') as f:
                data = json.load(f)
            
            api_keys = {}
            for service, config_data in data.items():
                api_keys[service] = APIKeyInfo.from_dict(config_data)
            
            return api_keys
            
        except Exception as e:
            logger.error(f"Error loading API key configs: {str(e)}")
            return {}
    
    def _save_api_key_configs(self):
        """Save API key configurations to file"""
        try:
            data = {}
            for service, info in self.api_keys.items():
                data[service] = info.to_dict()
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Set restrictive permissions
            os.chmod(self.config_file, 0o600)
            
        except Exception as e:
            logger.error(f"Error saving API key configs: {str(e)}")
    
    def _validate_key_with_endpoint(self, api_key: str, endpoint: str) -> bool:
        """Validate API key using HTTP endpoint"""
        try:
            import requests
            
            headers = {"Authorization": f"Bearer {api_key}"}
            response = requests.get(endpoint, headers=headers, timeout=10)
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error validating key with endpoint {endpoint}: {str(e)}")
            return False
    
    def _scheduler_loop(self) -> None:
        """Main scheduler loop for automatic rotations"""
        logger.info("Auto-rotation scheduler loop started")
        
        while self.scheduler_running:
            try:
                now = datetime.now()
                
                # Check each service for rotation needs
                for service, api_key_info in self.api_keys.items():
                    if not api_key_info.auto_rotation_enabled:
                        continue
                    
                    # Check if rotation is needed
                    if api_key_info.expires_at and api_key_info.expires_at <= now:
                        logger.info(f"Auto-rotating expired API key for service: {service}")
                        try:
                            self.rotate_api_key(service)
                        except Exception as e:
                            logger.error(f"Auto-rotation failed for {service}: {str(e)}")
                    
                    # Check if rotation is needed soon (within 7 days)
                    elif (api_key_info.expires_at and 
                          api_key_info.expires_at <= now + timedelta(days=7)):
                        logger.info(f"API key expiring soon for service: {service}")
                
                # Sleep for 1 hour before next check
                time.sleep(3600)
                
            except Exception as e:
                logger.error(f"Error in auto-rotation scheduler loop: {str(e)}")
                time.sleep(3600)  # Continue after error
        
        logger.info("Auto-rotation scheduler loop stopped")


# Service-specific rotation handlers

def anthropic_rotation_handler() -> str:
    """Generate new Anthropic API key (placeholder)"""
    # In practice, this would integrate with Anthropic's API key management
    logger.warning("Anthropic API key rotation not implemented - manual rotation required")
    raise APIKeyError("Anthropic API key rotation requires manual intervention")


def weather_api_rotation_handler() -> str:
    """Generate new weather API key (placeholder)"""
    # In practice, this would integrate with the weather service's API
    logger.warning("Weather API key rotation not implemented - manual rotation required")
    raise APIKeyError("Weather API key rotation requires manual intervention")


# Service-specific validation handlers

def anthropic_validation_handler(api_key: str) -> bool:
    """Validate Anthropic API key"""
    try:
        # Placeholder - would make actual API call to validate
        return len(api_key) > 0 and api_key.startswith("sk-")
    except Exception:
        return False


def weather_api_validation_handler(api_key: str) -> bool:
    """Validate weather API key"""
    try:
        # Placeholder - would make actual API call to validate
        return len(api_key) > 0
    except Exception:
        return False 