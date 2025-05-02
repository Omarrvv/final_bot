#!/usr/bin/env python3
"""
Database Initialization Script.
Creates the necessary database tables for the Egypt Tourism Chatbot.
"""

import psycopg2
import os
import logging
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def init_db_tables(postgres_uri):
    """Initialize all required database tables in PostgreSQL."""
    conn = psycopg2.connect(postgres_uri)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    # Drop and recreate cities table for test/dev environments to ensure schema is up-to-date
    cursor.execute('DROP TABLE IF EXISTS cities CASCADE')
    # Create referenced tables first
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cities (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL, -- JSON string for multilingual
        description TEXT,
        region_id TEXT,
        population INTEGER,
        location TEXT, -- JSON string (latitude, longitude)
        images TEXT,   -- JSON string (list)
        known_for TEXT, -- JSON string (list)
        best_time_to_visit TEXT,
        data TEXT,
        embedding BYTEA, -- ADDED: vector embedding for city
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(region_id) REFERENCES regions(id)
    )''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attraction_types (
        id TEXT PRIMARY KEY,
        name TEXT
    )''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS accommodation_types (
        id TEXT PRIMARY KEY,
        name TEXT
    )''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cuisines (
        id TEXT PRIMARY KEY,
        name TEXT
    )''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS regions (
        id TEXT PRIMARY KEY,
        name TEXT
    )''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT NOT NULL,
        email TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        preferred_language TEXT
    )''')

    # Create attractions table (normalized)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attractions (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL, -- JSON string for multilingual
        description TEXT,   -- JSON string for multilingual
        city_id TEXT,
        type_id TEXT,
        latitude REAL,
        longitude REAL,
        data TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(city_id) REFERENCES cities(id),
        FOREIGN KEY(type_id) REFERENCES attraction_types(id)
    )
    ''')
    
    # Create restaurants table (normalized)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS restaurants (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL, -- JSON string for multilingual
        description TEXT,   -- JSON string for multilingual
        city_id TEXT,
        cuisine_id TEXT,
        latitude REAL,
        longitude REAL,
        data TEXT,
        user_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(city_id) REFERENCES cities(id),
        FOREIGN KEY(cuisine_id) REFERENCES cuisines(id)
    )
    ''')
    
    # Create accommodations table (normalized)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS accommodations (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL, -- JSON string for multilingual
        description TEXT,   -- JSON string for multilingual
        city_id TEXT,
        type_id TEXT,
        latitude REAL,
        longitude REAL,
        data TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(city_id) REFERENCES cities(id),
        FOREIGN KEY(type_id) REFERENCES accommodation_types(id)
    )
    ''')

    # Create new indices for normalized columns
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_attractions_name ON attractions (name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_attractions_city_id ON attractions (city_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_attractions_type_id ON attractions (type_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_restaurants_name ON restaurants (name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_restaurants_city_id ON restaurants (city_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_restaurants_cuisine_id ON restaurants (cuisine_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_accommodations_name ON accommodations (name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_accommodations_city_id ON accommodations (city_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_accommodations_type_id ON accommodations (type_id)')
    
    conn.commit()
    logger.info(f"Database tables created successfully (normalized schema)")
    return True

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
    init_db_tables(args.db_path)
    
    # Exit with appropriate code
    sys.exit(0)

if __name__ == '__main__':
    # Example usage: Set POSTGRES_URI in your environment or pass as argument
    postgres_uri = os.environ.get('POSTGRES_URI')
    if not postgres_uri:
        raise ValueError('POSTGRES_URI environment variable not set.')
    init_db_tables(postgres_uri)
    print('PostgreSQL tables initialized.')