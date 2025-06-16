"""
Environment Manager
==================

Environment isolation and validation system providing:
- Environment-specific configuration validation
- Cross-environment access prevention
- Environment health monitoring and reporting
- Environment switching and validation tools

Part of Foundation Gaps Implementation - Phase 3
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class EnvironmentError(Exception):
    """Custom exception for environment management operations"""
    
    def __init__(self, message: str, environment: str = None, cause: Exception = None):
        super().__init__(message)
        self.environment = environment
        self.cause = cause


class EnvironmentType(Enum):
    """Environment types"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class EnvironmentConfig:
    """Environment configuration"""
    name: str
    type: EnvironmentType
    database_uri: str
    redis_uri: Optional[str] = None
    debug: bool = False
    log_level: str = "INFO"
    allowed_hosts: List[str] = None
    cors_origins: List[str] = None
    api_rate_limits: Dict[str, int] = None
    feature_flags: Dict[str, bool] = None
    security_settings: Dict[str, Any] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.allowed_hosts is None:
            self.allowed_hosts = []
        if self.cors_origins is None:
            self.cors_origins = []
        if self.api_rate_limits is None:
            self.api_rate_limits = {}
        if self.feature_flags is None:
            self.feature_flags = {}
        if self.security_settings is None:
            self.security_settings = {}
        if self.metadata is None:
            self.metadata = {}


