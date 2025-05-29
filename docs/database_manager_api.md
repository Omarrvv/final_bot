# Database Manager API Reference

This document provides a comprehensive reference for the DatabaseManager class in the Egypt Tourism Chatbot.

## Overview

The `DatabaseManager` class is responsible for managing database connections and providing methods for interacting with the database. It supports both PostgreSQL and Redis databases, and provides a variety of methods for querying, updating, and managing data.

## Initialization

```python
from src.knowledge.database import DatabaseManager

# Initialize the database manager
db_manager = DatabaseManager()
```

## Core Database Methods

### Connection Management

#### connect()

Establishes connections to PostgreSQL and Redis databases.

```python
db_manager.connect()
```

#### close()

Closes all database connections.

```python
db_manager.close()
```

#### is_connected()

Checks if the database manager is connected to PostgreSQL.

```python
if db_manager.is_connected():
    print("Connected to PostgreSQL")
else:
    print("Not connected to PostgreSQL")
```

### Query Execution

#### execute_postgres_query(query, params=None, fetchall=True)

Executes a PostgreSQL query with optional parameters.

**Parameters:**
- `query` (str): SQL query to execute
- `params` (tuple, optional): Parameters for the query
- `fetchall` (bool): Whether to fetch all results or just one

**Returns:**
- For SELECT queries with `fetchall=True`: List of dictionaries, each representing a row
- For SELECT queries with `fetchall=False`: Dictionary representing a single row
- For INSERT/UPDATE/DELETE queries: Number of affected rows

```python
# Fetch all rows
results = db_manager.execute_postgres_query(
    "SELECT * FROM attractions WHERE type_id = %s",
    ("museum",),
    fetchall=True
)

# Fetch a single row
result = db_manager.execute_postgres_query(
    "SELECT * FROM attractions WHERE id = %s",
    ("attraction_id",),
    fetchall=False
)

# Insert a row
affected_rows = db_manager.execute_postgres_query(
    "INSERT INTO attractions (id, name) VALUES (%s, %s)",
    ("attraction_id", "Attraction Name"),
    fetchall=False
)
```

#### execute_redis_command(command, *args)

Executes a Redis command with optional arguments.

**Parameters:**
- `command` (str): Redis command to execute
- `*args`: Arguments for the command

**Returns:**
- Result of the Redis command

```python
# Set a value
db_manager.execute_redis_command("SET", "key", "value")

# Get a value
value = db_manager.execute_redis_command("GET", "key")

# Delete a key
db_manager.execute_redis_command("DEL", "key")
```

### Transaction Management

#### transaction()

Creates a transaction context manager for executing multiple queries in a transaction.

```python
with db_manager.transaction() as cursor:
    cursor.execute("INSERT INTO attractions (id, name) VALUES (%s, %s)", ("attraction_id", "Attraction Name"))
    cursor.execute("INSERT INTO attractions (id, name) VALUES (%s, %s)", ("attraction_id2", "Attraction Name 2"))
```

## Data Access Methods

### Attraction Methods

#### get_attraction(attraction_id)

Gets an attraction by ID.

**Parameters:**
- `attraction_id` (str): ID of the attraction

**Returns:**
- Dictionary containing attraction data or None if not found

```python
attraction = db_manager.get_attraction("attraction_id")
if attraction:
    print(f"Found attraction: {attraction['name']}")
else:
    print("Attraction not found")
```

#### search_attractions(query=None, filters=None, limit=10, offset=0, language="en")

Searches attractions based on query or filters.

**Parameters:**
- `query` (dict or str): Dictionary of search criteria or text query string
- `filters` (dict): Additional filters to apply
- `limit` (int): Maximum number of results to return
- `offset` (int): Offset for pagination
- `language` (str): Language code (en, ar)

**Returns:**
- List of dictionaries, each representing an attraction

```python
# Search by text
attractions = db_manager.search_attractions("pyramid", limit=5)

# Search by filters
attractions = db_manager.search_attractions(
    filters={"type_id": "museum", "city_id": "cairo"},
    limit=10,
    offset=0,
    language="en"
)
```

#### vector_search_attractions(embedding, filters=None, limit=10)

Performs a vector search on attractions.

**Parameters:**
- `embedding` (list): Vector embedding for similarity search
- `filters` (dict, optional): Additional filters to apply
- `limit` (int): Maximum number of results to return

**Returns:**
- List of dictionaries, each representing an attraction with similarity score

```python
# Get embedding for a query
embedding = db_manager.get_embedding("What are the best pyramids to visit?")

# Search attractions by vector similarity
attractions = db_manager.vector_search_attractions(embedding, limit=5)

# Search with filters
attractions = db_manager.vector_search_attractions(
    embedding,
    filters={"type_id": "historical"},
    limit=10
)
```

### Restaurant Methods

#### get_restaurant(restaurant_id)

Gets a restaurant by ID.

**Parameters:**
- `restaurant_id` (str): ID of the restaurant

**Returns:**
- Dictionary containing restaurant data or None if not found

