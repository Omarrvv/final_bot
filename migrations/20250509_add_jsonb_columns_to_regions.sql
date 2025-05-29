-- Migration: Add JSONB columns to regions table
-- Date: 2025-05-09
-- Description: This migration adds JSONB columns for name and description to the regions table,
-- creates GIN indexes for these columns, and migrates data from text fields to JSONB columns.

-- Step 1: Add JSONB columns if they don't exist
DO $$
BEGIN
    -- Add name JSONB column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'regions' AND column_name = 'name' AND data_type = 'jsonb'
    ) THEN
        ALTER TABLE regions ADD COLUMN name JSONB;
        RAISE NOTICE 'Added name JSONB column to regions table';
    ELSE
        RAISE NOTICE 'name JSONB column already exists in regions table';
    END IF;

    -- Add description JSONB column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'regions' AND column_name = 'description' AND data_type = 'jsonb'
    ) THEN
        ALTER TABLE regions ADD COLUMN description JSONB;
        RAISE NOTICE 'Added description JSONB column to regions table';
    ELSE
        RAISE NOTICE 'description JSONB column already exists in regions table';
    END IF;
END $$;

-- Step 2: Create GIN indexes for JSONB columns
DO $$
BEGIN
    -- Create GIN index for name JSONB column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'regions' AND indexname = 'idx_regions_name_jsonb'
    ) THEN
        CREATE INDEX idx_regions_name_jsonb ON regions USING GIN (name jsonb_path_ops);
        RAISE NOTICE 'Created GIN index for name JSONB column in regions table';
    ELSE
        RAISE NOTICE 'GIN index for name JSONB column already exists in regions table';
    END IF;

    -- Create GIN index for description JSONB column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'regions' AND indexname = 'idx_regions_description_jsonb'
    ) THEN
        CREATE INDEX idx_regions_description_jsonb ON regions USING GIN (description jsonb_path_ops);
        RAISE NOTICE 'Created GIN index for description JSONB column in regions table';
    ELSE
        RAISE NOTICE 'GIN index for description JSONB column already exists in regions table';
    END IF;
END $$;

-- Step 3: Migrate data from text fields to JSONB columns
UPDATE regions
SET name = jsonb_build_object(
    'en', name_en,
    'ar', name_ar
)
WHERE (name IS NULL OR jsonb_typeof(name) = 'null')
  AND (name_en IS NOT NULL OR name_ar IS NOT NULL);

-- For description, we need to check if description_en and description_ar columns exist
DO $$
BEGIN
    -- Check if description_en and description_ar columns exist
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'regions' AND column_name = 'description_en'
    ) AND EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'regions' AND column_name = 'description_ar'
    ) THEN
        -- Migrate description data
        EXECUTE '
            UPDATE regions
            SET description = jsonb_build_object(
                ''en'', description_en,
                ''ar'', description_ar
            )
            WHERE (description IS NULL OR jsonb_typeof(description) = ''null'')
              AND (description_en IS NOT NULL OR description_ar IS NOT NULL)
        ';
        RAISE NOTICE 'Migrated description data from text fields to JSONB column in regions table';
    ELSE
        -- If description_en and description_ar columns don't exist, create empty JSONB objects
        UPDATE regions
        SET description = '{}'::jsonb
        WHERE description IS NULL OR jsonb_typeof(description) = 'null';
        RAISE NOTICE 'Created empty JSONB objects for description column in regions table';
    END IF;
END $$;

-- Step 4: Verify migration
DO $$
DECLARE
    total_count INTEGER;
    migrated_count INTEGER;
BEGIN
    -- Get total count of regions
    SELECT COUNT(*) INTO total_count FROM regions;
    
    -- Get count of regions with populated name JSONB column
    SELECT COUNT(*) INTO migrated_count FROM regions WHERE name IS NOT NULL AND jsonb_typeof(name) != 'null';
    
    RAISE NOTICE 'Migration verification: % of % regions have populated name JSONB column', migrated_count, total_count;
    
    -- Get count of regions with populated description JSONB column
    SELECT COUNT(*) INTO migrated_count FROM regions WHERE description IS NOT NULL AND jsonb_typeof(description) != 'null';
    
    RAISE NOTICE 'Migration verification: % of % regions have populated description JSONB column', migrated_count, total_count;
END $$;
