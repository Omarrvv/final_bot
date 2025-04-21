#!/usr/bin/env python3
"""
Database Initialization Script.
Creates the necessary database tables for the Egypt Tourism Chatbot.
"""

import sqlite3
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def init_db_tables(db_path_or_conn):
    """
    Initialize database tables.
    
    Args:
        db_path_or_conn: Either a path to SQLite database file, ':memory:', or an existing connection
    
    Returns:
        bool: Success status
    """
    db_path = None # Initialize db_path to None
    try:
        # Handle both connection and path cases
        if isinstance(db_path_or_conn, sqlite3.Connection):
            conn = db_path_or_conn
            cursor = conn.cursor()
            should_close = False
        else:
            # Only create directory if using file-based database
            if db_path_or_conn != ':memory:':
                os.makedirs(os.path.dirname(db_path_or_conn), exist_ok=True)
            db_path = db_path_or_conn # Assign db_path
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            should_close = True
        
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
            data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create cities table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS cities (
            id TEXT PRIMARY KEY,
            name_en TEXT NOT NULL,
            name_ar TEXT,
            description_en TEXT,
            description_ar TEXT,
            region TEXT,
            data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
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
            data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
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
            data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
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
        
        # Create sessions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # Create analytics table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            event_data TEXT,
            session_id TEXT,
            user_id TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # Create feedback table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        
        # Create test table - for testing only
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS test_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            value TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_attractions_name_en ON attractions (name_en)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_attractions_type ON attractions (type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_cities_name_en ON cities (name_en)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_accommodations_name_en ON accommodations (name_en)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_accommodations_type ON accommodations (type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_restaurants_name_en ON restaurants (name_en)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_restaurants_cuisine ON restaurants (cuisine)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions (user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_analytics_event_type ON analytics (event_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_analytics_session_id ON analytics (session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_analytics_user_id ON analytics (user_id)')
        
        # Commit changes
        conn.commit()
        logger.info(f"Database tables created successfully at {db_path if db_path is not None else 'memory'}")
        
        # Only close if we created the connection
        if should_close:
            conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        print(f"\n*** DATABASE INIT FAILED: {e} ***\n")
        return False

def main():
    """Main function to initialize database from command line."""
    import argparse
    import sys
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Initialize database tables')
    parser.add_argument('--db-path', '-d', default='data/egypt_chatbot.db',
                        help='Path to SQLite database file')
    args = parser.parse_args()
    
    # Initialize database
    success = init_db_tables(args.db_path)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main() 