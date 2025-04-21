"""
Settings module for the Egypt Tourism Chatbot.
Uses pydantic-settings to manage configuration from .env file and environment variables.
"""
import os
from typing import Dict, List, Optional, Union, Any
from pydantic import Field, field_validator, SecretStr, AnyHttpUrl, validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import logging

logger = logging.getLogger(__name__)

class FeatureFlags(BaseSettings):
    """Feature flags for enabling/disabling components."""
    
    # Core architecture flags
    use_new_kb: bool = Field(default=False, description="Use the new Knowledge Base implementation", env="USE_NEW_KB")
    use_new_api: bool = Field(default=False, description="Use FastAPI instead of Flask", env="USE_NEW_API")
    use_postgres: bool = Field(default=False, description="Use PostgreSQL instead of SQLite", env="USE_POSTGRES")
    
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
    database_uri: str = Field(default="sqlite:///./data/egypt_chatbot.db")
    vector_db_uri: str = Field(default="./data/vector_db")
    content_path: str = Field(default="./data")
    
    # Session storage
    session_storage_uri: str = Field(default="file:///./data/sessions")
    redis_url: str = Field(default="redis://localhost:6379/0")
    
    # API configuration
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=5000)
    frontend_url: Optional[str] = Field(default=None)
    allowed_origins: List[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    
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
        
        # Initialize feature flags explicitly with direct environment variable checks
        # feature_flags_dict = {}
        # feature_flags_dict["use_new_kb"] = os.getenv("USE_NEW_KB", "false").lower() == "true"
        # feature_flags_dict["use_new_api"] = os.getenv("USE_NEW_API", "false").lower() == "true"
        # feature_flags_dict["use_postgres"] = os.getenv("USE_POSTGRES", "false").lower() == "true"
        # feature_flags_dict["use_new_nlu"] = os.getenv("USE_NEW_NLU", "false").lower() == "true"
        # feature_flags_dict["use_new_dialog"] = os.getenv("USE_NEW_DIALOG", "false").lower() == "true"
        # feature_flags_dict["use_rag"] = os.getenv("USE_RAG", "false").lower() == "true"
        # feature_flags_dict["use_redis"] = os.getenv("USE_REDIS", "false").lower() == "true"
        # feature_flags_dict["use_service_hub"] = os.getenv("USE_SERVICE_HUB", "false").lower() == "true"
        # 
        # # Log the actual environment values we're using for feature flags
        # logger.info("Feature flag values directly from environment variables:")
        # for key, value in feature_flags_dict.items():
        #     logger.info(f"  {key.upper()} (from env): {value}")
        # 
        # # Create FeatureFlags instance with the dictionary values
        # self.feature_flags = FeatureFlags(**feature_flags_dict)
        # Rely on Pydantic's default env var loading for feature_flags
        pass # No explicit feature flag init needed here if loaded via pydantic
    
    @field_validator("allowed_origins")
    def validate_allowed_origins(cls, v, info):
        """Validate allowed origins and add frontend_url if set."""
        if not v:
            v = ["http://localhost:3000"]
        
        # Add frontend_url to allowed_origins if set and not already present
        frontend_url = os.getenv("FRONTEND_URL")
        if frontend_url and frontend_url not in v and frontend_url != "*":
            v.append(frontend_url)
            
        # Check for insecure wildcard with credentials
        if "*" in v:
            logger.warning("SECURITY RISK: Using wildcard (*) for CORS allowed_origins with credentials is unsafe and violates the CORS spec")
            
        return v
    
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
    
# Create a global instance
settings = Settings() 