```python
restaurant = db_manager.get_restaurant("restaurant_id")
if restaurant:
    print(f"Found restaurant: {restaurant['name']}")
else:
    print("Restaurant not found")
```

#### search_restaurants(query=None, filters=None, limit=10, offset=0, language="en")

Searches restaurants based on query or filters.

**Parameters:**
- `query` (dict or str): Dictionary of search criteria or text query string
- `filters` (dict): Additional filters to apply
- `limit` (int): Maximum number of results to return
- `offset` (int): Offset for pagination
- `language` (str): Language code (en, ar)

**Returns:**
- List of dictionaries, each representing a restaurant

```python
# Search by text
restaurants = db_manager.search_restaurants("seafood", limit=5)

# Search by filters
restaurants = db_manager.search_restaurants(
    filters={"cuisine_id": "egyptian", "city_id": "cairo"},
    limit=10,
    offset=0,
    language="en"
)
```

#### vector_search_restaurants(embedding, filters=None, limit=10)

Performs a vector search on restaurants.

**Parameters:**
- `embedding` (list): Vector embedding for similarity search
- `filters` (dict, optional): Additional filters to apply
- `limit` (int): Maximum number of results to return

**Returns:**
- List of dictionaries, each representing a restaurant with similarity score

```python
# Get embedding for a query
embedding = db_manager.get_embedding("What are the best seafood restaurants in Cairo?")

# Search restaurants by vector similarity
restaurants = db_manager.vector_search_restaurants(embedding, limit=5)

# Search with filters
restaurants = db_manager.vector_search_restaurants(
    embedding,
    filters={"cuisine_id": "seafood"},
    limit=10
)
```

### Accommodation Methods

#### get_accommodation(accommodation_id)

Gets an accommodation by ID.

**Parameters:**
- `accommodation_id` (str): ID of the accommodation

**Returns:**
- Dictionary containing accommodation data or None if not found

```python
accommodation = db_manager.get_accommodation("accommodation_id")
if accommodation:
    print(f"Found accommodation: {accommodation['name']}")
else:
    print("Accommodation not found")
```

#### search_accommodations(query=None, filters=None, limit=10, offset=0, language="en")

Searches accommodations based on query or filters.

**Parameters:**
- `query` (dict or str): Dictionary of search criteria or text query string
- `filters` (dict): Additional filters to apply
- `limit` (int): Maximum number of results to return
- `offset` (int): Offset for pagination
- `language` (str): Language code (en, ar)

**Returns:**
- List of dictionaries, each representing an accommodation

```python
# Search by text
accommodations = db_manager.search_accommodations("luxury", limit=5)

# Search by filters
accommodations = db_manager.search_accommodations(
    filters={"type_id": "hotel", "city_id": "cairo"},
    limit=10,
    offset=0,
    language="en"
)
```

## Vector Search Methods

### vector_search(table_name, embedding, filters=None, limit=10)

Performs a vector search on a specified table.

**Parameters:**
- `table_name` (str): Name of the table to search
- `embedding` (list): Vector embedding for similarity search
- `filters` (dict, optional): Additional filters to apply
- `limit` (int): Maximum number of results to return

**Returns:**
- List of dictionaries, each representing a row with similarity score

```python
# Get embedding for a query
embedding = db_manager.get_embedding("What are the best historical sites in Egypt?")

# Search a specific table
results = db_manager.vector_search("attractions", embedding, limit=10)

# Search with filters
results = db_manager.vector_search(
    "attractions",
    embedding,
    filters={"type_id": "historical"},
    limit=10
)
```

### get_embedding(text)

Gets a vector embedding for a text string.

**Parameters:**
- `text` (str): Text to get embedding for

**Returns:**
- List of floats representing the embedding

```python
# Get embedding for a query
embedding = db_manager.get_embedding("What are the best historical sites in Egypt?")
```

## Generic CRUD Operations

### generic_get(table, record_id, jsonb_fields=None)

Gets a record by ID from a specified table.

**Parameters:**
- `table` (str): Table name
- `record_id` (str): ID of the record to retrieve
- `jsonb_fields` (list, optional): List of JSONB fields to parse

**Returns:**
- Dictionary containing record data or None if not found

```python
# Get a record from a specific table
record = db_manager.generic_get("attractions", "attraction_id", ["name", "description", "data"])
```

### generic_search(table, filters=None, limit=10, offset=0, jsonb_fields=None, language="en")

Searches records in a specified table.

**Parameters:**
- `table` (str): Table name
- `filters` (dict, optional): Dictionary of field-value pairs to filter by
- `limit` (int): Maximum number of results to return
- `offset` (int): Offset for pagination
- `jsonb_fields` (list, optional): List of JSONB fields to parse
- `language` (str): Language code (en, ar)

**Returns:**
- List of dictionaries, each representing a record

```python
# Search records in a specific table
records = db_manager.generic_search(
    "attractions",
    filters={"type_id": "museum"},
    limit=10,
    offset=0,
    jsonb_fields=["name", "description", "data"],
    language="en"
)
```

