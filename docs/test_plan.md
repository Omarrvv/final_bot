# Test Plan for Database Manager

This document outlines the test plan for the database manager in the Egypt Tourism Chatbot.

## Test Categories

The test plan is divided into the following categories:

1. **Unit Tests**: Test individual components in isolation
2. **Integration Tests**: Test interactions between components
3. **Performance Tests**: Test performance under various conditions
4. **Stress Tests**: Test behavior under high load
5. **Regression Tests**: Test that previously fixed issues remain fixed

## Unit Tests

### DatabaseManager Tests

- Test initialization
- Test connection management
- Test query execution
- Test transaction management
- Test error handling

### TieredCache Tests

- Test initialization
- Test get/set operations
- Test invalidation
- Test fallback mechanism
- Test serialization/deserialization

### VectorTieredCache Tests

- Test initialization
- Test vector search caching
- Test embedding handling
- Test invalidation
- Test fallback mechanism

### QueryCache Tests

- Test initialization
- Test query result caching
- Test search result caching
- Test record caching
- Test invalidation

### QueryAnalyzer Tests

- Test initialization
- Test query recording
- Test slow query identification
- Test query plan analysis
- Test index suggestions

### QueryBatch Tests

- Test initialization
- Test batch operations
- Test batch execution
- Test error handling
- Test context manager

## Integration Tests

### Database Connection Tests

- Test PostgreSQL connection
- Test Redis connection
- Test connection pooling
- Test connection recovery

### Cache Integration Tests

- Test cache integration with database operations
- Test cache invalidation on data changes
- Test cache fallback to database
- Test cache performance impact

### Query Optimization Tests

- Test query analyzer integration
- Test slow query identification in real queries
- Test query plan analysis with real queries
- Test index suggestions with real database schema

### Batch Operation Tests

- Test batch operations with real database
- Test batch performance compared to individual operations
- Test batch error handling with real database
- Test batch context manager with real database

## Performance Tests

### Query Performance Tests

- Test query performance with various data sizes
- Test query performance with various query complexities
- Test query performance with various indexes
- Test query performance with various caching strategies

### Cache Performance Tests

- Test cache hit/miss performance
- Test cache performance with various data sizes
- Test cache performance with various TTLs
- Test cache performance with various serialization strategies

### Vector Search Performance Tests

- Test vector search performance with various data sizes
- Test vector search performance with various embedding dimensions
- Test vector search performance with various indexes
- Test vector search performance with various caching strategies

### Batch Operation Performance Tests

- Test batch operation performance with various batch sizes
- Test batch operation performance with various data sizes
- Test batch operation performance with various operation types
- Test batch operation performance with auto-execute enabled/disabled

## Stress Tests

### Connection Pool Stress Tests

- Test connection pool under high concurrency
- Test connection pool with connection leaks
- Test connection pool with connection timeouts
- Test connection pool recovery after failures

### Query Stress Tests

- Test query performance under high concurrency
- Test query performance with large result sets
- Test query performance with complex queries
- Test query error handling under stress

### Cache Stress Tests

- Test cache performance under high concurrency
- Test cache performance with large data sets
- Test cache performance with high invalidation rate
- Test cache fallback under Redis failure

### Vector Search Stress Tests

- Test vector search under high concurrency
- Test vector search with large embedding sets
- Test vector search with high dimensionality
- Test vector search with various distance metrics

## Test Implementation Plan

### Phase 1: Unit Tests

#### 1.1 Create Test Environment

```python
# Create a test environment with a test database
@pytest.fixture
def test_db_manager():
    # Set up test database
    db_manager = DatabaseManager(
        postgres_uri="postgresql://postgres:postgres@localhost:5432/test_db",
        redis_uri="redis://localhost:6379/1"
    )
    
    # Create test tables
    with db_manager.transaction() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_attractions (
                id TEXT PRIMARY KEY,
                name JSONB,
                description JSONB,
                type_id TEXT,
                city_id TEXT,
                region_id TEXT,
                embedding VECTOR(384)
            )
        """)
    
    yield db_manager
    
    # Clean up
    with db_manager.transaction() as cursor:
        cursor.execute("DROP TABLE IF EXISTS test_attractions")
    
    db_manager.close()
```

