"""
Unified Configuration System for Egypt Tourism Chatbot

This module consolidates all configuration systems into a single, robust solution:
- Legacy config.py (manual environment parsing)
- Modern utils/settings.py (Pydantic-based)
- FastAPI-specific config/fastapi_config.py
- YAML configurations
- Environment files

Features:
- Type safety with Pydantic BaseSettings
- Comprehensive field validation
- SecretStr for sensitive data
- Feature flags system
- Backward compatibility with property aliases
- Multiple environment file support
- Clear deprecation warnings for migration

Author: Configuration Consolidation Team
Date: June 2025
"""

import os
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from urllib.parse import quote_plus

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Set up logging
logger = logging.getLogger(__name__)


class FeatureFlags(BaseSettings):
    """Feature flags for enabling/disabling application features."""
    
    # Core feature flags
    use_redis: bool = Field(
        default=False, 
        description="Enable Redis for session storage and caching",
        env="USE_REDIS"
    )
    use_postgres: bool = Field(
        default=True, 
        description="Use PostgreSQL database instead of SQLite",
        env="USE_POSTGRES"
    )
    use_new_kb: bool = Field(
        default=False, 
        description="Enable new knowledge base implementation",
        env="USE_NEW_KB"
    )
    use_vector_search: bool = Field(
        default=True, 
        description="Enable vector-based semantic search",
        env="USE_VECTOR_SEARCH"
    )
    enable_analytics: bool = Field(
        default=True, 
        description="Enable analytics and logging",
        env="ENABLE_ANALYTICS"
    )
    enable_caching: bool = Field(
        default=True, 
        description="Enable response caching",
        env="ENABLE_CACHING"
    )
    enable_rate_limiting: bool = Field(
        default=True, 
        description="Enable API rate limiting",
        env="ENABLE_RATE_LIMITING"
    )
    
    # FastAPI specific flags
    use_new_api: bool = Field(
        default=False, 
        description="Enable new API features",
        env="USE_NEW_API"
    )
    enable_redis_sessions: bool = Field(
        default=False, 
        description="Enable Redis-based session management",
        env="ENABLE_REDIS_SESSIONS"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    def log_status(self):
        """Log the current feature flag status."""
        logger.info("Feature Flags Status:")
        for field_name, field_value in self.model_dump().items():
            status = "ENABLED" if field_value else "DISABLED"
            logger.info(f"  {field_name}: {status}")


class UnifiedSettings(BaseSettings):
    """
    Unified configuration system consolidating all previous config approaches.
    
    This class replaces:
    - src/config.py (Legacy)
    - src/utils/settings.py (Modern)
    - src/config/fastapi_config.py (FastAPI-specific)
    """

    # ============================================================================
    # FEATURE FLAGS
    # ============================================================================
    feature_flags: FeatureFlags = Field(default_factory=FeatureFlags)

    # ============================================================================
    # ENVIRONMENT & DEBUG
    # ============================================================================
    env: str = Field(
        default="development", 
        description="Application environment",
        env="ENV"
    )
    debug: bool = Field(
        default=False, 
        description="Enable debug mode",
        env="DEBUG"
    )
    log_level: str = Field(
        default="INFO", 
        description="Logging level",
        env="LOG_LEVEL"
    )
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log message format",
        env="LOG_FORMAT"
    )

    # ============================================================================
    # API SERVER CONFIGURATION
    # ============================================================================
    api_host: str = Field(
        default="0.0.0.0", 
        description="API server host",
        env="API_HOST"
    )
    api_port: int = Field(
        default=5050, 
        description="API server port",
        env="API_PORT"
    )
    reload: bool = Field(
        default=True, 
        description="Enable auto-reload in development",
        env="API_RELOAD"
    )
    workers: int = Field(
        default=1, 
        description="Number of API worker processes",
        env="API_WORKERS"
    )

    # ============================================================================
    # DATABASE CONFIGURATION
    # ============================================================================
    database_uri: str = Field(
        default="postgresql://user:password@localhost:5432/egypt_chatbot",
        description="PostgreSQL database connection URI",
        env="POSTGRES_URI"
    )
    postgres_host: str = Field(default="localhost", env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")
    postgres_db: str = Field(default="egypt_chatbot", env="POSTGRES_DB")
    postgres_user: str = Field(default="user", env="POSTGRES_USER")
    postgres_password: SecretStr = Field(default=SecretStr("password"), env="POSTGRES_PASSWORD")
    
    # Vector database
    vector_db_uri: str = Field(
        default="./data/vector_db",
        description="Vector database storage path",
        env="VECTOR_DB_URI"
    )

    # ============================================================================
    # REDIS CONFIGURATION
    # ============================================================================
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Complete Redis connection URL",
        env="REDIS_URL"
    )
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")

    # ============================================================================
    # SESSION CONFIGURATION
    # ============================================================================
    session_storage_uri: str = Field(
        default="file:///./data/sessions",
        description="URI for session storage (file:// or redis://)",
        env="SESSION_STORAGE_URI"
    )
    session_ttl: int = Field(
        default=86400, 
        description="Session time-to-live in seconds (24 hours)",
        env="SESSION_TTL_SECONDS"
    )
    session_cookie_name: str = Field(
        default="egypt_tourism_session", 
        description="Name of the session cookie",
        env="SESSION_COOKIE_NAME"
    )
    session_cookie_secure: bool = Field(
        default=False, 
        description="Whether to set the secure flag on session cookies",
        env="COOKIE_SECURE"
    )
    session_expiry: int = Field(
        default=3600 * 24, 
        description="Session expiry in seconds",
        env="SESSION_EXPIRY"
    )

    # ============================================================================
    # SECURITY CONFIGURATION
    # ============================================================================
    secret_key: str = Field(
        default="egypt-tourism-chatbot-secret-key-change-in-production",
        description="Application secret key",
        env="SECRET_KEY"
    )
    jwt_secret: str = Field(
        default="generate_a_strong_secret_key_here",
        description="JWT signing secret",
        env="JWT_SECRET"
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm",
        env="JWT_ALGORITHM"
    )
    jwt_expiration: int = Field(
        default=3600, 
        description="JWT token expiration in seconds",
        env="JWT_EXPIRATION"
    )

    # ============================================================================
    # CORS CONFIGURATION
    # ============================================================================
    allowed_origins: str = Field(
        default="http://localhost:3000,http://localhost:5050",
        description="Comma-separated list of allowed CORS origins",
        env="ALLOWED_ORIGINS"
    )
    _allowed_origins_list: List[str] = []

    @field_validator("allowed_origins")
    def parse_allowed_origins(cls, v: str) -> str:
        """Store raw string value and return it."""
        return v

    @property
    def cors_origins(self) -> List[str]:
        """Get allowed origins as a list."""
        if not self._allowed_origins_list:
            self._allowed_origins_list = [
                origin.strip()
                for origin in self.allowed_origins.split(",")
                if origin.strip()
            ]
        return self._allowed_origins_list

    # ============================================================================
    # API KEYS (SECURE)
    # ============================================================================
    anthropic_api_key: SecretStr = Field(
        default=SecretStr(""),
        description="Anthropic API key for Claude",
        env="ANTHROPIC_API_KEY"
    )
    weather_api_key: SecretStr = Field(
        default=SecretStr(""),
        description="Weather API key",
        env="WEATHER_API_KEY"
    )
    translation_api_key: SecretStr = Field(
        default=SecretStr(""),
        description="Translation service API key",
        env="TRANSLATION_API_KEY"
    )

    # ============================================================================
    # FILE PATHS
    # ============================================================================
    content_path: str = Field(
        default="./data",
        description="Base path for content data",
        env="CONTENT_PATH"
    )
    models_config: str = Field(
        default="./configs/models.json",
        description="Path to models configuration",
        env="MODELS_CONFIG"
    )
    flows_config: str = Field(
        default="./configs/dialog_flows.json",
        description="Path to dialog flows configuration",
        env="FLOWS_CONFIG"
    )
    services_config: str = Field(
        default="./configs/services.json",
        description="Path to services configuration",
        env="SERVICES_CONFIG"
    )
    templates_path: str = Field(
        default="./configs/response_templates",
        description="Path to response templates",
        env="TEMPLATES_PATH"
    )

    # ============================================================================
    # FASTAPI SPECIFIC
    # ============================================================================
    api_title: str = Field(
        default="Egypt Tourism Chatbot API",
        description="API documentation title",
        env="API_TITLE"
    )
    api_description: str = Field(
        default="API for the Egypt Tourism Chatbot providing tourism information and recommendations",
        description="API documentation description",
        env="API_DESCRIPTION"
    )
    api_version: str = Field(
        default="1.0.0",
        description="API version",
        env="API_VERSION"
    )
    frontend_url: Optional[str] = Field(
        default=None,
        description="Frontend application URL",
        env="FRONTEND_URL"
    )

    # ============================================================================
    # PATHS & DIRECTORIES
    # ============================================================================
    base_dir: str = Field(
        default_factory=lambda: str(Path(__file__).parent.parent),
        description="Base directory of the application"
    )

    # ============================================================================
    # PYDANTIC CONFIGURATION
    # ============================================================================
    model_config = SettingsConfigDict(
        env_file=[".env", ".env.local", ".env.development", ".env.production"],
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
        case_sensitive=False,
    )

    def __init__(self, **kwargs):
        """Initialize settings with environment-specific adjustments."""
        super().__init__(**kwargs)

        # Set debug based on environment
        if self.env == "development":
            self.debug = True

        # Ensure log level is uppercase
        self.log_level = self.log_level.upper()

        # Initialize JWT secret from main secret if not set
        if self.jwt_secret == "generate_a_strong_secret_key_here":
            self.jwt_secret = self.secret_key

    # ============================================================================
    # BACKWARD COMPATIBILITY PROPERTIES
    # ============================================================================
    
    # Legacy config.py compatibility
    @property
    def API_HOST(self) -> str:
        """Backward compatibility: Legacy API_HOST field."""
        return self.api_host
    
    @property
    def API_PORT(self) -> int:
        """Backward compatibility: Legacy API_PORT field."""
        return self.api_port
    
    @property
    def REDIS_HOST(self) -> str:
        """Backward compatibility: Legacy REDIS_HOST field."""
        return self.redis_host
    
    @property
    def REDIS_PORT(self) -> int:
        """Backward compatibility: Legacy REDIS_PORT field."""
        return self.redis_port
    
    @property
    def REDIS_DB(self) -> int:
        """Backward compatibility: Legacy REDIS_DB field."""
        return self.redis_db
    
    @property
    def REDIS_PASSWORD(self) -> Optional[str]:
        """Backward compatibility: Legacy REDIS_PASSWORD field."""
        return self.redis_password
    
    @property
    def SECRET_KEY(self) -> str:
        """Backward compatibility: Legacy SECRET_KEY field."""
        return self.secret_key
    
    @property
    def JWT_SECRET(self) -> str:
        """Backward compatibility: Legacy JWT_SECRET field."""
        return self.jwt_secret
    
    @property
    def JWT_ALGORITHM(self) -> str:
        """Backward compatibility: Legacy JWT_ALGORITHM field."""
        return self.jwt_algorithm
    
    @property
    def JWT_EXPIRATION(self) -> int:
        """Backward compatibility: Legacy JWT_EXPIRATION field."""
        return self.jwt_expiration
    
    @property
    def SESSION_TTL_SECONDS(self) -> int:
        """Backward compatibility: Legacy SESSION_TTL_SECONDS field."""
        return self.session_ttl
    
    @property
    def COOKIE_SECURE(self) -> bool:
        """Backward compatibility: Legacy COOKIE_SECURE field."""
        return self.session_cookie_secure
    
    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        """Backward compatibility: Legacy ALLOWED_ORIGINS field."""
        return self.cors_origins

    # FastAPI config compatibility
    @property
    def HOST(self) -> str:
        """Backward compatibility: FastAPI HOST field."""
        return self.api_host
    
    @property
    def PORT(self) -> int:
        """Backward compatibility: FastAPI PORT field."""
        return self.api_port
    
    @property
    def DEBUG(self) -> bool:
        """Backward compatibility: FastAPI DEBUG field."""
        return self.debug
    
    @property
    def RELOAD(self) -> bool:
        """Backward compatibility: FastAPI RELOAD field."""
        return self.reload
    
    @property
    def WORKERS(self) -> int:
        """Backward compatibility: FastAPI WORKERS field."""
        return self.workers
    
    @property
    def SESSION_COOKIE_NAME(self) -> str:
        """Backward compatibility: FastAPI SESSION_COOKIE_NAME field."""
        return self.session_cookie_name
    
    @property
    def SESSION_EXPIRY(self) -> int:
        """Backward compatibility: FastAPI SESSION_EXPIRY field."""
        return self.session_expiry
    
    @property
    def LOG_LEVEL(self) -> str:
        """Backward compatibility: FastAPI LOG_LEVEL field."""
        return self.log_level
    
    @property
    def LOG_FORMAT(self) -> str:
        """Backward compatibility: FastAPI LOG_FORMAT field."""
        return self.log_format
    
    @property
    def USE_NEW_API(self) -> bool:
        """Backward compatibility: FastAPI USE_NEW_API field."""
        return self.feature_flags.use_new_api
    
    @property
    def ENABLE_REDIS_SESSIONS(self) -> bool:
        """Backward compatibility: FastAPI ENABLE_REDIS_SESSIONS field."""
        return self.feature_flags.enable_redis_sessions
    
    @property
    def BASE_DIR(self) -> str:
        """Backward compatibility: FastAPI BASE_DIR field."""
        return self.base_dir
    
    @property
    def API_TITLE(self) -> str:
        """Backward compatibility: FastAPI API_TITLE field."""
        return self.api_title
    
    @property
    def API_DESCRIPTION(self) -> str:
        """Backward compatibility: FastAPI API_DESCRIPTION field."""
        return self.api_description
    
    @property
    def API_VERSION(self) -> str:
        """Backward compatibility: FastAPI API_VERSION field."""
        return self.api_version

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================

    def as_dict(self) -> Dict[str, Any]:
        """Convert settings to a dictionary, handling SecretStr fields."""
        data = self.model_dump(exclude={"feature_flags"})

        # Replace SecretStr with string value or empty string if None
        for key, value in data.items():
            if isinstance(value, SecretStr):
                data[key] = value.get_secret_value() if value else ""

        # Add feature flags
        for key, value in self.feature_flags.model_dump().items():
            data[key] = value

        return data

    def log_settings(self, include_secrets: bool = False):
        """Log the current settings."""
        logger.info("=== UNIFIED CONFIGURATION SETTINGS ===")
        logger.info(f"Environment: {self.env}")
        logger.info(f"Debug Mode: {self.debug}")
        logger.info(f"API Server: {self.api_host}:{self.api_port}")
        
        for field_name, field_value in self.model_dump(exclude={"feature_flags"}).items():
            # Skip logging secrets unless explicitly requested
            if not include_secrets and any(name in field_name.lower() for name in ["key", "secret", "password", "token", "jwt"]):
                logger.info(f"  {field_name}: [REDACTED]")
            else:
                logger.info(f"  {field_name}: {field_value}")

        # Log feature flags separately
        self.feature_flags.log_status()
        logger.info("=== END CONFIGURATION ===")

    @model_validator(mode='after')
    def validate_and_setup_config(self):
        """Post-initialization validation and setup."""
        # Validate database setup
        logger.debug(f"Using PostgreSQL database URI: {self.database_uri}")

        # Handle session storage URI based on feature flags
        if self.feature_flags.use_redis or self.feature_flags.enable_redis_sessions:
            # Construct Redis URL if individual components are provided
            if all([self.redis_host, self.redis_port]):
                auth = f":{quote_plus(self.redis_password)}@" if self.redis_password else ""
                self.redis_url = f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"
            self.session_storage_uri = self.redis_url
            logger.debug("Redis enabled for session storage")
        else:
            logger.debug("Using file-based session storage")

        # Validate paths exist
        for path_field in ["content_path", "templates_path"]:
            path_value = getattr(self, path_field)
            if not os.path.exists(path_value):
                logger.warning(f"Path does not exist: {path_field} = {path_value}")

        return self


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

