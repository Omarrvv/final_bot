"""
Simple database adapter for knowledge infrastructure layer.
Provides database functionality without violating architectural layers.
"""
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class InfrastructureDatabaseService:
    """
    Simple database service for infrastructure layer.
    Avoids importing from services layer to maintain clean architecture.
    """
    
    def __init__(self, database_uri: str = None, vector_dimension: int = 1536):
        # Lazy import to avoid circular dependencies
        from src.knowledge.core.connection_manager import ConnectionManager

        self.database_uri = database_uri
        self.vector_dimension = vector_dimension

        # CRITICAL FIX: Use ConnectionManager directly and implement search methods ourselves
        # This avoids circular dependency with DatabaseManager
        self.connection_manager = ConnectionManager(database_uri)

        logger.info(f"✅ Infrastructure database service initialized with direct ConnectionManager")

    def _execute_query(self, sql: str, params: List = None) -> List[Dict]:
        """
        Execute a SQL query and return results.

        Args:
            sql: SQL query string
            params: Query parameters

        Returns:
            List of result dictionaries
        """
        try:
            conn = self.connection_manager.get_connection()
            if not conn:
                logger.error("Failed to get database connection")
                return []

            try:
                from psycopg2.extras import RealDictCursor
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(sql, params or [])
                    results = cursor.fetchall()
                    return [dict(row) for row in results] if results else []
            finally:
                self.connection_manager.return_connection(conn)

        except Exception as e:
            logger.error(f"Error executing query: {e}")
            logger.debug(f"SQL: {sql}, Params: {params}")
            return []
    
    def is_connected(self) -> bool:
        """Check if database is connected."""
        return self.connection_manager.is_connected()
    
    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            return self.connection_manager.is_connected()
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a database query."""
        return self._execute_query(query, list(params))

    def execute_postgres_query(self, query, params=None, fetchall=True, cursor_factory=None):
        """Execute PostgreSQL query."""
        # For compatibility, delegate to our _execute_query method
        return self._execute_query(query, params or [])

    def generic_get(self, table: str, record_id: int, jsonb_fields: List[str] = None) -> Optional[Dict[str, Any]]:
        """Get a record by ID."""
        try:
            sql = f"SELECT * FROM {table} WHERE id = %s"
            result = self._execute_query(sql, [record_id])
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Error in generic_get: {e}")
            return None

    def generic_search(self, table: str, filters: Dict[str, Any] = None,
                      limit: int = 10, offset: int = 0,
                      jsonb_fields: List[str] = None,
                      language: str = "en") -> List[Dict[str, Any]]:
        """Search records in a table."""
        try:
            sql = f"SELECT * FROM {table} WHERE 1=1"
            params = []

            if filters:
                if "text" in filters:
                    # Simple text search across common fields
                    sql += " AND (name->>'en' ILIKE %s OR name->>'ar' ILIKE %s OR description->>'en' ILIKE %s OR description->>'ar' ILIKE %s)"
                    search_term = f"%{filters['text']}%"
                    params.extend([search_term, search_term, search_term, search_term])

            sql += f" LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            return self._execute_query(sql, params)
        except Exception as e:
            logger.error(f"Error in generic_search: {e}")
            return []

    def generic_create(self, table: str, data: Dict[str, Any]) -> Optional[int]:
        """Create a new record."""
        # Simplified implementation - not fully implemented for this fix
        logger.warning("generic_create not fully implemented in simplified adapter")
        return None

    def generic_update(self, table: str, record_id: int, data: Dict[str, Any]) -> bool:
        """Update a record."""
        # Simplified implementation - not fully implemented for this fix
        logger.warning("generic_update not fully implemented in simplified adapter")
        return False

    def generic_delete(self, table: str, record_id: int) -> bool:
        """Delete a record."""
        # Simplified implementation - not fully implemented for this fix
        logger.warning("generic_delete not fully implemented in simplified adapter")
        return False

    # ========================================================================
    # CRITICAL FIX: Missing Search Methods for Issue #2
    # ========================================================================

    def search_attractions(self, query: str = "", filters: Dict = None,
                          limit: int = 10, offset: int = 0, language: str = "en") -> List[Dict]:
        """
        Search attractions with direct SQL implementation.

        Args:
            query: Text query string for searching attractions
            filters: Additional filters to apply
            language: Language code (en, ar)
            limit: Maximum number of results

        Returns:
            List of attraction records matching the criteria
        """
        try:
            # Build SQL query
            sql = "SELECT * FROM attractions WHERE 1=1"
            params = []

            # Add text search if query provided - FIXED: Better JSONB handling
            if query and isinstance(query, str) and query.strip():
                search_term = f"%{query.strip().lower()}%"
                sql += """ AND (
                    LOWER(name->>'en') ILIKE %s OR
                    LOWER(name->>'ar') ILIKE %s OR
                    LOWER(description->>'en') ILIKE %s OR
                    LOWER(description->>'ar') ILIKE %s OR
                    LOWER(name::text) ILIKE %s OR
                    LOWER(description::text) ILIKE %s
                )"""
                params.extend([search_term, search_term, search_term, search_term, search_term, search_term])

            # Add filters
            if filters:
                if "city" in filters:
                    sql += " AND city_id = (SELECT id FROM cities WHERE name->>'en' ILIKE %s OR name->>'ar' ILIKE %s LIMIT 1)"
                    params.extend([f"%{filters['city']}%", f"%{filters['city']}%"])

                if "region" in filters:
                    sql += " AND region_id = (SELECT id FROM regions WHERE name->>'en' ILIKE %s OR name->>'ar' ILIKE %s LIMIT 1)"
                    params.extend([f"%{filters['region']}%", f"%{filters['region']}%"])

            # Add limit
            sql += " LIMIT %s"
            params.append(limit)

            # Execute query
            result = self._execute_query(sql, params)

            logger.debug(f"search_attractions: query='{query}', filters={filters}, results={len(result or [])}")
            return result or []

        except Exception as e:
            logger.error(f"Error searching attractions: {e}")
            return []

    def search_restaurants(self, query: Dict = None, filters: Dict = None,
                          limit: int = 10, offset: int = 0, language: str = "en") -> List[Dict]:
        """
        Search restaurants with direct SQL implementation.

        Args:
            query: Dictionary query with search parameters
            limit: Maximum number of results
            language: Language code (en, ar)

        Returns:
            List of restaurant records matching the criteria
        """
        try:
            # Build SQL query
            sql = "SELECT * FROM restaurants WHERE 1=1"
            params = []

            # Handle different query formats
            text_query = None
            if query:
                if isinstance(query, dict):
                    # Extract text query if present
                    if "text" in query:
                        text_query = query["text"]
                    # Handle other filters
                    if "city" in query:
                        sql += " AND city_id = (SELECT id FROM cities WHERE name->>'en' ILIKE %s OR name->>'ar' ILIKE %s LIMIT 1)"
                        params.extend([f"%{query['city']}%", f"%{query['city']}%"])
                    if "cuisine" in query:
                        sql += " AND cuisine_id ILIKE %s"
                        params.append(f"%{query['cuisine']}%")
                else:
                    # Convert non-dict query to text search
                    text_query = str(query)

            # Add text search if provided - FIXED: Better JSONB handling
            if text_query:
                search_term = f"%{text_query.lower()}%"
                sql += """ AND (
                    LOWER(name->>'en') ILIKE %s OR
                    LOWER(name->>'ar') ILIKE %s OR
                    LOWER(description->>'en') ILIKE %s OR
                    LOWER(description->>'ar') ILIKE %s OR
                    LOWER(name::text) ILIKE %s OR
                    LOWER(description::text) ILIKE %s
                )"""
                params.extend([search_term, search_term, search_term, search_term, search_term, search_term])

            # Add limit
            sql += " LIMIT %s"
            params.append(limit)

            # Execute query
            result = self._execute_query(sql, params)

            logger.debug(f"search_restaurants: query={query}, results={len(result or [])}")
            return result or []

        except Exception as e:
            logger.error(f"Error searching restaurants: {e}")
            return []

    def search_hotels(self, query: Dict = None, filters: Dict = None,
                     limit: int = 10, offset: int = 0, language: str = "en") -> List[Dict]:
        """
        Search hotels with direct SQL implementation.

        Args:
            query: Dictionary query with search parameters
            limit: Maximum number of results
            language: Language code (en, ar)

        Returns:
            List of hotel records matching the criteria
        """
        try:
            # Build SQL query (hotels are stored in accommodations table)
            sql = "SELECT * FROM accommodations WHERE 1=1"
            params = []

            # Handle different query formats
            text_query = None
            if query:
                if isinstance(query, dict):
                    # Extract text query if present
                    if "text" in query:
                        text_query = query["text"]
                    # Handle other filters
                    if "city" in query:
                        sql += " AND city_id = (SELECT id FROM cities WHERE name->>'en' ILIKE %s OR name->>'ar' ILIKE %s LIMIT 1)"
                        params.extend([f"%{query['city']}%", f"%{query['city']}%"])
                    if "stars" in query:
                        sql += " AND stars >= %s"
                        params.append(int(query["stars"]))
                else:
                    # Convert non-dict query to text search
                    text_query = str(query)

            # Add text search if provided - FIXED: Better JSONB handling
            if text_query:
                search_term = f"%{text_query.lower()}%"
                sql += """ AND (
                    LOWER(name->>'en') ILIKE %s OR
                    LOWER(name->>'ar') ILIKE %s OR
                    LOWER(description->>'en') ILIKE %s OR
                    LOWER(description->>'ar') ILIKE %s OR
                    LOWER(name::text) ILIKE %s OR
                    LOWER(description::text) ILIKE %s
                )"""
                params.extend([search_term, search_term, search_term, search_term, search_term, search_term])

            # Add limit
            sql += " LIMIT %s"
            params.append(limit)

            # Execute query
            result = self._execute_query(sql, params)

            logger.debug(f"search_hotels: query={query}, results={len(result or [])}")
            return result or []

        except Exception as e:
            logger.error(f"Error searching hotels: {e}")
            return []

    def close(self):
        """Close database connections."""
        if hasattr(self, 'connection_manager'):
            self.connection_manager.close()
    
    def __enter__(self):
        """Enter context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        self.close()


def get_database_service(database_uri: str = None) -> InfrastructureDatabaseService:
    """Get database service instance."""
    return InfrastructureDatabaseService(database_uri) 