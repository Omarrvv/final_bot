#!/usr/bin/env python
"""
Migration script for transitioning to the new database architecture.

This script helps with the transition from the old database architecture to the new one.
It performs the following tasks:
1. Creates a backup of the old database files
2. Runs tests to verify the new implementation
3. Updates imports in the codebase to use the new implementation
"""
import os
import sys
import shutil
import subprocess
import argparse
from datetime import datetime

def create_backup(files_to_backup):
    """
    Create a backup of the specified files.
    
    Args:
        files_to_backup: List of files to backup
    
    Returns:
        str: Path to the backup directory
    """
    # Create backup directory
    backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    # Backup files
    for file_path in files_to_backup:
        if os.path.exists(file_path):
            # Create subdirectories in backup if needed
            backup_path = os.path.join(backup_dir, file_path)
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            # Copy file to backup
            shutil.copy2(file_path, backup_path)
            print(f"Backed up {file_path} to {backup_path}")
    
    return backup_dir

def run_tests(test_file):
    """
    Run tests to verify the new implementation.
    
    Args:
        test_file: Path to the test file
    
    Returns:
        bool: True if tests pass, False otherwise
    """
    print(f"Running tests in {test_file}...")
    result = subprocess.run(["python", "-m", "unittest", test_file], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("Tests passed!")
        return True
    else:
        print("Tests failed!")
        print(result.stdout)
        print(result.stderr)
        return False

def update_imports(files_to_update, old_import, new_import):
    """
    Update imports in the specified files.
    
    Args:
        files_to_update: List of files to update
        old_import: Old import statement to replace
        new_import: New import statement to use
    """
    for file_path in files_to_update:
        if os.path.exists(file_path):
            # Read file
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Replace import
            updated_content = content.replace(old_import, new_import)
            
            # Write updated content
            with open(file_path, 'w') as f:
                f.write(updated_content)
            
            print(f"Updated imports in {file_path}")

def rename_files(file_mappings):
    """
    Rename files according to the provided mappings.
    
    Args:
        file_mappings: Dictionary mapping old file paths to new file paths
    """
    for old_path, new_path in file_mappings.items():
        if os.path.exists(old_path):
            # Create directory for new path if needed
            os.makedirs(os.path.dirname(new_path), exist_ok=True)
            
            # Rename file
            shutil.move(old_path, new_path)
            print(f"Renamed {old_path} to {new_path}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Migrate to new database architecture")
    parser.add_argument("--backup-only", action="store_true", help="Only create backup, don't make changes")
    parser.add_argument("--skip-tests", action="store_true", help="Skip running tests")
    parser.add_argument("--skip-backup", action="store_true", help="Skip creating backup")
    args = parser.parse_args()
    
    # Files to backup
    files_to_backup = [
        "src/knowledge/database.py",
        "src/services/base_service.py",
        "src/services/attraction_service.py",
        "src/services/restaurant_service.py",
        "src/services/service_registry.py"
    ]
    
    # Create backup
    if not args.skip_backup:
        backup_dir = create_backup(files_to_backup)
        print(f"Backup created in {backup_dir}")
    
    # Exit if backup-only
    if args.backup_only:
        print("Backup completed. Exiting without making changes.")
        return
    
    # Run tests
    if not args.skip_tests:
        tests_pass = run_tests("tests/test_database_refactoring.py")
        if not tests_pass:
            print("Tests failed. Aborting migration.")
            return
    
    # Rename files
    file_mappings = {
        "src/knowledge/database_manager_new.py": "src/knowledge/database.py"
    }
    rename_files(file_mappings)
    
    # Update imports in files
    files_to_update = [
        "src/knowledge_base.py",
        "src/app.py",
        "src/chatbot.py",
        "tests/test_database.py",
        "tests/test_knowledge_base.py"
    ]
    
    old_import = "from src.knowledge.database import DatabaseManager"
    new_import = "from src.knowledge.database import DatabaseManager"
    
    update_imports(files_to_update, old_import, new_import)
    
    print("Migration completed successfully!")

if __name__ == "__main__":
    main()
