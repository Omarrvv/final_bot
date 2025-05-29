-- migrations/20250710_implement_selective_cache_invalidation.sql
-- Implement selective cache invalidation

-- Transaction to ensure all changes are applied atomically
BEGIN;

-- Add category column to query_cache table for selective invalidation
DO $$
BEGIN
    -- Add category column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'query_cache' AND column_name = 'category') THEN
        ALTER TABLE query_cache ADD COLUMN category TEXT;
    END IF;
    
    -- Create index on category for efficient invalidation
    IF NOT EXISTS (SELECT 1 FROM pg_indexes 
                  WHERE tablename = 'query_cache' AND indexname = 'idx_query_cache_category') THEN
        CREATE INDEX idx_query_cache_category ON query_cache(category);
    END IF;
END $$;

-- Create a function to set cache entry category
CREATE OR REPLACE FUNCTION set_cache_category(
    p_cache_key TEXT,
    p_category TEXT
) RETURNS BOOLEAN AS $$
DECLARE
    updated_rows INTEGER;
BEGIN
    UPDATE query_cache
    SET category = p_category
    WHERE cache_key = p_cache_key
    RETURNING 1 INTO updated_rows;
    
    RETURN updated_rows IS NOT NULL;
END;
$$ LANGUAGE plpgsql;

-- Create a function to invalidate cache by category
CREATE OR REPLACE FUNCTION invalidate_cache_by_category(
    p_category TEXT
) RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    WITH deleted AS (
        DELETE FROM query_cache
        WHERE category = p_category
        RETURNING *
    )
    SELECT COUNT(*) INTO deleted_count FROM deleted;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create a function to invalidate cache for a specific table
CREATE OR REPLACE FUNCTION invalidate_table_cache(
    p_table_name TEXT
) RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    WITH deleted AS (
        DELETE FROM query_cache
        WHERE category = p_table_name OR category LIKE p_table_name || ':%'
        RETURNING *
    )
    SELECT COUNT(*) INTO deleted_count FROM deleted;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create triggers to automatically invalidate cache when tables are modified
CREATE OR REPLACE FUNCTION invalidate_cache_on_table_change() RETURNS TRIGGER AS $$
BEGIN
    PERFORM invalidate_table_cache(TG_TABLE_NAME);
    RAISE NOTICE 'Invalidated cache for table: %', TG_TABLE_NAME;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for main tables
DO $$
DECLARE
    tables TEXT[] := ARRAY['attractions', 'restaurants', 'accommodations', 'cities', 'regions'];
    table_name TEXT;
