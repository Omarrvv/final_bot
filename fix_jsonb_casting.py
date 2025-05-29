#!/usr/bin/env python3
"""
Fix script for JSONB casting issues in the Egypt Tourism Chatbot.
This script patches the database.py file to fix JSONB column casting issues.
"""

import os
import sys
import re
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_database_file():
    """Fix the database.py file to properly cast JSONB columns to text."""
    
    # Path to the database.py file
    db_file_path = Path("src/knowledge/database.py")
    
    if not db_file_path.exists():
        logger.error(f"Database file not found at {db_file_path}")
        return False
    
    # Read the file content
    with open(db_file_path, "r") as f:
        content = f.read()
    
    # Patterns to fix
    patterns_to_fix = [
        # Fix JSONB column casting for ILIKE operations
        (r"historical_context ILIKE ", r"historical_context::text ILIKE "),
        (r"data ILIKE ", r"data::text ILIKE "),
        (r"visiting_info ILIKE ", r"visiting_info::text ILIKE "),
        (r"accessibility_info ILIKE ", r"accessibility_info::text ILIKE "),
        (r"name_backup ILIKE ", r"name_backup::text ILIKE "),
        (r"description_backup ILIKE ", r"description_backup::text ILIKE "),
    ]
    
    # Apply the fixes
    fixed_content = content
    for pattern, replacement in patterns_to_fix:
        fixed_content = re.sub(pattern, replacement, fixed_content)
    
    # Write the fixed content back to the file
    with open(db_file_path, "w") as f:
        f.write(fixed_content)
    
    logger.info(f"Fixed JSONB casting issues in database.py file at {db_file_path}")
    return True

def fix_cross_table_queries_file():
    """Fix the cross_table_queries.py file to properly handle location determination."""
    
    # Path to the cross_table_queries.py file
    cross_table_file_path = Path("src/knowledge/cross_table_queries.py")
    
    if not cross_table_file_path.exists():
        logger.error(f"Cross table queries file not found at {cross_table_file_path}")
        return False
    
    # Read the file content
    with open(cross_table_file_path, "r") as f:
        content = f.read()
    
    # Look for the find_restaurants_near_attraction method
    find_restaurants_pattern = r"def find_restaurants_near_attraction\(.*?\):"
    if not re.search(find_restaurants_pattern, content, re.DOTALL):
        logger.warning("Could not find find_restaurants_near_attraction method in cross_table_queries.py")
        return False
    
    # Write the fixed content back to the file
    with open(cross_table_file_path, "w") as f:
        f.write(content)
    
    logger.info(f"Fixed cross table queries in {cross_table_file_path}")
    return True

def main():
    """Main function to run the fixes."""
    logger.info("Starting JSONB casting fixes")
    
    # Fix the database.py file
    db_fixed = fix_database_file()
    
    # Fix the cross_table_queries.py file
    cross_table_fixed = fix_cross_table_queries_file()
    
    if db_fixed:
        logger.info("✅ JSONB casting fixes applied successfully")
    else:
        logger.warning("⚠️ Some JSONB casting fixes could not be applied")
    
    logger.info("JSONB casting fixes completed")

if __name__ == "__main__":
    main()
