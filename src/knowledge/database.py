"""
Database module for the Egypt Tourism Chatbot.
Provides database connectivity and operations for persistent storage.
"""
import json
import os
import threading
from enum import Enum
import psycopg2
from psycopg2 import pool, errors
from psycopg2.extras import RealDictCursor, DictCursor
from typing import Any, Dict, List, Optional, Tuple, Union
import math
import time

from src.utils.logger import get_logger
from src.knowledge.vector_cache import VectorSearchCache

logger = get_logger(__name__)

class DatabaseType(Enum):
    POSTGRES = "postgres"

class DatabaseManager:
    def __enter__(self):
        """Support context manager pattern for automatic resource cleanup."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close connections when exiting context manager."""
        self.close()
        
    def close(self):
        """Close the database connection."""
        try:
            if hasattr(self, 'pg_pool') and self.pg_pool:
                self.pg_pool.closeall()
                self.pg_pool = None
                logger.info("Closed PostgreSQL connection pool.")
        except Exception as e:
            logger.error(f"Error closing PostgreSQL connection pool: {e}")

    def __init__(self, database_uri: str = None, vector_dimension: int = 1536):
        """Initialize the database manager."""
        # Print env vars and args for debugging
        print(f"[DB INIT DEBUG] POSTGRES_URI={os.environ.get('POSTGRES_URI')}")
        print(f"[DB INIT DEBUG] database_uri arg: {database_uri}")
        self.db_type = DatabaseType.POSTGRES
        self.database_uri = database_uri or os.environ.get("POSTGRES_URI")
        logger.info(f"Database type determined: {self.db_type}")

        # Set vector dimension
        self.vector_dimension = vector_dimension
        
        # Define valid tables for whitelist checking
        self.VALID_TABLES = {'attractions', 'restaurants', 'accommodations', 'cities', 
                          'regions', 'users', 'hotels', 'vector_search_metrics', 'vector_indexes'}

        # Initialize connection attributes
        self.pg_pool = None
        self.lock = threading.RLock()
        
        # Set shorter timeout for tests
        self.operation_timeout = 2 if os.environ.get('TESTING') == 'true' else 10
        
        # Initialize vector search cache
        redis_uri = os.environ.get("REDIS_URI")
        self.vector_cache = VectorSearchCache(
            redis_uri=redis_uri,
            ttl=3600,  # Cache vector search results for 1 hour
            max_size=1000  # Maximum size of local LRU cache
        )
        logger.info("Initialized vector search cache")
        
        # Connect to PostgreSQL
        self.connect()

    def connect(self):
        """Establish database connection (PostgreSQL only)."""
        return self._initialize_postgres_connection()

    def _initialize_postgres_connection(self) -> bool:
        """Initialize PostgreSQL connection with pool."""
        try:
            # Test if we have superuser privileges for PostGIS
            has_superuser = False
            try:
                # Use the provided database URI
                test_conn = psycopg2.connect(self.database_uri)
                with test_conn.cursor() as cursor:
                    cursor.execute("SELECT rolsuper FROM pg_roles WHERE rolname = CURRENT_USER")
                    result = cursor.fetchone()
                    has_superuser = result[0] if result else False
                test_conn.close()
            except Exception as e:
                logger.warning(f"Could not check superuser status: {str(e)}")
                return False  # Return False early if we can't connect

            # Create the connection pool
            min_conn = 1
            max_conn = 3 if os.environ.get('TESTING') == 'true' else 10
            
            logger.info(f"Creating PostgreSQL connection pool (min={min_conn}, max={max_conn})...")
            # Use the provided database URI instead of hardcoded connection
            self.pg_pool = pool.ThreadedConnectionPool(
                minconn=min_conn,
                maxconn=max_conn,
                dsn=self.database_uri
            )
            
            # Test the pool and create schema
            conn = self.pg_pool.getconn()
            if not conn:
                logger.error("Failed to get connection from pool")
                return False
                
            try:
                conn.autocommit = True  # For extension creation
                
                # Try to create PostGIS extension if we have privileges
                if has_superuser:
                    with conn.cursor() as cursor:
                        try:
                            cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis")
                            logger.info("PostGIS extension enabled successfully")
                        except Exception as e:
                            logger.warning(f"Could not enable PostGIS: {str(e)}")
                else:
                    logger.info("Skipping PostGIS creation - requires superuser privileges")
                
                # Switch back to normal transaction mode
                conn.autocommit = False
                
                # Create tables and indexes
                self._create_postgres_tables()
                
                logger.info("PostgreSQL initialization completed successfully")
                return True
                
            finally:
                if conn:
                    try:
                        conn.autocommit = False
                    except:
                        pass
                    self._return_pg_connection(conn)
                    
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL: {str(e)}")
            if self.pg_pool:
                try:
                    self.pg_pool.closeall()
                except:
                    pass
            self.pg_pool = None
            return False

    def _create_postgres_tables(self):
        """Create required tables in PostgreSQL if they don't exist."""
        conn = self._get_pg_connection()
        try:
            with conn.cursor() as cursor:
                # Create users table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id TEXT PRIMARY KEY,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE,
                        password_hash TEXT,
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMPTZ,
                        preferences JSONB
                    )
                """)

                # Create attractions table with proper columns
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS attractions (
                        id TEXT PRIMARY KEY,
                        name_en TEXT NOT NULL,
                        name_ar TEXT,
                        type TEXT,
                        city TEXT,
                        region TEXT,
                        latitude DOUBLE PRECISION,
                        longitude DOUBLE PRECISION,
                        description_en TEXT,
                        description_ar TEXT,
                        data JSONB,
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        user_id TEXT REFERENCES users(id) ON DELETE SET NULL,
                        embedding vector(%s)
                    )
                """, (self.vector_dimension,))

                # Create restaurants table with correct structure including latitude/longitude
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS restaurants (
                        id TEXT PRIMARY KEY,
                        name_en TEXT NOT NULL,
                        name_ar TEXT,
                        cuisine TEXT,
                        city TEXT,
                        region TEXT,
                        latitude DOUBLE PRECISION,
                        longitude DOUBLE PRECISION,
                        description_en TEXT,
                        description_ar TEXT,
                        data JSONB,
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        user_id TEXT REFERENCES users(id) ON DELETE SET NULL,
                        embedding vector(%s)
                    )
                """, (self.vector_dimension,))

                # Create accommodations table (hotels)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS accommodations (
                        id TEXT PRIMARY KEY,
                        name_en TEXT NOT NULL,
                        name_ar TEXT,
                        type TEXT,
                        city TEXT,
                        region TEXT,
                        latitude DOUBLE PRECISION,
                        longitude DOUBLE PRECISION,
                        description_en TEXT,
                        description_ar TEXT, 
                        data JSONB,
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        user_id TEXT REFERENCES users(id) ON DELETE SET NULL,
                        embedding vector(%s)
                    )
                """, (self.vector_dimension,))

                # Create cities table with vector support
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS cities (
                        id TEXT PRIMARY KEY,
                        name_en TEXT NOT NULL,
                        name_ar TEXT,
                        region TEXT,
                        latitude DOUBLE PRECISION,
                        longitude DOUBLE PRECISION,
                        description_en TEXT,
                        description_ar TEXT,
                        data JSONB,
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        user_id TEXT REFERENCES users(id) ON DELETE SET NULL,
                        embedding vector(%s)
                    )
                """, (self.vector_dimension,))

                # Create regions table with vector support
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS regions (
                        id TEXT PRIMARY KEY,
                        name_en TEXT NOT NULL,
                        name_ar TEXT,
                        country TEXT,
                        latitude DOUBLE PRECISION,
                        longitude DOUBLE PRECISION,
                        description_en TEXT,
                        description_ar TEXT,
                        data JSONB,
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        user_id TEXT REFERENCES users(id) ON DELETE SET NULL,
                        embedding vector(%s)
                    )
                """, (self.vector_dimension,))

                # Create analytics events table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS analytics_events (
                        id SERIAL PRIMARY KEY,
                        event_type TEXT NOT NULL,
                        event_data JSONB,
                        session_id TEXT,
                        user_id TEXT,
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create feedback table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS feedback (
                        id SERIAL PRIMARY KEY,
                        message_id TEXT,
                        session_id TEXT,
                        user_id TEXT,
                        rating INTEGER,
                        comment TEXT,
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Create indexes
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_attractions_name ON attractions (name_en, name_ar)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_attractions_type ON attractions (type)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_attractions_city ON attractions (city)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_attractions_user ON attractions (user_id)')
                
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_restaurants_name ON restaurants (name_en, name_ar)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_restaurants_cuisine ON restaurants (cuisine)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_restaurants_city ON restaurants (city)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_restaurants_user ON restaurants (user_id)')
                
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_accommodations_name ON accommodations (name_en, name_ar)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_accommodations_type ON accommodations (type)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_accommodations_city ON accommodations (city)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_accommodations_user ON accommodations (user_id)')
                
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_cities_name ON cities (name_en, name_ar)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_cities_region ON cities (region)')
                
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_regions_name ON regions (name_en, name_ar)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_regions_country ON regions (country)')

                # Create spatial index if PostGIS extension exists
                cursor.execute("SELECT 1 FROM pg_extension WHERE extname = 'postgis'")
                if cursor.fetchone():
                    # Add geometry columns to appropriate tables
                    tables_with_geo = ["attractions", "restaurants", "accommodations", "cities", "regions"]
                    for table in tables_with_geo:
                        cursor.execute(f"""
                            ALTER TABLE {table} ADD COLUMN IF NOT EXISTS geom geometry(Point, 4326);
                            CREATE INDEX IF NOT EXISTS idx_{table}_geom ON {table} USING GIST (geom);
                        """)

                conn.commit()
                logger.info("Tables and indexes created successfully")

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to create PostgreSQL tables: {str(e)}")
            raise

        finally:
            if conn:
                self._return_pg_connection(conn)

    def _get_pg_connection(self):
        """Get a connection from the pool with retry logic."""
        if not self.pg_pool:
            logger.error("No PostgreSQL connection pool available")
            return None
            
        retries = 3
        for attempt in range(retries):
            try:
                conn = self.pg_pool.getconn()
                if not conn.closed:
                    return conn
                    
                logger.warning("Got closed connection from pool, attempting to reconnect...")
                self.pg_pool.putconn(conn)
                
            except Exception as e:
                logger.error(f"Error getting connection on attempt {attempt + 1}: {str(e)}")
                if attempt == retries - 1:
                    return None
                    
        return None

    def _return_pg_connection(self, conn):
        """Safely return a connection to the pool."""
        if self.pg_pool and conn:
            try:
                if not conn.closed:
                    self.pg_pool.putconn(conn)
                else:
                    logger.warning("Attempted to return closed connection to pool")
            except Exception as e:
                logger.error(f"Error returning connection to pool: {str(e)}")

    def execute_postgres_query(self, query, params=None, fetchall=True, cursor_factory=None):
        """Execute a PostgreSQL query using the connection pool."""
        if self.db_type != DatabaseType.POSTGRES:
            logger.error("Attempted to execute PostgreSQL query when not using PostgreSQL")
            return None
            
        conn = None
        try:
            conn = self._get_pg_connection()
            if not conn:
                logger.error("Failed to get PostgreSQL connection")
                return None
                
            cursor_factory = cursor_factory or RealDictCursor
            with conn.cursor(cursor_factory=cursor_factory) as cursor:
                cursor.execute(query, params or ())
                
                if query.strip().upper().startswith(("SELECT", "WITH")):
                    result = cursor.fetchall() if fetchall else cursor.fetchone()
                else:
                    conn.commit()
                    result = cursor.rowcount
                    
                return result
                
        except Exception as e:
            logger.error(f"Error executing PostgreSQL query: {str(e)}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            if conn and not conn.closed:
                try:
                    conn.rollback()
                except Exception as rb_err:
                    logger.error(f"Error during rollback: {str(rb_err)}")
            return None
            
        finally:
            if conn:
                self._return_pg_connection(conn)

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a database query and return results as a list of dictionaries (PostgreSQL only)."""
        logger.debug(f"[DB QUERY] SQL: {query}\nParams: {params}")
        return self.execute_postgres_query(query, params)

    def get_attraction(self, attraction_id):
        """
        Get attraction by ID (PostgreSQL only).
        Args:
            attraction_id (str): ID of the attraction
        Returns:
            dict: Attraction data or None if not found
        """
        logger.info(f"DatabaseManager.get_attraction called for ID: {attraction_id}")
        try:
            sql = """
                SELECT id, name_en, name_ar, description_en, description_ar,
                       type, city, region, latitude, longitude, data,
                       created_at, updated_at
                FROM attractions 
                WHERE id = %s
            """
            logger.info(f"Executing PostgreSQL query: {sql} with params ({attraction_id},)")
            result = self.execute_postgres_query(sql, (attraction_id,), fetchall=False)
            if result:
                # Parse JSON data if present
                if 'data' in result and result['data']:
                    try:
                        result['data'] = json.loads(result['data'])
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse JSON data for attraction {attraction_id}")
                logger.info(f"Successfully retrieved attraction {attraction_id}")
                return result
            else:
                logger.info(f"No attraction found with ID {attraction_id}")
                return None
        except Exception as e:
            logger.error(f"Error getting attraction {attraction_id} from PostgreSQL: {str(e)}")
            return None

    def get_restaurant(self, restaurant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get restaurant by ID.
        Schema: restaurants(id, name_en, name_ar, description_en, description_ar, ...)
        Returns: dict or None
        """
        logger.info(f"Called get_restaurant for ID: {restaurant_id}")
        try:
            sql = """
                SELECT id, name_en, name_ar, description_en, description_ar,
                       cuisine, city, region, latitude, longitude, data,
                       created_at, updated_at
                FROM restaurants 
                WHERE id = %s
            """
            result = self.execute_postgres_query(sql, (restaurant_id,), fetchall=False)
            if result:
                # Parse JSON data if present
                if 'data' in result and result['data']:
                    if isinstance(result['data'], str):
                        try:
                            result['data'] = json.loads(result['data'])
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse JSON data for restaurant {restaurant_id}")
                return result
            return None
        except Exception as e:
            logger.error(f"Error getting restaurant {restaurant_id}: {e}")
            return None

    def get_city(self, city_id: str) -> Optional[Dict[str, Any]]:
        """
        Get city by ID (PostgreSQL only).
        Returns: dict or None
        """
        logger.info(f"Called get_city for ID: {city_id}")
        try:
            sql = "SELECT * FROM cities WHERE id = %s"
            result = self.execute_postgres_query(sql, (city_id,), fetchall=False)
            if result:
                if "data" in result and result["data"]:
                    try:
                        result["data"] = json.loads(result["data"])
                    except Exception:
                        pass
                return result
            return None
        except Exception as e:
            logger.error(f"Error fetching city {city_id}: {e}")
            return None

    def get_accommodation(self, accommodation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get accommodation by ID.
        Schema: accommodations(id, ...)
        Returns: dict or None
        """
        logger.info(f"Called get_accommodation for ID: {accommodation_id}")
        try:
            sql = """
                SELECT id, name_en, name_ar, description_en, description_ar,
                       type, city, region, latitude, longitude, data,
                       created_at, updated_at
                FROM accommodations 
                WHERE id = %s
            """
            result = self.execute_postgres_query(sql, (accommodation_id,), fetchall=False)
            if result:
                # Parse JSON data if present
                if 'data' in result and result['data']:
                    if isinstance(result['data'], str):
                        try:
                            result['data'] = json.loads(result['data'])
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse JSON data for accommodation {accommodation_id}")
                return result
            return None
        except Exception as e:
            logger.error(f"Error getting accommodation {accommodation_id}: {e}")
            return None

    def get_region(self, region_id: str) -> Optional[Dict[str, Any]]:
        """
        Get region by ID.
        Schema: regions(id, ...)
        Returns: dict or None
        """
        logger.info(f"Called get_region for ID: {region_id}")
        try:
            sql = "SELECT * FROM regions WHERE id = %s"
            result = self.execute_postgres_query(sql, (region_id,), fetchall=False)
            if result:
                if "data" in result and result["data"]:
                    try:
                        result["data"] = json.loads(result["data"])
                    except Exception:
                        pass
                return result
            return None
        except Exception as e:
            logger.error(f"Error fetching region {region_id}: {e}")
            return None

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user by ID.
        Schema: users(id, username, ...)
        Returns: dict or None
        """
        logger.info(f"Called get_user for ID: {user_id}")
        try:
            sql = "SELECT * FROM users WHERE id = %s"
            result = self.execute_postgres_query(sql, (user_id,), fetchall=False)
            if result:
                if "preferences" in result and result["preferences"]:
                    try:
                        result["preferences"] = json.loads(result["preferences"])
                    except Exception:
                        pass
                return result
            return None
        except Exception as e:
            logger.error(f"Error fetching user {user_id}: {e}")
            return None

    def search_restaurants(self, query: Optional[Dict[str, Any]] = None, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Search restaurants table.
        Args: 
            query (dict): Dictionary of search criteria or text query string
            limit (int): Maximum number of results to return
            offset (int): Offset for pagination
        Returns: list of dicts
        """
        logger.info(f"Called search_restaurants with query={query}, limit={limit}, offset={offset}")
        try:
            base_query = "SELECT * FROM restaurants WHERE 1=1"
            params = []

            if query:
                if isinstance(query, str):
                    # Handle string query for text search
                    base_query += " AND (name_en ILIKE %s OR name_ar ILIKE %s OR description_en ILIKE %s OR description_ar ILIKE %s)"
                    pattern = f"%{query}%"
                    params.extend([pattern, pattern, pattern, pattern])
                else:
                    # Handle dictionary query for structured search
                    if "city" in query:
                        base_query += " AND city ILIKE %s"
                        params.append(f"%{query['city']}%")

                    if "type" in query:
                        base_query += " AND type ILIKE %s"
                        params.append(f"%{query['type']}%")
                        
                    if "cuisine" in query:
                        base_query += " AND cuisine ILIKE %s"
                        params.append(f"%{query['cuisine']}%")

                    if "name" in query:
                        base_query += " AND (name_en ILIKE %s OR name_ar ILIKE %s)"
                        name_pattern = f"%{query['name']}%"
                        params.extend([name_pattern, name_pattern])

            base_query += " LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            results = self.execute_query(base_query, tuple(params))
            return results or []
        except Exception as e:
            logger.error(f"Error searching restaurants: {e}")
            return []

    def search_cities(self, query: Optional[Dict[str, Any]] = None, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Search cities table (PostgreSQL only).
        Args: query (dict), limit (int), offset (int)
        Returns: list of dicts
        """
        logger.info(f"Called search_cities with query={query}, limit={limit}, offset={offset}")
        try:
            where_clause, params = self._build_postgres_where_clause(query or {})
            sql = f"SELECT * FROM cities"
            if where_clause:
                sql += f" WHERE {where_clause}"
            sql += " LIMIT %s OFFSET %s"
            params = list(params) + [limit, offset]
            rows = self.execute_postgres_query(sql, tuple(params))
            results = []
            for row in rows or []:
                if "data" in row and row["data"]:
                    try:
                        row["data"] = json.loads(row["data"])
                    except Exception:
                        pass
                results.append(row)
            return results
        except Exception as e:
            logger.error(f"Error searching cities: {e}")
            return []

    def search_regions(self, query: Optional[Dict[str, Any]] = None, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Search regions table.
        Args: query (dict), limit (int), offset (int)
        Returns: list of dicts
        """
        logger.info(f"Called search_regions with query={query}, limit={limit}, offset={offset}")
        try:
            where_clause, params = self._build_postgres_where_clause(query or {})
            sql = f"SELECT * FROM regions"
            if where_clause:
                sql += f" WHERE {where_clause}"
            sql += " LIMIT %s OFFSET %s"
            params = list(params) + [limit, offset]
            rows = self.execute_postgres_query(sql, tuple(params))
            results = []
            for row in rows or []:
                if "data" in row and row["data"]:
                    try:
                        row["data"] = json.loads(row["data"])
                    except Exception:
                        pass
                results.append(row)
            return results
        except Exception as e:
            logger.error(f"Error searching regions: {e}")
            return []

    def search_users(self, query: Optional[Dict[str, Any]] = None, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Search users table.
        Args: query (dict), limit (int), offset (int)
        Returns: list of dicts
        """
        logger.info(f"Called search_users with query={query}, limit={limit}, offset={offset}")
        try:
            where_clause, params = self._build_postgres_where_clause(query or {})
            sql = f"SELECT * FROM users"
            if where_clause:
                sql += f" WHERE {where_clause}"
            sql += " LIMIT %s OFFSET %s"
            params = list(params) + [limit, offset]
            return self.execute_postgres_query(sql, tuple(params)) or []
        except Exception as e:
            logger.error(f"Error searching users: {e}")
            return []

    def enhanced_search(self, table: str, search_text: str, filters: Optional[Dict[str, Any]] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Enhanced search (e.g., full-text search) on a table.
        Args: 
            table (str): Name of the table to search
            search_text (str): Text to search for
            filters (Dict[str, Any], optional): Additional filters to apply
            limit (int): Maximum number of results to return
        Returns: list of dicts
        """
        logger.info(f"Called enhanced_search on table={table} with search_text={search_text}, filters={filters}, limit={limit}")
        try:
            # Start with base query
            sql = f"""
                SELECT * FROM {table} 
                WHERE (name_en ILIKE %s OR name_ar ILIKE %s OR description_en ILIKE %s OR description_ar ILIKE %s)
            """
            pattern = f"%{search_text}%"
            params = [pattern, pattern, pattern, pattern]
            
            # Add filters if provided
            if filters:
                for key, value in filters.items():
                    if isinstance(value, dict) and '$jsonb_contains' in value:
                        # Handle JSONB contains operator
                        jsonb_value = json.dumps(value['$jsonb_contains'])
                        sql += f" AND {key} @> %s::jsonb"
                        params.append(jsonb_value)
                    else:
                        # Handle simple equality filters
                        sql += f" AND {key} = %s"
                        params.append(value)
            
            # Add limit
            sql += " LIMIT %s"
            params.append(limit)
            
            return self.execute_postgres_query(sql, tuple(params)) or []
        except Exception as e:
            logger.error(f"Error in enhanced search: {e}")
            return []

    def vector_search(self, table_name: str, embedding: list, filters: Optional[dict] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Perform a vector search with caching.

        Args:
            table_name (str): Name of the table to search.
            embedding (list): Vector embedding for similarity search.
            filters (dict, optional): Additional filters to apply.
            limit (int): Maximum number of results to return.

        Returns:
            List[Dict[str, Any]]: Search results.
        """
        # Validate table name against whitelist
        if table_name not in self.VALID_TABLES:
            logger.error(f"Invalid table name: {table_name}")
            return []
            
        # Check cache first
        cached_results = self.vector_cache.get(table_name, embedding, filters, limit)
        if cached_results is not None:
            logger.info(f"Cache hit for vector search on table {table_name}")
            return cached_results

        logger.info(f"Performing vector search on table {table_name} with embedding and filters")

        try:
            # Build the query
            sql = f"""
                SELECT *, embedding <-> %s::vector AS distance
                FROM {table_name}
                WHERE embedding IS NOT NULL
            """
            params = [embedding]

            # Add filters if provided
            if filters:
                for key, value in filters.items():
                    sql += f" AND {key} = %s"
                    params.append(value)

            # Add order by and limit
            sql += " ORDER BY distance LIMIT %s"
            params.append(limit)

            # Execute the query
            results = self.execute_postgres_query(sql, tuple(params))

            # Cache the results
            self.vector_cache.set(table_name, embedding, results, filters, limit)

            return results

        except Exception as e:
            logger.error(f"Error in vector search for table {table_name}: {e}")
            return []

    def vector_search_restaurants(self, embedding: list, filters: Optional[dict] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Vector search on restaurants table.
        Schema: restaurants(embedding VECTOR, ...)
        Args: embedding (list[float]), filters (dict), limit (int)
        Returns: list of dicts
        """
        logger.info(f"Called vector_search_restaurants with embedding, filters={filters}, limit={limit}")
        try:
            # Check if pgvector extension is available
            check_sql = "SELECT 1 FROM pg_extension WHERE extname = 'vector'"
            result = self.execute_postgres_query(check_sql)
            if not result:
                logger.error("Vector search requires the 'vector' extension")
                return []
                
            # Build the query
            sql = """
                SELECT *, embedding <-> %s::vector AS distance
                FROM restaurants
                WHERE 1=1
            """
            params = [embedding]
            
            # Add filters if provided
            if filters:
                if 'city' in filters:
                    sql += " AND city = %s"
                    params.append(filters['city'])
                if 'type' in filters:
                    sql += " AND type = %s"
                    params.append(filters['type'])
            
            sql += " ORDER BY distance LIMIT %s"
            params.append(limit)
            
            return self.execute_postgres_query(sql, tuple(params)) or []
        except Exception as e:
            logger.error(f"Error in vector search for restaurants: {e}")
            return []

    def vector_search_hotels(self, embedding: list, filters: Optional[dict] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Vector search on hotels table.
        Schema: hotels(embedding VECTOR, ...)
        Args: embedding (list[float]), filters (dict), limit (int)
        Returns: list of dicts
        """
        logger.info(f"Called vector_search_hotels with embedding, filters={filters}, limit={limit}")
        try:
            # Check if pgvector extension is available
            check_sql = "SELECT 1 FROM pg_extension WHERE extname = 'vector'"
            result = self.execute_postgres_query(check_sql)
            if not result:
                logger.error("Vector search requires the 'vector' extension")
                return []
                
            # Build the query
            sql = """
                SELECT *, embedding <-> %s::vector AS distance
                FROM accommodations
                WHERE 1=1
            """
            params = [embedding]
            
            # Add filters if provided
            if filters:
                if 'city' in filters:
                    sql += " AND city = %s"
                    params.append(filters['city'])
                if 'type' in filters:
                    sql += " AND type = %s"
                    params.append(filters['type'])
            
            sql += " ORDER BY distance LIMIT %s"
            params.append(limit)
            
            return self.execute_postgres_query(sql, tuple(params)) or []
        except Exception as e:
            logger.error(f"Error in vector search for hotels: {e}")
            return []

    def vector_search_cities(self, embedding: list, filters: Optional[dict] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Vector search on cities table.
        Schema: cities(embedding VECTOR, ...)
        Args: embedding (list[float]), filters (dict), limit (int)
        Returns: list of dicts
        """
        logger.info(f"Called vector_search_cities with embedding, filters={filters}, limit={limit}")
        try:
            # Check if pgvector extension is available
            check_sql = "SELECT 1 FROM pg_extension WHERE extname = 'vector'"
            result = self.execute_postgres_query(check_sql)
            if not result:
                logger.error("Vector search requires the 'vector' extension")
                return []
                
            # Build the query
            sql = """
                SELECT *, embedding <-> %s::vector AS distance
                FROM cities
                WHERE 1=1
            """
            params = [embedding]
            
            # Add filters if provided
            if filters:
                if 'region' in filters:
                    sql += " AND region = %s"
                    params.append(filters['region'])
            
            sql += " ORDER BY distance LIMIT %s"
            params.append(limit)
            
            return self.execute_postgres_query(sql, tuple(params)) or []
        except Exception as e:
            logger.error(f"Error in vector search for cities: {e}")
            return []

    def _build_where_clause(self, query: Dict[str, Any], placeholder: str = '?') -> Tuple[str, list]:
        """
        Build a SQL WHERE clause and parameters from a query dict.
        Supports operators: $like, $eq, $ne, $gt, $lt, $gte, $lte, $in, $nin, $or, $and, $exists.
        Returns (clause, params) where clause is a SQL string and params is a list.
        """
        if not query:
            return '', []
        def handle_subquery(q):
            subclauses = []
            subparams = []
            for key, value in q.items():
                if key == '$or' and isinstance(value, list):
                    or_clauses = []
                    or_params = []
                    for cond in value:
                        clause, p = handle_subquery(cond)
                        or_clauses.append(f"({clause})")
                        or_params.extend(p)
                    subclauses.append(f"({' OR '.join(or_clauses)})")
                    subparams.extend(or_params)
                elif key == '$and' and isinstance(value, list):
                    and_clauses = []
                    and_params = []
                    for cond in value:
                        clause, p = handle_subquery(cond)
                        and_clauses.append(f"({clause})")
                        and_params.extend(p)
                    subclauses.append(f"({' AND '.join(and_clauses)})")
                    subparams.extend(and_params)
                elif isinstance(value, dict):
                    for op, v in value.items():
                        if op == '$like':
                            subclauses.append(f"{key} LIKE {placeholder}")
                            subparams.append(v)
                        elif op == '$eq':
                            subclauses.append(f"{key} = {placeholder}")
                            subparams.append(v)
                        elif op == '$ne':
                            subclauses.append(f"{key} != {placeholder}")
                            subparams.append(v)
                        elif op == '$gt':
                            subclauses.append(f"{key} > {placeholder}")
                            subparams.append(v)
                        elif op == '$lt':
                            subclauses.append(f"{key} < {placeholder}")
                            subparams.append(v)
                        elif op == '$gte':
                            subclauses.append(f"{key} >= {placeholder}")
                            subparams.append(v)
                        elif op == '$lte':
                            subclauses.append(f"{key} <= {placeholder}")
                            subparams.append(v)
                        elif op == '$in' and isinstance(v, (list, tuple)):
                            placeholders = ', '.join([placeholder] * len(v))
                            subclauses.append(f"{key} IN ({placeholders})")
                            subparams.extend(v)
                        elif op == '$nin' and isinstance(v, (list, tuple)):
                            placeholders = ', '.join([placeholder] * len(v))
                            subclauses.append(f"{key} NOT IN ({placeholders})")
                            subparams.extend(v)
                        elif op == '$exists':
                            if v:
                                subclauses.append(f"{key} IS NOT NULL")
                            else:
                                subclauses.append(f"{key} IS NULL")
                        elif op == '$jsonb_contains' and placeholder == '%s':
                            subclauses.append(f"{key} @> %s::jsonb")
                            subparams.append(json.dumps(v))
                        elif op == '$fts' and placeholder == '%s':
                            # Add support for PostgreSQL full-text search
                            language = "english"  # Default language
                            if isinstance(v, dict) and "language" in v:
                                language = v["language"]
                                v = v["query"]
                            subclauses.append(f"to_tsvector('{language}', {key}) @@ plainto_tsquery('{language}', {placeholder})")
                            subparams.append(v)
                        else:
                            logger.warning(f"Unsupported operator in _build_where_clause: {op}")
                else:
                    subclauses.append(f"{key} = {placeholder}")
                    subparams.append(value)
            return ' AND '.join(subclauses), subparams
        clause, params = handle_subquery(query)
        logger.debug(f"Built WHERE clause: {clause} | Params: {params}")
        return clause, params

    def _build_postgres_where_clause(self, query: Dict[str, Any]) -> Tuple[str, list]:
        """
        Build a PostgreSQL WHERE clause and parameters from a query dict.
        Uses %s as the placeholder.
        """
        logger.debug("Building PostgreSQL WHERE clause with query: %s", query)
        return self._build_where_clause(query, placeholder='%s')

    def _build_pagination_query(self, table: str, query: Optional[Dict[str, Any]] = None, limit: int = 10, offset: int = 0) -> Tuple[str, list]:
        """
        Build a paginated query for the given table.
        Returns (sql, params).
        """
        # Validate pagination
        if not (isinstance(limit, int) and isinstance(offset, int) and limit >= 0 and offset >= 0):
            raise ValueError("Invalid limit or offset")
        where_clause, params = self._build_where_clause(query or {}, placeholder='%s')
        sql = f"SELECT * FROM {table} WHERE 1=1"
        if where_clause:
            sql += f" AND {where_clause}"
        sql += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        return sql, params

    def _table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the current PostgreSQL database.
        """
        try:
            if self.db_type == DatabaseType.POSTGRES and self.pg_pool:
                conn = self._get_pg_connection()
                try:
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name=%s)", (table_name,))
                        exists = cursor.fetchone()[0]
                    return exists
                finally:
                    self._return_pg_connection(conn)
            else:
                logger.error("_table_exists called, but not using PostgreSQL or pool not initialized.")
                return False
        except Exception as e:
            logger.error(f"Error checking if table exists: {e}")
            return False

    def get_all_restaurants_no_user(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get restaurants without requiring user_id column for testing."""
        query = "SELECT * FROM restaurants LIMIT %s"
        params = (limit,)
        return self.execute_query(query, params)

    def search_attractions(self, query: Optional[Dict[str, Any]] = None, filters: Optional[Dict[str, Any]] = None, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """Search attractions based on query or filters."""
        # Combine query and filters if both are provided
        search_filters = {}
        if query:
            search_filters.update(query)
        if filters:
            search_filters.update(filters)

        base_query = "SELECT * FROM attractions WHERE 1=1"
        params = []

        if search_filters:
            if "city" in search_filters:
                base_query += " AND city LIKE %s"
                params.append(f"%{search_filters['city']}%")

            if "type" in search_filters:
                base_query += " AND type LIKE %s"
                params.append(f"%{search_filters['type']}%")

            if "name" in search_filters:
                base_query += " AND (name_en LIKE %s OR name_ar LIKE %s)"
                name_pattern = f"%{search_filters['name']}%"
                params.extend([name_pattern, name_pattern])
                
            if "name_en" in search_filters:
                if isinstance(search_filters["name_en"], dict) and "$like" in search_filters["name_en"]:
                    base_query += " AND name_en LIKE %s"
                    params.append(search_filters["name_en"]["$like"])
                else:
                    base_query += " AND name_en = %s"
                    params.append(search_filters["name_en"])

        base_query += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        return self.execute_query(base_query, tuple(params))

    def search_accommodations(self, query: Optional[Dict[str, Any]] = None, filters: Optional[Dict[str, Any]] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Search accommodations based on query or filters."""
        # Combine query and filters if both are provided
        search_filters = {}
        if query:
            search_filters.update(query)
        if filters:
            search_filters.update(filters)

        base_query = "SELECT * FROM accommodations WHERE 1=1"
        params = []

        if "city" in search_filters:
            base_query += " AND city LIKE %s"
            params.append(f"%{search_filters['city']}%")

        if "type" in search_filters:
            base_query += " AND type LIKE %s"
            params.append(f"%{search_filters['type']}%")

        if "name" in search_filters:
            base_query += " AND (name_en LIKE %s OR name_ar LIKE %s)"
            name_pattern = f"%{search_filters['name']}%"
            params.extend([name_pattern, name_pattern])

        base_query += " LIMIT %s"
        params.append(limit)

        return self.execute_query(base_query, tuple(params))

    def search_hotels(self, query: Optional[Dict[str, Any]] = None, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Search hotels table (alias for search_accommodations).
        
        Args: 
            query: Dictionary of search criteria
            limit: Maximum number of results to return
            offset: Offset for pagination
            
        Returns: list of dicts
        """
        logger.info(f"Called search_hotels with query={query}, limit={limit}, offset={offset}")
        return self.search_accommodations(query=query, filters=None, limit=limit)

    def test_connection(self) -> bool:
        """Test database connection and verify it's working properly."""
        try:
            # First check if the pool was initialized successfully
            if not self.pg_pool:
                logger.warning("Connection test failed: connection pool is not initialized")
                return False

            # Try to get a connection from the pool
            conn = None
            try:
                conn = self.pg_pool.getconn()
                if not conn or conn.closed:
                    logger.warning("Connection test failed: got invalid or closed connection from pool")
                    return False
                    
                # Execute a simple query to verify the connection works
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1 as test")
                    result = cursor.fetchone()
                    return result[0] == 1
            except Exception as e:
                logger.warning(f"Connection test query failed: {str(e)}")
                return False
            finally:
                if conn and not conn.closed:
                    self.pg_pool.putconn(conn)
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False

    def _postgres_column_exists(self, table_name: str, column_name: str) -> bool:
        """Check if a column exists in a PostgreSQL table."""
        try:
            sql = """
                SELECT EXISTS (
                    SELECT 1 
                    FROM information_schema.columns 
                    WHERE table_name = %s AND column_name = %s
                ) AS exists
            """
            result = self.execute_postgres_query(sql, (table_name, column_name))
            if result and len(result) > 0:
                return result[0].get('exists', False)
            return False
        except Exception as e:
            logger.error(f"Error checking if column exists: {str(e)}")
            return False

    def _check_postgis_enabled(self) -> bool:
        """Check if PostGIS extension is enabled in the database."""
        try:
            sql = "SELECT COUNT(*) as count FROM pg_extension WHERE extname = 'postgis'"
            result = self.execute_postgres_query(sql)
            if result and len(result) > 0:
                return result[0].get('count', 0) > 0
            return False
        except Exception as e:
            logger.error(f"Error checking if PostGIS is enabled: {str(e)}")
            return False

    def _check_vector_enabled(self) -> bool:
        """Check if pgvector extension is enabled in the database."""
        try:
            sql = "SELECT COUNT(*) as count FROM pg_extension WHERE extname = 'vector'"
            result = self.execute_postgres_query(sql)
            if result and len(result) > 0:
                return result[0].get('count', 0) > 0
            return False
        except Exception as e:
            logger.error(f"Error checking if pgvector is enabled: {str(e)}")
            return False

    def update_geospatial_columns(self, tables: List[str] = None) -> bool:
        """
        Update geospatial columns for the specified tables.
        
        Args:
            tables: List of table names to update. If None, all tables with lat/long will be updated.
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self._check_postgis_enabled():
            logger.warning("PostGIS is not enabled, cannot update geospatial columns")
            return False
            
        if tables is None:
            tables = ['attractions', 'restaurants', 'accommodations']
            
        try:
            for table in tables:
                if not self._table_exists(table):
                    logger.warning(f"Table '{table}' does not exist, skipping geospatial update")
                    continue
                    
                # Check if geometry column exists
                if not self._postgres_column_exists(table, 'geom'):
                    # Add geometry column if it doesn't exist
                    sql = f"""
                        ALTER TABLE {table} 
                        ADD COLUMN geom geometry(Point, 4326);
                        
                        CREATE INDEX IF NOT EXISTS idx_{table}_geom 
                        ON {table} USING GIST (geom);
                    """
                    self.execute_postgres_query(sql)
                    logger.info(f"Added geometry column to {table}")
                
                # Update geometry column from latitude/longitude
                sql = f"""
                    UPDATE {table}
                    SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
                    WHERE latitude IS NOT NULL AND longitude IS NOT NULL AND geom IS NULL;
                """
                affected = self.execute_postgres_query(sql)
                logger.info(f"Updated {affected} geospatial points in {table}")
                
            return True
            
        except Exception as e:
            logger.error(f"Error updating geospatial columns: {str(e)}")
            return False

    def find_nearby(self, table: str, latitude: float, longitude: float, radius_km: float, 
                    limit: int = 10, additional_filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Find items near a geographical point using PostGIS.
        
        Args:
            table: Table name to search
            latitude: Latitude of the center point
            longitude: Longitude of the center point
            radius_km: Search radius in kilometers
            limit: Maximum number of results
            additional_filters: Additional filters to apply
            
        Returns:
            List of items with distance_km added
        """
        try:
            # Check if table exists
            if not self._table_exists(table):
                logger.warning(f"Table '{table}' does not exist")
                return []
                
            # Check if PostGIS is enabled
            if not self._check_postgis_enabled():
                logger.warning("PostGIS is not enabled, using fallback distance calculation")
                return []
                
            # Check if geometry column exists
            has_geom = self._postgres_column_exists(table, 'geom')
                
            # Build base query
            if has_geom:
                # Use PostGIS for efficient spatial query
                sql = f"""
                    SELECT *, 
                           ST_Distance(
                               geom, 
                               ST_SetSRID(ST_MakePoint(%s, %s), 4326), 
                               true
                           ) / 1000 AS distance_km
                    FROM {table}
                    WHERE ST_DWithin(
                        geom, 
                        ST_SetSRID(ST_MakePoint(%s, %s), 4326), 
                        %s * 1000
                    )
                """
                params = [longitude, latitude, longitude, latitude, radius_km]
            else:
                # Fallback to approximate distance calculation
                sql = f"""
                    SELECT *, 
                           (6371 * acos(cos(radians(%s)) * cos(radians(latitude)) * 
                           cos(radians(longitude) - radians(%s)) + 
                           sin(radians(%s)) * sin(radians(latitude)))) AS distance_km
                    FROM {table}
                    WHERE latitude IS NOT NULL AND longitude IS NOT NULL
                """
                params = [latitude, longitude, latitude]
                
            # Add additional filters
            if additional_filters:
                for key, value in additional_filters.items():
                    sql += f" AND {key} = %s"
                    params.append(value)
            
            # Add distance filter for non-PostGIS query
            if not has_geom:
                sql += f" AND (6371 * acos(cos(radians(%s)) * cos(radians(latitude)) * "
                sql += f"cos(radians(longitude) - radians(%s)) + "
                sql += f"sin(radians(%s)) * sin(radians(latitude)))) < %s"
                params.extend([latitude, longitude, latitude, radius_km])
            
            # Add ordering and limit
            sql += " ORDER BY distance_km LIMIT %s"
            params.append(limit)
            
            # Execute query
            results = self.execute_postgres_query(sql, tuple(params))
            return results or []
            
        except Exception as e:
            logger.error(f"Error finding nearby items: {str(e)}")
            return []

    def update_vector_columns(self, tables: List[str] = None) -> bool:
        """
        Update vector columns for the specified tables to ensure pgvector is properly set up.
        
        Args:
            tables: List of table names to update. If None, all tables with embedding columns will be updated.
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self._check_vector_enabled():
            logger.warning("pgvector extension is not enabled, cannot update vector columns")
            return False
            
        if tables is None:
            tables = ['attractions', 'restaurants', 'accommodations', 'cities', 'regions']
            
        try:
            for table in tables:
                if not self._table_exists(table):
                    logger.warning(f"Table '{table}' does not exist, skipping vector update")
                    continue
                    
                # Check if embedding column exists
                if not self._postgres_column_exists(table, 'embedding'):
                    # Add embedding column if it doesn't exist
                    sql = f"""
                        ALTER TABLE {table} 
                        ADD COLUMN embedding vector(1536);
                        
                        CREATE INDEX IF NOT EXISTS idx_{table}_embedding 
                        ON {table} USING hnsw (embedding vector_l2_ops);
                    """
                    self.execute_postgres_query(sql)
                    logger.info(f"Added vector embedding column to {table}")
                
            return True
            
        except Exception as e:
            logger.error(f"Error updating vector columns: {str(e)}")
            return False

    def store_embedding(self, table: str, record_id: str, embedding: List[float]) -> bool:
        """
        Store a vector embedding for a specific record.
        
        Args:
            table: The table name
            record_id: The ID of the record
            embedding: The vector embedding to store
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self._check_vector_enabled():
            logger.warning("pgvector extension is not enabled, cannot store embeddings")
            return False
            
        try:
            # Verify the table exists
            if not self._table_exists(table):
                logger.warning(f"Table '{table}' does not exist")
                return False
                
            # Verify the embedding column exists
            if not self._postgres_column_exists(table, 'embedding'):
                logger.warning(f"Table '{table}' does not have an embedding column")
                return False
            
            # Convert numpy array to list if necessary
            import numpy as np
            if isinstance(embedding, np.ndarray):
                embedding = embedding.tolist()
                
            # First check if the record exists
            check_sql = f"SELECT 1 FROM {table} WHERE id = %s"
            result = self.execute_postgres_query(check_sql, (record_id,))
            
            if not result:
                # Insert a new record with the embedding
                sql = f"""
                    INSERT INTO {table} (id, embedding)
                    VALUES (%s, %s::vector)
                """
                result = self.execute_postgres_query(sql, (record_id, embedding))
            else:
                # Update the existing record
                sql = f"""
                    UPDATE {table}
                    SET embedding = %s::vector
                    WHERE id = %s
                """
                result = self.execute_postgres_query(sql, (embedding, record_id))
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing embedding: {str(e)}")
            return False

    def batch_store_embeddings(self, table: str, embeddings: Dict[str, List[float]]) -> bool:
        """
        Store multiple vector embeddings in batch using efficient bulk operations.
        
        Args:
            table: The table name
            embeddings: Dict mapping record IDs to embeddings
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self._check_vector_enabled():
            logger.warning("pgvector extension is not enabled, cannot store embeddings")
            return False
            
        if not embeddings:
            return True  # Nothing to do
            
        # Validate table name
        if table not in self.VALID_TABLES:
            logger.error(f"Invalid table name: {table}")
            return False
            
        try:
            # Verify the table exists
            if not self._table_exists(table):
                logger.warning(f"Table '{table}' does not exist")
                return False
                
            # Verify the embedding column exists
            if not self._postgres_column_exists(table, 'embedding'):
                logger.warning(f"Table '{table}' does not have an embedding column")
                return False
                
            # Get a connection for this transaction
            conn = self._get_pg_connection()
            if not conn:
                logger.error("Failed to get database connection")
                return False
                
            try:
                start_time = time.time()
                with conn:  # Use transaction for atomicity
                    with conn.cursor() as cursor:
                        # Use execute_values for efficient bulk update
                        from psycopg2.extras import execute_values
                        
                        # Prepare data for batch update
                        update_data = [(embedding, record_id) for record_id, embedding in embeddings.items()]
                        
                        # Use execute_values for efficient batch operation
                        execute_values(
                            cursor,
                            f"UPDATE {table} SET embedding = %s::vector WHERE id = %s",
                            update_data,
                            template=None,  # Use default template
                            page_size=100   # Process in batches of 100
                        )
                
                duration = time.time() - start_time
                logger.info(f"Batch updated {len(embeddings)} embeddings in {duration:.2f} seconds")
                return True
                
            finally:
                self._return_pg_connection(conn)
                
        except Exception as e:
            logger.error(f"Error batch storing embeddings: {str(e)}")
            return False

    def get_embedding(self, table: str, record_id: str) -> Optional[List[float]]:
        """
        Retrieve the vector embedding for a specific record.
        
        Args:
            table: The table name
            record_id: The ID of the record
            
        Returns:
            Optional[List[float]]: The embedding or None if not found
        """
        if not self._check_vector_enabled():
            logger.warning("pgvector extension is not enabled, cannot retrieve embedding")
            return None
            
        try:
            # Verify the table exists
            if not self._table_exists(table):
                logger.warning(f"Table '{table}' does not exist")
                return None
                
            # Verify the embedding column exists
            if not self._postgres_column_exists(table, 'embedding'):
                logger.warning(f"Table '{table}' does not have an embedding column")
                return None
                
            # Get the embedding
            sql = f"""
                SELECT embedding
                FROM {table}
                WHERE id = %s
            """
            result = self.execute_postgres_query(sql, (record_id,), fetchall=False)
            
            if result and 'embedding' in result and result['embedding'] is not None:
                return result['embedding']
                
            return None
            
        except Exception as e:
            logger.error(f"Error getting embedding: {str(e)}")
            return None

    def find_similar(self, table: str, embedding: List[float], limit: int = 10, additional_filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Find records with similar embeddings.
        
        Args:
            table: The table name
            embedding: The query embedding
            limit: Maximum number of results
            additional_filters: Additional filters to apply
            
        Returns:
            List[Dict[str, Any]]: List of similar records with similarity scores
        """
        if not self._check_vector_enabled():
            logger.warning("pgvector extension is not enabled, cannot find similar vectors")
            return []
            
        try:
            # Verify the table exists
            if not self._table_exists(table):
                logger.warning(f"Table '{table}' does not exist")
                return []
                
            # Verify the embedding column exists
            if not self._postgres_column_exists(table, 'embedding'):
                logger.warning(f"Table '{table}' does not have an embedding column")
                return []
                
            # Build the query
            sql = f"""
                SELECT *, 1 - (embedding <=> %s::vector) AS similarity
                FROM {table}
                WHERE embedding IS NOT NULL
            """
            params = [embedding]
            
            # Add additional filters
            if additional_filters:
                for key, value in additional_filters.items():
                    sql += f" AND {key} = %s"
                    params.append(value)
            
            # Add ordering and limit
            sql += " ORDER BY similarity DESC LIMIT %s"
            params.append(limit)
            
            # Execute query
            results = self.execute_postgres_query(sql, tuple(params))
            return results or []
            
        except Exception as e:
            logger.error(f"Error finding similar records: {str(e)}")
            return []

    def insert_attraction(self, attraction: Dict[str, Any]) -> bool:
        """
        Insert a new attraction record with transaction support.
        
        Args:
            attraction: Dictionary with attraction data
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Get a connection for this transaction
        conn = self._get_pg_connection()
        if not conn:
            logger.error("Failed to get database connection")
            return False

        try:
            # Start a transaction
            with conn:  # This automatically manages the transaction
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Ensure required fields are present
                    required_fields = ['id', 'name_en']
                    for field in required_fields:
                        if field not in attraction:
                            raise ValueError(f"Missing required field: {field}")

                    # Handle JSON data field if present
                    data_json = None
                    if 'data' in attraction:
                        if isinstance(attraction['data'], str):
                            data_json = attraction['data']  # Already a JSON string
                        else:
                            data_json = json.dumps(attraction['data'])
                            
                    # Prepare fields and values
                    fields = []
                    values = []
                    placeholders = []
                    
                    for key, value in attraction.items():
                        if key == 'data':
                            continue  # Skip, we handle it separately
                        if key == 'location' and isinstance(value, dict) and 'lat' in value and 'lng' in value:
                            # Extract coordinates from location object
                            fields.extend(['latitude', 'longitude'])
                            values.extend([value['lat'], value['lng']])
                            placeholders.extend(['%s', '%s'])
                        else:
                            fields.append(key)
                            values.append(value)
                            placeholders.append('%s')
                            
                    # Add data field if present
                    if data_json is not None:
                        fields.append('data')
                        values.append(data_json)
                        placeholders.append('%s')
                        
                    # Build and execute insert query
                    sql = f"""
                        INSERT INTO attractions ({', '.join(fields)})
                        VALUES ({', '.join(placeholders)})
                        ON CONFLICT (id) DO NOTHING
                        RETURNING id
                    """
                    
                    cursor.execute(sql, tuple(values))
                    result = cursor.fetchone()
                    
                    # Update geospatial point if PostGIS is enabled
                    if result and self._check_postgis_enabled() and 'latitude' in fields and 'longitude' in fields:
                        lat_idx = fields.index('latitude')
                        lng_idx = fields.index('longitude')
                        update_sql = """
                            UPDATE attractions
                            SET geom = ST_SetSRID(ST_MakePoint(%s, %s), 4326)
                            WHERE id = %s
                        """
                        cursor.execute(update_sql, (values[lng_idx], values[lat_idx], attraction['id']))
                    
                    return result is not None

        except Exception as e:
            logger.error(f"Error inserting attraction: {str(e)}")
            return False
        finally:
            # Return the connection to the pool
            self._return_pg_connection(conn)

    def update_attraction(self, attraction_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing attraction.
        
        Args:
            attraction_id: ID of the attraction to update
            updates: Dictionary of fields to update
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Handle empty updates
            if not updates:
                return True
                
            # Handle JSON data field
            if 'data' in updates and not isinstance(updates['data'], str):
                updates['data'] = json.dumps(updates['data'])
                
            # Extract location if present
            if 'location' in updates and isinstance(updates['location'], dict):
                if 'lat' in updates['location']:
                    updates['latitude'] = updates['location']['lat']
                if 'lng' in updates['location']:
                    updates['longitude'] = updates['location']['lng']
                del updates['location']
                
            # Build SET clause
            set_clauses = []
            values = []
            
            for key, value in updates.items():
                set_clauses.append(f"{key} = %s")
                values.append(value)
                
            # Add updated_at timestamp
            set_clauses.append("updated_at = CURRENT_TIMESTAMP")
            
            # Build and execute update query
            sql = f"""
                UPDATE attractions
                SET {', '.join(set_clauses)}
                WHERE id = %s
                RETURNING id
            """
            values.append(attraction_id)
            
            result = self.execute_postgres_query(sql, tuple(values))
            
            # Update geospatial point if coordinates were updated
            if result and 'latitude' in updates and 'longitude' in updates and self._check_postgis_enabled():
                self._update_geospatial_point('attractions', attraction_id, updates['latitude'], updates['longitude'])
                
            return result is not None
            
        except Exception as e:
            logger.error(f"Error updating attraction {attraction_id}: {str(e)}")
            return False

    def delete_attraction(self, attraction_id: str) -> bool:
        """
        Delete an attraction by ID.
        
        Args:
            attraction_id: ID of the attraction to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            sql = "DELETE FROM attractions WHERE id = %s RETURNING id"
            result = self.execute_postgres_query(sql, (attraction_id,), fetchall=False)
            return result is not None
        except Exception as e:
            logger.error(f"Error deleting attraction {attraction_id}: {str(e)}")
            return False

    def insert_restaurant(self, restaurant: Dict[str, Any]) -> bool:
        """
        Insert a new restaurant record.
        
        Args:
            restaurant: Dictionary with restaurant data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Ensure required fields are present
            required_fields = ['id', 'name_en']
            for field in required_fields:
                if field not in restaurant:
                    logger.error(f"Missing required field: {field}")
                    return False

            # Handle JSON data field if present
            data_json = None
            if 'data' in restaurant:
                if isinstance(restaurant['data'], str):
                    data_json = restaurant['data']
                else:
                    data_json = json.dumps(restaurant['data'])
                    
            # Prepare fields and values
            fields = []
            values = []
            placeholders = []
            
            for key, value in restaurant.items():
                if key == 'data':
                    continue  # Skip, we handle it separately
                if key == 'location' and isinstance(value, dict) and 'lat' in value and 'lng' in value:
                    # Extract coordinates from location object
                    fields.extend(['latitude', 'longitude'])
                    values.extend([value['lat'], value['lng']])
                    placeholders.extend(['%s', '%s'])
                else:
                    fields.append(key)
                    values.append(value)
                    placeholders.append('%s')
                    
            # Add data field if present
            if data_json is not None:
                fields.append('data')
                values.append(data_json)
                placeholders.append('%s')
                
            # Build and execute insert query
            sql = f"""
                INSERT INTO restaurants ({', '.join(fields)})
                VALUES ({', '.join(placeholders)})
                ON CONFLICT (id) DO NOTHING
                RETURNING id
            """
            
            result = self.execute_postgres_query(sql, tuple(values), fetchall=False)
            
            # Update geospatial point if PostGIS is enabled
            if result and self._check_postgis_enabled() and 'latitude' in fields and 'longitude' in fields:
                lat_idx = fields.index('latitude')
                lng_idx = fields.index('longitude')
                update_sql = """
                    UPDATE restaurants
                    SET geom = ST_SetSRID(ST_MakePoint(%s, %s), 4326)
                    WHERE id = %s
                """
                result = self.execute_postgres_query(update_sql, (values[lng_idx], values[lat_idx], restaurant['id']))
                
            return result is not None
            
        except Exception as e:
            logger.error(f"Error inserting restaurant: {str(e)}")
            return False

    def update_restaurant(self, restaurant_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing restaurant.
        
        Args:
            restaurant_id: ID of the restaurant to update
            updates: Dictionary of fields to update
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Handle empty updates
            if not updates:
                return True
                
            # Handle JSON data field
            if 'data' in updates and not isinstance(updates['data'], str):
                updates['data'] = json.dumps(updates['data'])
                
            # Extract location if present
            if 'location' in updates and isinstance(updates['location'], dict):
                if 'lat' in updates['location']:
                    updates['latitude'] = updates['location']['lat']
                if 'lng' in updates['location']:
                    updates['longitude'] = updates['location']['lng']
                del updates['location']
                
            # Build SET clause
            set_clauses = []
            values = []
            
            for key, value in updates.items():
                set_clauses.append(f"{key} = %s")
                values.append(value)
                
            # Add updated_at timestamp
            set_clauses.append("updated_at = CURRENT_TIMESTAMP")
            
            # Build and execute update query
            sql = f"""
                UPDATE restaurants
                SET {', '.join(set_clauses)}
                WHERE id = %s
                RETURNING id
            """
            values.append(restaurant_id)
            
            result = self.execute_postgres_query(sql, tuple(values), fetchall=False)
            
            # Update geospatial point if coordinates were updated
            if result and 'latitude' in updates and 'longitude' in updates and self._check_postgis_enabled():
                self._update_geospatial_point('restaurants', restaurant_id, updates['latitude'], updates['longitude'])
                
            return result is not None
            
        except Exception as e:
            logger.error(f"Error updating restaurant {restaurant_id}: {str(e)}")
            return False

    def delete_restaurant(self, restaurant_id: str) -> bool:
        """
        Delete a restaurant by ID.
        
        Args:
            restaurant_id: ID of the restaurant to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            sql = "DELETE FROM restaurants WHERE id = %s RETURNING id"
            result = self.execute_postgres_query(sql, (restaurant_id,), fetchall=False)
            return result is not None
        except Exception as e:
            logger.error(f"Error deleting restaurant {restaurant_id}: {str(e)}")
            return False

    def insert_accommodation(self, accommodation: Dict[str, Any]) -> bool:
        """
        Insert a new accommodation record.
        
        Args:
            accommodation: Dictionary with accommodation data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Ensure required fields are present
            required_fields = ['id', 'name_en']
            for field in required_fields:
                if field not in accommodation:
                    logger.error(f"Missing required field: {field}")
                    return False

            # Handle JSON data field if present
            data_json = None
            if 'data' in accommodation:
                if isinstance(accommodation['data'], str):
                    data_json = accommodation['data']
                else:
                    data_json = json.dumps(accommodation['data'])
                    
            # Prepare fields and values
            fields = []
            values = []
            placeholders = []
            
            for key, value in accommodation.items():
                if key == 'data':
                    continue  # Skip, we handle it separately
                if key == 'location' and isinstance(value, dict) and 'lat' in value and 'lng' in value:
                    # Extract coordinates from location object
                    fields.extend(['latitude', 'longitude'])
                    values.extend([value['lat'], value['lng']])
                    placeholders.extend(['%s', '%s'])
                else:
                    fields.append(key)
                    values.append(value)
                    placeholders.append('%s')
                    
            # Add data field if present
            if data_json is not None:
                fields.append('data')
                values.append(data_json)
                placeholders.append('%s')
                
            # Build and execute insert query
            sql = f"""
                INSERT INTO accommodations ({', '.join(fields)})
                VALUES ({', '.join(placeholders)})
                ON CONFLICT (id) DO NOTHING
                RETURNING id
            """
            
            result = self.execute_postgres_query(sql, tuple(values), fetchall=False)
            
            # Update geospatial point if PostGIS is enabled
            if result and self._check_postgis_enabled() and 'latitude' in fields and 'longitude' in fields:
                lat_idx = fields.index('latitude')
                lng_idx = fields.index('longitude')
                self._update_geospatial_point('accommodations', accommodation['id'], values[lat_idx], values[lng_idx])
                
            return result is not None
            
        except Exception as e:
            logger.error(f"Error inserting accommodation: {str(e)}")
            return False

    # Alias method for compatibility with tests
    def insert_hotel(self, hotel: Dict[str, Any]) -> bool:
        """Alias for insert_accommodation to maintain compatibility with tests."""
        return self.insert_accommodation(hotel)

    def update_accommodation(self, accommodation_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing accommodation.
        
        Args:
            accommodation_id: ID of the accommodation to update
            updates: Dictionary of fields to update
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Handle empty updates
            if not updates:
                return True
                
            # Handle JSON data field
            if 'data' in updates and not isinstance(updates['data'], str):
                updates['data'] = json.dumps(updates['data'])
                
            # Extract location if present
            if 'location' in updates and isinstance(updates['location'], dict):
                if 'lat' in updates['location']:
                    updates['latitude'] = updates['location']['lat']
                if 'lng' in updates['location']:
                    updates['longitude'] = updates['location']['lng']
                del updates['location']
                
            # Build SET clause
            set_clauses = []
            values = []
            
            for key, value in updates.items():
                set_clauses.append(f"{key} = %s")
                values.append(value)
                
            # Add updated_at timestamp
            set_clauses.append("updated_at = CURRENT_TIMESTAMP")
            
            # Build and execute update query
            sql = f"""
                UPDATE accommodations
                SET {', '.join(set_clauses)}
                WHERE id = %s
                RETURNING id
            """
            values.append(accommodation_id)
            
            result = self.execute_postgres_query(sql, tuple(values), fetchall=False)
            
            # Update geospatial point if coordinates were updated
            if result and 'latitude' in updates and 'longitude' in updates and self._check_postgis_enabled():
                self._update_geospatial_point('accommodations', accommodation_id, updates['latitude'], updates['longitude'])
                
            return result is not None
            
        except Exception as e:
            logger.error(f"Error updating accommodation {accommodation_id}: {str(e)}")
            return False

    # Alias method for compatibility with tests
    def update_hotel(self, hotel_id: str, updates: Dict[str, Any]) -> bool:
        """Alias for update_accommodation to maintain compatibility with tests."""
        return self.update_accommodation(hotel_id, updates)

    def delete_accommodation(self, accommodation_id: str) -> bool:
        """
        Delete an accommodation by ID.
        
        Args:
            accommodation_id: ID of the accommodation to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            sql = "DELETE FROM accommodations WHERE id = %s RETURNING id"
            result = self.execute_postgres_query(sql, (accommodation_id,), fetchall=False)
            return result is not None
        except Exception as e:
            logger.error(f"Error deleting accommodation {accommodation_id}: {str(e)}")
            return False

    # Alias method for compatibility with tests
    def delete_hotel(self, hotel_id: str) -> bool:
        """Alias for delete_accommodation to maintain compatibility with tests."""
        return self.delete_accommodation(hotel_id)

    def get_all_attractions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all attractions with optional limit.
        
        Args:
            limit: Maximum number of attractions to retrieve
            
        Returns:
            List of attraction records
        """
        try:
            sql = "SELECT * FROM attractions LIMIT %s"
            return self.execute_postgres_query(sql, (limit,)) or []
        except Exception as e:
            logger.error(f"Error getting all attractions: {str(e)}")
            return []

    def get_all_restaurants(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all restaurants with optional limit.
        
        Args:
            limit: Maximum number of restaurants to retrieve
            
        Returns:
            List of restaurant records
        """
        try:
            sql = "SELECT * FROM restaurants LIMIT %s"
            return self.execute_postgres_query(sql, (limit,)) or []
        except Exception as e:
            logger.error(f"Error getting all restaurants: {str(e)}")
            return []

    def get_all_accommodations(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all accommodations with optional limit.
        
        Args:
            limit: Maximum number of accommodations to retrieve
            
        Returns:
            List of accommodation records
        """
        try:
            sql = "SELECT * FROM accommodations LIMIT %s"
            return self.execute_postgres_query(sql, (limit,)) or []
        except Exception as e:
            logger.error(f"Error getting all accommodations: {str(e)}")
            return []

    # Alias method for compatibility with tests
    def get_all_hotels(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Alias for get_all_accommodations to maintain compatibility with tests."""
        return self.get_all_accommodations(limit)

    def hybrid_search(self, table_name: str, query_text: str, embedding: list, 
                    filters: Optional[Dict[str, Any]] = None, 
                    limit: int = 10, 
                    vector_weight: float = 0.7,
                    language: str = 'english') -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining vector similarity and keyword matching.
        
        Args:
            table_name: Name of the table to search (attractions, restaurants, accommodations, etc.)
            query_text: Text query for keyword search
            embedding: Vector embedding for semantic search
            filters: Additional filters to apply
            limit: Maximum number of results to return
            vector_weight: Weight to give vector search vs keyword search (0.0-1.0)
            language: Language for text search ('english' or 'arabic')
            
        Returns:
            List of matching records with combined relevance score
        """
        logger.info(f"Called hybrid_search on {table_name} with query={query_text}, filters={filters}")
        
        # Validate table name against whitelist
        if table_name not in self.VALID_TABLES:
            logger.error(f"Invalid table name: {table_name}")
            return []
            
        # Validate parameters
        if not 0.0 <= vector_weight <= 1.0:
            logger.warning(f"Invalid vector_weight {vector_weight}, must be between 0.0 and 1.0. Using 0.7")
            vector_weight = 0.7
            
        # Validate language
        if language not in ('english', 'arabic'):
            logger.warning(f"Unsupported language '{language}', falling back to english")
            language = 'english'
            
        try:
            # Check if vector extension is available
            if not self._check_vector_enabled():
                logger.warning("Vector extension not available, falling back to keyword search only")
                return self.enhanced_search(table_name, query_text, limit)
                
            # Ensure table exists
            if not self._table_exists(table_name):
                logger.error(f"Table {table_name} does not exist")
                return []
                
            # Ensure embedding column exists
            if not self._postgres_column_exists(table_name, 'embedding'):
                logger.warning(f"Table {table_name} does not have embedding column, falling back to keyword search")
                return self.enhanced_search(table_name, query_text, limit)
            
            # Build filter conditions
            filter_sql = ""
            filter_params = []
            if filters:
                for key, value in filters.items():
                    filter_sql += f" AND {key} = %s"
                    filter_params.append(value)
            
            # Determine name and description fields based on language
            name_field = f"name_{language[:2]}"  # name_en or name_ar
            desc_field = f"description_{language[:2]}"  # description_en or description_ar
            
            # Fallback fields - if primary language fields aren't available, use the other language
            fallback_name = "name_ar" if language == 'english' else "name_en"
            fallback_desc = "description_ar" if language == 'english' else "description_en"
            
            # Compute hybrid search SQL - combines vector distance with text similarity
            # Includes both languages in the text search for better coverage
            sql = f"""
                WITH vector_results AS (
                    SELECT 
                        *, 
                        embedding <-> %s::vector AS vector_distance
                    FROM {table_name}
                    WHERE embedding IS NOT NULL {filter_sql}
                ),
                text_results AS (
                    SELECT 
                        *, 
                        ts_rank(
                            to_tsvector('{language}', 
                                COALESCE({name_field}, '') || ' ' || 
                                COALESCE({desc_field}, '') || ' ' || 
                                COALESCE({fallback_name}, '') || ' ' || 
                                COALESCE({fallback_desc}, '')
                            ), 
                            plainto_tsquery('{language}', %s)
                        ) AS text_rank
                    FROM {table_name}
                    WHERE 1=1 {filter_sql}
                    AND (
                        to_tsvector('{language}', 
                            COALESCE({name_field}, '') || ' ' || 
                            COALESCE({desc_field}, '') || ' ' || 
                            COALESCE({fallback_name}, '') || ' ' || 
                            COALESCE({fallback_desc}, '')
                        ) @@ plainto_tsquery('{language}', %s)
                    )
                )
                SELECT 
                    vr.*, 
                    vr.vector_distance,
                    COALESCE(tr.text_rank, 0) AS text_rank,
                    ({vector_weight} * (1 - LEAST(vr.vector_distance / 2, 1)) + 
                     {1 - vector_weight} * COALESCE(tr.text_rank, 0)) AS hybrid_score
                FROM 
                    vector_results vr
                LEFT JOIN 
                    text_results tr ON vr.id = tr.id
                ORDER BY 
                    hybrid_score DESC
                LIMIT %s
            """
            
            # Add parameters for the query
            params = [embedding, query_text, query_text] + filter_params + filter_params + [limit]
            
            # Track performance start time
            start_time = time.time()
            
            # Execute the search
            results = self.execute_postgres_query(sql, tuple(params)) or []
            
            # Log performance metrics
            query_time = time.time() - start_time
            self._track_vector_search_performance(
                table_name, 
                query_time, 
                len(results), 
                self.vector_dimension, 
                "hybrid", 
                {"language": language, "query_text": query_text, "filters": filters or {}}
            )
            
            logger.info(f"Hybrid search returned {len(results)} results in {query_time:.3f}s")
            return results
            
        except Exception as e:
            logger.error(f"Error in hybrid search: {str(e)}")
            # Fallback to vector search only in case of# Error in hybrid search: {str(e)}
            # Fallback to vector search only in case of errors with hybrid approach
            logger.info("Falling back to vector search only")
            return self.vector_search(table_name, embedding, filters, limit)

    def rerank_hybrid_results(self, results: List[Dict[str, Any]], vector_weight: float = 0.7) -> List[Dict[str, Any]]:
        """
        Rerank hybrid search results based on vector similarity and keyword relevance.

        Args:
            results (List[Dict[str, Any]]): List of results with vector_distance and text_rank.
            vector_weight (float): Weight for vector similarity (0.0 to 1.0).

        Returns:
            List[Dict[str, Any]]: Reranked results.
        """
        try:
            for result in results:
                vector_score = 1 - min(result.get("vector_distance", 1.0), 1.0)
                text_score = result.get("text_rank", 0.0)
                result["hybrid_score"] = (vector_weight * vector_score) + ((1 - vector_weight) * text_score)

            # Sort results by hybrid_score in descending order
            results.sort(key=lambda x: x["hybrid_score"], reverse=True)
            return results

        except Exception as e:
            logger.error(f"Error reranking hybrid results: {e}")
            return results

    def _track_vector_search_performance(self, table_name: str, query_time: float, 
                                 result_count: int, dimension: int = None, 
                                 query_type: str = "vector", additional_info: Optional[Dict[str, Any]] =None):
        """
        Track vector search performance metrics for monitoring and optimization.

        Args:
            table_name: The table that was searched
            query_time: Time in seconds the query took
            result_count: Number of results returned
            vector_dimension: Vector dimension used, if known
            query_type: Type of query (e.g., "vector", "hybrid")
            additional_info: Additional metadata to log (e.g., filters, query text)
        """
        try:
            # Create performance metrics table if it doesn't exist
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS vector_search_metrics (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT NOW(),
                table_name VARCHAR(255) NOT NULL,
                query_time_ms FLOAT NOT NULL,
                result_count INT NOT NULL,
                vector_dimension INT,
                query_type VARCHAR(50),
                additional_info JSONB
            )
            """
            self.execute_postgres_query(create_table_sql)

            # Insert performance data
            insert_sql = """
            INSERT INTO vector_search_metrics
                (table_name, query_time_ms, result_count, vector_dimension, query_type, additional_info)
            VALUES
                (%s, %s, %s, %s, %s, %s)
            """
            self.execute_postgres_query(
                insert_sql, 
                (table_name, query_time * 1000, result_count, dimension, query_type, json.dumps(additional_info or {}))
            )

        except Exception as e:
            logger.warning(f"Failed to record vector search metrics: {str(e)}")
            # Non-critical error, don't raise exception

    def ensure_vector_indexes(self, table_name: str, vector_column: str = 'embedding', index_type:str = 'hnsw', 
                             dimension: int = 768, m: int = 16, ef_construction: int = 64) -> bool:
        """
        Ensures that the proper vector index is created for a vector column tooptimize search performance.
        
        Args:
            table_name: Name of the table containing the vector column
            vector_column: Name of the vector column (```python
            vector_column: Name of the vector column (default: 'embedding')
            index_type: Type of index to create ('ivfflat', 'hnsw')
            dimension: Dimension of the vectors
            m: HNSW-specific parameter: max number of connections per layer
            ef_construction: HNSW-specific parameter: size of the dynamic candidate list for construction
            
        Returns:
            bool: True if the index was created or already exists, False on failure
        """
        logger.info(f"Ensuring vector index for {table_name}.{vector_column}")
        
        if not self._check_vector_enabled():
            logger.error("Vector extension not available, cannot create vector indexes")
            return False
        
        try:
            # Check if index already exists
            check_sql = """
                SELECT 1 FROM pg_indexes
                WHERE tablename = %s AND indexdef LIKE %s
            """
            index_pattern = f"%{table_name}%{vector_column}%"
            result = self.execute_postgres_query(check_sql, (table_name, index_pattern))
            
            if result:
                logger.info(f"Vector index already exists for {table_name}.{vector_column}")
                return True
            
            # Create the index based on the specified type
            if index_type.lower() == 'ivfflat':
                # IVFFlat is better for larger datasets with faster but less precise searches
                # Determine number of lists based on dataset size (rule of thumb: sqrt(n)/2)
                count_sql = f"SELECT COUNT(*) FROM {table_name} WHERE {vector_column} IS NOT NULL"
                count_result = self.execute_postgres_query(count_sql)
                row_count = count_result[0]['count'] if count_result else 0
                
                # Calculate lists (at least 4, at most 1000)
                lists = max(4, min(1000, int(math.sqrt(row_count) / 2)))
                
                index_name = f"idx_ivfflat_{table_name}_{vector_column}"
                index_sql = f"""
                    CREATE INDEX {index_name} ON {table_name} 
                    USING ivfflat ({vector_column} vector_l2_ops) 
                    WITH (lists = {lists})
                """
            elif index_type.lower() == 'hnsw':
                # HNSW is better for more precise searches, slightly slower indexing
                index_name = f"idx_hnsw_{table_name}_{vector_column}"
                index_sql = f"""
                    CREATE INDEX {index_name} ON {table_name} 
                    USING hnsw ({vector_column} vector_l2_ops) 
                    WITH (m = {m}, ef_construction = {ef_construction})
                """
            else:
                logger.error(f"Unsupported index type: {index_type}")
                return False
            
            # Execute the index creation
            start_time = time.time()
            self.execute_postgres_query(index_sql)
            duration = time.time() - start_time
            
            logger.info(f"Created {index_type} index for {table_name}.{vector_column} in {duration:.2f} seconds")
            
            # Record index creation in metrics
            self._record_index_creation(table_name, vector_column, index_type, dimension, duration)
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating vector index for {table_name}.{vector_column}: {e}")
            return False
    
    def _record_index_creation(self, table_name: str, column_name: str, index_type: str,
                              dimension: int, duration: float):
        """Record vector index creation metrics"""
        try:
            # Create the vector_indexes table if it doesn't exist
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS vector_indexes (
                id SERIAL PRIMARY KEY,
                table_name VARCHAR(100) NOT NULL,
                column_name VARCHAR(100) NOT NULL,
                index_type VARCHAR(20) NOT NULL,
                dimension INTEGER NOT NULL,
                creation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                duration_seconds FLOAT NOT NULL
            )
            """
            self.execute_postgres_query(create_table_sql)
            
            # Insert the record
            insert_sql = """
            INSERT INTO vector_indexes 
            (table_name, column_name, index_type, dimension, duration_seconds) 
            VALUES (%s, %s, %s, %s, %s)
            """
            self.execute_postgres_query(insert_sql, 
                (table_name, column_name, index_type, dimension, duration))

        except Exception as e:
            logger.warning(f"Failed to record vector index creation metrics: {str(e)}")
            # Non-critical, don't propagate exception

    def _update_geospatial_point(self, table: str, record_id: str, latitude: float, longitude: float) -> bool:
        """
        Update the geospatial point for a record.
        
        Args:
            table: Table name
            record_id: ID of the record
            latitude: New latitude
            longitude: New longitude
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            sql = f"""
                UPDATE {table}
                SET geom = ST_SetSRID(ST_MakePoint(%s, %s), 4326)
                WHERE id = %s
            """
            result = self.execute_postgres_query(sql, (longitude, latitude, record_id))
            return result is not None
        except Exception as e:
            logger.error(f"Error updating geospatial point for {table} {record_id}: {str(e)}")
            return False

    def transaction(self):
        """
        Create a transaction context manager.
        
        Usage:
        with db_manager.transaction() as cursor:
            cursor.execute("INSERT INTO...")
            # All operations are in same transaction
            # Commits automatically on exit if no exceptions
            # Rolls back on exceptions
            
        Returns:
            A context manager for database transactions that provides a cursor
        """
        class TransactionContextManager:
            def __init__(self, db_manager):
                self.db_manager = db_manager
                self.conn = None
                self.cursor = None
            
            def __enter__(self):
                self.conn = self.db_manager._get_pg_connection()
                if not self.conn:
                    raise Exception("Failed to get database connection for transaction")
                self.cursor = self.conn.cursor()
                return self.cursor
                
            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.cursor:
                    try:
                        self.cursor.close()
                    except Exception:
                        pass
                    self.cursor = None
                    
                if not self.conn or self.conn.closed:
                    return
                    
                try:
                    if exc_type is not None:
                        # An exception occurred, roll back
                        self.conn.rollback()
                        logger.info(f"Transaction rolled back due to {exc_type.__name__}")
                    else:
                        # No exception, commit
                        self.conn.commit()
                        logger.info("Transaction committed successfully")
                finally:
                    self.db_manager._return_pg_connection(self.conn)
                    self.conn = None
                    
        return TransactionContextManager(self)

    def _test_raise_exception(self):
        """Method used only for testing exception handling in connection pool management."""
        raise Exception("Test exception for connection pool management")

    def text_to_embedding(self, text: str) -> List[float]:
        """
        Convert text to a vector embedding.
        
        Args:
            text: Text to convert to an embedding
            
        Returns:
            Vector embedding as a list of floats
            
        Note: This is a stub implementation that should be overridden by a concrete implementation
        that uses an actual embedding model.
        """
        logger.info(f"Called text_to_embedding with text: {text[:50]}...")
        try:
            # In a real implementation, this would call an embedding model
            # For test/stub purposes, generate a random vector of the correct dimension
            import numpy as np
            random_embedding = np.random.randn(self.vector_dimension).astype(np.float32).tolist()
            
            # Note: This is a stub implementation and should be replaced with actual model inference
            # Example real implementation would use a model like:
            # from sentence_transformers import SentenceTransformer
            # model = SentenceTransformer('all-MiniLM-L6-v2')
            # embedding = model.encode(text).tolist()
            
            logger.warning("Using stub implementation of text_to_embedding - replace with actual model for production")
            return random_embedding
        except Exception as e:
            logger.error(f"Error generating text embedding: {str(e)}")
            # Return a zero vector as fallback
            return [0.0] * self.vector_dimension

    def semantic_search(self, query: str, table: str = "attractions", limit: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Perform a semantic search using text-to-embedding conversion and vector search.
        
        Args:
            query: Text query to search with
            table: Table to search in
            limit: Maximum number of results to return
            filters: Additional filters to apply
            
        Returns:
            List of results matching the semantic search
        """
        logger.info(f"Called semantic_search with query={query}, table={table}, limit={limit}")
        try:
            # Convert text to embedding
            embedding = self.text_to_embedding(query)
            
            # Perform vector search with the embedding
            return self.vector_search(table, embedding, filters, limit)
        except Exception as e:
            logger.error(f"Error in semantic search: {str(e)}")
            return []
# End of file
