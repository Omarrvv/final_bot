"""
Integration tests for the database manager.

This module contains integration tests for the database manager,
testing interactions between components and with the database.
"""
import json
import time
import pytest
from typing import Dict, List, Any, Optional

from src.knowledge.database import DatabaseManager
from src.utils.query_cache import QueryCache
from src.utils.query_analyzer import QueryAnalyzer
from src.utils.query_batch import QueryBatch

class TestDatabaseIntegration:
    """Integration tests for the database manager."""

    @pytest.fixture
    def db_manager(self):
        """Create a database manager for testing."""
        # Use the test database
        db_manager = DatabaseManager(
            database_uri="postgresql://postgres:postgres@localhost:5432/egypt_chatbot"
        )

        # Ensure we're connected
        if not db_manager.is_connected():
            db_manager.connect()

        # Create test tables and data
        self._setup_test_data(db_manager)

        yield db_manager

        # Clean up test data
        self._cleanup_test_data(db_manager)

        # Close connections
        db_manager.close()

    def _setup_test_data(self, db_manager):
        """Set up test data for integration tests."""
        # Create test tables if they don't exist
        with db_manager.transaction() as cursor:
            # Create test_attractions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_attractions (
                    id TEXT PRIMARY KEY,
                    name JSONB,
                    description JSONB,
                    type_id TEXT,
                    city_id TEXT,
                    region_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create test_restaurants table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_restaurants (
                    id TEXT PRIMARY KEY,
                    name JSONB,
                    description JSONB,
                    cuisine_id TEXT,
                    city_id TEXT,
                    region_id TEXT,
                    price_range TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

        # Insert test data
        with db_manager.transaction() as cursor:
            # Clear existing test data
            cursor.execute("DELETE FROM test_attractions")
            cursor.execute("DELETE FROM test_restaurants")

            # Insert test attractions
            for i in range(10):
                cursor.execute(
                    """
                    INSERT INTO test_attractions (id, name, description, type_id, city_id, region_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        f"test_attraction_{i}",
                        json.dumps({"en": f"Test Attraction {i}", "ar": f"معلم اختبار {i}"}),
                        json.dumps({"en": f"Description for Test Attraction {i}", "ar": f"وصف لمعلم اختبار {i}"}),
                        "museum" if i % 3 == 0 else "historical" if i % 3 == 1 else "natural",
                        "cairo" if i % 2 == 0 else "luxor",
                        "cairo" if i % 2 == 0 else "upper_egypt"
                    )
                )

            # Insert test restaurants
            for i in range(10):
                cursor.execute(
                    """
                    INSERT INTO test_restaurants (id, name, description, cuisine_id, city_id, region_id, price_range)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        f"test_restaurant_{i}",
                        json.dumps({"en": f"Test Restaurant {i}", "ar": f"مطعم اختبار {i}"}),
                        json.dumps({"en": f"Description for Test Restaurant {i}", "ar": f"وصف لمطعم اختبار {i}"}),
                        "egyptian" if i % 3 == 0 else "seafood" if i % 3 == 1 else "international",
                        "cairo" if i % 2 == 0 else "alexandria",
                        "cairo" if i % 2 == 0 else "north_coast",
                        "budget" if i % 3 == 0 else "moderate" if i % 3 == 1 else "luxury"
                    )
                )

    def _cleanup_test_data(self, db_manager):
        """Clean up test data after integration tests."""
        with db_manager.transaction() as cursor:
            # Clear test data
            cursor.execute("DELETE FROM test_attractions")
            cursor.execute("DELETE FROM test_restaurants")

    def test_connection(self, db_manager):
        """Test database connection."""
        assert db_manager.is_connected()

    def test_generic_get(self, db_manager):
        """Test generic_get method."""
        # Get a test attraction
        attraction = db_manager.generic_get("test_attractions", "test_attraction_0")

        # Verify the result
        assert attraction is not None
        assert attraction["id"] == "test_attraction_0"
        assert json.loads(attraction["name"])["en"] == "Test Attraction 0"
        assert json.loads(attraction["description"])["en"] == "Description for Test Attraction 0"
        assert attraction["type_id"] == "museum"
        assert attraction["city_id"] == "cairo"
        assert attraction["region_id"] == "cairo"

    def test_generic_search(self, db_manager):
        """Test generic_search method."""
        # Search for museums in Cairo
        attractions = db_manager.generic_search(
            "test_attractions",
            filters={"type_id": "museum", "city_id": "cairo"},
            limit=10
        )

        # Verify the results
        assert len(attractions) > 0
        for attraction in attractions:
            assert attraction["type_id"] == "museum"
            assert attraction["city_id"] == "cairo"

    def test_generic_create_update_delete(self, db_manager):
        """Test generic_create, generic_update, and generic_delete methods."""
        # Create a new attraction
        attraction_id = "test_attraction_new"
        created = db_manager.generic_create(
            "test_attractions",
            {
                "id": attraction_id,
                "name": {"en": "New Test Attraction", "ar": "معلم اختبار جديد"},
                "description": {"en": "Description for New Test Attraction", "ar": "وصف لمعلم اختبار جديد"},
                "type_id": "museum",
                "city_id": "cairo",
                "region_id": "cairo"
            }
        )

        # Verify creation
        assert created is not None

        # Get the created attraction
        attraction = db_manager.generic_get("test_attractions", attraction_id)

        # Verify the result
        assert attraction is not None
        assert attraction["id"] == attraction_id
        assert json.loads(attraction["name"])["en"] == "New Test Attraction"

        # Update the attraction
        updated = db_manager.generic_update(
            "test_attractions",
            attraction_id,
            {
                "name": {"en": "Updated Test Attraction", "ar": "معلم اختبار محدث"},
                "type_id": "historical"
            }
        )

        # Verify update
        assert updated is True

        # Get the updated attraction
        attraction = db_manager.generic_get("test_attractions", attraction_id)

        # Verify the result
        assert attraction is not None
        assert json.loads(attraction["name"])["en"] == "Updated Test Attraction"
        assert attraction["type_id"] == "historical"

        # Delete the attraction
        deleted = db_manager.generic_delete("test_attractions", attraction_id)

        # Verify deletion
        assert deleted is True

        # Try to get the deleted attraction
        attraction = db_manager.generic_get("test_attractions", attraction_id)

        # Verify the result
        assert attraction is None

    def test_transaction(self, db_manager):
        """Test transaction context manager."""
        # Start a transaction
        with db_manager.transaction() as cursor:
            # Insert a new attraction
            cursor.execute(
                """
                INSERT INTO test_attractions (id, name, description, type_id, city_id, region_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    "test_attraction_transaction",
                    json.dumps({"en": "Transaction Test Attraction", "ar": "معلم اختبار المعاملة"}),
                    json.dumps({"en": "Description for Transaction Test Attraction", "ar": "وصف لمعلم اختبار المعاملة"}),
                    "museum",
                    "cairo",
                    "cairo"
                )
            )

            # Insert a related record
            cursor.execute(
                """
                INSERT INTO test_restaurants (id, name, description, cuisine_id, city_id, region_id, price_range)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    "test_restaurant_transaction",
                    json.dumps({"en": "Transaction Test Restaurant", "ar": "مطعم اختبار المعاملة"}),
                    json.dumps({"en": "Description for Transaction Test Restaurant", "ar": "وصف لمطعم اختبار المعاملة"}),
                    "egyptian",
                    "cairo",
                    "cairo",
                    "moderate"
                )
            )

        # Verify that both records were inserted
        attraction = db_manager.generic_get("test_attractions", "test_attraction_transaction")
        restaurant = db_manager.generic_get("test_restaurants", "test_restaurant_transaction")

        assert attraction is not None
        assert restaurant is not None

    def test_transaction_rollback(self, db_manager):
        """Test transaction rollback."""
        try:
            # Start a transaction that will fail
            with db_manager.transaction() as cursor:
                # Insert a new attraction
                cursor.execute(
                    """
                    INSERT INTO test_attractions (id, name, description, type_id, city_id, region_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        "test_attraction_rollback",
                        json.dumps({"en": "Rollback Test Attraction", "ar": "معلم اختبار التراجع"}),
                        json.dumps({"en": "Description for Rollback Test Attraction", "ar": "وصف لمعلم اختبار التراجع"}),
                        "museum",
                        "cairo",
                        "cairo"
                    )
                )

                # Execute an invalid query to trigger a rollback
                cursor.execute("SELECT * FROM non_existent_table")
        except:
            # Exception should be raised
            pass

        # Verify that the attraction was not inserted
        attraction = db_manager.generic_get("test_attractions", "test_attraction_rollback")

        assert attraction is None

    def test_query_cache(self, db_manager):
        """Test query cache integration."""
        # Clear the cache
        db_manager.query_cache.clear()

        # Get a test attraction (should cache the result)
        attraction_id = "test_attraction_0"
        attraction = db_manager.generic_get("test_attractions", attraction_id)

        # Verify the result
        assert attraction is not None

        # Check if the result is cached
        cached_result = db_manager.query_cache.get_record("test_attractions", attraction_id)

        # Verify the cached result
        assert cached_result is not None
        assert cached_result["id"] == attraction_id

        # Update the attraction
        db_manager.generic_update(
            "test_attractions",
            attraction_id,
            {
                "name": {"en": "Updated Cache Test Attraction", "ar": "معلم اختبار الذاكرة المؤقتة المحدث"}
            }
        )

        # Cache should be invalidated
        cached_result = db_manager.query_cache.get_record("test_attractions", attraction_id)

        # Verify the cache is invalidated
        assert cached_result is None

    def test_query_batch(self, db_manager):
        """Test query batch integration."""
        # Create a batch executor
        batch = db_manager.create_batch_executor(
            batch_size=10,
            auto_execute=False
        )

        # Add insert operations
        for i in range(5):
            batch.add_insert(
                table="test_attractions",
                data={
                    "id": f"test_attraction_batch_{i}",
                    "name": {"en": f"Batch Test Attraction {i}", "ar": f"معلم اختبار الدفعة {i}"},
                    "description": {"en": f"Description for Batch Test Attraction {i}", "ar": f"وصف لمعلم اختبار الدفعة {i}"},
                    "type_id": "museum",
                    "city_id": "cairo",
                    "region_id": "cairo"
                }
            )

        # Execute the batch
        batch.execute_inserts("test_attractions")

        # Verify that the attractions were inserted
        for i in range(5):
            attraction = db_manager.generic_get("test_attractions", f"test_attraction_batch_{i}")
            assert attraction is not None
            assert attraction["id"] == f"test_attraction_batch_{i}"

        # Add update operations
        for i in range(5):
            batch.add_update(
                table="test_attractions",
                record_id=f"test_attraction_batch_{i}",
                data={
                    "name": {"en": f"Updated Batch Test Attraction {i}", "ar": f"معلم اختبار الدفعة المحدث {i}"}
                }
            )

        # Execute the batch
        batch.execute_updates("test_attractions")

        # Verify that the attractions were updated
        for i in range(5):
            attraction = db_manager.generic_get("test_attractions", f"test_attraction_batch_{i}")
            assert attraction is not None
            assert json.loads(attraction["name"])["en"] == f"Updated Batch Test Attraction {i}"

        # Add delete operations
        for i in range(5):
            batch.add_delete(
                table="test_attractions",
                record_id=f"test_attraction_batch_{i}"
            )

        # Execute the batch
        batch.execute_deletes("test_attractions")

        # Verify that the attractions were deleted
        for i in range(5):
            attraction = db_manager.generic_get("test_attractions", f"test_attraction_batch_{i}")
            assert attraction is None

    def test_query_analyzer(self, db_manager):
        """Test query analyzer integration."""
        # Clear the query analyzer
        db_manager.query_analyzer = QueryAnalyzer(
            slow_query_threshold_ms=500,
            max_queries_to_track=100
        )

        # Execute a fast query
        start_time = time.time()
        attraction = db_manager.generic_get("test_attractions", "test_attraction_0")
        duration_ms = (time.time() - start_time) * 1000

        # Verify the result
        assert attraction is not None

        # Execute a slow query (simulated)
        start_time = time.time()
        attractions = db_manager.generic_search("test_attractions", limit=10)
        # Simulate a slow query by adding a delay
        time.sleep(0.6)  # 600ms delay
        duration_ms = (time.time() - start_time) * 1000

        # Verify the result
        assert len(attractions) > 0

        # Get slow queries
        slow_queries = db_manager.query_analyzer.get_slow_queries()

        # Verify that the slow query was recorded
        assert len(slow_queries) > 0

        # Analyze slow queries
        analysis = db_manager.analyze_slow_queries()

        # Verify the analysis
        assert "slow_queries" in analysis
        assert "suggestions" in analysis
        assert "indexes" in analysis
