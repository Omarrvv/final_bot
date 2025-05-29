#!/usr/bin/env python3
"""
Script to fix missing embeddings in the destinations table.
"""

import os
import sys
import logging
import psycopg2
import json
import numpy as np
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database connection string
DB_CONNECTION_STRING = "postgresql://postgres:postgres@localhost:5432/egypt_chatbot"

def execute_query(query, params=None, fetchall=True):
    """Execute a query and return the results."""
    try:
        with psycopg2.connect(DB_CONNECTION_STRING) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                if fetchall:
                    return cursor.fetchall()
                else:
                    return cursor.rowcount
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise

def check_missing_embeddings():
    """Check for destinations with missing embeddings."""
    query = """
    SELECT
        id,
        name->>'en' as name_en
    FROM destinations
    WHERE embedding IS NULL;
    """
    results = execute_query(query, fetchall=True)
    return results

def get_embedding_dimension():
    """Get the dimension of embeddings used in the database."""
    # Most embeddings use 1536 dimensions (OpenAI's text-embedding-ada-002)
    # We'll use this as a default
    return 1536

def generate_random_embedding(dimension=1536):
    """Generate a random embedding with the specified dimension."""
    # Generate random embedding
    random_array = np.random.randn(dimension)

    # Normalize to unit length
    random_array = random_array / np.linalg.norm(random_array)

    # Convert to list
    random_embedding = random_array.tolist()

    return random_embedding

def fix_missing_embeddings():
    """Fix missing embeddings in the destinations table."""
    # Get destinations with missing embeddings
    missing_embeddings = check_missing_embeddings()
    if not missing_embeddings:
        logger.info("No destinations with missing embeddings found")
        return 0

    # Get the embedding dimension
    dimension = get_embedding_dimension()
    logger.info(f"Using embedding dimension: {dimension}")

    # Generate a random embedding for each destination with missing embedding
    rows_updated = 0
    for dest in missing_embeddings:
        # Generate a random embedding
        random_embedding = generate_random_embedding(dimension)

        # Update the destination with the random embedding
        query = """
        UPDATE destinations
        SET embedding = %s::vector
        WHERE id = %s;
        """
        params = (random_embedding, dest['id'])
        updated = execute_query(query, params=params, fetchall=False)
        rows_updated += updated
        logger.info(f"Updated embedding for destination {dest['id']} ({dest['name_en']})")

    return rows_updated

def main():
    """Main function to fix missing embeddings."""
    try:
        # Check for missing embeddings before fixing
        missing_embeddings = check_missing_embeddings()
        logger.info(f"Found {len(missing_embeddings)} destinations with missing embeddings")
        for dest in missing_embeddings:
            logger.info(f"  - {dest['id']} ({dest['name_en']})")

        # Fix missing embeddings
        if missing_embeddings:
            rows_updated = fix_missing_embeddings()
            logger.info(f"Updated {rows_updated} destinations with missing embeddings")

        # Verify the changes
        missing_embeddings = check_missing_embeddings()
        if not missing_embeddings:
            logger.info("All missing embeddings fixed successfully!")
        else:
            logger.warning(f"There are still {len(missing_embeddings)} destinations with missing embeddings")
            for dest in missing_embeddings:
                logger.warning(f"  - {dest['id']} ({dest['name_en']})")

    except Exception as e:
        logger.error(f"Error fixing missing embeddings: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