#### 1.2 Implement DatabaseManager Tests

```python
def test_db_manager_init(test_db_manager):
    """Test DatabaseManager initialization."""
    assert test_db_manager is not None
    assert test_db_manager.is_connected()

def test_db_manager_query(test_db_manager):
    """Test DatabaseManager query execution."""
    # Insert test data
    test_db_manager.execute_postgres_query(
        "INSERT INTO test_attractions (id, name) VALUES (%s, %s)",
        ("test_id", json.dumps({"en": "Test Attraction"}))
    )
    
    # Query test data
    result = test_db_manager.execute_postgres_query(
        "SELECT * FROM test_attractions WHERE id = %s",
        ("test_id",),
        fetchall=False
    )
    
    assert result is not None
    assert result["id"] == "test_id"
    assert json.loads(result["name"])["en"] == "Test Attraction"
```

#### 1.3 Implement Cache Tests

```python
def test_tiered_cache():
    """Test TieredCache."""
    cache = TieredCache(
        cache_prefix="test_cache",
        redis_uri="redis://localhost:6379/1",
        ttl=3600,
        max_size=100
    )
    
    # Set a value
    cache.set({"key": "test_key"}, "test_value")
    
    # Get the value
    value = cache.get({"key": "test_key"})
    
    assert value == "test_value"
    
    # Invalidate the value
    cache.invalidate("test_key")
    
    # Value should be gone
    value = cache.get({"key": "test_key"})
    
    assert value is None
```

#### 1.4 Implement Query Optimization Tests

```python
def test_query_analyzer():
    """Test QueryAnalyzer."""
    analyzer = QueryAnalyzer(
        slow_query_threshold_ms=500,
        max_queries_to_track=100
    )
    
    # Record a fast query
    analyzer.record_query(
        query="SELECT * FROM test_attractions WHERE id = %s",
        params=("test_id",),
        duration_ms=100.0,
        rows_affected=1
    )
    
    # Record a slow query
    analyzer.record_query(
        query="SELECT * FROM test_attractions",
        params=(),
        duration_ms=600.0,
        rows_affected=100
    )
    
    # Get slow queries
    slow_queries = analyzer.get_slow_queries()
    
    assert len(slow_queries) == 1
    assert slow_queries[0]["query"] == "SELECT * FROM test_attractions"
    assert slow_queries[0]["duration_ms"] == 600.0
```

### Phase 2: Integration Tests

#### 2.1 Create Integration Test Environment

```python
@pytest.fixture
def integration_db_manager():
    # Set up integration test database
    db_manager = DatabaseManager(
        postgres_uri="postgresql://postgres:postgres@localhost:5432/integration_db",
        redis_uri="redis://localhost:6379/2"
    )
    
    # Create test tables and load test data
    with db_manager.transaction() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attractions (
                id TEXT PRIMARY KEY,
                name JSONB,
                description JSONB,
                type_id TEXT,
                city_id TEXT,
                region_id TEXT,
                embedding VECTOR(384)
            )
        """)
        
        # Load test data
        for i in range(100):
            cursor.execute(
                "INSERT INTO attractions (id, name, type_id, city_id, region_id) VALUES (%s, %s, %s, %s, %s)",
                (
                    f"attraction_{i}",
                    json.dumps({"en": f"Attraction {i}", "ar": f"معلم {i}"}),
                    "museum" if i % 3 == 0 else "historical" if i % 3 == 1 else "natural",
                    "cairo" if i % 4 == 0 else "luxor" if i % 4 == 1 else "aswan" if i % 4 == 2 else "alexandria",
                    "cairo" if i % 2 == 0 else "upper_egypt"
                )
            )
    
    yield db_manager
    
    # Clean up
    with db_manager.transaction() as cursor:
        cursor.execute("DROP TABLE IF EXISTS attractions")
    
    db_manager.close()
```

#### 2.2 Implement Database Integration Tests

