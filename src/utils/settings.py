"""
Settings module for the Egypt Tourism Chatbot.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class FeatureFlags(BaseSettings):
    """Feature flags configuration."""
    
    use_new_kb: bool = Field(default=False, env="USE_NEW_KB")
    use_postgres: bool = Field(default=True, env="USE_POSTGRES")
    use_redis: bool = Field(default=False, env="USE_REDIS")
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"  # Ignore extra fields from .env
    }


class Settings(BaseSettings):
    """Application settings."""
    
    # Environment
    env: str = Field(default="development", env="ENV")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Database
    database_uri: str = Field(default="postgresql://localhost:5432/egypt_chatbot", env="POSTGRES_URI")
    
    # Session storage
    session_storage_uri: str = Field(default="redis://localhost:6379/0", env="REDIS_URI")
    
    # Content path
    content_path: str = Field(default="./data", env="CONTENT_PATH")
    
    # Security
    jwt_secret: str = Field(default="dev-secret-change-in-production", env="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    
    # Feature flags
    feature_flags: FeatureFlags = Field(default_factory=FeatureFlags)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure content path exists
        Path(self.content_path).mkdir(parents=True, exist_ok=True)
        
        # Initialize feature flags
        self.feature_flags = FeatureFlags()
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"  # Ignore extra fields from .env
    }


# Global settings instance
settings = Settings()
