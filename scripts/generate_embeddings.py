#!/usr/bin/env python3
"""
Script to generate embeddings for tourism data and store them in PostgreSQL using pgvector.

This script:
1. Loads tourism data from the database (attractions, restaurants, hotels, cities)
2. Generates embeddings using a specified model
3. Updates the database tables with the generated embeddings
4. Creates appropriate indexes for vector similarity search
"""

import os
import sys
import json
import logging
import argparse
import time
from typing import List, Dict, Any, Optional, Tuple
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
import numpy as np
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Project root directory
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import from project
try:
    from src.utils.environment import get_env_var
except ImportError:
    logger.error("Failed to import required modules from project. Make sure the project structure is correct.")
    
    # Fallback implementation
    def get_env_var(name, default=None):
        return os.getenv(name, default)

# Parse arguments
def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Generate embeddings for tourism data")
    parser.add_argument("--model", type=str, default="sentence-transformers/all-MiniLM-L6-v2", 
                        help="Model to use for generating embeddings")
    parser.add_argument("--tables", type=str, nargs="+", 
                        default=["attractions", "restaurants", "hotels", "cities"],
                        help="Tables to generate embeddings for")
    parser.add_argument("--batch-size", type=int, default=16,
                        help="Batch size for generating embeddings")
    parser.add_argument("--force", action="store_true", 
                        help="Force regeneration of embeddings even if they already exist")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print operations without executing them")
    parser.add_argument("--language", type=str, choices=["en", "ar", "both"], default="both",
                        help="Language to generate embeddings for")
    
    return parser.parse_args()

# Load environment
def load_config():
    """Load configuration from .env file."""
    dotenv_path = os.path.join(project_root, '.env')
    load_dotenv(dotenv_path)
    
    # Get PostgreSQL URI
    postgres_uri = get_env_var("POSTGRES_URI")
    if not postgres_uri:
        logger.error("POSTGRES_URI environment variable not set")
        sys.exit(1)
    
    logger.info(f"Using PostgreSQL URI: {postgres_uri}")
    return postgres_uri

# Connect to PostgreSQL
def connect_to_postgres(postgres_uri):
    """Connect to PostgreSQL database."""
    try:
        conn = psycopg2.connect(postgres_uri)
        logger.info("Connected to PostgreSQL database")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to PostgreSQL: {e}")
        sys.exit(1)

