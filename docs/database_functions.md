# Database Functions Documentation

This document provides documentation for the database functions in the Egypt Tourism Chatbot database. These functions are organized by category and include information about their purpose, parameters, and return values.

## JSONB Language Functions

These functions handle multilingual text stored in JSONB columns.

### `add_language_to_jsonb(json_data jsonb, text_value text, lang text)`

**Purpose**: Adds a new language to an existing JSONB object.

**Parameters**:
- `json_data jsonb`: The existing JSONB object.
- `text_value text`: The text value to add.
- `lang text`: The language code to add the text for.

**Returns**: `jsonb` - The updated JSONB object with the new language added.

**Example**:
```sql
SELECT add_language_to_jsonb('{"en": "Hello"}', 'مرحبا', 'ar');
-- Returns: {"en": "Hello", "ar": "مرحبا"}
```

### `create_language_jsonb(text_value text, lang text DEFAULT 'en')`

**Purpose**: Creates a new JSONB object with the specified language.

**Parameters**:
- `text_value text`: The text value to add.
- `lang text`: The language code to add the text for (default: 'en').

**Returns**: `jsonb` - A new JSONB object with the specified language.

**Example**:
```sql
SELECT create_language_jsonb('Hello', 'en');
-- Returns: {"en": "Hello"}
```

### `get_available_languages(json_data jsonb)`

**Purpose**: Returns an array of language codes from a JSONB object.

**Parameters**:
- `json_data jsonb`: The JSONB object to extract language codes from.

**Returns**: `text[]` - An array of language codes.

**Example**:
```sql
SELECT get_available_languages('{"en": "Hello", "ar": "مرحبا"}');
-- Returns: ["en", "ar"]
```

### `search_jsonb_text(json_data jsonb, search_text text, lang text DEFAULT 'en')`

**Purpose**: Searches for text in a JSONB object for a specific language.

**Parameters**:
- `json_data jsonb`: The JSONB object to search in.
- `search_text text`: The text to search for.
- `lang text`: The language code to search in (default: 'en').

**Returns**: `boolean` - True if the text is found, false otherwise.

**Example**:
```sql
SELECT search_jsonb_text('{"en": "Hello World", "ar": "مرحبا بالعالم"}', 'World', 'en');
-- Returns: true
```

## Caching Functions

These functions handle query caching for improved performance.

### `get_cached_query(query_text text, params jsonb, category text DEFAULT NULL, ttl_seconds integer DEFAULT 3600)`

**Purpose**: Retrieves or creates a cached query result.

**Parameters**:
- `query_text text`: The SQL query to execute.
- `params jsonb`: The parameters for the query.
- `category text`: The category for the cached query (optional).
- `ttl_seconds integer`: The time-to-live for the cached query in seconds (default: 3600).

**Returns**: `jsonb` - The query result.

**Example**:
```sql
SELECT get_cached_query('SELECT * FROM attractions WHERE id = $1', '[1]', 'attractions', 3600);
```

### `clear_expired_cache()`

**Purpose**: Clears expired cache entries.

**Parameters**: None

**Returns**: `integer` - The number of cache entries cleared.

**Example**:
```sql
SELECT clear_expired_cache();
```

### `clear_all_cache()`

**Purpose**: Clears all cache entries.

**Parameters**: None

**Returns**: `integer` - The number of cache entries cleared.

**Example**:
```sql
SELECT clear_all_cache();
```

### `get_cache_stats()`

**Purpose**: Returns statistics about the cache.

**Parameters**: None

**Returns**: A table with the following columns:
- `total_entries integer`: The total number of cache entries.
- `hit_count bigint`: The total number of cache hits.
- `avg_hits numeric`: The average number of hits per cache entry.
- `oldest_entry timestamp with time zone`: The oldest cache entry.
- `newest_entry timestamp with time zone`: The newest cache entry.
- `memory_usage_kb bigint`: The memory usage of the cache in KB.

