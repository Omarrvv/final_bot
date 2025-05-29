-- Migration: Implement Query Caching
-- Date: 2025-07-04
-- Part of Task 8.3: Performance Tuning - Query Caching

-- This migration implements caching for expensive queries

BEGIN;

-- Create a table to store cached query results
CREATE TABLE IF NOT EXISTS query_cache (
    cache_key TEXT PRIMARY KEY,
    query_text TEXT NOT NULL,
    result JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ NOT NULL,
    hit_count INTEGER DEFAULT 0
);

-- Create an index on the expiration time for efficient cleanup
CREATE INDEX IF NOT EXISTS idx_query_cache_expires_at ON query_cache(expires_at);

-- Create a function to get a cached result or execute the query
CREATE OR REPLACE FUNCTION get_cached_query(
    p_query TEXT,
    p_params JSONB DEFAULT NULL,
    p_ttl_seconds INTEGER DEFAULT 3600
) RETURNS JSONB AS $$
DECLARE
    v_cache_key TEXT;
    v_result JSONB;
    v_cached_result JSONB;
    v_now TIMESTAMPTZ;
BEGIN
    -- Generate a cache key based on the query and parameters
    v_cache_key := md5(p_query || COALESCE(p_params::TEXT, ''));
    v_now := NOW();

    -- Check if we have a valid cached result
    SELECT result INTO v_cached_result
    FROM query_cache
    WHERE cache_key = v_cache_key
    AND expires_at > v_now;

    -- If we have a cached result, update hit count and return it
    IF v_cached_result IS NOT NULL THEN
        UPDATE query_cache
        SET hit_count = hit_count + 1
        WHERE cache_key = v_cache_key;

        RETURN v_cached_result;
    END IF;

    -- Execute the query
    EXECUTE p_query INTO v_result;

    -- Cache the result
    INSERT INTO query_cache (cache_key, query_text, result, expires_at)
    VALUES (v_cache_key, p_query, v_result, v_now + (p_ttl_seconds || ' seconds')::INTERVAL)
    ON CONFLICT (cache_key)
    DO UPDATE SET
        result = v_result,
        created_at = v_now,
        expires_at = v_now + (p_ttl_seconds || ' seconds')::INTERVAL,
        hit_count = 0;

    RETURN v_result;
END;
$$ LANGUAGE plpgsql;

-- Create a function to clear expired cache entries
CREATE OR REPLACE FUNCTION clear_expired_cache() RETURNS INTEGER AS $$
DECLARE
    v_deleted_count INTEGER;
BEGIN
    DELETE FROM query_cache
    WHERE expires_at < NOW()
    RETURNING COUNT(*) INTO v_deleted_count;

    RETURN v_deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create a function to clear all cache entries
CREATE OR REPLACE FUNCTION clear_all_cache() RETURNS INTEGER AS $$
DECLARE
    v_deleted_count INTEGER;
BEGIN
    DELETE FROM query_cache
    RETURNING COUNT(*) INTO v_deleted_count;

    RETURN v_deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create a function to get cache statistics
CREATE OR REPLACE FUNCTION get_cache_stats() RETURNS TABLE (
    total_entries INTEGER,
    expired_entries INTEGER,
    total_size_bytes BIGINT,
    avg_hit_count NUMERIC,
    max_hit_count INTEGER,
    oldest_entry_age INTERVAL,
    newest_entry_age INTERVAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*)::INTEGER AS total_entries,
        COUNT(*) FILTER (WHERE expires_at < NOW())::INTEGER AS expired_entries,
        SUM(pg_column_size(result))::BIGINT AS total_size_bytes,
        AVG(hit_count)::NUMERIC AS avg_hit_count,
        MAX(hit_count)::INTEGER AS max_hit_count,
        NOW() - MIN(created_at) AS oldest_entry_age,
        NOW() - MAX(created_at) AS newest_entry_age
    FROM query_cache;
END;
$$ LANGUAGE plpgsql;

-- Create cached versions of expensive queries

-- 1. Cached version of nearby attractions query
CREATE OR REPLACE FUNCTION cached_nearby_attractions(
    p_latitude DOUBLE PRECISION,
    p_longitude DOUBLE PRECISION,
    p_radius_km DOUBLE PRECISION DEFAULT 5.0,
    p_limit INTEGER DEFAULT 10,
    p_ttl_seconds INTEGER DEFAULT 3600
) RETURNS JSONB AS $$
DECLARE
    v_query TEXT;
    v_params JSONB;
BEGIN
    v_query := '
        SELECT json_agg(t) FROM (
            SELECT *,
                   ST_Distance(
                       geom,
                       ST_SetSRID(ST_MakePoint($1, $2), 4326),
                       true
                   ) / 1000 AS distance_km
            FROM attractions
            WHERE ST_DWithin(
                geom,
                ST_SetSRID(ST_MakePoint($1, $2), 4326),
                $3 * 1000
            )
            ORDER BY distance_km
            LIMIT $4
        ) t
    ';

    v_params := jsonb_build_object(
        '1', p_longitude,
        '2', p_latitude,
        '3', p_radius_km,
        '4', p_limit
    );

    RETURN get_cached_query(v_query, v_params, p_ttl_seconds);
END;
$$ LANGUAGE plpgsql;

-- 2. Cached version of vector search query
CREATE OR REPLACE FUNCTION cached_vector_search(
    p_table_name TEXT,
    p_embedding TEXT,
    p_limit INTEGER DEFAULT 10,
    p_ttl_seconds INTEGER DEFAULT 3600
) RETURNS JSONB AS $$
DECLARE
    v_query TEXT;
    v_params JSONB;
BEGIN
    v_query := '
        SELECT json_agg(t) FROM (
            SELECT *, embedding <-> $1::vector AS distance
            FROM ' || quote_ident(p_table_name) || '
            WHERE embedding IS NOT NULL
            ORDER BY distance
            LIMIT $2
        ) t
    ';

    v_params := jsonb_build_object(
        '1', p_embedding,
        '2', p_limit
    );

    RETURN get_cached_query(v_query, v_params, p_ttl_seconds);
END;
$$ LANGUAGE plpgsql;

-- Create a scheduled job to clean up expired cache entries
-- This would typically be done with a cron job or similar mechanism
-- For PostgreSQL 12+, we could use pg_cron extension
-- For now, we'll just create a comment with instructions

COMMENT ON FUNCTION clear_expired_cache() IS
'Run this function periodically to clean up expired cache entries.
Example cron job: 0 * * * * psql -c "SELECT clear_expired_cache()" egypt_chatbot';

-- Update the schema version if it doesn't exist
INSERT INTO schema_migrations (version, name, applied_at, checksum, execution_time, status)
VALUES ('20250704', 'implement_query_caching', NOW(), md5('20250704_implement_query_caching'), 0, 'success')
ON CONFLICT (version) DO NOTHING;

COMMIT;