# Check if pgvector extension is installed
def check_pgvector_extension(conn):
    """Check if pgvector extension is installed and available."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')")
            has_extension = cursor.fetchone()[0]
            
            if not has_extension:
                logger.error("pgvector extension is not installed. Please run scripts/setup_pgvector.py first.")
                return False
            
            logger.info("pgvector extension is installed and available")
            return True
    except Exception as e:
        logger.error(f"Error checking pgvector extension: {e}")
        return False

# Check if embedding columns exist
def check_embedding_columns(conn, tables):
    """Check if embedding columns exist in the specified tables."""
    missing_columns = {}
    
    try:
        with conn.cursor() as cursor:
            for table in tables:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_schema = 'public' 
                        AND table_name = %s 
                        AND column_name = 'embedding'
                    )
                """, (table,))
                has_column = cursor.fetchone()[0]
                
                if not has_column:
                    missing_columns[table] = 'embedding'
                
                # Check for language-specific embedding columns
                for lang in ['en', 'ar']:
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.columns 
                            WHERE table_schema = 'public' 
                            AND table_name = %s 
                            AND column_name = %s
                        )
                    """, (table, f'embedding_{lang}'))
                    has_lang_column = cursor.fetchone()[0]
                    
                    if not has_lang_column:
                        if table not in missing_columns:
                            missing_columns[table] = []
                        if isinstance(missing_columns[table], list):
                            missing_columns[table].append(f'embedding_{lang}')
                        else:
                            missing_columns[table] = [missing_columns[table], f'embedding_{lang}']
        
        return missing_columns
    except Exception as e:
        logger.error(f"Error checking embedding columns: {e}")
        return {table: ['embedding', 'embedding_en', 'embedding_ar'] for table in tables}

# Add embedding columns
def add_embedding_columns(conn, missing_columns, dry_run=False):
    """Add embedding columns to the specified tables."""
    try:
        with conn.cursor() as cursor:
            for table, columns in missing_columns.items():
                if not isinstance(columns, list):
                    columns = [columns]
                
                for column in columns:
                    sql = f"ALTER TABLE {table} ADD COLUMN {column} vector(384)"
                    
                    if dry_run:
                        logger.info(f"[DRY RUN] Would execute: {sql}")
                    else:
                        try:
                            cursor.execute(sql)
                            conn.commit()
                            logger.info(f"Added column {column} to {table}")
                        except Exception as e:
                            logger.error(f"Error adding column {column} to {table}: {e}")
                            conn.rollback()
        
        return True
    except Exception as e:
        logger.error(f"Error adding embedding columns: {e}")
        return False

# Load sentence transformer model
def load_model(model_name):
    """Load the sentence transformer model."""
    try:
        # Dynamically import sentence-transformers to avoid requiring it for dry runs
        from sentence_transformers import SentenceTransformer
        
        logger.info(f"Loading model: {model_name}")
        model = SentenceTransformer(model_name)
        logger.info(f"Model loaded: {model_name}")
        return model
    except ImportError:
        logger.error("Failed to import sentence-transformers. Please install it with: pip install sentence-transformers")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error loading model {model_name}: {e}")
        sys.exit(1)

# Fetch data from table
def fetch_data(conn, table, force=False):
    """Fetch data from the specified table."""
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            where_clause = ""
            if not force:
                where_clause = "WHERE embedding IS NULL OR embedding_en IS NULL OR embedding_ar IS NULL"
                
            cursor.execute(f"SELECT * FROM {table} {where_clause}")
            rows = cursor.fetchall()
            logger.info(f"Fetched {len(rows)} records from {table}")
            return rows
    except Exception as e:
        logger.error(f"Error fetching data from {table}: {e}")
        return []

# Prepare text for embedding
def prepare_text_for_embedding(record, table, language='en'):
    """Prepare text for embedding generation."""
    text_pieces = []
    
    # Add name and description
    name_key = f"name_{language}" if language in ('en', 'ar') else "name"
    desc_key = f"description_{language}" if language in ('en', 'ar') else "description"
    
    # Handle both direct columns and JSONB fields
    name = record.get(name_key, "")
    if not name and language in ('en', 'ar'):
        # Try to get from data JSONB
        data = record.get('data', {})
        if data and isinstance(data, dict):
            name = data.get(name_key, "")
    
    description = record.get(desc_key, "")
    if not description and language in ('en', 'ar'):
        # Try to get from data JSONB
        data = record.get('data', {})
        if data and isinstance(data, dict):
            description = data.get(desc_key, "")
    
    if name:
        text_pieces.append(name)
    
    if description:
        text_pieces.append(description)
    
    # Add specific fields based on table
    if table == 'attractions':
        # Add attraction type, city
        attraction_type = record.get('type', "")
        city = record.get('city', "")
        
        if attraction_type:
            text_pieces.append(f"Type: {attraction_type}")
        
        if city:
            text_pieces.append(f"Located in: {city}")
    
    elif table == 'restaurants':
        # Add cuisine, price range, city
        cuisine = record.get('cuisine', "")
        price_range = record.get('price_range', "")
        city = record.get('city', "")
        
        if cuisine:
            text_pieces.append(f"Cuisine: {cuisine}")
        
        if price_range:
            text_pieces.append(f"Price range: {price_range}")
        
        if city:
            text_pieces.append(f"Located in: {city}")
    
    elif table == 'hotels':
        # Add hotel class, city
        hotel_class = record.get('class', "")
        amenities = record.get('amenities', [])
        city = record.get('city', "")
        
        if hotel_class:
            text_pieces.append(f"Class: {hotel_class}")
        
        if amenities and isinstance(amenities, list):
            text_pieces.append(f"Amenities: {', '.join(amenities)}")
        
        if city:
            text_pieces.append(f"Located in: {city}")
    
    elif table == 'cities':
        # Add region, highlights
        region = record.get('region', "")
        highlights = record.get(f'highlights_{language}' if language in ('en', 'ar') else 'highlights', [])
        
        if region:
            text_pieces.append(f"Region: {region}")
        
        if highlights and isinstance(highlights, list):
            text_pieces.append(f"Highlights: {', '.join(highlights)}")
    
    # Combine all text pieces
    combined_text = " ".join(text_pieces)
    
    # Return the combined text, or a placeholder if empty
    return combined_text if combined_text.strip() else f"No {language} text available for this {table[:-1]}"

# Generate embeddings
def generate_embeddings(model, records, table, batch_size=16, language='both'):
    """Generate embeddings for the specified records."""
    embeddings_dict = {}
    
    languages = ['en', 'ar'] if language == 'both' else [language]
    
    # Prepare batches of text for each language
    for lang in languages:
        texts = []
        record_ids = []
        
        for record in records:
            record_id = record.get('id')
            text = prepare_text_for_embedding(record, table, lang)
            
            texts.append(text)
            record_ids.append(record_id)
        
        # Generate embeddings in batches
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_ids = record_ids[i:i + batch_size]
            
            logger.info(f"Generating {lang} embeddings for batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size} of {table}")
            
            try:
                batch_embeddings = model.encode(batch_texts)
                
                for j, record_id in enumerate(batch_ids):
                    if record_id not in embeddings_dict:
                        embeddings_dict[record_id] = {}
                    
                    embeddings_dict[record_id][f'embedding_{lang}'] = batch_embeddings[j].tolist()
                    
                    # Also set the default embedding to English
                    if lang == 'en':
                        embeddings_dict[record_id]['embedding'] = batch_embeddings[j].tolist()
            
            except Exception as e:
                logger.error(f"Error generating embeddings for batch {i//batch_size + 1}: {e}")
                continue
    
    return embeddings_dict

# Update embeddings in database
def update_embeddings(conn, table, embeddings_dict, dry_run=False):
    """Update embeddings in the database."""
    try:
        update_count = 0
        
        with conn.cursor() as cursor:
            for record_id, embeddings in embeddings_dict.items():
                # Prepare SET clause
                set_clause = []
                params = []
                
                for column, embedding in embeddings.items():
                    set_clause.append(f"{column} = %s")
                    params.append(embedding)
                
                if not set_clause:
                    continue
                
                # Add record_id to params
                params.append(record_id)
                
                sql = f"""
                UPDATE {table}
                SET {', '.join(set_clause)}
                WHERE id = %s
                """
                
                if dry_run:
                    logger.info(f"[DRY RUN] Would update embeddings for {table} record {record_id}")
                else:
                    try:
                        cursor.execute(sql, params)
                        update_count += 1
                    except Exception as e:
                        logger.error(f"Error updating embeddings for {table} record {record_id}: {e}")
                        conn.rollback()
                        continue
                
                # Commit every 100 updates to avoid transaction size issues
                if update_count % 100 == 0 and not dry_run:
                    conn.commit()
                    logger.info(f"Committed {update_count} updates")
            
            # Final commit
            if not dry_run and update_count % 100 != 0:
                conn.commit()
        
        logger.info(f"{'Would update' if dry_run else 'Updated'} embeddings for {update_count} records in {table}")
        return update_count
    except Exception as e:
        logger.error(f"Error updating embeddings in {table}: {e}")
        if not dry_run:
            conn.rollback()
        return 0

# Create or update vector indexes
def create_vector_indexes(conn, tables, dry_run=False):
    """Create or update vector indexes."""
    try:
        indexes_created = 0
        
        with conn.cursor() as cursor:
            for table in tables:
                # Define indexes to create
                index_definitions = [
                    # Main embedding index
                    {
                        'name': f'idx_{table}_embedding',
                        'column': 'embedding',
                        'method': 'ivfflat',
                        'options': "WITH (lists = 100)"
                    },
                    # Language-specific indexes
                    {
                        'name': f'idx_{table}_embedding_en',
                        'column': 'embedding_en',
                        'method': 'ivfflat',
                        'options': "WITH (lists = 100)"
                    },
                    {
                        'name': f'idx_{table}_embedding_ar',
                        'column': 'embedding_ar',
                        'method': 'ivfflat',
                        'options': "WITH (lists = 100)"
                    }
                ]
                
                for index_def in index_definitions:
                    # Check if index exists
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM pg_indexes
                            WHERE schemaname = 'public'
                            AND tablename = %s
                            AND indexname = %s
                        )
                    """, (table, index_def['name']))
                    
                    index_exists = cursor.fetchone()[0]
                    
                    if index_exists:
                        logger.info(f"Index {index_def['name']} already exists")
                        continue
                    
                    # Create the index
                    sql = f"""
                    CREATE INDEX {index_def['name']} ON {table} 
                    USING {index_def['method']} ({index_def['column']}) {index_def['options']}
                    """
                    
                    if dry_run:
                        logger.info(f"[DRY RUN] Would create index: {sql}")
                    else:
                        try:
                            cursor.execute(sql)
                            conn.commit()
                            logger.info(f"Created index {index_def['name']}")
                            indexes_created += 1
                        except Exception as e:
                            logger.error(f"Error creating index {index_def['name']}: {e}")
                            conn.rollback()
                            continue
        
        logger.info(f"{'Would create' if dry_run else 'Created'} {indexes_created} vector indexes")
        return indexes_created
    except Exception as e:
        logger.error(f"Error creating vector indexes: {e}")
        if not dry_run:
            conn.rollback()
        return 0

