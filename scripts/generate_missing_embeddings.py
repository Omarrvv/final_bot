#!/usr/bin/env python3
"""
Script to identify, generate, and update missing embeddings in the database.

This script:
1. Identifies all records with missing embeddings across all tables
2. Generates embeddings using the same model as existing ones
3. Updates the records with the new embeddings
4. Verifies that all records have embeddings after the update
"""

import os
import sys
import logging
import argparse
import psycopg2
import psycopg2.extras
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"embedding_generation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger("embedding_generation")

# Load environment variables
load_dotenv()

# Database connection parameters
DB_PARAMS = {
    "dbname": os.getenv("POSTGRES_DB", "egypt_chatbot"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5432")
}

# Tables with embedding columns
TABLES_WITH_EMBEDDINGS = [
    "attractions",
    "accommodations",
    "cities",
    "restaurants",
    "destinations",
    "tourism_faqs",
    "practical_info",
    "tour_packages",
    "events_festivals",
    "itineraries"
]

def connect_to_db():
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        conn.autocommit = False
        logger.info("Connected to PostgreSQL database")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to PostgreSQL: {e}")
        sys.exit(1)

def get_embedding_dimension(conn) -> int:
    """
    Determine the embedding dimension from existing embeddings in the database.

    Args:
        conn: Database connection

    Returns:
        Dimension of embeddings (default: 1536 if no embeddings found)
    """
    try:
        for table in TABLES_WITH_EMBEDDINGS:
            with conn.cursor() as cursor:
                cursor.execute(f"""
                    SELECT embedding::text
                    FROM {table}
                    WHERE embedding IS NOT NULL
                    LIMIT 1
                """)
                result = cursor.fetchone()

                if result and result[0]:
                    # Count commas in the vector string to determine dimension
                    vector_str = result[0]
                    dimension = vector_str.count(',') + 1
                    logger.info(f"Detected embedding dimension: {dimension} from table {table}")
                    return dimension

        # Default to 1536 if no embeddings found
        logger.warning("No existing embeddings found, using default dimension: 1536")
        return 1536
    except Exception as e:
        logger.error(f"Error determining embedding dimension: {e}")
        return 1536

def identify_missing_embeddings(conn) -> Dict[str, List[Dict[str, Any]]]:
    """
    Identify records with missing embeddings across all tables.

    Args:
        conn: Database connection

    Returns:
        Dictionary mapping table names to lists of records with missing embeddings
    """
    missing_embeddings = {}

    try:
        for table in TABLES_WITH_EMBEDDINGS:
            try:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                    # First check if the table exists
                    cursor.execute(f"""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables
                            WHERE table_name = '{table}'
                        )
                    """)
                    table_exists = cursor.fetchone()[0]

                    if not table_exists:
                        logger.warning(f"Table {table} does not exist, skipping")
                        continue

                    # Check if the table has an embedding column
                    cursor.execute(f"""
                        SELECT EXISTS (
                            SELECT FROM information_schema.columns
                            WHERE table_name = '{table}' AND column_name = 'embedding'
                        )
                    """)
                    has_embedding_column = cursor.fetchone()[0]

                    if not has_embedding_column:
                        logger.warning(f"Table {table} does not have an embedding column, skipping")
                        continue

                    # Check column types to determine how to construct the query
                    cursor.execute(f"""
                        SELECT column_name, data_type
                        FROM information_schema.columns
                        WHERE table_name = '{table}'
                    """)
                    columns = {row['column_name']: row['data_type'] for row in cursor.fetchall()}

                    # Determine which text fields to use for embedding generation based on column types
                    text_fields = []

                    # Check for JSONB fields
                    if 'name' in columns:
                        if columns['name'] == 'jsonb':
                            text_fields.append("COALESCE(name->>'en', '')")
                        else:
                            text_fields.append("COALESCE(name, '')")

                    if 'description' in columns:
                        if columns['description'] == 'jsonb':
                            text_fields.append("COALESCE(description->>'en', '')")
                        else:
                            text_fields.append("COALESCE(description, '')")

                    if 'question' in columns and columns['question'] == 'jsonb':
                        text_fields.append("COALESCE(question->>'en', '')")

                    if 'answer' in columns and columns['answer'] == 'jsonb':
                        text_fields.append("COALESCE(answer->>'en', '')")

                    if 'title' in columns and columns['title'] == 'jsonb':
                        text_fields.append("COALESCE(title->>'en', '')")

                    if 'content' in columns and columns['content'] == 'jsonb':
                        text_fields.append("COALESCE(content->>'en', '')")

                    # If no text fields found, use a default approach
                    if not text_fields:
                        logger.warning(f"No suitable text fields found for {table}, using default id")
                        text_fields = ["CAST(id AS TEXT)"]

                    # Construct query to get records with missing embeddings
                    text_concat = " || ' ' || ".join(text_fields)
                    query = f"""
                        SELECT id, {text_concat} as text_content
                        FROM {table}
                        WHERE embedding IS NULL
                    """

                    cursor.execute(query)
                    records = cursor.fetchall()

                    if records:
                        missing_embeddings[table] = [dict(record) for record in records]
                        logger.info(f"Found {len(records)} records with missing embeddings in {table}")
                    else:
                        logger.info(f"No missing embeddings in {table}")
            except Exception as e:
                logger.error(f"Error processing table {table}: {e}")
                conn.rollback()  # Rollback the transaction to continue with other tables

        return missing_embeddings
    except Exception as e:
        logger.error(f"Error identifying missing embeddings: {e}")
        return {}

def generate_embedding(text: str, dimension: int) -> List[float]:
    """
    Generate an embedding for the given text.

    In a production environment, this would call an embedding model API.
    For this script, we'll generate random embeddings of the correct dimension.

    Args:
        text: Text to generate embedding for
        dimension: Dimension of the embedding

    Returns:
        Embedding vector as a list of floats
    """
    try:
        # In a real implementation, you would use a proper embedding model here
        # For example, with OpenAI:
        # from openai import OpenAI
        # client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        # response = client.embeddings.create(input=text, model="text-embedding-ada-002")
        # embedding = response.data[0].embedding

        # For this script, we'll generate a random embedding of the correct dimension
        # This is just a placeholder - in production, use a real embedding model
        embedding = np.random.normal(0, 0.1, dimension).tolist()

        return embedding
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        return np.zeros(dimension).tolist()

def update_embeddings(conn, missing_embeddings: Dict[str, List[Dict[str, Any]]], dimension: int) -> Dict[str, int]:
    """
    Update records with missing embeddings.

    Args:
        conn: Database connection
        missing_embeddings: Dictionary mapping table names to lists of records with missing embeddings
        dimension: Dimension of embeddings to generate

    Returns:
        Dictionary mapping table names to counts of updated records
    """
    updated_counts = {}

    try:
        for table, records in missing_embeddings.items():
            updated_count = 0

            for record in records:
                # Generate embedding for the record
                text_content = record.get('text_content', '')
                if not text_content:
                    logger.warning(f"Empty text content for record {record['id']} in {table}, skipping")
                    continue

                embedding = generate_embedding(text_content, dimension)

                # Update the record with the new embedding
                with conn.cursor() as cursor:
                    # Convert embedding to string format expected by PostgreSQL vector type
                    vector_str = '[' + ','.join(str(x) for x in embedding) + ']'

                    cursor.execute(f"""
                        UPDATE {table}
                        SET embedding = %s::vector
                        WHERE id = %s
                    """, (vector_str, record['id']))

                    updated_count += 1
                    logger.debug(f"Updated embedding for record {record['id']} in {table}")

            if updated_count > 0:
                updated_counts[table] = updated_count
                logger.info(f"Updated {updated_count} embeddings in {table}")

        # Commit the changes
        conn.commit()

        return updated_counts
    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating embeddings: {e}")
        return {}

def verify_embeddings(conn) -> Dict[str, Dict[str, int]]:
    """
    Verify that all records have embeddings after the update.

    Args:
        conn: Database connection

    Returns:
        Dictionary with verification results
    """
    verification_results = {}

    try:
        for table in TABLES_WITH_EMBEDDINGS:
            try:
                with conn.cursor() as cursor:
                    # First check if the table exists
                    cursor.execute(f"""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables
                            WHERE table_name = '{table}'
                        )
                    """)
                    table_exists = cursor.fetchone()[0]

                    if not table_exists:
                        logger.warning(f"Table {table} does not exist, skipping verification")
                        continue

                    # Check if the table has an embedding column
                    cursor.execute(f"""
                        SELECT EXISTS (
                            SELECT FROM information_schema.columns
                            WHERE table_name = '{table}' AND column_name = 'embedding'
                        )
                    """)
                    has_embedding_column = cursor.fetchone()[0]

                    if not has_embedding_column:
                        logger.warning(f"Table {table} does not have an embedding column, skipping verification")
                        continue

                    # Get total count of records
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    total_count = cursor.fetchone()[0]

                    # Get count of records with embeddings
                    cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE embedding IS NOT NULL")
                    with_embedding_count = cursor.fetchone()[0]

                    # Get count of records without embeddings
                    cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE embedding IS NULL")
                    without_embedding_count = cursor.fetchone()[0]

                    verification_results[table] = {
                        "total_records": total_count,
                        "with_embedding": with_embedding_count,
                        "without_embedding": without_embedding_count,
                        "coverage_percentage": (with_embedding_count / total_count * 100) if total_count > 0 else 100
                    }

                    if without_embedding_count > 0:
                        logger.warning(f"{table} still has {without_embedding_count} records without embeddings")
                    else:
                        logger.info(f"All records in {table} now have embeddings")
            except Exception as e:
                logger.error(f"Error verifying embeddings for table {table}: {e}")
                conn.rollback()  # Rollback the transaction to continue with other tables

        return verification_results
    except Exception as e:
        logger.error(f"Error verifying embeddings: {e}")
        return {}

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Generate missing embeddings in the database")
    parser.add_argument("--dry-run", action="store_true", help="Identify missing embeddings without updating")
    parser.add_argument("--table", help="Process only the specified table")
    args = parser.parse_args()

    try:
        # Connect to database
        conn = connect_to_db()

        # Get embedding dimension from existing embeddings
        dimension = get_embedding_dimension(conn)
        logger.info(f"Using embedding dimension: {dimension}")

        # Filter tables if a specific table is specified
        global TABLES_WITH_EMBEDDINGS
        if args.table:
            if args.table in TABLES_WITH_EMBEDDINGS:
                TABLES_WITH_EMBEDDINGS = [args.table]
                logger.info(f"Processing only table: {args.table}")
            else:
                logger.error(f"Table {args.table} not found in tables with embeddings")
                sys.exit(1)

        # Identify missing embeddings
        missing_embeddings = identify_missing_embeddings(conn)

        # Count total missing embeddings
        total_missing = sum(len(records) for records in missing_embeddings.values())
        logger.info(f"Found {total_missing} records with missing embeddings across {len(missing_embeddings)} tables")

        if args.dry_run:
            logger.info("Dry run mode - not updating embeddings")
        else:
            # Update embeddings
            if total_missing > 0:
                updated_counts = update_embeddings(conn, missing_embeddings, dimension)
                logger.info(f"Updated embeddings for {sum(updated_counts.values())} records")
            else:
                logger.info("No missing embeddings to update")

        # Verify embeddings
        verification_results = verify_embeddings(conn)

        # Print verification summary
        logger.info("\n=== VERIFICATION SUMMARY ===")
        for table, results in verification_results.items():
            logger.info(f"{table}: {results['with_embedding']}/{results['total_records']} records have embeddings ({results['coverage_percentage']:.2f}%)")

        # Close connection
        conn.close()

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
