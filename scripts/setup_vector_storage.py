#!/usr/bin/env python3
"""
Setup Vector Storage for Semantic Search

This script:
1. Checks if pgvector extension is installed in PostgreSQL
2. Adds vector columns to relevant tables if they don't exist
3. Generates embeddings using a simple model, and stores these embeddings

Prerequisites:
- PostgreSQL with pgvector extension
- Python packages: psycopg2, numpy, sentence-transformers
"""

import os
import json
import logging
import time
import psycopg2
from psycopg2.extras import RealDictCursor
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    HAVE_TRANSFORMERS = True
except ImportError:
    print("Warning: sentence-transformers not installed. Installing now...")
    import subprocess
    subprocess.check_call(['pip', 'install', 'sentence-transformers'])
    from sentence_transformers import SentenceTransformer
    HAVE_TRANSFORMERS = True

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
def load_config():
    """Load configuration from .env file"""
    import dotenv
    dotenv.load_dotenv()
    
    # Get PostgreSQL URI from environment or use default
    pg_uri = os.environ.get("POSTGRES_URI", "postgresql://omarmohamed@localhost:5432/postgres")
    logger.info(f"Using PostgreSQL URI: {pg_uri}")
    return pg_uri

def check_pgvector(conn):
    """Check if pgvector extension is installed"""
    with conn.cursor() as cur:
        try:
            cur.execute("SELECT * FROM pg_extension WHERE extname = 'vector'")
            if cur.fetchone():
                logger.info("pgvector extension is already installed")
                return True
            else:
                logger.info("pgvector extension not found, attempting to install...")
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
                conn.commit()
                logger.info("pgvector extension installed successfully")
                return True
        except Exception as e:
            logger.error(f"Error checking/installing pgvector extension: {e}")
            return False

def add_vector_columns(conn):
    """Add vector columns to relevant tables if they don't exist"""
    tables = ["attractions", "restaurants", "hotels"]
    dimension = 384  # Using dimension for all-MiniLM-L6-v2 model
    
    with conn.cursor() as cur:
        for table in tables:
            try:
                # Check if the table exists
                cur.execute(f"SELECT to_regclass('{table}')")
                if not cur.fetchone()[0]:
                    logger.warning(f"Table {table} does not exist, skipping")
                    continue
                
                # Check if embedding column exists
                cur.execute(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = '{table}' AND column_name = 'embedding'
                """)
                
                if not cur.fetchone():
                    logger.info(f"Adding embedding column to {table}")
                    cur.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS embedding vector({dimension})")
                    
                    # Create index for vector similarity search
                    index_name = f"{table}_embedding_idx"
                    logger.info(f"Creating vector index {index_name}")
                    cur.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table} USING ivfflat (embedding vector_cosine_ops)")
                    
                    conn.commit()
                    logger.info(f"Vector column and index added to {table}")
                else:
                    logger.info(f"Vector column already exists in {table}")
                    
            except Exception as e:
                conn.rollback()
                logger.error(f"Error adding vector column to {table}: {e}")

def load_embedding_model():
    """Load a sentence embedding model for generating text embeddings"""
    try:
        # Use a small but effective model for demonstration
        model_name = "all-MiniLM-L6-v2"
        logger.info(f"Loading embedding model: {model_name}")
        model = SentenceTransformer(model_name)
        return model
    except Exception as e:
        logger.error(f"Error loading embedding model: {e}")
        return None

def generate_embeddings(conn, model, batch_size=50):
    """Generate and store embeddings for text data in the database"""
    tables = [
        {"name": "attractions", "text_fields": ["name_en", "description_en"]},
        {"name": "restaurants", "text_fields": ["name_en", "description_en"]},
        {"name": "hotels", "text_fields": ["name_en", "description_en"]}
    ]
    
    for table_info in tables:
        table = table_info["name"]
        text_fields = table_info["text_fields"]
        
        try:
            # Check if table exists
            with conn.cursor() as cur:
                cur.execute(f"SELECT to_regclass('{table}')")
                if not cur.fetchone()[0]:
                    logger.warning(f"Table {table} does not exist, skipping embeddings")
                    continue
                
                # Count records that need embeddings
                cur.execute(f"SELECT COUNT(*) FROM {table} WHERE embedding IS NULL")
                count = cur.fetchone()[0]
                
                if count == 0:
                    logger.info(f"No records need embeddings in {table}")
                    continue
                
                logger.info(f"Generating embeddings for {count} records in {table}")
                
                # Process in batches
                offset = 0
                total_processed = 0
                
                while offset < count:
                    # Get batch of records needing embeddings
                    cur.execute(f"""
                    SELECT id, {', '.join(text_fields)}
                    FROM {table}
                    WHERE embedding IS NULL
                    LIMIT {batch_size} OFFSET {offset}
                    """)
                    
                    records = cur.fetchall()
                    if not records:
                        break
                    
                    # Process each record
                    for record in records:
                        record_id = record[0]
                        
                        # Concatenate text fields for embedding
                        text_content = " ".join([str(record[i+1]) for i in range(len(text_fields)) if record[i+1]])
                        
                        if not text_content.strip():
                            logger.warning(f"No text content for {table} id={record_id}, skipping")
                            continue
                        
                        # Generate embedding
                        embedding = model.encode(text_content)
                        
                        # Store embedding
                        update_query = f"UPDATE {table} SET embedding = %s WHERE id = %s"
                        cur.execute(update_query, (embedding.tolist(), record_id))
                        
                        total_processed += 1
                        
                    conn.commit()
                    logger.info(f"Processed {total_processed}/{count} embeddings for {table}")
                    offset += batch_size
                
                logger.info(f"Completed embedding generation for {table}: {total_processed} records processed")
                
        except Exception as e:
            conn.rollback()
            logger.error(f"Error generating embeddings for {table}: {e}")

def main():
    """Main execution function"""
    start_time = time.time()
    logger.info("Starting vector storage setup")
    
    # Load configuration
    pg_uri = load_config()
    
    try:
        # Connect to PostgreSQL
        logger.info("Connecting to PostgreSQL")
        conn = psycopg2.connect(pg_uri)
        conn.autocommit = True
        
        # Check pgvector extension
        if not check_pgvector(conn):
            logger.error("pgvector extension not available, cannot proceed")
            return False
        
        # Add vector columns to tables
        add_vector_columns(conn)
        
        # Load embedding model
        model = load_embedding_model()
        if not model:
            logger.error("Failed to load embedding model, cannot generate embeddings")
            return False
        
        # Generate and store embeddings
        conn.autocommit = False  # Use transactions for embedding updates
        generate_embeddings(conn, model)
        
        logger.info(f"Vector storage setup completed in {time.time() - start_time:.2f} seconds")
        return True
        
    except Exception as e:
        logger.error(f"Error during vector storage setup: {e}")
        return False
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            logger.info("Database connection closed")

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 