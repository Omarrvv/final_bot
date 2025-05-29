-- Migration: Optimize Connection Pooling
-- Date: 2025-07-02
-- Part of Task 8.2: Connection Pooling Optimization

-- This migration adds functions and tables to monitor and optimize connection pooling

BEGIN;

-- Create a table to track connection pool statistics
CREATE TABLE IF NOT EXISTS connection_pool_stats (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    min_connections INTEGER,
    max_connections INTEGER,
    current_connections INTEGER,
    available_connections INTEGER,
    acquisition_time_ms DOUBLE PRECISION,
    query_count INTEGER,
    error_count INTEGER
);

-- Create a function to record connection pool statistics
CREATE OR REPLACE FUNCTION record_connection_pool_stats(
    p_min_connections INTEGER,
    p_max_connections INTEGER,
    p_current_connections INTEGER,
    p_available_connections INTEGER,
    p_acquisition_time_ms DOUBLE PRECISION,
    p_query_count INTEGER,
    p_error_count INTEGER
) RETURNS VOID AS $$
BEGIN
    INSERT INTO connection_pool_stats (
        min_connections,
        max_connections,
        current_connections,
        available_connections,
        acquisition_time_ms,
        query_count,
        error_count
    ) VALUES (
        p_min_connections,
        p_max_connections,
        p_current_connections,
        p_available_connections,
        p_acquisition_time_ms,
        p_query_count,
        p_error_count
    );
END;
$$ LANGUAGE plpgsql;

-- Create a function to get connection pool recommendations
CREATE OR REPLACE FUNCTION get_connection_pool_recommendations() RETURNS TABLE (
    recommendation TEXT,
    current_value TEXT,
    suggested_value TEXT,
    priority INTEGER
) AS $$
DECLARE
    avg_connections INTEGER;
    max_used_connections INTEGER;
    avg_acquisition_time DOUBLE PRECISION;
    max_acquisition_time DOUBLE PRECISION;
    connection_errors INTEGER;
    current_max_connections INTEGER;
BEGIN
    -- Get statistics from the last 24 hours
    SELECT
        AVG(current_connections)::INTEGER,
        MAX(current_connections),
        AVG(acquisition_time_ms),
        MAX(acquisition_time_ms),
        SUM(error_count),
        MAX(max_connections)
    INTO
        avg_connections,
        max_used_connections,
        avg_acquisition_time,
        max_acquisition_time,
        connection_errors,
        current_max_connections
    FROM connection_pool_stats
    WHERE timestamp > NOW() - INTERVAL '24 hours';

    -- Recommend minimum connections
    IF avg_connections > 0 THEN
        recommendation := 'Minimum Connections';
        current_value := (SELECT MIN(min_connections)::TEXT FROM connection_pool_stats LIMIT 1);
        suggested_value := GREATEST(1, (avg_connections / 2)::INTEGER)::TEXT;
        priority := CASE
            WHEN avg_acquisition_time > 50 THEN 1  -- High priority if acquisition time is high
            ELSE 3  -- Low priority otherwise
        END;
        RETURN NEXT;
    END IF;

    -- Recommend maximum connections
    IF max_used_connections > 0 AND current_max_connections > 0 THEN
        recommendation := 'Maximum Connections';
        current_value := current_max_connections::TEXT;

        -- If we're using more than 80% of max connections, increase
        IF max_used_connections > (current_max_connections * 0.8) THEN
            suggested_value := LEAST(100, (current_max_connections * 1.5)::INTEGER)::TEXT;
            priority := 1;  -- High priority
        -- If we're using less than 30% of max connections, decrease
        ELSIF max_used_connections < (current_max_connections * 0.3) THEN
            suggested_value := GREATEST(5, (current_max_connections * 0.7)::INTEGER)::TEXT;
            priority := 2;  -- Medium priority
        ELSE
            suggested_value := current_max_connections::TEXT;
            priority := 4;  -- Very low priority
        END IF;

        RETURN NEXT;
    END IF;

    -- Recommend connection validation if errors are high
    IF connection_errors > 10 THEN
        recommendation := 'Connection Validation';
        current_value := 'Not enabled';
        suggested_value := 'Enable';
        priority := 1;  -- High priority
        RETURN NEXT;
    END IF;

    -- Recommend connection timeout if acquisition time is high
    IF max_acquisition_time > 1000 THEN  -- More than 1 second
        recommendation := 'Connection Timeout';
        current_value := 'Default';
        suggested_value := '5 seconds';
        priority := 1;  -- High priority
        RETURN NEXT;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Create a view for connection pool monitoring
CREATE OR REPLACE VIEW connection_pool_monitoring AS
SELECT
    date_trunc('hour', timestamp) AS hour,
    AVG(current_connections) AS avg_connections,
    MAX(current_connections) AS max_connections,
    AVG(acquisition_time_ms) AS avg_acquisition_time_ms,
    MAX(acquisition_time_ms) AS max_acquisition_time_ms,
    SUM(query_count) AS total_queries,
    SUM(error_count) AS total_errors
FROM connection_pool_stats
GROUP BY date_trunc('hour', timestamp)
ORDER BY hour DESC;

-- Update the schema version if it doesn't exist
INSERT INTO schema_migrations (version, name, applied_at, checksum, execution_time, status)
VALUES ('20250702', 'optimize_connection_pooling', NOW(), md5('20250702_optimize_connection_pooling'), 0, 'success')
ON CONFLICT (version) DO NOTHING;

COMMIT;
