#!/usr/bin/env python3
"""
PostgreSQL Database Initialization Script.
Creates the necessary PostgreSQL tables for the Egypt Tourism Chatbot.
"""

import os
import sys
import psycopg2
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def init_postgres_tables(postgres_uri):
    """
    Initialize PostgreSQL database tables.
    
    Args:
        postgres_uri: URI of the PostgreSQL database
    
    Returns:
        bool: Success status
    """
    # Print the URI for debugging
    print(f"Using PostgreSQL URI: {postgres_uri}")
    
    try:
        # Connect to the database
        conn = psycopg2.connect(postgres_uri)
        conn.autocommit = True
        cursor = conn.cursor()
        
        tables_created = 0
        
        # Create tables one by one with error handling
        try:
            # Create attractions table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS attractions (
                id TEXT PRIMARY KEY,
                name_en TEXT NOT NULL,
                name_ar TEXT,
                description_en TEXT,
                description_ar TEXT,
                location TEXT,
                type TEXT,
                data JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            tables_created += 1
            logger.info("Created attractions table")
        except Exception as e:
            logger.error(f"Error creating attractions table: {e}")
        
        try:
            # Create cities table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS cities (
                id TEXT PRIMARY KEY,
                name_en TEXT NOT NULL,
                name_ar TEXT,
                description_en TEXT,
                description_ar TEXT,
                region TEXT,
                data JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            tables_created += 1
            logger.info("Created cities table")
        except Exception as e:
            logger.error(f"Error creating cities table: {e}")
        
        try:
            # Create accommodations table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS accommodations (
                id TEXT PRIMARY KEY,
                name_en TEXT NOT NULL,
                name_ar TEXT,
                description_en TEXT,
                description_ar TEXT,
                location TEXT,
                type TEXT,
                data JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            tables_created += 1
            logger.info("Created accommodations table")
        except Exception as e:
            logger.error(f"Error creating accommodations table: {e}")
        
        try:
            # Create restaurants table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS restaurants (
                id TEXT PRIMARY KEY,
                name_en TEXT NOT NULL,
                name_ar TEXT,
                description_en TEXT,
                description_ar TEXT,
                location TEXT,
                cuisine TEXT,
                data JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            tables_created += 1
            logger.info("Created restaurants table")
        except Exception as e:
            logger.error(f"Error creating restaurants table: {e}")
        
        try:
            # Create users table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE,
                password_hash TEXT NOT NULL,
                first_name TEXT,
                last_name TEXT,
                preferred_language TEXT DEFAULT 'en',
                role TEXT DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
            ''')
            tables_created += 1
            logger.info("Created users table")
        except Exception as e:
            logger.error(f"Error creating users table: {e}")
        
        try:
            # Create sessions table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                data JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            ''')
            tables_created += 1
            logger.info("Created sessions table")
        except Exception as e:
            logger.error(f"Error creating sessions table: {e}")
        
        try:
            # Create analytics table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics (
                id SERIAL PRIMARY KEY,
                event_type TEXT NOT NULL,
                event_data JSONB,
                session_id TEXT,
                user_id TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            ''')
            tables_created += 1
            logger.info("Created analytics table")
        except Exception as e:
            logger.error(f"Error creating analytics table: {e}")
        
        try:
            # Create feedback table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id SERIAL PRIMARY KEY,
                session_id TEXT,
                user_id TEXT,
                message_id TEXT,
                rating INTEGER,
                feedback_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            ''')
            tables_created += 1
            logger.info("Created feedback table")
        except Exception as e:
            logger.error(f"Error creating feedback table: {e}")
        
        try:
            # Create test table - for testing only
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_table (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            tables_created += 1
            logger.info("Created test_table")
        except Exception as e:
            logger.error(f"Error creating test_table: {e}")
            
        # Create indexes (simplified for clarity, add more later)
        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_attractions_name_en ON attractions (name_en)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_attractions_type ON attractions (type)')
            logger.info("Created attraction indexes")
        except Exception as e:
            logger.error(f"Error creating attraction indexes: {e}")

        # Close the connection
        cursor.close()
        conn.close()
        
        logger.info(f"Created {tables_created} PostgreSQL tables successfully")
        
        return tables_created > 0
        
    except Exception as e:
        logger.error(f"Error initializing PostgreSQL database: {str(e)}")
        print(f"\n*** POSTGRESQL DATABASE INIT FAILED: {e} ***\n")
        return False

def main():
    """Main function to initialize database from command line."""
    # Use the correct PostgreSQL URI directly
    postgres_uri = "postgresql://omarmohamed@localhost:5432/egypt_chatbot"
    
    # Initialize database
    success = init_postgres_tables(postgres_uri)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main() 