**Example**:
```sql
SELECT * FROM get_cache_stats();
```

### `set_cache_category(p_cache_key text, p_category text)`

**Purpose**: Sets the category for a cached query.

**Parameters**:
- `p_cache_key text`: The cache key.
- `p_category text`: The category to set.

**Returns**: `boolean` - True if the category was set, false otherwise.

**Example**:
```sql
SELECT set_cache_category('abc123', 'attractions');
```

## Utility Functions

These functions provide various utilities.

### `update_timestamp()`

**Purpose**: Updates the timestamp for a record. This is a trigger function that sets the updated_at column to the current timestamp.

**Parameters**: None (trigger function)

**Returns**: `trigger` - The updated record.

**Example**:
```sql
CREATE TRIGGER update_timestamp_trigger
BEFORE UPDATE ON attractions
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();
```

## Performance-Critical Search Functions

These functions handle performance-critical search operations.

### `cached_vector_search(p_table_name text, p_embedding text, p_limit integer DEFAULT 10, p_ttl_seconds integer DEFAULT 3600)`

**Purpose**: Performs a vector search and caches the result.

**Parameters**:
- `p_table_name text`: The name of the table to search in.
- `p_embedding text`: The embedding vector to search for.
- `p_limit integer`: The maximum number of results to return (default: 10).
- `p_ttl_seconds integer`: The time-to-live for the cached query in seconds (default: 3600).

**Returns**: `jsonb` - The search results.

**Example**:
```sql
SELECT cached_vector_search('attractions', '[0.1, 0.2, 0.3, ...]', 5, 3600);
```

### `cached_nearby_attractions(lat double precision, lng double precision, radius_km double precision DEFAULT 5.0, limit_val integer DEFAULT 10, ttl_seconds integer DEFAULT 3600)`

**Purpose**: Finds attractions near a given location and caches the result.

**Parameters**:
- `lat double precision`: The latitude of the location.
- `lng double precision`: The longitude of the location.
- `radius_km double precision`: The radius in kilometers (default: 5.0).
- `limit_val integer`: The maximum number of results to return (default: 10).
- `ttl_seconds integer`: The time-to-live for the cached query in seconds (default: 3600).

**Returns**: `jsonb` - The search results.

**Example**:
```sql
SELECT cached_nearby_attractions(30.0444, 31.2357, 10.0, 20, 3600);
```

### `cached_nearby_accommodations(lat double precision, lng double precision, radius_km double precision DEFAULT 5.0, limit_val integer DEFAULT 10, ttl_seconds integer DEFAULT 3600)`

**Purpose**: Finds accommodations near a given location and caches the result.

**Parameters**:
- `lat double precision`: The latitude of the location.
- `lng double precision`: The longitude of the location.
- `radius_km double precision`: The radius in kilometers (default: 5.0).
- `limit_val integer`: The maximum number of results to return (default: 10).
- `ttl_seconds integer`: The time-to-live for the cached query in seconds (default: 3600).

**Returns**: `jsonb` - The search results.

**Example**:
```sql
SELECT cached_nearby_accommodations(30.0444, 31.2357, 10.0, 20, 3600);
```

### `cached_nearby_restaurants(lat double precision, lng double precision, radius_km double precision DEFAULT 5.0, limit_val integer DEFAULT 10, ttl_seconds integer DEFAULT 3600)`

**Purpose**: Finds restaurants near a given location and caches the result.

**Parameters**:
- `lat double precision`: The latitude of the location.
- `lng double precision`: The longitude of the location.
- `radius_km double precision`: The radius in kilometers (default: 5.0).
- `limit_val integer`: The maximum number of results to return (default: 10).
- `ttl_seconds integer`: The time-to-live for the cached query in seconds (default: 3600).

**Returns**: `jsonb` - The search results.

**Example**:
```sql
SELECT cached_nearby_restaurants(30.0444, 31.2357, 10.0, 20, 3600);
```
