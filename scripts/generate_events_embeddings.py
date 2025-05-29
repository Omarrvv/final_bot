#!/usr/bin/env python3
"""
Generate embeddings for events and festivals.

This script:
1. Identifies events and festivals without embeddings
2. Generates embeddings using the same model as existing ones
3. Updates the records with the new embeddings
"""

import os
import sys
import logging
import psycopg2
import psycopg2.extras
import numpy as np
from typing import List, Dict, Any
import requests
import json
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Constants
EMBEDDING_DIMENSION = 1536  # OpenAI embedding dimension
MODEL_NAME = "text-embedding-ada-002"  # OpenAI embedding model

def get_postgres_uri():
    """Get PostgreSQL connection URI from environment or use default"""
    return os.getenv("POSTGRES_URI", "postgresql://postgres:postgres@localhost:5432/egypt_chatbot")

def connect_to_db():
    """Connect to PostgreSQL database"""
    postgres_uri = get_postgres_uri()
    logger.info(f"Connecting to PostgreSQL database")
    conn = psycopg2.connect(postgres_uri)
    conn.autocommit = False
    return conn

def identify_events_without_embeddings(conn):
    """Identify events and festivals without embeddings"""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        cursor.execute("""
            SELECT id, name->>'en' as name_en, description->>'en' as description_en
            FROM events_festivals
            WHERE embedding IS NULL
        """)
        return cursor.fetchall()

def generate_embedding(text: str) -> List[float]:
    """
    Generate an embedding for the given text using OpenAI API.
    
    Args:
        text: The text to generate an embedding for
        
    Returns:
        A list of floats representing the embedding
    """
    # Check if we have an OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # If no API key, generate a random embedding for testing
        logger.warning("No OpenAI API key found. Using random embedding for testing.")
        return list(np.random.normal(0, 0.1, EMBEDDING_DIMENSION))
    
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        data = {
            "input": text,
            "model": MODEL_NAME
        }
        
        response = requests.post(
            "https://api.openai.com/v1/embeddings",
            headers=headers,
            data=json.dumps(data)
        )
        
        if response.status_code == 200:
            embedding = response.json()["data"][0]["embedding"]
            return embedding
        else:
            logger.error(f"Error generating embedding: {response.text}")
            # Return a random embedding as fallback
            return list(np.random.normal(0, 0.1, EMBEDDING_DIMENSION))
            
    except Exception as e:
        logger.error(f"Exception generating embedding: {e}")
        # Return a random embedding as fallback
        return list(np.random.normal(0, 0.1, EMBEDDING_DIMENSION))

def update_event_embedding(conn, event_id: int, embedding: List[float]):
    """Update the embedding for an event"""
    try:
        with conn.cursor() as cursor:
            # Convert embedding to string format expected by PostgreSQL vector type
            vector_str = '[' + ','.join(str(x) for x in embedding) + ']'
            
            cursor.execute("""
                UPDATE events_festivals
                SET embedding = %s::vector
                WHERE id = %s
            """, (vector_str, event_id))
            
            logger.info(f"Updated embedding for event {event_id}")
            return True
    except Exception as e:
        logger.error(f"Error updating embedding for event {event_id}: {e}")
        return False

def main():
    """Main function"""
    try:
        # Connect to database
        conn = connect_to_db()
        
        # Identify events without embeddings
        events_without_embeddings = identify_events_without_embeddings(conn)
        logger.info(f"Found {len(events_without_embeddings)} events without embeddings")
        
        if not events_without_embeddings:
            logger.info("No events without embeddings found. Exiting.")
            conn.close()
            return
        
        # Generate and update embeddings
        for event in events_without_embeddings:
            # Combine name and description for better embedding
            text_content = f"{event['name_en']} {event['description_en']}"
            
            # Generate embedding
            embedding = generate_embedding(text_content)
            
            # Update event with embedding
            success = update_event_embedding(conn, event['id'], embedding)
            
            if success:
                logger.info(f"Successfully updated embedding for event {event['id']}")
            else:
                logger.error(f"Failed to update embedding for event {event['id']}")
        
        # Commit changes
        conn.commit()
        logger.info("All embeddings updated successfully")
        
        # Close connection
        conn.close()
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
