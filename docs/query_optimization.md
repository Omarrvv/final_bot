# Query Optimization

This document provides an overview of the query optimization features implemented in the Egypt Tourism Chatbot.

## Overview

The query optimization features are designed to improve the performance of database operations by:

1. **Analyzing query performance** to identify slow queries
2. **Suggesting optimizations** based on query patterns
3. **Implementing tiered caching** to reduce database load
4. **Batching database operations** for improved efficiency

## Components

### 1. QueryAnalyzer

The `QueryAnalyzer` class is responsible for tracking query performance and suggesting optimizations.

#### Key Features

- **Query tracking**: Records execution time and affected rows for each query
- **Slow query identification**: Identifies queries that exceed a configurable threshold
- **Query plan analysis**: Analyzes execution plans to identify performance issues
- **Index suggestions**: Suggests indexes based on query patterns

#### Usage Example

```python
# Initialize the query analyzer
query_analyzer = QueryAnalyzer(
    slow_query_threshold_ms=500,  # 500ms threshold for slow queries
    max_queries_to_track=100
)

# Record a query
query_analyzer.record_query(
    query="SELECT * FROM attractions WHERE type_id = %s",
    params=("museum",),
    duration_ms=600.0,
    rows_affected=100
)

# Get slow queries
slow_queries = query_analyzer.get_slow_queries()

# Analyze a query plan
plan_info = query_analyzer.analyze_query_plan(
    db_manager,
    "SELECT * FROM attractions WHERE type_id = %s",
    ("museum",)
)

# Get index suggestions
suggestions = query_analyzer.suggest_indexes(db_manager)
```

### 2. QueryBatch

The `QueryBatch` class provides tools for batching database operations to reduce the number of round trips to the database.

#### Key Features

- **Batch inserts**: Collects multiple insert operations and executes them in a single query
- **Batch updates**: Collects multiple update operations and executes them in a single transaction
- **Batch deletes**: Collects multiple delete operations and executes them in a single query
- **Custom batches**: Supports custom batch operations with user-defined processors

#### Usage Example

```python
# Create a batch executor
batch = QueryBatch(
    db_manager=db_manager,
    batch_size=100,
    auto_execute=False
)

# Add operations to the batch
batch.add_insert(
    table="attractions",
    data={"id": "test_id1", "name": "Test Attraction 1"}
)

batch.add_update(
    table="restaurants",
    record_id="test_id1",
    data={"name": "Updated Restaurant 1"}
)

batch.add_delete(
    table="cities",
    record_id="test_id1"
)

# Execute all operations
batch.execute_all()

# Or use as a context manager
with QueryBatch(db_manager) as batch:
    batch.add_insert(
        table="attractions",
        data={"id": "test_id1", "name": "Test Attraction 1"}
    )
    # Operations are automatically executed when exiting the context
```

### 3. TieredCache

The `TieredCache` class provides a two-level caching system that combines in-memory and Redis caching.

#### Key Features

- **In-memory cache**: Fast access to frequently used data
- **Redis cache**: Distributed caching across multiple instances
- **Fallback mechanism**: Falls back to in-memory cache if Redis is unavailable
- **Automatic serialization**: Handles serialization and deserialization of data

#### Usage Example

```python
# Create a tiered cache
cache = TieredCache(
    cache_prefix="my_cache",
    redis_uri="redis://localhost:6379/0",
    ttl=3600,  # 1 hour
    max_size=1000
)

# Set a value in the cache
cache.set(
    key_parts={"id": "test_id", "type": "attraction"},
    value={"id": "test_id", "name": "Test Attraction"}
)

# Get a value from the cache
value = cache.get(
    key_parts={"id": "test_id", "type": "attraction"}
)

# Invalidate cache entries
cache.invalidate("test_id")

# Clear the entire cache
cache.clear()
```

### 4. VectorTieredCache

The `VectorTieredCache` class extends the `TieredCache` class to provide specialized functionality for caching vector search results.

#### Key Features

- **Embedding handling**: Handles different embedding formats (list, numpy array, string)
- **Efficient key generation**: Generates efficient cache keys for embeddings
- **Table-specific invalidation**: Invalidates cache entries for specific tables

