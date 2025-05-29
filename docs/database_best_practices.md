# Database Best Practices

This document provides best practices for using the database manager in the Egypt Tourism Chatbot.

## Connection Management

### Use a Single Database Manager Instance

Create a single instance of the DatabaseManager class and reuse it throughout your application. This ensures efficient use of connection pooling and prevents resource leaks.

```python
# Good practice
db_manager = DatabaseManager()

# Use the same instance throughout your application
def get_db_manager():
    return db_manager

# Bad practice - creating multiple instances
def some_function():
    db_manager = DatabaseManager()  # Don't do this
    # ...
```

### Close Connections When Done

Always close database connections when you're done with them to release resources.

```python
# Using context manager (recommended)
with DatabaseManager() as db_manager:
    # Use db_manager here
    # Connections are automatically closed when exiting the context

# Manual closing
db_manager = DatabaseManager()
try:
    # Use db_manager here
finally:
    db_manager.close()
```

### Check Connection Status

Check if the database is connected before executing queries, especially after periods of inactivity.

```python
if not db_manager.is_connected():
    db_manager.connect()
```

## Query Execution

### Use Parameterized Queries

Always use parameterized queries to prevent SQL injection attacks.

```python
# Good practice
db_manager.execute_postgres_query(
    "SELECT * FROM attractions WHERE id = %s",
    ("attraction_id",)
)

# Bad practice - vulnerable to SQL injection
attraction_id = "attraction_id"
db_manager.execute_postgres_query(
    f"SELECT * FROM attractions WHERE id = '{attraction_id}'"  # Don't do this
)
```

### Use Transactions for Multiple Operations

Use transactions when executing multiple related queries to ensure atomicity.

```python
with db_manager.transaction() as cursor:
    cursor.execute("INSERT INTO attractions (id, name) VALUES (%s, %s)", ("attraction_id", "Attraction Name"))
    cursor.execute("INSERT INTO attraction_tags (attraction_id, tag_id) VALUES (%s, %s)", ("attraction_id", "tag_id"))
```

### Limit Result Sets

Always limit the number of results returned by queries to prevent memory issues and improve performance.

```python
# Good practice
results = db_manager.search_attractions(limit=10, offset=0)

# Bad practice - no limit
results = db_manager.execute_postgres_query("SELECT * FROM attractions")  # Don't do this
```

### Handle Query Errors

Always handle errors when executing queries and provide appropriate fallbacks.

```python
try:
    results = db_manager.search_attractions("pyramid")
    if not results:
        # Handle empty results
        results = []
except Exception as e:
    logger.error(f"Error searching attractions: {e}")
    # Provide fallback
    results = []
```

## Performance Optimization

### Use Caching

Use caching for frequently accessed data to reduce database load and improve response times.

```python
# Check cache first
cached_result = db_manager.query_cache.get_record("attractions", attraction_id)
if cached_result is not None:
    return cached_result

# Cache miss, get from database
result = db_manager.get_attraction(attraction_id)

# Cache the result if found
if result:
    db_manager.query_cache.set_record("attractions", attraction_id, result)
```

### Use Query Batching

Use query batching for bulk operations to reduce the number of round trips to the database.

```python
# Create a batch executor
with db_manager.create_batch_executor() as batch:
    # Add multiple operations
    for i in range(100):
        batch.add_insert(
            table="attractions",
            data={
                "id": f"attraction_id_{i}",
                "name": f"Attraction Name {i}"
            }
        )
    # Operations are automatically executed when exiting the context
```

### Analyze Slow Queries

Regularly analyze slow queries to identify performance issues and optimize them.

```python
# Analyze slow queries
analysis = db_manager.analyze_slow_queries()

# Log suggestions
for suggestion in analysis["suggestions"]:
    logger.info(f"Query optimization suggestion: {suggestion}")

# Implement suggested indexes
for table, indexes in analysis["indexes"].items():
    logger.info(f"Suggested indexes for table {table}:")
    for index in indexes:
        logger.info(f"  {index}")
```

### Use Appropriate Indexes

Ensure that tables have appropriate indexes for frequently queried columns.

```sql
-- Example indexes for attractions table
CREATE INDEX idx_attractions_type_id ON attractions (type_id);
CREATE INDEX idx_attractions_city_id ON attractions (city_id);
CREATE INDEX idx_attractions_region_id ON attractions (region_id);
CREATE INDEX idx_attractions_name_en ON attractions ((name->>'en'));
```

### Optimize Vector Search

Use the optimized vector search methods for semantic queries, and consider adding specialized vector indexes for large tables.

```sql
-- Example HNSW index for attractions table
CREATE INDEX idx_attractions_embedding_hnsw ON attractions USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=64);
```

## Data Access Patterns

### Use Specialized Methods

