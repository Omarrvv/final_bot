-- migrations/20250708_optimize_connection_pooling.sql
-- Optimize connection pooling and implement monitoring

-- Transaction to ensure all changes are applied atomically
BEGIN;

-- Alter connection pool monitoring table to add new columns
DO $$
BEGIN
    -- Add hour column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                  WHERE table_name = 'connection_pool_stats' AND column_name = 'hour') THEN
        ALTER TABLE connection_pool_stats ADD COLUMN hour TIMESTAMP WITH TIME ZONE;
    END IF;

    -- Add total_connections column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                  WHERE table_name = 'connection_pool_stats' AND column_name = 'total_connections') THEN
        ALTER TABLE connection_pool_stats ADD COLUMN total_connections INTEGER;
    END IF;

    -- Add waiting_clients column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                  WHERE table_name = 'connection_pool_stats' AND column_name = 'waiting_clients') THEN
        ALTER TABLE connection_pool_stats ADD COLUMN waiting_clients INTEGER;
    END IF;

    -- Add max_wait_time_ms column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                  WHERE table_name = 'connection_pool_stats' AND column_name = 'max_wait_time_ms') THEN
        ALTER TABLE connection_pool_stats ADD COLUMN max_wait_time_ms DOUBLE PRECISION;
    END IF;
END $$;

-- Create index on hour for efficient querying
CREATE INDEX IF NOT EXISTS idx_connection_pool_stats_hour ON connection_pool_stats(hour);

-- Create a function to record connection pool statistics
CREATE OR REPLACE FUNCTION record_connection_pool_stats(
    p_min_connections INTEGER,
    p_max_connections INTEGER,
    p_active_connections INTEGER,
    p_total_connections INTEGER,
    p_idle_connections INTEGER,
    p_waiting_clients INTEGER,
    p_avg_wait_time_ms DOUBLE PRECISION,
    p_max_wait_time_ms DOUBLE PRECISION,
    p_total_queries INTEGER,
    p_error_count INTEGER
) RETURNS VOID AS $$
DECLARE
    current_hour TIMESTAMP WITH TIME ZONE;
BEGIN
    -- Round to the current hour
    current_hour := date_trunc('hour', NOW());

    -- Insert or update the statistics for the current hour
    INSERT INTO connection_pool_stats (
        hour,
        min_connections,
        max_connections,
        active_connections,
        total_connections,
        idle_connections,
        waiting_clients,
        avg_wait_time_ms,
        max_wait_time_ms,
        total_queries,
        error_count
    ) VALUES (
        current_hour,
        p_min_connections,
        p_max_connections,
        p_active_connections,
        p_total_connections,
        p_idle_connections,
        p_waiting_clients,
        p_avg_wait_time_ms,
        p_max_wait_time_ms,
        p_total_queries,
        p_error_count
    )
    ON CONFLICT (hour) DO UPDATE SET
        active_connections = p_active_connections,
        total_connections = p_total_connections,
        idle_connections = p_idle_connections,
        waiting_clients = p_waiting_clients,
        avg_wait_time_ms = p_avg_wait_time_ms,
        max_wait_time_ms = GREATEST(connection_pool_stats.max_wait_time_ms, p_max_wait_time_ms),
        total_queries = p_total_queries,
        error_count = p_error_count,
        timestamp = CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- Create a function to get connection pool statistics
CREATE OR REPLACE FUNCTION get_connection_pool_stats(
    p_hours INTEGER DEFAULT 24
) RETURNS TABLE (
    hour TIMESTAMP WITH TIME ZONE,
    min_connections INTEGER,
    max_connections INTEGER,
    active_connections INTEGER,
    total_connections INTEGER,
    idle_connections INTEGER,
    waiting_clients INTEGER,
    avg_wait_time_ms DOUBLE PRECISION,
    max_wait_time_ms DOUBLE PRECISION,
    total_queries INTEGER,
    error_count INTEGER,
    query_error_rate DOUBLE PRECISION
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        cps.hour,
        cps.min_connections,
        cps.max_connections,
        cps.active_connections,
        cps.total_connections,
        cps.idle_connections,
        cps.waiting_clients,
        cps.avg_wait_time_ms,
        cps.max_wait_time_ms,
        cps.total_queries,
        cps.error_count,
        CASE
            WHEN cps.total_queries > 0 THEN
                (cps.error_count::DOUBLE PRECISION / cps.total_queries::DOUBLE PRECISION) * 100.0
            ELSE 0.0
        END AS query_error_rate
    FROM connection_pool_stats cps
    WHERE cps.hour >= (NOW() - (p_hours || ' hours')::INTERVAL)
    ORDER BY cps.hour DESC;
END;
$$ LANGUAGE plpgsql;

-- Create a function to clean old connection pool statistics
CREATE OR REPLACE FUNCTION clean_old_connection_pool_stats(
    p_days INTEGER DEFAULT 30
) RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    WITH deleted AS (
        DELETE FROM connection_pool_stats
        WHERE hour < (NOW() - (p_days || ' days')::INTERVAL)
        RETURNING *
    )
    SELECT COUNT(*) INTO deleted_count FROM deleted;

    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create a function to get current database connection statistics
CREATE OR REPLACE FUNCTION get_current_db_connections() RETURNS TABLE (
    database_name TEXT,
    total_connections BIGINT,
    active_connections BIGINT,
    idle_connections BIGINT,
    idle_in_transaction BIGINT,
    longest_transaction_seconds BIGINT,
    longest_query_seconds BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        datname::TEXT AS database_name,
        COUNT(*)::BIGINT AS total_connections,
        COUNT(*) FILTER (WHERE state = 'active')::BIGINT AS active_connections,
        COUNT(*) FILTER (WHERE state = 'idle')::BIGINT AS idle_connections,
        COUNT(*) FILTER (WHERE state = 'idle in transaction')::BIGINT AS idle_in_transaction,
        COALESCE(MAX(EXTRACT(EPOCH FROM (NOW() - xact_start))) FILTER (WHERE xact_start IS NOT NULL), 0)::BIGINT AS longest_transaction_seconds,
        COALESCE(MAX(EXTRACT(EPOCH FROM (NOW() - query_start))) FILTER (WHERE query_start IS NOT NULL), 0)::BIGINT AS longest_query_seconds
    FROM pg_stat_activity
    WHERE datname = current_database()
    GROUP BY datname;
END;
$$ LANGUAGE plpgsql;

-- Update schema_migrations table
INSERT INTO schema_migrations (version, name, applied_at, checksum, execution_time, status)
VALUES ('20250708', 'optimize_connection_pooling', NOW(), md5('20250708_optimize_connection_pooling'), 0, 'success')
ON CONFLICT (version) DO NOTHING;

COMMIT;
