"""
Database module for the Egypt Tourism Chatbot.
Provides database connectivity and operations for persistent storage.
"""
import os
import json
import logging
import sqlite3
import redis
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
import threading
from pathlib import Path
import uuid
import numpy as np

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Database manager providing database operations for the chatbot.
    Supports multiple database backends, including SQLite, PostgreSQL, and Redis.
    """
    
    def __init__(self, database_uri: Optional[str] = None):
        """
        Initialize the database manager with the specified database URIs.
        Connects to SQLite (primary/fallback) and optionally PostgreSQL.
        
        Args:
            database_uri (str, optional): URI for the primary (SQLite) database connection.
        """
        self.database_uri = database_uri or os.getenv("DATABASE_URI", "sqlite:///data/chatbot.db")
        self.postgres_uri = os.getenv("POSTGRES_URI") # Get Postgres URI
        
        self.connection = None # For SQLite
        self.postgres_connection = None # For PostgreSQL
        
        self.db_type = self._determine_db_type() # This might need adjustment or removal if primary focus shifts
        self.lock = threading.Lock() # Keep lock for SQLite operations
        
        # Initialize primary (SQLite) connection
        self._initialize_sqlite_connection() # Renamed for clarity
        
        # Initialize secondary (PostgreSQL) connection if URI is provided
        if self.postgres_uri:
            self._initialize_postgres_connection()
        else:
            logger.info("POSTGRES_URI not found in environment. PostgreSQL connection skipped.")
            
        logger.info(f"Database manager initialized. SQLite URI: {self.database_uri}, PostgreSQL URI: {self.postgres_uri if self.postgres_uri else 'Not Configured'}")
    
    def _determine_db_type(self) -> str:
        """Determine primary database type from URI configuration."""
        # First check for PostgreSQL
        if self.postgres_uri and self.postgres_uri.startswith("postgresql:"):
            logger.info("Using PostgreSQL as primary database.")
            return "postgres"
        # Fallback to SQLite
        elif self.database_uri and self.database_uri.startswith("sqlite:"):
            logger.info("Using SQLite as primary database.")
            return "sqlite"
        else:
            logger.warning(f"No valid database URI found. PostgreSQL URI: {self.postgres_uri}, SQLite URI: {self.database_uri}")
            logger.warning("Defaulting to SQLite (memory) as fallback.")
            return "sqlite" # Default to SQLite for safety
    
    def _initialize_sqlite_connection(self) -> None:
        """Initialize SQLite database connection."""
        try:
            if not self.database_uri or not self.database_uri.startswith("sqlite:"):
                logger.error(f"Invalid or missing SQLite URI: {self.database_uri}. Cannot initialize SQLite.")
                return
                
            db_path = self.database_uri.replace("sqlite:///", "")
            
            # Create directory if it doesn't exist
            if db_path != ":memory:":
                os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
            
            # Connect to database
            self.connection = sqlite3.connect(db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
            logger.info(f"SQLite connection established: {db_path}")
            
            # Create tables if they don't exist (this should ideally be handled by init_db.py)
            self._create_sqlite_tables()
            
        except Exception as e:
            logger.error(f"Failed to initialize SQLite connection: {str(e)}")
            self.connection = None # Ensure connection is None on failure
    
    def _initialize_postgres_connection(self) -> None:
        """Initialize PostgreSQL database connection."""
        if not self.postgres_uri:
            logger.error("Attempted to initialize PostgreSQL without POSTGRES_URI set.")
            return
        try:
            self.postgres_connection = psycopg2.connect(self.postgres_uri)
            self.postgres_connection.autocommit = True # Set autocommit for simpler handling, or manage transactions explicitly
            # Test connection by creating a cursor
            with self.postgres_connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            logger.info(f"PostgreSQL connection established successfully to {self.postgres_uri.split('@')[-1]}") # Log sanitized URI
            
            # Create tables if they don't exist
            self._create_postgres_tables()
            
        except psycopg2.OperationalError as e:
            logger.error(f"Failed to connect to PostgreSQL database: {e}")
            self.postgres_connection = None
        except Exception as e:
            logger.error(f"An unexpected error occurred during PostgreSQL initialization: {e}")
            self.postgres_connection = None
            
    def _create_postgres_tables(self) -> None:
        """Create PostgreSQL tables if they don't exist."""
        if not self.postgres_connection:
            logger.warning("Cannot create PostgreSQL tables: PostgreSQL connection not available.")
            return 
            
        try:
            with self.postgres_connection.cursor() as cursor:
                # Attractions table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS attractions (
                        id TEXT PRIMARY KEY,
                        name_en TEXT NOT NULL,
                        name_ar TEXT,
                        type TEXT,
                        city TEXT,
                        region TEXT,
                        latitude FLOAT,
                        longitude FLOAT,
                        description_en TEXT,
                        description_ar TEXT,
                        data JSONB,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                
                # Accommodations table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS accommodations (
                        id TEXT PRIMARY KEY,
                        name_en TEXT NOT NULL,
                        name_ar TEXT,
                        type TEXT,
                        category TEXT,
                        city TEXT,
                        region TEXT,
                        latitude FLOAT,
                        longitude FLOAT,
                        description_en TEXT,
                        description_ar TEXT,
                        price_min FLOAT,
                        price_max FLOAT,
                        data JSONB,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                
                # Restaurants table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS restaurants (
                        id TEXT PRIMARY KEY,
                        name_en TEXT NOT NULL,
                        name_ar TEXT,
                        cuisine TEXT,
                        city TEXT,
                        region TEXT,
                        latitude FLOAT,
                        longitude FLOAT,
                        description_en TEXT,
                        description_ar TEXT,
                        price_range TEXT,
                        data JSONB,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                
                # Sessions table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sessions (
                        id TEXT PRIMARY KEY,
                        data JSONB,
                        created_at TEXT,
                        updated_at TEXT,
                        expires_at TEXT
                    )
                ''')
                
                # Analytics table - uses PostgreSQL specific types like JSONB
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS analytics (
                        id SERIAL PRIMARY KEY,
                        event_type TEXT NOT NULL,
                        event_data JSONB,
                        session_id TEXT,
                        user_id TEXT,
                        timestamp TEXT NOT NULL
                    )
                ''')
                
                # Create indexes
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_attractions_city ON attractions (city)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_attractions_type ON attractions (type)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_accommodations_city ON accommodations (city)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_accommodations_type ON accommodations (type)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_restaurants_city ON restaurants (city)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_restaurants_cuisine ON restaurants (cuisine)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_analytics_session_id ON analytics (session_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_analytics_event_type ON analytics (event_type)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_analytics_timestamp ON analytics (timestamp)')
                
                logger.info("PostgreSQL tables created successfully.")
                
        except Exception as e:
            logger.error(f"Failed to create PostgreSQL tables: {e}")
    
    def _create_sqlite_tables(self) -> None:
        """Create SQLite tables if they don't exist."""
        if not self.connection:
            logger.warning("Cannot create SQLite tables: SQLite connection not available.")
            return 
        with self.lock:
            cursor = self.connection.cursor()
            
            # Attractions table
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
            
            # Accommodations table
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
            
            # Restaurants table
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
            
            # Sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    data JSON,
                    created_at TEXT,
                    updated_at TEXT,
                    expires_at TEXT
                )
            ''')
            
            # Users table
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
            
            # Analytics table (Ensure name matches actual table)
            # Note: Table name in log_analytics_event is 'analytics'. Keep consistent.
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
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_attractions_type ON attractions (type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_attractions_city ON attractions (city)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_accommodations_city ON accommodations (city)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_restaurants_city ON restaurants (city)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_restaurants_cuisine ON restaurants (cuisine)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions (expires_at)')
            # Add indexes for analytics table
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_analytics_session_id ON analytics (session_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_analytics_event_type ON analytics (event_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_analytics_timestamp ON analytics (timestamp)')
            
            self.connection.commit()
    
    def close(self) -> None:
        """Close all active database connections."""
        if self.connection:
            try:
                self.connection.close()
                logger.info("SQLite connection closed.")
            except Exception as e:
                logger.error(f"Error closing SQLite connection: {e}")
        if self.postgres_connection:
            try:
                self.postgres_connection.close()
                logger.info("PostgreSQL connection closed.")
            except Exception as e:
                logger.error(f"Error closing PostgreSQL connection: {e}")
        self.connection = None
        self.postgres_connection = None
    
    def get_attraction(self, attraction_id: str) -> Optional[Dict]:
        """
        Get attraction by ID.
        
        Args:
            attraction_id (str): Attraction ID
            
        Returns:
            dict: Attraction data if found, None otherwise
        """
        try:
            if self.db_type == "sqlite":
                with self.lock:
                    cursor = self.connection.cursor()
                    cursor.execute("SELECT * FROM attractions WHERE id = ?", (attraction_id,))
                    row = cursor.fetchone()
                    
                    if row:
                        attraction = dict(row)
                        if "data" in attraction and attraction["data"]:
                            # Parse JSON data
                            attraction.update(json.loads(attraction["data"]))
                            del attraction["data"]
                        return attraction
                    
                    return None
                    
            elif self.db_type == "postgres":
                cursor = self.postgres_connection.cursor(cursor_factory=RealDictCursor)
                cursor.execute("SELECT * FROM attractions WHERE id = %s", (attraction_id,))
                row = cursor.fetchone()
                if row:
                    # Remove PostgreSQL _id
                    if "_id" in row:
                        del row["_id"]
                    return row
                return None
                
            elif self.db_type == "redis":
                data = self.connection.get(f"attraction:{attraction_id}")
                if data:
                    return json.loads(data)
                return None
                
        except Exception as e:
            logger.error(f"Error getting attraction {attraction_id}: {str(e)}")
            return None
    
    def search_attractions(self, query: Dict = None, limit: int = 10, offset: int = 0) -> List[Dict]:
        """
        Search attractions with filters.
        
        Args:
            query (dict, optional): Search filters
            limit (int): Maximum number of results
            offset (int): Result offset
            
        Returns:
            list: List of attraction data
        """
        query = query or {}
        results = []
        
        try:
            if self.db_type == "sqlite":
                with self.lock:
                    cursor = self.connection.cursor()
                    
                    # Build query
                    sql = "SELECT * FROM attractions WHERE 1=1"
                    params = []
                    
                    if "type" in query:
                        sql += " AND type = ?"
                        params.append(query["type"])
                    
                    if "city" in query:
                        sql += " AND city = ?"
                        params.append(query["city"])
                    
                    if "region" in query:
                        sql += " AND region = ?"
                        params.append(query["region"])
                    
                    # Add sorting
                    sql += " ORDER BY name_en"
                    
                    # Add pagination
                    sql += " LIMIT ? OFFSET ?"
                    params.extend([limit, offset])
                    
                    # Execute query
                    cursor.execute(sql, params)
                    rows = cursor.fetchall()
                    
                    # Convert to list of dictionaries
                    for row in rows:
                        attraction = dict(row)
                        if "data" in attraction and attraction["data"]:
                            # Parse JSON data
                            attraction.update(json.loads(attraction["data"]))
                            del attraction["data"]
                        results.append(attraction)
                    
            elif self.db_type == "postgres":
                cursor = self.postgres_connection.cursor(cursor_factory=RealDictCursor)
                sql = "SELECT * FROM attractions WHERE 1=1"
                params = []
                
                if "type" in query:
                    sql += " AND type = %s"
                    params.append(query["type"])
                
                if "city" in query:
                    sql += " AND city = %s"
                    params.append(query["city"])
                
                if "region" in query:
                    sql += " AND region = %s"
                    params.append(query["region"])
                
                # Add sorting
                sql += " ORDER BY name_en"
                
                # Add pagination
                sql += " LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                
                for row in rows:
                    # Remove PostgreSQL _id
                    if "_id" in row:
                        del row["_id"]
                    results.append(row)
                
            elif self.db_type == "redis":
                # Redis doesn't support complex queries natively
                # This is a simplified implementation for demonstration
                # In a real application, you might want to use Redis Search or a different storage for this
                keys = self.connection.keys("attraction:*")
                for key in keys[offset:offset+limit]:
                    data = self.connection.get(key)
                    if data:
                        attraction = json.loads(data)
                        
                        # Apply filters
                        if "type" in query and attraction.get("type") != query["type"]:
                            continue
                        
                        if "city" in query and attraction.get("city") != query["city"]:
                            continue
                        
                        if "region" in query and attraction.get("region") != query["region"]:
                            continue
                        
                        results.append(attraction)
                
                # Sort results by name
                results.sort(key=lambda x: x.get("name", {}).get("en", ""))
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching attractions: {str(e)}")
            return []
    
    def save_attraction(self, attraction: Dict) -> bool:
        """
        Save attraction data.
        
        Args:
            attraction (dict): Attraction data
            
        Returns:
            bool: Success status
        """
        try:
            # Ensure attraction has an ID
            if "id" not in attraction:
                return False
            
            # Set timestamps
            now = datetime.now().isoformat()
            if "updated_at" not in attraction:
                attraction["updated_at"] = now
            
            if "created_at" not in attraction:
                attraction["created_at"] = now
            
            if self.db_type == "sqlite":
                with self.lock:
                    cursor = self.connection.cursor()
                    
                    # Extract primary fields
                    attraction_id = attraction["id"]
                    name_en = attraction.get("name", {}).get("en", "")
                    name_ar = attraction.get("name", {}).get("ar", "")
                    attraction_type = attraction.get("type", "")
                    city = attraction.get("location", {}).get("city", "")
                    region = attraction.get("location", {}).get("region", "")
                    latitude = attraction.get("location", {}).get("coordinates", {}).get("latitude")
                    longitude = attraction.get("location", {}).get("coordinates", {}).get("longitude")
                    description_en = attraction.get("description", {}).get("en", "")
                    description_ar = attraction.get("description", {}).get("ar", "")
                    
                    # Store full data as JSON
                    data_json = json.dumps(attraction)
                    
                    # Check if attraction exists
                    cursor.execute("SELECT COUNT(*) FROM attractions WHERE id = ?", (attraction_id,))
                    count = cursor.fetchone()[0]
                    
                    if count > 0:
                        # Update existing attraction
                        cursor.execute("""
                            UPDATE attractions 
                            SET name_en = ?, name_ar = ?, type = ?, city = ?, region = ?,
                                latitude = ?, longitude = ?, description_en = ?, description_ar = ?,
                                data = ?, updated_at = ?
                            WHERE id = ?
                        """, (
                            name_en, name_ar, attraction_type, city, region,
                            latitude, longitude, description_en, description_ar,
                            data_json, now, attraction_id
                        ))
                    else:
                        # Insert new attraction
                        cursor.execute("""
                            INSERT INTO attractions 
                            (id, name_en, name_ar, type, city, region,
                             latitude, longitude, description_en, description_ar,
                             data, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            attraction_id, name_en, name_ar, attraction_type, city, region,
                            latitude, longitude, description_en, description_ar,
                            data_json, now, now
                        ))
                    
                    self.connection.commit()
                    return True
                    
            elif self.db_type == "postgres":
                cursor = self.postgres_connection.cursor()
                # Define filter for upsert
                filter_doc = {"id": attraction["id"]}
                
                # Upsert document
                cursor.execute("""
                    INSERT INTO attractions (id, name_en, name_ar, type, city, region,
                     latitude, longitude, description_en, description_ar,
                     data, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE
                    SET name_en = EXCLUDED.name_en, name_ar = EXCLUDED.name_ar, type = EXCLUDED.type, city = EXCLUDED.city, region = EXCLUDED.region,
                        latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude, description_en = EXCLUDED.description_en, description_ar = EXCLUDED.description_ar,
                        data = EXCLUDED.data, updated_at = EXCLUDED.updated_at
                """, (
                    attraction["id"], attraction["name_en"], attraction["name_ar"], attraction["type"], attraction["city"], attraction["region"],
                    attraction["latitude"], attraction["longitude"], attraction["description_en"], attraction["description_ar"],
                    json.dumps(attraction["data"]), attraction["created_at"], attraction["updated_at"]
                ))
                self.postgres_connection.commit()
                return True
                
            elif self.db_type == "redis":
                # Store as JSON
                key = f"attraction:{attraction['id']}"
                self.connection.set(key, json.dumps(attraction))
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error saving attraction: {str(e)}")
            return False
    
    def delete_attraction(self, attraction_id: str) -> bool:
        """
        Delete attraction by ID.
        
        Args:
            attraction_id (str): Attraction ID
            
        Returns:
            bool: Success status
        """
        try:
            if self.db_type == "sqlite":
                with self.lock:
                    cursor = self.connection.cursor()
                    cursor.execute("DELETE FROM attractions WHERE id = ?", (attraction_id,))
                    self.connection.commit()
                    return cursor.rowcount > 0
                    
            elif self.db_type == "postgres":
                cursor = self.postgres_connection.cursor()
                cursor.execute("DELETE FROM attractions WHERE id = %s", (attraction_id,))
                self.postgres_connection.commit()
                return cursor.rowcount > 0
                
            elif self.db_type == "redis":
                key = f"attraction:{attraction_id}"
                count = self.connection.delete(key)
                return count > 0
                
            return False
            
        except Exception as e:
            logger.error(f"Error deleting attraction {attraction_id}: {str(e)}")
            return False
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Get session by ID.
        
        Args:
            session_id (str): Session ID
            
        Returns:
            dict: Session data if found, None otherwise
        """
        try:
            if self.db_type == "sqlite":
                with self.lock:
                    cursor = self.connection.cursor()
                    cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
                    row = cursor.fetchone()
                    
                    if row:
                        session = dict(row)
                        if "data" in session and session["data"]:
                            # Parse JSON data
                            session_data = json.loads(session["data"])
                            return session_data
                    
                    return None
                    
            elif self.db_type == "postgres":
                cursor = self.postgres_connection.cursor(cursor_factory=RealDictCursor)
                cursor.execute("SELECT * FROM sessions WHERE id = %s", (session_id,))
                row = cursor.fetchone()
                if row:
                    # Remove PostgreSQL _id
                    if "_id" in row:
                        del row["_id"]
                    return row
                return None
                
            elif self.db_type == "redis":
                data = self.connection.get(f"session:{session_id}")
                if data:
                    return json.loads(data)
                return None
                
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {str(e)}")
            return None
    
    def save_session(self, session_id: str, session_data: Dict) -> bool:
        """
        Save session data.
        
        Args:
            session_id (str): Session ID
            session_data (dict): Session data
            
        Returns:
            bool: Success status
        """
        try:
            # Ensure session has timestamps
            now = datetime.now().isoformat()
            session_data["last_activity"] = now
            
            if "created_at" not in session_data:
                session_data["created_at"] = now
            
            expires_at = session_data.get("expires_at", now)
            
            if self.db_type == "sqlite":
                with self.lock:
                    cursor = self.connection.cursor()
                    
                    # Store session data as JSON
                    data_json = json.dumps(session_data)
                    
                    # Check if session exists
                    cursor.execute("SELECT COUNT(*) FROM sessions WHERE id = ?", (session_id,))
                    count = cursor.fetchone()[0]
                    
                    if count > 0:
                        # Update existing session
                        cursor.execute("""
                            UPDATE sessions 
                            SET data = ?, updated_at = ?, expires_at = ?
                            WHERE id = ?
                        """, (
                            data_json, now, expires_at, session_id
                        ))
                    else:
                        # Insert new session
                        cursor.execute("""
                            INSERT INTO sessions 
                            (id, data, created_at, updated_at, expires_at)
                            VALUES (?, ?, ?, ?, ?)
                        """, (
                            session_id, data_json, now, now, expires_at
                        ))
                    
                    self.connection.commit()
                    return True
                    
            elif self.db_type == "postgres":
                cursor = self.postgres_connection.cursor()
                # Define filter for upsert
                filter_doc = {"id": session_id}
                
                # Upsert document
                cursor.execute("""
                    INSERT INTO sessions (id, data, created_at, updated_at, expires_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE
                    SET data = EXCLUDED.data, updated_at = EXCLUDED.updated_at, expires_at = EXCLUDED.expires_at
                """, (
                    session_id, json.dumps(session_data), session_data["created_at"], session_data["updated_at"], session_data["expires_at"]
                ))
                self.postgres_connection.commit()
                return True
                
            elif self.db_type == "redis":
                # Store as JSON with expiration
                key = f"session:{session_id}"
                
                # Calculate TTL in seconds
                try:
                    expires_datetime = datetime.fromisoformat(expires_at)
                    now_datetime = datetime.now()
                    ttl = int((expires_datetime - now_datetime).total_seconds())
                    
                    # Set minimum TTL to 1 second
                    ttl = max(ttl, 1)
                except (ValueError, TypeError) as e:
                    logger.error(f"Invalid expiration format: {expires_at}. Error: {str(e)}")
                    ttl = 3600
                    # Default to 1 hour if parsing fails
                    ttl = 3600
                
                # Store session with expiration
                self.connection.setex(key, ttl, json.dumps(session_data))
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error saving session {session_id}: {str(e)}")
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete session by ID.
        
        Args:
            session_id (str): Session ID
            
        Returns:
            bool: Success status
        """
        try:
            if self.db_type == "sqlite":
                with self.lock:
                    cursor = self.connection.cursor()
                    cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
                    self.connection.commit()
                    return cursor.rowcount > 0
                    
            elif self.db_type == "postgres":
                cursor = self.postgres_connection.cursor()
                cursor.execute("DELETE FROM sessions WHERE id = %s", (session_id,))
                self.postgres_connection.commit()
                return cursor.rowcount > 0
                
            elif self.db_type == "redis":
                key = f"session:{session_id}"
                count = self.connection.delete(key)
                return count > 0
                
            return False
            
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {str(e)}")
            return False
    
    def cleanup_expired_sessions(self) -> int:
        """
        Remove expired sessions.
        
        Returns:
            int: Number of sessions removed
        """
        try:
            now = datetime.now().isoformat()
            
            if self.db_type == "sqlite":
                with self.lock:
                    cursor = self.connection.cursor()
                    cursor.execute("DELETE FROM sessions WHERE expires_at < ?", (now,))
                    self.connection.commit()
                    return cursor.rowcount
                    
            elif self.db_type == "postgres":
                cursor = self.postgres_connection.cursor()
                cursor.execute("DELETE FROM sessions WHERE expires_at < %s", (now,))
                self.postgres_connection.commit()
                return cursor.rowcount
                
            elif self.db_type == "redis":
                # Redis automatically expires keys, no need to manually clean up
                return 0
                
            return 0
            
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {str(e)}")
            return 0
    
    def save_user(self, user: Dict) -> bool:
        """
        Save user data.
        
        Args:
            user (dict): User data
            
        Returns:
            bool: Success status
        """
        try:
            # Ensure user has an ID and username
            if "id" not in user or "username" not in user:
                return False
            
            # Set timestamps
            now = datetime.now().isoformat()
            if "created_at" not in user:
                user["created_at"] = now
            
            if self.db_type == "sqlite":
                with self.lock:
                    cursor = self.connection.cursor()
                    
                    # Extract primary fields
                    user_id = user["id"]
                    username = user["username"]
                    email = user.get("email", "")
                    password_hash = user.get("password_hash", "")
                    salt = user.get("salt", "")
                    role = user.get("role", "user")
                    last_login = user.get("last_login")
                    
                    # Store additional data as JSON
                    data = {**user}
                    # Remove fields that are stored separately
                    for field in ["id", "username", "email", "password_hash", "salt", "role", "created_at", "last_login"]:
                        if field in data:
                            del data[field]
                    
                    data_json = json.dumps(data) if data else None
                    
                    # Check if user exists
                    cursor.execute("SELECT COUNT(*) FROM users WHERE id = ?", (user_id,))
                    count = cursor.fetchone()[0]
                    
                    if count > 0:
                        # Update existing user
                        cursor.execute("""
                            UPDATE users 
                            SET username = ?, email = ?, password_hash = ?, salt = ?,
                                role = ?, data = ?, last_login = ?
                            WHERE id = ?
                        """, (
                            username, email, password_hash, salt,
                            role, data_json, last_login, user_id
                        ))
                    else:
                        # Insert new user
                        cursor.execute("""
                            INSERT INTO users 
                            (id, username, email, password_hash, salt,
                             role, data, created_at, last_login)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            user_id, username, email, password_hash, salt,
                            role, data_json, user["created_at"], last_login
                        ))
                    
                    self.connection.commit()
                    return True
                    
            elif self.db_type == "postgres":
                cursor = self.postgres_connection.cursor()
                # Define filter for upsert
                filter_doc = {"id": user["id"]}
                
                # Upsert document
                cursor.execute("""
                    INSERT INTO users (id, username, email, password_hash, salt,
                     role, data, created_at, last_login)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE
                    SET username = EXCLUDED.username, email = EXCLUDED.email, password_hash = EXCLUDED.password_hash, salt = EXCLUDED.salt,
                        role = EXCLUDED.role, data = EXCLUDED.data, last_login = EXCLUDED.last_login
                """, (
                    user["id"], user["username"], user["email"], user["password_hash"], user["salt"],
                    user["role"], json.dumps(user["data"]), user["created_at"], user["last_login"]
                ))
                self.postgres_connection.commit()
                return True
                
            elif self.db_type == "redis":
                # Store as JSON
                key = f"user:{user['id']}"
                username_key = f"username:{user['username']}"
                email_key = f"email:{user.get('email', '')}"
                
                # Use a pipeline for atomic operations
                pipeline = self.connection.pipeline()
                
                # Store user data
                pipeline.set(key, json.dumps(user))
                
                # Store username and email references
                pipeline.set(username_key, user['id'])
                if user.get('email'):
                    pipeline.set(email_key, user['id'])
                
                # Execute pipeline
                pipeline.execute()
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error saving user: {str(e)}")
            return False
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """
        Get user by ID.
        
        Args:
            user_id (str): User ID
            
        Returns:
            dict: User data if found, None otherwise
        """
        try:
            if self.db_type == "sqlite":
                with self.lock:
                    cursor = self.connection.cursor()
                    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
                    row = cursor.fetchone()
                    
                    if row:
                        user = dict(row)
                        if "data" in user and user["data"]:
                            # Parse JSON data
                            user_data = json.loads(user["data"])
                            user.update(user_data)
                            del user["data"]
                        return user
                    
                    return None
                    
            elif self.db_type == "postgres":
                cursor = self.postgres_connection.cursor(cursor_factory=RealDictCursor)
                cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                row = cursor.fetchone()
                if row:
                    # Remove PostgreSQL _id
                    if "_id" in row:
                        del row["_id"]
                    return row
                return None
                
            elif self.db_type == "redis":
                data = self.connection.get(f"user:{user_id}")
                if data:
                    return json.loads(data)
                return None
                
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {str(e)}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """
        Get user by username.
        
        Args:
            username (str): Username
            
        Returns:
            dict: User data if found, None otherwise
        """
        try:
            if self.db_type == "sqlite":
                with self.lock:
                    cursor = self.connection.cursor()
                    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
                    row = cursor.fetchone()
                    
                    if row:
                        user = dict(row)
                        if "data" in user and user["data"]:
                            # Parse JSON data
                            user_data = json.loads(user["data"])
                            user.update(user_data)
                            del user["data"]
                        return user
                    
                    return None
                    
            elif self.db_type == "postgres":
                cursor = self.postgres_connection.cursor(cursor_factory=RealDictCursor)
                cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
                row = cursor.fetchone()
                if row:
                    # Remove PostgreSQL _id
                    if "_id" in row:
                        del row["_id"]
                    return row
                return None
                
            elif self.db_type == "redis":
                # Get user ID from username reference
                user_id = self.connection.get(f"username:{username}")
                if user_id:
                    # Get user data using ID
                    data = self.connection.get(f"user:{user_id.decode('utf-8')}")
                    if data:
                        return json.loads(data)
                return None
                
        except Exception as e:
            logger.error(f"Error getting user by username {username}: {str(e)}")
            return None
    
    def _numpy_converter(self, obj):
        """Convert NumPy types to standard Python types for JSON serialization."""
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (datetime, date)): # Handle datetime as well if needed
            return obj.isoformat()
        # Let the default encoder raise the TypeError for other types
        raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')

    def log_analytics_event(self, event_type: str, event_data: dict,
                            session_id: str = None, user_id: str = None) -> bool:
        """
        Log an analytics event to the database.

        Args:
            event_type (str): Type of event
            event_data (dict): Event data
            session_id (str, optional): Session ID
            user_id (str, optional): User ID

        Returns:
            bool: Success flag
        """
        try:
            # Create event document
            event = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                # Use the custom converter for JSON serialization
                "event_data": json.dumps(event_data, default=self._numpy_converter),
                "session_id": session_id,
                "user_id": user_id
            }

            if self.db_type == "sqlite":
                with self.lock:
                    cursor = self.connection.cursor()
                    # Generate UUID for SQLite ID
                    event_id = str(uuid.uuid4())
                    cursor.execute("""
                        INSERT INTO analytics (id, session_id, user_id, event_type, event_data, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (event_id, session_id, user_id, event_type, event['event_data'], event['timestamp']))
                    self.connection.commit()
                return True
            elif self.db_type == "postgres":
                cursor = self.postgres_connection.cursor()
                cursor.execute("""
                    INSERT INTO analytics (id, session_id, user_id, event_type, event_data, timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    event_id, session_id, user_id, event_type, event['event_data'], event['timestamp']
                ))
                self.postgres_connection.commit()
                return True
            else:
                # Handle other DB types or log unsupported operation
                logger.warning(f"Analytics logging only implemented for SQLite and PostgreSQL. DB type: {self.db_type}") # Adjusted warning
                return False

        except Exception as e:
            logger.error(f"Error logging analytics event: {str(e)}", exc_info=True)
            return False

    def get_analytics_events(self, filters: dict = None, limit: int = 1000,
                             skip: int = 0, sort_by: str = "timestamp",
                             sort_dir: int = -1) -> list:
        """
        Get analytics events from the database.

        Args:
            filters (dict, optional): Query filters
            limit (int, optional): Maximum number of events to return
            skip (int, optional): Number of events to skip
            sort_by (str, optional): Field to sort by
            sort_dir (int, optional): Sort direction (1 for ascending, -1 for descending)

        Returns:
            list: List of events
        """
        try:
            if self.db_type == "sqlite":
                 with self.lock:
                    cursor = self.connection.cursor()
                    query_parts = []
                    params = []

                    if filters:
                        # Add specific filter handling for SQLite here
                        # Example:
                        if "event_type" in filters:
                            query_parts.append("event_type = ?")
                            params.append(filters["event_type"])
                        if "session_id" in filters:
                            query_parts.append("session_id = ?")
                            params.append(filters["session_id"])
                        # Add timestamp range filters if needed

                    base_query = "SELECT * FROM analytics"
                    if query_parts:
                        base_query += " WHERE " + " AND ".join(query_parts)

                    # Add sorting
                    order_clause = f" ORDER BY {sort_by} {'ASC' if sort_dir == 1 else 'DESC'}"
                    base_query += order_clause

                    # Add limit and offset
                    base_query += f" LIMIT {limit} OFFSET {skip}"

                    cursor.execute(base_query, params)
                    rows = cursor.fetchall()
                    # Convert rows to dicts and parse JSON data
                    events = []
                    for row in rows:
                        event = dict(row)
                        if event.get('event_data'):
                            try:
                                event['event_data'] = json.loads(event['event_data'])
                            except json.JSONDecodeError:
                                logger.warning(f"Could not decode event_data for event ID {event.get('id')}")
                                event['event_data'] = None # Or keep as string?
                        events.append(event)
                    return events

            elif self.db_type == "postgres":
                cursor = self.postgres_connection.cursor(cursor_factory=RealDictCursor)
                query_parts = []
                params = []

                if filters:
                    # Add specific filter handling for PostgreSQL here
                    # Example:
                    if "event_type" in filters:
                        query_parts.append("event_type = %s")
                        params.append(filters["event_type"])
                    if "session_id" in filters:
                        query_parts.append("session_id = %s")
                        params.append(filters["session_id"])
                    # Add timestamp range filters if needed

                base_query = "SELECT * FROM analytics"
                if query_parts:
                    base_query += " WHERE " + " AND ".join(query_parts)

                # Add sorting
                order_clause = f" ORDER BY {sort_by} {'ASC' if sort_dir == 1 else 'DESC'}"
                base_query += order_clause

                # Add limit and offset
                base_query += f" LIMIT {limit} OFFSET {skip}"

                cursor.execute(base_query, params)
                rows = cursor.fetchall()
                # Convert rows to dicts and parse JSON data
                events = []
                for row in rows:
                    event = dict(row)
                    if event.get('event_data'):
                        try:
                            event['event_data'] = json.loads(event['event_data'])
                        except json.JSONDecodeError:
                            logger.warning(f"Could not decode event_data for event ID {event.get('id')}")
                            event['event_data'] = None # Or keep as string?
                    events.append(event)
                return events

            else:
                logger.warning(f"Getting analytics events only implemented for SQLite and PostgreSQL. DB type: {self.db_type}")
                return []

        except Exception as e:
            logger.error(f"Error getting analytics events: {str(e)}", exc_info=True)
            return []

    def get_analytics_aggregation(self, pipeline: list) -> list:
         """
         Run an aggregation pipeline on analytics events.

         Args:
             pipeline (list): Aggregation pipeline (syntax may vary by DB type)

         Returns:
             list: Aggregation results
         """
         try:
             if self.db_type == "sqlite":
                 # SQLite does not directly support complex aggregation pipelines like PostgreSQL.
                 # This would require translating the pipeline logic into complex SQL GROUP BY queries,
                 # which is beyond the scope of a simple replacement.
                 # For now, log a warning or raise NotImplementedError.
                 logger.warning("SQLite does not support complex aggregation pipelines directly.")
                 return [] # Or raise NotImplementedError("Aggregation not implemented for SQLite")
             elif self.db_type == "postgres":
                 # PostgreSQL does not directly support complex aggregation pipelines like SQLite.
                 # This would require translating the pipeline logic into complex SQL GROUP BY queries,
                 # which is beyond the scope of a simple replacement.
                 # For now, log a warning or raise NotImplementedError.
                 logger.warning("PostgreSQL does not support complex aggregation pipelines directly.")
                 return [] # Or raise NotImplementedError("Aggregation not implemented for PostgreSQL")
             else:
                 logger.warning(f"Analytics aggregation only implemented for SQLite and PostgreSQL. DB type: {self.db_type}")
                 return []

         except Exception as e:
             logger.error(f"Error running analytics aggregation: {str(e)}", exc_info=True)
             return []

    def delete_old_analytics_events(self, days: int = 90) -> Tuple[bool, int]:
         """
         Delete analytics events older than the specified number of days.

         Args:
             days (int): Number of days to keep

         Returns:
             Tuple[bool, int]: Success flag and number of deleted records
         """
         deleted_count = 0
         try:
             # Calculate cutoff date
             cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

             if self.db_type == "sqlite":
                 with self.lock:
                    cursor = self.connection.cursor()
                    # First count how many will be deleted
                    cursor.execute("SELECT COUNT(*) FROM analytics WHERE timestamp < ?", (cutoff_date,))
                    count_result = cursor.fetchone()
                    deleted_count = count_result[0] if count_result else 0

                    # Then delete
                    if deleted_count > 0:
                        cursor.execute("DELETE FROM analytics WHERE timestamp < ?", (cutoff_date,))
                        self.connection.commit()
                    logger.info(f"Deleted {deleted_count} old analytics events (SQLite)")
                    return True, deleted_count
             elif self.db_type == "postgres":
                 cursor = self.postgres_connection.cursor()
                 # First count how many will be deleted
                 cursor.execute("SELECT COUNT(*) FROM analytics WHERE timestamp < %s", (cutoff_date,))
                 count_result = cursor.fetchone()
                 deleted_count = count_result[0] if count_result else 0

                 # Then delete
                 if deleted_count > 0:
                     cursor.execute("DELETE FROM analytics WHERE timestamp < %s", (cutoff_date,))
                     self.postgres_connection.commit()
                 logger.info(f"Deleted {deleted_count} old analytics events (PostgreSQL)")
                 return True, deleted_count
             else:
                 logger.warning(f"Deleting old analytics events only implemented for SQLite and PostgreSQL. DB type: {self.db_type}")
                 return False, 0

         except Exception as e:
             logger.error(f"Error deleting old analytics events: {str(e)}", exc_info=True)
             return False, deleted_count

    # --- NEW Feedback Logging Method ---

    def log_feedback(self, message_id: str, rating: int, comment: Optional[str] = None,
                       session_id: Optional[str] = None, user_id: Optional[str] = None) -> bool:
        """Logs user feedback as a specific analytics event.

        Args:
            message_id (str): The ID of the message being rated.
            rating (int): The feedback rating (e.g., 1-5).
            comment (str, optional): Optional user comment.
            session_id (str, optional): The session ID associated with the feedback.
            user_id (str, optional): The user ID associated with the feedback.

        Returns:
            bool: True if logging was successful, False otherwise.
        """
        logger.debug(f"Logging feedback for message {message_id}: rating={rating}")
        event_data = {
            "message_id": message_id,
            "rating": rating,
            "comment": comment,
            "is_positive": rating >= 4 # Example heuristic for positive/negative
        }
        
        return self.log_analytics_event(
            event_type="user_feedback",
            event_data=event_data,
            session_id=session_id,
            user_id=user_id
        )
    # --- END Feedback Logging Method ---

    # ---- Accommodation Methods ----

    def search_accommodations(self, query: Dict = None, limit: int = 10, offset: int = 0) -> List[Dict]:
        """(Placeholder) Search accommodations."""
        logger.warning("search_accommodations not fully implemented yet.")
        # TODO: Implement based on search_attractions logic
        return []

    def get_accommodation(self, accommodation_id: str) -> Optional[Dict]:
        """(Placeholder) Get accommodation by ID."""
        logger.warning(f"get_accommodation({accommodation_id}) not implemented yet.")
        # TODO: Implement based on get_attraction logic
        return None

    def save_accommodation(self, accommodation: Dict) -> bool:
        """(Placeholder) Save accommodation data."""
        logger.warning("save_accommodation not implemented yet.")
        # TODO: Implement based on save_attraction logic
        return False

    def delete_accommodation(self, accommodation_id: str) -> bool:
        """(Placeholder) Delete accommodation by ID."""
        logger.warning(f"delete_accommodation({accommodation_id}) not implemented yet.")
        # TODO: Implement based on delete_attraction logic
        return False

    # ---- Restaurant Methods ----

    def search_restaurants(self, query: Dict = None, limit: int = 10, offset: int = 0) -> List[Dict]:
        """(Placeholder) Search restaurants."""
        logger.warning("search_restaurants not fully implemented yet.")
        # TODO: Implement based on search_attractions logic
        return []

    def get_restaurant(self, restaurant_id: str) -> Optional[Dict]:
        """(Placeholder) Get restaurant by ID."""
        logger.warning(f"get_restaurant({restaurant_id}) not implemented yet.")
        # TODO: Implement based on get_attraction logic
        return None

    def save_restaurant(self, restaurant: Dict) -> bool:
        """(Placeholder) Save restaurant data."""
        logger.warning("save_restaurant not implemented yet.")
        # TODO: Implement based on save_attraction logic
        return False

    def delete_restaurant(self, restaurant_id: str) -> bool:
        """(Placeholder) Delete restaurant by ID."""
        logger.warning(f"delete_restaurant({restaurant_id}) not implemented yet.")
        # TODO: Implement based on delete_attraction logic
        return False

    # ---- Utility Methods ----
    def _build_sqlite_query(self, table_name: str, query: Dict = None, limit: int = 10, offset: int = 0) -> Tuple[str, List]:
        """
        Build SQLite query from dictionary.
        (This is a placeholder and needs implementation based on query structure)
        """
        sql = f"SELECT * FROM {table_name} WHERE 1=1"
        params = []
        # TODO: Implement query building based on query dict
        sql += f" LIMIT {limit} OFFSET {offset}"
        return sql, params