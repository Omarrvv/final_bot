#!/usr/bin/env python3
"""
Feature Flag Status Checker

This script displays the current state of all feature flags in the Egypt Tourism Chatbot.
Use it to verify your environment configuration.
"""

import os
import sys
import logging
from pathlib import Path

# Add parent directory to sys.path to allow importing from src
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def get_feature_flag_value(flag_name):
    """Get the boolean value of a feature flag from environment variables."""
    value = os.getenv(flag_name, "false").lower()
    return value in ("true", "1", "yes")

def main():
    """Display the current state of all feature flags."""
    # Core feature flags
    core_flags = [
        "USE_NEW_KB",
        "USE_NEW_API", 
        "USE_POSTGRES",
    ]
    
    # Advanced feature flags
    advanced_flags = [
        "USE_NEW_NLU",
        "USE_NEW_DIALOG",
        "USE_RAG",
        "USE_REDIS",
        "USE_SERVICE_HUB"
    ]
    
    print("\n==== Egypt Tourism Chatbot Feature Flags ====\n")
    
    print("Core Architecture Flags:")
    print("-----------------------")
    for flag in core_flags:
        value = get_feature_flag_value(flag)
        status = "ENABLED" if value else "DISABLED"
        print(f"{flag:15} : {status}")
    
    print("\nAdvanced Feature Flags:")
    print("---------------------")
    for flag in advanced_flags:
        value = get_feature_flag_value(flag)
        status = "ENABLED" if value else "DISABLED"
        print(f"{flag:15} : {status}")
    
    print("\nNote: To change feature flag state, set the environment variables")
    print("      or update your .env file and restart the application.")
    print("\n==============================================\n")

if __name__ == "__main__":
    main() 