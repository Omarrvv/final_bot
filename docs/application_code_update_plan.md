# Application Code Update Plan

This document outlines the plan for updating the application code to match the database schema changes that have already been implemented.

## Overview

The database schema has been updated with the following changes:

1. **Name/Description Redundancy**: Removed redundant `name_en`, `name_ar`, `description_en`, `description_ar` columns and standardized on JSONB `name` and `description` columns.

2. **Location Redundancy (Lat/Lon vs Geom)**: Removed redundant `latitude` and `longitude` columns and standardized on `geom` (geometry) columns.

3. **Location Redundancy (Text vs ID)**: Removed redundant `city` and `region` text columns and standardized on `city_id` and `region_id` foreign key columns.

4. **Vector Indexes**: Standardized on HNSW indexes for vector search.

5. **ID Standardization**: Standardized all ID columns to use integers instead of text.

6. **Timestamp Standardization**: Standardized all timestamp columns to use `created_at` and `updated_at` with the proper timestamp data type.

However, the application code has not been fully updated to match these changes. We need to update the code to ensure it works correctly with the new schema.

## Files to Update

Based on our analysis, the following files need to be updated:

1. `src/services/attraction_service.py`
2. `src/services/restaurant_service.py`
3. `src/services/accommodation_service.py`
4. `src/services/city_service.py`
5. `src/services/region_service.py`
6. `src/services/hotel_service.py`
7. `src/knowledge/database.py`
8. `src/repositories/attraction_repository.py`
9. `src/repositories/base_repository.py`

## Changes Needed

### 1. Update JSONB Field Access

Replace code that accesses `name_en`, `name_ar`, `description_en`, `description_ar` with code that accesses the JSONB `name` and `description` columns:

```python
# Old code
name_en = attraction['name_en']
description_ar = attraction['description_ar']

# New code
name_en = attraction['name']['en'] if 'name' in attraction and 'en' in attraction['name'] else None
description_ar = attraction['description']['ar'] if 'description' in attraction and 'ar' in attraction['description'] else None

# Or using get_text_by_language function
name_en = get_text_by_language(attraction['name'], 'en')
description_ar = get_text_by_language(attraction['description'], 'ar')
```

### 2. Update Spatial Queries

Replace code that uses `latitude` and `longitude` with code that uses the `geom` column:

```python
# Old code
sql = """
    SELECT *, 
    ST_Distance(
        ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography,
        ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
    ) / 1000 AS distance
    FROM attractions
    WHERE latitude IS NOT NULL AND longitude IS NOT NULL
    AND ST_DWithin(
        ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography,
        ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
        %s * 1000
    )
    ORDER BY distance
    LIMIT %s
"""
params = (longitude, latitude, longitude, latitude, radius_km, limit)

# New code
sql = """
    SELECT *, 
    ST_Distance(
        geom::geography,
        ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
    ) / 1000 AS distance
    FROM attractions
    WHERE geom IS NOT NULL
    AND ST_DWithin(
        geom::geography,
        ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
        %s * 1000
    )
    ORDER BY distance
    LIMIT %s
"""
params = (longitude, latitude, longitude, latitude, radius_km, limit)
```

### 3. Update Location References

Replace code that uses `city` and `region` text columns with code that uses `city_id` and `region_id` foreign key columns:

```python
# Old code
city_name = attraction['city']
region_name = attraction['region']

# New code
city_id = attraction['city_id']
region_id = attraction['region_id']

# To get the city or region name, join with the cities or regions table
sql = """
    SELECT a.*, c.name AS city_name, r.name AS region_name
    FROM attractions a
    LEFT JOIN cities c ON a.city_id = c.id
    LEFT JOIN regions r ON a.region_id = r.id
    WHERE a.id = %s
"""
```

### 4. Update ID Handling

Update code to handle integer IDs instead of text IDs:

```python
# Old code
attraction_id = "nile_say_settlement_old_force_marketplace"

# New code
attraction_id = 1
```

### 5. Update Timestamp Handling

Update code to use `created_at` and `updated_at` consistently:

```python
# Old code
timestamp = record['timestamp']

# New code
created_at = record['created_at']
updated_at = record['updated_at']
```

## Implementation Plan

1. **Create a Test Branch**: Create a new branch for these changes to avoid disrupting the main codebase.

2. **Update Service Classes**: Update the service classes to use the new schema.

3. **Update Repository Classes**: Update the repository classes to use the new schema.

4. **Update Database Manager**: Update the database manager to use the new schema.

5. **Test Changes**: Test the changes to ensure they work correctly.

6. **Merge Changes**: Merge the changes into the main codebase.

## Priority Order

1. **High Priority**:
   - Update spatial queries to use `geom` instead of `latitude` and `longitude`
   - Update JSONB field access to use `name` and `description` instead of `name_en`, `name_ar`, etc.

2. **Medium Priority**:
   - Update location references to use `city_id` and `region_id` instead of `city` and `region`
   - Update ID handling to use integer IDs instead of text IDs

3. **Low Priority**:
   - Update timestamp handling to use `created_at` and `updated_at` consistently

## Conclusion

By following this plan, we will ensure that the application code is fully updated to match the database schema changes that have already been implemented. This will improve the consistency and maintainability of the codebase and prevent errors that could occur due to mismatches between the code and the database schema.
