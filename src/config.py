import os
import yaml


CONFIG_DIR = os.path.join(os.path.dirname(__file__), '../config')


def deep_update(source, overrides):
    """
    Update a nested dictionary or similar mapping.
    Modify source in place.
    """
    for key, value in overrides.items():
        if isinstance(value, dict) and key in source and isinstance(source[key], dict):
            deep_update(source[key], value)
        else:
            source[key] = value
    return source

def load_config():
    """
    Load configuration from config files.
    
    Returns:
        dict: Combined configuration
    """
    config = {}
    
    # Load app config
    app_config_path = os.path.join(CONFIG_DIR, 'app_config.yml')
    if os.path.exists(app_config_path):
        with open(app_config_path, 'r') as f:
            app_config = yaml.safe_load(f)
            if app_config:
                config.update(app_config)
    
    # Load NLU config
    nlu_config_path = os.path.join(CONFIG_DIR, 'nlu_config.yml')
    if os.path.exists(nlu_config_path):
        with open(nlu_config_path, 'r') as f:
            nlu_config = yaml.safe_load(f)
            if nlu_config:
                config['NLU'] = nlu_config
    
    # Load database config
    db_config_path = os.path.join(CONFIG_DIR, 'database_config.yml')
    if os.path.exists(db_config_path):
        with open(db_config_path, 'r') as f:
            db_config = yaml.safe_load(f)
            if db_config:
                config['DATABASE'] = db_config
                
    # Load analytics config
    analytics_config_path = os.path.join(CONFIG_DIR, 'analytics_config.yml')
    if os.path.exists(analytics_config_path):
        with open(analytics_config_path, 'r') as f:
            analytics_config = yaml.safe_load(f)
            if analytics_config:
                config['ANALYTICS'] = analytics_config
    
    # Override with environment-specific config if available
    env = os.environ.get('FLASK_ENV', 'development')
    env_config_path = os.path.join(CONFIG_DIR, f'{env}_config.yml')
    if os.path.exists(env_config_path):
        with open(env_config_path, 'r') as f:
            env_config = yaml.safe_load(f)
            if env_config:
                deep_update(config, env_config)
    
    return config

# Settings class for the application
class Settings:
    """Application settings with environment variable overrides."""
    
    def __init__(self):
        # Default settings 
        
        # Session settings
        self.SESSION_TTL_SECONDS = int(os.environ.get("SESSION_TTL_SECONDS", 86400))  # 24 hours default
        self.COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "false").lower() == "true"
        
        # Redis configuration
        self.REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
        self.REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
        self.REDIS_DB = int(os.environ.get("REDIS_DB", 0))
        self.REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", None)
        
        # API configuration
        self.API_HOST = os.environ.get("API_HOST", "0.0.0.0")
        self.API_PORT = int(os.environ.get("API_PORT", 5050))
        
        # Security
        self.SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-change-me-in-production")
        self.JWT_SECRET = os.environ.get("JWT_SECRET", self.SECRET_KEY)
        self.JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
        self.JWT_EXPIRATION = int(os.environ.get("JWT_EXPIRATION", 3600))  # 1 hour default
        
        # CORS settings
        self.ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "*").split(",")

# Create a singleton instance
settings = Settings() 