### generic_create(table, data)

Creates a record in a specified table.

**Parameters:**
- `table` (str): Table name
- `data` (dict): Dictionary of field-value pairs

**Returns:**
- ID of the created record or None if creation failed

```python
# Create a record in a specific table
record_id = db_manager.generic_create(
    "attractions",
    {
        "id": "attraction_id",
        "name": {"en": "Attraction Name", "ar": "اسم الجذب"},
        "description": {"en": "Attraction Description", "ar": "وصف الجذب"},
        "type_id": "museum",
        "city_id": "cairo",
        "region_id": "cairo"
    }
)
```

### generic_update(table, record_id, data)

Updates a record in a specified table.

**Parameters:**
- `table` (str): Table name
- `record_id` (str): ID of the record to update
- `data` (dict): Dictionary of field-value pairs to update

**Returns:**
- True if update was successful, False otherwise

```python
# Update a record in a specific table
success = db_manager.generic_update(
    "attractions",
    "attraction_id",
    {
        "name": {"en": "Updated Attraction Name", "ar": "اسم الجذب المحدث"},
        "description": {"en": "Updated Attraction Description", "ar": "وصف الجذب المحدث"}
    }
)
```

### generic_delete(table, record_id)

Deletes a record from a specified table.

**Parameters:**
- `table` (str): Table name
- `record_id` (str): ID of the record to delete

**Returns:**
- True if deletion was successful, False otherwise

```python
# Delete a record from a specific table
success = db_manager.generic_delete("attractions", "attraction_id")
```

## Query Optimization Methods

### analyze_slow_queries()

Analyzes slow queries and suggests optimizations.

**Returns:**
- Dictionary containing analysis results and optimization suggestions

```python
# Analyze slow queries
analysis = db_manager.analyze_slow_queries()

# Access the analysis results
slow_queries = analysis["slow_queries"]
plans = analysis["plans"]
suggestions = analysis["suggestions"]
indexes = analysis["indexes"]
```

### create_batch_executor(batch_size=100, auto_execute=False)

Creates a query batch executor for efficient bulk operations.

**Parameters:**
- `batch_size` (int): Maximum number of operations in a batch
- `auto_execute` (bool): Whether to automatically execute batches when they reach batch_size

**Returns:**
- QueryBatch: Batch executor instance

```python
# Create a batch executor
batch = db_manager.create_batch_executor(
    batch_size=100,
    auto_execute=False
)

# Add operations to the batch
batch.add_insert(
    table="attractions",
    data={"id": "attraction_id", "name": "Attraction Name"}
)

# Execute all operations
batch.execute_all()
```

## Caching Methods

### get_vector_cache()

Gets the vector cache instance.

**Returns:**
- VectorTieredCache: Vector cache instance

```python
# Get the vector cache
vector_cache = db_manager.get_vector_cache()

# Use the vector cache
results = vector_cache.get_vector_search_results(
    table_name="attractions",
    embedding=embedding,
    filters={"type_id": "museum"},
    limit=10
)
```

### get_query_cache()

Gets the query cache instance.

**Returns:**
- QueryCache: Query cache instance

```python
# Get the query cache
query_cache = db_manager.get_query_cache()

# Use the query cache
results = query_cache.get_search_results(
    table_name="attractions",
    query={"name": "pyramid"},
    filters={"type_id": "museum"},
    limit=10,
    offset=0,
    language="en"
)
```

## Error Handling

The DatabaseManager class provides standardized error handling for all database operations. If an error occurs, the method will return None or an empty list, depending on the context, and log the error.

```python
# Error handling for get methods
result = db_manager.get_attraction("non_existent_id")
if result is None:
    print("Attraction not found or an error occurred")

# Error handling for search methods
results = db_manager.search_attractions("invalid query")
if not results:
    print("No results found or an error occurred")
```

## Best Practices

1. **Use connection pooling**: The DatabaseManager class uses connection pooling to efficiently manage database connections. Avoid creating multiple instances of the DatabaseManager class.

2. **Use transactions for multiple operations**: Use the transaction context manager for executing multiple queries in a transaction.

3. **Use generic methods for simple operations**: Use the generic_get, generic_search, generic_create, generic_update, and generic_delete methods for simple operations on any table.

4. **Use specialized methods for complex operations**: Use the specialized methods (get_attraction, search_attractions, etc.) for complex operations that require specific logic.

5. **Use vector search for semantic queries**: Use vector search methods for semantic queries that require understanding of natural language.

6. **Use query batching for bulk operations**: Use the create_batch_executor method to create a batch executor for efficient bulk operations.

7. **Use caching for frequently accessed data**: Use the vector_cache and query_cache for caching frequently accessed data.

8. **Handle errors appropriately**: Check the return value of methods to handle errors appropriately.

9. **Close connections when done**: Call the close method when done with the DatabaseManager to release database connections.

10. **Monitor slow queries**: Use the analyze_slow_queries method to identify and optimize slow queries.
