#!/usr/bin/env python3
"""
Data Loading Verification Script for Egypt Tourism Chatbot

This script verifies that data has been correctly loaded into the PostgreSQL database
by querying each table and displaying summary statistics.
"""
import sys
import time
from pathlib import Path
from typing import Dict, List, Any

# Add the src directory to the Python path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.logger import get_logger
from src.knowledge.database import DatabaseManager, DatabaseType

# Set up logging
logger = get_logger(__name__)

def count_entities(db_manager: DatabaseManager, table_name: str) -> int:
    """
    Count the number of entities in a table.
    
    Args:
        db_manager: Database manager instance
        table_name: Name of the table to count
        
    Returns:
        Number of entities in the table
    """
    query = f"SELECT COUNT(*) as count FROM {table_name}"
    result = db_manager.execute_query(query)
    return result[0]['count'] if result else 0

def get_entity_sample(db_manager: DatabaseManager, table_name: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Get a sample of entities from a table.
    
    Args:
        db_manager: Database manager instance
        table_name: Name of the table to sample
        limit: Maximum number of entities to return
        
    Returns:
        List of entities
    """
    query = f"SELECT id, name_en, name_ar FROM {table_name} LIMIT {limit}"
    return db_manager.execute_query(query) or []

def check_embeddings(db_manager: DatabaseManager, table_name: str) -> Dict[str, Any]:
    """
    Check if embeddings are present in a table.
    
    Args:
        db_manager: Database manager instance
        table_name: Name of the table to check
        
    Returns:
        Dictionary with embedding statistics
    """
    # Count total rows
    total_query = f"SELECT COUNT(*) as count FROM {table_name}"
    total_result = db_manager.execute_query(total_query)
    total = total_result[0]['count'] if total_result else 0
    
    # Count rows with embeddings
    with_embedding_query = f"SELECT COUNT(*) as count FROM {table_name} WHERE embedding IS NOT NULL"
    with_embedding_result = db_manager.execute_query(with_embedding_query)
    with_embedding = with_embedding_result[0]['count'] if with_embedding_result else 0
    
    return {
        'total': total,
        'with_embedding': with_embedding,
        'percentage': round(with_embedding / total * 100, 2) if total > 0 else 0
    }

def verify_vector_search(db_manager: DatabaseManager, table_name: str, query_text: str) -> List[Dict[str, Any]]:
    """
    Verify vector search functionality by performing a search.
    
    Args:
        db_manager: Database manager instance
        table_name: Name of the table to search
        query_text: Text to search for
        
    Returns:
        List of search results
    """
    # Generate embedding for query text
    embedding = db_manager.text_to_embedding(query_text)
    
    # Perform vector search
    query = f"""
        SELECT id, name_en, name_ar, embedding <-> %s::vector AS distance
        FROM {table_name}
        WHERE embedding IS NOT NULL
        ORDER BY distance ASC
        LIMIT 5
    """
    
    return db_manager.execute_query(query, (embedding,)) or []

def main():
    """Main function to verify data loading."""
    start_time = time.time()
    logger.info("Starting data verification process...")
    
    # Initialize database manager
    db_manager = DatabaseManager()
    
    # Ensure we're using PostgreSQL
    if db_manager.db_type != DatabaseType.POSTGRES:
        logger.error(f"PostgreSQL database not configured. Current type: {db_manager.db_type}")
        return
        
    logger.info("Connected to PostgreSQL database")
    
    # Define tables to verify
    tables = ['cities', 'attractions', 'accommodations', 'restaurants']
    
    # Verify each table
    try:
        for table in tables:
            # Count entities
            count = count_entities(db_manager, table)
            logger.info(f"Table '{table}' contains {count} entities")
            
            # Get sample entities
            sample = get_entity_sample(db_manager, table)
            logger.info(f"Sample entities from '{table}':")
            for entity in sample:
                logger.info(f"  - {entity['id']}: {entity['name_en']} ({entity.get('name_ar', 'No Arabic name')})")
            
            # Check embeddings
            embedding_stats = check_embeddings(db_manager, table)
            logger.info(f"Embedding statistics for '{table}':")
            logger.info(f"  - Total entities: {embedding_stats['total']}")
            logger.info(f"  - Entities with embeddings: {embedding_stats['with_embedding']}")
            logger.info(f"  - Percentage with embeddings: {embedding_stats['percentage']}%")
            
            # Verify vector search
            if count > 0:
                search_query = "Egypt"
                if table == 'restaurants':
                    search_query = "Traditional Egyptian food"
                elif table == 'accommodations':
                    search_query = "Luxury hotel with Nile view"
                elif table == 'attractions':
                    search_query = "Ancient pyramids"
                elif table == 'cities':
                    search_query = "Historical city with temples"
                
                logger.info(f"Testing vector search on '{table}' with query: '{search_query}'")
                search_results = verify_vector_search(db_manager, table, search_query)
                
                if search_results:
                    logger.info(f"Vector search results for '{search_query}' in '{table}':")
                    for result in search_results:
                        logger.info(f"  - {result['id']}: {result['name_en']} (distance: {result['distance']:.4f})")
                else:
                    logger.warning(f"No vector search results found for '{search_query}' in '{table}'")
            
            logger.info("-" * 50)
        
        elapsed_time = time.time() - start_time
        logger.info(f"Data verification completed in {elapsed_time:.2f} seconds")
        
    except Exception as e:
        logger.error(f"Error during data verification: {str(e)}")
    finally:
        db_manager.close()

if __name__ == '__main__':
    main()