#### Usage Example

```python
# Create a vector tiered cache
vector_cache = VectorTieredCache(
    redis_uri="redis://localhost:6379/0",
    ttl=3600,  # 1 hour
    max_size=1000
)

# Get vector search results
results = vector_cache.get_vector_search_results(
    table_name="attractions",
    embedding=[0.1, 0.2, 0.3],
    filters={"type": "museum"},
    limit=10
)

# Set vector search results
vector_cache.set_vector_search_results(
    table_name="attractions",
    embedding=[0.1, 0.2, 0.3],
    results=[{"id": "test_id", "name": "Test Attraction"}],
    filters={"type": "museum"},
    limit=10
)

# Invalidate cache entries for a table
vector_cache.invalidate_table("attractions")

# Invalidate all vector search results
vector_cache.invalidate_all_vector_searches()
```

### 5. QueryCache

The `QueryCache` class extends the `TieredCache` class to provide specialized functionality for caching database query results.

#### Key Features

- **Query-specific caching**: Caches results for specific query types
- **Parameter-based keys**: Generates cache keys based on query parameters
- **Table-specific invalidation**: Invalidates cache entries for specific tables
- **Query type invalidation**: Invalidates cache entries for specific query types

#### Usage Example

```python
# Create a query cache
query_cache = QueryCache(
    redis_uri="redis://localhost:6379/0",
    ttl=1800,  # 30 minutes
    max_size=500
)

# Get search results
results = query_cache.get_search_results(
    table_name="attractions",
    query={"name": "pyramid"},
    filters={"type": "museum"},
    limit=10,
    offset=0,
    language="en"
)

# Set search results
query_cache.set_search_results(
    table_name="attractions",
    results=[{"id": "test_id", "name": "Test Attraction"}],
    query={"name": "pyramid"},
    filters={"type": "museum"},
    limit=10,
    offset=0,
    language="en"
)

# Get a record
record = query_cache.get_record(
    table_name="attractions",
    record_id="test_id"
)

# Set a record
query_cache.set_record(
    table_name="attractions",
    record_id="test_id",
    record={"id": "test_id", "name": "Test Attraction"}
)

# Invalidate cache entries for a table
query_cache.invalidate_table("attractions")

# Invalidate cache entries for a query type
query_cache.invalidate_query_type("search")

# Invalidate all query results
query_cache.invalidate_all_queries()
```

## Integration with DatabaseManager

The query optimization features are integrated with the `DatabaseManager` class to provide a seamless experience.

### Initialization

```python
# Initialize the database manager
db_manager = DatabaseManager()

# Access the query analyzer
query_analyzer = db_manager.query_analyzer

# Access the vector cache
vector_cache = db_manager.vector_cache

# Access the query cache
query_cache = db_manager.query_cache

# Create a batch executor
batch = db_manager.create_batch_executor(
    batch_size=100,
    auto_execute=False
)
```

### Analyzing Slow Queries

```python
# Analyze slow queries
analysis = db_manager.analyze_slow_queries()

# Access the analysis results
slow_queries = analysis["slow_queries"]
plans = analysis["plans"]
suggestions = analysis["suggestions"]
indexes = analysis["indexes"]
```

## Best Practices

1. **Use caching for frequently accessed data**: Implement caching for data that is accessed frequently but changes infrequently.

2. **Use query batching for bulk operations**: Batch multiple insert, update, or delete operations to reduce the number of round trips to the database.

3. **Analyze slow queries regularly**: Regularly analyze slow queries to identify performance issues and optimize them.

4. **Implement suggested indexes**: Implement the indexes suggested by the query analyzer to improve query performance.

5. **Monitor cache hit rates**: Monitor cache hit rates to ensure that caching is effective.

6. **Use the appropriate cache TTL**: Set an appropriate time-to-live (TTL) for cached data based on how frequently it changes.

7. **Use the context manager pattern for batch operations**: Use the context manager pattern for batch operations to ensure that they are executed properly.

8. **Invalidate cache entries when data changes**: Invalidate cache entries when the underlying data changes to ensure that cached data is always up-to-date.
