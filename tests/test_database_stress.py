"""
Stress tests for the database manager.

This module contains stress tests for the database manager,
testing behavior under high load.
"""
import json
import time
import pytest
import random
import string
import threading
import concurrent.futures
from typing import Dict, List, Any, Optional

from src.knowledge.database import DatabaseManager
from src.utils.query_cache import QueryCache
from src.utils.query_analyzer import QueryAnalyzer
from src.utils.query_batch import QueryBatch

class TestDatabaseStress:
    """Stress tests for the database manager."""
    
    @pytest.fixture
    def db_manager(self):
        """Create a database manager for testing."""
        # Use the test database
        db_manager = DatabaseManager(
            postgres_uri="postgresql://postgres:postgres@localhost:5432/egypt_chatbot",
            redis_uri="redis://localhost:6379/0"
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
        """Set up test data for stress tests."""
        # Create test tables if they don't exist
        with db_manager.transaction() as cursor:
            # Create stress_attractions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stress_attractions (
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
                CREATE INDEX IF NOT EXISTS idx_stress_attractions_type_id ON stress_attractions (type_id)
            """)
            
            # Create index on city_id
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_stress_attractions_city_id ON stress_attractions (city_id)
            """)
        
        # Insert test data
        with db_manager.transaction() as cursor:
            # Clear existing test data
            cursor.execute("DELETE FROM stress_attractions")
            
            # Check if we need to insert data
            cursor.execute("SELECT COUNT(*) FROM stress_attractions")
            count = cursor.fetchone()[0]
            
            if count < 1000:
                # Insert 1000 test attractions
                for i in range(1000):
                    cursor.execute(
                        """
                        INSERT INTO stress_attractions (id, name, description, type_id, city_id, region_id)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (
                            f"stress_attraction_{i}",
                            json.dumps({"en": f"Stress Test Attraction {i}", "ar": f"معلم اختبار الضغط {i}"}),
                            json.dumps({"en": f"Description for Stress Test Attraction {i}", "ar": f"وصف لمعلم اختبار الضغط {i}"}),
                            random.choice(["museum", "historical", "natural", "cultural", "religious"]),
                            random.choice(["cairo", "luxor", "aswan", "alexandria", "hurghada"]),
                            random.choice(["cairo", "upper_egypt", "north_coast", "red_sea", "sinai"])
                        )
                    )
    
    def _cleanup_test_data(self, db_manager):
        """Clean up test data after stress tests."""
        # We don't delete the test data after stress tests
        # to avoid having to recreate it for each test run
        pass
    
    def test_concurrent_queries(self, db_manager):
        """Test concurrent query execution."""
        # Number of concurrent queries
        num_queries = 50
        
        # Results container
        results = []
        errors = []
        
        # Query function
        def query_thread(query_type, query_id):
            try:
                if query_type == "get":
                    # Get a random attraction
                    attraction_id = f"stress_attraction_{random.randint(0, 999)}"
                    result = db_manager.generic_get("stress_attractions", attraction_id)
                    results.append(result)
                elif query_type == "search":
                    # Search with random filters
                    type_id = random.choice(["museum", "historical", "natural", "cultural", "religious"])
                    city_id = random.choice(["cairo", "luxor", "aswan", "alexandria", "hurghada"])
                    result = db_manager.generic_search(
                        "stress_attractions",
                        filters={"type_id": type_id, "city_id": city_id},
                        limit=10
                    )
                    results.append(result)
                else:
                    raise ValueError(f"Unknown query type: {query_type}")
            except Exception as e:
                errors.append((query_type, query_id, str(e)))
        
        # Create and start threads
        threads = []
        start_time = time.time()
        
        for i in range(num_queries):
            query_type = "get" if i % 2 == 0 else "search"
            thread = threading.Thread(target=query_thread, args=(query_type, i))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        total_duration_ms = (end_time - start_time) * 1000
        
        # Log performance
        print(f"Concurrent queries: {num_queries}")
        print(f"Total duration: {total_duration_ms:.2f}ms")
        print(f"Average duration per query: {total_duration_ms / num_queries:.2f}ms")
        print(f"Successful queries: {len(results)}")
        print(f"Failed queries: {len(errors)}")
        
        if errors:
            print("Errors:")
            for query_type, query_id, error in errors:
                print(f"  {query_type} query {query_id}: {error}")
        
        # All queries should succeed
        assert len(errors) == 0
        assert len(results) == num_queries
    
    def test_connection_pool_stress(self, db_manager):
        """Test connection pool under high concurrency."""
        # Number of concurrent connections
        num_connections = 50
        
        # Results container
        results = []
        errors = []
        
        # Query function
        def query_func(query_id):
            try:
                # Execute a simple query
                result = db_manager.execute_postgres_query(
                    "SELECT COUNT(*) FROM stress_attractions",
                    fetchall=False
                )
                results.append(result)
            except Exception as e:
                errors.append((query_id, str(e)))
        
        # Create and start threads using a thread pool
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_connections) as executor:
            futures = [executor.submit(query_func, i) for i in range(num_connections)]
            concurrent.futures.wait(futures)
        
        end_time = time.time()
        total_duration_ms = (end_time - start_time) * 1000
        
        # Log performance
        print(f"Concurrent connections: {num_connections}")
        print(f"Total duration: {total_duration_ms:.2f}ms")
        print(f"Average duration per connection: {total_duration_ms / num_connections:.2f}ms")
        print(f"Successful connections: {len(results)}")
        print(f"Failed connections: {len(errors)}")
        
        if errors:
            print("Errors:")
            for query_id, error in errors:
                print(f"  Connection {query_id}: {error}")
        
        # All connections should succeed
        assert len(errors) == 0
        assert len(results) == num_connections
        
        # Check connection pool metrics
        pool_metrics = db_manager.pool_metrics
        print(f"Connection pool metrics: {pool_metrics}")
        
        # Pool should handle the load
        assert pool_metrics["error_count"] == 0
    
    def test_cache_stress(self, db_manager):
        """Test cache under high concurrency."""
        # Clear the cache
        db_manager.query_cache.clear()
        
        # Number of concurrent queries
        num_queries = 50
        
        # Results container
        results = []
        errors = []
        cache_hits = []
        cache_misses = []
        
        # Query function
        def query_thread(query_id):
            try:
                # Get a specific attraction (all threads get the same one to test cache)
                attraction_id = "stress_attraction_0"
                
                # Check cache first
                cached_result = db_manager.query_cache.get_record("stress_attractions", attraction_id)
                
                if cached_result is not None:
                    cache_hits.append(query_id)
                    results.append(cached_result)
                else:
                    cache_misses.append(query_id)
                    
                    # Cache miss, get from database
                    result = db_manager.generic_get("stress_attractions", attraction_id)
                    results.append(result)
                    
                    # Cache the result
                    if result:
                        db_manager.query_cache.set_record("stress_attractions", attraction_id, result)
            except Exception as e:
                errors.append((query_id, str(e)))
        
        # Create and start threads
        threads = []
        start_time = time.time()
        
        for i in range(num_queries):
            thread = threading.Thread(target=query_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        total_duration_ms = (end_time - start_time) * 1000
        
        # Log performance
        print(f"Concurrent cache queries: {num_queries}")
        print(f"Total duration: {total_duration_ms:.2f}ms")
        print(f"Average duration per query: {total_duration_ms / num_queries:.2f}ms")
        print(f"Successful queries: {len(results)}")
        print(f"Failed queries: {len(errors)}")
        print(f"Cache hits: {len(cache_hits)}")
        print(f"Cache misses: {len(cache_misses)}")
        
        if errors:
            print("Errors:")
            for query_id, error in errors:
                print(f"  Query {query_id}: {error}")
        
        # All queries should succeed
        assert len(errors) == 0
        assert len(results) == num_queries
        
        # Should have at least some cache hits
        assert len(cache_hits) > 0
    
    def test_query_batch_stress(self, db_manager):
        """Test query batch under high load."""
        # Number of records to batch
        num_records = 500
        
        # Generate test data
        test_data = []
        for i in range(num_records):
            test_data.append({
                "id": f"stress_batch_attraction_{i}",
                "name": {"en": f"Batch Stress Test Attraction {i}", "ar": f"معلم اختبار ضغط الدفعة {i}"},
                "description": {"en": f"Description for Batch Stress Test Attraction {i}", "ar": f"وصف لمعلم اختبار ضغط الدفعة {i}"},
                "type_id": random.choice(["museum", "historical", "natural", "cultural", "religious"]),
                "city_id": random.choice(["cairo", "luxor", "aswan", "alexandria", "hurghada"]),
                "region_id": random.choice(["cairo", "upper_egypt", "north_coast", "red_sea", "sinai"])
            })
        
        # Create a batch executor
        batch = db_manager.create_batch_executor(
            batch_size=100,  # Use a smaller batch size to test multiple batches
            auto_execute=True  # Auto-execute when batch size is reached
        )
        
        # Add insert operations
        start_time = time.time()
        
        for data in test_data:
            batch.add_insert("stress_attractions", data)
        
        # Execute any remaining operations
        batch.execute_all()
        
        end_time = time.time()
        total_duration_ms = (end_time - start_time) * 1000
        
        # Log performance
        print(f"Batch stress test:")
        print(f"  Records: {num_records}")
        print(f"  Batch size: {batch.batch_size}")
        print(f"  Total duration: {total_duration_ms:.2f}ms")
        print(f"  Average duration per record: {total_duration_ms / num_records:.2f}ms")
        
        # Verify that the records were inserted
        count = 0
        with db_manager.transaction() as cursor:
            cursor.execute("SELECT COUNT(*) FROM stress_attractions WHERE id LIKE 'stress_batch_attraction_%'")
            count = cursor.fetchone()[0]
        
        print(f"  Inserted records: {count}")
        
        # All records should be inserted
        assert count == num_records
        
        # Clean up batch inserts
        with db_manager.transaction() as cursor:
            cursor.execute("DELETE FROM stress_attractions WHERE id LIKE 'stress_batch_attraction_%'")
    
    def test_transaction_stress(self, db_manager):
        """Test transactions under high concurrency."""
        # Number of concurrent transactions
        num_transactions = 20
        
        # Results container
        results = []
        errors = []
        
        # Transaction function
        def transaction_thread(transaction_id):
            try:
                # Start a transaction
                with db_manager.transaction() as cursor:
                    # Insert a new record
                    cursor.execute(
                        """
                        INSERT INTO stress_attractions (id, name, description, type_id, city_id, region_id)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (
                            f"stress_transaction_{transaction_id}",
                            json.dumps({"en": f"Transaction Stress Test {transaction_id}", "ar": f"اختبار ضغط المعاملة {transaction_id}"}),
                            json.dumps({"en": f"Description for Transaction Stress Test {transaction_id}", "ar": f"وصف لاختبار ضغط المعاملة {transaction_id}"}),
                            "museum",
                            "cairo",
                            "cairo"
                        )
                    )
                    
                    # Simulate some work
                    time.sleep(0.01)
                    
                    # Update the record
                    cursor.execute(
                        """
                        UPDATE stress_attractions
                        SET name = %s
                        WHERE id = %s
                        """,
                        (
                            json.dumps({"en": f"Updated Transaction Stress Test {transaction_id}", "ar": f"اختبار ضغط المعاملة المحدث {transaction_id}"}),
                            f"stress_transaction_{transaction_id}"
                        )
                    )
                
                # Transaction succeeded
                results.append(transaction_id)
            except Exception as e:
                errors.append((transaction_id, str(e)))
        
        # Create and start threads
        threads = []
        start_time = time.time()
        
        for i in range(num_transactions):
            thread = threading.Thread(target=transaction_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        total_duration_ms = (end_time - start_time) * 1000
        
        # Log performance
        print(f"Concurrent transactions: {num_transactions}")
        print(f"Total duration: {total_duration_ms:.2f}ms")
        print(f"Average duration per transaction: {total_duration_ms / num_transactions:.2f}ms")
        print(f"Successful transactions: {len(results)}")
        print(f"Failed transactions: {len(errors)}")
        
        if errors:
            print("Errors:")
            for transaction_id, error in errors:
                print(f"  Transaction {transaction_id}: {error}")
        
        # All transactions should succeed
        assert len(errors) == 0
        assert len(results) == num_transactions
        
        # Verify that all records were inserted and updated
        count = 0
        with db_manager.transaction() as cursor:
            cursor.execute("SELECT COUNT(*) FROM stress_attractions WHERE id LIKE 'stress_transaction_%'")
            count = cursor.fetchone()[0]
        
        print(f"  Inserted records: {count}")
        
        # All records should be inserted
        assert count == num_transactions
        
        # Clean up transaction inserts
        with db_manager.transaction() as cursor:
            cursor.execute("DELETE FROM stress_attractions WHERE id LIKE 'stress_transaction_%'")
