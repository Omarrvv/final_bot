# Database Usage Examples

This document provides practical examples of using the database manager in the Egypt Tourism Chatbot.

## Basic Usage

### Initialization and Connection

```python
from src.knowledge.database import DatabaseManager

# Initialize the database manager
db_manager = DatabaseManager()

# Check if connected
if db_manager.is_connected():
    print("Connected to PostgreSQL")
else:
    print("Not connected to PostgreSQL")
    db_manager.connect()

# Using context manager (recommended)
with DatabaseManager() as db_manager:
    # Use db_manager here
    # Connections are automatically closed when exiting the context
```

### Simple Queries

```python
# Execute a simple query
results = db_manager.execute_postgres_query(
    "SELECT * FROM attractions LIMIT 10",
    fetchall=True
)

# Print results
for result in results:
    print(f"Attraction: {result['name']}")

# Execute a query with parameters
result = db_manager.execute_postgres_query(
    "SELECT * FROM attractions WHERE id = %s",
    ("attraction_id",),
    fetchall=False
)

if result:
    print(f"Found attraction: {result['name']}")
else:
    print("Attraction not found")
```

### Redis Commands

```python
# Set a value in Redis
db_manager.execute_redis_command("SET", "key", "value")

# Get a value from Redis
value = db_manager.execute_redis_command("GET", "key")
print(f"Value: {value}")

# Set a value with expiration
db_manager.execute_redis_command("SETEX", "key", 3600, "value")  # Expires in 1 hour

# Delete a key
db_manager.execute_redis_command("DEL", "key")
```

## Working with Attractions

### Get Attraction by ID

```python
# Get attraction by ID
attraction = db_manager.get_attraction("attraction_id")

if attraction:
    print(f"Found attraction: {attraction['name']}")
    print(f"Description: {attraction['description']}")
    print(f"Location: {attraction['city']}, {attraction['region']}")
else:
    print("Attraction not found")
```

### Search Attractions

```python
# Search attractions by text
attractions = db_manager.search_attractions("pyramid", limit=5)
print(f"Found {len(attractions)} attractions matching 'pyramid'")

# Search attractions by filters
attractions = db_manager.search_attractions(
    filters={"type_id": "historical", "city_id": "cairo"},
    limit=10,
    offset=0,
    language="en"
)
print(f"Found {len(attractions)} historical attractions in Cairo")

# Search attractions with combined text and filters
attractions = db_manager.search_attractions(
    query="temple",
    filters={"region_id": "luxor"},
    limit=10,
    offset=0,
    language="en"
)
print(f"Found {len(attractions)} temples in Luxor region")
```

### Vector Search Attractions

```python
# Get embedding for a query
embedding = db_manager.get_embedding("What are the best pyramids to visit?")

# Search attractions by vector similarity
attractions = db_manager.vector_search_attractions(embedding, limit=5)
print(f"Found {len(attractions)} attractions similar to the query")

# Print results with similarity scores
for attraction in attractions:
    print(f"Attraction: {attraction['name']} (Similarity: {attraction['similarity']:.2f})")

# Search with filters
attractions = db_manager.vector_search_attractions(
    embedding,
    filters={"type_id": "historical"},
    limit=10
)
print(f"Found {len(attractions)} historical attractions similar to the query")
```

## Working with Restaurants

### Get Restaurant by ID

```python
# Get restaurant by ID
restaurant = db_manager.get_restaurant("restaurant_id")

if restaurant:
    print(f"Found restaurant: {restaurant['name']}")
    print(f"Cuisine: {restaurant['cuisine_id']}")
    print(f"Price Range: {restaurant['price_range']}")
else:
    print("Restaurant not found")
```

### Search Restaurants

```python
# Search restaurants by text
restaurants = db_manager.search_restaurants("seafood", limit=5)
print(f"Found {len(restaurants)} restaurants matching 'seafood'")

# Search restaurants by filters
restaurants = db_manager.search_restaurants(
    filters={"cuisine_id": "egyptian", "city_id": "cairo"},
    limit=10,
    offset=0,
    language="en"
)
print(f"Found {len(restaurants)} Egyptian restaurants in Cairo")

# Search restaurants with price range
restaurants = db_manager.search_restaurants(
    filters={"price_range": "moderate"},
    limit=10,
    offset=0,
    language="en"
)
print(f"Found {len(restaurants)} moderately priced restaurants")
```

### Vector Search Restaurants

```python
# Get embedding for a query
embedding = db_manager.get_embedding("What are the best seafood restaurants in Cairo?")

# Search restaurants by vector similarity
restaurants = db_manager.vector_search_restaurants(embedding, limit=5)
print(f"Found {len(restaurants)} restaurants similar to the query")

# Search with filters
restaurants = db_manager.vector_search_restaurants(
    embedding,
    filters={"cuisine_id": "seafood"},
    limit=10
)
print(f"Found {len(restaurants)} seafood restaurants similar to the query")
```

## Working with Accommodations

### Get Accommodation by ID

```python
# Get accommodation by ID
accommodation = db_manager.get_accommodation("accommodation_id")

if accommodation:
    print(f"Found accommodation: {accommodation['name']}")
    print(f"Type: {accommodation['type_id']}")
    print(f"Price Range: {accommodation['price_min']} - {accommodation['price_max']}")
else:
    print("Accommodation not found")
```

### Search Accommodations

