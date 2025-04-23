#!/usr/bin/env python3
"""
Feature Flag Configuration Script

This script allows setting feature flags for the Egypt Tourism Chatbot.
It updates the .env file with the appropriate feature flag settings.
"""

import os
import sys
import argparse
import logging
from dotenv import load_dotenv, set_key

# Add the project root to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("feature_flags")

# Define available feature flags
FEATURE_FLAGS = {
    "USE_POSTGRES": {
        "description": "Use PostgreSQL instead of SQLite",
        "default": False,
        "dependencies": []
    },
    "USE_NEW_KB": {
        "description": "Use the new Knowledge Base implementation",
        "default": False,
        "dependencies": []
    },
    "USE_NEW_API": {
        "description": "Use FastAPI instead of Flask",
        "default": False,
        "dependencies": ["USE_NEW_KB"]
    },
    "USE_NEW_NLU": {
        "description": "Use advanced NLU engine",
        "default": False,
        "dependencies": ["USE_NEW_KB"]
    },
    "USE_NEW_DIALOG": {
        "description": "Use stateful Dialog Manager",
        "default": False,
        "dependencies": ["USE_NEW_KB", "USE_NEW_NLU"]
    },
    "USE_REDIS": {
        "description": "Use Redis for session storage",
        "default": False,
        "dependencies": []
    },
    "USE_RAG": {
        "description": "Use RAG pipeline for retrieval",
        "default": False,
        "dependencies": ["USE_NEW_KB"]
    },
    "USE_SERVICE_HUB": {
        "description": "Use Service Hub for external integrations",
        "default": False,
        "dependencies": []
    }
}

def get_current_flags():
    """Get current feature flag values from environment."""
    load_dotenv()
    
    current_flags = {}
    for flag in FEATURE_FLAGS:
        value = os.environ.get(flag, "false").lower() == "true"
        current_flags[flag] = value
    
    return current_flags

def validate_dependencies(flag_values):
    """Validate that dependencies are satisfied."""
    issues = []
    
    for flag, value in flag_values.items():
        if value:  # Only check enabled flags
            for dependency in FEATURE_FLAGS[flag]["dependencies"]:
                if not flag_values.get(dependency, False):
                    issues.append(f"{flag} requires {dependency} to be enabled")
    
    return issues

def update_env_file(flag_values):
    """Update .env file with new flag values."""
    env_path = os.path.join(project_root, '.env')
    
    # Create .env file if it doesn't exist
    if not os.path.exists(env_path):
        with open(env_path, 'w') as f:
            f.write("# Egypt Tourism Chatbot Environment Variables\n\n")
    
    # Update each flag in the .env file
    for flag, value in flag_values.items():
        set_key(env_path, flag, str(value).lower())
    
    logger.info(f"Updated feature flags in {env_path}")
    return True

def print_current_flags(current_flags):
    """Print current feature flag values in a formatted table."""
    print("\n=== Current Feature Flag Settings ===\n")
    
    # Find the longest flag name for formatting
    max_length = max(len(flag) for flag in FEATURE_FLAGS.keys())
    
    # Print table header
    print(f"{'Flag':{max_length}} | {'Enabled':<7} | Description")
    print(f"{'-' * max_length}-+-{'-' * 7}-+-{'-' * 50}")
    
    # Print each flag
    for flag, config in FEATURE_FLAGS.items():
        value = current_flags.get(flag, FEATURE_FLAGS[flag]['default'])
        status = "✅ Yes" if value else "❌ No"
        print(f"{flag:{max_length}} | {status:<7} | {config['description']}")

def main():
    """Main function to handle feature flag configuration."""
    parser = argparse.ArgumentParser(
        description="Configure feature flags for Egypt Tourism Chatbot."
    )
    
    # Add arguments for each feature flag
    for flag, config in FEATURE_FLAGS.items():
        parser.add_argument(
            f"--{flag.lower().replace('_', '-')}",
            dest=flag,
            action="store_true",
            help=config["description"]
        )
        parser.add_argument(
            f"--no-{flag.lower().replace('_', '-')}",
            dest=flag,
            action="store_false",
            help=f"Disable {flag}"
        )
        parser.set_defaults(**{flag: None})
    
    # Add general arguments
    parser.add_argument(
        "--set-env",
        action="store_true",
        help="Update .env file with new values"
    )
    parser.add_argument(
        "--check-dependencies",
        action="store_true",
        help="Check dependencies between feature flags"
    )
    parser.add_argument(
        "--enable-all",
        action="store_true",
        help="Enable all feature flags"
    )
    parser.add_argument(
        "--disable-all",
        action="store_true",
        help="Disable all feature flags"
    )
    parser.add_argument(
        "--safe-transition",
        action="store_true",
        help="Enable a safe transition path: KB → Postgres → Redis → NLU → Dialog → RAG → Service Hub → API"
    )
    
    args = parser.parse_args()
    
    # Get current flag values
    current_flags = get_current_flags()
    
    # Print current flags
    print_current_flags(current_flags)
    
    # Determine new flag values
    new_flags = current_flags.copy()
    
    # Handle --enable-all/--disable-all
    if args.enable_all:
        for flag in FEATURE_FLAGS:
            new_flags[flag] = True
    elif args.disable_all:
        for flag in FEATURE_FLAGS:
            new_flags[flag] = False
    elif args.safe_transition:
        # Implement a safe transition path:
        # KB → Postgres → Redis → NLU → Dialog → RAG → Service Hub → API
        transition_order = [
            "USE_NEW_KB",
            "USE_POSTGRES",
            "USE_REDIS",
            "USE_NEW_NLU",
            "USE_NEW_DIALOG",
            "USE_RAG",
            "USE_SERVICE_HUB",
            "USE_NEW_API"
        ]
        for flag in transition_order:
            new_flags[flag] = True
    else:
        # Apply individual flag changes from arguments
        for flag in FEATURE_FLAGS:
            value = getattr(args, flag)
            if value is not None:  # Only update if explicitly set
                new_flags[flag] = value
    
    # Check for changes
    changes = {flag: new_flags[flag] for flag in FEATURE_FLAGS if current_flags.get(flag, False) != new_flags[flag]}
    
    if not changes:
        print("\nNo changes to feature flags.")
        return True
    
    # Check dependencies
    if args.check_dependencies or args.set_env:
        issues = validate_dependencies(new_flags)
        if issues:
            print("\n⚠️ Dependency issues detected:")
            for issue in issues:
                print(f"  - {issue}")
            
            if args.set_env:
                response = input("\nDo you want to proceed anyway? (y/N): ").lower()
                if response != 'y':
                    print("Operation cancelled.")
                    return False
    
    # Update .env file if requested
    if args.set_env:
        if update_env_file(new_flags):
            # Print changes
            print("\n=== Feature Flag Changes ===\n")
            for flag, value in changes.items():
                print(f"{flag}: {'✅ Enabled' if value else '❌ Disabled'}")
            print("\nFeature flags updated successfully.")
        else:
            print("\nFailed to update feature flags.")
            return False
    else:
        # Print what would change
        print("\n=== Proposed Feature Flag Changes ===\n")
        for flag, value in changes.items():
            print(f"{flag}: {'✅ Enable' if value else '❌ Disable'}")
        print("\nRun with --set-env to apply these changes.")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 