```python
def test_search_attractions(integration_db_manager):
    """Test searching attractions."""
    # Search by text
    attractions = integration_db_manager.search_attractions("Attraction", limit=10)
    
    assert len(attractions) == 10
    
    # Search by filters
    attractions = integration_db_manager.search_attractions(
        filters={"type_id": "museum", "city_id": "cairo"},
        limit=10
    )
    
    assert all(a["type_id"] == "museum" and a["city_id"] == "cairo" for a in attractions)
```

#### 2.3 Implement Cache Integration Tests

```python
def test_cache_integration(integration_db_manager):
    """Test cache integration with database operations."""
    # Get attraction (should cache the result)
    attraction = integration_db_manager.get_attraction("attraction_0")
    
    assert attraction is not None
    
    # Check cache
    cached_attraction = integration_db_manager.query_cache.get_record("attractions", "attraction_0")
    
    assert cached_attraction is not None
    assert cached_attraction["id"] == "attraction_0"
    
    # Update attraction
    integration_db_manager.generic_update(
        "attractions",
        "attraction_0",
        {"name": {"en": "Updated Attraction", "ar": "معلم محدث"}}
    )
    
    # Cache should be invalidated
    cached_attraction = integration_db_manager.query_cache.get_record("attractions", "attraction_0")
    
    assert cached_attraction is None
```

### Phase 3: Performance Tests

#### 3.1 Create Performance Test Environment

```python
@pytest.fixture
def performance_db_manager():
    # Set up performance test database
    db_manager = DatabaseManager(
        postgres_uri="postgresql://postgres:postgres@localhost:5432/performance_db",
        redis_uri="redis://localhost:6379/3"
    )
    
    # Create test tables and load test data
    with db_manager.transaction() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attractions (
                id TEXT PRIMARY KEY,
                name JSONB,
                description JSONB,
                type_id TEXT,
                city_id TEXT,
                region_id TEXT,
                embedding VECTOR(384)
            )
        """)
        
        # Load test data (1000 records)
        for i in range(1000):
            cursor.execute(
                "INSERT INTO attractions (id, name, type_id, city_id, region_id) VALUES (%s, %s, %s, %s, %s)",
                (
                    f"attraction_{i}",
                    json.dumps({"en": f"Attraction {i}", "ar": f"معلم {i}"}),
                    "museum" if i % 3 == 0 else "historical" if i % 3 == 1 else "natural",
                    "cairo" if i % 4 == 0 else "luxor" if i % 4 == 1 else "aswan" if i % 4 == 2 else "alexandria",
                    "cairo" if i % 2 == 0 else "upper_egypt"
                )
            )
    
    yield db_manager
    
    # Clean up
    with db_manager.transaction() as cursor:
        cursor.execute("DROP TABLE IF EXISTS attractions")
    
    db_manager.close()
```

#### 3.2 Implement Query Performance Tests

```python
def test_query_performance(performance_db_manager):
    """Test query performance."""
    # Measure query performance
    start_time = time.time()
    
    # Execute query
    results = performance_db_manager.search_attractions(
        filters={"type_id": "museum", "city_id": "cairo"},
        limit=100
    )
    
    end_time = time.time()
    duration_ms = (end_time - start_time) * 1000
    
    assert duration_ms < 100  # Query should complete in less than 100ms
    assert len(results) > 0
```

#### 3.3 Implement Cache Performance Tests

```python
def test_cache_performance(performance_db_manager):
    """Test cache performance."""
    # Clear cache
    performance_db_manager.query_cache.clear()
    
    # Measure uncached query performance
    start_time = time.time()
    
    # Execute query
    results = performance_db_manager.search_attractions(
        filters={"type_id": "museum", "city_id": "cairo"},
        limit=100
    )
    
    uncached_duration_ms = (time.time() - start_time) * 1000
    
    # Measure cached query performance
    start_time = time.time()
    
    # Execute same query (should be cached)
    results = performance_db_manager.search_attractions(
        filters={"type_id": "museum", "city_id": "cairo"},
        limit=100
    )
    
    cached_duration_ms = (time.time() - start_time) * 1000
    
    assert cached_duration_ms < uncached_duration_ms  # Cached query should be faster
    assert cached_duration_ms < 10  # Cached query should complete in less than 10ms
```

