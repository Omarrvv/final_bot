"""
Example usage of query optimization features.

This module demonstrates how to use the query optimization features
implemented in the Egypt Tourism Chatbot.
"""
import os
import time
import json
from typing import Dict, List, Any

from src.knowledge.database import DatabaseManager
from src.utils.query_analyzer import QueryAnalyzer
from src.utils.query_batch import QueryBatch
from src.utils.tiered_cache import TieredCache
from src.utils.query_cache import QueryCache
from src.knowledge.vector_tiered_cache import VectorTieredCache

def demonstrate_query_analyzer():
    """Demonstrate the QueryAnalyzer class."""
    print("\n=== QueryAnalyzer Example ===\n")
    
    # Initialize the database manager
    db_manager = DatabaseManager()
    
    # Access the query analyzer
    query_analyzer = db_manager.query_analyzer
    
    # Execute some queries
    print("Executing queries...")
    
    # Fast query
    start_time = time.time()
    result = db_manager.execute_postgres_query(
        "SELECT id, name FROM attractions LIMIT 5",
        fetchall=True
    )
    duration_ms = (time.time() - start_time) * 1000
    print(f"Fast query executed in {duration_ms:.2f}ms")
    
    # Slow query (simulated)
    start_time = time.time()
    result = db_manager.execute_postgres_query(
        "SELECT * FROM attractions WHERE name_en ILIKE %s",
        ("%pyramid%",),
        fetchall=True
    )
    # Simulate a slow query by adding a delay
    time.sleep(0.6)  # 600ms delay
    duration_ms = (time.time() - start_time) * 1000
    print(f"Slow query executed in {duration_ms:.2f}ms")
    
    # Get slow queries
    slow_queries = query_analyzer.get_slow_queries()
    print(f"\nFound {len(slow_queries)} slow queries:")
    for i, query in enumerate(slow_queries):
        print(f"{i+1}. {query['query']} ({query['duration_ms']:.2f}ms)")
    
    # Analyze slow queries
    analysis = db_manager.analyze_slow_queries()
    
    print("\nSuggestions:")
    for suggestion in analysis["suggestions"]:
        print(f"- {suggestion}")
    
    print("\nIndex suggestions:")
    for table, indexes in analysis["indexes"].items():
        print(f"Table: {table}")
        for index in indexes:
            print(f"- {index}")

def demonstrate_query_batch():
    """Demonstrate the QueryBatch class."""
    print("\n=== QueryBatch Example ===\n")
    
    # Initialize the database manager
    db_manager = DatabaseManager()
    
    # Create a batch executor
    batch = db_manager.create_batch_executor(
        batch_size=100,
        auto_execute=False
    )
    
    # Add operations to the batch
    print("Adding operations to the batch...")
    
    # Add insert operations
    for i in range(5):
        batch.add_insert(
            table="attractions",
            data={
                "id": f"test_id_{i}",
                "name": {"en": f"Test Attraction {i}", "ar": f"اختبار الجذب {i}"},
                "description": {"en": f"Test Description {i}", "ar": f"وصف الاختبار {i}"},
                "type_id": "test_type",
                "city_id": "test_city",
                "region_id": "test_region"
            }
        )
    
    # Add update operations
    for i in range(5):
        batch.add_update(
            table="attractions",
            record_id=f"test_id_{i}",
            data={
                "name": {"en": f"Updated Attraction {i}", "ar": f"تحديث الجذب {i}"}
            }
        )
    
    # Add delete operations
    for i in range(5):
        batch.add_delete(
            table="attractions",
            record_id=f"test_id_{i}"
        )
    
    # Print batch status
    print(f"Batch status:")
    print(f"- Inserts: {sum(len(ops) for ops in batch.inserts.values())} operations")
    print(f"- Updates: {sum(len(ops) for ops in batch.updates.values())} operations")
    print(f"- Deletes: {sum(len(ops) for ops in batch.deletes.values())} operations")
    
    # Execute the batch
    print("\nExecuting the batch...")
    batch.execute_all()
    
    # Print batch status after execution
    print(f"\nBatch status after execution:")
    print(f"- Inserts: {sum(len(ops) for ops in batch.inserts.values())} operations")
    print(f"- Updates: {sum(len(ops) for ops in batch.updates.values())} operations")
    print(f"- Deletes: {sum(len(ops) for ops in batch.deletes.values())} operations")
    
    # Demonstrate context manager
    print("\nUsing context manager...")
    with db_manager.create_batch_executor() as batch:
        batch.add_insert(
            table="attractions",
            data={
                "id": "test_context_id",
                "name": {"en": "Test Context Attraction", "ar": "اختبار الجذب السياق"},
                "description": {"en": "Test Context Description", "ar": "وصف الاختبار السياق"},
                "type_id": "test_type",
                "city_id": "test_city",
                "region_id": "test_region"
            }
        )
        print("Added operation to the context batch")
    print("Context exited, batch executed automatically")

