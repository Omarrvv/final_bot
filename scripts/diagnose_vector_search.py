#!/usr/bin/env python3
"""
Diagnostic script for vector search issues.
This script tests different approaches to vector search to identify the issue.
"""

import os
import sys
import json
import logging
import traceback
from typing import List, Dict, Any, Optional

# Add the parent directory to the path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.knowledge.database import DatabaseManager
from src.utils.logger import get_logger

# Configure logging
logger = get_logger(__name__)
logger.setLevel(logging.INFO)

def parse_embedding(embedding_str: str) -> List[float]:
    """Parse embedding from string to list of floats."""
    logger.info(f"Parsing embedding of type: {type(embedding_str)}")
    
    if isinstance(embedding_str, str):
        try:
            # Try to parse as JSON first
            embedding = json.loads(embedding_str)
            logger.info(f"Successfully parsed embedding using JSON: {len(embedding)} elements")
            return embedding
        except json.JSONDecodeError:
            # If that fails, try manual parsing
            logger.info("JSON parsing failed, trying manual parsing")
            # Remove brackets and split by comma
            embedding_values = embedding_str.strip('[]').split(',')
            embedding = [float(val) for val in embedding_values]
            logger.info(f"Successfully parsed embedding manually: {len(embedding)} elements")
            return embedding
    else:
        logger.info(f"Embedding is not a string but a {type(embedding_str)}")
        return embedding_str

def test_vector_search_with_string(db: DatabaseManager) -> bool:
    """Test vector search with string embedding."""
    logger.info("Testing vector search with string embedding...")
    
    # Get a sample embedding as string
    embedding_query = """
        SELECT embedding::text 
        FROM attractions 
        WHERE embedding IS NOT NULL 
        LIMIT 1
    """
    embedding_result = db.execute_query(embedding_query)
    if not embedding_result:
        logger.error("No embeddings found in the database")
        return False
    
    embedding_str = embedding_result[0]['embedding']
    logger.info(f"Got embedding string of length: {len(embedding_str)}")
    
    # Try to use the string directly
    try:
        logger.info("Trying to use the embedding string directly...")
        results = db.vector_search_attractions(embedding_str, limit=5)
        logger.info(f"Direct string usage results: {len(results) if results else 0}")
    except Exception as e:
        logger.error(f"Error using embedding string directly: {e}")
        logger.error(traceback.format_exc())
    
    # Parse the embedding and try again
    try:
        logger.info("Parsing embedding string to list...")
        embedding = parse_embedding(embedding_str)
        logger.info(f"Parsed embedding has {len(embedding)} elements")
        
        logger.info("Trying vector search with parsed embedding...")
        results = db.vector_search_attractions(embedding, limit=5)
        logger.info(f"Parsed embedding results: {len(results) if results else 0}")
        
        if results:
            logger.info("Vector search with parsed embedding succeeded!")
            return True
        else:
            logger.error("Vector search with parsed embedding returned no results")
            return False
    except Exception as e:
        logger.error(f"Error using parsed embedding: {e}")
        logger.error(traceback.format_exc())
        return False

def test_vector_search_with_array(db: DatabaseManager) -> bool:
    """Test vector search with array casting."""
    logger.info("Testing vector search with array casting...")
    
    try:
        # Get a sample embedding and cast to array
        embedding_query = """
            SELECT id, embedding::float8[] as embedding_array
            FROM attractions 
            WHERE embedding IS NOT NULL 
            LIMIT 1
        """
        
        logger.info("Executing query to get embedding as array...")
        embedding_result = db.execute_query(embedding_query)
        if not embedding_result:
            logger.error("No embeddings found or cannot cast to array")
            return False
        
        embedding_array = embedding_result[0]['embedding_array']
        logger.info(f"Got embedding array of type: {type(embedding_array)}")
        
        if isinstance(embedding_array, str):
            logger.info("Parsing embedding array string...")
            embedding_array = parse_embedding(embedding_array)
        
        logger.info(f"Using embedding array with {len(embedding_array) if isinstance(embedding_array, list) else 'unknown'} elements")
        
        # Try vector search with the array
        results = db.vector_search_attractions(embedding_array, limit=5)
        logger.info(f"Array embedding results: {len(results) if results else 0}")
        
        if results:
            logger.info("Vector search with array embedding succeeded!")
            return True
        else:
            logger.error("Vector search with array embedding returned no results")
            return False
    except Exception as e:
        logger.error(f"Error in array embedding test: {e}")
        logger.error(traceback.format_exc())
        return False

