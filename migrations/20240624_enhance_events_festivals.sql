-- Migration: Enhance Events and Festivals Tables
-- Description: This migration enhances the events_festivals table and adds event_categories table

-- Check if event_categories table exists, if not create it
CREATE TABLE IF NOT EXISTS event_categories (
    id VARCHAR(50) PRIMARY KEY,
    name JSONB NOT NULL,
    description JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add index on name for event_categories
CREATE INDEX IF NOT EXISTS idx_event_categories_name ON event_categories USING GIN (name);

-- Check if events_festivals table exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'events_festivals') THEN
        -- Create events_festivals table if it doesn't exist
        CREATE TABLE events_festivals (
            id SERIAL PRIMARY KEY,
            name JSONB NOT NULL,
            description JSONB,
            category_id VARCHAR(50) REFERENCES event_categories(id),
            location JSONB,
            start_date DATE,
            end_date DATE,
            recurring BOOLEAN DEFAULT FALSE,
            frequency VARCHAR(100),
            ticket_info JSONB,
            website VARCHAR(255),
            contact_info JSONB,
            images JSONB,
            tags TEXT[],
            data JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- Add indexes
        CREATE INDEX idx_events_festivals_name ON events_festivals USING GIN (name);
        CREATE INDEX idx_events_festivals_category_id ON events_festivals (category_id);
        CREATE INDEX idx_events_festivals_tags ON events_festivals USING GIN (tags);
        CREATE INDEX idx_events_festivals_start_date ON events_festivals (start_date);
        CREATE INDEX idx_events_festivals_end_date ON events_festivals (end_date);
    ELSE
        -- Alter existing events_festivals table to ensure it has all required columns
        
        -- Check and add category_id column if it doesn't exist
        IF NOT EXISTS (SELECT FROM information_schema.columns 
                       WHERE table_name = 'events_festivals' AND column_name = 'category_id') THEN
            ALTER TABLE events_festivals ADD COLUMN category_id VARCHAR(50) REFERENCES event_categories(id);
            CREATE INDEX idx_events_festivals_category_id ON events_festivals (category_id);
        END IF;
        
        -- Check and add location column if it doesn't exist
        IF NOT EXISTS (SELECT FROM information_schema.columns 
                       WHERE table_name = 'events_festivals' AND column_name = 'location') THEN
            ALTER TABLE events_festivals ADD COLUMN location JSONB;
        END IF;
        
        -- Check and add recurring column if it doesn't exist
        IF NOT EXISTS (SELECT FROM information_schema.columns 
                       WHERE table_name = 'events_festivals' AND column_name = 'recurring') THEN
            ALTER TABLE events_festivals ADD COLUMN recurring BOOLEAN DEFAULT FALSE;
        END IF;
        
        -- Check and add frequency column if it doesn't exist
        IF NOT EXISTS (SELECT FROM information_schema.columns 
                       WHERE table_name = 'events_festivals' AND column_name = 'frequency') THEN
            ALTER TABLE events_festivals ADD COLUMN frequency VARCHAR(100);
        END IF;
        
        -- Check and add ticket_info column if it doesn't exist
        IF NOT EXISTS (SELECT FROM information_schema.columns 
                       WHERE table_name = 'events_festivals' AND column_name = 'ticket_info') THEN
            ALTER TABLE events_festivals ADD COLUMN ticket_info JSONB;
        END IF;
        
        -- Check and add website column if it doesn't exist
        IF NOT EXISTS (SELECT FROM information_schema.columns 
                       WHERE table_name = 'events_festivals' AND column_name = 'website') THEN
            ALTER TABLE events_festivals ADD COLUMN website VARCHAR(255);
        END IF;
        
        -- Check and add contact_info column if it doesn't exist
        IF NOT EXISTS (SELECT FROM information_schema.columns 
                       WHERE table_name = 'events_festivals' AND column_name = 'contact_info') THEN
            ALTER TABLE events_festivals ADD COLUMN contact_info JSONB;
        END IF;
        
        -- Check and add images column if it doesn't exist
        IF NOT EXISTS (SELECT FROM information_schema.columns 
                       WHERE table_name = 'events_festivals' AND column_name = 'images') THEN
            ALTER TABLE events_festivals ADD COLUMN images JSONB;
        END IF;
        
        -- Check and add data column if it doesn't exist
        IF NOT EXISTS (SELECT FROM information_schema.columns 
                       WHERE table_name = 'events_festivals' AND column_name = 'data') THEN
            ALTER TABLE events_festivals ADD COLUMN data JSONB;
        END IF;
        
        -- Ensure name and description are JSONB
        ALTER TABLE events_festivals 
        ALTER COLUMN name TYPE JSONB USING name::JSONB,
        ALTER COLUMN description TYPE JSONB USING description::JSONB;
        
        -- Add missing indexes if they don't exist
        IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_events_festivals_name') THEN
            CREATE INDEX idx_events_festivals_name ON events_festivals USING GIN (name);
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_events_festivals_tags') THEN
            CREATE INDEX idx_events_festivals_tags ON events_festivals USING GIN (tags);
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_events_festivals_start_date') THEN
            CREATE INDEX idx_events_festivals_start_date ON events_festivals (start_date);
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_events_festivals_end_date') THEN
            CREATE INDEX idx_events_festivals_end_date ON events_festivals (end_date);
        END IF;
    END IF;
END $$;

-- Create function to find events by date range
CREATE OR REPLACE FUNCTION find_events_by_date_range(
    start_date_param DATE,
    end_date_param DATE,
    limit_param INTEGER DEFAULT 10
)
RETURNS TABLE (
    id INTEGER,
    name JSONB,
    description JSONB,
    category_id VARCHAR(50),
    location JSONB,
    start_date DATE,
    end_date DATE,
    recurring BOOLEAN,
    frequency VARCHAR(100),
    ticket_info JSONB,
    website VARCHAR(255),
    contact_info JSONB,
    images JSONB,
    tags TEXT[],
    data JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.id, e.name, e.description, e.category_id, e.location, 
        e.start_date, e.end_date, e.recurring, e.frequency, 
        e.ticket_info, e.website, e.contact_info, e.images, e.tags, e.data
    FROM 
        events_festivals e
    WHERE 
        (e.start_date BETWEEN start_date_param AND end_date_param)
        OR (e.end_date BETWEEN start_date_param AND end_date_param)
        OR (e.start_date <= start_date_param AND e.end_date >= end_date_param)
    ORDER BY 
        e.start_date ASC
    LIMIT 
        limit_param;
END;
$$ LANGUAGE plpgsql;

-- Create function to find events by category
CREATE OR REPLACE FUNCTION find_events_by_category(
    category_id_param VARCHAR(50),
    limit_param INTEGER DEFAULT 10
)
RETURNS TABLE (
    id INTEGER,
    name JSONB,
    description JSONB,
    category_id VARCHAR(50),
    location JSONB,
    start_date DATE,
    end_date DATE,
    recurring BOOLEAN,
    frequency VARCHAR(100),
    ticket_info JSONB,
    website VARCHAR(255),
    contact_info JSONB,
    images JSONB,
    tags TEXT[],
    data JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.id, e.name, e.description, e.category_id, e.location, 
        e.start_date, e.end_date, e.recurring, e.frequency, 
        e.ticket_info, e.website, e.contact_info, e.images, e.tags, e.data
    FROM 
        events_festivals e
    WHERE 
        e.category_id = category_id_param
    ORDER BY 
        e.start_date ASC
    LIMIT 
        limit_param;
END;
$$ LANGUAGE plpgsql;

-- Create function to search events by text
CREATE OR REPLACE FUNCTION search_events_by_text(
    search_text TEXT,
    limit_param INTEGER DEFAULT 10
)
RETURNS TABLE (
    id INTEGER,
    name JSONB,
    description JSONB,
    category_id VARCHAR(50),
    location JSONB,
    start_date DATE,
    end_date DATE,
    recurring BOOLEAN,
    frequency VARCHAR(100),
    ticket_info JSONB,
    website VARCHAR(255),
    contact_info JSONB,
    images JSONB,
    tags TEXT[],
    data JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.id, e.name, e.description, e.category_id, e.location, 
        e.start_date, e.end_date, e.recurring, e.frequency, 
        e.ticket_info, e.website, e.contact_info, e.images, e.tags, e.data
    FROM 
        events_festivals e
    WHERE 
        e.name::TEXT ILIKE '%' || search_text || '%'
        OR e.description::TEXT ILIKE '%' || search_text || '%'
        OR search_text = ANY(e.tags)
        OR e.location::TEXT ILIKE '%' || search_text || '%'
    ORDER BY 
        e.start_date ASC
    LIMIT 
        limit_param;
END;
$$ LANGUAGE plpgsql;