def demonstrate_tiered_cache():
    """Demonstrate the TieredCache class."""
    print("\n=== TieredCache Example ===\n")
    
    # Initialize the tiered cache
    redis_uri = os.environ.get("REDIS_URI")
    cache = TieredCache(
        cache_prefix="example_cache",
        redis_uri=redis_uri,
        ttl=3600,  # 1 hour
        max_size=1000
    )
    
    # Set a value in the cache
    key_parts = {"id": "test_id", "type": "attraction"}
    value = {"id": "test_id", "name": "Test Attraction", "data": {"key": "value"}}
    
    print(f"Setting value in cache with key parts: {key_parts}")
    cache.set(key_parts, value)
    
    # Get the value from the cache
    print(f"Getting value from cache with key parts: {key_parts}")
    cached_value = cache.get(key_parts)
    
    if cached_value:
        print(f"Cache hit! Value: {cached_value}")
    else:
        print("Cache miss!")
    
    # Invalidate the cache
    print(f"Invalidating cache with pattern: test_id")
    cache.invalidate("test_id")
    
    # Try to get the value again
    print(f"Getting value from cache after invalidation")
    cached_value = cache.get(key_parts)
    
    if cached_value:
        print(f"Cache hit! Value: {cached_value}")
    else:
        print("Cache miss!")
    
    # Clear the cache
    print(f"Clearing the entire cache")
    cache.clear()

def demonstrate_vector_cache():
    """Demonstrate the VectorTieredCache class."""
    print("\n=== VectorTieredCache Example ===\n")
    
    # Initialize the database manager
    db_manager = DatabaseManager()
    
    # Access the vector cache
    vector_cache = db_manager.vector_cache
    
    # Create a sample embedding
    embedding = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    
    # Set vector search results
    results = [
        {"id": "test_id_1", "name": "Test Attraction 1", "similarity": 0.9},
        {"id": "test_id_2", "name": "Test Attraction 2", "similarity": 0.8},
        {"id": "test_id_3", "name": "Test Attraction 3", "similarity": 0.7}
    ]
    
    print(f"Setting vector search results in cache")
    vector_cache.set_vector_search_results(
        table_name="attractions",
        embedding=embedding,
        results=results,
        filters={"type": "museum"},
        limit=10
    )
    
    # Get vector search results
    print(f"Getting vector search results from cache")
    cached_results = vector_cache.get_vector_search_results(
        table_name="attractions",
        embedding=embedding,
        filters={"type": "museum"},
        limit=10
    )
    
    if cached_results:
        print(f"Cache hit! Found {len(cached_results)} results")
        for i, result in enumerate(cached_results):
            print(f"{i+1}. {result['name']} (similarity: {result['similarity']:.2f})")
    else:
        print("Cache miss!")
    
    # Invalidate cache entries for a table
    print(f"Invalidating cache entries for table: attractions")
    vector_cache.invalidate_table("attractions")
    
    # Try to get the results again
    print(f"Getting vector search results after invalidation")
    cached_results = vector_cache.get_vector_search_results(
        table_name="attractions",
        embedding=embedding,
        filters={"type": "museum"},
        limit=10
    )
    
    if cached_results:
        print(f"Cache hit! Found {len(cached_results)} results")
    else:
        print("Cache miss!")

def demonstrate_query_cache():
    """Demonstrate the QueryCache class."""
    print("\n=== QueryCache Example ===\n")
    
    # Initialize the database manager
    db_manager = DatabaseManager()
    
    # Access the query cache
    query_cache = db_manager.query_cache
    
    # Set search results
    results = [
        {"id": "test_id_1", "name": "Test Attraction 1"},
        {"id": "test_id_2", "name": "Test Attraction 2"},
        {"id": "test_id_3", "name": "Test Attraction 3"}
    ]
    
    print(f"Setting search results in cache")
    query_cache.set_search_results(
        table_name="attractions",
        results=results,
        query={"name": "pyramid"},
        filters={"type": "museum"},
        limit=10,
        offset=0,
        language="en"
    )
    
    # Get search results
    print(f"Getting search results from cache")
    cached_results = query_cache.get_search_results(
        table_name="attractions",
        query={"name": "pyramid"},
        filters={"type": "museum"},
        limit=10,
        offset=0,
        language="en"
    )
    
    if cached_results:
        print(f"Cache hit! Found {len(cached_results)} results")
        for i, result in enumerate(cached_results):
            print(f"{i+1}. {result['name']}")
    else:
        print("Cache miss!")
    
    # Set a record
    record = {"id": "test_id", "name": "Test Attraction", "data": {"key": "value"}}
    
    print(f"Setting record in cache")
    query_cache.set_record(
        table_name="attractions",
        record_id="test_id",
        record=record
    )
    
    # Get the record
    print(f"Getting record from cache")
    cached_record = query_cache.get_record(
        table_name="attractions",
        record_id="test_id"
    )
    
    if cached_record:
        print(f"Cache hit! Record: {cached_record}")
    else:
        print("Cache miss!")
    
    # Invalidate cache entries for a table
    print(f"Invalidating cache entries for table: attractions")
    query_cache.invalidate_table("attractions")
    
    # Try to get the record again
    print(f"Getting record after invalidation")
    cached_record = query_cache.get_record(
        table_name="attractions",
        record_id="test_id"
    )
    
    if cached_record:
        print(f"Cache hit! Record: {cached_record}")
    else:
        print("Cache miss!")

def main():
    """Run all demonstrations."""
    print("=== Query Optimization Examples ===")
    
    # Demonstrate the QueryAnalyzer class
    demonstrate_query_analyzer()
    
    # Demonstrate the QueryBatch class
    demonstrate_query_batch()
    
    # Demonstrate the TieredCache class
    demonstrate_tiered_cache()
    
    # Demonstrate the VectorTieredCache class
    demonstrate_vector_cache()
    
    # Demonstrate the QueryCache class
    demonstrate_query_cache()

if __name__ == "__main__":
    main()