# Main function
def main():
    """Main function to generate and store embeddings."""
    # Parse arguments
    args = parse_args()
    
    # Load configuration
    postgres_uri = load_config()
    
    # Connect to PostgreSQL
    conn = connect_to_postgres(postgres_uri)
    
    try:
        # Check if pgvector extension is installed
        if not check_pgvector_extension(conn):
            return
        
        # Check if embedding columns exist
        missing_columns = check_embedding_columns(conn, args.tables)
        
        if missing_columns:
            logger.info(f"Missing embedding columns: {missing_columns}")
            
            # Add embedding columns
            if not add_embedding_columns(conn, missing_columns, args.dry_run):
                logger.error("Failed to add embedding columns")
                return
        
        # Load model (skip for dry run)
        model = None
        if not args.dry_run:
            model = load_model(args.model)
        
        # Process each table
        for table in args.tables:
            # Fetch data
            records = fetch_data(conn, table, args.force)
            
            if not records:
                logger.info(f"No records to process for {table}")
                continue
            
            # Generate embeddings (skip for dry run)
            if not args.dry_run:
                embeddings_dict = generate_embeddings(
                    model, records, table, 
                    batch_size=args.batch_size,
                    language=args.language
                )
                
                # Update embeddings in database
                updated = update_embeddings(conn, table, embeddings_dict, args.dry_run)
                logger.info(f"Updated embeddings for {updated} records in {table}")
            else:
                logger.info(f"[DRY RUN] Would generate embeddings for {len(records)} records in {table}")
        
        # Create vector indexes
        create_vector_indexes(conn, args.tables, args.dry_run)
        
        logger.info("Embedding generation completed successfully")
        
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
    finally:
        conn.close()
        logger.info("Database connection closed")

if __name__ == "__main__":
    main() 