BEGIN
    FOREACH table_name IN ARRAY tables LOOP
        -- Drop existing trigger if it exists
        EXECUTE format('DROP TRIGGER IF EXISTS trg_invalidate_cache_on_%s_change ON %s', table_name, table_name);
        
        -- Create new trigger
        EXECUTE format('
            CREATE TRIGGER trg_invalidate_cache_on_%s_change
            AFTER INSERT OR UPDATE OR DELETE ON %s
            FOR EACH STATEMENT
            EXECUTE FUNCTION invalidate_cache_on_table_change()
        ', table_name, table_name);
    END LOOP;
END $$;

-- Modify get_cached_query function to support categories
CREATE OR REPLACE FUNCTION get_cached_query(
    query_text TEXT,
    params JSONB,
    category TEXT DEFAULT NULL,
    ttl_seconds INTEGER DEFAULT 3600
) RETURNS JSONB AS $$
DECLARE
    cache_key_var TEXT;
    cached_result JSONB;
    query_result JSONB;
    curr_time TIMESTAMP;
    expiry_time TIMESTAMP;
    param_values TEXT[];
    i INTEGER;
    param_count INTEGER;
    dynamic_query TEXT;
BEGIN
    -- Generate cache key from query and parameters
    cache_key_var := md5(query_text || params::TEXT);
    
    -- Check if result is in cache
    SELECT result, expires_at INTO cached_result, expiry_time
    FROM query_cache
    WHERE query_cache.cache_key = cache_key_var;
    
    curr_time := NOW();
    
    -- If cached result exists and is not expired, return it
    IF cached_result IS NOT NULL AND expiry_time > curr_time THEN
        -- Update hit count
        UPDATE query_cache
        SET hit_count = query_cache.hit_count + 1
        WHERE query_cache.cache_key = cache_key_var;
        
        RETURN cached_result;
    END IF;
    
    -- Extract parameter values from JSONB array
    param_count := jsonb_array_length(params);
    param_values := ARRAY[]::TEXT[];
    
    -- Convert JSONB parameters to text array
    FOR i IN 0..(param_count-1) LOOP
        param_values := array_append(param_values, (params->i)::TEXT);
    END LOOP;
    
    -- Create dynamic query with proper parameter binding
    dynamic_query := 'SELECT json_agg(t) FROM (' || query_text || ') t';
    
    -- Execute the query with parameters, casting to appropriate types
    EXECUTE dynamic_query USING 
        CASE WHEN param_count > 0 THEN param_values[1]::DOUBLE PRECISION ELSE NULL END,
        CASE WHEN param_count > 1 THEN param_values[2]::DOUBLE PRECISION ELSE NULL END,
        CASE WHEN param_count > 2 THEN param_values[3]::DOUBLE PRECISION ELSE NULL END,
        CASE WHEN param_count > 3 THEN param_values[4]::INTEGER ELSE NULL END,
        CASE WHEN param_count > 4 THEN param_values[5] ELSE NULL END,
        CASE WHEN param_count > 5 THEN param_values[6] ELSE NULL END,
        CASE WHEN param_count > 6 THEN param_values[7] ELSE NULL END,
        CASE WHEN param_count > 7 THEN param_values[8] ELSE NULL END
    INTO query_result;
    
    -- Store result in cache
    INSERT INTO query_cache (cache_key, query_text, result, created_at, expires_at, hit_count, category)
    VALUES (cache_key_var, query_text, query_result, curr_time, curr_time + (ttl_seconds || ' seconds')::INTERVAL, 1, category)
    ON CONFLICT (cache_key) 
    DO UPDATE SET 
        query_text = EXCLUDED.query_text,
        result = EXCLUDED.result,
        expires_at = curr_time + (ttl_seconds || ' seconds')::INTERVAL,
        hit_count = query_cache.hit_count + 1,
        category = COALESCE(EXCLUDED.category, query_cache.category);
    
    RETURN query_result;
END;
$$ LANGUAGE plpgsql;

-- Update cached_nearby_attractions function to use categories
CREATE OR REPLACE FUNCTION cached_nearby_attractions(
    lat DOUBLE PRECISION,
    lng DOUBLE PRECISION,
    radius_km DOUBLE PRECISION DEFAULT 5.0,
    limit_val INTEGER DEFAULT 10,
    ttl_seconds INTEGER DEFAULT 3600
) RETURNS JSONB AS $$
DECLARE
    query_text TEXT;
    params JSONB;
BEGIN
    -- Define the query
    query_text := '
        SELECT *,
               ST_Distance(
                   geom,
                   ST_SetSRID(ST_MakePoint($2, $1), 4326),
                   true
               ) / 1000 AS distance_km
        FROM attractions
        WHERE ST_DWithin(
            geom,
            ST_SetSRID(ST_MakePoint($2, $1), 4326),
            $3 * 1000
        )
        ORDER BY distance_km
        LIMIT $4
    ';
    
    -- Create parameters array
    params := jsonb_build_array(lat, lng, radius_km, limit_val);
    
    -- Get cached or fresh result with category
    RETURN get_cached_query(query_text, params, 'attractions:spatial', ttl_seconds);
END;
$$ LANGUAGE plpgsql;

-- Update cached_nearby_restaurants function to use categories
CREATE OR REPLACE FUNCTION cached_nearby_restaurants(
    lat DOUBLE PRECISION,
    lng DOUBLE PRECISION,
    radius_km DOUBLE PRECISION DEFAULT 5.0,
    limit_val INTEGER DEFAULT 10,
    ttl_seconds INTEGER DEFAULT 3600
) RETURNS JSONB AS $$
DECLARE
    query_text TEXT;
    params JSONB;
BEGIN
    -- Define the query
    query_text := '
        SELECT *,
               ST_Distance(
                   geom,
                   ST_SetSRID(ST_MakePoint($2, $1), 4326),
                   true
               ) / 1000 AS distance_km
        FROM restaurants
        WHERE ST_DWithin(
            geom,
            ST_SetSRID(ST_MakePoint($2, $1), 4326),
            $3 * 1000
        )
        ORDER BY distance_km
        LIMIT $4
    ';
    
    -- Create parameters array
    params := jsonb_build_array(lat, lng, radius_km, limit_val);
    
    -- Get cached or fresh result with category
    RETURN get_cached_query(query_text, params, 'restaurants:spatial', ttl_seconds);
END;
$$ LANGUAGE plpgsql;

-- Update cached_nearby_accommodations function to use categories
CREATE OR REPLACE FUNCTION cached_nearby_accommodations(
    lat DOUBLE PRECISION,
    lng DOUBLE PRECISION,
    radius_km DOUBLE PRECISION DEFAULT 5.0,
    limit_val INTEGER DEFAULT 10,
    ttl_seconds INTEGER DEFAULT 3600
) RETURNS JSONB AS $$
DECLARE
    query_text TEXT;
    params JSONB;
BEGIN
    -- Define the query
    query_text := '
        SELECT *,
               ST_Distance(
                   geom,
                   ST_SetSRID(ST_MakePoint($2, $1), 4326),
                   true
               ) / 1000 AS distance_km
        FROM accommodations
        WHERE ST_DWithin(
            geom,
            ST_SetSRID(ST_MakePoint($2, $1), 4326),
            $3 * 1000
        )
        ORDER BY distance_km
        LIMIT $4
    ';
    
    -- Create parameters array
    params := jsonb_build_array(lat, lng, radius_km, limit_val);
    
    -- Get cached or fresh result with category
    RETURN get_cached_query(query_text, params, 'accommodations:spatial', ttl_seconds);
END;
$$ LANGUAGE plpgsql;

-- Update schema_migrations table
INSERT INTO schema_migrations (version, name, applied_at, checksum, execution_time, status)
VALUES ('20250710', 'implement_selective_cache_invalidation', NOW(), md5('20250710_implement_selective_cache_invalidation'), 0, 'success')
ON CONFLICT (version) DO NOTHING;

COMMIT;
