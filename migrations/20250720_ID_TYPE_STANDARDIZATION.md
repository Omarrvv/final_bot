# ID Type Standardization

## Overview

This document describes the standardization of ID types in the database schema to ensure consistency and proper referential integrity.

## Current State

The database schema has several inconsistencies in ID types:

1. **Main Entity Tables**: Most main entity tables (attractions, restaurants, cities, etc.) use integer IDs.
2. **Category/Type Tables**: Category and type tables (attraction_types, event_categories, etc.) use text IDs.
3. **User ID Foreign Keys**: The users table has integer IDs, but many foreign key columns referencing it use text type.
4. **Polymorphic Associations**: The media, reviews, and favorites tables use text for target_id while the target tables now use integer IDs.

## Decisions

### 1. Category/Type Tables

We've decided to **keep text IDs for category/type tables** as they serve as human-readable slugs (e.g., "historical", "cultural"). This is a common pattern in many systems, where lookup tables use meaningful text identifiers.

### 2. User ID Foreign Keys

We've decided to **standardize all user_id foreign keys to integer type** to match the users table. This ensures proper referential integrity.

### 3. Polymorphic Associations

We've decided to **convert polymorphic target_id columns to integer type** to match the target tables. This avoids type mismatches when linking to target entities.

## Migration Plan

### Phase 1: Fix User ID Inconsistency

The migration script `20250720_fix_user_id_inconsistency.sql` performs the following steps:

1. Creates backup columns for user_id in all affected tables
2. Drops foreign key constraints if they exist
3. Converts user_id columns from text to integer
4. Adds foreign key constraints to reference users.id

### Phase 2: Fix Polymorphic Associations

The migration script `20250720_fix_polymorphic_associations.sql` performs the following steps:

1. Creates backup columns for target_id in all affected tables
2. Creates a mapping table to store the relationship between text IDs and integer IDs
3. Updates target_id values based on the mapping
4. Converts target_id columns from text to integer
5. Recreates check constraints and indexes

### Phase 3: Fix Remaining User ID Columns

The migration script `20250720_fix_remaining_user_id.sql` performs the following steps:

1. Identifies tables where user_id is still text type
2. Creates backup columns if they don't already exist
3. Drops foreign key constraints if they exist
4. Converts user_id columns from text to integer
5. Adds foreign key constraints to reference users.id

## Application Code Impact

The migration should have minimal impact on application code since most code already treats IDs as opaque identifiers. However, the following areas may need updates:

1. **User ID Handling**: Code that explicitly treats user_id as text may need updates.
2. **Polymorphic Association Handling**: Code that handles polymorphic associations may need updates to handle integer target_id values.

## Rollback Plan

If issues are encountered, the backup columns created during migration can be used to restore the original values:

```sql
-- Rollback user_id changes
UPDATE table_name SET user_id = user_id_backup WHERE user_id_backup IS NOT NULL;
ALTER TABLE table_name ALTER COLUMN user_id TYPE TEXT;

-- Rollback target_id changes
UPDATE table_name SET target_id = target_id_backup WHERE target_id_backup IS NOT NULL;
ALTER TABLE table_name ALTER COLUMN target_id TYPE TEXT;
```

## Verification

After running the migrations, verify the changes:

1. Check that user_id columns are integer type and have foreign key constraints:

   ```sql
   SELECT table_name, column_name, data_type
   FROM information_schema.columns
   WHERE column_name = 'user_id' AND table_schema = 'public';

   SELECT tc.table_name, kcu.column_name, ccu.table_name AS foreign_table_name
   FROM information_schema.table_constraints AS tc
   JOIN information_schema.key_column_usage AS kcu ON tc.constraint_name = kcu.constraint_name
   JOIN information_schema.constraint_column_usage AS ccu ON ccu.constraint_name = tc.constraint_name
   WHERE tc.constraint_type = 'FOREIGN KEY' AND kcu.column_name = 'user_id';
   ```

2. Check that target_id columns are integer type:
   ```sql
   SELECT table_name, column_name, data_type
   FROM information_schema.columns
   WHERE column_name = 'target_id' AND table_schema = 'public';
   ```