```python
# Search accommodations by text
accommodations = db_manager.search_accommodations("luxury", limit=5)
print(f"Found {len(accommodations)} accommodations matching 'luxury'")

# Search accommodations by filters
accommodations = db_manager.search_accommodations(
    filters={"type_id": "hotel", "city_id": "cairo"},
    limit=10,
    offset=0,
    language="en"
)
print(f"Found {len(accommodations)} hotels in Cairo")

# Search accommodations with price range
accommodations = db_manager.search_accommodations(
    filters={"price_min": 100, "price_max": 300},
    limit=10,
    offset=0,
    language="en"
)
print(f"Found {len(accommodations)} accommodations in the price range $100-$300")
```

## Generic CRUD Operations

### Generic Get

```python
# Get a record from a specific table
record = db_manager.generic_get("attractions", "attraction_id", ["name", "description", "data"])

if record:
    print(f"Found record: {record['name']}")
else:
    print("Record not found")
```

### Generic Search

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
print(f"Found {len(records)} museums")
```

### Generic Create

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

if record_id:
    print(f"Created record with ID: {record_id}")
else:
    print("Failed to create record")
```

### Generic Update

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

if success:
    print("Record updated successfully")
else:
    print("Failed to update record")
```

### Generic Delete

```python
# Delete a record from a specific table
success = db_manager.generic_delete("attractions", "attraction_id")

if success:
    print("Record deleted successfully")
else:
    print("Failed to delete record")
```

## Transactions

### Using Transactions

```python
# Using transactions for multiple operations
with db_manager.transaction() as cursor:
    # Insert a new attraction
    cursor.execute(
        "INSERT INTO attractions (id, name, type_id, city_id, region_id) VALUES (%s, %s, %s, %s, %s)",
        ("attraction_id", "Attraction Name", "museum", "cairo", "cairo")
    )
    
    # Insert tags for the attraction
    cursor.execute(
        "INSERT INTO attraction_tags (attraction_id, tag_id) VALUES (%s, %s)",
        ("attraction_id", "historical")
    )
    
    cursor.execute(
        "INSERT INTO attraction_tags (attraction_id, tag_id) VALUES (%s, %s)",
        ("attraction_id", "museum")
    )
    
    # If any of these operations fail, the entire transaction is rolled back
```

## Query Optimization

### Analyzing Slow Queries

```python
# Analyze slow queries
analysis = db_manager.analyze_slow_queries()

# Print slow queries
print("Slow Queries:")
for i, query in enumerate(analysis["slow_queries"]):
    print(f"{i+1}. {query['query']} ({query['duration_ms']:.2f}ms)")

# Print suggestions
print("\nSuggestions:")
for suggestion in analysis["suggestions"]:
    print(f"- {suggestion}")

# Print index suggestions
print("\nIndex Suggestions:")
for table, indexes in analysis["indexes"].items():
    print(f"Table: {table}")
    for index in indexes:
        print(f"- {index}")
```

### Using Query Batching

```python
# Create a batch executor
batch = db_manager.create_batch_executor(
    batch_size=100,
    auto_execute=False
)

# Add insert operations
for i in range(10):
    batch.add_insert(
        table="attractions",
        data={
            "id": f"attraction_id_{i}",
            "name": {"en": f"Attraction Name {i}", "ar": f"اسم الجذب {i}"},
            "type_id": "museum",
            "city_id": "cairo",
            "region_id": "cairo"
        }
    )

# Add update operations
for i in range(5):
    batch.add_update(
        table="attractions",
        record_id=f"attraction_id_{i}",
        data={
            "name": {"en": f"Updated Attraction Name {i}", "ar": f"اسم الجذب المحدث {i}"}
        }
    )

# Execute all operations
batch.execute_all()

# Using context manager
with db_manager.create_batch_executor() as batch:
    # Add operations
    batch.add_insert(
        table="attractions",
        data={
            "id": "attraction_id",
            "name": {"en": "Attraction Name", "ar": "اسم الجذب"},
            "type_id": "museum",
            "city_id": "cairo",
            "region_id": "cairo"
        }
    )
    # Operations are automatically executed when exiting the context
```

## Caching

### Using Vector Cache

```python
# Get the vector cache
vector_cache = db_manager.vector_cache

# Get vector search results from cache
results = vector_cache.get_vector_search_results(
    table_name="attractions",
    embedding=embedding,
    filters={"type_id": "museum"},
    limit=10
)

if results:
    print(f"Cache hit! Found {len(results)} results")
else:
    print("Cache miss")
    
    # Perform the search
    results = db_manager.vector_search_attractions(
        embedding,
        filters={"type_id": "museum"},
        limit=10
    )
    
    # Cache the results
    vector_cache.set_vector_search_results(
        table_name="attractions",
        embedding=embedding,
        results=results,
        filters={"type_id": "museum"},
        limit=10
    )

# Invalidate cache entries for a table
vector_cache.invalidate_table("attractions")
```

### Using Query Cache

```python
# Get the query cache
query_cache = db_manager.query_cache

# Get search results from cache
results = query_cache.get_search_results(
    table_name="attractions",
    query={"name": "pyramid"},
    filters={"type_id": "museum"},
    limit=10,
    offset=0,
    language="en"
)

if results:
    print(f"Cache hit! Found {len(results)} results")
else:
    print("Cache miss")
    
    # Perform the search
    results = db_manager.search_attractions(
        query="pyramid",
        filters={"type_id": "museum"},
        limit=10,
        offset=0,
        language="en"
    )
    
    # Cache the results
    query_cache.set_search_results(
        table_name="attractions",
        results=results,
        query={"name": "pyramid"},
        filters={"type_id": "museum"},
        limit=10,
        offset=0,
        language="en"
    )

# Invalidate cache entries for a table
query_cache.invalidate_table("attractions")
```