class EnvironmentManager:
    """
    Environment isolation and validation manager.
    
    Features:
    - Environment-specific configuration validation
    - Cross-environment access prevention
    - Environment health monitoring
    - Configuration drift detection
    - Environment switching validation
    """
    
    def __init__(self, 
                 current_environment: str = None,
                 config_file: str = "configs/environments.json"):
        """
        Initialize environment manager.
        
        Args:
            current_environment: Current environment name
            config_file: Path to environment configuration file
        """
        self.current_environment = current_environment or os.getenv("ENV", "development")
        self.config_file = Path(config_file)
        
        # Load environment configurations
        self.environments: Dict[str, EnvironmentConfig] = self._load_environment_configs()
        
        # Validation rules
        self.validation_rules = self._load_validation_rules()
        
        # Environment isolation guards
        self.isolation_enabled = True
        self.cross_env_access_log: List[Dict[str, Any]] = []
        
        logger.info(f"EnvironmentManager initialized for environment: {self.current_environment}")
    
    def validate_environment_config(self) -> Dict[str, Any]:
        """
        Validate current environment configuration.
        
        Returns:
            Dict containing validation results
        """
        try:
            env_config = self.get_environment_config(self.current_environment)
            if not env_config:
                return {
                    "valid": False,
                    "errors": [f"Environment not found: {self.current_environment}"],
                    "warnings": [],
                    "checks": {}
                }
            
            validation_result = {
                "valid": True,
                "errors": [],
                "warnings": [],
                "checks": {}
            }
            
            # Run validation checks
            self._validate_database_config(env_config, validation_result)
            self._validate_security_config(env_config, validation_result)
            self._validate_network_config(env_config, validation_result)
            self._validate_feature_flags(env_config, validation_result)
            self._validate_logging_config(env_config, validation_result)
            
            # Check for configuration drift
            drift_issues = self._check_configuration_drift(env_config)
            if drift_issues:
                validation_result["warnings"].extend(drift_issues)
            
            # Overall validation status
            validation_result["valid"] = len(validation_result["errors"]) == 0
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating environment config: {str(e)}")
            return {
                "valid": False,
                "errors": [f"Validation failed: {str(e)}"],
                "warnings": [],
                "checks": {}
            }
    
    def get_environment_specific_config(self) -> Dict[str, Any]:
        """
        Get environment-specific configuration.
        
        Returns:
            Dict containing environment configuration
        """
        env_config = self.get_environment_config(self.current_environment)
        if not env_config:
            raise EnvironmentError(f"Environment not found: {self.current_environment}")
        
        return {
            "name": env_config.name,
            "type": env_config.type.value,
            "database_uri": env_config.database_uri,
            "redis_uri": env_config.redis_uri,
            "debug": env_config.debug,
            "log_level": env_config.log_level,
            "allowed_hosts": env_config.allowed_hosts,
            "cors_origins": env_config.cors_origins,
            "api_rate_limits": env_config.api_rate_limits,
            "feature_flags": env_config.feature_flags,
            "security_settings": env_config.security_settings,
            "metadata": env_config.metadata
        }
    
    def prevent_cross_environment_access(self, target_environment: str, 
                                       operation: str, resource: str) -> bool:
        """
        Prevent cross-environment access.
        
        Args:
            target_environment: Target environment name
            operation: Operation being attempted
            resource: Resource being accessed
            
        Returns:
            bool: True if access is allowed
        """
        if not self.isolation_enabled:
            return True
        
        # Allow access to same environment
        if target_environment == self.current_environment:
            return True
        
        # Check if cross-environment access is explicitly allowed
        current_config = self.get_environment_config(self.current_environment)
        if current_config and current_config.security_settings.get("allow_cross_env_access", False):
            return True
        
        # Log unauthorized access attempt
        access_attempt = {
            "timestamp": datetime.now().isoformat(),
            "current_environment": self.current_environment,
            "target_environment": target_environment,
            "operation": operation,
            "resource": resource,
            "blocked": True
        }
        self.cross_env_access_log.append(access_attempt)
        
        logger.warning(f"Blocked cross-environment access: {self.current_environment} -> {target_environment}")
        return False
    
    def get_environment_health(self) -> Dict[str, Any]:
        """
        Get environment health status.
        
        Returns:
            Dict containing health information
        """
        try:
            env_config = self.get_environment_config(self.current_environment)
            if not env_config:
                return {"healthy": False, "error": f"Environment not found: {self.current_environment}"}
            
            health_status = {
                "healthy": True,
                "environment": self.current_environment,
                "type": env_config.type.value,
                "checks": {},
                "warnings": [],
                "last_checked": datetime.now().isoformat()
            }
            
            # Database connectivity check
            health_status["checks"]["database"] = self._check_database_health(env_config)
            
            # Redis connectivity check (if configured)
            if env_config.redis_uri:
                health_status["checks"]["redis"] = self._check_redis_health(env_config)
            
            # Security configuration check
            health_status["checks"]["security"] = self._check_security_health(env_config)
            
            # Resource availability check
            health_status["checks"]["resources"] = self._check_resource_health()
            
            # Configuration validation
            validation_result = self.validate_environment_config()
            health_status["checks"]["configuration"] = {
                "valid": validation_result["valid"],
                "errors": validation_result["errors"],
                "warnings": validation_result["warnings"]
            }
            
            # Overall health status
            failed_checks = [name for name, check in health_status["checks"].items() 
                           if not check.get("healthy", True)]
            health_status["healthy"] = len(failed_checks) == 0
            
            if failed_checks:
                health_status["failed_checks"] = failed_checks
            
            return health_status
            
        except Exception as e:
            logger.error(f"Error checking environment health: {str(e)}")
            return {
                "healthy": False,
                "error": str(e),
                "environment": self.current_environment
            }
    
    def switch_environment(self, new_environment: str) -> bool:
        """
        Switch to a different environment.
        
        Args:
            new_environment: Target environment name
            
        Returns:
            bool: True if switch was successful
        """
        try:
            # Validate target environment exists
            target_config = self.get_environment_config(new_environment)
            if not target_config:
                raise EnvironmentError(f"Target environment not found: {new_environment}")
            
            # Validate target environment configuration
            old_env = self.current_environment
            self.current_environment = new_environment
            
            validation_result = self.validate_environment_config()
            if not validation_result["valid"]:
                # Revert on validation failure
                self.current_environment = old_env
                raise EnvironmentError(f"Target environment validation failed: {validation_result['errors']}")
            
            # Update environment variable
            os.environ["ENV"] = new_environment
            
            logger.info(f"Successfully switched environment: {old_env} -> {new_environment}")
            return True
            
        except Exception as e:
            logger.error(f"Error switching environment: {str(e)}")
            raise EnvironmentError(f"Failed to switch environment: {str(e)}", environment=new_environment, cause=e)
    
    def get_environment_config(self, environment_name: str) -> Optional[EnvironmentConfig]:
        """
        Get configuration for a specific environment.
        
        Args:
            environment_name: Environment name
            
        Returns:
            EnvironmentConfig or None if not found
        """
        return self.environments.get(environment_name)
    
    def list_environments(self) -> List[str]:
        """
        List all available environments.
        
        Returns:
            List of environment names
        """
        return list(self.environments.keys())
    
    def get_cross_env_access_log(self) -> List[Dict[str, Any]]:
        """
        Get cross-environment access log.
        
        Returns:
            List of access attempts
        """
        return self.cross_env_access_log.copy()
    
    # Private methods
    
    def _load_environment_configs(self) -> Dict[str, EnvironmentConfig]:
        """Load environment configurations from file"""
        try:
            if not self.config_file.exists():
                return self._create_default_environments()
            
            with open(self.config_file, 'r') as f:
                data = json.load(f)
            
            environments = {}
            for name, config_data in data.items():
                environments[name] = EnvironmentConfig(
                    name=name,
                    type=EnvironmentType(config_data["type"]),
                    database_uri=config_data["database_uri"],
                    redis_uri=config_data.get("redis_uri"),
                    debug=config_data.get("debug", False),
                    log_level=config_data.get("log_level", "INFO"),
                    allowed_hosts=config_data.get("allowed_hosts", []),
                    cors_origins=config_data.get("cors_origins", []),
                    api_rate_limits=config_data.get("api_rate_limits", {}),
                    feature_flags=config_data.get("feature_flags", {}),
                    security_settings=config_data.get("security_settings", {}),
                    metadata=config_data.get("metadata", {})
                )
            
            return environments
            
        except Exception as e:
            logger.error(f"Error loading environment configs: {str(e)}")
            return self._create_default_environments()
    
    def _create_default_environments(self) -> Dict[str, EnvironmentConfig]:
        """Create default environment configurations"""
        return {
            "development": EnvironmentConfig(
                name="development",
                type=EnvironmentType.DEVELOPMENT,
                database_uri="postgresql://user:password@localhost:5432/egypt_chatbot_dev",
                redis_uri="redis://localhost:6379/0",
                debug=True,
                log_level="DEBUG",
                allowed_hosts=["localhost", "127.0.0.1"],
                cors_origins=["http://localhost:3000", "http://localhost:5050"],
                feature_flags={"enable_debug_mode": True, "enable_test_data": True}
            ),
            "testing": EnvironmentConfig(
                name="testing",
                type=EnvironmentType.TESTING,
                database_uri="postgresql://user:password@localhost:5432/egypt_chatbot_test",
                redis_uri="redis://localhost:6379/1",
                debug=False,
                log_level="INFO",
                allowed_hosts=["localhost", "127.0.0.1"],
                cors_origins=["http://localhost:3000"],
                feature_flags={"enable_test_data": True}
            ),
            "production": EnvironmentConfig(
                name="production",
                type=EnvironmentType.PRODUCTION,
                database_uri="postgresql://user:password@prod-db:5432/egypt_chatbot",
                redis_uri="redis://prod-redis:6379/0",
                debug=False,
                log_level="WARNING",
                allowed_hosts=["yourdomain.com", "www.yourdomain.com"],
                cors_origins=["https://yourdomain.com"],
                security_settings={"require_https": True, "enable_csrf": True},
                feature_flags={}
            )
        }
    
    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load validation rules"""
        return {
            "database": {
                "required_schemes": ["postgresql", "sqlite"],
                "production_requirements": ["ssl_required", "backup_configured"]
            },
            "security": {
                "production_requirements": ["https_only", "csrf_enabled", "secure_cookies"],
                "forbidden_in_production": ["debug_mode", "test_data"]
            },
            "logging": {
                "production_min_level": "WARNING",
                "development_max_level": "DEBUG"
            }
        }
    
    def _validate_database_config(self, env_config: EnvironmentConfig, result: Dict[str, Any]):
        """Validate database configuration"""
        checks = {}
        
        # Check database URI format
        if not env_config.database_uri:
            result["errors"].append("Database URI is required")
            checks["database_uri"] = False
        else:
            # Basic URI validation
            if not any(scheme in env_config.database_uri for scheme in ["postgresql://", "sqlite://"]):
                result["errors"].append("Invalid database URI scheme")
                checks["database_uri"] = False
            else:
                checks["database_uri"] = True
        
        # Production-specific checks
        if env_config.type == EnvironmentType.PRODUCTION:
            if "localhost" in env_config.database_uri:
                result["warnings"].append("Production environment using localhost database")
            
            if "password" in env_config.database_uri:
                result["warnings"].append("Database password visible in URI (consider using secrets)")
        
        result["checks"]["database"] = checks
    
    def _validate_security_config(self, env_config: EnvironmentConfig, result: Dict[str, Any]):
        """Validate security configuration"""
        checks = {}
        
        # Production security requirements
        if env_config.type == EnvironmentType.PRODUCTION:
            security_settings = env_config.security_settings
            
            if not security_settings.get("require_https", False):
                result["errors"].append("HTTPS is required in production")
                checks["https_required"] = False
            else:
                checks["https_required"] = True
            
            if not security_settings.get("enable_csrf", False):
                result["warnings"].append("CSRF protection should be enabled in production")
                checks["csrf_enabled"] = False
            else:
                checks["csrf_enabled"] = True
            
            if env_config.debug:
                result["errors"].append("Debug mode must be disabled in production")
                checks["debug_disabled"] = False
            else:
                checks["debug_disabled"] = True
        
        # CORS validation
        if env_config.cors_origins:
            for origin in env_config.cors_origins:
                if origin == "*":
                    result["warnings"].append("Wildcard CORS origin is not recommended")
                    break
        
        result["checks"]["security"] = checks
    
    def _validate_network_config(self, env_config: EnvironmentConfig, result: Dict[str, Any]):
        """Validate network configuration"""
        checks = {}
        
        # Allowed hosts validation
        if not env_config.allowed_hosts:
            result["warnings"].append("No allowed hosts configured")
            checks["allowed_hosts"] = False
        else:
            checks["allowed_hosts"] = True
        
        # Production network checks
        if env_config.type == EnvironmentType.PRODUCTION:
            localhost_hosts = [host for host in env_config.allowed_hosts 
                             if host in ["localhost", "127.0.0.1"]]
            if localhost_hosts:
                result["warnings"].append("Localhost hosts in production allowed_hosts")
        
        result["checks"]["network"] = checks
    
    def _validate_feature_flags(self, env_config: EnvironmentConfig, result: Dict[str, Any]):
        """Validate feature flags"""
        checks = {}
        
        # Production feature flag checks
        if env_config.type == EnvironmentType.PRODUCTION:
            dangerous_flags = ["enable_debug_mode", "enable_test_data"]
            enabled_dangerous = [flag for flag in dangerous_flags 
                                if env_config.feature_flags.get(flag, False)]
            
            if enabled_dangerous:
                result["errors"].extend([f"Dangerous feature flag enabled in production: {flag}" 
                                       for flag in enabled_dangerous])
                checks["production_safe"] = False
            else:
                checks["production_safe"] = True
        
        result["checks"]["feature_flags"] = checks
    
    def _validate_logging_config(self, env_config: EnvironmentConfig, result: Dict[str, Any]):
        """Validate logging configuration"""
        checks = {}
        
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if env_config.log_level not in valid_levels:
            result["errors"].append(f"Invalid log level: {env_config.log_level}")
            checks["valid_level"] = False
        else:
            checks["valid_level"] = True
        
        # Environment-specific log level checks
        if env_config.type == EnvironmentType.PRODUCTION and env_config.log_level == "DEBUG":
            result["warnings"].append("DEBUG logging in production may impact performance")
        
        result["checks"]["logging"] = checks
    
    def _check_configuration_drift(self, env_config: EnvironmentConfig) -> List[str]:
        """Check for configuration drift"""
        drift_issues = []
        
        # Check environment variables vs config
        env_db_uri = os.getenv("POSTGRES_URI")
        if env_db_uri and env_db_uri != env_config.database_uri:
            drift_issues.append("Database URI mismatch between environment and config")
        
        env_debug = os.getenv("DEBUG", "").lower() in ["true", "1"]
        if env_debug != env_config.debug:
            drift_issues.append("Debug setting mismatch between environment and config")
        
        return drift_issues
    
    def _check_database_health(self, env_config: EnvironmentConfig) -> Dict[str, Any]:
        """Check database health"""
        # Placeholder - would implement actual database connectivity check
        return {
            "healthy": True,
            "response_time_ms": 50,
            "connection_pool_status": "healthy"
        }
    
    def _check_redis_health(self, env_config: EnvironmentConfig) -> Dict[str, Any]:
        """Check Redis health"""
        # Placeholder - would implement actual Redis connectivity check
        return {
            "healthy": True,
            "response_time_ms": 10,
            "memory_usage": "normal"
        }
    
    def _check_security_health(self, env_config: EnvironmentConfig) -> Dict[str, Any]:
        """Check security health"""
        return {
            "healthy": True,
            "https_enabled": env_config.security_settings.get("require_https", False),
            "csrf_enabled": env_config.security_settings.get("enable_csrf", False)
        }
    
    def _check_resource_health(self) -> Dict[str, Any]:
        """Check system resource health"""
        import psutil
        
        return {
            "healthy": True,
            "cpu_usage_percent": psutil.cpu_percent(),
            "memory_usage_percent": psutil.virtual_memory().percent,
            "disk_usage_percent": psutil.disk_usage('/').percent
        } 