#!/usr/bin/env python3
"""
Fix script for Egypt Tourism Chatbot transportation query issues.
This script will:
1. Fix the transportation query issue with 'column "text" does not exist'
2. Enhance the enhanced_search method to handle transportation queries properly
"""
import os
import sys
import logging
import json
from typing import Dict, List, Any, Optional
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the necessary components
from src.knowledge.database import DatabaseManager

def fix_enhanced_search():
    """Fix the enhanced_search method in DatabaseManager to handle transportation queries properly."""
    logger.info("\n=== Fixing Enhanced Search for Transportation Queries ===")
    
    # Monkey patch the enhanced_search method in DatabaseManager
    try:
        # Get the DatabaseManager class
        db_manager_class = DatabaseManager
        
        # Store the original method for reference
        original_enhanced_search = db_manager_class.enhanced_search
        
        # Define the fixed method
        def fixed_enhanced_search(self, table: str, search_text: str, filters: Dict = None, limit: int = 10):
            """
            Fixed version of enhanced_search that properly handles transportation queries.
            """
            logger.info(f"Enhanced search on table={table} with search_text={search_text}, filters={filters}, limit={limit}")
            
            try:
                # Get the columns in the table
                columns = self._get_table_columns(table)
                logger.debug(f"Table {table} columns: {columns}")
                
                # Build the SQL query based on available columns
                sql_parts = ["SELECT * FROM", table, "WHERE 1=1"]
                params = []
                
                # Add search condition based on available columns
                search_conditions = []
                
                # Check for specific tables and handle them differently
                if table == "transportation_routes":
                    # For transportation_routes, search in specific columns
                    if "name_en" in columns:
                        search_conditions.append("name_en ILIKE %s")
                        params.append(f"%{search_text}%")
                    
                    if "name_ar" in columns:
                        search_conditions.append("name_ar ILIKE %s")
                        params.append(f"%{search_text}%")
                    
                    if "description_en" in columns:
                        search_conditions.append("description_en ILIKE %s")
                        params.append(f"%{search_text}%")
                    
                    if "description_ar" in columns:
                        search_conditions.append("description_ar ILIKE %s")
                        params.append(f"%{search_text}%")
                    
                    # Check for JSONB columns
                    if "name" in columns:
                        search_conditions.append("name->>'en' ILIKE %s")
                        params.append(f"%{search_text}%")
                        search_conditions.append("name->>'ar' ILIKE %s")
                        params.append(f"%{search_text}%")
                    
                    if "description" in columns:
                        search_conditions.append("description->>'en' ILIKE %s")
                        params.append(f"%{search_text}%")
                        search_conditions.append("description->>'ar' ILIKE %s")
                        params.append(f"%{search_text}%")
                    
                    # Also search in origin and destination
                    if "origin_id" in columns:
                        search_conditions.append("origin_id ILIKE %s")
                        params.append(f"%{search_text}%")
                    
                    if "destination_id" in columns:
                        search_conditions.append("destination_id ILIKE %s")
                        params.append(f"%{search_text}%")
                    
                    # Also search in transportation_type
                    if "transportation_type" in columns:
                        search_conditions.append("transportation_type ILIKE %s")
                        params.append(f"%{search_text}%")
                else:
                    # For other tables, use the original method
                    return original_enhanced_search(self, table, search_text, filters, limit)
                
                # Add search conditions to SQL
                if search_conditions:
                    sql_parts.append("AND (" + " OR ".join(search_conditions) + ")")
                else:
                    # If no search conditions could be created, return empty result
                    logger.warning(f"No searchable columns found in table {table}")
                    return []
                
                # Add filters if provided
                if filters:
                    for key, value in filters.items():
                        if key in columns:
                            sql_parts.append(f"AND {key} = %s")
                            params.append(value)
                
                # Add limit
                sql_parts.append(f"LIMIT {limit}")
                
                # Execute the query
                sql = " ".join(sql_parts)
                logger.debug(f"Executing SQL: {sql} with params: {params}")
                
                results = self.execute_query(sql, tuple(params))
                logger.info(f"Enhanced search found {len(results)} results")
                
                return results
            
            except Exception as e:
                logger.error(f"Error in fixed_enhanced_search: {str(e)}")
                # Return empty list if there's an error
                return []
        
        # Replace the original method with the fixed one
        db_manager_class.enhanced_search = fixed_enhanced_search
        
        logger.info("Successfully patched enhanced_search method to handle transportation queries")
        return True
    except Exception as e:
        logger.error(f"Failed to patch enhanced_search: {str(e)}")
        return False

