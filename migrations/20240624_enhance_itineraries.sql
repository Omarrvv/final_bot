-- Migration: Enhance Itineraries Table
-- Description: This migration enhances the itineraries table and adds itinerary_categories table

-- Check if itinerary_categories table exists, if not create it
CREATE TABLE IF NOT EXISTS itinerary_categories (
    id VARCHAR(50) PRIMARY KEY,
    name JSONB NOT NULL,
    description JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add index on name for itinerary_categories
CREATE INDEX IF NOT EXISTS idx_itinerary_categories_name ON itinerary_categories USING GIN (name);

-- Populate itinerary_categories with initial data
INSERT INTO itinerary_categories (id, name, description)
VALUES
    ('short_trips', 
     '{"en": "Short Trips", "ar": "رحلات قصيرة"}',
     '{"en": "Itineraries for 1-3 day trips", "ar": "مسارات لرحلات من 1-3 أيام"}'),
    ('medium_trips', 
     '{"en": "Medium Trips", "ar": "رحلات متوسطة"}',
     '{"en": "Itineraries for 4-7 day trips", "ar": "مسارات لرحلات من 4-7 أيام"}'),
    ('long_trips', 
     '{"en": "Long Trips", "ar": "رحلات طويلة"}',
     '{"en": "Itineraries for 8+ day trips", "ar": "مسارات لرحلات من 8+ أيام"}'),
    ('family_trips', 
     '{"en": "Family Trips", "ar": "رحلات عائلية"}',
     '{"en": "Itineraries suitable for families with children", "ar": "مسارات مناسبة للعائلات مع الأطفال"}'),
    ('adventure_trips', 
     '{"en": "Adventure Trips", "ar": "رحلات مغامرة"}',
     '{"en": "Itineraries focused on adventure activities", "ar": "مسارات تركز على أنشطة المغامرة"}'),
    ('cultural_trips', 
     '{"en": "Cultural Trips", "ar": "رحلات ثقافية"}',
     '{"en": "Itineraries focused on cultural and historical sites", "ar": "مسارات تركز على المواقع الثقافية والتاريخية"}'),
    ('luxury_trips', 
     '{"en": "Luxury Trips", "ar": "رحلات فاخرة"}',
     '{"en": "Itineraries featuring luxury accommodations and experiences", "ar": "مسارات تتضمن إقامات وتجارب فاخرة"}'),
    ('budget_trips', 
     '{"en": "Budget Trips", "ar": "رحلات اقتصادية"}',
     '{"en": "Itineraries designed for budget-conscious travelers", "ar": "مسارات مصممة للمسافرين الواعين بالميزانية"}')
ON CONFLICT (id) DO NOTHING;

-- Check if itineraries table exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'itineraries') THEN
        -- Create itineraries table if it doesn't exist
        CREATE TABLE itineraries (
            id SERIAL PRIMARY KEY,
            name JSONB NOT NULL,
            description JSONB,
            category_id VARCHAR(50) REFERENCES itinerary_categories(id),
            duration_days INTEGER,
            difficulty_level VARCHAR(20),
            suitable_for JSONB,
            destinations JSONB,
            day_plans JSONB,
            highlights JSONB,
            practical_info JSONB,
            estimated_budget JSONB,
            best_time_to_visit JSONB,
            images JSONB,
            tags TEXT[],
            is_featured BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- Add indexes
        CREATE INDEX idx_itineraries_name ON itineraries USING GIN (name);
        CREATE INDEX idx_itineraries_category_id ON itineraries (category_id);
        CREATE INDEX idx_itineraries_duration_days ON itineraries (duration_days);
        CREATE INDEX idx_itineraries_difficulty_level ON itineraries (difficulty_level);
        CREATE INDEX idx_itineraries_tags ON itineraries USING GIN (tags);
        CREATE INDEX idx_itineraries_is_featured ON itineraries (is_featured);
    ELSE
        -- Alter existing itineraries table to ensure it has all required columns
        
        -- Check and add category_id column if it doesn't exist
        IF NOT EXISTS (SELECT FROM information_schema.columns 
                       WHERE table_name = 'itineraries' AND column_name = 'category_id') THEN
            ALTER TABLE itineraries ADD COLUMN category_id VARCHAR(50) REFERENCES itinerary_categories(id);
            CREATE INDEX idx_itineraries_category_id ON itineraries (category_id);
        END IF;
        
        -- Check and add duration_days column if it doesn't exist
        IF NOT EXISTS (SELECT FROM information_schema.columns 
                       WHERE table_name = 'itineraries' AND column_name = 'duration_days') THEN
            ALTER TABLE itineraries ADD COLUMN duration_days INTEGER;
            CREATE INDEX idx_itineraries_duration_days ON itineraries (duration_days);
        END IF;
        
        -- Check and add difficulty_level column if it doesn't exist
        IF NOT EXISTS (SELECT FROM information_schema.columns 
                       WHERE table_name = 'itineraries' AND column_name = 'difficulty_level') THEN
            ALTER TABLE itineraries ADD COLUMN difficulty_level VARCHAR(20);
            CREATE INDEX idx_itineraries_difficulty_level ON itineraries (difficulty_level);
        END IF;
        
        -- Check and add suitable_for column if it doesn't exist
        IF NOT EXISTS (SELECT FROM information_schema.columns 
                       WHERE table_name = 'itineraries' AND column_name = 'suitable_for') THEN
            ALTER TABLE itineraries ADD COLUMN suitable_for JSONB;
        END IF;
        
        -- Check and add destinations column if it doesn't exist
        IF NOT EXISTS (SELECT FROM information_schema.columns 
                       WHERE table_name = 'itineraries' AND column_name = 'destinations') THEN
            ALTER TABLE itineraries ADD COLUMN destinations JSONB;
        END IF;
        
        -- Check and add day_plans column if it doesn't exist
        IF NOT EXISTS (SELECT FROM information_schema.columns 
                       WHERE table_name = 'itineraries' AND column_name = 'day_plans') THEN
            ALTER TABLE itineraries ADD COLUMN day_plans JSONB;
        END IF;
        
        -- Check and add highlights column if it doesn't exist
        IF NOT EXISTS (SELECT FROM information_schema.columns 
                       WHERE table_name = 'itineraries' AND column_name = 'highlights') THEN
            ALTER TABLE itineraries ADD COLUMN highlights JSONB;
        END IF;
        
        -- Check and add practical_info column if it doesn't exist
        IF NOT EXISTS (SELECT FROM information_schema.columns 
                       WHERE table_name = 'itineraries' AND column_name = 'practical_info') THEN
            ALTER TABLE itineraries ADD COLUMN practical_info JSONB;
        END IF;
        
        -- Check and add estimated_budget column if it doesn't exist
        IF NOT EXISTS (SELECT FROM information_schema.columns 
                       WHERE table_name = 'itineraries' AND column_name = 'estimated_budget') THEN
            ALTER TABLE itineraries ADD COLUMN estimated_budget JSONB;
        END IF;
        
        -- Check and add best_time_to_visit column if it doesn't exist
        IF NOT EXISTS (SELECT FROM information_schema.columns 
                       WHERE table_name = 'itineraries' AND column_name = 'best_time_to_visit') THEN
            ALTER TABLE itineraries ADD COLUMN best_time_to_visit JSONB;
        END IF;
        
        -- Check and add images column if it doesn't exist
        IF NOT EXISTS (SELECT FROM information_schema.columns 
                       WHERE table_name = 'itineraries' AND column_name = 'images') THEN
            ALTER TABLE itineraries ADD COLUMN images JSONB;
        END IF;
        
        -- Ensure name and description are JSONB
        ALTER TABLE itineraries 
        ALTER COLUMN name TYPE JSONB USING name::JSONB,
        ALTER COLUMN description TYPE JSONB USING description::JSONB;
        
        -- Add missing indexes if they don't exist
        IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_itineraries_name') THEN
            CREATE INDEX idx_itineraries_name ON itineraries USING GIN (name);
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_itineraries_tags') THEN
            CREATE INDEX idx_itineraries_tags ON itineraries USING GIN (tags);
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_itineraries_is_featured') THEN
            CREATE INDEX idx_itineraries_is_featured ON itineraries (is_featured);
        END IF;
    END IF;
END $$;

-- Create function to find itineraries by duration
CREATE OR REPLACE FUNCTION find_itineraries_by_duration(
    min_days INTEGER,
    max_days INTEGER,
    limit_param INTEGER DEFAULT 10
)
RETURNS TABLE (
    id INTEGER,
    name JSONB,
    description JSONB,
    category_id VARCHAR(50),
    duration_days INTEGER,
    difficulty_level VARCHAR(20),
    suitable_for JSONB,
    destinations JSONB,
    highlights JSONB,
    estimated_budget JSONB,
    tags TEXT[],
    is_featured BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        i.id, i.name, i.description, i.category_id, i.duration_days, i.difficulty_level,
        i.suitable_for, i.destinations, i.highlights, i.estimated_budget, i.tags, i.is_featured
    FROM 
        itineraries i
    WHERE 
        i.duration_days BETWEEN min_days AND max_days
    ORDER BY 
        i.is_featured DESC,
        i.duration_days ASC
    LIMIT 
        limit_param;
END;
$$ LANGUAGE plpgsql;

-- Create function to find itineraries by category
CREATE OR REPLACE FUNCTION find_itineraries_by_category(
    category_id_param VARCHAR(50),
    limit_param INTEGER DEFAULT 10
)
RETURNS TABLE (
    id INTEGER,
    name JSONB,
    description JSONB,
    category_id VARCHAR(50),
    duration_days INTEGER,
    difficulty_level VARCHAR(20),
    suitable_for JSONB,
    destinations JSONB,
    highlights JSONB,
    estimated_budget JSONB,
    tags TEXT[],
    is_featured BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        i.id, i.name, i.description, i.category_id, i.duration_days, i.difficulty_level,
        i.suitable_for, i.destinations, i.highlights, i.estimated_budget, i.tags, i.is_featured
    FROM 
        itineraries i
    WHERE 
        i.category_id = category_id_param
    ORDER BY 
        i.is_featured DESC,
        i.duration_days ASC
    LIMIT 
        limit_param;
END;
$$ LANGUAGE plpgsql;

-- Create function to search itineraries by text
CREATE OR REPLACE FUNCTION search_itineraries_by_text(
    search_text TEXT,
    limit_param INTEGER DEFAULT 10
)
RETURNS TABLE (
    id INTEGER,
    name JSONB,
    description JSONB,
    category_id VARCHAR(50),
    duration_days INTEGER,
    difficulty_level VARCHAR(20),
    suitable_for JSONB,
    destinations JSONB,
    highlights JSONB,
    estimated_budget JSONB,
    tags TEXT[],
    is_featured BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        i.id, i.name, i.description, i.category_id, i.duration_days, i.difficulty_level,
        i.suitable_for, i.destinations, i.highlights, i.estimated_budget, i.tags, i.is_featured
    FROM 
        itineraries i
    WHERE 
        i.name::TEXT ILIKE '%' || search_text || '%'
        OR i.description::TEXT ILIKE '%' || search_text || '%'
        OR search_text = ANY(i.tags)
        OR i.destinations::TEXT ILIKE '%' || search_text || '%'
    ORDER BY 
        i.is_featured DESC,
        i.duration_days ASC
    LIMIT 
        limit_param;
END;
$$ LANGUAGE plpgsql;
