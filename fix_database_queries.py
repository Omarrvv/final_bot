#!/usr/bin/env python3
"""
Fix script for database query issues in the Egypt Tourism Chatbot.
This script patches the database.py file to fix column name issues.
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
    """Fix the database.py file to use correct JSONB column references."""
    
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
        # Fix name_en references to use JSONB syntax
        (r"ORDER BY name_en", r"ORDER BY name->>'en'"),
        (r"WHERE name_en = ", r"WHERE name->>'en' = "),
        (r"WHERE name_en LIKE ", r"WHERE name->>'en' LIKE "),
        (r"WHERE name_en ILIKE ", r"WHERE name->>'en' ILIKE "),
        (r"AND name_en = ", r"AND name->>'en' = "),
        (r"AND name_en LIKE ", r"AND name->>'en' LIKE "),
        (r"AND name_en ILIKE ", r"AND name->>'en' ILIKE "),
        (r"OR name_en LIKE ", r"OR name->>'en' LIKE "),
        (r"OR name_en ILIKE ", r"OR name->>'en' ILIKE "),
        
        # Fix name_ar references
        (r"ORDER BY name_ar", r"ORDER BY name->>'ar'"),
        (r"WHERE name_ar = ", r"WHERE name->>'ar' = "),
        (r"WHERE name_ar LIKE ", r"WHERE name->>'ar' LIKE "),
        (r"WHERE name_ar ILIKE ", r"WHERE name->>'ar' ILIKE "),
        (r"AND name_ar = ", r"AND name->>'ar' = "),
        (r"AND name_ar LIKE ", r"AND name->>'ar' LIKE "),
        (r"AND name_ar ILIKE ", r"AND name->>'ar' ILIKE "),
        (r"OR name_ar LIKE ", r"OR name->>'ar' LIKE "),
        (r"OR name_ar ILIKE ", r"OR name->>'ar' ILIKE "),
        
        # Fix description_en references
        (r"ORDER BY description_en", r"ORDER BY description->>'en'"),
        (r"WHERE description_en = ", r"WHERE description->>'en' = "),
        (r"WHERE description_en LIKE ", r"WHERE description->>'en' LIKE "),
        (r"WHERE description_en ILIKE ", r"WHERE description->>'en' ILIKE "),
        (r"AND description_en = ", r"AND description->>'en' = "),
        (r"AND description_en LIKE ", r"AND description->>'en' LIKE "),
        (r"AND description_en ILIKE ", r"AND description->>'en' ILIKE "),
        (r"OR description_en LIKE ", r"OR description->>'en' LIKE "),
        (r"OR description_en ILIKE ", r"OR description->>'en' ILIKE "),
        
        # Fix description_ar references
        (r"ORDER BY description_ar", r"ORDER BY description->>'ar'"),
        (r"WHERE description_ar = ", r"WHERE description->>'ar' = "),
        (r"WHERE description_ar LIKE ", r"WHERE description->>'ar' LIKE "),
        (r"WHERE description_ar ILIKE ", r"WHERE description->>'ar' ILIKE "),
        (r"AND description_ar = ", r"AND description->>'ar' = "),
        (r"AND description_ar LIKE ", r"AND description->>'ar' LIKE "),
        (r"AND description_ar ILIKE ", r"AND description->>'ar' ILIKE "),
        (r"OR description_ar LIKE ", r"OR description->>'ar' LIKE "),
        (r"OR description_ar ILIKE ", r"OR description->>'ar' ILIKE "),
        
        # Fix historical_context references if it's a JSONB column
        (r"historical_context ILIKE ", r"historical_context::text ILIKE "),
        (r"historical_context LIKE ", r"historical_context::text LIKE "),
    ]
    
    # Apply the fixes
    fixed_content = content
    for pattern, replacement in patterns_to_fix:
        fixed_content = re.sub(pattern, replacement, fixed_content)
    
    # Write the fixed content back to the file
    with open(db_file_path, "w") as f:
        f.write(fixed_content)
    
    logger.info(f"Fixed database.py file at {db_file_path}")
    return True

def fix_postgres_database_file():
    """Fix the postgres_database.py file to use correct JSONB column references."""
    
    # Path to the postgres_database.py file
    db_file_path = Path("src/utils/postgres_database.py")
    
    if not db_file_path.exists():
        logger.error(f"Postgres database file not found at {db_file_path}")
        return False
    
    # Read the file content
    with open(db_file_path, "r") as f:
        content = f.read()
    
    # Patterns to fix
    patterns_to_fix = [
        # Fix name_en references to use JSONB syntax
        (r"name_en ILIKE %s", r"name->>'en' ILIKE %s"),
        (r"name_ar ILIKE %s", r"name->>'ar' ILIKE %s"),
        (r"ORDER BY name_en", r"ORDER BY name->>'en'"),
    ]
    
    # Apply the fixes
    fixed_content = content
    for pattern, replacement in patterns_to_fix:
        fixed_content = re.sub(pattern, replacement, fixed_content)
    
    # Write the fixed content back to the file
    with open(db_file_path, "w") as f:
        f.write(fixed_content)
    
    logger.info(f"Fixed postgres_database.py file at {db_file_path}")
    return True

def main():
    """Main function to run the fixes."""
    logger.info("Starting database query fixes")
    
    # Fix the database.py file
    db_fixed = fix_database_file()
    
    # Fix the postgres_database.py file
    postgres_fixed = fix_postgres_database_file()
    
    if db_fixed and postgres_fixed:
        logger.info("✅ All fixes applied successfully")
    else:
        logger.warning("⚠️ Some fixes could not be applied")
    
    logger.info("Database query fixes completed")

if __name__ == "__main__":
    main()
