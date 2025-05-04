"""
Settings module for the Egypt Tourism Chatbot.
Uses pydantic-settings to manage configuration from .env file and environment variables.
"""
import os
from typing import Dict, List, Optional, Any
from pydantic import Field, field_validator, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import logging

logger = logging.getLogger(__name__)

class FeatureFlags(BaseSettings):
    """Feature flags for enabling/disabling components."""

    # Core architecture flags
    use_new_kb: bool = Field(default=False, description="Use the new Knowledge Base implementation", env="USE_NEW_KB")
    use_postgres: bool = Field(default=True, description="Use PostgreSQL instead of SQLite", env="USE_POSTGRES")

    # Advanced features flags
    use_new_nlu: bool = Field(default=False, description="Use the advanced NLU engine", env="USE_NEW_NLU")
    use_new_dialog: bool = Field(default=False, description="Use the stateful Dialog Manager", env="USE_NEW_DIALOG")
    use_rag: bool = Field(default=False, description="Use the RAG pipeline", env="USE_RAG")
    use_redis: bool = Field(default=False, description="Use Redis for session storage", env="USE_REDIS")
    use_service_hub: bool = Field(default=False, description="Use the Service Hub for external APIs", env="USE_SERVICE_HUB")

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    def log_status(self):
        """Log the current status of all feature flags."""
        logger.info("Feature flags configuration:")
        for field_name, field_value in self.model_dump().items():
            logger.info(f"  {field_name.upper()}: {field_value}")

class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    # Feature flags
    feature_flags: FeatureFlags = Field(default_factory=FeatureFlags)

    # Environment
    env: str = Field(default="development", env="ENV")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")

    # Database
    database_uri: str = Field(
        default="postgresql://user:password@localhost:5432/egypt_chatbot",
        description="PostgreSQL database connection URI",
        env="POSTGRES_URI"
    )
    vector_db_uri: str = Field(default="./data/vector_db")
    content_path: str = Field(default="./data")

    # Session storage
    session_storage_uri: str = Field(
        default="file:///./data/sessions",
        description="URI for session storage. Will use Redis if USE_REDIS is true"
    )
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL"
    )
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")

    # Session configuration
    session_ttl: int = Field(default=86400, description="Session time-to-live in seconds", env="SESSION_TTL_SECONDS")
    session_cookie_name: str = Field(default="session_token", description="Name of the session cookie", env="SESSION_COOKIE_NAME")
    session_cookie_secure: bool = Field(default=False, description="Whether to set the secure flag on session cookies", env="COOKIE_SECURE")

    # API configuration
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=5000)
    frontend_url: Optional[str] = Field(default=None)
    allowed_origins: str = Field(default="http://localhost:3000,http://localhost:5050")
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

    # Security
    jwt_secret: str = Field(default="generate_a_strong_secret_key_here")
    jwt_algorithm: str = Field(default="HS256")
    jwt_expiration: int = Field(default=3600)  # 1 hour in seconds

    # Paths
    models_config: str = Field(default="./configs/models.json")
    flows_config: str = Field(default="./configs/dialog_flows.json")
    services_config: str = Field(default="./configs/services.json")
    templates_path: str = Field(default="./configs/response_templates")

    # API Keys (as SecretStr for security)
    anthropic_api_key: SecretStr = Field(default=SecretStr(""))
    weather_api_key: SecretStr = Field(default=SecretStr(""))
    translation_api_key: SecretStr = Field(default=SecretStr(""))

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
        case_sensitive=False,
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Set debug based on environment
        if self.env == "development":
            self.debug = True

        # Parse log level
        self.log_level = self.log_level.upper()

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
        logger.info("Application settings:")
        for field_name, field_value in self.model_dump(exclude={"feature_flags"}).items():
            # Skip logging secrets unless explicitly requested
            if not include_secrets and any(name in field_name for name in ["key", "secret", "password", "token", "jwt"]):
                logger.info(f"  {field_name}: [REDACTED]")
            else:
                logger.info(f"  {field_name}: {field_value}")

        # Log feature flags separately
        self.feature_flags.log_status()

    @model_validator(mode='after')
    def validate_storage_config(self):
        """Update storage URIs based on feature flags."""
        # Log database setup
        logger.info(f"Using PostgreSQL database URI: {self.database_uri}")

        # Handle session storage URI
        if self.feature_flags.use_redis:
            # Construct Redis URL if individual components are provided
            if all([self.redis_host, self.redis_port]):
                auth = f":{self.redis_password}@" if self.redis_password else ""
                self.redis_url = f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"
            self.session_storage_uri = self.redis_url
            logger.info("Redis enabled for session storage")
        else:
            logger.info("Using file-based session storage")

        return self

# Create a global instance
settings = Settings()