def test_raw_sql_vector_search(db: DatabaseManager) -> bool:
    """Test vector search with raw SQL."""
    logger.info("Testing vector search with raw SQL...")
    
    try:
        # Get a sample embedding
        embedding_query = """
            SELECT id, embedding 
            FROM attractions 
            WHERE embedding IS NOT NULL 
            LIMIT 1
        """
        
        embedding_result = db.execute_query(embedding_query)
        if not embedding_result:
            logger.error("No embeddings found in the database")
            return False
        
        embedding_id = embedding_result[0]['id']
        logger.info(f"Using embedding from attraction: {embedding_id}")
        
        # Use the embedding directly in a SQL query
        raw_sql = """
            SET hnsw.ef_search = 100;
            SELECT *, embedding <-> (SELECT embedding FROM attractions WHERE id = %s) AS distance
            FROM attractions
            WHERE id != %s
            ORDER BY distance
            LIMIT 5
        """
        
        logger.info("Executing raw SQL vector search...")
        results = db.execute_query(raw_sql, (embedding_id, embedding_id))
        logger.info(f"Raw SQL results: {len(results) if results else 0}")
        
        if results:
            logger.info("Raw SQL vector search succeeded!")
            return True
        else:
            logger.error("Raw SQL vector search returned no results")
            return False
    except Exception as e:
        logger.error(f"Error in raw SQL test: {e}")
        logger.error(traceback.format_exc())
        return False

def fix_vector_search_method(db: DatabaseManager) -> bool:
    """Fix the vector_search_attractions method."""
    logger.info("Attempting to fix vector_search_attractions method...")
    
    # Test the fixed method
    try:
        # Get a sample embedding
        embedding_query = """
            SELECT embedding::text 
            FROM attractions 
            WHERE embedding IS NOT NULL 
            LIMIT 1
        """
        embedding_result = db.execute_query(embedding_query)
        if not embedding_result:
            logger.error("No embeddings found in the database")
            return False
        
        embedding_str = embedding_result[0]['embedding']
        embedding = parse_embedding(embedding_str)
        
        # Define a fixed vector search method
        def fixed_vector_search(embedding_list, limit=5):
            """Fixed vector search method."""
            # Convert embedding list to string format expected by pgvector
            embedding_str = str(embedding_list).replace(' ', '')
            
            # Use raw SQL to perform the search
            sql = """
                SET hnsw.ef_search = 100;
                SELECT *, embedding <-> %s::vector AS distance
                FROM attractions
                WHERE 1=1
                ORDER BY distance
                LIMIT %s
            """
            
            return db.execute_query(sql, (embedding_str, limit))
        
        # Test the fixed method
        logger.info("Testing fixed vector search method...")
        results = fixed_vector_search(embedding, limit=5)
        logger.info(f"Fixed method results: {len(results) if results else 0}")
        
        if results:
            logger.info("Fixed vector search method succeeded!")
            return True
        else:
            logger.error("Fixed vector search method returned no results")
            return False
    except Exception as e:
        logger.error(f"Error in fixed method test: {e}")
        logger.error(traceback.format_exc())
        return False

def main():
    """Main function to run the diagnostic tests."""
    # Get database URI from environment variable
    database_uri = os.environ.get("POSTGRES_URI")
    if not database_uri:
        logger.error("POSTGRES_URI environment variable not set")
        sys.exit(1)
    
    # Initialize database manager
    db = DatabaseManager(database_uri=database_uri)
    
    # Run diagnostic tests
    logger.info("Starting vector search diagnostic tests...")
    
    tests = [
        test_vector_search_with_string,
        test_vector_search_with_array,
        test_raw_sql_vector_search,
        fix_vector_search_method
    ]
    
    success = False
    for test in tests:
        try:
            if test(db):
                success = True
                logger.info(f"Test {test.__name__} succeeded!")
                break
            else:
                logger.error(f"Test {test.__name__} failed")
        except Exception as e:
            logger.error(f"Error in test {test.__name__}: {e}")
            logger.error(traceback.format_exc())
    
    # Close database connection
    db.close()
    
    if success:
        logger.info("Diagnostic tests found a working solution!")
        sys.exit(0)
    else:
        logger.error("All diagnostic tests failed. Further investigation needed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
