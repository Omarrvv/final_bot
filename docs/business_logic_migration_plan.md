# Business Logic Migration Plan

This document outlines the plan for migrating business logic from database functions to the application layer in the Egypt Tourism Chatbot.

## Overview

Based on our analysis, we've identified several functions that should be moved from the database to the application layer. This migration will improve maintainability, testability, and flexibility of the codebase.

## Functions to Migrate

### 1. Complex Search Functions

These functions contain complex business logic that would be better implemented in the application layer:

1. `search_attractions_by_keywords`
2. `search_events_festivals`
3. `search_faqs`
4. `search_itineraries`
5. `search_practical_info`
6. `search_tour_packages`
7. `get_attraction_by_name`
8. `get_accommodations_by_city`

### 2. Transportation Functions

These functions handle transportation routes and would be better implemented in the application layer:

1. `find_transportation_routes`
2. `find_routes_from_destination`
3. `find_routes_to_destination`
4. `find_related_attractions`

### 3. Connection Pool Management

These functions should be handled by the application or a dedicated connection pool manager:

1. `clean_old_connection_pool_stats`
2. `get_connection_pool_recommendations`
3. `get_connection_pool_stats`
4. `record_connection_pool_stats`

### 4. Query Analysis

These functions would be better implemented in the application layer:

1. `analyze_query_patterns`
2. `analyze_query_performance`

## Migration Strategy

For each function to be migrated, we'll follow these steps:

1. **Create Application Layer Equivalent**: Implement the function in the application layer using Python.
2. **Test the New Implementation**: Ensure the new implementation produces the same results as the database function.
3. **Update References**: Update all references to the database function to use the new application layer function.
4. **Deprecate the Database Function**: Mark the database function as deprecated but don't remove it yet.
5. **Monitor Usage**: Monitor usage of the deprecated function to ensure it's no longer being used.
6. **Remove the Database Function**: Once we're confident the function is no longer being used, remove it from the database.

## Implementation Plan

### Phase 1: Complex Search Functions

#### 1.1 Create Python Equivalents

Create Python functions in `app/services/search_service.py` for each of the complex search functions:

```python
def search_attractions_by_keywords(keywords, lang='en'):
    """
    Search attractions by keywords.
    
    Args:
        keywords (str): The keywords to search for.
        lang (str, optional): The language to search in. Defaults to 'en'.
        
    Returns:
        list: A list of attractions matching the keywords.
    """
    query = """
    SELECT
        a.id,
        a.name,
        a.description,
        a.city,
        a.region,
        a.type,
        ts_rank_cd(
            to_tsvector(get_text_by_language(a.description, %s)),
            to_tsquery(%s)
        ) AS relevance
    FROM
        attractions a
    WHERE
        to_tsvector(get_text_by_language(a.description, %s)) @@
        to_tsquery(%s)
    ORDER BY
        relevance DESC
    """
    
    # Convert keywords to tsquery format
    tsquery = ' & '.join(keywords.split())
    
    # Execute the query
    with db.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (lang, tsquery, lang, tsquery))
            results = cursor.fetchall()
            
    # Process results
    attractions = []
    for row in results:
        attractions.append({
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'city': row[3],
            'region': row[4],
            'type': row[5],
            'relevance': row[6]
        })
            
    return attractions
```

Implement similar functions for the other complex search functions.

#### 1.2 Update References

Update all references to the database functions in the codebase to use the new Python functions.

#### 1.3 Deprecate Database Functions

Mark the database functions as deprecated by adding a comment to each function:

```sql
-- DEPRECATED: This function has been moved to the application layer.
-- Please use the equivalent function in app/services/search_service.py instead.
```

### Phase 2: Transportation Functions

Follow the same steps as Phase 1 for the transportation functions.

### Phase 3: Connection Pool Management

Implement connection pool management in the application layer using a library like `psycopg2.pool` or `SQLAlchemy`.

### Phase 4: Query Analysis

Implement query analysis in the application layer using Python's profiling and logging capabilities.

## Timeline

- Phase 1: 1 week
- Phase 2: 1 week
- Phase 3: 1 week
- Phase 4: 1 week

## Risks and Mitigations

### Risks

1. **Functionality Changes**: The new implementation might not exactly match the behavior of the database function.
2. **Performance Impact**: Moving functions to the application layer might impact performance.
3. **Dependency Issues**: The database functions might be used in unexpected places.

### Mitigations

1. **Thorough Testing**: Test the new implementations thoroughly to ensure they match the behavior of the database functions.
2. **Performance Monitoring**: Monitor performance before and after the migration to identify any issues.
3. **Gradual Migration**: Migrate functions one at a time and monitor for issues before proceeding.
4. **Deprecation Period**: Keep the deprecated functions for a period of time to catch any missed references.

## Conclusion

This migration plan provides a structured approach to moving business logic from the database to the application layer. By following this plan, we'll improve the maintainability, testability, and flexibility of the Egypt Tourism Chatbot codebase.
