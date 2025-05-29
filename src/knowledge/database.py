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
import uuid

from src.utils.logger import get_logger
from src.knowledge.vector_tiered_cache import VectorTieredCache
from src.utils.query_cache import QueryCache
from src.utils.query_monitor import QueryMonitor
from src.utils.query_analyzer import QueryAnalyzer
from src.utils.query_batch import QueryBatch
from src.services.service_registry import ServiceRegistry

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
        # Initialize database connection
        self.db_type = DatabaseType.POSTGRES
        self.database_uri = database_uri or os.environ.get("POSTGRES_URI")
        logger.debug(f"Database URI: {self.database_uri}")
        logger.info(f"Database type determined: {self.db_type}")

        # Set vector dimension
        self.vector_dimension = vector_dimension

        # Define valid tables for whitelist checking
        self.VALID_TABLES = {'attractions', 'restaurants', 'accommodations', 'cities',
                          'regions', 'users', 'hotels', 'vector_search_metrics', 'vector_indexes',
                          'tourism_faqs', 'practical_info', 'events_festivals', 'tour_packages',
                          'itineraries', 'itinerary_types', 'itinerary_days'}

        # Initialize connection attributes
        self.pg_pool = None
        self.lock = threading.RLock()

        # Set shorter timeout for tests
        self.operation_timeout = 2 if os.environ.get('TESTING') == 'true' else 10

        # Initialize vector search cache
        redis_uri = os.environ.get("REDIS_URI")
        self.vector_cache = VectorTieredCache(
            redis_uri=redis_uri,
            ttl=3600,  # Cache vector search results for 1 hour
            max_size=1000  # Maximum size of local LRU cache
        )
        logger.info("Initialized vector tiered cache")

        # Initialize query cache
        self.query_cache = QueryCache(
            redis_uri=redis_uri,
            ttl=1800,  # Cache query results for 30 minutes
            max_size=500  # Maximum size of local LRU cache
        )
        logger.info("Initialized query cache")

        # Initialize service registry
        self.services = ServiceRegistry(self)
        logger.info("Initialized service registry")

        # Initialize query analyzer
        self.query_analyzer = QueryAnalyzer(
            slow_query_threshold_ms=500,  # 500ms threshold for slow queries
            max_queries_to_track=100
        )
        logger.info("Initialized query analyzer")

        # Connect to PostgreSQL
        self.connect()

    def connect(self):
        """Establish database connection (PostgreSQL only)."""
        return self._initialize_postgres_connection()

    def is_connected(self):
        """Check if the database connection is established."""
        return self.pg_pool is not None and hasattr(self.pg_pool, '_pool')

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

            # Create the connection pool with optimized settings
            min_conn = int(os.environ.get("PG_MIN_CONNECTIONS", "2"))
            max_conn = int(os.environ.get("PG_MAX_CONNECTIONS", "20"))

            # Use smaller pool for tests
            if os.environ.get('TESTING') == 'true':
                min_conn = 1
                max_conn = 3

            logger.info(f"Creating PostgreSQL connection pool (min={min_conn}, max={max_conn})...")

            # Use the provided database URI with optimized connection parameters
            self.pg_pool = pool.ThreadedConnectionPool(
                minconn=min_conn,
                maxconn=max_conn,
                dsn=self.database_uri,
                # Add connection validation and timeout settings
                connect_timeout=5,  # 5 seconds connection timeout
                keepalives=1,       # Enable TCP keepalives
                keepalives_idle=60, # Idle time before sending keepalive
                keepalives_interval=10, # Interval between keepalives
                keepalives_count=3  # Number of keepalives before giving up
            )

            # Initialize connection pool metrics
            self.pool_metrics = {
                "acquisition_times": [],
                "query_count": 0,
                "error_count": 0,
                "last_metrics_time": time.time()
            }

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
        # Import the database initialization module
        from src.knowledge.database_init import create_postgres_tables

        conn = self._get_pg_connection()
        if not conn:
            logger.error("Failed to get PostgreSQL connection for table creation")
            raise Exception("Failed to get PostgreSQL connection for table creation")

        try:
            # Use the improved implementation from database_init module
            create_postgres_tables(conn, self.vector_dimension)
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
        """Get a connection from the pool with retry logic and metrics tracking."""
        if not self.pg_pool:
            logger.error("No PostgreSQL connection pool available")
            return None

        start_time = time.time()
        retries = 3
        conn = None

        for attempt in range(retries):
            try:
                conn = self.pg_pool.getconn()
                if not conn.closed:
                    # Track connection acquisition time
                    acquisition_time_ms = (time.time() - start_time) * 1000
                    self.pool_metrics["acquisition_times"].append(acquisition_time_ms)

                    # Log slow connection acquisitions
                    if acquisition_time_ms > 100:  # More than 100ms is slow
                        logger.warning(f"Slow connection acquisition: {acquisition_time_ms:.2f}ms")

                    # Record metrics periodically
                    self._record_pool_metrics()

                    return conn

                logger.warning("Got closed connection from pool, attempting to reconnect...")
                self.pg_pool.putconn(conn)

            except Exception as e:
                logger.error(f"Error getting connection on attempt {attempt + 1}: {str(e)}")
                self.pool_metrics["error_count"] += 1
                if attempt == retries - 1:
                    return None

        return None

    def _record_pool_metrics(self):
        """Record connection pool metrics to the database."""
        # Only record metrics every 5 minutes
        current_time = time.time()
        if current_time - self.pool_metrics["last_metrics_time"] < 300:  # 5 minutes
            return

        try:
            # Get current pool status
            if not hasattr(self.pg_pool, "_used") or not hasattr(self.pg_pool, "_pool"):
                return

            current_connections = len(self.pg_pool._used)
            available_connections = len(self.pg_pool._pool)

            # Calculate average acquisition time
            avg_acquisition_time = 0
            if self.pool_metrics["acquisition_times"]:
                avg_acquisition_time = sum(self.pool_metrics["acquisition_times"]) / len(self.pool_metrics["acquisition_times"])

            # Record metrics to database
            sql = """
                SELECT record_connection_pool_stats(%s, %s, %s, %s, %s, %s, %s)
            """
            params = (
                self.pg_pool.minconn,
                self.pg_pool.maxconn,
                current_connections,
                available_connections,
                avg_acquisition_time,
                self.pool_metrics["query_count"],
                self.pool_metrics["error_count"]
            )

            # Execute directly without using our wrapper to avoid recursion
            conn = None
            try:
                conn = self.pg_pool.getconn()
                with conn.cursor() as cursor:
                    cursor.execute(sql, params)
                    conn.commit()
            finally:
                if conn:
                    self.pg_pool.putconn(conn)

            # Reset metrics
            self.pool_metrics = {
                "acquisition_times": [],
                "query_count": 0,
                "error_count": 0,
                "last_metrics_time": current_time
            }

        except Exception as e:
            logger.error(f"Error recording pool metrics: {e}")
            # Don't let metrics recording failure affect normal operation

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

    @QueryMonitor.monitor_query
    def execute_postgres_query(self, query, params=None, fetchall=True, cursor_factory=None):
        """
        Execute a PostgreSQL query using the connection pool.

        This method is decorated with QueryMonitor.monitor_query to track performance.
        Slow queries (>100ms) will be logged with detailed information.

        Args:
            query (str): SQL query to execute
            params (tuple, optional): Query parameters
            fetchall (bool): Whether to fetch all results or just one
            cursor_factory: Factory for cursor creation

        Returns:
            Query results or None if an error occurred
        """
        if self.db_type != DatabaseType.POSTGRES:
            logger.error("Attempted to execute PostgreSQL query when not using PostgreSQL")
            return None

        conn = None
        query_id = str(uuid.uuid4())
        start_time = time.time()

        try:
            conn = self._get_pg_connection()
            if not conn:
                logger.error("Failed to get PostgreSQL connection")
                self.pool_metrics["error_count"] += 1
                return None

            cursor_factory = cursor_factory or RealDictCursor
            with conn.cursor(cursor_factory=cursor_factory) as cursor:
                cursor.execute(query, params or ())

                if query.strip().upper().startswith(("SELECT", "WITH")):
                    result = cursor.fetchall() if fetchall else cursor.fetchone()
                    rows_affected = len(result) if result and fetchall else (1 if result else 0)
                else:
                    conn.commit()
                    result = cursor.rowcount
                    rows_affected = result

                # Calculate execution time
                execution_time_ms = (time.time() - start_time) * 1000

                # Track query metrics
                self.pool_metrics["query_count"] += 1

                # Record query for analysis
                rows_affected = len(result) if result and fetchall else (1 if result else 0) if query.strip().upper().startswith(("SELECT", "WITH")) else result
                self.query_analyzer.record_query(query, params or (), execution_time_ms, rows_affected)

                # Log slow queries (>100ms)
                if execution_time_ms > 100:
                    logger.warning(f"Slow query ({execution_time_ms:.2f}ms): {query[:100]}...")

                return result

        except Exception as e:
            logger.error(f"Error executing PostgreSQL query: {str(e)}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            self.pool_metrics["error_count"] += 1
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

    def get_attraction(self, attraction_id: int):
        """
        Get attraction by ID (PostgreSQL only).

        Args:
            attraction_id (int): ID of the attraction

        Returns:
            dict: Attraction data or None if not found
        """
        logger.info(f"DatabaseManager.get_attraction called for ID: {attraction_id}")

        # Check cache first
        cached_result = self.query_cache.get_record("attractions", attraction_id)
        if cached_result is not None:
            logger.info(f"Cache hit for attraction {attraction_id}")
            return cached_result

        # Cache miss, get from database
        logger.info(f"Cache miss for attraction {attraction_id}, fetching from database")

        # Import here to avoid circular imports
        from src.services.attraction_service import AttractionService

        # Get the attraction service from the registry
        attraction_service = self.services.get_service(AttractionService)

        # Use the service to get the attraction
        result = attraction_service.get_attraction(attraction_id)

        # Cache the result if found
        if result:
            self.query_cache.set_record("attractions", attraction_id, result)

        return result

    def get_restaurant(self, restaurant_id: int) -> Optional[Dict[str, Any]]:
        """
        Get restaurant by ID.

        Args:
            restaurant_id: ID of the restaurant to retrieve

        Returns:
            dict: Restaurant data or None if not found
        """
        logger.info(f"Called get_restaurant for ID: {restaurant_id}")

        # Check cache first
        cached_result = self.query_cache.get_record("restaurants", restaurant_id)
        if cached_result is not None:
            logger.info(f"Cache hit for restaurant {restaurant_id}")
            return cached_result

        # Cache miss, get from database
        logger.info(f"Cache miss for restaurant {restaurant_id}, fetching from database")

        # Import here to avoid circular imports
        from src.services.restaurant_service import RestaurantService

        # Get the restaurant service from the registry
        restaurant_service = self.services.get_service(RestaurantService)

        # Use the service to get the restaurant
        result = restaurant_service.get_restaurant(restaurant_id)

        # Cache the result if found
        if result:
            self.query_cache.set_record("restaurants", restaurant_id, result)

        return result

    def get_city(self, city_id: int) -> Optional[Dict[str, Any]]:
        """
        Get city by ID (PostgreSQL only).

        Args:
            city_id: ID of the city to retrieve

        Returns:
            dict: City data or None if not found
        """
        logger.info(f"Called get_city for ID: {city_id}")
        try:
            sql = "SELECT * FROM cities WHERE id = %s"
            result = self.execute_postgres_query(sql, (city_id,), fetchall=False)
            if result:
                # Parse JSON fields
                json_fields = ['data', 'name', 'description']
                for field in json_fields:
                    self._parse_json_field(result, field)
                return result
            return None
        except Exception as e:
            return self._handle_error(f"get_city_{city_id}", e)

    def get_accommodation(self, accommodation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get accommodation by ID.

        Args:
            accommodation_id: ID of the accommodation to retrieve

        Returns:
            dict: Accommodation data or None if not found
        """
        logger.info(f"Called get_accommodation for ID: {accommodation_id}")
        try:
            sql = """
                SELECT id, name, description, type_id, city_id, region_id,
                       latitude, longitude, data, price_min, price_max,
                       created_at, updated_at
                FROM accommodations
                WHERE id = %s
            """
            result = self.execute_postgres_query(sql, (accommodation_id,), fetchall=False)
            if result:
                # Parse JSON fields
                json_fields = ['data', 'name', 'description']
                for field in json_fields:
                    self._parse_json_field(result, field)
                return result
            return None
        except Exception as e:
            return self._handle_error(f"get_accommodation_{accommodation_id}", e)

    def get_region(self, region_id: str) -> Optional[Dict[str, Any]]:
        """
        Get region by ID.

        Args:
            region_id: ID of the region to retrieve

        Returns:
            dict: Region data or None if not found
        """
        logger.info(f"Called get_region for ID: {region_id}")
        try:
            sql = "SELECT * FROM regions WHERE id = %s"
            result = self.execute_postgres_query(sql, (region_id,), fetchall=False)
            if result:
                # Parse JSON fields
                json_fields = ['data', 'name', 'description']
                for field in json_fields:
                    self._parse_json_field(result, field)
                return result
            return None
        except Exception as e:
            return self._handle_error(f"get_region_{region_id}", e)

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user by ID.
        Schema: users(id, username, ...)

        Args:
            user_id: User ID (integer)

        Returns:
            dict or None: User data or None if not found
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

    def search_restaurants(self, query: Optional[Dict[str, Any]] = None, filters: Optional[Dict[str, Any]] = None, limit: int = 10, offset: int = 0, language: str = "en") -> List[Dict[str, Any]]:
        """
        Search restaurants based on query or filters.

        Args:
            query (dict or str): Dictionary of search criteria or text query string
            filters (dict): Additional filters to apply
            limit (int): Maximum number of results to return
            offset (int): Offset for pagination
            language (str): Language code (en, ar)

        Returns:
            list of dicts: List of restaurant records matching the search criteria
        """
        logger.info(f"Called search_restaurants with query={query}, filters={filters}, limit={limit}, offset={offset}, language={language}")

        try:
            # Combine query and filters if both are provided
            search_filters = {}

            # Handle string query (text search)
            if isinstance(query, str) and query:
                search_filters["text_search"] = query
            # Handle dictionary query
            elif isinstance(query, dict) and query:
                search_filters.update(query)

            # Add any additional filters
            if filters:
                search_filters.update(filters)

            # Build the base query
            base_query = "SELECT * FROM restaurants WHERE 1=1"
            params = []

            # Apply filters to the query
            if search_filters:
                # City filter - use city_id instead of city
                if "city" in search_filters:
                    base_query += " AND city_id = %s"
                    params.append(search_filters['city'])

                # Cuisine filter - use cuisine_id instead of cuisine
                if "cuisine" in search_filters:
                    base_query += " AND cuisine_id = %s"
                    params.append(search_filters['cuisine'])

                # Name filter - use JSONB name field
                if "name" in search_filters:
                    base_query += " AND (name->>'en' ILIKE %s OR name->>'ar' ILIKE %s)"
                    name_pattern = f"%{search_filters['name']}%"
                    params.extend([name_pattern, name_pattern])

                # Price range filter
                if "price_range" in search_filters:
                    base_query += " AND price_range = %s"
                    params.append(search_filters['price_range'])

                # Text search across multiple fields
                if "text_search" in search_filters:
                    search_term = search_filters["text_search"]
                    base_query += " AND (name->>'en' ILIKE %s OR name->>'ar' ILIKE %s OR description->>'en' ILIKE %s OR description->>'ar' ILIKE %s OR cuisine_id ILIKE %s)"
                    search_pattern = f"%{search_term}%"
                    params.extend([search_pattern, search_pattern, search_pattern, search_pattern, search_pattern])

                # Region filter - use region_id instead of region
                if "region" in search_filters:
                    base_query += " AND region_id = %s"
                    params.append(search_filters['region'])

                # Type filter - use type_id instead of type
                if "type" in search_filters:
                    base_query += " AND type_id = %s"
                    params.append(search_filters['type'])

            # Add pagination with ordering by JSONB name field
            base_query += " ORDER BY name->>'en' LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            # Execute the query
            results = self.execute_postgres_query(base_query, tuple(params))
            if results is None:
                logger.warning("Query returned None result")
                return []

            # Process JSONB data fields
            processed_results = []
            for row in results:
                if "data" in row and row["data"]:
                    try:
                        if isinstance(row["data"], str):
                            row["data"] = json.loads(row["data"])
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse JSON data for restaurant {row.get('id', 'unknown')}")
                processed_results.append(row)

            logger.info(f"Found {len(processed_results)} restaurants matching the criteria")
            return processed_results
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

        Args:
            query: Dictionary of search criteria
            limit: Maximum number of results to return
            offset: Offset for pagination

        Returns:
            List of user records matching the search criteria
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
            # Check if table exists
            if not self._table_exists(table):
                logger.error(f"Table {table} does not exist")
                return []

            # Get table columns to determine search approach
            columns = self._get_table_columns(table)
            logger.debug(f"Table {table} columns: {columns}")

            # Start with base query
            sql = f"SELECT * FROM {table} WHERE 1=1"
            params = []

            # Add search conditions based on table schema
            if search_text:
                search_conditions = []
                pattern = f"%{search_text}%"

                # Prioritize JSONB columns over legacy columns

                # Check for JSONB name column
                if 'name' in columns:
                    search_conditions.append("name->>'en' ILIKE %s")
                    search_conditions.append("name->>'ar' ILIKE %s")
                    params.extend([pattern, pattern])
                # Fall back to legacy columns if JSONB not available
                elif 'name_en' in columns and 'name_ar' in columns:
                    # Legacy code path - should be removed once migration is complete
                    logger.warning("Using legacy name_en/name_ar columns instead of JSONB name column")
                    search_conditions.append("name_en ILIKE %s")
                    search_conditions.append("name_ar ILIKE %s")
                    params.extend([pattern, pattern])

                # Check for JSONB description column
                if 'description' in columns:
                    search_conditions.append("description->>'en' ILIKE %s")
                    search_conditions.append("description->>'ar' ILIKE %s")
                    params.extend([pattern, pattern])
                # Fall back to legacy columns if JSONB not available
                elif 'description_en' in columns and 'description_ar' in columns:
                    search_conditions.append("description_en ILIKE %s")
                    search_conditions.append("description_ar ILIKE %s")
                    params.extend([pattern, pattern])

                # Add text search to any other text columns that might contain the search term
                for col in columns:
                    if col not in ['name_en', 'name_ar', 'description_en', 'description_ar', 'name', 'description'] and \
                       any(text_type in col.lower() for text_type in ['text', 'name', 'title', 'description', 'address']):
                        search_conditions.append(f"{col} ILIKE %s")
                        params.append(pattern)

                # If no search conditions were added, add a fallback
                if not search_conditions:
                    # Add a generic condition that will work for most tables
                    search_conditions.append("id::text ILIKE %s")
                    params.append(pattern)

                # Add search conditions to query
                if search_conditions:
                    sql += f" AND ({' OR '.join(search_conditions)})"

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

            # Log the final SQL query for debugging
            logger.debug(f"Enhanced search SQL: {sql}")
            logger.debug(f"Enhanced search params: {params}")

            return self.execute_postgres_query(sql, tuple(params)) or []
        except Exception as e:
            logger.error(f"Error in enhanced search: {e}")
            return []

    def vector_search(self, table_name: str, embedding: list, filters: Optional[dict] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Perform a vector search with tiered caching and optimized query execution.

        Args:
            table_name (str): Name of the table to search.
            embedding (list): Vector embedding for similarity search.
            filters (dict, optional): Additional filters to apply.
            limit (int): Maximum number of results to return.

        Returns:
            List[Dict[str, Any]]: Search results.
        """
        try:
            # Check cache first
            cached_results = self.vector_cache.get_vector_search_results(
                table_name=table_name,
                embedding=embedding,
                filters=filters,
                limit=limit
            )

            if cached_results is not None:
                logger.info(f"Cache hit for vector search on {table_name}")
                return cached_results

            # Cache miss, perform the search
            logger.info(f"Cache miss for vector search on {table_name}, performing database query")

            # Validate table name
            if not self._table_exists(table_name):
                logger.warning(f"Table '{table_name}' does not exist")
                return []

            # Verify the embedding column exists
            if not self._postgres_column_exists(table_name, 'embedding'):
                logger.warning(f"Table '{table_name}' does not have an embedding column")
                return []

            # Check if pgvector is enabled
            if not self._check_vector_enabled():
                logger.warning("pgvector extension is not enabled, cannot perform vector search")
                return []

            # Optimize the query based on table size and index availability
            conn = self._get_pg_connection()
            if not conn:
                logger.error("Failed to get database connection")
                return []

            try:
                with conn.cursor() as cursor:
                    # Check table size
                    cursor.execute(f"SELECT count(*) FROM {table_name}")
                    table_size = cursor.fetchone()[0]

                    # Check if HNSW index exists
                    cursor.execute(f"""
                        SELECT indexname FROM pg_indexes
                        WHERE tablename = '{table_name}'
                        AND indexdef LIKE '%USING hnsw%'
                    """)
                    has_hnsw_index = cursor.fetchone() is not None

                    # Check if IVFFlat index exists
                    cursor.execute(f"""
                        SELECT indexname FROM pg_indexes
                        WHERE tablename = '{table_name}'
                        AND indexdef LIKE '%USING ivfflat%'
                    """)
                    has_ivfflat_index = cursor.fetchone() is not None

                    # Determine the best search method based on table size and available indexes
                    if has_hnsw_index:
                        # HNSW is best for approximate nearest neighbor search
                        search_method = "hnsw"
                    elif has_ivfflat_index:
                        # IVFFlat is good for medium-sized tables
                        search_method = "ivfflat"
                    elif table_size < 10000:
                        # For small tables, exact search is fine
                        search_method = "exact"
                    else:
                        # For large tables without specialized indexes, use exact search but with a limit
                        search_method = "exact_limited"

                    logger.info(f"Using {search_method} search method for table {table_name} with size {table_size}")

                    # Build the query based on the search method
                    if search_method == "hnsw" or search_method == "ivfflat":
                        # Use the index for approximate search
                        sql = f"""
                            SELECT *, 1 - (embedding <=> %s::vector) AS similarity
                            FROM {table_name}
                            WHERE embedding IS NOT NULL
                        """
                    elif search_method == "exact":
                        # Use exact search with cosine distance
                        sql = f"""
                            SELECT *, 1 - (embedding <=> %s::vector) AS similarity
                            FROM {table_name}
                            WHERE embedding IS NOT NULL
                        """
                    else:  # exact_limited
                        # Use exact search but with a preliminary filter to limit the search space
                        sql = f"""
                            WITH candidates AS (
                                SELECT id, embedding
                                FROM {table_name}
                                WHERE embedding IS NOT NULL
                                LIMIT 10000
                            )
                            SELECT t.*, 1 - (t.embedding <=> %s::vector) AS similarity
                            FROM {table_name} t
                            JOIN candidates c ON t.id = c.id
                        """

                    params = [embedding]

                    # Add additional filters
                    if filters:
                        for key, value in filters.items():
                            sql += f" AND {key} = %s"
                            params.append(value)

                    # Add ordering and limit
                    sql += " ORDER BY similarity DESC LIMIT %s"
                    params.append(limit)

                    # Execute the query
                    cursor.execute(sql, tuple(params))
                    results = cursor.fetchall()

                    # Convert results to dictionaries
                    dict_results = []
                    for row in results:
                        dict_row = {}
                        for i, col in enumerate(cursor.description):
                            dict_row[col.name] = row[i]
                        dict_results.append(dict_row)

                    # Cache the results
                    if dict_results:
                        self.vector_cache.set_vector_search_results(
                            table_name=table_name,
                            embedding=embedding,
                            results=dict_results,
                            filters=filters,
                            limit=limit
                        )

                    return dict_results
            finally:
                self._return_pg_connection(conn)
        except Exception as e:
            return self._handle_error(f"vector_search_{table_name}", e, return_empty_list=True)

    def vector_search_attractions(self, embedding: list, filters: Optional[dict] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Vector search on attractions table.
        Schema: attractions(embedding VECTOR, ...)
        Args: embedding (list[float]), filters (dict), limit (int)
        Returns: list of dicts
        """
        logger.info(f"Called vector_search_attractions with filters={filters}, limit={limit}")

        try:
            # Use the vector search service
            service = self._get_vector_search_service()
            return service.search_attractions(embedding, filters, limit)
        except Exception as e:
            return self._handle_error("vector_search_attractions", e, return_empty_list=True)

    def vector_search_restaurants(self, embedding: list, filters: Optional[dict] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Vector search on restaurants table.
        Schema: restaurants(embedding VECTOR, ...)
        Args: embedding (list[float]), filters (dict), limit (int)
        Returns: list of dicts
        """
        logger.info(f"Called vector_search_restaurants with filters={filters}, limit={limit}")

        try:
            # Use the vector search service
            service = self._get_vector_search_service()
            return service.search_restaurants(embedding, filters, limit)
        except Exception as e:
            return self._handle_error("vector_search_restaurants", e, return_empty_list=True)

    def vector_search_hotels(self, embedding: list, filters: Optional[dict] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Vector search on hotels table.
        Schema: hotels(embedding VECTOR, ...)
        Args: embedding (list[float]), filters (dict), limit (int)
        Returns: list of dicts
        """
        logger.info(f"Called vector_search_hotels with filters={filters}, limit={limit}")

        try:
            # Use the vector search service
            service = self._get_vector_search_service()
            return service.search_hotels(embedding, filters, limit)
        except Exception as e:
            return self._handle_error("vector_search_hotels", e, return_empty_list=True)

    def vector_search_cities(self, embedding: list, filters: Optional[dict] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Vector search on cities table.
        Schema: cities(embedding VECTOR, ...)
        Args: embedding (list[float]), filters (dict), limit (int)
        Returns: list of dicts
        """
        logger.info(f"Called vector_search_cities with filters={filters}, limit={limit}")

        try:
            # Use the vector search service
            service = self._get_vector_search_service()
            return service.search_cities(embedding, filters, limit)
        except Exception as e:
            return self._handle_error("vector_search_cities", e, return_empty_list=True)

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

    def _get_table_columns(self, table_name: str) -> List[str]:
        """
        Get the column names for a table in the current PostgreSQL database.
        """
        try:
            if self.db_type == DatabaseType.POSTGRES and self.pg_pool:
                conn = self._get_pg_connection()
                try:
                    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                        cursor.execute("""
                            SELECT column_name
                            FROM information_schema.columns
                            WHERE table_name = %s
                            ORDER BY ordinal_position
                        """, (table_name,))
                        columns = cursor.fetchall()
                    return [col['column_name'] for col in columns] if columns else []
                finally:
                    self._return_pg_connection(conn)
            else:
                logger.error("_get_table_columns called, but not using PostgreSQL or pool not initialized.")
                return []
        except Exception as e:
            logger.error(f"Error getting table columns: {e}")
            return []

    def get_all_restaurants_no_user(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get restaurants without requiring user_id column for testing."""
        query = "SELECT * FROM restaurants LIMIT %s"
        params = (limit,)
        return self.execute_query(query, params)

    def search_attractions(self, query: Optional[Dict[str, Any]] = None, filters: Optional[Dict[str, Any]] = None, limit: int = 10, offset: int = 0, language: str = "en") -> List[Dict[str, Any]]:
        """
        Search attractions based on query or filters.

        Args:
            query (dict or str): Dictionary of search criteria or text query string
            filters (dict): Additional filters to apply
            limit (int): Maximum number of results to return
            offset (int): Offset for pagination
            language (str): Language code (en, ar)

        Returns:
            list of dicts: List of attraction records matching the search criteria
        """
        logger.info(f"[KB] search_attractions called with query={query}, filters={filters}, language={language}, limit={limit}")

        try:
            # Check cache first
            cached_results = self.query_cache.get_search_results(
                table_name="attractions",
                query=query,
                filters=filters,
                limit=limit,
                offset=offset,
                language=language
            )

            if cached_results is not None:
                logger.info(f"Cache hit for attractions search with query={query}, filters={filters}")
                return cached_results

            # Cache miss, perform the search
            logger.info(f"Cache miss for attractions search, performing database query")

            # Combine query and filters if both are provided
            search_filters = {}

            # Handle string query (text search)
            if isinstance(query, str) and query:
                search_filters["text_search"] = query
            # Handle dictionary query
            elif isinstance(query, dict) and query:
                search_filters.update(query)

            # Add any additional filters
            if filters:
                search_filters.update(filters)

            # Build the base query
            base_query = "SELECT * FROM attractions WHERE 1=1"
            params = []

            # Apply filters to the query
            if search_filters:
                # City filter
                if "city" in search_filters:
                    base_query += " AND city ILIKE %s"
                    params.append(f"%{search_filters['city']}%")

                # Type filter
                if "type" in search_filters:
                    base_query += " AND type ILIKE %s"
                    params.append(f"%{search_filters['type']}%")

                # Name filter
                if "name" in search_filters:
                    base_query += " AND (name_en ILIKE %s OR name->>'ar' ILIKE %s)"
                    name_pattern = f"%{search_filters['name']}%"
                    params.extend([name_pattern, name_pattern])

                # Region filter
                if "region" in search_filters:
                    base_query += " AND region ILIKE %s"
                    params.append(f"%{search_filters['region']}%")

                # Text search across multiple fields
                if "text_search" in search_filters:
                    search_term = search_filters["text_search"]
                    base_query += " AND (name_en ILIKE %s OR name->>'ar' ILIKE %s OR description->>'en' ILIKE %s OR description->>'ar' ILIKE %s OR type ILIKE %s)"
                    search_pattern = f"%{search_term}%"
                    params.extend([search_pattern, search_pattern, search_pattern, search_pattern, search_pattern])

                # Specific name_en filter with operator support
                if "name_en" in search_filters:
                    if isinstance(search_filters["name_en"], dict) and "$like" in search_filters["name_en"]:
                        base_query += " AND name->>'en' ILIKE %s"
                        params.append(search_filters["name_en"]["$like"])
                    else:
                        base_query += " AND name->>'en' = %s"
                        params.append(search_filters["name_en"])

                # Specific name_ar filter with operator support
                if "name_ar" in search_filters:
                    if isinstance(search_filters["name_ar"], dict) and "$like" in search_filters["name_ar"]:
                        base_query += " AND name->>'ar' ILIKE %s"
                        params.append(search_filters["name_ar"]["$like"])
                    else:
                        base_query += " AND name->>'ar' = %s"
                        params.append(search_filters["name_ar"])

            # Add pagination with ordering
            base_query += " ORDER BY name->>'en' LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            # Execute the query
            results = self.execute_postgres_query(base_query, tuple(params))
            if results is None:
                logger.warning("Query returned None result")
                return []

            # Process JSONB data fields
            processed_results = []
            for row in results:
                if "data" in row and row["data"]:
                    try:
                        if isinstance(row["data"], str):
                            row["data"] = json.loads(row["data"])
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse JSON data for attraction {row.get('id', 'unknown')}")
                processed_results.append(row)

            # Cache the results
            if processed_results:
                self.query_cache.set_search_results(
                    table_name="attractions",
                    results=processed_results,
                    query=query,
                    filters=filters,
                    limit=limit,
                    offset=offset,
                    language=language
                )

            logger.info(f"Found {len(processed_results)} attractions matching the criteria")
            return processed_results
        except Exception as e:
            logger.error(f"Error searching attractions: {e}")
            return []

    def search_accommodations(self, query: Optional[Dict[str, Any]] = None, filters: Optional[Dict[str, Any]] = None, limit: int = 10, offset: int = 0, language: str = "en") -> List[Dict[str, Any]]:
        """
        Search accommodations based on query or filters.

        Args:
            query (dict or str): Dictionary of search criteria or text query string
            filters (dict): Additional filters to apply
            limit (int): Maximum number of results to return
            offset (int): Offset for pagination
            language (str): Language code (en, ar)

        Returns:
            list of dicts: List of accommodation records matching the search criteria
        """
        logger.info(f"Called search_accommodations with query={query}, filters={filters}, limit={limit}, offset={offset}, language={language}")

        try:
            # Combine query and filters if both are provided
            search_filters = {}

            # Handle string query (text search)
            if isinstance(query, str) and query:
                search_filters["text_search"] = query
            # Handle dictionary query
            elif isinstance(query, dict) and query:
                search_filters.update(query)

            # Add any additional filters
            if filters:
                search_filters.update(filters)

            # Build the base query
            base_query = "SELECT * FROM accommodations WHERE 1=1"
            params = []

            # Apply filters to the query
            if search_filters:
                # City filter
                if "city" in search_filters:
                    base_query += " AND city ILIKE %s"
                    params.append(f"%{search_filters['city']}%")

                # Type filter
                if "type" in search_filters:
                    base_query += " AND type ILIKE %s"
                    params.append(f"%{search_filters['type']}%")

                # Name filter
                if "name" in search_filters:
                    base_query += " AND (name_en ILIKE %s OR name->>'ar' ILIKE %s)"
                    name_pattern = f"%{search_filters['name']}%"
                    params.extend([name_pattern, name_pattern])

                # Price range filters
                if "price_min" in search_filters:
                    base_query += " AND price_min >= %s"
                    params.append(search_filters["price_min"])

                if "price_max" in search_filters:
                    base_query += " AND price_max <= %s"
                    params.append(search_filters["price_max"])

                # Category filter
                if "category" in search_filters:
                    base_query += " AND category ILIKE %s"
                    params.append(f"%{search_filters['category']}%")

                # Region filter
                if "region" in search_filters:
                    base_query += " AND region ILIKE %s"
                    params.append(f"%{search_filters['region']}%")

                # Text search across multiple fields
                if "text_search" in search_filters:
                    search_term = search_filters["text_search"]
                    base_query += " AND (name_en ILIKE %s OR name->>'ar' ILIKE %s OR description->>'en' ILIKE %s OR description->>'ar' ILIKE %s OR type ILIKE %s)"
                    search_pattern = f"%{search_term}%"
                    params.extend([search_pattern, search_pattern, search_pattern, search_pattern, search_pattern])

            # Add pagination with ordering
            base_query += " ORDER BY name->>'en' LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            # Execute the query
            results = self.execute_postgres_query(base_query, tuple(params))
            if results is None:
                logger.warning("Query returned None result")
                return []

            # Process JSONB data fields
            processed_results = []
            for row in results:
                if "data" in row and row["data"]:
                    try:
                        if isinstance(row["data"], str):
                            row["data"] = json.loads(row["data"])
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse JSON data for accommodation {row.get('id', 'unknown')}")
                processed_results.append(row)

            logger.info(f"Found {len(processed_results)} accommodations matching the criteria")
            return processed_results
        except Exception as e:
            logger.error(f"Error searching accommodations: {e}")
            return []

    def search_hotels(self, query: Optional[Dict[str, Any]] = None, filters: Optional[Dict[str, Any]] = None, limit: int = 10, offset: int = 0, language: str = "en") -> List[Dict[str, Any]]:
        """
        Search hotels table (alias for search_accommodations).

        Args:
            query: Dictionary of search criteria
            filters: Additional filters to apply
            limit: Maximum number of results to return
            offset: Offset for pagination
            language: Language code (en, ar)

        Returns: list of dicts
        """
        logger.info(f"Called search_hotels with query={query}, filters={filters}, limit={limit}, offset={offset}, language={language}")
        return self.search_accommodations(query=query, filters=filters, limit=limit, offset=offset, language=language)

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

    def _handle_error(self, operation: str, error: Exception, return_empty_list: bool = False):
        """
        Standardized error handling for database operations.

        Args:
            operation: Description of the operation that failed
            error: The exception that was raised
            return_empty_list: Whether to return an empty list (True) or None (False)

        Returns:
            [] if return_empty_list is True, None otherwise
        """
        logger.error(f"Error in {operation}: {str(error)}")
        if hasattr(error, "__traceback__"):
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
        return [] if return_empty_list else None

    def analyze_slow_queries(self) -> Dict[str, Any]:
        """
        Analyze slow queries and suggest optimizations.

        Returns:
            Dict containing analysis results and optimization suggestions
        """
        logger.info("Analyzing slow queries")

        # Get slow queries
        slow_queries = self.query_analyzer.get_slow_queries()

        if not slow_queries:
            logger.info("No slow queries found")
            return {
                "slow_queries": [],
                "suggestions": [],
                "indexes": {}
            }

        # Analyze query plans for slow queries
        plans = []
        for query_info in slow_queries[:5]:  # Analyze top 5 slowest queries
            query = query_info["query"]
            params = query_info["params"]

            try:
                plan_info = self.query_analyzer.analyze_query_plan(self, query, params)
                if plan_info:
                    plans.append({
                        "query": query,
                        "duration_ms": query_info["duration_ms"],
                        "plan": plan_info
                    })
            except Exception as e:
                logger.error(f"Error analyzing query plan: {str(e)}")

        # Get index suggestions
        index_suggestions = self.query_analyzer.suggest_indexes(self)

        # Compile general suggestions
        suggestions = []

        # Check for sequential scans
        seq_scan_count = sum(1 for p in plans if p.get("plan", {}).get("analysis", {}).get("issues", []) and any("Sequential scan" in issue for issue in p.get("plan", {}).get("analysis", {}).get("issues", [])))
        if seq_scan_count > 0:
            suggestions.append(f"Found {seq_scan_count} queries with sequential scans. Consider adding indexes on frequently queried columns.")

        # Check for expensive joins
        join_issues_count = sum(1 for p in plans if p.get("plan", {}).get("analysis", {}).get("issues", []) and any("join" in issue.lower() for issue in p.get("plan", {}).get("analysis", {}).get("issues", [])))
        if join_issues_count > 0:
            suggestions.append(f"Found {join_issues_count} queries with expensive joins. Review join conditions and consider adding indexes on join columns.")

        # Check for filter issues
        filter_issues_count = sum(1 for p in plans if p.get("plan", {}).get("analysis", {}).get("issues", []) and any("filter" in issue.lower() for issue in p.get("plan", {}).get("analysis", {}).get("issues", [])))
        if filter_issues_count > 0:
            suggestions.append(f"Found {filter_issues_count} queries with filter issues. Review filter conditions and consider adding indexes for frequently filtered columns.")

        # Add caching suggestion if appropriate
        if len(slow_queries) > 3:
            suggestions.append("Consider implementing caching for frequently executed queries to reduce database load.")

        # Add query batching suggestion if appropriate
        if any(q["query"].startswith("INSERT") or q["query"].startswith("UPDATE") for q in slow_queries):
            suggestions.append("Consider using query batching for bulk insert and update operations.")

        return {
            "slow_queries": [{
                "query": q["query"],
                "duration_ms": q["duration_ms"],
                "rows_affected": q["rows_affected"],
                "timestamp": q["timestamp"]
            } for q in slow_queries],
            "plans": plans,
            "suggestions": suggestions,
            "indexes": index_suggestions
        }

    def create_batch_executor(self, batch_size: int = 100, auto_execute: bool = False) -> QueryBatch:
        """
        Create a query batch executor for efficient bulk operations.

        Args:
            batch_size: Maximum number of operations in a batch
            auto_execute: Whether to automatically execute batches when they reach batch_size

        Returns:
            QueryBatch: Batch executor instance
        """
        return QueryBatch(self, batch_size, auto_execute)

    def _parse_json_field(self, record: dict, field_name: str) -> dict:
        """
        Parse a JSON field in a record safely.

        Args:
            record: The record containing the field
            field_name: The name of the field to parse

        Returns:
            The updated record with the parsed field
        """
        if field_name in record and record[field_name]:
            if isinstance(record[field_name], str):
                try:
                    record[field_name] = json.loads(record[field_name])
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON data for {field_name}")
        return record

    def generic_get(self, table: str, record_id: int, jsonb_fields: List[str] = None) -> Optional[Dict[str, Any]]:
        """
        Generic method to get a record by ID.

        Args:
            table: Table name
            record_id: ID of the record to retrieve
            jsonb_fields: List of JSONB fields to parse

        Returns:
            dict: Record data or None if not found
        """
        logger.info(f"Called generic_get for table={table}, id={record_id}")
        try:
            # Validate table name
            if table not in self.VALID_TABLES:
                logger.error(f"Invalid table name: {table}")
                return None

            sql = f"SELECT * FROM {table} WHERE id = %s"
            result = self.execute_postgres_query(sql, (record_id,), fetchall=False)

            if result:
                # Parse JSON fields
                if jsonb_fields:
                    for field in jsonb_fields:
                        self._parse_json_field(result, field)
                return result
            return None
        except Exception as e:
            return self._handle_error(f"generic_get_{table}_{record_id}", e)

    def generic_search(self, table: str, filters: Dict[str, Any] = None,
                      limit: int = 10, offset: int = 0,
                      jsonb_fields: List[str] = None,
                      language: str = "en") -> List[Dict[str, Any]]:
        """
        Generic method to search records.

        Args:
            table: Table name
            filters: Dictionary of field-value pairs to filter by
            limit: Maximum number of results to return
            offset: Offset for pagination
            jsonb_fields: List of JSONB fields to parse
            language: Language code (en, ar)

        Returns:
            list: List of records matching the criteria
        """
        logger.info(f"Called generic_search for table={table}, filters={filters}")
        try:
            # Validate table name
            if table not in self.VALID_TABLES:
                logger.error(f"Invalid table name: {table}")
                return []

            # Validate language parameter
            if language not in ["en", "ar"]:
                logger.warning(f"Invalid language '{language}', defaulting to 'en'")
                language = "en"

            # Build the base query
            query = f"SELECT * FROM {table} WHERE 1=1"
            params = []

            # Apply filters
            if filters:
                for key, value in filters.items():
                    # Handle JSONB fields
                    if jsonb_fields and key in jsonb_fields:
                        query += f" AND {key}->>'%s' ILIKE %s"
                        params.extend([language, f"%{value}%"])
                    else:
                        query += f" AND {key} = %s"
                        params.append(value)

            # Add limit and offset
            query += " LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            # Execute the query
            results = self.execute_postgres_query(query, tuple(params))

            # Parse JSON fields
            if results and jsonb_fields:
                for result in results:
                    for field in jsonb_fields:
                        self._parse_json_field(result, field)

            return results or []
        except Exception as e:
            return self._handle_error(f"generic_search_{table}", e, return_empty_list=True)

    def generic_create(self, table: str, data: Dict[str, Any]) -> Optional[int]:
        """
        Generic method to create a record.

        Args:
            table: Table name
            data: Dictionary of field-value pairs

        Returns:
            int: ID of the created record or None if creation failed
        """
        logger.info(f"Called generic_create for table={table}")
        try:
            # Validate table name
            if table not in self.VALID_TABLES:
                logger.error(f"Invalid table name: {table}")
                return None

            # Extract fields and values
            fields = list(data.keys())
            placeholders = ["%s"] * len(fields)
            values = [data[field] for field in fields]

            # Build the query
            fields_str = ", ".join(fields)
            placeholders_str = ", ".join(placeholders)
            sql = f"INSERT INTO {table} ({fields_str}) VALUES ({placeholders_str}) RETURNING id"

            # Execute the query
            result = self.execute_postgres_query(sql, tuple(values), fetchall=False)

            if result and "id" in result:
                return result["id"]
            return None
        except Exception as e:
            return self._handle_error(f"generic_create_{table}", e)

    def generic_update(self, table: str, record_id: int, data: Dict[str, Any]) -> bool:
        """
        Generic method to update a record.

        Args:
            table: Table name
            record_id: ID of the record to update
            data: Dictionary of field-value pairs to update

        Returns:
            bool: True if update was successful, False otherwise
        """
        logger.info(f"Called generic_update for table={table}, id={record_id}")
        try:
            # Validate table name
            if table not in self.VALID_TABLES:
                logger.error(f"Invalid table name: {table}")
                return False

            # Extract fields and values
            fields = list(data.keys())
            set_clauses = [f"{field} = %s" for field in fields]
            values = [data[field] for field in fields]

            # Add the ID to the values
            values.append(record_id)

            # Build the query
            set_str = ", ".join(set_clauses)
            sql = f"UPDATE {table} SET {set_str} WHERE id = %s"

            # Execute the query
            result = self.execute_postgres_query(sql, tuple(values))

            return result is not None
        except Exception as e:
            logger.error(f"Error in generic_update_{table}_{record_id}: {str(e)}")
            return False

    def generic_delete(self, table: str, record_id: int) -> bool:
        """
        Generic method to delete a record.

        Args:
            table: Table name
            record_id: ID of the record to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        logger.info(f"Called generic_delete for table={table}, id={record_id}")
        try:
            # Validate table name
            if table not in self.VALID_TABLES:
                logger.error(f"Invalid table name: {table}")
                return False

            # Build the query
            sql = f"DELETE FROM {table} WHERE id = %s"

            # Execute the query
            result = self.execute_postgres_query(sql, (record_id,))

            return result is not None
        except Exception as e:
            logger.error(f"Error in generic_delete_{table}_{record_id}: {str(e)}")
            return False

    def _get_vector_search_service(self):
        """
        Get or initialize the vector search service.

        Returns:
            The vector search service instance
        """
        if not hasattr(self, '_vector_search_service'):
            from src.services.vector_search_service import VectorSearchService
            self._vector_search_service = VectorSearchService(self)
            logger.info("Initialized Vector Search Service")
        return self._vector_search_service

    def update_geospatial_columns(self, tables: List[str] = None) -> bool:
        """
        Update geospatial columns for the specified tables.

        Args:
            tables: List of table names to update. If None, all tables with lat/long will be updated.

        Returns:
            bool: True if successful, False otherwise
        """
        default_tables = ['attractions', 'restaurants', 'accommodations']
        tables_to_update = tables if tables is not None else default_tables

        try:
            # Check if PostGIS is enabled
            if not self._check_postgis_enabled():
                logger.warning("PostGIS is not enabled, cannot update geospatial columns")
                return False

            for table in tables_to_update:
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
            return self._handle_error(f"update_geospatial_columns", e, return_empty_list=False)

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
        default_tables = ['attractions', 'restaurants', 'accommodations', 'cities', 'regions']
        tables_to_update = tables if tables is not None else default_tables

        try:
            # Check if pgvector is enabled
            if not self._check_vector_enabled():
                logger.warning("pgvector extension is not enabled, cannot update vector columns")
                return False

            for table in tables_to_update:
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
            return self._handle_error("update_vector_columns", e, return_empty_list=False)

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
                    required_fields = ['id', 'name']
                    for field in required_fields:
                        if field not in attraction:
                            raise ValueError(f"Missing required field: {field}")

                    # Ensure name is a JSONB object
                    if 'name' in attraction and not isinstance(attraction['name'], dict):
                        try:
                            attraction['name'] = json.loads(attraction['name'])
                        except (json.JSONDecodeError, TypeError):
                            # If it's not valid JSON, create a simple object with the value as both en and ar
                            attraction['name'] = {
                                "en": str(attraction['name']),
                                "ar": str(attraction['name'])
                            }

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
                        if key == 'location' and isinstance(value, dict):
                            # Extract coordinates from location object
                            lat = value.get('lat', value.get('latitude'))
                            lng = value.get('lng', value.get('longitude'))

                            if lat is not None and lng is not None:
                                # We'll set geom directly using PostGIS
                                fields.append('geom')
                                values.append(f"ST_SetSRID(ST_MakePoint({lng}, {lat}), 4326)")
                                placeholders.append('ST_SetSRID(ST_MakePoint(%s, %s), 4326)')
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
                lat = updates['location'].get('lat', updates['location'].get('latitude'))
                lng = updates['location'].get('lng', updates['location'].get('longitude'))

                if lat is not None and lng is not None:
                    # Set geom directly using PostGIS
                    updates['geom'] = f"ST_SetSRID(ST_MakePoint({lng}, {lat}), 4326)"

                del updates['location']

            # Build SET clause
            set_clauses = []
            values = []

            for key, value in updates.items():
                if key == 'geom' and isinstance(value, str) and value.startswith('ST_SetSRID'):
                    # Handle PostGIS function directly
                    set_clauses.append(f"{key} = {value}")
                else:
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

    def get_itinerary(self, itinerary_id: int) -> Optional[Dict[str, Any]]:
        """
        Get itinerary by ID with related entities from junction tables.

        Args:
            itinerary_id: ID of the itinerary to retrieve

        Returns:
            dict: Itinerary data with related entities or None if not found
        """
        logger.info(f"Called get_itinerary for ID: {itinerary_id}")
        try:
            # Check cache first
            cached_result = self.query_cache.get_record("itineraries", itinerary_id)
            if cached_result is not None:
                logger.info(f"Cache hit for itinerary {itinerary_id}")
                return cached_result

            # Cache miss, get from database
            logger.info(f"Cache miss for itinerary {itinerary_id}, fetching from database")

            # Get the base itinerary data
            sql = """
                SELECT id, type_id, name, description, duration_days,
                       daily_plans, budget_range, best_seasons, difficulty_level,
                       target_audience, highlights, practical_tips, tags, is_featured,
                       created_at, updated_at
                FROM itineraries
                WHERE id = %s
            """
            result = self.execute_postgres_query(sql, (itinerary_id,), fetchall=False)

            if not result:
                logger.warning(f"Itinerary {itinerary_id} not found")
                return None

            # Parse JSON fields
            json_fields = ['name', 'description', 'daily_plans', 'budget_range',
                          'target_audience', 'highlights', 'practical_tips']
            for field in json_fields:
                self._parse_json_field(result, field)

            # Get cities from junction table
            cities_sql = """
                SELECT c.id, c.name, ic.order_index, ic.stay_duration
                FROM itinerary_cities ic
                JOIN cities c ON ic.city_id = c.id
                WHERE ic.itinerary_id = %s
                ORDER BY ic.order_index
            """
            cities = self.execute_postgres_query(cities_sql, (itinerary_id,))

            # Format cities data
            formatted_cities = []
            if cities:
                for city in cities:
                    if 'name' in city and isinstance(city['name'], str):
                        try:
                            city['name'] = json.loads(city['name'])
                        except json.JSONDecodeError:
                            pass
                    formatted_cities.append(city)

            result['cities'] = formatted_cities

            # Get attractions from junction table
            attractions_sql = """
                SELECT a.id, a.name, ia.order_index, ia.day_number
                FROM itinerary_attractions ia
                JOIN attractions a ON ia.attraction_id = a.id
                WHERE ia.itinerary_id = %s
                ORDER BY ia.day_number, ia.order_index
            """
            attractions = self.execute_postgres_query(attractions_sql, (itinerary_id,))

            # Format attractions data
            formatted_attractions = []
            if attractions:
                for attraction in attractions:
                    if 'name' in attraction and isinstance(attraction['name'], str):
                        try:
                            attraction['name'] = json.loads(attraction['name'])
                        except json.JSONDecodeError:
                            pass
                    formatted_attractions.append(attraction)

            result['attractions'] = formatted_attractions

            # Cache the result
            self.query_cache.set_record("itineraries", itinerary_id, result)

            return result
        except Exception as e:
            return self._handle_error(f"get_itinerary_{itinerary_id}", e)

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

            # Set ef_search parameter for HNSW index
            set_ef_search = "SET hnsw.ef_search = 100;"

            # Compute hybrid search SQL - combines vector distance with text similarity
            # Includes both languages in the text search for better coverage
            main_sql = f"""
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

            # Combine the SET command with the main query
            sql = f"{set_ef_search} {main_sql}"

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
        Ensures that the proper vector index is created for a vector column to optimize search performance.

        Args:
            table_name: Name of the table containing the vector column
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

    def _update_geospatial_point(self, table: str, record_id: int, latitude: float, longitude: float) -> bool:
        """
        Update the geospatial point for a record.

        Args:
            table: Table name
            record_id: ID of the record (integer)
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

            def __exit__(self, exc_type, exc_val, _):
                """
                Exit the context manager, handling transaction commit/rollback.

                Args:
                    exc_type: Exception type if an exception was raised, None otherwise
                    exc_val: Exception value if an exception was raised, None otherwise
                    _: Exception traceback (unused)
                """
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
                        logger.info(f"Transaction rolled back due to {exc_type.__name__}: {str(exc_val)}")
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
        Convert text to a vector embedding using sentence-transformers.

        Args:
            text: Text to convert to an embedding

        Returns:
            Vector embedding as a list of floats
        """
        logger.info(f"Called text_to_embedding with text: {text[:50]}...")
        try:
            # Use sentence-transformers for real embeddings
            from sentence_transformers import SentenceTransformer

            # Lazy-load the model to avoid loading it on every import
            if not hasattr(self, '_embedding_model'):
                logger.info("Loading sentence-transformers model for the first time")
                try:
                    self._embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                    logger.info("Successfully loaded embedding model")
                except Exception as e:
                    logger.error(f"Failed to load embedding model: {str(e)}")
                    raise

            # Generate embedding
            embedding = self._embedding_model.encode(text).tolist()

            # Ensure the embedding has the correct dimension
            if len(embedding) != self.vector_dimension:
                logger.warning(f"Embedding dimension mismatch: got {len(embedding)}, expected {self.vector_dimension}")
                # Pad or truncate to match expected dimension
                if len(embedding) < self.vector_dimension:
                    embedding.extend([0.0] * (self.vector_dimension - len(embedding)))
                else:
                    embedding = embedding[:self.vector_dimension]

            return embedding
        except ImportError:
            logger.warning("sentence-transformers not installed, falling back to random embeddings")
            # Fallback to random embeddings if sentence-transformers is not available
            import numpy as np
            return np.random.randn(self.vector_dimension).astype(np.float32).tolist()
        except Exception as e:
            logger.error(f"Error generating text embedding: {str(e)}")
            # Return a zero vector as fallback
            return [0.0] * self.vector_dimension

    def get_tourism_faq(self, faq_id: int) -> Optional[Dict[str, Any]]:
        """
        Get tourism FAQ by ID.

        Args:
            faq_id (int): ID of the FAQ (integer)

        Returns:
            dict: FAQ data or None if not found
        """
        logger.info(f"Called get_tourism_faq for ID: {faq_id}")
        try:
            sql = """
                SELECT id, question, answer, category_id, created_at, updated_at
                FROM tourism_faqs
                WHERE id = %s
            """
            result = self.execute_postgres_query(sql, (faq_id,), fetchall=False)
            if result:
                # Parse JSON fields
                json_fields = ['question', 'answer']
                for field in json_fields:
                    self._parse_json_field(result, field)
                return result
            return None
        except Exception as e:
            return self._handle_error(f"get_tourism_faq_{faq_id}", e)

    def get_practical_info(self, info_id: int) -> Optional[Dict[str, Any]]:
        """
        Get practical information by ID.

        Args:
            info_id (int): ID of the practical information (integer)

        Returns:
            dict: Practical information data or None if not found
        """
        logger.info(f"Called get_practical_info for ID: {info_id}")
        try:
            sql = """
                SELECT id, title, content, category_id, created_at, updated_at
                FROM practical_info
                WHERE id = %s
            """
            result = self.execute_postgres_query(sql, (info_id,), fetchall=False)
            if result:
                # Parse JSON fields
                json_fields = ['title', 'content']
                for field in json_fields:
                    self._parse_json_field(result, field)
                return result
            return None
        except Exception as e:
            return self._handle_error(f"get_practical_info_{info_id}", e)

    def get_event_festival(self, event_id: int) -> Optional[Dict[str, Any]]:
        """
        Get event or festival by ID.

        Args:
            event_id (int): ID of the event or festival (integer)

        Returns:
            dict: Event/festival data or None if not found
        """
        logger.info(f"Called get_event_festival for ID: {event_id}")
        try:
            sql = """
                SELECT id, name, description, category_id, start_date, end_date,
                       location_description, destination_id, venue, organizer,
                       admission, schedule, highlights, historical_significance,
                       tips, website, contact_info, tags, is_featured,
                       created_at, updated_at
                FROM events_festivals
                WHERE id = %s
            """
            result = self.execute_postgres_query(sql, (event_id,), fetchall=False)
            if result:
                # Parse JSON fields
                jsonb_fields = ['name', 'description', 'location_description', 'venue',
                               'organizer', 'admission', 'schedule', 'highlights',
                               'historical_significance', 'tips', 'contact_info']
                for field in jsonb_fields:
                    self._parse_json_field(result, field)
                return result
            return None
        except Exception as e:
            return self._handle_error(f"get_event_festival_{event_id}", e)

    def get_tour_package(self, package_id: int) -> Optional[Dict[str, Any]]:
        """
        Get tour package by ID with related entities from junction tables.

        Args:
            package_id (int): ID of the tour package (integer)

        Returns:
            dict: Tour package data with related entities or None if not found
        """
        logger.info(f"Called get_tour_package for ID: {package_id}")
        try:
            # Check cache first
            cached_result = self.query_cache.get_record("tour_packages", package_id)
            if cached_result is not None:
                logger.info(f"Cache hit for tour package {package_id}")
                return cached_result

            # Cache miss, get from database
            logger.info(f"Cache miss for tour package {package_id}, fetching from database")

            # Get the base tour package data
            sql = """
                SELECT id, name, description, category_id, duration_days, price_range,
                       included_services, excluded_services, created_at, updated_at
                FROM tour_packages
                WHERE id = %s
            """
            result = self.execute_postgres_query(sql, (package_id,), fetchall=False)

            if not result:
                logger.warning(f"Tour package {package_id} not found")
                return None

            # Parse JSON fields
            json_fields = ['name', 'description', 'included_services', 'excluded_services']
            for field in json_fields:
                self._parse_json_field(result, field)

            # Get destinations from junction table
            destinations_sql = """
                SELECT d.id, d.name, tpd.order_index, tpd.stay_duration
                FROM tour_package_destinations tpd
                JOIN destinations d ON tpd.destination_id = d.id
                WHERE tpd.tour_package_id = %s
                ORDER BY tpd.order_index
            """
            destinations = self.execute_postgres_query(destinations_sql, (package_id,))

            # Format destinations data
            formatted_destinations = []
            if destinations:
                for destination in destinations:
                    if 'name' in destination and isinstance(destination['name'], str):
                        try:
                            destination['name'] = json.loads(destination['name'])
                        except json.JSONDecodeError:
                            pass
                    formatted_destinations.append(destination)

            result['destinations'] = formatted_destinations

            # Get attractions from junction table
            attractions_sql = """
                SELECT a.id, a.name, tpa.order_index, tpa.day_number
                FROM tour_package_attractions tpa
                JOIN attractions a ON tpa.attraction_id = a.id
                WHERE tpa.tour_package_id = %s
                ORDER BY tpa.day_number, tpa.order_index
            """
            attractions = self.execute_postgres_query(attractions_sql, (package_id,))

            # Format attractions data
            formatted_attractions = []
            if attractions:
                for attraction in attractions:
                    if 'name' in attraction and isinstance(attraction['name'], str):
                        try:
                            attraction['name'] = json.loads(attraction['name'])
                        except json.JSONDecodeError:
                            pass
                    formatted_attractions.append(attraction)

            result['attractions'] = formatted_attractions

            # Cache the result
            self.query_cache.set_record("tour_packages", package_id, result)

            return result
        except Exception as e:
            return self._handle_error(f"get_tour_package_{package_id}", e)

    def search_tourism_faqs(self, query: Optional[str] = None, category_id: Optional[str] = None, limit: int = 10, offset: int = 0, language: str = "en") -> List[Dict[str, Any]]:
        """
        Search tourism FAQs based on query or category.

        Args:
            query (str): Text query to search for
            category_id (str): Category ID to filter by
            limit (int): Maximum number of results to return
            offset (int): Offset for pagination
            language (str): Language code (en, ar)

        Returns:
            list of dicts: List of FAQ records matching the search criteria
        """
        logger.info(f"Called search_tourism_faqs with query={query}, category_id={category_id}, limit={limit}, offset={offset}, language={language}")
        try:
            # Validate language parameter
            if language not in ["en", "ar"]:
                logger.warning(f"Invalid language '{language}', defaulting to 'en'")
                language = "en"

            # Build the base query
            base_query = "SELECT * FROM tourism_faqs WHERE 1=1"
            params = []

            # Apply filters
            if query:
                base_query += f" AND (question->>'{language}' ILIKE %s OR answer->>'{language}' ILIKE %s)"
                query_pattern = f"%{query}%"
                params.extend([query_pattern, query_pattern])

            if category_id:
                base_query += " AND category_id = %s"
                params.append(category_id)

            # Add limit and offset
            base_query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            # Execute the query
            results = self.execute_postgres_query(base_query, tuple(params))
            return results or []
        except Exception as e:
            return self._handle_error("search_tourism_faqs", e, return_empty_list=True)

    def search_practical_info(self, query: Optional[str] = None, category_id: Optional[str] = None, limit: int = 10, offset: int = 0, language: str = "en") -> List[Dict[str, Any]]:
        """
        Search practical information based on query or category.

        Args:
            query (str): Text query to search for
            category_id (str): Category ID to filter by
            limit (int): Maximum number of results to return
            offset (int): Offset for pagination
            language (str): Language code (en, ar)

        Returns:
            list of dicts: List of practical info records matching the search criteria
        """
        logger.info(f"Called search_practical_info with query={query}, category_id={category_id}, limit={limit}, offset={offset}, language={language}")
        try:
            # Validate language parameter
            if language not in ["en", "ar"]:
                logger.warning(f"Invalid language '{language}', defaulting to 'en'")
                language = "en"

            # Build the base query
            base_query = "SELECT * FROM practical_info WHERE 1=1"
            params = []

            # Apply filters
            if query:
                base_query += f" AND (title->>'{language}' ILIKE %s OR content->>'{language}' ILIKE %s)"
                query_pattern = f"%{query}%"
                params.extend([query_pattern, query_pattern])

            if category_id:
                base_query += " AND category_id = %s"
                params.append(category_id)

            # Add limit and offset
            base_query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            # Execute the query
            results = self.execute_postgres_query(base_query, tuple(params))
            return results or []
        except Exception as e:
            return self._handle_error("search_practical_info", e, return_empty_list=True)

    def search_events_festivals(self, query: Optional[str] = None, category_id: Optional[str] = None, destination_id: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None, limit: int = 10, offset: int = 0, language: str = "en") -> List[Dict[str, Any]]:
        """
        Search events and festivals based on various criteria.

        Args:
            query (str): Text query to search for
            category_id (str): Category ID to filter by
            destination_id (str): Destination ID to filter by
            start_date (str): Start date to filter by (YYYY-MM-DD)
            end_date (str): End date to filter by (YYYY-MM-DD)
            limit (int): Maximum number of results to return
            offset (int): Offset for pagination
            language (str): Language code (en, ar)

        Returns:
            list of dicts: List of event/festival records matching the search criteria
        """
        logger.info(f"Called search_events_festivals with query={query}, category_id={category_id}, destination_id={destination_id}, limit={limit}, offset={offset}, language={language}")
        try:
            # Validate language parameter
            if language not in ["en", "ar"]:
                logger.warning(f"Invalid language '{language}', defaulting to 'en'")
                language = "en"

            # Build the base query
            base_query = "SELECT * FROM events_festivals WHERE 1=1"
            params = []

            # Apply filters
            if query:
                base_query += f" AND (name->>'{language}' ILIKE %s OR description->>'{language}' ILIKE %s OR location_description->>'{language}' ILIKE %s)"
                query_pattern = f"%{query}%"
                params.extend([query_pattern, query_pattern, query_pattern])

            if category_id:
                base_query += " AND category_id = %s"
                params.append(category_id)

            if destination_id:
                base_query += " AND destination_id = %s"
                params.append(destination_id)

            if start_date:
                base_query += " AND start_date >= %s"
                params.append(start_date)

            if end_date:
                base_query += " AND end_date <= %s"
                params.append(end_date)

            # Add limit and offset
            base_query += " ORDER BY start_date ASC LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            # Execute the query
            results = self.execute_postgres_query(base_query, tuple(params))
            return results or []
        except Exception as e:
            return self._handle_error("search_events_festivals", e, return_empty_list=True)

    def search_tour_packages(self, query: Optional[str] = None, category_id: Optional[str] = None, min_duration: Optional[int] = None, max_duration: Optional[int] = None, limit: int = 10, offset: int = 0, language: str = "en") -> List[Dict[str, Any]]:
        """
        Search tour packages based on various criteria.

        Args:
            query (str): Text query to search for
            category_id (str): Category ID to filter by
            min_duration (int): Minimum duration in days
            max_duration (int): Maximum duration in days
            limit (int): Maximum number of results to return
            offset (int): Offset for pagination
            language (str): Language code (en, ar)

        Returns:
            list of dicts: List of tour package records matching the search criteria
        """
        logger.info(f"Called search_tour_packages with query={query}, category_id={category_id}, min_duration={min_duration}, max_duration={max_duration}, limit={limit}, offset={offset}, language={language}")
        try:
            # Validate language parameter
            if language not in ["en", "ar"]:
                logger.warning(f"Invalid language '{language}', defaulting to 'en'")
                language = "en"

            # Build the base query
            base_query = "SELECT * FROM tour_packages WHERE 1=1"
            params = []

            # Apply filters
            if query:
                base_query += f" AND (name->>'{language}' ILIKE %s OR description->>'{language}' ILIKE %s)"
                query_pattern = f"%{query}%"
                params.extend([query_pattern, query_pattern])

            if category_id:
                base_query += " AND category_id = %s"
                params.append(category_id)

            if min_duration is not None:
                base_query += " AND duration_days >= %s"
                params.append(min_duration)

            if max_duration is not None:
                base_query += " AND duration_days <= %s"
                params.append(max_duration)

            # Add limit and offset
            base_query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            # Execute the query
            results = self.execute_postgres_query(base_query, tuple(params))
            return results or []
        except Exception as e:
            return self._handle_error("search_tour_packages", e, return_empty_list=True)

    def find_related_attractions(self, attraction_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Find attractions related to a given attraction using the junction table.

        Args:
            attraction_id: ID of the attraction to find related attractions for
            limit: Maximum number of results to return

        Returns:
            List of related attraction records
        """
        logger.info(f"Called find_related_attractions for ID: {attraction_id}, limit: {limit}")
        try:
            # Query the attraction_relationships junction table
            sql = """
                SELECT a.id, a.name, a.description, a.type_id, a.city_id, a.region_id,
                       ar.relationship_type, ar.description as relationship_description
                FROM attraction_relationships ar
                JOIN attractions a ON ar.related_attraction_id = a.id
                WHERE ar.attraction_id = %s
                ORDER BY a.name->>'en'
                LIMIT %s
            """
            results = self.execute_postgres_query(sql, (attraction_id, limit))

            # Format results
            formatted_results = []
            if results:
                for result in results:
                    # Parse JSON fields
                    json_fields = ['name', 'description']
                    for field in json_fields:
                        self._parse_json_field(result, field)
                    formatted_results.append(result)

            return formatted_results
        except Exception as e:
            return self._handle_error(f"find_related_attractions_{attraction_id}", e, return_empty_list=True)

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
            # Validate table name
            if table not in self.VALID_TABLES:
                logger.warning(f"Invalid table name: {table}, defaulting to 'attractions'")
                table = "attractions"

            # Convert text to embedding
            embedding = self.text_to_embedding(query)

            # Perform vector search with the embedding
            return self.vector_search(table, embedding, filters, limit)
        except Exception as e:
            return self._handle_error("semantic_search", e, return_empty_list=True)
