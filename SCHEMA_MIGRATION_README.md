# Egypt Chatbot Schema Migration

This project contains a set of SQL migration scripts to improve the Egypt Chatbot database schema by addressing redundancy, standardizing naming conventions, and optimizing performance.

## Migration Overview

The migration process is divided into phases, each addressing specific aspects of the schema:

### Phase 1: Critical Cleanup - Redundancy & Vector Indexes

1. **Consolidate Name/Description Columns** (001_consolidate_name_description_columns.sql)
   - Migrates data from `name_en`, `name_ar` to JSONB `name` column
   - Migrates data from `description_en`, `description_ar` to JSONB `description` column
   - Removes redundant columns after verification

2. **Consolidate Location Columns** (002_consolidate_location_columns.sql)
   - Migrates data from `latitude`, `longitude` to PostGIS `geom` column
   - Adds helper functions to extract coordinates from geometry
   - Removes redundant columns after verification

3. **Consolidate Location Reference Columns** (003_consolidate_location_reference_columns.sql)
   - Migrates data from text `city`, `region` columns to foreign key `city_id`, `region_id` columns
   - Removes redundant columns after verification

4. **Consolidate Vector Indexes** (004_consolidate_vector_indexes.sql)
   - Standardizes on HNSW indexes for vector search
   - Removes redundant IVFFlat indexes
   - Renames indexes to follow a consistent naming convention

### Phase 2: Consistency & Refinement

5. **Standardize Timestamp Columns** (005_standardize_timestamp_columns.sql)
   - Standardizes timestamp column naming to `created_at` and `updated_at`
   - Ensures proper data types for timestamp columns
   - Adds missing timestamp columns and update triggers

6. **Standardize Foreign Key Constraints** (006_standardize_foreign_key_constraints.sql)
   - Standardizes foreign key constraint rules (ON DELETE/UPDATE)
   - Adds missing foreign key constraints
   - Documents the standardized rules

## Prerequisites

- PostgreSQL 12 or higher
- PostGIS extension
- pg_trgm extension
- vector extension (for HNSW and IVFFlat indexes)
- Database user with schema modification privileges

## Running the Migrations

### Automated Method

1. Make the migration script executable:
   ```bash
   chmod +x run_migrations.sh
   ```

2. Run the migration script:
   ```bash
   ./run_migrations.sh
   ```

The script will:
- Create a backup of the database before running migrations
- Execute each migration file in order
- Log the results of each migration
- Create a post-migration backup
- Attempt to restore from backup if any migration fails

### Manual Method

1. Create a database backup:
   ```bash
   pg_dump -h localhost -p 5432 -U postgres -F c -b -v -f egypt_chatbot_backup.dump egypt_chatbot
   ```

2. Run each migration file in order:
   ```bash
   psql -h localhost -p 5432 -U postgres -d egypt_chatbot -f migrations/001_consolidate_name_description_columns.sql
   psql -h localhost -p 5432 -U postgres -d egypt_chatbot -f migrations/002_consolidate_location_columns.sql
   psql -h localhost -p 5432 -U postgres -d egypt_chatbot -f migrations/003_consolidate_location_reference_columns.sql
   psql -h localhost -p 5432 -U postgres -d egypt_chatbot -f migrations/004_consolidate_vector_indexes.sql
   psql -h localhost -p 5432 -U postgres -d egypt_chatbot -f migrations/005_standardize_timestamp_columns.sql
   psql -h localhost -p 5432 -U postgres -d egypt_chatbot -f migrations/006_standardize_foreign_key_constraints.sql
   ```

3. If any migration fails, restore from backup:
   ```bash
   pg_restore -h localhost -p 5432 -U postgres -d egypt_chatbot -c egypt_chatbot_backup.dump
   ```

## Verification

After running the migrations, verify the changes:

1. Check that redundant columns have been removed:
   ```sql
   \d accommodations
   \d attractions
   \d cities
   \d hotels
   \d regions
   \d restaurants
   ```

2. Verify that data has been preserved:
   ```sql
   SELECT COUNT(*) FROM accommodations;
   SELECT COUNT(*) FROM attractions;
   SELECT COUNT(*) FROM cities;
   SELECT COUNT(*) FROM hotels;
   SELECT COUNT(*) FROM regions;
   SELECT COUNT(*) FROM restaurants;
   ```

3. Test vector search functionality:
   ```sql
   SELECT id, name FROM attractions ORDER BY embedding <-> (SELECT embedding FROM attractions WHERE id = 'some-id') LIMIT 5;
   ```

## Rollback

If you need to rollback the migrations, restore from the backup:

```bash
pg_restore -h localhost -p 5432 -U postgres -d egypt_chatbot -c egypt_chatbot_backup.dump
```

## Application Code Changes

After migrating the database schema, you'll need to update the application code:

1. Update code that reads from or writes to the removed columns
2. Use the JSONB columns for multilingual text
3. Use the PostGIS geometry functions for spatial data
4. Use foreign key relationships instead of text columns

## Future Improvements

Future phases of schema improvement could include:

1. Standardizing ID data types (e.g., using UUIDs consistently)
2. Reviewing and optimizing business logic in database functions
3. Addressing polymorphic associations in media, reviews, and favorites tables
4. Documenting and potentially refactoring generic JSONB data columns
5. Evaluating array columns for relationships
