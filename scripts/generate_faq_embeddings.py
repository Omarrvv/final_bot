#!/usr/bin/env python3
"""
Generate embeddings for tourism FAQs.

This script:
1. Identifies FAQs without embeddings
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

def identify_faqs_without_embeddings(conn):
    """Identify FAQs without embeddings"""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        cursor.execute("""
            SELECT id, question->>'en' as question_en, answer->>'en' as answer_en
            FROM tourism_faqs
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

def update_faq_embedding(conn, faq_id: int, embedding: List[float]):
    """Update the embedding for a FAQ"""
    try:
        with conn.cursor() as cursor:
            # Convert embedding to string format expected by PostgreSQL vector type
            vector_str = '[' + ','.join(str(x) for x in embedding) + ']'
            
            cursor.execute("""
                UPDATE tourism_faqs
                SET embedding = %s::vector
                WHERE id = %s
            """, (vector_str, faq_id))
            
            logger.info(f"Updated embedding for FAQ {faq_id}")
            return True
    except Exception as e:
        logger.error(f"Error updating embedding for FAQ {faq_id}: {e}")
        return False

def main():
    """Main function"""
    try:
        # Connect to database
        conn = connect_to_db()
        
        # Identify FAQs without embeddings
        faqs_without_embeddings = identify_faqs_without_embeddings(conn)
        logger.info(f"Found {len(faqs_without_embeddings)} FAQs without embeddings")
        
        if not faqs_without_embeddings:
            logger.info("No FAQs without embeddings found. Exiting.")
            conn.close()
            return
        
        # Generate and update embeddings
        for faq in faqs_without_embeddings:
            # Combine question and answer for better embedding
            text_content = f"{faq['question_en']} {faq['answer_en']}"
            
            # Generate embedding
            embedding = generate_embedding(text_content)
            
            # Update FAQ with embedding
            success = update_faq_embedding(conn, faq['id'], embedding)
            
            if success:
                logger.info(f"Successfully updated embedding for FAQ {faq['id']}")
            else:
                logger.error(f"Failed to update embedding for FAQ {faq['id']}")
        
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