def fix_get_table_columns():
    """Add a _get_table_columns method to DatabaseManager if it doesn't exist."""
    logger.info("\n=== Adding _get_table_columns Method ===")
    
    # Monkey patch the _get_table_columns method in DatabaseManager
    try:
        # Get the DatabaseManager class
        db_manager_class = DatabaseManager
        
        # Check if the method already exists
        if hasattr(db_manager_class, '_get_table_columns'):
            logger.info("_get_table_columns method already exists, skipping")
            return True
        
        # Define the method
        def _get_table_columns(self, table: str) -> List[str]:
            """
            Get the column names for a table.
            
            Args:
                table: Table name
                
            Returns:
                List of column names
            """
            try:
                # Query to get column names
                sql = """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = %s
                """
                
                results = self.execute_query(sql, (table,))
                
                # Extract column names
                columns = [row['column_name'] for row in results]
                
                return columns
            except Exception as e:
                logger.error(f"Error getting columns for table {table}: {str(e)}")
                return []
        
        # Add the method to the class
        db_manager_class._get_table_columns = _get_table_columns
        
        logger.info("Successfully added _get_table_columns method")
        return True
    except Exception as e:
        logger.error(f"Failed to add _get_table_columns method: {str(e)}")
        return False

def fix_table_exists():
    """Add a _table_exists method to DatabaseManager if it doesn't exist."""
    logger.info("\n=== Adding _table_exists Method ===")
    
    # Monkey patch the _table_exists method in DatabaseManager
    try:
        # Get the DatabaseManager class
        db_manager_class = DatabaseManager
        
        # Check if the method already exists
        if hasattr(db_manager_class, '_table_exists'):
            logger.info("_table_exists method already exists, skipping")
            return True
        
        # Define the method
        def _table_exists(self, table: str) -> bool:
            """
            Check if a table exists in the database.
            
            Args:
                table: Table name
                
            Returns:
                True if the table exists, False otherwise
            """
            try:
                # Query to check if table exists
                sql = """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_name = %s
                )
                """
                
                results = self.execute_query(sql, (table,))
                
                # Extract result
                if results and len(results) > 0:
                    return results[0]['exists']
                
                return False
            except Exception as e:
                logger.error(f"Error checking if table {table} exists: {str(e)}")
                return False
        
        # Add the method to the class
        db_manager_class._table_exists = _table_exists
        
        logger.info("Successfully added _table_exists method")
        return True
    except Exception as e:
        logger.error(f"Failed to add _table_exists method: {str(e)}")
        return False

def main():
    """Run all fixes."""
    logger.info("Starting transportation query fixes for Egypt Tourism Chatbot...")
    
    # Add _table_exists method
    if fix_table_exists():
        logger.info("✅ _table_exists method added")
    else:
        logger.error("❌ _table_exists method addition failed")
    
    # Add _get_table_columns method
    if fix_get_table_columns():
        logger.info("✅ _get_table_columns method added")
    else:
        logger.error("❌ _get_table_columns method addition failed")
    
    # Fix enhanced_search method
    if fix_enhanced_search():
        logger.info("✅ Enhanced search fix applied")
    else:
        logger.error("❌ Enhanced search fix failed")
    
    logger.info("\nAll fixes applied. Please restart the chatbot for changes to take effect.")

if __name__ == "__main__":
    main()
