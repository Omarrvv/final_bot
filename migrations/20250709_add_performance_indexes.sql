-- migrations/20250709_add_performance_indexes.sql
-- Add indexes for query performance optimization

-- Transaction to ensure all changes are applied atomically
BEGIN;

-- Create GIN indexes for JSONB columns
DO $$
BEGIN
    -- Check if attractions.name index exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'attractions' AND indexname = 'idx_attractions_name_gin'
    ) THEN
        CREATE INDEX idx_attractions_name_gin ON attractions USING GIN (name);
    END IF;
    
    -- Check if attractions.description index exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'attractions' AND indexname = 'idx_attractions_description_gin'
    ) THEN
        CREATE INDEX idx_attractions_description_gin ON attractions USING GIN (description);
    END IF;
    
    -- Check if restaurants.name index exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'restaurants' AND indexname = 'idx_restaurants_name_gin'
    ) THEN
        CREATE INDEX idx_restaurants_name_gin ON restaurants USING GIN (name);
    END IF;
    
    -- Check if restaurants.description index exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'restaurants' AND indexname = 'idx_restaurants_description_gin'
    ) THEN
        CREATE INDEX idx_restaurants_description_gin ON restaurants USING GIN (description);
    END IF;
    
    -- Check if accommodations.name index exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'accommodations' AND indexname = 'idx_accommodations_name_gin'
    ) THEN
        CREATE INDEX idx_accommodations_name_gin ON accommodations USING GIN (name);
    END IF;
    
    -- Check if accommodations.description index exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'accommodations' AND indexname = 'idx_accommodations_description_gin'
    ) THEN
        CREATE INDEX idx_accommodations_description_gin ON accommodations USING GIN (description);
    END IF;
    
    -- Check if cities.name index exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'cities' AND indexname = 'idx_cities_name_gin'
    ) THEN
        CREATE INDEX idx_cities_name_gin ON cities USING GIN (name);
    END IF;
    
    -- Check if cities.description index exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'cities' AND indexname = 'idx_cities_description_gin'
    ) THEN
        CREATE INDEX idx_cities_description_gin ON cities USING GIN (description);
    END IF;
END $$;

-- Create indexes for common query patterns
DO $$
BEGIN
    -- Check if attractions.city_id index exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'attractions' AND indexname = 'idx_attractions_city_id'
    ) THEN
        CREATE INDEX idx_attractions_city_id ON attractions (city_id);
    END IF;
    
    -- Check if attractions.type_id index exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'attractions' AND indexname = 'idx_attractions_type_id'
    ) THEN
        CREATE INDEX idx_attractions_type_id ON attractions (type_id);
    END IF;
    
    -- Check if restaurants.city_id index exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'restaurants' AND indexname = 'idx_restaurants_city_id'
    ) THEN
        CREATE INDEX idx_restaurants_city_id ON restaurants (city_id);
    END IF;
    
    -- Check if restaurants.cuisine_id index exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'restaurants' AND indexname = 'idx_restaurants_cuisine_id'
    ) THEN
        CREATE INDEX idx_restaurants_cuisine_id ON restaurants (cuisine_id);
    END IF;
    
    -- Check if accommodations.city_id index exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'accommodations' AND indexname = 'idx_accommodations_city_id'
    ) THEN
        CREATE INDEX idx_accommodations_city_id ON accommodations (city_id);
    END IF;
    
    -- Check if accommodations.stars index exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'accommodations' AND indexname = 'idx_accommodations_stars'
    ) THEN
        CREATE INDEX idx_accommodations_stars ON accommodations (stars);
    END IF;
    
    -- Check if cities.region_id index exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'cities' AND indexname = 'idx_cities_region_id'
    ) THEN
        CREATE INDEX idx_cities_region_id ON cities (region_id);
    END IF;
END $$;

-- Create spatial indexes for PostGIS columns
DO $$
BEGIN
    -- Check if attractions.geom index exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'attractions' AND indexname = 'idx_attractions_geom'
    ) THEN
        CREATE INDEX idx_attractions_geom ON attractions USING GIST (geom);
    END IF;
    
    -- Check if restaurants.geom index exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'restaurants' AND indexname = 'idx_restaurants_geom'
    ) THEN
        CREATE INDEX idx_restaurants_geom ON restaurants USING GIST (geom);
    END IF;
    
    -- Check if accommodations.geom index exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'accommodations' AND indexname = 'idx_accommodations_geom'
    ) THEN
        CREATE INDEX idx_accommodations_geom ON accommodations USING GIST (geom);
    END IF;
    
    -- Check if cities.geom index exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'cities' AND indexname = 'idx_cities_geom'
    ) THEN
        CREATE INDEX idx_cities_geom ON cities USING GIST (geom);
    END IF;
END $$;

-- Create a function to analyze query performance
CREATE OR REPLACE FUNCTION analyze_query_performance(
    query_text TEXT,
    params TEXT[] DEFAULT NULL
) RETURNS TABLE (
    plan_json JSONB,
    execution_time_ms DOUBLE PRECISION
) AS $$
DECLARE
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    execution_time DOUBLE PRECISION;
    explain_result JSONB;
BEGIN
    -- Get the execution plan
    EXECUTE 'EXPLAIN (FORMAT JSON) ' || query_text INTO explain_result USING params;
    
    -- Measure execution time
    start_time := clock_timestamp();
    EXECUTE query_text USING params;
    end_time := clock_timestamp();
    
    -- Calculate execution time in milliseconds
    execution_time := extract(epoch from (end_time - start_time)) * 1000;
    
    -- Return results
    RETURN QUERY SELECT explain_result, execution_time;
END;
$$ LANGUAGE plpgsql;

-- Update schema_migrations table
INSERT INTO schema_migrations (version, name, applied_at, checksum, execution_time, status)
VALUES ('20250709', 'add_performance_indexes', NOW(), md5('20250709_add_performance_indexes'), 0, 'success')
ON CONFLICT (version) DO NOTHING;

COMMIT;
