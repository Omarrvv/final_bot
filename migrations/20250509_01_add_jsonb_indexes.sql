-- Migration: add_jsonb_indexes
-- Version: 20250509_01
-- Created: 2025-05-09T19:32:52.680219
-- Description: Add recommended JSONB indexes to improve query performance

-- Add GIN indexes for JSONB columns
DO $$
BEGIN
    -- Add GIN index to accommodations.data
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'accommodations' AND indexname = 'idx_accommodations_data_gin'
    ) THEN
        CREATE INDEX idx_accommodations_data_gin ON accommodations USING GIN (data);
        RAISE NOTICE 'Created GIN index on accommodations.data';
    ELSE
        RAISE NOTICE 'GIN index on accommodations.data already exists';
    END IF;

    -- Add GIN index to analytics.event_data
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'analytics' AND indexname = 'idx_analytics_event_data_gin'
    ) THEN
        CREATE INDEX idx_analytics_event_data_gin ON analytics USING GIN (event_data);
        RAISE NOTICE 'Created GIN index on analytics.event_data';
    ELSE
        RAISE NOTICE 'GIN index on analytics.event_data already exists';
    END IF;

    -- Add GIN index to attractions.data
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'attractions' AND indexname = 'idx_attractions_data_gin'
    ) THEN
        CREATE INDEX idx_attractions_data_gin ON attractions USING GIN (data);
        RAISE NOTICE 'Created GIN index on attractions.data';
    ELSE
        RAISE NOTICE 'GIN index on attractions.data already exists';
    END IF;

    -- Add GIN index to sessions.data
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'sessions' AND indexname = 'idx_sessions_data_gin'
    ) THEN
        CREATE INDEX idx_sessions_data_gin ON sessions USING GIN (data);
        RAISE NOTICE 'Created GIN index on sessions.data';
    ELSE
        RAISE NOTICE 'GIN index on sessions.data already exists';
    END IF;
END $$;

-- Add expression indexes for specific JSONB fields
DO $$
BEGIN
    -- Add expression index for regions.name->ar
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'regions' AND indexname = 'idx_regions_name_ar'
    ) THEN
        CREATE INDEX idx_regions_name_ar ON regions ((name->'ar'));
        RAISE NOTICE 'Created expression index on regions.name->ar';
    ELSE
        RAISE NOTICE 'Expression index on regions.name->ar already exists';
    END IF;

    -- Add expression index for regions.name->en
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'regions' AND indexname = 'idx_regions_name_en'
    ) THEN
        CREATE INDEX idx_regions_name_en ON regions ((name->'en'));
        RAISE NOTICE 'Created expression index on regions.name->en';
    ELSE
        RAISE NOTICE 'Expression index on regions.name->en already exists';
    END IF;

    -- Add expression index for restaurants.data->name
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'restaurants' AND indexname = 'idx_restaurants_data_name'
    ) THEN
        CREATE INDEX idx_restaurants_data_name ON restaurants ((data->'name'));
        RAISE NOTICE 'Created expression index on restaurants.data->name';
    ELSE
        RAISE NOTICE 'Expression index on restaurants.data->name already exists';
    END IF;

    -- Add expression index for restaurants.data->description
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'restaurants' AND indexname = 'idx_restaurants_data_description'
    ) THEN
        CREATE INDEX idx_restaurants_data_description ON restaurants ((data->'description'));
        RAISE NOTICE 'Created expression index on restaurants.data->description';
    ELSE
        RAISE NOTICE 'Expression index on restaurants.data->description already exists';
    END IF;
END $$;

-- Add commonly used expression indexes for multilingual fields
DO $$
BEGIN
    -- Add expression indexes for cities.name->en and cities.name->ar
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'cities' AND indexname = 'idx_cities_name_en'
    ) THEN
        CREATE INDEX idx_cities_name_en ON cities ((name->'en'));
        RAISE NOTICE 'Created expression index on cities.name->en';
    ELSE
        RAISE NOTICE 'Expression index on cities.name->en already exists';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'cities' AND indexname = 'idx_cities_name_ar'
    ) THEN
        CREATE INDEX idx_cities_name_ar ON cities ((name->'ar'));
        RAISE NOTICE 'Created expression index on cities.name->ar';
    ELSE
        RAISE NOTICE 'Expression index on cities.name->ar already exists';
    END IF;

    -- Add expression indexes for attractions.name->en and attractions.name->ar
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'attractions' AND indexname = 'idx_attractions_name_en'
    ) THEN
        CREATE INDEX idx_attractions_name_en ON attractions ((name->'en'));
        RAISE NOTICE 'Created expression index on attractions.name->en';
    ELSE
        RAISE NOTICE 'Expression index on attractions.name->en already exists';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'attractions' AND indexname = 'idx_attractions_name_ar'
    ) THEN
        CREATE INDEX idx_attractions_name_ar ON attractions ((name->'ar'));
        RAISE NOTICE 'Created expression index on attractions.name->ar';
    ELSE
        RAISE NOTICE 'Expression index on attractions.name->ar already exists';
    END IF;

    -- Add expression indexes for accommodations.name->en and accommodations.name->ar
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'accommodations' AND indexname = 'idx_accommodations_name_en'
    ) THEN
        CREATE INDEX idx_accommodations_name_en ON accommodations ((name->'en'));
        RAISE NOTICE 'Created expression index on accommodations.name->en';
    ELSE
        RAISE NOTICE 'Expression index on accommodations.name->en already exists';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'accommodations' AND indexname = 'idx_accommodations_name_ar'
    ) THEN
        CREATE INDEX idx_accommodations_name_ar ON accommodations ((name->'ar'));
        RAISE NOTICE 'Created expression index on accommodations.name->ar';
    ELSE
        RAISE NOTICE 'Expression index on accommodations.name->ar already exists';
    END IF;
END $$;