### Phase 4: Stress Tests

#### 4.1 Create Stress Test Environment

```python
@pytest.fixture
def stress_db_manager():
    # Set up stress test database
    db_manager = DatabaseManager(
        postgres_uri="postgresql://postgres:postgres@localhost:5432/stress_db",
        redis_uri="redis://localhost:6379/4"
    )
    
    # Create test tables and load test data
    with db_manager.transaction() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attractions (
                id TEXT PRIMARY KEY,
                name JSONB,
                description JSONB,
                type_id TEXT,
                city_id TEXT,
                region_id TEXT,
                embedding VECTOR(384)
            )
        """)
        
        # Load test data (10000 records)
        for i in range(10000):
            cursor.execute(
                "INSERT INTO attractions (id, name, type_id, city_id, region_id) VALUES (%s, %s, %s, %s, %s)",
                (
                    f"attraction_{i}",
                    json.dumps({"en": f"Attraction {i}", "ar": f"معلم {i}"}),
                    "museum" if i % 3 == 0 else "historical" if i % 3 == 1 else "natural",
                    "cairo" if i % 4 == 0 else "luxor" if i % 4 == 1 else "aswan" if i % 4 == 2 else "alexandria",
                    "cairo" if i % 2 == 0 else "upper_egypt"
                )
            )
    
    yield db_manager
    
    # Clean up
    with db_manager.transaction() as cursor:
        cursor.execute("DROP TABLE IF EXISTS attractions")
    
    db_manager.close()
```

#### 4.2 Implement Connection Pool Stress Tests

```python
def test_connection_pool_stress(stress_db_manager):
    """Test connection pool under high concurrency."""
    # Create multiple threads to simulate concurrent requests
    threads = []
    results = []
    
    def query_thread():
        try:
            # Execute query
            result = stress_db_manager.search_attractions(
                filters={"type_id": "museum", "city_id": "cairo"},
                limit=10
            )
            results.append(result)
        except Exception as e:
            results.append(e)
    
    # Create and start threads
    for i in range(100):
        thread = threading.Thread(target=query_thread)
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Check results
    assert all(isinstance(r, list) for r in results)  # All results should be lists
    assert all(len(r) > 0 for r in results)  # All results should have at least one item
```

#### 4.3 Implement Query Stress Tests

```python
def test_query_stress(stress_db_manager):
    """Test query performance under high load."""
    # Execute multiple queries in sequence
    start_time = time.time()
    
    for i in range(100):
        # Execute query
        results = stress_db_manager.search_attractions(
            filters={"type_id": "museum" if i % 3 == 0 else "historical" if i % 3 == 1 else "natural",
                    "city_id": "cairo" if i % 4 == 0 else "luxor" if i % 4 == 1 else "aswan" if i % 4 == 2 else "alexandria"},
            limit=10
        )
        
        assert len(results) > 0
    
    end_time = time.time()
    total_duration_ms = (end_time - start_time) * 1000
    avg_duration_ms = total_duration_ms / 100
    
    assert avg_duration_ms < 100  # Average query should complete in less than 100ms
```

## Test Execution Plan

1. **Set up test environments**:
   - Create test databases
   - Load test data
   - Configure test fixtures

2. **Run unit tests**:
   - Run tests for each component
   - Verify basic functionality
   - Fix any issues

3. **Run integration tests**:
   - Run tests for component interactions
   - Verify end-to-end functionality
   - Fix any issues

4. **Run performance tests**:
   - Run tests for query performance
   - Run tests for cache performance
   - Optimize as needed

5. **Run stress tests**:
   - Run tests for connection pool
   - Run tests for query stress
   - Fix any issues

6. **Run regression tests**:
   - Run tests for previously fixed issues
   - Verify that issues remain fixed
   - Fix any regressions

7. **Generate test reports**:
   - Generate coverage reports
   - Generate performance reports
   - Document any issues or optimizations
