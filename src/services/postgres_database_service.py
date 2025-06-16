"""
PostgreSQL Database Manager

This module provides a database manager for connecting to and querying
the PostgreSQL database containing tourism information, with support for
vector embeddings and geospatial queries.
"""
import os
import json
import logging
import psycopg2
import numpy as np
from psycopg2.extras import DictCursor, execute_values
from typing import Any, Dict, List, Optional, Tuple, Union

from src.utils.logger import get_logger

logger = get_logger(__name__)


class PostgresqlDatabaseManager:
    def close(self):
        """Close the PostgreSQL connection or pool."""
        try:
            if hasattr(self, 'pg_pool') and self.pg_pool:
                self.pg_pool.closeall()
                self.pg_pool = None
                logger.info("Closed PostgreSQL connection pool.")
            if hasattr(self, 'connection') and self.connection:
                self.connection.close()
                self.connection = None
                logger.info("Closed PostgreSQL direct connection.")
        except Exception as e:
            logger.error(f"Error closing PostgreSQL connection: {e}")

    """
    Database manager for PostgreSQL access.

    This class provides methods for connecting to and querying the
    PostgreSQL database containing tourism information, with support
    for vector embeddings and geospatial queries using pgvector and postgis.
    """

    def __init__(self, database_uri: str = None):
        """
        Initialize the database manager.

        Args:
            database_uri: URI of the PostgreSQL database
        """
        # Use provided URI or get from environment
        self.database_uri = database_uri or os.environ.get(
            "POSTGRES_URI", "postgresql://postgres:postgres@localhost:5432/egypt_chatbot"
        )

        self.connection = None
        self.db_type = "postgresql"
        logger.info(f"PostgresqlDatabaseManager initialized with {self.db_type}")

    def connect(self) -> None:
        """
        Connect to the database.

        This method establishes a connection to the PostgreSQL database.
        """
        try:
            # Connect to the database
            self.connection = psycopg2.connect(self.database_uri)

            logger.info(f"Connected to PostgreSQL database: {self.database_uri.split('@')[1] if '@' in self.database_uri else self.database_uri}")
        except Exception as e:
            logger.error(f"Error connecting to database: {str(e)}")
            raise

    def disconnect(self) -> None:
        """
        Disconnect from the database.

        This method closes the connection to the PostgreSQL database.
        """
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Disconnected from PostgreSQL database")

    def get_connection(self) -> psycopg2.extensions.connection:
        """
        Get a database connection.

        This method returns an existing connection or creates a new one.

        Returns:
            PostgreSQL connection
        """
        if not self.connection:
            self.connect()
        return self.connection

    def execute_query(
        self, query: str, params: tuple = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a PostgreSQL query and return the results.

        Args:
            query: SQL query to execute
            params: Query parameters

        Returns:
            List of dictionaries representing the query results
        """
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                # Execute the query
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                # Fetch results
                results = [dict(row) for row in cursor.fetchall()]

                return results
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise

    def execute_update(
        self, query: str, params: tuple = None
    ) -> int:
        """
        Execute a PostgreSQL update/insert/delete and return the row count.

        Args:
            query: SQL query to execute
            params: Query parameters

        Returns:
            Number of rows affected
        """
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                # Execute the query
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                # Commit the changes
                conn.commit()

                # Return row count
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Error executing update: {str(e)}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            conn.rollback()
            raise

    def get_attraction_by_id(self, attraction_id: int) -> Optional[Dict[str, Any]]:
        """
        Get an attraction by its ID.

        Args:
            attraction_id: Attraction ID (integer)

        Returns:
            Attraction data as a dictionary, or None if not found
        """
        logger.info(f"POSTGRES DB Manager: get_attraction_by_id called for ID: {attraction_id}")
        # Log the SQL query it's about to run
        query = "SELECT * FROM attractions WHERE id = %s" # Replicate the query string used
        logger.info(f"POSTGRES DB Manager: Executing SQL: {query} with params ({attraction_id},)")

        params = (attraction_id,)

        results = self.execute_query(query, params)

        if results:
            attraction = results[0]

            # Parse the JSON data field if it exists
            if "data" in attraction and attraction["data"]:
                try:
                    attraction["data"] = json.loads(attraction["data"])
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in attraction {attraction_id}")

            return attraction

        return None

    def search_attractions(
        self, filters: Dict[str, Any], limit: int = 10, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Search for attractions based on filters.

        Args:
            filters: Dictionary of search filters
            limit: Maximum number of results
            offset: Result offset for pagination

        Returns:
            List of attractions matching the filters
        """
        # Build the query
        query = "SELECT * FROM attractions WHERE 1=1"
        params = []

        # Add filters to the query
        if "name" in filters:
            query += " AND (name->>'en' ILIKE %s OR name->>'ar' ILIKE %s)"
            params.extend([f"%{filters['name']}%", f"%{filters['name']}%"])

        if "city_id" in filters:
            query += " AND city_id = %s"
            params.append(filters["city_id"])

        if "type" in filters:
            query += " AND type = %s"
            params.append(filters["type"])

        # Add limit and offset
        query += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        # Execute the query
        results = self.execute_query(query, tuple(params))

        # Parse JSON data fields
        for attraction in results:
            if "data" in attraction and attraction["data"]:
                try:
                    attraction["data"] = json.loads(attraction["data"])
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in attraction {attraction.get('id')}")

        return results

    def vector_search_attractions(
        self, embedding: List[float], filters: Dict[str, Any] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for attractions based on vector similarity.

        Args:
            embedding: Vector embedding to search with
            filters: Additional filters to apply
            limit: Maximum number of results

        Returns:
            List of attractions ordered by similarity
        """
        # Build the query
        query = """
            SELECT *, embedding <-> %s::vector AS distance
            FROM attractions
            WHERE embedding IS NOT NULL
        """
        params = [embedding]

        # Add filters to the query
        if filters:
            if "city_id" in filters:
                query += " AND city_id = %s"
                params.append(filters["city_id"])

            if "type" in filters:
                query += " AND type = %s"
                params.append(filters["type"])

        # Add order by and limit
        query += " ORDER BY distance LIMIT %s"
        params.append(limit)

        # Execute the query
        results = self.execute_query(query, tuple(params))

        # Parse JSON data fields
        for attraction in results:
            if "data" in attraction and attraction["data"]:
                try:
                    attraction["data"] = json.loads(attraction["data"])
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in attraction {attraction.get('id')}")

        return results

    def update_attraction_embedding(
        self, attraction_id: int, embedding: List[float]
    ) -> bool:
        """
        Update the embedding for an attraction.

        Args:
            attraction_id: ID of the attraction (integer)
            embedding: Vector embedding

        Returns:
            True if successful, False otherwise
        """
        try:
            query = """
                UPDATE attractions
                SET embedding = %s::vector
                WHERE id = %s
            """
            params = (embedding, attraction_id)

            rowcount = self.execute_update(query, params)
            return rowcount > 0
        except Exception as e:
            logger.error(f"Error updating attraction embedding: {str(e)}")
            return False

    def get_city_by_id(self, city_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a city by its ID.

        Args:
            city_id: City ID (integer)

        Returns:
            City data as a dictionary, or None if not found
        """
        query = "SELECT * FROM cities WHERE id = %s"
        params = (city_id,)

        results = self.execute_query(query, params)

        if results:
            city = results[0]

            # Parse the JSON data field if it exists
            if "data" in city and city["data"]:
                try:
                    city["data"] = json.loads(city["data"])
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in city {city_id}")

            return city

        return None

    def search_cities(
        self, filters: Dict[str, Any], limit: int = 10, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Search for cities based on filters.

        Args:
            filters: Dictionary of search filters
            limit: Maximum number of results
            offset: Result offset for pagination

        Returns:
            List of cities matching the filters
        """
        # Build the query
        query = "SELECT * FROM cities WHERE 1=1"
        params = []

        # Add filters to the query
        if "name" in filters:
            query += " AND (name->>'en' ILIKE %s OR name->>'ar' ILIKE %s)"
            params.extend([f"%{filters['name']}%", f"%{filters['name']}%"])

        # Add limit and offset
        query += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        # Execute the query
        results = self.execute_query(query, tuple(params))

        # Parse JSON data fields
        for city in results:
            if "data" in city and city["data"]:
                try:
                    city["data"] = json.loads(city["data"])
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in city {city.get('id')}")

        return results

    def vector_search_cities(
        self, embedding: List[float], filters: Dict[str, Any] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for cities based on vector similarity.

        Args:
            embedding: Vector embedding to search with
            filters: Additional filters to apply
            limit: Maximum number of results

        Returns:
            List of cities ordered by similarity
        """
        # Build the query
        query = """
            SELECT *, embedding <-> %s::vector AS distance
            FROM cities
            WHERE embedding IS NOT NULL
        """
        params = [embedding]

        # Add filters to the query
        if filters and "name" in filters:
            query += " AND (name->>'en' ILIKE %s OR name->>'ar' ILIKE %s)"
            params.extend([f"%{filters['name']}%", f"%{filters['name']}%"])

        # Add order by and limit
        query += " ORDER BY distance LIMIT %s"
        params.append(limit)

        # Execute the query
        results = self.execute_query(query, tuple(params))

        # Parse JSON data fields
        for city in results:
            if "data" in city and city["data"]:
                try:
                    city["data"] = json.loads(city["data"])
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in city {city.get('id')}")

        return results

    def update_city_embedding(
        self, city_id: int, embedding: List[float]
    ) -> bool:
        """
        Update the embedding for a city.

        Args:
            city_id: ID of the city (integer)
            embedding: Vector embedding

        Returns:
            True if successful, False otherwise
        """
        try:
            query = """
                UPDATE cities
                SET embedding = %s::vector
                WHERE id = %s
            """
            params = (embedding, city_id)

            rowcount = self.execute_update(query, params)
            return rowcount > 0
        except Exception as e:
            logger.error(f"Error updating city embedding: {str(e)}")
            return False

    def get_hotel_by_id(self, hotel_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a hotel by its ID.

        Args:
            hotel_id: Hotel ID (integer)

        Returns:
            Hotel data as a dictionary, or None if not found
        """
        query = "SELECT * FROM hotels WHERE id = %s"
        params = (hotel_id,)

        results = self.execute_query(query, params)

        if results:
            hotel = results[0]

            # Parse the JSON data field if it exists
            if "data" in hotel and hotel["data"]:
                try:
                    hotel["data"] = json.loads(hotel["data"])
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in hotel {hotel_id}")

            return hotel

        return None

    def search_hotels(
        self, filters: Dict[str, Any], limit: int = 10, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Search for hotels based on filters.

        Args:
            filters: Dictionary of search filters
            limit: Maximum number of results
            offset: Result offset for pagination

        Returns:
            List of hotels matching the filters
        """
        # Build the query
        query = "SELECT * FROM hotels WHERE 1=1"
        params = []

        # Add filters to the query
        if "name" in filters:
            query += " AND (name->>'en' ILIKE %s OR name->>'ar' ILIKE %s)"
            params.extend([f"%{filters['name']}%", f"%{filters['name']}%"])

        if "city_id" in filters:
            query += " AND city_id = %s"
            params.append(filters["city_id"])

        if "stars" in filters:
            query += " AND stars >= %s"
            params.append(filters["stars"])

        # Add limit and offset
        query += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        # Execute the query
        results = self.execute_query(query, tuple(params))

        # Parse JSON data fields
        for hotel in results:
            if "data" in hotel and hotel["data"]:
                try:
                    hotel["data"] = json.loads(hotel["data"])
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in hotel {hotel.get('id')}")

        return results

    def vector_search_hotels(
        self, embedding: List[float], filters: Dict[str, Any] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for hotels based on vector similarity.

        Args:
            embedding: Vector embedding to search with
            filters: Additional filters to apply
            limit: Maximum number of results

        Returns:
            List of hotels ordered by similarity
        """
        # Build the query
        query = """
            SELECT *, embedding <-> %s::vector AS distance
            FROM hotels
            WHERE embedding IS NOT NULL
        """
        params = [embedding]

        # Add filters to the query
        if filters:
            if "city_id" in filters:
                query += " AND city_id = %s"
                params.append(filters["city_id"])

            if "stars" in filters:
                query += " AND stars >= %s"
                params.append(filters["stars"])

        # Add order by and limit
        query += " ORDER BY distance LIMIT %s"
        params.append(limit)

        # Execute the query
        results = self.execute_query(query, tuple(params))

        # Parse JSON data fields
        for hotel in results:
            if "data" in hotel and hotel["data"]:
                try:
                    hotel["data"] = json.loads(hotel["data"])
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in hotel {hotel.get('id')}")

        return results

    def update_hotel_embedding(
        self, hotel_id: str, embedding: List[float]
    ) -> bool:
        """
        Update the embedding for a hotel.

        Args:
            hotel_id: ID of the hotel
            embedding: Vector embedding

        Returns:
            True if successful, False otherwise
        """
        try:
            query = """
                UPDATE hotels
                SET embedding = %s::vector
                WHERE id = %s
            """
            params = (embedding, hotel_id)

            rowcount = self.execute_update(query, params)
            return rowcount > 0
        except Exception as e:
            logger.error(f"Error updating hotel embedding: {str(e)}")
            return False

    def get_restaurant_by_id(self, restaurant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a restaurant by its ID.

        Args:
            restaurant_id: Restaurant ID

        Returns:
            Restaurant data as a dictionary, or None if not found
        """
        query = "SELECT * FROM restaurants WHERE id = %s"
        params = (restaurant_id,)

        results = self.execute_query(query, params)

        if results:
            restaurant = results[0]

            # Parse the JSON data field if it exists
            if "data" in restaurant and restaurant["data"]:
                try:
                    restaurant["data"] = json.loads(restaurant["data"])
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in restaurant {restaurant_id}")

            return restaurant

        return None

    def search_restaurants(
        self, filters: Dict[str, Any], limit: int = 10, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Search for restaurants based on filters.

        Args:
            filters: Dictionary of search filters
            limit: Maximum number of results
            offset: Result offset for pagination

        Returns:
            List of restaurants matching the filters
        """
        # Build the query
        query = "SELECT * FROM restaurants WHERE 1=1"
        params = []

        # Add filters to the query
        if "name" in filters:
            query += " AND (name->>'en' ILIKE %s OR name->>'ar' ILIKE %s)"
            params.extend([f"%{filters['name']}%", f"%{filters['name']}%"])

        if "city_id" in filters:
            query += " AND city_id = %s"
            params.append(filters["city_id"])

        if "cuisine" in filters:
            query += " AND cuisine ILIKE %s"
            params.append(f"%{filters['cuisine']}%")

        # Add limit and offset
        query += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        # Execute the query
        results = self.execute_query(query, tuple(params))

        # Parse JSON data fields
        for restaurant in results:
            if "data" in restaurant and restaurant["data"]:
                try:
                    restaurant["data"] = json.loads(restaurant["data"])
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in restaurant {restaurant.get('id')}")

        return results

    def vector_search_restaurants(
        self, embedding: List[float], filters: Dict[str, Any] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for restaurants based on vector similarity.

        Args:
            embedding: Vector embedding to search with
            filters: Additional filters to apply
            limit: Maximum number of results

        Returns:
            List of restaurants ordered by similarity
        """
        # Build the query
        query = """
            SELECT *, embedding <-> %s::vector AS distance
            FROM restaurants
            WHERE embedding IS NOT NULL
        """
        params = [embedding]

        # Add filters to the query
        if filters:
            if "city_id" in filters:
                query += " AND city_id = %s"
                params.append(filters["city_id"])

            if "cuisine" in filters:
                query += " AND cuisine ILIKE %s"
                params.append(f"%{filters['cuisine']}%")

        # Add order by and limit
        query += " ORDER BY distance LIMIT %s"
        params.append(limit)

        # Execute the query
        results = self.execute_query(query, tuple(params))

        # Parse JSON data fields
        for restaurant in results:
            if "data" in restaurant and restaurant["data"]:
                try:
                    restaurant["data"] = json.loads(restaurant["data"])
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in restaurant {restaurant.get('id')}")

        return results

    def update_restaurant_embedding(
        self, restaurant_id: str, embedding: List[float]
    ) -> bool:
        """
        Update the embedding for a restaurant.

        Args:
            restaurant_id: ID of the restaurant
            embedding: Vector embedding

        Returns:
            True if successful, False otherwise
        """
        try:
            query = """
                UPDATE restaurants
                SET embedding = %s::vector
                WHERE id = %s
            """
            params = (embedding, restaurant_id)

            rowcount = self.execute_update(query, params)
            return rowcount > 0
        except Exception as e:
            logger.error(f"Error updating restaurant embedding: {str(e)}")
            return False

    def search_nearby(
        self, latitude: float, longitude: float,
        table: str, radius_km: float = 5.0,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for locations near the given coordinates.

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            table: Table to search in (attractions, hotels, restaurants, cities)
            radius_km: Search radius in kilometers
            limit: Maximum number of results

        Returns:
            List of locations within the radius, ordered by distance
        """
        try:
            # Create a point from the coordinates
            query = f"""
                SELECT *,
                       ST_Distance(
                           location,
                           ST_SetSRID(ST_Point(%s, %s), 4326)::geography
                       ) as distance
                FROM {table}
                WHERE location IS NOT NULL
                AND ST_DWithin(
                    location,
                    ST_SetSRID(ST_Point(%s, %s), 4326)::geography,
                    %s * 1000
                )
                ORDER BY distance
                LIMIT %s
            """
            params = (longitude, latitude, longitude, latitude, radius_km, limit)

            results = self.execute_query(query, params)

            # Parse JSON data fields
            for item in results:
                if "data" in item and item["data"]:
                    try:
                        item["data"] = json.loads(item["data"])
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON in {table} {item.get('id')}")

            return results
        except Exception as e:
            logger.error(f"Error searching nearby locations: {str(e)}")
            return []

    # Implement additional methods similar to SQLite DatabaseManager for practical_info,
    # analytics_events, and user management, but with PostgreSQL-specific syntax

    # Add combined search method that leverages both vector and text search
    def hybrid_search(
        self, table: str, text_query: str = None, embedding: List[float] = None,
        filters: Dict[str, Any] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Perform a hybrid search using both vector similarity and text search.

        Args:
            table: Table to search in (attractions, hotels, restaurants, cities)
            text_query: Text query for full-text search
            embedding: Vector embedding for similarity search
            filters: Additional filters to apply
            limit: Maximum number of results

        Returns:
            List of results ranked by a combination of text and vector relevance
        """
        if not text_query and not embedding:
            logger.error("Either text_query or embedding must be provided for hybrid_search")
            return []

        try:
            # Start building the query
            query_parts = [f"SELECT * FROM {table} WHERE 1=1"]
            params = []

            # Add vector search component if embedding provided
            if embedding:
                query_parts[0] = f"SELECT *, embedding <-> %s::vector AS vector_distance FROM {table} WHERE embedding IS NOT NULL"
                params.append(embedding)

            # Add text search component if text_query provided
            if text_query:
                if table == "attractions":
                    query_parts.append("AND (name->>'en' ILIKE %s OR name->>'ar' ILIKE %s OR description_en ILIKE %s OR description_ar ILIKE %s)")
                    text_param = f"%{text_query}%"
                    params.extend([text_param, text_param, text_param, text_param])
                elif table == "cities":
                    query_parts.append("AND (name->>'en' ILIKE %s OR name->>'ar' ILIKE %s OR description_en ILIKE %s OR description_ar ILIKE %s)")
                    text_param = f"%{text_query}%"
                    params.extend([text_param, text_param, text_param, text_param])
                elif table == "hotels":
                    query_parts.append("AND (name->>'en' ILIKE %s OR name->>'ar' ILIKE %s OR description_en ILIKE %s OR description_ar ILIKE %s)")
                    text_param = f"%{text_query}%"
                    params.extend([text_param, text_param, text_param, text_param])
                elif table == "restaurants":
                    query_parts.append("AND (name->>'en' ILIKE %s OR name->>'ar' ILIKE %s OR description_en ILIKE %s OR description_ar ILIKE %s OR cuisine ILIKE %s)")
                    text_param = f"%{text_query}%"
                    params.extend([text_param, text_param, text_param, text_param, text_param])

            # Add any additional filters
            if filters:
                if "city_id" in filters:
                    query_parts.append("AND city_id = %s")
                    params.append(filters["city_id"])

                if "type" in filters and table == "attractions":
                    query_parts.append("AND type = %s")
                    params.append(filters["type"])

                if "stars" in filters and table == "hotels":
                    query_parts.append("AND stars >= %s")
                    params.append(filters["stars"])

                if "cuisine" in filters and table == "restaurants":
                    query_parts.append("AND cuisine ILIKE %s")
                    params.append(f"%{filters['cuisine']}%")

            # Add sorting and limit
            if embedding:
                query_parts.append("ORDER BY vector_distance LIMIT %s")
            else:
                query_parts.append("ORDER BY id LIMIT %s")
            params.append(limit)

            # Execute query
            final_query = " ".join(query_parts)
            results = self.execute_query(final_query, tuple(params))

            # Parse JSON data fields
            for item in results:
                if "data" in item and item["data"]:
                    try:
                        item["data"] = json.loads(item["data"])
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON in {table} {item.get('id')}")

            return results
        except Exception as e:
            logger.error(f"Error performing hybrid search: {str(e)}")
            return []

    def test_connection(self) -> bool:
        """Test database connection and verify it's working properly."""
        try:
            if not self.connection:
                self.connect()

            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1 as test")
                result = cursor.fetchone()
                return result[0] == 1

        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False