# Create the unified settings singleton
settings = UnifiedSettings()

# ============================================================================
# BACKWARD COMPATIBILITY EXPORTS
# ============================================================================

# For immediate compatibility during migration
unified_settings = settings  # Explicit unified reference
legacy_settings = settings   # Legacy compatibility
fastapi_settings = settings  # FastAPI compatibility

# ============================================================================
# DEPRECATION WARNING HELPER
# ============================================================================

def warn_deprecated_import(old_module: str, old_field: str, new_field: str):
    """Helper to warn about deprecated configuration imports."""
    import warnings
    warnings.warn(
        f"Importing '{old_field}' from '{old_module}' is deprecated. "
        f"Use 'from src.config_unified import settings; settings.{new_field}' instead.",
        DeprecationWarning,
        stacklevel=3
    )


if __name__ == "__main__":
    # Configuration validation and testing
    print("=== Egypt Tourism Chatbot - Unified Configuration ===")
    print(f"Environment: {settings.env}")
    print(f"Debug: {settings.debug}")
    print(f"API: {settings.api_host}:{settings.api_port}")
    print(f"Database: {settings.database_uri}")
    print(f"Redis: {settings.redis_url}")
    print(f"Session Storage: {settings.session_storage_uri}")
    print("=== Configuration Loaded Successfully ===")
