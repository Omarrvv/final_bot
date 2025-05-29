# Egypt Chatbot Database Migration - July 2025

This migration addresses several issues identified in the database schema, focusing on removing redundancy, standardizing foreign keys, and ensuring data consistency.

## Migration Overview

The migration is divided into four phases, each addressing specific aspects of the schema:

### Phase 1: Remove Redundant Backup Columns
- Removes `*_backup` columns from `accommodations`, `attractions`, `cities`, and `restaurants` tables
- These columns were created during the migration to JSONB and vector types and are no longer needed

### Phase 2: Update Related Attractions Function
- Updates the `find_related_attractions` function to use the junction table instead of the array column
- This ensures consistent access to related attractions data

### Phase 3: Remove Array Columns
- Verifies that data has been migrated from array columns to junction tables
- Removes redundant array columns from `attractions` and `itineraries` tables
- This eliminates data duplication and ensures a single source of truth

### Phase 4: Fix User ID Inconsistency
- Standardizes `user_id` columns to integer type across all tables
- Creates backups of the original values before conversion
- This ensures consistent foreign key relationships with the `users` table

### Phase 5: Standardize Foreign Key Constraints
- Adds missing foreign key constraints with consistent ON DELETE and ON UPDATE actions
- This improves data integrity and ensures consistent behavior when records are updated or deleted

## Prerequisites

Before running these migrations, ensure that:

1. You have a recent backup of the database
2. The application is not actively writing to the database during migration
3. You have sufficient privileges to alter tables and create/drop constraints

## Execution Plan

Execute the migrations in the following order:

```bash
# 1. Remove backup columns
psql -h localhost -p 5432 -U postgres -d egypt_chatbot -f migrations/20250710_remove_backup_columns.sql

# 2. Update related attractions function
psql -h localhost -p 5432 -U postgres -d egypt_chatbot -f migrations/20250710_update_related_attractions_function.sql

# 3. Remove array columns
psql -h localhost -p 5432 -U postgres -d egypt_chatbot -f migrations/20250710_remove_array_columns.sql

# 4. Fix user ID inconsistency
psql -h localhost -p 5432 -U postgres -d egypt_chatbot -f migrations/20250710_fix_user_id_inconsistency.sql

# 5. Standardize foreign key constraints
psql -h localhost -p 5432 -U postgres -d egypt_chatbot -f migrations/20250710_standardize_foreign_keys.sql
```

## Verification

After running the migrations, verify the changes:

1. Check that backup columns have been removed:
   ```sql
   \d accommodations
   \d attractions
   \d cities
   \d restaurants
   ```

2. Verify that the `find_related_attractions` function is using the junction table:
   ```sql
   \df+ find_related_attractions
   ```

3. Confirm that array columns have been removed:
   ```sql
   \d attractions
   \d itineraries
   ```

4. Check that user_id columns are now integer type:
   ```sql
   SELECT table_name, column_name, data_type
   FROM information_schema.columns
   WHERE column_name = 'user_id'
   AND table_schema = 'public';
   ```

5. Verify that foreign key constraints have been added:
   ```sql
   SELECT tc.table_name, tc.constraint_name, 
          kcu.column_name, 
          ccu.table_name AS foreign_table_name,
          ccu.column_name AS foreign_column_name,
          rc.delete_rule, rc.update_rule
   FROM information_schema.table_constraints tc
   JOIN information_schema.key_column_usage kcu
     ON tc.constraint_name = kcu.constraint_name
   JOIN information_schema.constraint_column_usage ccu
     ON ccu.constraint_name = tc.constraint_name
   JOIN information_schema.referential_constraints rc
     ON tc.constraint_name = rc.constraint_name
   WHERE tc.constraint_type = 'FOREIGN KEY'
   AND tc.table_schema = 'public'
   ORDER BY tc.table_name, kcu.column_name;
   ```

## Rollback Plan

If any issues are encountered, restore from the backup:

```bash
pg_restore -h localhost -p 5432 -U postgres -d egypt_chatbot -c egypt_chatbot_backup.dump
```

## Application Code Updates

After completing the database migrations, the application code should be updated to:

1. Remove any references to the backup columns
2. Use the junction tables instead of array columns
3. Handle user_id as integer type instead of text
4. Ensure proper error handling for foreign key constraints

## Contact

For any issues or questions regarding this migration, please contact the database administrator.
