#!/usr/bin/env python3
"""
Dependency Verification Script

This script checks if all required dependencies can be imported successfully.
Run this after installing dependencies to verify the environment is correctly set up.
"""

import sys
import importlib
import logging
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def check_import(module_name: str) -> bool:
    """
    Attempt to import a module and return success/failure.
    
    Args:
        module_name: The name of the module to import
        
    Returns:
        bool: True if import succeeded, False otherwise
    """
    try:
        importlib.import_module(module_name)
        return True
    except ImportError as e:
        logger.error(f"Failed to import {module_name}: {str(e)}")
        return False

def main():
    """
    Main function to check all dependencies.
    """
    # Define groups of dependencies to check
    dependency_groups: Dict[str, List[str]] = {
        "FastAPI Framework": [
            "fastapi", "uvicorn", "pydantic", "pydantic_settings", "jinja2",
            "starlette", "fastapi_limiter"
        ],
        "Security": [
            "jwt", "passlib", "jose", "starlette_csrf", "bcrypt"
        ],
        "NLP & ML": [
            "spacy", "transformers", "torch", "sentence_transformers",
            "fasttext"
        ],
        "Database": [
            "sqlalchemy", "psycopg2", "redis"
        ],
        "HTTP & Networking": [
            "requests", "httpx"
        ],
        "Utilities": [
            "python_dateutil", "markdown", "email_validator", "wheel"
        ],
        "Development & Testing": [
            "pytest", "pytest_asyncio", "pytest_cov", "typer"
        ]
    }
    
    # Track results
    success_count = 0
    failure_count = 0
    
    print("\n==== Egypt Tourism Chatbot Dependency Verification ====\n")
    
    # Check each group
    for group_name, modules in dependency_groups.items():
        print(f"\n{group_name}:")
        print("-" * (len(group_name) + 1))
        
        for module in modules:
            success = check_import(module)
            if success:
                success_count += 1
                print(f"✅ {module}")
            else:
                failure_count += 1
                print(f"❌ {module}")
    
    # Summary
    total = success_count + failure_count
    print(f"\nSummary: {success_count}/{total} dependencies imported successfully.")
    
    if failure_count > 0:
        print(f"\n⚠️  {failure_count} dependencies failed to import.")
        print("Please install missing dependencies:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    else:
        print("\n✅ All dependencies imported successfully. Environment is ready!")
        sys.exit(0)

if __name__ == "__main__":
    main() 