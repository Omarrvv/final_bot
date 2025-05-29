#!/usr/bin/env python3
"""
Fix script for cross-table query implementation issues in the Egypt Tourism Chatbot.
This script patches the cross_table_queries.py file to improve location determination
and fix issues with finding attractions, restaurants, hotels, and events.
"""

import os
import sys
import re
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    
    # Fix 1: Improve attraction search in find_restaurants_near_attraction
    # Find the section where attraction is searched by name
    attraction_search_pattern = r"(# Search for attraction by name\s+attractions = self\.db_manager\.search_attractions\(\s+query=\{\"text\": attraction_name\},\s+limit=1\s+\))"
    
    # Replace with improved search that handles JSONB columns
    attraction_search_replacement = r"""# Search for attraction by name
                # Try multiple search approaches for finding the attraction
                attractions = None
                
                # First try: Direct name match
                try:
                    attractions = self.db_manager.search_attractions(
                        query={"text": attraction_name},
                        limit=1
                    )
                except Exception as e:
                    logger.warning(f"Error searching attraction by text: {str(e)}")
                
                # Second try: Use enhanced search if available
                if not attractions or len(attractions) == 0:
                    try:
                        if hasattr(self.db_manager, 'enhanced_search'):
                            logger.info(f"Using enhanced search for attraction: {attraction_name}")
                            attractions = self.db_manager.enhanced_search(
                                table="attractions",
                                search_text=attraction_name,
                                limit=1
                            )
                    except Exception as e:
                        logger.warning(f"Error using enhanced search for attraction: {str(e)}")
                
                # Third try: Direct SQL query as fallback
                if not attractions or len(attractions) == 0:
                    try:
                        logger.info(f"Using direct SQL query for attraction: {attraction_name}")
                        attractions = self.db_manager.execute_postgres_query(
                            "SELECT * FROM attractions WHERE name->>'en' ILIKE %s OR name->>'ar' ILIKE %s LIMIT 1",
                            (f"%{attraction_name}%", f"%{attraction_name}%")
                        )
                    except Exception as e:
                        logger.warning(f"Error using direct SQL query for attraction: {str(e)}")"""
    
    # Apply the fix
    content = re.sub(attraction_search_pattern, attraction_search_replacement, content)
    
    # Fix 2: Improve location determination in find_restaurants_near_attraction
    # Find the section where location is determined
    location_determination_pattern = r"(# Extract location information\s+location = None\s+city_name = None\s+region_name = None\s+coordinates = None)"
    
    # Replace with improved location determination
    location_determination_replacement = r"""# Extract location information
            location = None
            city_name = None
            region_name = None
            coordinates = None
            
            # Set default location if attraction_name is provided but no attraction found
            if attraction_name and not attraction:
                logger.info(f"No attraction found for '{attraction_name}', using it as location")
                location = attraction_name
                # Try to extract city name from attraction name
                if "in " in attraction_name.lower():
                    city_candidate = attraction_name.lower().split("in ")[1].strip()
                    if city_candidate:
                        city_name = city_candidate
                        logger.info(f"Extracted city name from attraction name: {city_name}")"""
    
    # Apply the fix
    content = re.sub(location_determination_pattern, location_determination_replacement, content)
    
    # Fix 3: Improve city search in find_restaurants_near_attraction
    # Find the section where city search is performed
    city_search_pattern = r"(# First try: Search by city name if available\s+if city_name:\s+logger\.info\(f\"Searching restaurants by city name: \{city_name\}\"\)\s+try:\s+city_results = self\.db_manager\.search_restaurants\(\s+query=\{\"city\": city_name\},\s+limit=limit\s+\))"
    
    # Replace with improved city search
    city_search_replacement = r"""# First try: Search by city name if available
                if city_name:
                    logger.info(f"Searching restaurants by city name: {city_name}")
                    try:
                        # Try multiple approaches for city search
                        city_results = None
                        
                        # First approach: Direct city match
                        try:
                            city_results = self.db_manager.search_restaurants(
                                query={"city": city_name},
                                limit=limit
                            )
                        except Exception as e:
                            logger.warning(f"Error searching restaurants by city (direct): {str(e)}")
                        
                        # Second approach: Try with city_id if no results
                        if not city_results or len(city_results) == 0:
                            try:
                                # Find city ID first
                                cities = self.db_manager.execute_postgres_query(
                                    "SELECT id FROM cities WHERE name->>'en' ILIKE %s OR name->>'ar' ILIKE %s LIMIT 1",
                                    (f"%{city_name}%", f"%{city_name}%")
                                )
                                if cities and len(cities) > 0:
                                    city_id = cities[0].get('id')
                                    logger.info(f"Found city ID {city_id} for {city_name}")
                                    city_results = self.db_manager.search_restaurants(
                                        query={"city_id": city_id},
                                        limit=limit
                                    )
                            except Exception as e:
                                logger.warning(f"Error searching restaurants by city_id: {str(e)}")
                        
                        # Third approach: Direct SQL query as fallback
                        if not city_results or len(city_results) == 0:
                            try:
                                logger.info(f"Using direct SQL query for restaurants in {city_name}")
                                city_results = self.db_manager.execute_postgres_query(
                                    "SELECT * FROM restaurants WHERE city_id IN (SELECT id FROM cities WHERE name->>'en' ILIKE %s OR name->>'ar' ILIKE %s) LIMIT %s",
                                    (f"%{city_name}%", f"%{city_name}%", limit)
                                )
                            except Exception as e:
                                logger.warning(f"Error using direct SQL query for restaurants: {str(e)}")"""
    
    # Apply the fix
    content = re.sub(city_search_pattern, city_search_replacement, content)
    
    # Write the fixed content back to the file
    with open(cross_table_file_path, "w") as f:
        f.write(content)
    
    logger.info(f"Fixed cross table queries in {cross_table_file_path}")
    return True

def main():
    """Main function to run the fixes."""
    logger.info("Starting cross-table query implementation fixes")
    
    # Fix the cross_table_queries.py file
    cross_table_fixed = fix_cross_table_queries_file()
    
    if cross_table_fixed:
        logger.info("✅ Cross-table query implementation fixes applied successfully")
    else:
        logger.warning("⚠️ Some cross-table query implementation fixes could not be applied")
    
    logger.info("Cross-table query implementation fixes completed")

if __name__ == "__main__":
    main()
