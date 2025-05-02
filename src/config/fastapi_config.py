"""
FastAPI Configuration Module

This module contains all configuration settings for the FastAPI application,
centralizing environment variables and configuration options.
"""
import os
from pydantic import BaseSettings, Field
from typing import Optional, Dict, Any, List

class FastAPISettings(BaseSettings):
    """FastAPI application settings with defaults loaded from environment variables."""
    
    # API Server Settings
    HOST: str = Field(default="0.0.0.0", env="API_HOST")
    PORT: int = Field(default=5050, env="FASTAPI_PORT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    RELOAD: bool = Field(default=True, env="API_RELOAD")
    WORKERS: int = Field(default=1, env="API_WORKERS")
    
    # Security Settings
    SECRET_KEY: str = Field(default=os.getenv("SECRET_KEY", "your-secret-key"), env="SECRET_KEY")
    SESSION_COOKIE_NAME: str = Field(default="egypt_tourism_session", env="SESSION_COOKIE_NAME")
    SESSION_EXPIRY: int = Field(default=3600 * 24, env="SESSION_EXPIRY")  # 24 hours in seconds
    allowed_origins: str = Field(
        default="http://localhost:3000,http://localhost:5050",
        env="ALLOWED_ORIGINS"
    )
    _allowed_origins_list: List[str] = []
    
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
    
    # Redis Settings for Session Storage
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    # API Documentation Settings
    API_TITLE: str = "Egypt Tourism Chatbot API"
    API_DESCRIPTION: str = "API for the Egypt Tourism Chatbot providing tourism information and recommendations"
    API_VERSION: str = "1.0.0"
    
    # Logging Settings
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Feature Flags
    USE_NEW_API: bool = Field(default=False, env="USE_NEW_API")
    ENABLE_REDIS_SESSIONS: bool = Field(default=False, env="ENABLE_REDIS_SESSIONS")
    
    # Application Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    class Config:
        """Pydantic settings configuration"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# Create a singleton instance
settings = FastAPISettings()

# Dictionary of log levels
LOG_LEVELS = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50
}

def get_log_level() -> int:
    """Get the numeric log level from the settings."""
    return LOG_LEVELS.get(settings.LOG_LEVEL, 20)  # Default to INFO

def get_api_metadata() -> Dict[str, Any]:
    """Get API metadata for documentation."""
    return {
        "title": settings.API_TITLE,
        "description": settings.API_DESCRIPTION,
        "version": settings.API_VERSION,
    }