-- migrations/20250707_fix_spatial_queries.sql
-- Fix spatial queries and implement proper parameter binding

-- Transaction to ensure all changes are applied atomically
BEGIN;

-- Drop existing functions if they exist
DROP FUNCTION IF EXISTS cached_nearby_attractions;
DROP FUNCTION IF EXISTS get_cached_query;
DROP FUNCTION IF EXISTS get_cache_stats;

-- Create a function to handle cached queries with proper parameter binding
CREATE OR REPLACE FUNCTION get_cached_query(
    query_text TEXT,
    params JSONB,
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
    INSERT INTO query_cache (cache_key, query_text, result, created_at, expires_at, hit_count)
    VALUES (cache_key_var, query_text, query_result, curr_time, curr_time + (ttl_seconds || ' seconds')::INTERVAL, 1)
    ON CONFLICT (cache_key)
    DO UPDATE SET
        query_text = EXCLUDED.query_text,
        result = EXCLUDED.result,
        expires_at = curr_time + (ttl_seconds || ' seconds')::INTERVAL,
        hit_count = query_cache.hit_count + 1;

    RETURN query_result;
END;
$$ LANGUAGE plpgsql;

-- Create a function to find nearby attractions with caching
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

    -- Get cached or fresh result
    RETURN get_cached_query(query_text, params, ttl_seconds);
END;
$$ LANGUAGE plpgsql;

-- Create a function to find nearby restaurants with caching
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

    -- Get cached or fresh result
    RETURN get_cached_query(query_text, params, ttl_seconds);
END;
$$ LANGUAGE plpgsql;

-- Create a function to find nearby accommodations with caching
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

    -- Get cached or fresh result
    RETURN get_cached_query(query_text, params, ttl_seconds);
END;
$$ LANGUAGE plpgsql;

-- Create a function to get cache statistics
CREATE OR REPLACE FUNCTION get_cache_stats() RETURNS TABLE (
    total_entries INTEGER,
    hit_count BIGINT,
    avg_hits NUMERIC,
    oldest_entry TIMESTAMP WITH TIME ZONE,
    newest_entry TIMESTAMP WITH TIME ZONE,
    memory_usage_kb BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*)::INTEGER AS total_entries,
        SUM(qc.hit_count)::BIGINT AS hit_count,
        CASE WHEN COUNT(*) > 0 THEN (SUM(qc.hit_count)::NUMERIC / COUNT(*)::NUMERIC) ELSE 0 END AS avg_hits,
        MIN(qc.created_at) AS oldest_entry,
        MAX(qc.created_at) AS newest_entry,
        pg_total_relation_size('query_cache')::BIGINT / 1024 AS memory_usage_kb
    FROM query_cache qc;
END;
$$ LANGUAGE plpgsql;

-- Drop and recreate query_cache table
DROP TABLE IF EXISTS query_cache;

CREATE TABLE query_cache (
    cache_key TEXT PRIMARY KEY,
    query_text TEXT NOT NULL,
    result JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    hit_count INTEGER DEFAULT 0
);

-- Create index on expires_at for efficient cleanup
CREATE INDEX IF NOT EXISTS idx_query_cache_expires_at ON query_cache(expires_at);

-- Create a function to clean expired cache entries
CREATE OR REPLACE FUNCTION clean_expired_cache() RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    WITH deleted AS (
        DELETE FROM query_cache
        WHERE expires_at < NOW()
        RETURNING *
    )
    SELECT COUNT(*) INTO deleted_count FROM deleted;

    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Update schema_migrations table
INSERT INTO schema_migrations (version, name, applied_at, checksum, execution_time, status)
VALUES ('20250707', 'fix_spatial_queries', NOW(), md5('20250707_fix_spatial_queries'), 0, 'success')
ON CONFLICT (version) DO NOTHING;

COMMIT;
