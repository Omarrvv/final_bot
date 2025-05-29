-- Migration: Enhance Attractions Table (Part 4)
-- Date: 2024-06-28
-- Description: Add new columns to attractions table

-- 1. Add subcategory_id column to attractions table
ALTER TABLE attractions ADD COLUMN IF NOT EXISTS subcategory_id TEXT REFERENCES attraction_subcategories(id);
CREATE INDEX IF NOT EXISTS idx_attractions_subcategory_id ON attractions(subcategory_id);

-- 2. Add visiting_info column to attractions table
ALTER TABLE attractions ADD COLUMN IF NOT EXISTS visiting_info JSONB DEFAULT '{}'::jsonb;
CREATE INDEX IF NOT EXISTS idx_attractions_visiting_info_gin ON attractions USING GIN (visiting_info);

-- 3. Add accessibility_info column to attractions table
ALTER TABLE attractions ADD COLUMN IF NOT EXISTS accessibility_info JSONB DEFAULT '{}'::jsonb;
CREATE INDEX IF NOT EXISTS idx_attractions_accessibility_info_gin ON attractions USING GIN (accessibility_info);

-- 4. Add related_attractions column to attractions table
ALTER TABLE attractions ADD COLUMN IF NOT EXISTS related_attractions TEXT[] DEFAULT '{}'::text[];
CREATE INDEX IF NOT EXISTS idx_attractions_related_attractions ON attractions USING GIN (related_attractions array_ops);

-- 5. Add historical_context column to attractions table
ALTER TABLE attractions ADD COLUMN IF NOT EXISTS historical_context JSONB DEFAULT '{}'::jsonb;
CREATE INDEX IF NOT EXISTS idx_attractions_historical_context_gin ON attractions USING GIN (historical_context);

-- 6. Create function to find related attractions
CREATE OR REPLACE FUNCTION find_related_attractions(
    p_attraction_id TEXT,
    p_limit INTEGER DEFAULT 5
)
RETURNS TABLE (
    id TEXT,
    name JSONB,
    type TEXT,
    subcategory_id TEXT,
    city_id TEXT,
    region_id TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        a.id,
        a.name,
        a.type,
        a.subcategory_id,
        a.city_id,
        a.region_id
    FROM 
        attractions a
    WHERE 
        a.id = ANY(
            SELECT related_attractions 
            FROM attractions 
            WHERE id = p_attraction_id
        )
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;
