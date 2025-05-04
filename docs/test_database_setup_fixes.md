# Test Database Setup Fixes

This document outlines the changes made to fix issues with the test database setup in the Egypt Tourism Chatbot project.

## Issues Identified

1. **Async/Sync Mismatch**: The database fixtures were synchronous but needed to be async to properly handle async database operations.
2. **Schema Mismatch**: The test fixtures were not creating tables with the correct schema that matched what the code expected.
3. **Mock Data Issues**: The mock data being inserted did not match the expected schema in some cases.
4. **Connection Handling**: There were issues with how connections were managed in the test fixtures.

## Changes Made

### 1. Updated Database Fixtures to Use Async/Await

- Changed `initialized_db_manager` fixture in `conftest.py` to use `@pytest_asyncio.fixture` instead of `@pytest.fixture`
- Made the fixture function `async` and added proper `await` calls for async operations
- Added proper error handling and connection cleanup

```python
@pytest_asyncio.fixture
async def initialized_db_manager():
    """Fixture that provides a DatabaseManager with properly initialized tables."""
    # Implementation...
    try:
        # Setup code...
        yield db_manager
    finally:
        # Ensure connection is closed properly
        await db_manager.close() if hasattr(db_manager.close, '__await__') else db_manager.close()
```

### 2. Improved Schema Verification and Initialization

- Added code to verify that tables exist with the expected schema
- Added fallback to initialize the schema if tables don't exist
- Ensured that the schema matches what the code expects

```python
# First verify that the tables exist with the expected schema
with conn:
    with conn.cursor() as cursor:
        # Check if tables exist
        tables = ["users", "cities", "attractions", "restaurants", "accommodations", "regions"]
        for table in tables:
            cursor.execute(f"SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = '{table}')")
            if not cursor.fetchone()[0]:
                # If table doesn't exist, we need to initialize the schema
                from tests.setup_test_env import initialize_postgres_test_schema
                initialize_postgres_test_schema()
                break
```

### 3. Enhanced Database Schema Initialization

- Updated `initialize_postgres_test_schema` in `setup_test_env.py` to accept an optional connection parameter
- Added proper connection handling and cleanup
- Added missing tables and columns to match the expected schema
- Added indexes for common query patterns

```python
def initialize_postgres_test_schema(conn=None):
    """
    Initialize the PostgreSQL test database schema.
    
    Args:
        conn: Optional existing database connection. If not provided, a new connection
             will be created using the POSTGRES_URI environment variable.
    
    Returns:
        bool: True if initialization was successful
    """
    # Implementation...
```

### 4. Fixed Redis Client Tests

- Updated `mock_redis_lib` fixture in `test_redis_client.py` to use `@pytest_asyncio.fixture`
- Added proper error logging for test skipping
- Ensured consistent async/await usage throughout the tests

```python
@pytest_asyncio.fixture
async def mock_redis_lib():
    """Fixture for a mocked underlying redis library client (async version)."""
    # Implementation...
```

### 5. Added Comprehensive Tests

- Created a new test file `test_db_setup.py` to verify that the database setup is working correctly
- Added tests for database manager initialization, table existence, test data insertion, schema matching, geospatial data, and CRUD operations

```python
async def test_tables_exist(initialized_db_manager):
    """Test that all required tables exist in the database."""
    # List of tables that should exist
    required_tables = [
        "users", "cities", "attractions", "restaurants", 
        "accommodations", "regions", "sessions"
    ]
    
    # Check each table
    for table in required_tables:
        result = initialized_db_manager.execute_query(
            f"SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = '{table}')"
        )
        assert result[0]['exists'], f"Table {table} does not exist"
```

## Benefits of These Changes

1. **Improved Reliability**: Tests now properly set up the database environment, reducing flaky tests.
2. **Better Error Handling**: Added proper error handling and logging for database operations.
3. **Consistent Async Usage**: Ensured consistent use of async/await throughout the test fixtures.
4. **Schema Verification**: Added checks to ensure the database schema matches what the code expects.
5. **Comprehensive Testing**: Added tests to verify that the database setup is working correctly.

## Future Considerations

1. **Database Migrations**: Consider implementing a proper database migration system for test environments.
2. **Test Data Factory**: Create a factory pattern for generating test data to make tests more maintainable.
3. **In-Memory Database Option**: Consider adding support for in-memory databases for faster tests.
4. **Test Isolation**: Improve test isolation by using separate database schemas for different test suites.
