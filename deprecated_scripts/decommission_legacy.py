#!/usr/bin/env python
"""
Script to safely decommission the legacy app.py and update requirements.txt

This script:
1. Backs up app.py (if it exists) to app.py.bak
2. Creates a warning file in place of app.py
3. Updates requirements.txt to remove Flask dependencies
"""
import os
import sys
import shutil
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("decommission_legacy")

# Set up paths
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
app_py_path = os.path.join(project_root, "app.py")
src_app_py_path = os.path.join(project_root, "src", "app.py")
requirements_path = os.path.join(project_root, "requirements.txt")
readme_path = os.path.join(project_root, "README.md")

def backup_file(file_path, backup_suffix=".bak"):
    """Backup a file by adding a suffix."""
    if os.path.exists(file_path):
        backup_path = f"{file_path}{backup_suffix}"
        shutil.copy2(file_path, backup_path)
        logger.info(f"Backed up {file_path} to {backup_path}")
        return True
    return False

def create_warning_file(file_path):
    """Create a warning file in place of the original file."""
    warning_content = f'''"""
DEPRECATION WARNING

This file has been decommissioned as part of the architecture unification process.
The application has been migrated to use FastAPI in the src/ directory.

To start the application, use:
    python -m uvicorn src.main:app --host 0.0.0.0 --port 5050

Or use the provided start_chatbot.sh script.

This file was decommissioned on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

# Raise an exception if someone tries to import from this file
raise ImportError(
    "This file has been decommissioned. "
    "The application has been migrated to src/main.py using FastAPI."
)
'''
    
    with open(file_path, 'w') as f:
        f.write(warning_content)
    logger.info(f"Created warning file at {file_path}")

def update_requirements():
    """Update requirements.txt to remove Flask dependencies."""
    if not os.path.exists(requirements_path):
        logger.warning(f"Requirements file not found at {requirements_path}")
        return False
    
    # Backup requirements.txt
    backup_file(requirements_path)
    
    # Define Flask-related packages to remove
    flask_packages = [
        'flask', 
        'Flask',
        'flask-cors',
        'Flask-Cors',
        'flask-wtf',
        'Flask-WTF',
        'flask-limiter',
        'Flask-Limiter'
    ]
    
    # Read current requirements
    with open(requirements_path, 'r') as f:
        requirements = f.readlines()
    
    # Filter out Flask-related packages
    new_requirements = []
    removed_packages = []
    
    for req in requirements:
        req = req.strip()
        is_flask_package = False
        
        for flask_pkg in flask_packages:
            if req.lower().startswith(flask_pkg.lower()):
                is_flask_package = True
                removed_packages.append(req)
                break
        
        if not is_flask_package:
            new_requirements.append(req)
    
    # Add FastAPI dependencies if not already present
    fastapi_packages = [
        'fastapi>=0.100.0',
        'uvicorn[standard]>=0.22.0',
        'python-multipart>=0.0.6',
        'starlette>=0.27.0'
    ]
    
    for pkg in fastapi_packages:
        pkg_name = pkg.split('>=')[0].lower()
        if not any(req.lower().startswith(pkg_name) for req in new_requirements):
            new_requirements.append(pkg)
            logger.info(f"Added {pkg} to requirements")
    
    # Write updated requirements
    with open(requirements_path, 'w') as f:
        f.write('\n'.join(new_requirements))
    
    # Log changes
    if removed_packages:
        logger.info(f"Removed packages from requirements.txt: {', '.join(removed_packages)}")
    
    return True

def update_readme():
    """Update README.md to reflect the new architecture."""
    if not os.path.exists(readme_path):
        logger.warning(f"README file not found at {readme_path}")
        return False
    
    # Backup README.md
    backup_file(readme_path)
    
    # Read current README
    with open(readme_path, 'r') as f:
        readme_content = f.read()
    
    # Add architecture migration notice
    migration_notice = """
## Architecture Migration Notice

This application has been migrated from a Flask-based architecture to FastAPI.
The new application structure is contained in the `src/` directory with `src/main.py` as the entry point.

To start the application, use:
```bash
python -m uvicorn src.main:app --host 0.0.0.0 --port 5050
```

Or use the provided `start_chatbot.sh` script.
"""
    
    # Check if the notice is already in the README
    if "Architecture Migration Notice" not in readme_content:
        # Find a good place to insert the notice (after the first heading)
        if "# " in readme_content:
            first_heading_end = readme_content.find("# ") + readme_content[readme_content.find("# "):].find("\n")
            new_readme = (
                readme_content[:first_heading_end + 1] + 
                migration_notice + 
                readme_content[first_heading_end + 1:]
            )
        else:
            # If no heading, add to the beginning
            new_readme = migration_notice + "\n" + readme_content
        
        # Write updated README
        with open(readme_path, 'w') as f:
            f.write(new_readme)
        
        logger.info(f"Updated README.md with architecture migration notice")
        return True
    
    return False

def main():
    """Main function to execute the decommissioning process."""
    logger.info("Starting legacy decommissioning process")
    
    # 1. Backup and replace app.py
    if os.path.exists(app_py_path):
        backup_file(app_py_path)
        create_warning_file(app_py_path)
    else:
        logger.warning(f"Legacy app.py not found at {app_py_path}")
    
    # 2. Backup and replace src/app.py if it exists
    if os.path.exists(src_app_py_path):
        backup_file(src_app_py_path)
        create_warning_file(src_app_py_path)
    
    # 3. Update requirements.txt
    update_requirements()
    
    # 4. Update README.md
    update_readme()
    
    logger.info("Legacy decommissioning process completed successfully")
    logger.info("IMPORTANT: Make sure to test the FastAPI application thoroughly before deploying")

if __name__ == "__main__":
    main() 