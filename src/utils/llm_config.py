"""
Configuration module for LLM settings in the Egypt Tourism Chatbot.
"""
import logging
import json
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Default configuration
_config = {
    "USE_LLM_FIRST": False,
    "MAX_TOKENS": 150,
    "RESPONSE_LENGTH": "short"  # "short", "medium", "long"
}

def get_config() -> Dict[str, Any]:
    """
    Get the current LLM configuration.
    
    Returns:
        Dict containing the configuration
    """
    return _config.copy()

def set_config(key: str, value: Any) -> Dict[str, Any]:
    """
    Set a configuration value.
    
    Args:
        key: Configuration key
        value: Configuration value
        
    Returns:
        Updated configuration
    """
    if key in _config:
        _config[key] = value
        logger.info(f"Updated LLM configuration: {key}={value}")
    else:
        logger.warning(f"Unknown LLM configuration key: {key}")
    
    return _config.copy()

def toggle_llm_first() -> bool:
    """
    Toggle the USE_LLM_FIRST setting.
    
    Returns:
        New value of USE_LLM_FIRST
    """
    _config["USE_LLM_FIRST"] = not _config["USE_LLM_FIRST"]
    logger.info(f"Toggled USE_LLM_FIRST to {_config['USE_LLM_FIRST']}")
    return _config["USE_LLM_FIRST"]

def use_llm_first() -> bool:
    """
    Check if LLM should be used first.
    
    Returns:
        True if LLM should be used first, False otherwise
    """
    return _config["USE_LLM_FIRST"]

def save_config(file_path: str = None) -> bool:
    """
    Save the configuration to a file.
    
    Args:
        file_path: Path to save the configuration to
        
    Returns:
        True if successful, False otherwise
    """
    if not file_path:
        file_path = os.path.join(os.path.dirname(__file__), "llm_config.json")
    
    try:
        with open(file_path, "w") as f:
            json.dump(_config, f, indent=2)
        logger.info(f"Saved LLM configuration to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save LLM configuration: {str(e)}")
        return False

def load_config(file_path: str = None) -> bool:
    """
    Load the configuration from a file.
    
    Args:
        file_path: Path to load the configuration from
        
    Returns:
        True if successful, False otherwise
    """
    if not file_path:
        file_path = os.path.join(os.path.dirname(__file__), "llm_config.json")
    
    if not os.path.exists(file_path):
        logger.warning(f"LLM configuration file not found: {file_path}")
        return False
    
    try:
        with open(file_path, "r") as f:
            config = json.load(f)
        
        for key, value in config.items():
            if key in _config:
                _config[key] = value
        
        logger.info(f"Loaded LLM configuration from {file_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to load LLM configuration: {str(e)}")
        return False
