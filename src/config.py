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
