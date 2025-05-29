"""
Performance tests for the database manager.

This module contains performance tests for the database manager,
testing performance under various conditions.
"""
import json
import time
import pytest
import random
import string
from typing import Dict, List, Any, Optional

from src.knowledge.database import DatabaseManager
from src.utils.query_cache import QueryCache
from src.utils.query_analyzer import QueryAnalyzer
from src.utils.query_batch import QueryBatch

class TestDatabasePerformance:
    """Performance tests for the database manager."""

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
        """Set up test data for performance tests."""
        # Create test tables if they don't exist
        with db_manager.transaction() as cursor:
            # Create perf_attractions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS perf_attractions (
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

            # Create index on type_id
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_perf_attractions_type_id ON perf_attractions (type_id)
            """)

            # Create index on city_id
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_perf_attractions_city_id ON perf_attractions (city_id)
            """)

        # Insert test data
        with db_manager.transaction() as cursor:
            # Clear existing test data
            cursor.execute("DELETE FROM perf_attractions")

            # Check if we need to insert data
            cursor.execute("SELECT COUNT(*) FROM perf_attractions")
            count = cursor.fetchone()[0]

            if count < 1000:
                # Insert 1000 test attractions
                for i in range(1000):
                    cursor.execute(
                        """
                        INSERT INTO perf_attractions (id, name, description, type_id, city_id, region_id)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (
                            f"perf_attraction_{i}",
                            json.dumps({"en": f"Performance Test Attraction {i}", "ar": f"معلم اختبار الأداء {i}"}),
                            json.dumps({"en": f"Description for Performance Test Attraction {i}", "ar": f"وصف لمعلم اختبار الأداء {i}"}),
                            random.choice(["museum", "historical", "natural", "cultural", "religious"]),
                            random.choice(["cairo", "luxor", "aswan", "alexandria", "hurghada"]),
                            random.choice(["cairo", "upper_egypt", "north_coast", "red_sea", "sinai"])
                        )
                    )

    def _cleanup_test_data(self, db_manager):
        """Clean up test data after performance tests."""
        # We don't delete the test data after performance tests
        # to avoid having to recreate it for each test run
        pass

    def test_query_performance(self, db_manager):
        """Test query performance."""
        # Measure query performance
        start_time = time.time()

        # Execute query
        results = db_manager.generic_search(
            "perf_attractions",
            filters={"type_id": "museum", "city_id": "cairo"},
            limit=100
        )

        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000

        # Log performance
        print(f"Query performance: {duration_ms:.2f}ms")

        # Verify the results
        assert len(results) > 0

        # Query should complete in a reasonable time
        assert duration_ms < 500  # 500ms is a reasonable threshold for this test

    def test_cache_performance(self, db_manager):
        """Test cache performance."""
        # Clear the cache
        db_manager.query_cache.clear()

        # Measure uncached query performance
        start_time = time.time()

        # Execute query
        results = db_manager.generic_search(
            "perf_attractions",
            filters={"type_id": "museum", "city_id": "cairo"},
            limit=100
        )

        uncached_duration_ms = (time.time() - start_time) * 1000

        # Measure cached query performance
        start_time = time.time()

        # Execute same query (should be cached)
        results = db_manager.generic_search(
            "perf_attractions",
            filters={"type_id": "museum", "city_id": "cairo"},
            limit=100
        )

        cached_duration_ms = (time.time() - start_time) * 1000

        # Log performance
        print(f"Uncached query performance: {uncached_duration_ms:.2f}ms")
        print(f"Cached query performance: {cached_duration_ms:.2f}ms")
        print(f"Cache speedup: {uncached_duration_ms / cached_duration_ms:.2f}x")

        # Verify the results
        assert len(results) > 0

        # Cached query should be faster
        assert cached_duration_ms < uncached_duration_ms

        # Cached query should be significantly faster
        assert cached_duration_ms < uncached_duration_ms / 2

    def test_batch_performance(self, db_manager):
        """Test batch operation performance."""
        # Generate test data
        test_data = []
        for i in range(100):
            test_data.append({
                "id": f"perf_batch_attraction_{i}",
                "name": {"en": f"Batch Performance Test Attraction {i}", "ar": f"معلم اختبار أداء الدفعة {i}"},
                "description": {"en": f"Description for Batch Performance Test Attraction {i}", "ar": f"وصف لمعلم اختبار أداء الدفعة {i}"},
                "type_id": random.choice(["museum", "historical", "natural", "cultural", "religious"]),
                "city_id": random.choice(["cairo", "luxor", "aswan", "alexandria", "hurghada"]),
                "region_id": random.choice(["cairo", "upper_egypt", "north_coast", "red_sea", "sinai"])
            })

        # Measure individual insert performance
        start_time = time.time()

        # Execute individual inserts
        for data in test_data[:10]:  # Only use 10 records for individual inserts to save time
            db_manager.generic_create("perf_attractions", data)

        individual_duration_ms = (time.time() - start_time) * 1000 / 10  # Average per insert

        # Clean up individual inserts
        with db_manager.transaction() as cursor:
            for i in range(10):
                cursor.execute("DELETE FROM perf_attractions WHERE id = %s", (f"perf_batch_attraction_{i}",))

        # Measure batch insert performance
        start_time = time.time()

        # Create a batch executor
        batch = db_manager.create_batch_executor(
            batch_size=100,
            auto_execute=False
        )

        # Add insert operations
        for data in test_data:
            batch.add_insert("perf_attractions", data)

        # Execute the batch
        batch.execute_inserts("perf_attractions")

        batch_duration_ms = (time.time() - start_time) * 1000 / 100  # Average per insert

        # Log performance
        print(f"Individual insert performance: {individual_duration_ms:.2f}ms per insert")
        print(f"Batch insert performance: {batch_duration_ms:.2f}ms per insert")
        print(f"Batch speedup: {individual_duration_ms / batch_duration_ms:.2f}x")

        # Batch insert should be faster
        assert batch_duration_ms < individual_duration_ms

        # Clean up batch inserts
        with db_manager.transaction() as cursor:
            for i in range(100):
                cursor.execute("DELETE FROM perf_attractions WHERE id = %s", (f"perf_batch_attraction_{i}",))

    def test_query_complexity_performance(self, db_manager):
        """Test query performance with different complexity levels."""
        # Simple query (single filter)
        start_time = time.time()
        results_simple = db_manager.generic_search(
            "perf_attractions",
            filters={"type_id": "museum"},
            limit=100
        )
        simple_duration_ms = (time.time() - start_time) * 1000

        # Medium query (two filters)
        start_time = time.time()
        results_medium = db_manager.generic_search(
            "perf_attractions",
            filters={"type_id": "museum", "city_id": "cairo"},
            limit=100
        )
        medium_duration_ms = (time.time() - start_time) * 1000

        # Complex query (three filters)
        start_time = time.time()
        results_complex = db_manager.generic_search(
            "perf_attractions",
            filters={"type_id": "museum", "city_id": "cairo", "region_id": "cairo"},
            limit=100
        )
        complex_duration_ms = (time.time() - start_time) * 1000

        # Log performance
        print(f"Simple query performance: {simple_duration_ms:.2f}ms")
        print(f"Medium query performance: {medium_duration_ms:.2f}ms")
        print(f"Complex query performance: {complex_duration_ms:.2f}ms")

        # Verify the results
        assert len(results_simple) > 0
        assert len(results_medium) > 0
        assert len(results_complex) > 0

        # More complex queries should take longer, but not excessively so
        assert complex_duration_ms < simple_duration_ms * 3

    def test_pagination_performance(self, db_manager):
        """Test query performance with different pagination settings."""
        # Small result set (10 records)
        start_time = time.time()
        results_small = db_manager.generic_search(
            "perf_attractions",
            limit=10,
            offset=0
        )
        small_duration_ms = (time.time() - start_time) * 1000

        # Medium result set (100 records)
        start_time = time.time()
        results_medium = db_manager.generic_search(
            "perf_attractions",
            limit=100,
            offset=0
        )
        medium_duration_ms = (time.time() - start_time) * 1000

        # Large result set (500 records)
        start_time = time.time()
        results_large = db_manager.generic_search(
            "perf_attractions",
            limit=500,
            offset=0
        )
        large_duration_ms = (time.time() - start_time) * 1000

        # Log performance
        print(f"Small result set (10 records) performance: {small_duration_ms:.2f}ms")
        print(f"Medium result set (100 records) performance: {medium_duration_ms:.2f}ms")
        print(f"Large result set (500 records) performance: {large_duration_ms:.2f}ms")

        # Verify the results
        assert len(results_small) == 10
        assert len(results_medium) == 100
        assert len(results_large) == 500

        # Larger result sets should take longer, but should scale reasonably
        assert medium_duration_ms < small_duration_ms * 15  # Not strictly linear due to overhead
        assert large_duration_ms < medium_duration_ms * 10  # Not strictly linear due to overhead

    def test_connection_pool_performance(self, db_manager):
        """Test connection pool performance."""
        # Measure query performance with connection pool
        durations = []

        for i in range(10):
            start_time = time.time()

            # Execute query
            results = db_manager.generic_search(
                "perf_attractions",
                filters={"type_id": "museum"},
                limit=10
            )

            duration_ms = (time.time() - start_time) * 1000
            durations.append(duration_ms)

        # Calculate statistics
        avg_duration_ms = sum(durations) / len(durations)
        min_duration_ms = min(durations)
        max_duration_ms = max(durations)

        # Log performance
        print(f"Connection pool performance:")
        print(f"  Average duration: {avg_duration_ms:.2f}ms")
        print(f"  Minimum duration: {min_duration_ms:.2f}ms")
        print(f"  Maximum duration: {max_duration_ms:.2f}ms")

        # Performance should be consistent
        assert max_duration_ms < min_duration_ms * 5  # Allow some variation, but not excessive

    def test_query_analyzer_performance(self, db_manager):
        """Test query analyzer performance impact."""
        # Clear the query analyzer
        db_manager.query_analyzer = QueryAnalyzer(
            slow_query_threshold_ms=500,
            max_queries_to_track=100
        )

        # Measure query performance without analyzer recording
        db_manager.query_analyzer.record_query = lambda *args, **kwargs: None

        start_time = time.time()
        results_without = db_manager.generic_search(
            "perf_attractions",
            filters={"type_id": "museum"},
            limit=100
        )
        without_duration_ms = (time.time() - start_time) * 1000

        # Restore the record_query method
        db_manager.query_analyzer = QueryAnalyzer(
            slow_query_threshold_ms=500,
            max_queries_to_track=100
        )

        # Measure query performance with analyzer recording
        start_time = time.time()
        results_with = db_manager.generic_search(
            "perf_attractions",
            filters={"type_id": "museum"},
            limit=100
        )
        with_duration_ms = (time.time() - start_time) * 1000

        # Log performance
        print(f"Query performance without analyzer: {without_duration_ms:.2f}ms")
        print(f"Query performance with analyzer: {with_duration_ms:.2f}ms")
        print(f"Analyzer overhead: {with_duration_ms - without_duration_ms:.2f}ms ({(with_duration_ms / without_duration_ms - 1) * 100:.2f}%)")

        # Verify the results
        assert len(results_without) == len(results_with)

        # Analyzer should not add excessive overhead
        assert with_duration_ms < without_duration_ms * 1.5  # Allow up to 50% overhead
