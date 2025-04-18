import sqlite3
import os
from pathlib import Path
import psycopg2
from dotenv import load_dotenv
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

def init_sqlite_db():
    """Initialize the SQLite database."""
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    db_path = data_dir / "egypt_chatbot.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        logger.info(f"Connected to SQLite database: {db_path}")
        
        # Create necessary tables
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS attractions (
            id TEXT PRIMARY KEY,
            name_en TEXT NOT NULL,
            name_ar TEXT,
            type TEXT,
            city TEXT,
            region TEXT,
            latitude REAL,
            longitude REAL,
            description_en TEXT,
            description_ar TEXT,
            data JSON,
            created_at TEXT,
            updated_at TEXT
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS accommodations (
            id TEXT PRIMARY KEY,
            name_en TEXT NOT NULL,
            name_ar TEXT,
            type TEXT,
            category TEXT,
            city TEXT,
            region TEXT,
            latitude REAL,
            longitude REAL,
            description_en TEXT,
            description_ar TEXT,
            price_min REAL,
            price_max REAL,
            data JSON,
            created_at TEXT,
            updated_at TEXT
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS restaurants (
            id TEXT PRIMARY KEY,
            name_en TEXT NOT NULL,
            name_ar TEXT,
            cuisine TEXT,
            city TEXT,
            region TEXT,
            latitude REAL,
            longitude REAL,
            description_en TEXT,
            description_ar TEXT,
            price_range TEXT,
            data JSON,
            created_at TEXT,
            updated_at TEXT
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            data JSON,
            created_at TEXT,
            updated_at TEXT,
            expires_at TEXT
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            role TEXT,
            data JSON,
            created_at TEXT,
            last_login TEXT
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS analytics (
            id TEXT PRIMARY KEY,
            session_id TEXT,
            user_id TEXT,
            event_type TEXT,
            event_data JSON,
            timestamp TEXT
        )
        ''')
        logger.info("SQLite tables created or already exist.")
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_attractions_type ON attractions (type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_attractions_city ON attractions (city)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_accommodations_type ON accommodations (type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_accommodations_city ON accommodations (city)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_restaurants_city ON restaurants (city)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_restaurants_cuisine ON restaurants (cuisine)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions (expires_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_analytics_timestamp ON analytics (timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_analytics_event_type ON analytics (event_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_analytics_session_id ON analytics (session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_analytics_user_id ON analytics (user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users (username)')
        logger.info("SQLite indexes created or already exist.")
        
        conn.commit()
        conn.close()
        logger.info(f"SQLite database initialized successfully at {db_path}")
        
    except sqlite3.Error as e:
        logger.error(f"Error initializing SQLite database: {e}")
        if conn:
            conn.close()
            
def init_postgres_db():
    """Initialize the PostgreSQL database."""
    postgres_uri = os.getenv("POSTGRES_URI")
    if not postgres_uri:
        logger.info("POSTGRES_URI not found, skipping PostgreSQL initialization.")
        return

    conn = None
    try:
        conn = psycopg2.connect(postgres_uri)
        conn.autocommit = False
        cursor = conn.cursor()
        logger.info(f"Connected to PostgreSQL database: {postgres_uri.split('@')[-1]}")

        # Create necessary tables
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS attractions (
            id TEXT PRIMARY KEY,
            name_en TEXT NOT NULL,
            name_ar TEXT,
            type TEXT,
            city TEXT,
            region TEXT,
            latitude REAL,
            longitude REAL,
            description_en TEXT,
            description_ar TEXT,
            data JSONB,
            created_at TIMESTAMPTZ,
            updated_at TIMESTAMPTZ
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS accommodations (
            id TEXT PRIMARY KEY,
            name_en TEXT NOT NULL,
            name_ar TEXT,
            type TEXT,
            category TEXT,
            city TEXT,
            region TEXT,
            latitude REAL,
            longitude REAL,
            description_en TEXT,
            description_ar TEXT,
            price_min REAL,
            price_max REAL,
            data JSONB,
            created_at TIMESTAMPTZ,
            updated_at TIMESTAMPTZ
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS restaurants (
            id TEXT PRIMARY KEY,
            name_en TEXT NOT NULL,
            name_ar TEXT,
            cuisine TEXT,
            city TEXT,
            region TEXT,
            latitude REAL,
            longitude REAL,
            description_en TEXT,
            description_ar TEXT,
            price_range TEXT,
            data JSONB,
            created_at TIMESTAMPTZ,
            updated_at TIMESTAMPTZ
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            data JSONB,
            created_at TIMESTAMPTZ,
            updated_at TIMESTAMPTZ,
            expires_at TIMESTAMPTZ
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            role TEXT,
            data JSONB,
            created_at TIMESTAMPTZ,
            last_login TIMESTAMPTZ
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS analytics (
            id TEXT PRIMARY KEY,
            session_id TEXT,
            user_id TEXT,
            event_type TEXT,
            event_data JSONB,
            timestamp TIMESTAMPTZ
        )
        ''')
        logger.info("PostgreSQL tables created or already exist.")

        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_attractions_type ON attractions (type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_attractions_city ON attractions (city)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_accommodations_type ON accommodations (type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_accommodations_city ON accommodations (city)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_restaurants_city ON restaurants (city)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_restaurants_cuisine ON restaurants (cuisine)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions (expires_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_analytics_timestamp ON analytics (timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_analytics_event_type ON analytics (event_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_analytics_session_id ON analytics (session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_analytics_user_id ON analytics (user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users (username)')
        logger.info("PostgreSQL indexes created or already exist.")

        conn.commit()
        cursor.close()
        conn.close()
        logger.info(f"PostgreSQL database initialized successfully.")

    except psycopg2.Error as e:
        logger.error(f"Error initializing PostgreSQL database: {e}")
        if conn:
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    logger.info("Initializing databases...")
    init_sqlite_db()
    init_postgres_db()
    logger.info("Database initialization process complete.")