#!/usr/bin/env python3
"""Debug script to identify issues with environment variables and settings."""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main function to debug settings."""
    # Print all environment variables
    logger.debug("Current environment variables:")
    for key, value in sorted(os.environ.items()):
        # Skip complex environment variables to keep output readable
        if key.startswith("CONDA_") or key.startswith("LC_") or key.startswith("LS_"):
            continue
        logger.debug(f"  {key}={value}")
    
    # Check Redis-related variables specifically
    redis_vars = {key: value for key, value in os.environ.items() if "REDIS" in key.upper()}
    logger.info("Redis-related environment variables:")
    for key, value in redis_vars.items():
        logger.info(f"  {key}={value}")
    
    # Check feature flag variables
    flag_vars = {
        key: value for key, value in os.environ.items() 
        if key.upper().startswith("USE_")
    }
    logger.info("Feature flag environment variables:")
    for key, value in flag_vars.items():
        logger.info(f"  {key}={value}")
    
    # Try to import the settings module
    try:
        # Add parent directory to sys.path to allow importing from src
        sys.path.append(str(Path(__file__).parent))
        
        # Try to import FeatureFlags only
        from src.utils.settings import FeatureFlags
        logger.info("Successfully imported FeatureFlags class")
        
        # Create an instance of FeatureFlags without initializing settings module
        flags = FeatureFlags()
        logger.info("FeatureFlags instance created successfully")
        
        # Print the flag values from the flags object
        logger.info("Feature flag values from FeatureFlags instance:")
        for field_name, field_value in flags.model_dump().items():
            logger.info(f"  {field_name}: {field_value}")
        
        return 0
    except Exception as e:
        logger.error(f"Error during settings import: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 