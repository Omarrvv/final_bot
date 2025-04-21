#!/usr/bin/env python3
"""Test script to check if .env file is loaded correctly."""

import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Check .env loading."""
    logger.info("Testing .env loading...")
    
    # 1. Try to load .env file
    logger.info("Loading .env file...")
    load_dotenv()
    
    # 2. Print current working directory
    logger.info(f"Current working directory: {os.getcwd()}")
    
    # 3. Check if .env file exists
    env_path = os.path.join(os.getcwd(), '.env')
    logger.info(f".env file exists: {os.path.exists(env_path)}")
    
    # 4. Check USE_NEW_KB value
    use_new_kb = os.getenv('USE_NEW_KB')
    logger.info(f"USE_NEW_KB value from os.getenv: {use_new_kb}")
    
    # 5. Print first few lines of .env file for debugging
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            env_content = f.readlines()
            logger.info("First 30 lines of .env file:")
            for i, line in enumerate(env_content[:30]):
                logger.info(f"  {i+1}: {line.strip()}")
    
    return 0

if __name__ == "__main__":
    main() 