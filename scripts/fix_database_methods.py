#!/usr/bin/env python3
"""
Script to fix database.py methods to ensure proper PostgreSQL support.
This script will update search_restaurants, get_restaurant, search_hotels, and 
get_accommodation methods to support PostgreSQL correctly.
"""

import re
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Path to the database.py file
DATABASE_PATH = os.path.join("src", "knowledge", "database.py")

def read_file(file_path):
    """Read file content."""
    try:
        with open(file_path, "r") as file:
            return file.read()
        
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return None

def write_file(file_path, content):
    """Write content to file."""
    try:
        with open(file_path, "w") as file:
            file.write(content)
        logger.info(f"Successfully updated {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error writing to file {file_path}: {e}")
        return False

def create_postgres_method(original_method_name, entity_type):
    """Create PostgreSQL-specific implementation based on entity type."""
    method_name = f"_{original_method_name}_postgres"
    
    if "search" in original_method_name:
        # For search methods
        return f"""
    def {method_name}(self, query=None, limit=10, offset=0):
        # Search {entity_type}s in PostgreSQL database.
        table_name = "{entity_type}s"
        if not self._postgres_table_exists(table_name):
            logger.warning(f"Table {{table_name}} does not exist in PostgreSQL database")
            return []
            
        try:
            query_tuple = self._build_postgres_query(table_name, query, limit, offset)
            sql_query, params = query_tuple
            
            results = self.execute_postgres_query(sql_query, params)
            return results
            
        except Exception as e:
            logger.error(f"Error searching {entity_type}s in PostgreSQL: {{e}}")
            return []
"""
    else:
        # For get methods
        id_field = f"{entity_type}_id"
        return f"""
    def {method_name}(self, {id_field}):
        # Get {entity_type} by ID from PostgreSQL database.
        table_name = "{entity_type}s"
        if not self._postgres_table_exists(table_name):
            logger.warning(f"Table {{table_name}} does not exist in PostgreSQL database")
            return None
            
        try:
            sql_query = f"SELECT * FROM {{table_name}} WHERE id = %s"
            params = [{id_field}]
            
            results = self.execute_postgres_query(sql_query, params)
            return results[0] if results else None
            
        except Exception as e:
            logger.error(f"Error getting {entity_type} by ID in PostgreSQL: {{e}}")
            return None
"""

def update_method(content, method_name, entity_type):
    """Update method to check database type and call appropriate implementation."""
    # Find the method pattern
    method_pattern = rf"def {method_name}\(self, (.*?)\):(.*?)(?=\n    def|\Z)"
    method_match = re.search(method_pattern, content, re.DOTALL)
    
    if not method_match:
        logger.error(f"Could not find method {method_name}")
        return content
    
    # Extract method arguments and body
    args = method_match.group(1)
    current_body = method_match.group(2)
    
    # Check if method already checks db_type
    if "if self.db_type == DatabaseType.POSTGRES" in current_body:
        logger.info(f"Method {method_name} already has PostgreSQL support")
        return content
    
    # Create new method body that checks db_type
    new_body = f"""
        # Method to {method_name.replace('_', ' ')}.
        if self.db_type == DatabaseType.POSTGRES:
            return self._{method_name}_postgres({', '.join(arg.split(':')[0].strip() for arg in args.split(','))})
        else:
            # Use existing SQLite implementation
            logger.debug(f"Using SQLite implementation for {method_name}")
            {current_body.strip()}
    """
    
    # Replace old method with new one
    new_method = f"def {method_name}(self, {args}):{new_body}"
    updated_content = re.sub(method_pattern, new_method, content, flags=re.DOTALL)
    
    return updated_content

def fix_database_methods():
    """Main function to fix database methods."""
    # Read database.py file
    content = read_file(DATABASE_PATH)
    if not content:
        return False
    
    # Methods to update
    methods_to_update = [
        ("search_restaurants", "restaurant"),
        ("get_restaurant", "restaurant"),
        ("search_hotels", "hotel"),
        ("get_accommodation", "hotel")
    ]
    
    # Update methods
    for method_name, entity_type in methods_to_update:
        # First, add PostgreSQL-specific method if not exists
        postgres_method_name = f"_{method_name}_postgres"
        if postgres_method_name not in content:
            postgres_method = create_postgres_method(method_name, entity_type)
            # Find position to insert (before the method to update)
            method_pos = content.find(f"def {method_name}(")
            if method_pos == -1:
                logger.error(f"Could not find method {method_name}")
                continue
                
            # Insert the PostgreSQL method before the main method
            content = content[:method_pos] + postgres_method + content[method_pos:]
            logger.info(f"Added PostgreSQL-specific method {postgres_method_name}")
        
        # Now update the main method to check db_type
        content = update_method(content, method_name, entity_type)
        logger.info(f"Updated method {method_name}")
    
    # Write updated content back to file
    return write_file(DATABASE_PATH, content)

if __name__ == "__main__":
    logger.info("Starting database methods fix")
    if fix_database_methods():
        logger.info("Successfully fixed database methods")
    else:
        logger.error("Failed to fix database methods") 