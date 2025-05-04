# Database Initialization Documentation

## Overview

This document describes the improvements made to the database initialization process for the Egypt Tourism Chatbot. The changes address issues with table creation order, foreign key constraints, and error handling.

## Changes Made

### 1. Improved Table Creation Order

The original implementation created tables in a fixed order, which could lead to foreign key constraint violations if a table was created before its dependencies. The new implementation uses a topological sort algorithm to ensure that tables are created in the correct order based on their dependencies.

### 2. Fixed Foreign Key Issues

The original implementation had issues with the `user_id` column and foreign key constraints:

- The `user_id` column was created without a foreign key constraint
- Foreign key constraints were not properly defined
- Tables with foreign keys were sometimes created before the referenced tables

The new implementation:

- Ensures that the `users` table is created first
- Adds proper foreign key constraints to the `user_id` column
- Uses `ON DELETE SET NULL` for foreign keys to handle user deletion gracefully

### 3. Improved Error Handling

The original implementation had limited error handling for when columns already exist or when there are issues with table creation. The new implementation:

- Uses `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` for adding columns
- Wraps each table and index creation in a try-except block
- Provides detailed error messages for troubleshooting
- Uses transactions to ensure atomicity

### 4. Added Testing

A comprehensive test suite has been added to verify that the database can be initialized from scratch correctly:

- Tests for topological sorting of tables
- Tests for table creation
- Tests for foreign key constraints
- Tests for index creation

## Implementation Details

### Topological Sort

The topological sort algorithm ensures that tables are created in the correct order based on their dependencies:

1. Start with a list of all tables and their dependencies
2. Find tables with no unresolved dependencies
3. Add these tables to the result and remove them from the list
4. Repeat until all tables are processed or no progress can be made

This ensures that referenced tables are always created before tables with foreign keys.

### Table Definitions

Table definitions are now stored in a dictionary with dependencies:

```python
TABLE_DEFINITIONS = {
    "users": {
        "sql": "CREATE TABLE IF NOT EXISTS users ...",
        "dependencies": [],
        "indexes": [...]
    },
    "attractions": {
        "sql": "CREATE TABLE IF NOT EXISTS attractions ...",
        "dependencies": ["users"],
        "indexes": [...]
    },
    ...
}
```

This makes it easy to add, remove, or modify tables without changing the core initialization logic.

### Foreign Key Constraints

Foreign key constraints are now added after table creation using PL/pgSQL blocks:

```sql
CREATE TABLE IF NOT EXISTS attractions (
    ...
    user_id TEXT
    ...
);

-- Add foreign key if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'attractions_user_id_fkey' AND conrelid = 'attractions'::regclass
    ) THEN
        ALTER TABLE attractions ADD CONSTRAINT attractions_user_id_fkey
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;
    END IF;
EXCEPTION
    WHEN undefined_table THEN
        -- Table doesn't exist yet, which is fine
    WHEN undefined_column THEN
        -- Column doesn't exist yet, which is fine
    WHEN others THEN
        RAISE;
END $$;
```

This approach:

1. Creates the table with the column but without the foreign key constraint
2. Checks if the constraint already exists
3. Adds the constraint if it doesn't exist
4. Handles errors gracefully

The `ON DELETE SET NULL` clause ensures that if a user is deleted, the `user_id` column in related tables is set to NULL rather than causing a constraint violation.

### Error Handling

Error handling has been improved at multiple levels:

- Each table is created in its own transaction
- Each index is created in its own transaction
- Each operation is wrapped in a try-except block
- Failures in one table or index don't prevent others from being created
- Detailed error messages are logged for troubleshooting

This approach makes the database initialization process much more robust, as it can continue even if some operations fail.

## Usage

The new implementation is used by the `DatabaseManager._create_postgres_tables` method:

```python
def _create_postgres_tables(self):
    """Create required tables in PostgreSQL if they don't exist."""
    from src.knowledge.database_init import create_postgres_tables

    conn = self._get_pg_connection()
    if not conn:
        logger.error("Failed to get PostgreSQL connection for table creation")
        raise Exception("Failed to get PostgreSQL connection for table creation")

    try:
        create_postgres_tables(conn, self.vector_dimension)
        logger.info("Tables and indexes created successfully")
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Failed to create PostgreSQL tables: {str(e)}")
        raise
    finally:
        if conn:
            self._return_pg_connection(conn)
```

## Testing

The new implementation is tested by the `test_database_init.py` file, which includes tests for:

- Topological sorting of tables
- Table creation
- Foreign key constraints
- Index creation

These tests ensure that the database can be initialized from scratch correctly and that foreign key constraints work as expected.

## Future Considerations

In the future, consider:

1. Adding support for database migrations
2. Implementing schema versioning
3. Adding more validation for schema consistency
4. Creating a command-line tool for database initialization and migration