Use specialized methods (get_attraction, search_attractions, etc.) for complex operations that require specific logic.

```python
# Good practice - uses specialized method with caching and error handling
attraction = db_manager.get_attraction("attraction_id")

# Less optimal - generic method without specialized logic
attraction = db_manager.generic_get("attractions", "attraction_id")
```

### Use Generic Methods for Simple Operations

Use generic methods (generic_get, generic_search, etc.) for simple operations on tables without specialized methods.

```python
# Good practice for tables without specialized methods
event = db_manager.generic_get("events", "event_id")
```

### Use Vector Search for Semantic Queries

Use vector search methods for semantic queries that require understanding of natural language.

```python
# Get embedding for a query
embedding = db_manager.get_embedding("What are the best historical sites in Egypt?")

# Search attractions by vector similarity
attractions = db_manager.vector_search_attractions(embedding, limit=5)
```

### Use Text Search for Keyword Queries

Use text search methods for keyword queries that don't require semantic understanding.

```python
# Search by text
attractions = db_manager.search_attractions("pyramid", limit=5)
```

## Error Handling

### Check Return Values

Always check the return values of database methods to handle errors appropriately.

```python
# Check for None (get methods)
attraction = db_manager.get_attraction("attraction_id")
if attraction is None:
    # Handle not found or error
    logger.warning(f"Attraction not found: attraction_id")
    return None

# Check for empty list (search methods)
attractions = db_manager.search_attractions("pyramid")
if not attractions:
    # Handle no results or error
    logger.warning(f"No attractions found for query: pyramid")
    return []
```

### Use Try-Except Blocks

Use try-except blocks to catch and handle database errors.

```python
try:
    attraction = db_manager.get_attraction("attraction_id")
    return attraction
except Exception as e:
    logger.error(f"Error getting attraction: {e}")
    return None
```

### Log Database Errors

Log database errors with sufficient context to help with debugging.

```python
try:
    attraction = db_manager.get_attraction("attraction_id")
    return attraction
except Exception as e:
    logger.error(f"Error getting attraction {attraction_id}: {e}", exc_info=True)
    return None
```

## Data Validation

### Validate Input Data

Validate input data before passing it to database methods.

```python
def get_attraction(attraction_id):
    # Validate input
    if not attraction_id or not isinstance(attraction_id, str):
        logger.error(f"Invalid attraction ID: {attraction_id}")
        return None
    
    # Get attraction
    return db_manager.get_attraction(attraction_id)
```

### Sanitize User Input

Sanitize user input before using it in database queries.

```python
def search_attractions_by_name(name):
    # Sanitize input
    name = name.strip()
    if not name:
        return []
    
    # Search attractions
    return db_manager.search_attractions(name)
```

### Validate Output Data

Validate data returned from the database before using it.

```python
attraction = db_manager.get_attraction("attraction_id")
if attraction and "name" in attraction and attraction["name"]:
    # Use attraction name
    name = attraction["name"]
else:
    # Handle missing or invalid data
    name = "Unknown Attraction"
```

## Monitoring and Logging

### Monitor Database Performance

Monitor database performance metrics to identify issues and optimize queries.

```python
# Get database metrics
metrics = db_manager.get_metrics()
logger.info(f"Database metrics: {metrics}")

# Log slow queries
slow_queries = db_manager.query_analyzer.get_slow_queries()
for query in slow_queries:
    logger.warning(f"Slow query: {query['query']} ({query['duration_ms']:.2f}ms)")
```

### Log Database Operations

Log database operations with appropriate log levels to help with debugging and monitoring.

```python
# Debug level for detailed query information
logger.debug(f"Executing query: {query} with params: {params}")

# Info level for important operations
logger.info(f"Creating new attraction: {attraction_id}")

# Warning level for potential issues
logger.warning(f"Slow query detected: {query} ({duration_ms:.2f}ms)")

# Error level for errors
logger.error(f"Error executing query: {e}")
```

### Monitor Connection Pool

Monitor the connection pool to ensure it's functioning properly.

```python
# Get connection pool metrics
pool_metrics = db_manager.pool_metrics
logger.info(f"Connection pool metrics: {pool_metrics}")

# Check for connection leaks
if pool_metrics["active_connections"] > pool_metrics["max_connections"] * 0.8:
    logger.warning(f"Connection pool nearing capacity: {pool_metrics['active_connections']}/{pool_metrics['max_connections']}")
```

## Summary

Following these best practices will help you use the database manager effectively and efficiently. Remember to:

1. Use a single database manager instance
2. Use parameterized queries
3. Use transactions for multiple operations
4. Use caching for frequently accessed data
5. Use query batching for bulk operations
6. Analyze and optimize slow queries
7. Use appropriate indexes
8. Handle errors appropriately
9. Validate input and output data
10. Monitor database performance
