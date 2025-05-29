--
-- PostgreSQL database dump
--

-- Dumped from database version 14.17 (Homebrew)
-- Dumped by pg_dump version 14.17 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: test_schema; Type: SCHEMA; Schema: -; Owner: omarmohamed
--

CREATE SCHEMA test_schema;


ALTER SCHEMA test_schema OWNER TO omarmohamed;

--
-- Name: pg_trgm; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;


--
-- Name: EXTENSION pg_trgm; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pg_trgm IS 'text similarity measurement and index searching based on trigrams';


--
-- Name: postgis; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA public;


--
-- Name: EXTENSION postgis; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION postgis IS 'PostGIS geometry and geography spatial types and functions';


--
-- Name: vector; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;


--
-- Name: EXTENSION vector; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION vector IS 'vector data type and ivfflat and hnsw access methods';


--
-- Name: add_language_to_jsonb(jsonb, text, text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.add_language_to_jsonb(json_data jsonb, text_value text, lang text) RETURNS jsonb
    LANGUAGE plpgsql IMMUTABLE
    AS $$
BEGIN
    -- Add a new language to an existing JSONB object
    RETURN json_data || jsonb_build_object(lang, text_value);
END;
$$;


ALTER FUNCTION public.add_language_to_jsonb(json_data jsonb, text_value text, lang text) OWNER TO postgres;

--
-- Name: analyze_query_patterns(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.analyze_query_patterns() RETURNS TABLE(table_name text, column_name text, query_count integer, avg_execution_time double precision, has_index boolean, index_name text, recommendation text)
    LANGUAGE plpgsql
    AS $$
DECLARE
    log_file TEXT;
    log_contents TEXT;
BEGIN
    -- This is a placeholder function that would normally analyze query logs
    -- In a real implementation, this would parse the query_metrics.log file
    -- and extract patterns of column usage in WHERE clauses

    -- For demonstration purposes, we'll return some hardcoded recommendations
    -- based on our knowledge of the application's query patterns

    -- Check for existing indexes on name and description JSONB fields
    RETURN QUERY
    SELECT
        t.table_name::TEXT,
        c.column_name::TEXT,
        100::INTEGER AS query_count, -- Placeholder count
        50.0::DOUBLE PRECISION AS avg_execution_time, -- Placeholder time in ms
        (EXISTS (
            SELECT 1 FROM pg_indexes
            WHERE tablename = t.table_name
            AND indexdef LIKE '%' || c.column_name || '%'
        ))::BOOLEAN AS has_index,
        (SELECT indexname FROM pg_indexes
         WHERE tablename = t.table_name
         AND indexdef LIKE '%' || c.column_name || '%'
         LIMIT 1)::TEXT AS index_name,
        CASE
            WHEN NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE tablename = t.table_name
                AND indexdef LIKE '%' || c.column_name || '%'
            ) THEN 'Create index'
            WHEN EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE tablename = t.table_name
                AND indexdef LIKE '%' || c.column_name || '%'
                AND indexdef NOT LIKE '%gin%'
                AND c.data_type = 'jsonb'
            ) THEN 'Convert to GIN index'
            ELSE 'No action needed'
        END AS recommendation
    FROM information_schema.tables t
    JOIN information_schema.columns c ON t.table_name = c.table_name
    WHERE t.table_schema = 'public'
    AND t.table_type = 'BASE TABLE'
    AND t.table_name IN ('attractions', 'restaurants', 'accommodations', 'cities')
    AND c.column_name IN ('name', 'description', 'data')
    AND c.data_type = 'jsonb';
END;
$$;


ALTER FUNCTION public.analyze_query_patterns() OWNER TO postgres;

--
-- Name: analyze_query_performance(text, text[]); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.analyze_query_performance(query_text text, params text[] DEFAULT NULL::text[]) RETURNS TABLE(plan_json jsonb, execution_time_ms double precision)
    LANGUAGE plpgsql
    AS $$
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
$$;


ALTER FUNCTION public.analyze_query_performance(query_text text, params text[]) OWNER TO postgres;

--
-- Name: cached_nearby_accommodations(double precision, double precision, double precision, integer, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.cached_nearby_accommodations(lat double precision, lng double precision, radius_km double precision DEFAULT 5.0, limit_val integer DEFAULT 10, ttl_seconds integer DEFAULT 3600) RETURNS jsonb
    LANGUAGE plpgsql
    AS $_$
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
$_$;


ALTER FUNCTION public.cached_nearby_accommodations(lat double precision, lng double precision, radius_km double precision, limit_val integer, ttl_seconds integer) OWNER TO postgres;

--
-- Name: cached_nearby_attractions(double precision, double precision, double precision, integer, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.cached_nearby_attractions(lat double precision, lng double precision, radius_km double precision DEFAULT 5.0, limit_val integer DEFAULT 10, ttl_seconds integer DEFAULT 3600) RETURNS jsonb
    LANGUAGE plpgsql
    AS $_$
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
$_$;


ALTER FUNCTION public.cached_nearby_attractions(lat double precision, lng double precision, radius_km double precision, limit_val integer, ttl_seconds integer) OWNER TO postgres;

--
-- Name: cached_nearby_restaurants(double precision, double precision, double precision, integer, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.cached_nearby_restaurants(lat double precision, lng double precision, radius_km double precision DEFAULT 5.0, limit_val integer DEFAULT 10, ttl_seconds integer DEFAULT 3600) RETURNS jsonb
    LANGUAGE plpgsql
    AS $_$
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
$_$;


ALTER FUNCTION public.cached_nearby_restaurants(lat double precision, lng double precision, radius_km double precision, limit_val integer, ttl_seconds integer) OWNER TO postgres;

--
-- Name: cached_vector_search(text, text, integer, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.cached_vector_search(p_table_name text, p_embedding text, p_limit integer DEFAULT 10, p_ttl_seconds integer DEFAULT 3600) RETURNS jsonb
    LANGUAGE plpgsql
    AS $_$
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
$_$;


ALTER FUNCTION public.cached_vector_search(p_table_name text, p_embedding text, p_limit integer, p_ttl_seconds integer) OWNER TO postgres;

--
-- Name: clean_expired_cache(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.clean_expired_cache() RETURNS integer
    LANGUAGE plpgsql
    AS $$
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
$$;


ALTER FUNCTION public.clean_expired_cache() OWNER TO postgres;

--
-- Name: clean_old_connection_pool_stats(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.clean_old_connection_pool_stats(p_days integer DEFAULT 30) RETURNS integer
    LANGUAGE plpgsql
    AS $$
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
$$;


ALTER FUNCTION public.clean_old_connection_pool_stats(p_days integer) OWNER TO postgres;

--
-- Name: clear_all_cache(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.clear_all_cache() RETURNS integer
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_deleted_count INTEGER;
BEGIN
    DELETE FROM query_cache
    RETURNING COUNT(*) INTO v_deleted_count;

    RETURN v_deleted_count;
END;
$$;


ALTER FUNCTION public.clear_all_cache() OWNER TO postgres;

--
-- Name: clear_expired_cache(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.clear_expired_cache() RETURNS integer
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_deleted_count INTEGER;
BEGIN
    DELETE FROM query_cache
    WHERE expires_at < NOW()
    RETURNING COUNT(*) INTO v_deleted_count;

    RETURN v_deleted_count;
END;
$$;


ALTER FUNCTION public.clear_expired_cache() OWNER TO postgres;

--
-- Name: FUNCTION clear_expired_cache(); Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON FUNCTION public.clear_expired_cache() IS 'Run this function periodically to clean up expired cache entries.
Example cron job: 0 * * * * psql -c "SELECT clear_expired_cache()" egypt_chatbot';


--
-- Name: create_language_jsonb(text, text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.create_language_jsonb(text_value text, lang text DEFAULT 'en'::text) RETURNS jsonb
    LANGUAGE plpgsql IMMUTABLE
    AS $$
BEGIN
    -- Create a new JSONB object with the specified language
    RETURN jsonb_build_object(lang, text_value);
END;
$$;


ALTER FUNCTION public.create_language_jsonb(text_value text, lang text) OWNER TO postgres;

--
-- Name: find_related_attractions(text, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.find_related_attractions(p_attraction_id text, p_limit integer DEFAULT 5) RETURNS TABLE(id text, name jsonb, type text, subcategory_id text, city_id text, region_id text)
    LANGUAGE plpgsql
    AS $$
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
$$;


ALTER FUNCTION public.find_related_attractions(p_attraction_id text, p_limit integer) OWNER TO postgres;

--
-- Name: find_routes_from_destination(text, text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.find_routes_from_destination(p_origin_id text, p_transportation_type text DEFAULT NULL::text) RETURNS TABLE(id integer, origin_id text, destination_id text, destination_name jsonb, transportation_type text, name jsonb, distance_km double precision, duration_minutes integer, price_range jsonb)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.id,
        r.origin_id,
        r.destination_id,
        d.name AS destination_name,
        r.transportation_type,
        r.name,
        r.distance_km,
        r.duration_minutes,
        r.price_range
    FROM 
        transportation_routes r
    JOIN
        destinations d ON r.destination_id = d.id
    WHERE 
        r.origin_id = p_origin_id
        AND (p_transportation_type IS NULL OR r.transportation_type = p_transportation_type)
    ORDER BY 
        r.transportation_type, r.duration_minutes ASC;
END;
$$;


ALTER FUNCTION public.find_routes_from_destination(p_origin_id text, p_transportation_type text) OWNER TO postgres;

--
-- Name: find_routes_to_destination(text, text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.find_routes_to_destination(p_destination_id text, p_transportation_type text DEFAULT NULL::text) RETURNS TABLE(id integer, origin_id text, origin_name jsonb, destination_id text, transportation_type text, name jsonb, distance_km double precision, duration_minutes integer, price_range jsonb)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.id,
        r.origin_id,
        d.name AS origin_name,
        r.destination_id,
        r.transportation_type,
        r.name,
        r.distance_km,
        r.duration_minutes,
        r.price_range
    FROM 
        transportation_routes r
    JOIN
        destinations d ON r.origin_id = d.id
    WHERE 
        r.destination_id = p_destination_id
        AND (p_transportation_type IS NULL OR r.transportation_type = p_transportation_type)
    ORDER BY 
        r.transportation_type, r.duration_minutes ASC;
END;
$$;


ALTER FUNCTION public.find_routes_to_destination(p_destination_id text, p_transportation_type text) OWNER TO postgres;

--
-- Name: find_transportation_routes(text, text, text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.find_transportation_routes(p_origin_id text, p_destination_id text, p_transportation_type text DEFAULT NULL::text) RETURNS TABLE(id integer, origin_id text, destination_id text, transportation_type text, name jsonb, description jsonb, distance_km double precision, duration_minutes integer, price_range jsonb)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.id,
        r.origin_id,
        r.destination_id,
        r.transportation_type,
        r.name,
        r.description,
        r.distance_km,
        r.duration_minutes,
        r.price_range
    FROM 
        transportation_routes r
    WHERE 
        r.origin_id = p_origin_id
        AND r.destination_id = p_destination_id
        AND (p_transportation_type IS NULL OR r.transportation_type = p_transportation_type)
    ORDER BY 
        r.duration_minutes ASC;
END;
$$;


ALTER FUNCTION public.find_transportation_routes(p_origin_id text, p_destination_id text, p_transportation_type text) OWNER TO postgres;

--
-- Name: get_accommodations_by_city(text, text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.get_accommodations_by_city(city_name text, lang text DEFAULT 'en'::text) RETURNS TABLE(id text, name jsonb, description jsonb, city text, type text, stars integer)
    LANGUAGE plpgsql STABLE
    AS $$
BEGIN
    RETURN QUERY
    SELECT
        a.id,
        a.name,
        a.description,
        a.city,
        a.type,
        a.stars
    FROM
        accommodations a
    JOIN
        cities c ON a.city_id = c.id
    WHERE
        search_jsonb_text(c.name, city_name, lang) = TRUE
        OR c.name_en ILIKE '%' || city_name || '%'
        OR c.name_ar ILIKE '%' || city_name || '%'
    ORDER BY
        a.stars DESC;
END;
$$;


ALTER FUNCTION public.get_accommodations_by_city(city_name text, lang text) OWNER TO postgres;

--
-- Name: get_attraction_by_name(text, text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.get_attraction_by_name(search_name text, lang text DEFAULT 'en'::text) RETURNS TABLE(id text, name jsonb, description jsonb, city text, region text, type text)
    LANGUAGE plpgsql STABLE
    AS $$
BEGIN
    RETURN QUERY
    SELECT
        a.id,
        a.name,
        a.description,
        a.city,
        a.region,
        a.type
    FROM
        attractions a
    WHERE
        search_jsonb_text(a.name, search_name, lang) = TRUE
    ORDER BY
        similarity(get_text_by_language(a.name, lang), search_name) DESC
    LIMIT 5;
END;
$$;


ALTER FUNCTION public.get_attraction_by_name(search_name text, lang text) OWNER TO postgres;

--
-- Name: get_available_languages(jsonb); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.get_available_languages(json_data jsonb) RETURNS text[]
    LANGUAGE plpgsql IMMUTABLE
    AS $$
BEGIN
    -- Return an array of language codes
    RETURN ARRAY(
        SELECT jsonb_object_keys(json_data)
    );
END;
$$;


ALTER FUNCTION public.get_available_languages(json_data jsonb) OWNER TO postgres;

--
-- Name: get_cache_stats(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.get_cache_stats() RETURNS TABLE(total_entries integer, hit_count bigint, avg_hits numeric, oldest_entry timestamp with time zone, newest_entry timestamp with time zone, memory_usage_kb bigint)
    LANGUAGE plpgsql
    AS $$
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
$$;


ALTER FUNCTION public.get_cache_stats() OWNER TO postgres;

--
-- Name: get_cached_query(text, jsonb, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.get_cached_query(query_text text, params jsonb, ttl_seconds integer DEFAULT 3600) RETURNS jsonb
    LANGUAGE plpgsql
    AS $$
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
$$;


ALTER FUNCTION public.get_cached_query(query_text text, params jsonb, ttl_seconds integer) OWNER TO postgres;

--
-- Name: get_cached_query(text, jsonb, text, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.get_cached_query(query_text text, params jsonb, category text DEFAULT NULL::text, ttl_seconds integer DEFAULT 3600) RETURNS jsonb
    LANGUAGE plpgsql
    AS $$
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
$$;


ALTER FUNCTION public.get_cached_query(query_text text, params jsonb, category text, ttl_seconds integer) OWNER TO postgres;

--
-- Name: get_connection_pool_recommendations(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.get_connection_pool_recommendations() RETURNS TABLE(recommendation text, current_value text, suggested_value text, priority integer)
    LANGUAGE plpgsql
    AS $$
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
$$;


ALTER FUNCTION public.get_connection_pool_recommendations() OWNER TO postgres;

--
-- Name: get_connection_pool_stats(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.get_connection_pool_stats(p_hours integer DEFAULT 24) RETURNS TABLE(hour timestamp with time zone, min_connections integer, max_connections integer, active_connections integer, total_connections integer, idle_connections integer, waiting_clients integer, avg_wait_time_ms double precision, max_wait_time_ms double precision, total_queries integer, error_count integer, query_error_rate double precision)
    LANGUAGE plpgsql
    AS $$
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
$$;


ALTER FUNCTION public.get_connection_pool_stats(p_hours integer) OWNER TO postgres;

--
-- Name: get_current_db_connections(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.get_current_db_connections() RETURNS TABLE(database_name text, total_connections bigint, active_connections bigint, idle_connections bigint, idle_in_transaction bigint, longest_transaction_seconds bigint, longest_query_seconds bigint)
    LANGUAGE plpgsql
    AS $$
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
$$;


ALTER FUNCTION public.get_current_db_connections() OWNER TO postgres;

--
-- Name: get_destination_children(text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.get_destination_children(p_parent_id text) RETURNS TABLE(id text, name jsonb, type text, level integer)
    LANGUAGE sql
    AS $$
WITH RECURSIVE destination_tree AS (
    -- Base case: immediate children
    SELECT 
        d.id,
        d.name,
        d.type,
        1 AS level
    FROM 
        destinations d
    WHERE 
        d.parent_id = p_parent_id
    
    UNION ALL
    
    -- Recursive case: children of children
    SELECT 
        d.id,
        d.name,
        d.type,
        dt.level + 1
    FROM 
        destinations d
    JOIN 
        destination_tree dt ON d.parent_id = dt.id
)
SELECT 
    id, 
    name, 
    type, 
    level
FROM 
    destination_tree
ORDER BY 
    level, type, name->>'en';
$$;


ALTER FUNCTION public.get_destination_children(p_parent_id text) OWNER TO postgres;

--
-- Name: get_destination_hierarchy(text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.get_destination_hierarchy(p_destination_id text) RETURNS TABLE(id text, name jsonb, type text, level integer)
    LANGUAGE sql
    AS $$
WITH RECURSIVE destination_tree AS (
    -- Base case: the destination itself
    SELECT 
        d.id,
        d.name,
        d.type,
        0 AS level
    FROM 
        destinations d
    WHERE 
        d.id = p_destination_id
    
    UNION ALL
    
    -- Recursive case: parent destinations
    SELECT 
        d.id,
        d.name,
        d.type,
        dt.level + 1
    FROM 
        destinations d
    JOIN 
        destination_tree dt ON d.id = dt.id
    JOIN 
        destinations parent ON dt.id = parent.parent_id
)
SELECT 
    id, 
    name, 
    type, 
    level
FROM 
    destination_tree
ORDER BY 
    level DESC;
$$;


ALTER FUNCTION public.get_destination_hierarchy(p_destination_id text) OWNER TO postgres;

--
-- Name: get_events_festivals_by_category(text, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.get_events_festivals_by_category(p_category_id text, p_limit integer DEFAULT 20) RETURNS TABLE(id integer, name jsonb, description jsonb, start_date date, end_date date, is_annual boolean, destination_id text, venue jsonb, is_featured boolean)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.id,
        e.name,
        e.description,
        e.start_date,
        e.end_date,
        e.is_annual,
        e.destination_id,
        e.venue,
        e.is_featured
    FROM 
        events_festivals e
    WHERE 
        e.category_id = p_category_id
    ORDER BY 
        e.is_featured DESC,
        CASE WHEN e.start_date IS NOT NULL AND e.start_date >= CURRENT_DATE THEN 0 ELSE 1 END,
        e.start_date,
        e.view_count DESC
    LIMIT p_limit;
END;
$$;


ALTER FUNCTION public.get_events_festivals_by_category(p_category_id text, p_limit integer) OWNER TO postgres;

--
-- Name: get_events_festivals_by_destination(text, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.get_events_festivals_by_destination(p_destination_id text, p_limit integer DEFAULT 20) RETURNS TABLE(id integer, category_id text, category_name jsonb, name jsonb, description jsonb, start_date date, end_date date, is_annual boolean, venue jsonb, is_featured boolean)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.id,
        e.category_id,
        c.name AS category_name,
        e.name,
        e.description,
        e.start_date,
        e.end_date,
        e.is_annual,
        e.venue,
        e.is_featured
    FROM 
        events_festivals e
    JOIN
        event_categories c ON e.category_id = c.id
    WHERE 
        e.destination_id = p_destination_id
    ORDER BY 
        e.is_featured DESC,
        CASE WHEN e.start_date IS NOT NULL AND e.start_date >= CURRENT_DATE THEN 0 ELSE 1 END,
        e.start_date,
        e.view_count DESC
    LIMIT p_limit;
END;
$$;


ALTER FUNCTION public.get_events_festivals_by_destination(p_destination_id text, p_limit integer) OWNER TO postgres;

--
-- Name: get_faqs_by_category(text, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.get_faqs_by_category(p_category_id text, p_limit integer DEFAULT 20) RETURNS TABLE(id integer, question jsonb, answer jsonb, tags text[], is_featured boolean)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        f.id,
        f.question,
        f.answer,
        f.tags,
        f.is_featured
    FROM 
        tourism_faqs f
    WHERE 
        f.category_id = p_category_id
    ORDER BY 
        f.is_featured DESC,
        f.helpful_count DESC,
        f.view_count DESC
    LIMIT p_limit;
END;
$$;


ALTER FUNCTION public.get_faqs_by_category(p_category_id text, p_limit integer) OWNER TO postgres;

--
-- Name: get_faqs_by_destination(text, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.get_faqs_by_destination(p_destination_id text, p_limit integer DEFAULT 20) RETURNS TABLE(id integer, category_id text, category_name jsonb, question jsonb, answer jsonb, is_featured boolean)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        f.id,
        f.category_id,
        c.name AS category_name,
        f.question,
        f.answer,
        f.is_featured
    FROM 
        tourism_faqs f
    JOIN
        faq_categories c ON f.category_id = c.id
    WHERE 
        p_destination_id = ANY(f.related_destination_ids)
    ORDER BY 
        f.is_featured DESC,
        f.helpful_count DESC,
        f.view_count DESC
    LIMIT p_limit;
END;
$$;


ALTER FUNCTION public.get_faqs_by_destination(p_destination_id text, p_limit integer) OWNER TO postgres;

--
-- Name: get_featured_events_festivals(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.get_featured_events_festivals(p_limit integer DEFAULT 10) RETURNS TABLE(id integer, category_id text, category_name jsonb, name jsonb, description jsonb, start_date date, end_date date, destination_id text, venue jsonb, is_annual boolean)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.id,
        e.category_id,
        c.name AS category_name,
        e.name,
        e.description,
        e.start_date,
        e.end_date,
        e.destination_id,
        e.venue,
        e.is_annual
    FROM 
        events_festivals e
    JOIN
        event_categories c ON e.category_id = c.id
    WHERE 
        e.is_featured = TRUE
    ORDER BY 
        CASE WHEN e.start_date IS NOT NULL AND e.start_date >= CURRENT_DATE THEN 0 ELSE 1 END,
        e.start_date,
        e.view_count DESC
    LIMIT p_limit;
END;
$$;


ALTER FUNCTION public.get_featured_events_festivals(p_limit integer) OWNER TO postgres;

--
-- Name: get_featured_faqs(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.get_featured_faqs(p_limit integer DEFAULT 10) RETURNS TABLE(id integer, category_id text, category_name jsonb, question jsonb, answer jsonb, tags text[])
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        f.id,
        f.category_id,
        c.name AS category_name,
        f.question,
        f.answer,
        f.tags
    FROM 
        tourism_faqs f
    JOIN
        faq_categories c ON f.category_id = c.id
    WHERE 
        f.is_featured = TRUE
    ORDER BY 
        f.helpful_count DESC,
        f.view_count DESC
    LIMIT p_limit;
END;
$$;


ALTER FUNCTION public.get_featured_faqs(p_limit integer) OWNER TO postgres;

--
-- Name: get_featured_itineraries(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.get_featured_itineraries(p_limit integer DEFAULT 10) RETURNS TABLE(id integer, type_id text, type_name jsonb, name jsonb, description jsonb, duration_days integer, regions text[], cities text[], attractions text[], budget_range jsonb, difficulty_level text)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT
        i.id,
        i.type_id,
        t.name AS type_name,
        i.name,
        i.description,
        i.duration_days,
        i.regions,
        i.cities,
        i.attractions,
        i.budget_range,
        i.difficulty_level
    FROM
        itineraries i
    JOIN
        itinerary_types t ON i.type_id = t.id
    WHERE
        i.is_featured = TRUE
    ORDER BY
        i.rating DESC NULLS LAST,
        i.view_count DESC
    LIMIT p_limit;
END;
$$;


ALTER FUNCTION public.get_featured_itineraries(p_limit integer) OWNER TO postgres;

--
-- Name: get_featured_practical_info(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.get_featured_practical_info(p_limit integer DEFAULT 10) RETURNS TABLE(id integer, category_id text, category_name jsonb, title jsonb, content jsonb, tags text[])
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.category_id,
        c.name AS category_name,
        p.title,
        p.content,
        p.tags
    FROM 
        practical_info p
    JOIN
        practical_info_categories c ON p.category_id = c.id
    WHERE 
        p.is_featured = TRUE
    ORDER BY 
        p.helpful_count DESC,
        p.view_count DESC
    LIMIT p_limit;
END;
$$;


ALTER FUNCTION public.get_featured_practical_info(p_limit integer) OWNER TO postgres;

--
-- Name: get_featured_tour_packages(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.get_featured_tour_packages(p_limit integer DEFAULT 10) RETURNS TABLE(id integer, category_id text, category_name jsonb, name jsonb, description jsonb, duration_days integer, price_range jsonb, destinations text[], rating numeric)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.category_id,
        c.name AS category_name,
        p.name,
        p.description,
        p.duration_days,
        p.price_range,
        p.destinations,
        p.rating
    FROM 
        tour_packages p
    JOIN
        tour_package_categories c ON p.category_id = c.id
    WHERE 
        p.is_featured = TRUE
    ORDER BY 
        p.rating DESC,
        p.booking_count DESC
    LIMIT p_limit;
END;
$$;


ALTER FUNCTION public.get_featured_tour_packages(p_limit integer) OWNER TO postgres;

--
-- Name: get_itineraries_by_region(text, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.get_itineraries_by_region(p_region text, p_limit integer DEFAULT 10) RETURNS TABLE(id integer, type_id text, type_name jsonb, name jsonb, description jsonb, duration_days integer, cities text[], attractions text[], budget_range jsonb, difficulty_level text, is_featured boolean)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT
        i.id,
        i.type_id,
        t.name AS type_name,
        i.name,
        i.description,
        i.duration_days,
        i.cities,
        i.attractions,
        i.budget_range,
        i.difficulty_level,
        i.is_featured
    FROM
        itineraries i
    JOIN
        itinerary_types t ON i.type_id = t.id
    WHERE
        p_region = ANY(i.regions)
    ORDER BY
        i.is_featured DESC,
        i.rating DESC NULLS LAST,
        i.view_count DESC
    LIMIT p_limit;
END;
$$;


ALTER FUNCTION public.get_itineraries_by_region(p_region text, p_limit integer) OWNER TO postgres;

--
-- Name: get_itineraries_by_type(text, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.get_itineraries_by_type(p_type_id text, p_limit integer DEFAULT 10) RETURNS TABLE(id integer, name jsonb, description jsonb, duration_days integer, regions text[], cities text[], attractions text[], budget_range jsonb, difficulty_level text, is_featured boolean)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT
        i.id,
        i.name,
        i.description,
        i.duration_days,
        i.regions,
        i.cities,
        i.attractions,
        i.budget_range,
        i.difficulty_level,
        i.is_featured
    FROM
        itineraries i
    WHERE
        i.type_id = p_type_id
    ORDER BY
        i.is_featured DESC,
        i.rating DESC NULLS LAST,
        i.view_count DESC
    LIMIT p_limit;
END;
$$;


ALTER FUNCTION public.get_itineraries_by_type(p_type_id text, p_limit integer) OWNER TO postgres;

--
-- Name: get_latitude(public.geometry); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.get_latitude(geom public.geometry) RETURNS double precision
    LANGUAGE plpgsql IMMUTABLE
    AS $$
BEGIN
    RETURN ST_Y(geom);
END;
$$;


ALTER FUNCTION public.get_latitude(geom public.geometry) OWNER TO postgres;

--
-- Name: get_longitude(public.geometry); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.get_longitude(geom public.geometry) RETURNS double precision
    LANGUAGE plpgsql IMMUTABLE
    AS $$
BEGIN
    RETURN ST_X(geom);
END;
$$;


ALTER FUNCTION public.get_longitude(geom public.geometry) OWNER TO postgres;

--
-- Name: get_practical_info_by_category(text, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.get_practical_info_by_category(p_category_id text, p_limit integer DEFAULT 20) RETURNS TABLE(id integer, title jsonb, content jsonb, tags text[], is_featured boolean)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.title,
        p.content,
        p.tags,
        p.is_featured
    FROM 
        practical_info p
    WHERE 
        p.category_id = p_category_id
    ORDER BY 
        p.is_featured DESC,
        p.helpful_count DESC,
        p.view_count DESC
    LIMIT p_limit;
END;
$$;


ALTER FUNCTION public.get_practical_info_by_category(p_category_id text, p_limit integer) OWNER TO postgres;

--
-- Name: get_practical_info_by_destination(text, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.get_practical_info_by_destination(p_destination_id text, p_limit integer DEFAULT 20) RETURNS TABLE(id integer, category_id text, category_name jsonb, title jsonb, content jsonb, is_featured boolean)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.category_id,
        c.name AS category_name,
        p.title,
        p.content,
        p.is_featured
    FROM 
        practical_info p
    JOIN
        practical_info_categories c ON p.category_id = c.id
    WHERE 
        p_destination_id = ANY(p.related_destination_ids)
    ORDER BY 
        p.is_featured DESC,
        p.helpful_count DESC,
        p.view_count DESC
    LIMIT p_limit;
END;
$$;


ALTER FUNCTION public.get_practical_info_by_destination(p_destination_id text, p_limit integer) OWNER TO postgres;

--
-- Name: get_text_by_language(jsonb, text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.get_text_by_language(json_data jsonb, lang text DEFAULT 'en'::text) RETURNS text
    LANGUAGE plpgsql IMMUTABLE
    AS $$
BEGIN
    -- Return the text for the specified language, or English if not found
    RETURN COALESCE(
        json_data->>lang,
        json_data->>'en',
        json_data->>'ar',
        json_data::TEXT
    );
END;
$$;


ALTER FUNCTION public.get_text_by_language(json_data jsonb, lang text) OWNER TO postgres;

--
-- Name: get_tour_packages_by_category(text, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.get_tour_packages_by_category(p_category_id text, p_limit integer DEFAULT 20) RETURNS TABLE(id integer, name jsonb, description jsonb, duration_days integer, price_range jsonb, destinations text[], rating numeric, is_featured boolean)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.name,
        p.description,
        p.duration_days,
        p.price_range,
        p.destinations,
        p.rating,
        p.is_featured
    FROM 
        tour_packages p
    WHERE 
        p.category_id = p_category_id
    ORDER BY 
        p.is_featured DESC,
        p.rating DESC,
        p.booking_count DESC
    LIMIT p_limit;
END;
$$;


ALTER FUNCTION public.get_tour_packages_by_category(p_category_id text, p_limit integer) OWNER TO postgres;

--
-- Name: get_tour_packages_by_destination(text, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.get_tour_packages_by_destination(p_destination text, p_limit integer DEFAULT 20) RETURNS TABLE(id integer, category_id text, category_name jsonb, name jsonb, description jsonb, duration_days integer, price_range jsonb, rating numeric, is_featured boolean)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.category_id,
        c.name AS category_name,
        p.name,
        p.description,
        p.duration_days,
        p.price_range,
        p.rating,
        p.is_featured
    FROM 
        tour_packages p
    JOIN
        tour_package_categories c ON p.category_id = c.id
    WHERE 
        p_destination = ANY(p.destinations)
    ORDER BY 
        p.is_featured DESC,
        p.rating DESC,
        p.booking_count DESC
    LIMIT p_limit;
END;
$$;


ALTER FUNCTION public.get_tour_packages_by_destination(p_destination text, p_limit integer) OWNER TO postgres;

--
-- Name: get_upcoming_events_festivals(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.get_upcoming_events_festivals(p_limit integer DEFAULT 10) RETURNS TABLE(id integer, category_id text, category_name jsonb, name jsonb, description jsonb, start_date date, end_date date, destination_id text, venue jsonb, is_featured boolean)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.id,
        e.category_id,
        c.name AS category_name,
        e.name,
        e.description,
        e.start_date,
        e.end_date,
        e.destination_id,
        e.venue,
        e.is_featured
    FROM 
        events_festivals e
    JOIN
        event_categories c ON e.category_id = c.id
    WHERE 
        e.start_date >= CURRENT_DATE
    ORDER BY 
        e.start_date,
        e.is_featured DESC
    LIMIT p_limit;
END;
$$;


ALTER FUNCTION public.get_upcoming_events_festivals(p_limit integer) OWNER TO postgres;

--
-- Name: identify_unused_indexes(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.identify_unused_indexes() RETURNS TABLE(index_name text, table_name text, index_size text, index_scans integer, recommendation text)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT
        i.indexrelname::TEXT AS index_name,
        t.relname::TEXT AS table_name,
        pg_size_pretty(pg_relation_size(i.indexrelid))::TEXT AS index_size,
        s.idx_scan::INTEGER AS index_scans,
        CASE
            WHEN s.idx_scan < 10 AND pg_relation_size(i.indexrelid) > 1024 * 1024 THEN 'Consider dropping'
            WHEN s.idx_scan < 100 AND pg_relation_size(i.indexrelid) > 5 * 1024 * 1024 THEN 'Monitor usage'
            ELSE 'Keep'
        END AS recommendation
    FROM pg_stat_user_indexes s
    JOIN pg_index i ON s.indexrelid = i.indexrelid
    JOIN pg_class t ON i.indrelid = t.oid
    WHERE s.schemaname = 'public'
    AND NOT i.indisprimary
    AND NOT i.indisunique
    ORDER BY s.idx_scan ASC, pg_relation_size(i.indexrelid) DESC;
END;
$$;


ALTER FUNCTION public.identify_unused_indexes() OWNER TO postgres;

--
-- Name: invalidate_cache_by_category(text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.invalidate_cache_by_category(p_category text) RETURNS integer
    LANGUAGE plpgsql
    AS $$
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
$$;


ALTER FUNCTION public.invalidate_cache_by_category(p_category text) OWNER TO postgres;

--
-- Name: invalidate_cache_on_table_change(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.invalidate_cache_on_table_change() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    PERFORM invalidate_table_cache(TG_TABLE_NAME);
    RAISE NOTICE 'Invalidated cache for table: %', TG_TABLE_NAME;
    RETURN NULL;
END;
$$;


ALTER FUNCTION public.invalidate_cache_on_table_change() OWNER TO postgres;

--
-- Name: invalidate_table_cache(text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.invalidate_table_cache(p_table_name text) RETURNS integer
    LANGUAGE plpgsql
    AS $$
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
$$;


ALTER FUNCTION public.invalidate_table_cache(p_table_name text) OWNER TO postgres;

--
-- Name: merge_language_jsonb(jsonb, jsonb); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.merge_language_jsonb(json_data1 jsonb, json_data2 jsonb) RETURNS jsonb
    LANGUAGE plpgsql IMMUTABLE
    AS $$
BEGIN
    -- Merge two JSONB objects, with json_data2 taking precedence
    RETURN json_data1 || json_data2;
END;
$$;


ALTER FUNCTION public.merge_language_jsonb(json_data1 jsonb, json_data2 jsonb) OWNER TO postgres;

--
-- Name: record_connection_pool_stats(integer, integer, integer, integer, double precision, integer, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.record_connection_pool_stats(p_min_connections integer, p_max_connections integer, p_current_connections integer, p_available_connections integer, p_acquisition_time_ms double precision, p_query_count integer, p_error_count integer) RETURNS void
    LANGUAGE plpgsql
    AS $$
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
$$;


ALTER FUNCTION public.record_connection_pool_stats(p_min_connections integer, p_max_connections integer, p_current_connections integer, p_available_connections integer, p_acquisition_time_ms double precision, p_query_count integer, p_error_count integer) OWNER TO postgres;

--
-- Name: record_connection_pool_stats(integer, integer, integer, integer, integer, integer, double precision, double precision, integer, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.record_connection_pool_stats(p_min_connections integer, p_max_connections integer, p_active_connections integer, p_total_connections integer, p_idle_connections integer, p_waiting_clients integer, p_avg_wait_time_ms double precision, p_max_wait_time_ms double precision, p_total_queries integer, p_error_count integer) RETURNS void
    LANGUAGE plpgsql
    AS $$
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
$$;


ALTER FUNCTION public.record_connection_pool_stats(p_min_connections integer, p_max_connections integer, p_active_connections integer, p_total_connections integer, p_idle_connections integer, p_waiting_clients integer, p_avg_wait_time_ms double precision, p_max_wait_time_ms double precision, p_total_queries integer, p_error_count integer) OWNER TO postgres;

--
-- Name: search_attractions_by_keywords(text, text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.search_attractions_by_keywords(keywords text, lang text DEFAULT 'en'::text) RETURNS TABLE(id text, name jsonb, description jsonb, city text, region text, type text, relevance double precision)
    LANGUAGE plpgsql STABLE
    AS $$
BEGIN
    RETURN QUERY
    SELECT
        a.id,
        a.name,
        a.description,
        a.city,
        a.region,
        a.type,
        ts_rank_cd(
            to_tsvector(get_text_by_language(a.description, lang)),
            to_tsquery(regexp_replace(keywords, '\s+', ' & ', 'g'))
        ) AS relevance
    FROM
        attractions a
    WHERE
        to_tsvector(get_text_by_language(a.description, lang)) @@
        to_tsquery(regexp_replace(keywords, '\s+', ' & ', 'g'))
    ORDER BY
        relevance DESC;
END;
$$;


ALTER FUNCTION public.search_attractions_by_keywords(keywords text, lang text) OWNER TO postgres;

--
-- Name: search_events_festivals(text, text, text, date, date, boolean, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.search_events_festivals(p_query text, p_category_id text DEFAULT NULL::text, p_destination_id text DEFAULT NULL::text, p_start_date date DEFAULT NULL::date, p_end_date date DEFAULT NULL::date, p_is_annual boolean DEFAULT NULL::boolean, p_limit integer DEFAULT 10) RETURNS TABLE(id integer, category_id text, category_name jsonb, name jsonb, description jsonb, start_date date, end_date date, is_annual boolean, destination_id text, venue jsonb, tags text[], is_featured boolean)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.id,
        e.category_id,
        c.name AS category_name,
        e.name,
        e.description,
        e.start_date,
        e.end_date,
        e.is_annual,
        e.destination_id,
        e.venue,
        e.tags,
        e.is_featured
    FROM 
        events_festivals e
    JOIN
        event_categories c ON e.category_id = c.id
    WHERE 
        (p_category_id IS NULL OR e.category_id = p_category_id)
        AND (p_destination_id IS NULL OR e.destination_id = p_destination_id)
        AND (p_start_date IS NULL OR e.start_date >= p_start_date OR e.is_annual = TRUE)
        AND (p_end_date IS NULL OR e.end_date <= p_end_date OR e.is_annual = TRUE)
        AND (p_is_annual IS NULL OR e.is_annual = p_is_annual)
        AND (
            p_query IS NULL
            OR to_tsvector('english', e.name->>'en') @@ plainto_tsquery('english', p_query)
            OR to_tsvector('english', e.description->>'en') @@ plainto_tsquery('english', p_query)
            OR p_query = ANY(e.tags)
        )
    ORDER BY 
        e.is_featured DESC,
        CASE WHEN e.start_date IS NOT NULL AND e.start_date >= CURRENT_DATE THEN 0 ELSE 1 END,
        e.start_date,
        e.view_count DESC
    LIMIT p_limit;
END;
$$;


ALTER FUNCTION public.search_events_festivals(p_query text, p_category_id text, p_destination_id text, p_start_date date, p_end_date date, p_is_annual boolean, p_limit integer) OWNER TO postgres;

--
-- Name: search_faqs(text, text, text, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.search_faqs(p_query text, p_category_id text DEFAULT NULL::text, p_destination_id text DEFAULT NULL::text, p_limit integer DEFAULT 10) RETURNS TABLE(id integer, category_id text, category_name jsonb, question jsonb, answer jsonb, tags text[], is_featured boolean)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        f.id,
        f.category_id,
        c.name AS category_name,
        f.question,
        f.answer,
        f.tags,
        f.is_featured
    FROM 
        tourism_faqs f
    JOIN
        faq_categories c ON f.category_id = c.id
    WHERE 
        (p_category_id IS NULL OR f.category_id = p_category_id)
        AND (p_destination_id IS NULL OR p_destination_id = ANY(f.related_destination_ids))
        AND (
            to_tsvector('english', f.question->>'en') @@ plainto_tsquery('english', p_query)
            OR to_tsvector('english', f.answer->>'en') @@ plainto_tsquery('english', p_query)
            OR p_query = ANY(f.tags)
        )
    ORDER BY 
        f.is_featured DESC,
        ts_rank(to_tsvector('english', f.question->>'en'), plainto_tsquery('english', p_query)) +
        ts_rank(to_tsvector('english', f.answer->>'en'), plainto_tsquery('english', p_query)) DESC,
        f.helpful_count DESC
    LIMIT p_limit;
END;
$$;


ALTER FUNCTION public.search_faqs(p_query text, p_category_id text, p_destination_id text, p_limit integer) OWNER TO postgres;

--
-- Name: search_itineraries(text, text, integer, integer, text, text, text, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.search_itineraries(p_query text, p_type_id text DEFAULT NULL::text, p_duration_min integer DEFAULT NULL::integer, p_duration_max integer DEFAULT NULL::integer, p_region text DEFAULT NULL::text, p_city text DEFAULT NULL::text, p_attraction text DEFAULT NULL::text, p_limit integer DEFAULT 10) RETURNS TABLE(id integer, type_id text, type_name jsonb, name jsonb, description jsonb, duration_days integer, regions text[], cities text[], attractions text[], budget_range jsonb, difficulty_level text, is_featured boolean)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT
        i.id,
        i.type_id,
        t.name AS type_name,
        i.name,
        i.description,
        i.duration_days,
        i.regions,
        i.cities,
        i.attractions,
        i.budget_range,
        i.difficulty_level,
        i.is_featured
    FROM
        itineraries i
    JOIN
        itinerary_types t ON i.type_id = t.id
    WHERE
        (p_type_id IS NULL OR i.type_id = p_type_id)
        AND (p_duration_min IS NULL OR i.duration_days >= p_duration_min)
        AND (p_duration_max IS NULL OR i.duration_days <= p_duration_max)
        AND (p_region IS NULL OR p_region = ANY(i.regions))
        AND (p_city IS NULL OR p_city = ANY(i.cities))
        AND (p_attraction IS NULL OR p_attraction = ANY(i.attractions))
        AND (
            p_query IS NULL
            OR to_tsvector('english', i.name->>'en') @@ plainto_tsquery('english', p_query)
            OR to_tsvector('english', i.description->>'en') @@ plainto_tsquery('english', p_query)
            OR p_query = ANY(i.tags)
        )
    ORDER BY
        i.is_featured DESC,
        i.rating DESC NULLS LAST,
        i.view_count DESC
    LIMIT p_limit;
END;
$$;


ALTER FUNCTION public.search_itineraries(p_query text, p_type_id text, p_duration_min integer, p_duration_max integer, p_region text, p_city text, p_attraction text, p_limit integer) OWNER TO postgres;

--
-- Name: search_jsonb_text(jsonb, text, text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.search_jsonb_text(json_data jsonb, search_text text, lang text DEFAULT 'en'::text) RETURNS boolean
    LANGUAGE plpgsql IMMUTABLE
    AS $$
BEGIN
    -- Check if the text for the specified language contains the search text
    RETURN (
        (json_data->>lang) ILIKE '%' || search_text || '%'
        OR
        (json_data->>'en') ILIKE '%' || search_text || '%'
    );
END;
$$;


ALTER FUNCTION public.search_jsonb_text(json_data jsonb, search_text text, lang text) OWNER TO postgres;

--
-- Name: search_practical_info(text, text, text, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.search_practical_info(p_query text, p_category_id text DEFAULT NULL::text, p_destination_id text DEFAULT NULL::text, p_limit integer DEFAULT 10) RETURNS TABLE(id integer, category_id text, category_name jsonb, title jsonb, content jsonb, tags text[], is_featured boolean)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.category_id,
        c.name AS category_name,
        p.title,
        p.content,
        p.tags,
        p.is_featured
    FROM 
        practical_info p
    JOIN
        practical_info_categories c ON p.category_id = c.id
    WHERE 
        (p_category_id IS NULL OR p.category_id = p_category_id)
        AND (p_destination_id IS NULL OR p_destination_id = ANY(p.related_destination_ids))
        AND (
            to_tsvector('english', p.title->>'en') @@ plainto_tsquery('english', p_query)
            OR to_tsvector('english', p.content->>'en') @@ plainto_tsquery('english', p_query)
            OR p_query = ANY(p.tags)
        )
    ORDER BY 
        p.is_featured DESC,
        ts_rank(to_tsvector('english', p.title->>'en'), plainto_tsquery('english', p_query)) +
        ts_rank(to_tsvector('english', p.content->>'en'), plainto_tsquery('english', p_query)) DESC,
        p.helpful_count DESC
    LIMIT p_limit;
END;
$$;


ALTER FUNCTION public.search_practical_info(p_query text, p_category_id text, p_destination_id text, p_limit integer) OWNER TO postgres;

--
-- Name: search_tour_packages(text, text, text, integer, integer, numeric, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.search_tour_packages(p_query text, p_category_id text DEFAULT NULL::text, p_destination text DEFAULT NULL::text, p_min_duration integer DEFAULT NULL::integer, p_max_duration integer DEFAULT NULL::integer, p_min_rating numeric DEFAULT NULL::numeric, p_limit integer DEFAULT 10) RETURNS TABLE(id integer, category_id text, category_name jsonb, name jsonb, description jsonb, duration_days integer, price_range jsonb, destinations text[], rating numeric, is_featured boolean)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.category_id,
        c.name AS category_name,
        p.name,
        p.description,
        p.duration_days,
        p.price_range,
        p.destinations,
        p.rating,
        p.is_featured
    FROM 
        tour_packages p
    JOIN
        tour_package_categories c ON p.category_id = c.id
    WHERE 
        (p_category_id IS NULL OR p.category_id = p_category_id)
        AND (p_destination IS NULL OR p_destination = ANY(p.destinations))
        AND (p_min_duration IS NULL OR p.duration_days >= p_min_duration)
        AND (p_max_duration IS NULL OR p.duration_days <= p_max_duration)
        AND (p_min_rating IS NULL OR p.rating >= p_min_rating)
        AND (
            p_query IS NULL
            OR to_tsvector('english', p.name->>'en') @@ plainto_tsquery('english', p_query)
            OR to_tsvector('english', p.description->>'en') @@ plainto_tsquery('english', p_query)
            OR p_query = ANY(p.tags)
        )
    ORDER BY 
        p.is_featured DESC,
        p.rating DESC,
        p.booking_count DESC
    LIMIT p_limit;
END;
$$;


ALTER FUNCTION public.search_tour_packages(p_query text, p_category_id text, p_destination text, p_min_duration integer, p_max_duration integer, p_min_rating numeric, p_limit integer) OWNER TO postgres;

--
-- Name: set_cache_category(text, text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.set_cache_category(p_cache_key text, p_category text) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
DECLARE
    updated_rows INTEGER;
BEGIN
    UPDATE query_cache
    SET category = p_category
    WHERE cache_key = p_cache_key
    RETURNING 1 INTO updated_rows;
    
    RETURN updated_rows IS NOT NULL;
END;
$$;


ALTER FUNCTION public.set_cache_category(p_cache_key text, p_category text) OWNER TO postgres;

--
-- Name: update_timestamp(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.update_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_timestamp() OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: accommodation_types; Type: TABLE; Schema: public; Owner: omarmohamed
--

CREATE TABLE public.accommodation_types (
    type text NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.accommodation_types OWNER TO omarmohamed;

--
-- Name: COLUMN accommodation_types.updated_at; Type: COMMENT; Schema: public; Owner: omarmohamed
--

COMMENT ON COLUMN public.accommodation_types.updated_at IS 'Timestamp when the record was last updated';


--
-- Name: COLUMN accommodation_types.created_at; Type: COMMENT; Schema: public; Owner: omarmohamed
--

COMMENT ON COLUMN public.accommodation_types.created_at IS 'Timestamp when the record was created';


--
-- Name: accommodations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.accommodations (
    stars integer,
    data jsonb DEFAULT '{}'::jsonb,
    embedding public.vector(1536),
    geom public.geometry(Point,4326),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    user_id text,
    name jsonb,
    description jsonb,
    price_min integer,
    price_max integer,
    type_id text,
    embedding_backup text,
    name_backup jsonb,
    description_backup jsonb,
    region_id integer,
    city_id integer,
    id integer NOT NULL,
    CONSTRAINT valid_accommodation_embedding CHECK (((embedding IS NULL) OR ((embedding)::text <> '[]'::text)))
);


ALTER TABLE public.accommodations OWNER TO postgres;

--
-- Name: COLUMN accommodations.embedding; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.accommodations.embedding IS 'Vector embedding for semantic search. Use vector operators (<->, <=>) for similarity search.';


--
-- Name: COLUMN accommodations.geom; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.accommodations.geom IS 'PostGIS geometry column. Use ST_X(geom) for longitude and ST_Y(geom) for latitude.';


--
-- Name: COLUMN accommodations.created_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.accommodations.created_at IS 'Timestamp when the record was created';


--
-- Name: COLUMN accommodations.updated_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.accommodations.updated_at IS 'Timestamp when the record was last updated';


--
-- Name: accommodations_integer_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.accommodations_integer_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.accommodations_integer_id_seq OWNER TO postgres;

--
-- Name: accommodations_integer_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.accommodations_integer_id_seq OWNED BY public.accommodations.id;


--
-- Name: analytics; Type: TABLE; Schema: public; Owner: user1
--

CREATE TABLE public.analytics (
    id integer NOT NULL,
    event_type text NOT NULL,
    event_data jsonb,
    session_id text,
    user_id text,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.analytics OWNER TO user1;

--
-- Name: COLUMN analytics.created_at; Type: COMMENT; Schema: public; Owner: user1
--

COMMENT ON COLUMN public.analytics.created_at IS 'Timestamp when the record was created';


--
-- Name: COLUMN analytics.updated_at; Type: COMMENT; Schema: public; Owner: user1
--

COMMENT ON COLUMN public.analytics.updated_at IS 'Timestamp when the record was last updated';


--
-- Name: analytics_events; Type: TABLE; Schema: public; Owner: omarmohamed
--

CREATE TABLE public.analytics_events (
    event_type text,
    event_data text,
    session_id text,
    user_id text,
    created_at timestamp with time zone,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    id integer NOT NULL
);


ALTER TABLE public.analytics_events OWNER TO omarmohamed;

--
-- Name: COLUMN analytics_events.created_at; Type: COMMENT; Schema: public; Owner: omarmohamed
--

COMMENT ON COLUMN public.analytics_events.created_at IS 'Timestamp when the record was created';


--
-- Name: COLUMN analytics_events.updated_at; Type: COMMENT; Schema: public; Owner: omarmohamed
--

COMMENT ON COLUMN public.analytics_events.updated_at IS 'Timestamp when the record was last updated';


--
-- Name: analytics_events_integer_id_seq; Type: SEQUENCE; Schema: public; Owner: omarmohamed
--

CREATE SEQUENCE public.analytics_events_integer_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.analytics_events_integer_id_seq OWNER TO omarmohamed;

--
-- Name: analytics_events_integer_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: omarmohamed
--

ALTER SEQUENCE public.analytics_events_integer_id_seq OWNED BY public.analytics_events.id;


--
-- Name: analytics_id_seq; Type: SEQUENCE; Schema: public; Owner: user1
--

CREATE SEQUENCE public.analytics_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.analytics_id_seq OWNER TO user1;

--
-- Name: analytics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user1
--

ALTER SEQUENCE public.analytics_id_seq OWNED BY public.analytics.id;


--
-- Name: attraction_relationships; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.attraction_relationships (
    id integer NOT NULL,
    attraction_id integer NOT NULL,
    related_attraction_id integer NOT NULL,
    relationship_type character varying(50) DEFAULT 'related'::character varying,
    description jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.attraction_relationships OWNER TO postgres;

--
-- Name: attraction_relationships_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.attraction_relationships_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.attraction_relationships_id_seq OWNER TO postgres;

--
-- Name: attraction_relationships_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.attraction_relationships_id_seq OWNED BY public.attraction_relationships.id;


--
-- Name: attraction_subcategories; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.attraction_subcategories (
    id text NOT NULL,
    parent_type text NOT NULL,
    name jsonb NOT NULL,
    description jsonb,
    icon text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.attraction_subcategories OWNER TO postgres;

--
-- Name: COLUMN attraction_subcategories.created_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.attraction_subcategories.created_at IS 'Timestamp when the record was created';


--
-- Name: COLUMN attraction_subcategories.updated_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.attraction_subcategories.updated_at IS 'Timestamp when the record was last updated';


--
-- Name: attraction_types; Type: TABLE; Schema: public; Owner: omarmohamed
--

CREATE TABLE public.attraction_types (
    type text NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.attraction_types OWNER TO omarmohamed;

--
-- Name: COLUMN attraction_types.updated_at; Type: COMMENT; Schema: public; Owner: omarmohamed
--

COMMENT ON COLUMN public.attraction_types.updated_at IS 'Timestamp when the record was last updated';


--
-- Name: COLUMN attraction_types.created_at; Type: COMMENT; Schema: public; Owner: omarmohamed
--

COMMENT ON COLUMN public.attraction_types.created_at IS 'Timestamp when the record was created';


--
-- Name: attractions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.attractions (
    type text,
    data jsonb DEFAULT '{}'::jsonb,
    embedding public.vector(1536),
    geom public.geometry(Point,4326),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    user_id text,
    name jsonb,
    description jsonb,
    type_id text,
    subcategory_id text,
    visiting_info jsonb DEFAULT '{}'::jsonb,
    accessibility_info jsonb DEFAULT '{}'::jsonb,
    related_attractions text[] DEFAULT '{}'::text[],
    historical_context jsonb DEFAULT '{}'::jsonb,
    embedding_backup text,
    name_backup jsonb,
    description_backup jsonb,
    region_id integer,
    city_id integer,
    id integer NOT NULL,
    opening_hours character varying(255),
    entrance_fee numeric,
    popularity integer,
    CONSTRAINT valid_attraction_embedding CHECK (((embedding IS NULL) OR ((embedding)::text <> '[]'::text)))
);


ALTER TABLE public.attractions OWNER TO postgres;

--
-- Name: COLUMN attractions.data; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.attractions.data IS 'Additional attraction data in JSONB format. Expected structure: 
{
  "popularity": integer (1-10),
  "year_built": integer,
  "entrance_fee": numeric,
  "opening_hours": string
}';


--
-- Name: COLUMN attractions.embedding; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.attractions.embedding IS 'Vector embedding for semantic search. Use vector operators (<->, <=>) for similarity search.';


--
-- Name: COLUMN attractions.geom; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.attractions.geom IS 'PostGIS geometry column. Use ST_X(geom) for longitude and ST_Y(geom) for latitude.';


--
-- Name: COLUMN attractions.created_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.attractions.created_at IS 'Timestamp when the record was created';


--
-- Name: COLUMN attractions.updated_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.attractions.updated_at IS 'Timestamp when the record was last updated';


--
-- Name: attractions_integer_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.attractions_integer_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.attractions_integer_id_seq OWNER TO postgres;

--
-- Name: attractions_integer_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.attractions_integer_id_seq OWNED BY public.attractions.id;


--
-- Name: chat_logs; Type: TABLE; Schema: public; Owner: omarmohamed
--

CREATE TABLE public.chat_logs (
    user_id text,
    message text,
    intent text,
    response text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    id integer NOT NULL
);


ALTER TABLE public.chat_logs OWNER TO omarmohamed;

--
-- Name: COLUMN chat_logs.created_at; Type: COMMENT; Schema: public; Owner: omarmohamed
--

COMMENT ON COLUMN public.chat_logs.created_at IS 'Timestamp when the record was created';


--
-- Name: COLUMN chat_logs.updated_at; Type: COMMENT; Schema: public; Owner: omarmohamed
--

COMMENT ON COLUMN public.chat_logs.updated_at IS 'Timestamp when the record was last updated';


--
-- Name: chat_logs_integer_id_seq; Type: SEQUENCE; Schema: public; Owner: omarmohamed
--

CREATE SEQUENCE public.chat_logs_integer_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.chat_logs_integer_id_seq OWNER TO omarmohamed;

--
-- Name: chat_logs_integer_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: omarmohamed
--

ALTER SEQUENCE public.chat_logs_integer_id_seq OWNED BY public.chat_logs.id;


--
-- Name: cities; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.cities (
    data jsonb DEFAULT '{}'::jsonb,
    embedding public.vector(1536),
    geom public.geometry(Point,4326),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    name jsonb,
    description jsonb,
    embedding_backup text,
    name_backup jsonb,
    description_backup jsonb,
    user_id integer,
    region_id integer,
    id integer NOT NULL,
    CONSTRAINT valid_city_embedding CHECK (((embedding IS NULL) OR ((embedding)::text <> '[]'::text)))
);


ALTER TABLE public.cities OWNER TO postgres;

--
-- Name: COLUMN cities.embedding; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.cities.embedding IS 'Vector embedding for semantic search. Use vector operators (<->, <=>) for similarity search.';


--
-- Name: COLUMN cities.geom; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.cities.geom IS 'PostGIS geometry column. Use ST_X(geom) for longitude and ST_Y(geom) for latitude.';


--
-- Name: COLUMN cities.created_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.cities.created_at IS 'Timestamp when the record was created';


--
-- Name: COLUMN cities.updated_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.cities.updated_at IS 'Timestamp when the record was last updated';


--
-- Name: cities_integer_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.cities_integer_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.cities_integer_id_seq OWNER TO postgres;

--
-- Name: cities_integer_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.cities_integer_id_seq OWNED BY public.cities.id;


--
-- Name: connection_pool_stats; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.connection_pool_stats (
    id integer NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    min_connections integer,
    max_connections integer,
    current_connections integer,
    available_connections integer,
    acquisition_time_ms double precision,
    query_count integer,
    error_count integer,
    hour timestamp with time zone,
    total_connections integer,
    waiting_clients integer,
    max_wait_time_ms double precision,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.connection_pool_stats OWNER TO postgres;

--
-- Name: COLUMN connection_pool_stats.created_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.connection_pool_stats.created_at IS 'Timestamp when the record was created';


--
-- Name: COLUMN connection_pool_stats.updated_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.connection_pool_stats.updated_at IS 'Timestamp when the record was last updated';


--
-- Name: connection_pool_monitoring; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.connection_pool_monitoring AS
 SELECT date_trunc('hour'::text, connection_pool_stats.created_at) AS hour,
    avg(connection_pool_stats.current_connections) AS avg_connections,
    max(connection_pool_stats.current_connections) AS max_connections,
    avg(connection_pool_stats.acquisition_time_ms) AS avg_acquisition_time_ms,
    max(connection_pool_stats.acquisition_time_ms) AS max_acquisition_time_ms,
    sum(connection_pool_stats.query_count) AS total_queries,
    sum(connection_pool_stats.error_count) AS total_errors
   FROM public.connection_pool_stats
  GROUP BY (date_trunc('hour'::text, connection_pool_stats.created_at))
  ORDER BY (date_trunc('hour'::text, connection_pool_stats.created_at)) DESC;


ALTER TABLE public.connection_pool_monitoring OWNER TO postgres;

--
-- Name: connection_pool_stats_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.connection_pool_stats_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.connection_pool_stats_id_seq OWNER TO postgres;

--
-- Name: connection_pool_stats_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.connection_pool_stats_id_seq OWNED BY public.connection_pool_stats.id;


--
-- Name: cuisines; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.cuisines (
    type text NOT NULL,
    name jsonb,
    description jsonb,
    popular_dishes jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    region_id integer
);


ALTER TABLE public.cuisines OWNER TO postgres;

--
-- Name: COLUMN cuisines.created_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.cuisines.created_at IS 'Timestamp when the record was created';


--
-- Name: COLUMN cuisines.updated_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.cuisines.updated_at IS 'Timestamp when the record was last updated';


--
-- Name: destination_events; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.destination_events (
    id integer NOT NULL,
    name jsonb NOT NULL,
    description jsonb,
    start_date date,
    end_date date,
    recurring boolean DEFAULT false,
    recurrence_pattern text,
    location_details jsonb,
    event_type text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    destination_id integer
);


ALTER TABLE public.destination_events OWNER TO postgres;

--
-- Name: COLUMN destination_events.created_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.destination_events.created_at IS 'Timestamp when the record was created';


--
-- Name: COLUMN destination_events.updated_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.destination_events.updated_at IS 'Timestamp when the record was last updated';


--
-- Name: destination_events_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.destination_events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.destination_events_id_seq OWNER TO postgres;

--
-- Name: destination_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.destination_events_id_seq OWNED BY public.destination_events.id;


--
-- Name: destination_images; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.destination_images (
    id integer NOT NULL,
    url text NOT NULL,
    caption jsonb,
    is_primary boolean DEFAULT false,
    credit text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    user_id text,
    destination_id integer
);


ALTER TABLE public.destination_images OWNER TO postgres;

--
-- Name: COLUMN destination_images.created_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.destination_images.created_at IS 'Timestamp when the record was created';


--
-- Name: COLUMN destination_images.updated_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.destination_images.updated_at IS 'Timestamp when the record was last updated';


--
-- Name: destination_images_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.destination_images_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.destination_images_id_seq OWNER TO postgres;

--
-- Name: destination_images_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.destination_images_id_seq OWNED BY public.destination_images.id;


--
-- Name: destination_seasons; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.destination_seasons (
    id integer NOT NULL,
    season text NOT NULL,
    start_month integer NOT NULL,
    end_month integer NOT NULL,
    description jsonb,
    temperature_min double precision,
    temperature_max double precision,
    precipitation double precision,
    humidity double precision,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    destination_id integer,
    CONSTRAINT destination_seasons_end_month_check CHECK (((end_month >= 1) AND (end_month <= 12))),
    CONSTRAINT destination_seasons_start_month_check CHECK (((start_month >= 1) AND (start_month <= 12)))
);


ALTER TABLE public.destination_seasons OWNER TO postgres;

--
-- Name: COLUMN destination_seasons.created_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.destination_seasons.created_at IS 'Timestamp when the record was created';


--
-- Name: COLUMN destination_seasons.updated_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.destination_seasons.updated_at IS 'Timestamp when the record was last updated';


--
-- Name: destination_seasons_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.destination_seasons_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.destination_seasons_id_seq OWNER TO postgres;

--
-- Name: destination_seasons_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.destination_seasons_id_seq OWNED BY public.destination_seasons.id;


--
-- Name: destination_types; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.destination_types (
    type text NOT NULL,
    name jsonb,
    description jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.destination_types OWNER TO postgres;

--
-- Name: COLUMN destination_types.created_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.destination_types.created_at IS 'Timestamp when the record was created';


--
-- Name: COLUMN destination_types.updated_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.destination_types.updated_at IS 'Timestamp when the record was last updated';


--
-- Name: destinations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.destinations (
    name jsonb NOT NULL,
    description jsonb,
    type text NOT NULL,
    country text,
    elevation double precision,
    population integer,
    area_km2 double precision,
    timezone text,
    local_language text,
    currency text,
    best_time_to_visit jsonb,
    weather jsonb,
    safety_info jsonb,
    local_customs jsonb,
    travel_tips jsonb,
    unesco_site boolean DEFAULT false,
    data jsonb DEFAULT '{}'::jsonb,
    embedding public.vector(1536),
    geom public.geometry(Point,4326),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    user_id text,
    id integer NOT NULL,
    parent_id integer
);


ALTER TABLE public.destinations OWNER TO postgres;

--
-- Name: COLUMN destinations.embedding; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.destinations.embedding IS 'Vector embedding for semantic search. Use vector operators (<->, <=>) for similarity search.';


--
-- Name: COLUMN destinations.geom; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.destinations.geom IS 'PostGIS geometry column. Use ST_X(geom) for longitude and ST_Y(geom) for latitude.';


--
-- Name: COLUMN destinations.created_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.destinations.created_at IS 'Timestamp when the record was created';


--
-- Name: COLUMN destinations.updated_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.destinations.updated_at IS 'Timestamp when the record was last updated';


--
-- Name: destinations_integer_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.destinations_integer_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.destinations_integer_id_seq OWNER TO postgres;

--
-- Name: destinations_integer_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.destinations_integer_id_seq OWNED BY public.destinations.id;


--
-- Name: event_categories; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.event_categories (
    id text NOT NULL,
    name jsonb NOT NULL,
    description jsonb,
    icon text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.event_categories OWNER TO postgres;

--
-- Name: COLUMN event_categories.created_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.event_categories.created_at IS 'Timestamp when the record was created';


--
-- Name: COLUMN event_categories.updated_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.event_categories.updated_at IS 'Timestamp when the record was last updated';


--
-- Name: events_festivals; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.events_festivals (
    id integer NOT NULL,
    category_id text NOT NULL,
    name jsonb NOT NULL,
    description jsonb NOT NULL,
    start_date date,
    end_date date,
    is_annual boolean DEFAULT true,
    annual_month integer,
    annual_day integer,
    lunar_calendar boolean DEFAULT false,
    location_description jsonb,
    destination_id text,
    venue jsonb,
    organizer jsonb,
    admission jsonb,
    schedule jsonb,
    highlights jsonb,
    historical_significance jsonb,
    tips jsonb,
    images jsonb,
    website text,
    contact_info jsonb,
    tags text[],
    is_featured boolean DEFAULT false,
    view_count integer DEFAULT 0,
    data jsonb DEFAULT '{}'::jsonb,
    embedding public.vector(1536),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    user_id text
);


ALTER TABLE public.events_festivals OWNER TO postgres;

--
-- Name: COLUMN events_festivals.embedding; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.events_festivals.embedding IS 'Vector embedding for semantic search. Use vector operators (<->, <=>) for similarity search.';


--
-- Name: COLUMN events_festivals.created_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.events_festivals.created_at IS 'Timestamp when the record was created';


--
-- Name: COLUMN events_festivals.updated_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.events_festivals.updated_at IS 'Timestamp when the record was last updated';


--
-- Name: events_festivals_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.events_festivals_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.events_festivals_id_seq OWNER TO postgres;

--
-- Name: events_festivals_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.events_festivals_id_seq OWNED BY public.events_festivals.id;


--
-- Name: faq_categories; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.faq_categories (
    id text NOT NULL,
    name jsonb NOT NULL,
    description jsonb,
    icon text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.faq_categories OWNER TO postgres;

--
-- Name: COLUMN faq_categories.created_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.faq_categories.created_at IS 'Timestamp when the record was created';


--
-- Name: COLUMN faq_categories.updated_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.faq_categories.updated_at IS 'Timestamp when the record was last updated';


--
-- Name: favorites; Type: TABLE; Schema: public; Owner: omarmohamed
--

CREATE TABLE public.favorites (
    user_id text,
    target_id text NOT NULL,
    target_type text NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    id integer NOT NULL,
    CONSTRAINT chk_favorites_target_type CHECK ((target_type = ANY (ARRAY['attraction'::text, 'restaurant'::text, 'accommodation'::text, 'city'::text, 'region'::text, 'event'::text, 'tour_package'::text])))
);


ALTER TABLE public.favorites OWNER TO omarmohamed;

--
-- Name: COLUMN favorites.target_id; Type: COMMENT; Schema: public; Owner: omarmohamed
--

COMMENT ON COLUMN public.favorites.target_id IS 'ID of the target entity (attraction, restaurant, etc.)';


--
-- Name: COLUMN favorites.target_type; Type: COMMENT; Schema: public; Owner: omarmohamed
--

COMMENT ON COLUMN public.favorites.target_type IS 'Type of the target entity (attraction, restaurant, etc.)';


--
-- Name: COLUMN favorites.created_at; Type: COMMENT; Schema: public; Owner: omarmohamed
--

COMMENT ON COLUMN public.favorites.created_at IS 'Timestamp when the record was created';


--
-- Name: COLUMN favorites.updated_at; Type: COMMENT; Schema: public; Owner: omarmohamed
--

COMMENT ON COLUMN public.favorites.updated_at IS 'Timestamp when the record was last updated';


--
-- Name: favorites_integer_id_seq; Type: SEQUENCE; Schema: public; Owner: omarmohamed
--

CREATE SEQUENCE public.favorites_integer_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.favorites_integer_id_seq OWNER TO omarmohamed;

--
-- Name: favorites_integer_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: omarmohamed
--

ALTER SEQUENCE public.favorites_integer_id_seq OWNED BY public.favorites.id;


--
-- Name: feedback; Type: TABLE; Schema: public; Owner: omarmohamed
--

CREATE TABLE public.feedback (
    id integer NOT NULL,
    user_id text,
    message_id text,
    rating integer,
    feedback_text text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    session_id integer
);


ALTER TABLE public.feedback OWNER TO omarmohamed;

--
-- Name: COLUMN feedback.created_at; Type: COMMENT; Schema: public; Owner: omarmohamed
--

COMMENT ON COLUMN public.feedback.created_at IS 'Timestamp when the record was created';


--
-- Name: COLUMN feedback.updated_at; Type: COMMENT; Schema: public; Owner: omarmohamed
--

COMMENT ON COLUMN public.feedback.updated_at IS 'Timestamp when the record was last updated';


--
-- Name: feedback_id_seq; Type: SEQUENCE; Schema: public; Owner: omarmohamed
--

CREATE SEQUENCE public.feedback_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.feedback_id_seq OWNER TO omarmohamed;

--
-- Name: feedback_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: omarmohamed
--

ALTER SEQUENCE public.feedback_id_seq OWNED BY public.feedback.id;


--
-- Name: hotels; Type: TABLE; Schema: public; Owner: omarmohamed
--

CREATE TABLE public.hotels (
    type text,
    name jsonb NOT NULL,
    description jsonb,
    address text,
    price_range text,
    data jsonb,
    geom public.geometry(Point,4326),
    embedding public.vector(1536),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    type_id text,
    city_id integer,
    id integer NOT NULL
);


ALTER TABLE public.hotels OWNER TO omarmohamed;

--
-- Name: COLUMN hotels.geom; Type: COMMENT; Schema: public; Owner: omarmohamed
--

COMMENT ON COLUMN public.hotels.geom IS 'PostGIS geometry column. Use ST_X(geom) for longitude and ST_Y(geom) for latitude.';


--
-- Name: COLUMN hotels.embedding; Type: COMMENT; Schema: public; Owner: omarmohamed
--

COMMENT ON COLUMN public.hotels.embedding IS 'Vector embedding for semantic search. Use vector operators (<->, <=>) for similarity search.';


--
-- Name: COLUMN hotels.created_at; Type: COMMENT; Schema: public; Owner: omarmohamed
--

COMMENT ON COLUMN public.hotels.created_at IS 'Timestamp when the record was created';


--
-- Name: COLUMN hotels.updated_at; Type: COMMENT; Schema: public; Owner: omarmohamed
--

COMMENT ON COLUMN public.hotels.updated_at IS 'Timestamp when the record was last updated';


--
-- Name: hotels_integer_id_seq; Type: SEQUENCE; Schema: public; Owner: omarmohamed
--

CREATE SEQUENCE public.hotels_integer_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hotels_integer_id_seq OWNER TO omarmohamed;

--
-- Name: hotels_integer_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: omarmohamed
--

ALTER SEQUENCE public.hotels_integer_id_seq OWNED BY public.hotels.id;


--
-- Name: index_usage_stats; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.index_usage_stats AS
 SELECT t.relname AS table_name,
    i.relname AS index_name,
    s.idx_scan AS index_scans,
    s.idx_tup_read AS tuples_read,
    s.idx_tup_fetch AS tuples_fetched,
    pg_size_pretty(pg_relation_size((i.oid)::regclass)) AS index_size,
        CASE
            WHEN (s.idx_scan = 0) THEN 'Unused'::text
            WHEN (s.idx_scan < 20) THEN 'Rarely used'::text
            WHEN (s.idx_scan < 100) THEN 'Sometimes used'::text
            ELSE 'Frequently used'::text
        END AS usage_category
   FROM ((pg_stat_user_indexes s
     JOIN pg_class t ON ((s.relid = t.oid)))
     JOIN pg_class i ON ((s.indexrelid = i.oid)))
  WHERE (t.relkind = 'r'::"char")
  ORDER BY s.idx_scan DESC;


ALTER TABLE public.index_usage_stats OWNER TO postgres;

--
-- Name: itineraries; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.itineraries (
    id integer NOT NULL,
    type_id text NOT NULL,
    name jsonb NOT NULL,
    description jsonb NOT NULL,
    duration_days integer NOT NULL,
    regions text[],
    cities text[],
    attractions text[],
    restaurants text[],
    accommodations text[],
    transportation_types text[],
    daily_plans jsonb NOT NULL,
    budget_range jsonb,
    best_seasons text[],
    difficulty_level text,
    target_audience jsonb,
    highlights jsonb,
    practical_tips jsonb,
    images jsonb,
    tags text[],
    is_featured boolean DEFAULT false,
    view_count integer DEFAULT 0,
    rating numeric(3,2),
    data jsonb DEFAULT '{}'::jsonb,
    embedding public.vector(1536),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    user_id text
);


ALTER TABLE public.itineraries OWNER TO postgres;

--
-- Name: COLUMN itineraries.embedding; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.itineraries.embedding IS 'Vector embedding for semantic search. Use vector operators (<->, <=>) for similarity search.';


--
-- Name: COLUMN itineraries.created_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.itineraries.created_at IS 'Timestamp when the record was created';


--
-- Name: COLUMN itineraries.updated_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.itineraries.updated_at IS 'Timestamp when the record was last updated';


--
-- Name: itineraries_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.itineraries_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.itineraries_id_seq OWNER TO postgres;

--
-- Name: itineraries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.itineraries_id_seq OWNED BY public.itineraries.id;


--
-- Name: itinerary_attractions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.itinerary_attractions (
    id integer NOT NULL,
    itinerary_id integer NOT NULL,
    attraction_id integer NOT NULL,
    order_index integer NOT NULL,
    day_number integer,
    visit_duration integer,
    notes jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.itinerary_attractions OWNER TO postgres;

--
-- Name: itinerary_attractions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.itinerary_attractions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.itinerary_attractions_id_seq OWNER TO postgres;

--
-- Name: itinerary_attractions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.itinerary_attractions_id_seq OWNED BY public.itinerary_attractions.id;


--
-- Name: itinerary_cities; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.itinerary_cities (
    id integer NOT NULL,
    itinerary_id integer NOT NULL,
    city_id integer NOT NULL,
    order_index integer NOT NULL,
    stay_duration integer,
    notes jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.itinerary_cities OWNER TO postgres;

--
-- Name: itinerary_cities_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.itinerary_cities_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.itinerary_cities_id_seq OWNER TO postgres;

--
-- Name: itinerary_cities_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.itinerary_cities_id_seq OWNED BY public.itinerary_cities.id;


--
-- Name: itinerary_types; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.itinerary_types (
    id text NOT NULL,
    name jsonb NOT NULL,
    description jsonb,
    icon text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.itinerary_types OWNER TO postgres;

--
-- Name: COLUMN itinerary_types.created_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.itinerary_types.created_at IS 'Timestamp when the record was created';


--
-- Name: COLUMN itinerary_types.updated_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.itinerary_types.updated_at IS 'Timestamp when the record was last updated';


--
-- Name: media; Type: TABLE; Schema: public; Owner: omarmohamed
--

CREATE TABLE public.media (
    target_id text NOT NULL,
    target_type text NOT NULL,
    url text NOT NULL,
    type text,
    metadata jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    id integer NOT NULL,
    CONSTRAINT chk_media_target_type CHECK ((target_type = ANY (ARRAY['attraction'::text, 'restaurant'::text, 'accommodation'::text, 'city'::text, 'region'::text, 'event'::text, 'tour_package'::text])))
);


ALTER TABLE public.media OWNER TO omarmohamed;

--
-- Name: COLUMN media.target_id; Type: COMMENT; Schema: public; Owner: omarmohamed
--

COMMENT ON COLUMN public.media.target_id IS 'ID of the target entity (attraction, restaurant, etc.)';


--
-- Name: COLUMN media.target_type; Type: COMMENT; Schema: public; Owner: omarmohamed
--

COMMENT ON COLUMN public.media.target_type IS 'Type of the target entity (attraction, restaurant, etc.)';


--
-- Name: COLUMN media.created_at; Type: COMMENT; Schema: public; Owner: omarmohamed
--

COMMENT ON COLUMN public.media.created_at IS 'Timestamp when the record was created';


--
-- Name: COLUMN media.updated_at; Type: COMMENT; Schema: public; Owner: omarmohamed
--

COMMENT ON COLUMN public.media.updated_at IS 'Timestamp when the record was last updated';


--
-- Name: media_integer_id_seq; Type: SEQUENCE; Schema: public; Owner: omarmohamed
--

CREATE SEQUENCE public.media_integer_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.media_integer_id_seq OWNER TO omarmohamed;

--
-- Name: media_integer_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: omarmohamed
--

ALTER SEQUENCE public.media_integer_id_seq OWNED BY public.media.id;


--
-- Name: perf_attractions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.perf_attractions (
    id text NOT NULL,
    name jsonb,
    description jsonb,
    type_id text,
    city_id text,
    region_id text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.perf_attractions OWNER TO postgres;

--
-- Name: COLUMN perf_attractions.created_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.perf_attractions.created_at IS 'Timestamp when the record was created';


--
-- Name: COLUMN perf_attractions.updated_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.perf_attractions.updated_at IS 'Timestamp when the record was last updated';


--
-- Name: practical_info; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.practical_info (
    id integer NOT NULL,
    category_id text NOT NULL,
    title jsonb NOT NULL,
    content jsonb NOT NULL,
    related_destination_ids text[],
    tags text[],
    is_featured boolean DEFAULT false,
    view_count integer DEFAULT 0,
    helpful_count integer DEFAULT 0,
    not_helpful_count integer DEFAULT 0,
    data jsonb DEFAULT '{}'::jsonb,
    embedding public.vector(1536),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    user_id text
);


ALTER TABLE public.practical_info OWNER TO postgres;

--
-- Name: COLUMN practical_info.embedding; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.practical_info.embedding IS 'Vector embedding for semantic search. Use vector operators (<->, <=>) for similarity search.';


--
-- Name: COLUMN practical_info.created_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.practical_info.created_at IS 'Timestamp when the record was created';


--
-- Name: COLUMN practical_info.updated_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.practical_info.updated_at IS 'Timestamp when the record was last updated';


--
-- Name: practical_info_categories; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.practical_info_categories (
    id text NOT NULL,
    name jsonb NOT NULL,
    description jsonb,
    icon text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.practical_info_categories OWNER TO postgres;

--
-- Name: COLUMN practical_info_categories.created_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.practical_info_categories.created_at IS 'Timestamp when the record was created';


--
-- Name: COLUMN practical_info_categories.updated_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.practical_info_categories.updated_at IS 'Timestamp when the record was last updated';


--
-- Name: practical_info_destinations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.practical_info_destinations (
    id integer NOT NULL,
    practical_info_id integer NOT NULL,
    destination_id integer NOT NULL,
    relevance_score double precision,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.practical_info_destinations OWNER TO postgres;

--
-- Name: practical_info_destinations_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.practical_info_destinations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.practical_info_destinations_id_seq OWNER TO postgres;

--
-- Name: practical_info_destinations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.practical_info_destinations_id_seq OWNED BY public.practical_info_destinations.id;


--
-- Name: practical_info_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.practical_info_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.practical_info_id_seq OWNER TO postgres;

--
-- Name: practical_info_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.practical_info_id_seq OWNED BY public.practical_info.id;


--
-- Name: query_cache; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.query_cache (
    cache_key text NOT NULL,
    query_text text NOT NULL,
    result jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    expires_at timestamp with time zone NOT NULL,
    hit_count integer DEFAULT 0,
    category text,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.query_cache OWNER TO postgres;

--
-- Name: COLUMN query_cache.created_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.query_cache.created_at IS 'Timestamp when the record was created';


--
-- Name: COLUMN query_cache.updated_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.query_cache.updated_at IS 'Timestamp when the record was last updated';


--
-- Name: regions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.regions (
    country text,
    data jsonb,
    embedding public.vector(1536),
    geom public.geometry(Point,4326),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    name jsonb,
    description jsonb,
    user_id integer,
    id integer NOT NULL
);


ALTER TABLE public.regions OWNER TO postgres;

--
-- Name: COLUMN regions.embedding; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.regions.embedding IS 'Vector embedding for semantic search. Use vector operators (<->, <=>) for similarity search.';


--
-- Name: COLUMN regions.geom; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.regions.geom IS 'PostGIS geometry column. Use ST_X(geom) for longitude and ST_Y(geom) for latitude.';


--
-- Name: COLUMN regions.created_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.regions.created_at IS 'Timestamp when the record was created';


--
-- Name: COLUMN regions.updated_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.regions.updated_at IS 'Timestamp when the record was last updated';


--
-- Name: COLUMN regions.name; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.regions.name IS 'Multilingual name in JSONB format with language codes as keys (e.g., {"en": "English Name", "ar": "Arabic Name"})';


--
-- Name: regions_integer_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.regions_integer_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.regions_integer_id_seq OWNER TO postgres;

--
-- Name: regions_integer_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.regions_integer_id_seq OWNED BY public.regions.id;


--
-- Name: restaurant_types; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.restaurant_types (
    type text NOT NULL,
    name jsonb,
    description jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.restaurant_types OWNER TO postgres;

--
-- Name: COLUMN restaurant_types.created_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.restaurant_types.created_at IS 'Timestamp when the record was created';


--
-- Name: COLUMN restaurant_types.updated_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.restaurant_types.updated_at IS 'Timestamp when the record was last updated';


--
-- Name: restaurants; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.restaurants (
    data jsonb DEFAULT '{}'::jsonb,
    embedding public.vector(1536),
    geom public.geometry(Point,4326),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    user_id text,
    name jsonb,
    description jsonb,
    type_id text,
    cuisine_id text,
    price_range text,
    rating numeric(3,1),
    embedding_backup text,
    name_backup jsonb,
    description_backup jsonb,
    region_id integer,
    city_id integer,
    id integer NOT NULL,
    phone character varying(255),
    email character varying(255),
    website character varying(255),
    CONSTRAINT restaurants_price_range_check CHECK ((price_range = ANY (ARRAY['budget'::text, 'mid_range'::text, 'luxury'::text]))),
    CONSTRAINT restaurants_rating_check CHECK (((rating >= (0)::numeric) AND (rating <= (5)::numeric))),
    CONSTRAINT valid_restaurant_embedding CHECK (((embedding IS NULL) OR ((embedding)::text <> '[]'::text)))
);


ALTER TABLE public.restaurants OWNER TO postgres;

--
-- Name: COLUMN restaurants.data; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.restaurants.data IS 'Additional restaurant data in JSONB format. Expected structure:
{
  "contact": {
    "email": string,
    "phone": string,
    "website": string,
    "social_media": {
      "facebook": string,
      "instagram": string
    }
  },
  "features": {
    "wifi": boolean,
    "alcohol": boolean,
    "parking": boolean,
    "smoking": boolean,
    "takeout": boolean,
    "delivery": boolean,
    "reservations": boolean,
    "outdoor_seating": boolean,
    "wheelchair_accessible": boolean
  },
  "menu_items": array of objects,
  "opening_hours": object,
  "dietary_options": object
}';


--
-- Name: COLUMN restaurants.embedding; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.restaurants.embedding IS 'Vector embedding for semantic search. Use vector operators (<->, <=>) for similarity search.';


--
-- Name: COLUMN restaurants.geom; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.restaurants.geom IS 'PostGIS geometry column. Use ST_X(geom) for longitude and ST_Y(geom) for latitude.';


--
-- Name: COLUMN restaurants.created_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.restaurants.created_at IS 'Timestamp when the record was created';


--
-- Name: COLUMN restaurants.updated_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.restaurants.updated_at IS 'Timestamp when the record was last updated';


--
-- Name: restaurants_integer_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.restaurants_integer_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.restaurants_integer_id_seq OWNER TO postgres;

--
-- Name: restaurants_integer_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.restaurants_integer_id_seq OWNED BY public.restaurants.id;


--
-- Name: reviews; Type: TABLE; Schema: public; Owner: omarmohamed
--

CREATE TABLE public.reviews (
    user_id text,
    target_id text NOT NULL,
    target_type text NOT NULL,
    rating integer,
    text text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    id integer NOT NULL,
    CONSTRAINT chk_reviews_target_type CHECK ((target_type = ANY (ARRAY['attraction'::text, 'restaurant'::text, 'accommodation'::text, 'city'::text, 'region'::text, 'event'::text, 'tour_package'::text])))
);


ALTER TABLE public.reviews OWNER TO omarmohamed;

--
-- Name: COLUMN reviews.target_id; Type: COMMENT; Schema: public; Owner: omarmohamed
--

COMMENT ON COLUMN public.reviews.target_id IS 'ID of the target entity (attraction, restaurant, etc.)';


--
-- Name: COLUMN reviews.target_type; Type: COMMENT; Schema: public; Owner: omarmohamed
--

COMMENT ON COLUMN public.reviews.target_type IS 'Type of the target entity (attraction, restaurant, etc.)';


--
-- Name: COLUMN reviews.created_at; Type: COMMENT; Schema: public; Owner: omarmohamed
--

COMMENT ON COLUMN public.reviews.created_at IS 'Timestamp when the record was created';


--
-- Name: COLUMN reviews.updated_at; Type: COMMENT; Schema: public; Owner: omarmohamed
--

COMMENT ON COLUMN public.reviews.updated_at IS 'Timestamp when the record was last updated';


--
-- Name: reviews_integer_id_seq; Type: SEQUENCE; Schema: public; Owner: omarmohamed
--

CREATE SEQUENCE public.reviews_integer_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.reviews_integer_id_seq OWNER TO omarmohamed;

--
-- Name: reviews_integer_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: omarmohamed
--

ALTER SEQUENCE public.reviews_integer_id_seq OWNED BY public.reviews.id;


--
-- Name: schema_migrations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.schema_migrations (
    id integer NOT NULL,
    version character varying(255) NOT NULL,
    name character varying(255) NOT NULL,
    applied_at timestamp without time zone DEFAULT now() NOT NULL,
    checksum character varying(64) NOT NULL,
    execution_time double precision NOT NULL,
    status character varying(20) DEFAULT 'success'::character varying NOT NULL,
    metadata jsonb
);


ALTER TABLE public.schema_migrations OWNER TO postgres;

--
-- Name: schema_migrations_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.schema_migrations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.schema_migrations_id_seq OWNER TO postgres;

--
-- Name: schema_migrations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.schema_migrations_id_seq OWNED BY public.schema_migrations.id;


--
-- Name: sessions; Type: TABLE; Schema: public; Owner: user1
--

CREATE TABLE public.sessions (
    data jsonb,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    expires_at timestamp with time zone,
    user_id integer,
    id integer NOT NULL
);


ALTER TABLE public.sessions OWNER TO user1;

--
-- Name: COLUMN sessions.created_at; Type: COMMENT; Schema: public; Owner: user1
--

COMMENT ON COLUMN public.sessions.created_at IS 'Timestamp when the record was created';


--
-- Name: COLUMN sessions.updated_at; Type: COMMENT; Schema: public; Owner: user1
--

COMMENT ON COLUMN public.sessions.updated_at IS 'Timestamp when the record was last updated';


--
-- Name: sessions_integer_id_seq; Type: SEQUENCE; Schema: public; Owner: user1
--

CREATE SEQUENCE public.sessions_integer_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.sessions_integer_id_seq OWNER TO user1;

--
-- Name: sessions_integer_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user1
--

ALTER SEQUENCE public.sessions_integer_id_seq OWNED BY public.sessions.id;


--
-- Name: test_attractions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.test_attractions (
    id text NOT NULL,
    name jsonb,
    description jsonb,
    type_id text,
    city_id text,
    region_id text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.test_attractions OWNER TO postgres;

--
-- Name: COLUMN test_attractions.created_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.test_attractions.created_at IS 'Timestamp when the record was created';


--
-- Name: COLUMN test_attractions.updated_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.test_attractions.updated_at IS 'Timestamp when the record was last updated';


--
-- Name: test_restaurants; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.test_restaurants (
    id text NOT NULL,
    name jsonb,
    description jsonb,
    cuisine_id text,
    city_id text,
    region_id text,
    price_range text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.test_restaurants OWNER TO postgres;

--
-- Name: COLUMN test_restaurants.created_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.test_restaurants.created_at IS 'Timestamp when the record was created';


--
-- Name: COLUMN test_restaurants.updated_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.test_restaurants.updated_at IS 'Timestamp when the record was last updated';


--
-- Name: tour_package_attractions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tour_package_attractions (
    id integer NOT NULL,
    tour_package_id integer NOT NULL,
    attraction_id integer NOT NULL,
    order_index integer NOT NULL,
    day_number integer,
    visit_duration integer,
    notes jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.tour_package_attractions OWNER TO postgres;

--
-- Name: tour_package_attractions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tour_package_attractions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.tour_package_attractions_id_seq OWNER TO postgres;

--
-- Name: tour_package_attractions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tour_package_attractions_id_seq OWNED BY public.tour_package_attractions.id;


--
-- Name: tour_package_categories; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tour_package_categories (
    id text NOT NULL,
    name jsonb NOT NULL,
    description jsonb,
    icon text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.tour_package_categories OWNER TO postgres;

--
-- Name: COLUMN tour_package_categories.created_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.tour_package_categories.created_at IS 'Timestamp when the record was created';


--
-- Name: COLUMN tour_package_categories.updated_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.tour_package_categories.updated_at IS 'Timestamp when the record was last updated';


--
-- Name: tour_package_destinations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tour_package_destinations (
    id integer NOT NULL,
    tour_package_id integer NOT NULL,
    destination_id integer NOT NULL,
    order_index integer NOT NULL,
    stay_duration integer,
    notes jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.tour_package_destinations OWNER TO postgres;

--
-- Name: tour_package_destinations_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tour_package_destinations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.tour_package_destinations_id_seq OWNER TO postgres;

--
-- Name: tour_package_destinations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tour_package_destinations_id_seq OWNED BY public.tour_package_destinations.id;


--
-- Name: tour_packages; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tour_packages (
    id integer NOT NULL,
    category_id text NOT NULL,
    name jsonb NOT NULL,
    description jsonb NOT NULL,
    duration_days integer NOT NULL,
    price_range jsonb NOT NULL,
    included_services jsonb NOT NULL,
    excluded_services jsonb,
    itinerary jsonb NOT NULL,
    destinations text[] NOT NULL,
    attractions text[],
    accommodations text[],
    transportation_types text[],
    min_group_size integer,
    max_group_size integer,
    difficulty_level text,
    accessibility_info jsonb,
    seasonal_info jsonb,
    booking_info jsonb,
    cancellation_policy jsonb,
    reviews jsonb,
    rating numeric(3,2),
    images jsonb,
    tags text[],
    is_featured boolean DEFAULT false,
    is_private boolean DEFAULT false,
    view_count integer DEFAULT 0,
    booking_count integer DEFAULT 0,
    data jsonb DEFAULT '{}'::jsonb,
    embedding public.vector(1536),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    user_id text
);


ALTER TABLE public.tour_packages OWNER TO postgres;

--
-- Name: COLUMN tour_packages.embedding; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.tour_packages.embedding IS 'Vector embedding for semantic search. Use vector operators (<->, <=>) for similarity search.';


--
-- Name: COLUMN tour_packages.created_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.tour_packages.created_at IS 'Timestamp when the record was created';


--
-- Name: COLUMN tour_packages.updated_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.tour_packages.updated_at IS 'Timestamp when the record was last updated';


--
-- Name: tour_packages_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tour_packages_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.tour_packages_id_seq OWNER TO postgres;

--
-- Name: tour_packages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tour_packages_id_seq OWNED BY public.tour_packages.id;


--
-- Name: tourism_faq_destinations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tourism_faq_destinations (
    id integer NOT NULL,
    tourism_faq_id integer NOT NULL,
    destination_id integer NOT NULL,
    relevance_score double precision,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.tourism_faq_destinations OWNER TO postgres;

--
-- Name: tourism_faq_destinations_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tourism_faq_destinations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.tourism_faq_destinations_id_seq OWNER TO postgres;

--
-- Name: tourism_faq_destinations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tourism_faq_destinations_id_seq OWNED BY public.tourism_faq_destinations.id;


--
-- Name: tourism_faqs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tourism_faqs (
    id integer NOT NULL,
    category_id text NOT NULL,
    question jsonb NOT NULL,
    answer jsonb NOT NULL,
    related_destination_ids text[],
    tags text[],
    is_featured boolean DEFAULT false,
    view_count integer DEFAULT 0,
    helpful_count integer DEFAULT 0,
    not_helpful_count integer DEFAULT 0,
    data jsonb DEFAULT '{}'::jsonb,
    embedding public.vector(1536),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    user_id text
);


ALTER TABLE public.tourism_faqs OWNER TO postgres;

--
-- Name: COLUMN tourism_faqs.embedding; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.tourism_faqs.embedding IS 'Vector embedding for semantic search. Use vector operators (<->, <=>) for similarity search.';


--
-- Name: COLUMN tourism_faqs.created_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.tourism_faqs.created_at IS 'Timestamp when the record was created';


--
-- Name: COLUMN tourism_faqs.updated_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.tourism_faqs.updated_at IS 'Timestamp when the record was last updated';


--
-- Name: tourism_faqs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tourism_faqs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.tourism_faqs_id_seq OWNER TO postgres;

--
-- Name: tourism_faqs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tourism_faqs_id_seq OWNED BY public.tourism_faqs.id;


--
-- Name: transportation_route_stations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.transportation_route_stations (
    route_id integer NOT NULL,
    station_id text NOT NULL,
    stop_order integer NOT NULL,
    arrival_offset_minutes integer,
    departure_offset_minutes integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.transportation_route_stations OWNER TO postgres;

--
-- Name: COLUMN transportation_route_stations.created_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.transportation_route_stations.created_at IS 'Timestamp when the record was created';


--
-- Name: COLUMN transportation_route_stations.updated_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.transportation_route_stations.updated_at IS 'Timestamp when the record was last updated';


--
-- Name: transportation_routes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.transportation_routes (
    id integer NOT NULL,
    transportation_type text NOT NULL,
    name jsonb,
    description jsonb,
    distance_km double precision,
    duration_minutes integer,
    frequency jsonb,
    schedule jsonb,
    price_range jsonb,
    booking_info jsonb,
    amenities jsonb,
    tips jsonb,
    data jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    user_id text,
    destination_id integer,
    origin_id integer
);


ALTER TABLE public.transportation_routes OWNER TO postgres;

--
-- Name: COLUMN transportation_routes.created_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.transportation_routes.created_at IS 'Timestamp when the record was created';


--
-- Name: COLUMN transportation_routes.updated_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.transportation_routes.updated_at IS 'Timestamp when the record was last updated';


--
-- Name: transportation_routes_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.transportation_routes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.transportation_routes_id_seq OWNER TO postgres;

--
-- Name: transportation_routes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.transportation_routes_id_seq OWNED BY public.transportation_routes.id;


--
-- Name: transportation_stations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.transportation_stations (
    id text NOT NULL,
    name jsonb NOT NULL,
    description jsonb,
    station_type text NOT NULL,
    address jsonb,
    contact_info jsonb,
    facilities jsonb,
    accessibility jsonb,
    data jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    user_id text,
    geom public.geometry(Point,4326),
    destination_id integer
);


ALTER TABLE public.transportation_stations OWNER TO postgres;

--
-- Name: COLUMN transportation_stations.created_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.transportation_stations.created_at IS 'Timestamp when the record was created';


--
-- Name: COLUMN transportation_stations.updated_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.transportation_stations.updated_at IS 'Timestamp when the record was last updated';


--
-- Name: COLUMN transportation_stations.geom; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.transportation_stations.geom IS 'PostGIS geometry column. Use ST_X(geom) for longitude and ST_Y(geom) for latitude.';


--
-- Name: transportation_types; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.transportation_types (
    type text NOT NULL,
    name jsonb,
    description jsonb,
    icon text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.transportation_types OWNER TO postgres;

--
-- Name: COLUMN transportation_types.created_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.transportation_types.created_at IS 'Timestamp when the record was created';


--
-- Name: COLUMN transportation_types.updated_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.transportation_types.updated_at IS 'Timestamp when the record was last updated';


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    username text NOT NULL,
    email text,
    password_hash text,
    salt text,
    role text DEFAULT 'user'::text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    last_login timestamp with time zone,
    preferences jsonb,
    id integer NOT NULL
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: COLUMN users.created_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.users.created_at IS 'Timestamp when the record was created';


--
-- Name: COLUMN users.updated_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.users.updated_at IS 'Timestamp when the record was last updated';


--
-- Name: users_integer_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_integer_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_integer_id_seq OWNER TO postgres;

--
-- Name: users_integer_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_integer_id_seq OWNED BY public.users.id;


--
-- Name: vector_indexes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.vector_indexes (
    id integer NOT NULL,
    table_name character varying(100) NOT NULL,
    column_name character varying(100) NOT NULL,
    index_type character varying(20) NOT NULL,
    dimension integer NOT NULL,
    creation_time timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    duration_seconds double precision NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.vector_indexes OWNER TO postgres;

--
-- Name: COLUMN vector_indexes.created_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.vector_indexes.created_at IS 'Timestamp when the record was created';


--
-- Name: COLUMN vector_indexes.updated_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.vector_indexes.updated_at IS 'Timestamp when the record was last updated';


--
-- Name: vector_indexes_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.vector_indexes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.vector_indexes_id_seq OWNER TO postgres;

--
-- Name: vector_indexes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.vector_indexes_id_seq OWNED BY public.vector_indexes.id;


--
-- Name: vector_search_metrics; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.vector_search_metrics (
    id integer NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    table_name character varying(255) NOT NULL,
    query_time_ms double precision NOT NULL,
    result_count integer NOT NULL,
    vector_dimension integer,
    query_type character varying(50),
    additional_info jsonb,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.vector_search_metrics OWNER TO postgres;

--
-- Name: COLUMN vector_search_metrics.created_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.vector_search_metrics.created_at IS 'Timestamp when the record was created';


--
-- Name: COLUMN vector_search_metrics.updated_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.vector_search_metrics.updated_at IS 'Timestamp when the record was last updated';


--
-- Name: vector_search_metrics_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.vector_search_metrics_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.vector_search_metrics_id_seq OWNER TO postgres;

--
-- Name: vector_search_metrics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.vector_search_metrics_id_seq OWNED BY public.vector_search_metrics.id;


--
-- Name: accommodations id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.accommodations ALTER COLUMN id SET DEFAULT nextval('public.accommodations_integer_id_seq'::regclass);


--
-- Name: analytics id; Type: DEFAULT; Schema: public; Owner: user1
--

ALTER TABLE ONLY public.analytics ALTER COLUMN id SET DEFAULT nextval('public.analytics_id_seq'::regclass);


--
-- Name: analytics_events id; Type: DEFAULT; Schema: public; Owner: omarmohamed
--

ALTER TABLE ONLY public.analytics_events ALTER COLUMN id SET DEFAULT nextval('public.analytics_events_integer_id_seq'::regclass);


--
-- Name: attraction_relationships id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.attraction_relationships ALTER COLUMN id SET DEFAULT nextval('public.attraction_relationships_id_seq'::regclass);


--
-- Name: attractions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.attractions ALTER COLUMN id SET DEFAULT nextval('public.attractions_integer_id_seq'::regclass);


--
-- Name: chat_logs id; Type: DEFAULT; Schema: public; Owner: omarmohamed
--

ALTER TABLE ONLY public.chat_logs ALTER COLUMN id SET DEFAULT nextval('public.chat_logs_integer_id_seq'::regclass);


--
-- Name: cities id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cities ALTER COLUMN id SET DEFAULT nextval('public.cities_integer_id_seq'::regclass);


--
-- Name: connection_pool_stats id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.connection_pool_stats ALTER COLUMN id SET DEFAULT nextval('public.connection_pool_stats_id_seq'::regclass);


--
-- Name: destination_events id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.destination_events ALTER COLUMN id SET DEFAULT nextval('public.destination_events_id_seq'::regclass);


--
-- Name: destination_images id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.destination_images ALTER COLUMN id SET DEFAULT nextval('public.destination_images_id_seq'::regclass);


--
-- Name: destination_seasons id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.destination_seasons ALTER COLUMN id SET DEFAULT nextval('public.destination_seasons_id_seq'::regclass);


--
-- Name: destinations id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.destinations ALTER COLUMN id SET DEFAULT nextval('public.destinations_integer_id_seq'::regclass);


--
-- Name: events_festivals id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.events_festivals ALTER COLUMN id SET DEFAULT nextval('public.events_festivals_id_seq'::regclass);


--
-- Name: favorites id; Type: DEFAULT; Schema: public; Owner: omarmohamed
--

ALTER TABLE ONLY public.favorites ALTER COLUMN id SET DEFAULT nextval('public.favorites_integer_id_seq'::regclass);


--
-- Name: feedback id; Type: DEFAULT; Schema: public; Owner: omarmohamed
--

ALTER TABLE ONLY public.feedback ALTER COLUMN id SET DEFAULT nextval('public.feedback_id_seq'::regclass);


--
-- Name: hotels id; Type: DEFAULT; Schema: public; Owner: omarmohamed
--

ALTER TABLE ONLY public.hotels ALTER COLUMN id SET DEFAULT nextval('public.hotels_integer_id_seq'::regclass);


--
-- Name: itineraries id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.itineraries ALTER COLUMN id SET DEFAULT nextval('public.itineraries_id_seq'::regclass);


--
-- Name: itinerary_attractions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.itinerary_attractions ALTER COLUMN id SET DEFAULT nextval('public.itinerary_attractions_id_seq'::regclass);


--
-- Name: itinerary_cities id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.itinerary_cities ALTER COLUMN id SET DEFAULT nextval('public.itinerary_cities_id_seq'::regclass);


--
-- Name: media id; Type: DEFAULT; Schema: public; Owner: omarmohamed
--

ALTER TABLE ONLY public.media ALTER COLUMN id SET DEFAULT nextval('public.media_integer_id_seq'::regclass);


--
-- Name: practical_info id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.practical_info ALTER COLUMN id SET DEFAULT nextval('public.practical_info_id_seq'::regclass);


--
-- Name: practical_info_destinations id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.practical_info_destinations ALTER COLUMN id SET DEFAULT nextval('public.practical_info_destinations_id_seq'::regclass);


--
-- Name: regions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.regions ALTER COLUMN id SET DEFAULT nextval('public.regions_integer_id_seq'::regclass);


--
-- Name: restaurants id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.restaurants ALTER COLUMN id SET DEFAULT nextval('public.restaurants_integer_id_seq'::regclass);


--
-- Name: reviews id; Type: DEFAULT; Schema: public; Owner: omarmohamed
--

ALTER TABLE ONLY public.reviews ALTER COLUMN id SET DEFAULT nextval('public.reviews_integer_id_seq'::regclass);


--
-- Name: schema_migrations id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.schema_migrations ALTER COLUMN id SET DEFAULT nextval('public.schema_migrations_id_seq'::regclass);


--
-- Name: sessions id; Type: DEFAULT; Schema: public; Owner: user1
--

ALTER TABLE ONLY public.sessions ALTER COLUMN id SET DEFAULT nextval('public.sessions_integer_id_seq'::regclass);


--
-- Name: tour_package_attractions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tour_package_attractions ALTER COLUMN id SET DEFAULT nextval('public.tour_package_attractions_id_seq'::regclass);


--
-- Name: tour_package_destinations id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tour_package_destinations ALTER COLUMN id SET DEFAULT nextval('public.tour_package_destinations_id_seq'::regclass);


--
-- Name: tour_packages id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tour_packages ALTER COLUMN id SET DEFAULT nextval('public.tour_packages_id_seq'::regclass);


--
-- Name: tourism_faq_destinations id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tourism_faq_destinations ALTER COLUMN id SET DEFAULT nextval('public.tourism_faq_destinations_id_seq'::regclass);


--
-- Name: tourism_faqs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tourism_faqs ALTER COLUMN id SET DEFAULT nextval('public.tourism_faqs_id_seq'::regclass);


--
-- Name: transportation_routes id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transportation_routes ALTER COLUMN id SET DEFAULT nextval('public.transportation_routes_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_integer_id_seq'::regclass);


--
-- Name: vector_indexes id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vector_indexes ALTER COLUMN id SET DEFAULT nextval('public.vector_indexes_id_seq'::regclass);


--
-- Name: vector_search_metrics id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vector_search_metrics ALTER COLUMN id SET DEFAULT nextval('public.vector_search_metrics_id_seq'::regclass);


--
-- Name: accommodation_types accommodation_types_pkey; Type: CONSTRAINT; Schema: public; Owner: omarmohamed
--

ALTER TABLE ONLY public.accommodation_types
    ADD CONSTRAINT accommodation_types_pkey PRIMARY KEY (type);


--
-- Name: accommodations accommodations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.accommodations
    ADD CONSTRAINT accommodations_pkey PRIMARY KEY (id);


--
-- Name: analytics_events analytics_events_pkey; Type: CONSTRAINT; Schema: public; Owner: omarmohamed
--

ALTER TABLE ONLY public.analytics_events
    ADD CONSTRAINT analytics_events_pkey PRIMARY KEY (id);


--
-- Name: analytics analytics_pkey; Type: CONSTRAINT; Schema: public; Owner: user1
--

ALTER TABLE ONLY public.analytics
    ADD CONSTRAINT analytics_pkey PRIMARY KEY (id);


--
-- Name: attraction_relationships attraction_relationships_attraction_id_related_attraction_i_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.attraction_relationships
    ADD CONSTRAINT attraction_relationships_attraction_id_related_attraction_i_key UNIQUE (attraction_id, related_attraction_id);


--
-- Name: attraction_relationships attraction_relationships_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.attraction_relationships
    ADD CONSTRAINT attraction_relationships_pkey PRIMARY KEY (id);


--
-- Name: attraction_subcategories attraction_subcategories_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.attraction_subcategories
    ADD CONSTRAINT attraction_subcategories_pkey PRIMARY KEY (id);


--
-- Name: attraction_types attraction_types_pkey; Type: CONSTRAINT; Schema: public; Owner: omarmohamed
--

ALTER TABLE ONLY public.attraction_types
    ADD CONSTRAINT attraction_types_pkey PRIMARY KEY (type);


--
-- Name: attractions attractions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.attractions
    ADD CONSTRAINT attractions_pkey PRIMARY KEY (id);


--
-- Name: chat_logs chat_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: omarmohamed
--

ALTER TABLE ONLY public.chat_logs
    ADD CONSTRAINT chat_logs_pkey PRIMARY KEY (id);


--
-- Name: cities cities_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cities
    ADD CONSTRAINT cities_pkey PRIMARY KEY (id);


--
-- Name: connection_pool_stats connection_pool_stats_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.connection_pool_stats
    ADD CONSTRAINT connection_pool_stats_pkey PRIMARY KEY (id);


--
-- Name: cuisines cuisines_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cuisines
    ADD CONSTRAINT cuisines_pkey PRIMARY KEY (type);


--
-- Name: destination_events destination_events_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.destination_events
    ADD CONSTRAINT destination_events_pkey PRIMARY KEY (id);


--
-- Name: destination_images destination_images_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.destination_images
    ADD CONSTRAINT destination_images_pkey PRIMARY KEY (id);


--
-- Name: destination_seasons destination_seasons_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.destination_seasons
    ADD CONSTRAINT destination_seasons_pkey PRIMARY KEY (id);


--
-- Name: destination_types destination_types_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.destination_types
    ADD CONSTRAINT destination_types_pkey PRIMARY KEY (type);


--
-- Name: destinations destinations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.destinations
    ADD CONSTRAINT destinations_pkey PRIMARY KEY (id);


--
-- Name: event_categories event_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.event_categories
    ADD CONSTRAINT event_categories_pkey PRIMARY KEY (id);


--
-- Name: events_festivals events_festivals_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.events_festivals
    ADD CONSTRAINT events_festivals_pkey PRIMARY KEY (id);


--
-- Name: faq_categories faq_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.faq_categories
    ADD CONSTRAINT faq_categories_pkey PRIMARY KEY (id);


--
-- Name: favorites favorites_pkey; Type: CONSTRAINT; Schema: public; Owner: omarmohamed
--

ALTER TABLE ONLY public.favorites
    ADD CONSTRAINT favorites_pkey PRIMARY KEY (id);


--
-- Name: feedback feedback_pkey; Type: CONSTRAINT; Schema: public; Owner: omarmohamed
--

ALTER TABLE ONLY public.feedback
    ADD CONSTRAINT feedback_pkey PRIMARY KEY (id);


--
-- Name: hotels hotels_pkey; Type: CONSTRAINT; Schema: public; Owner: omarmohamed
--

ALTER TABLE ONLY public.hotels
    ADD CONSTRAINT hotels_pkey PRIMARY KEY (id);


--
-- Name: itineraries itineraries_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.itineraries
    ADD CONSTRAINT itineraries_pkey PRIMARY KEY (id);


--
-- Name: itinerary_attractions itinerary_attractions_itinerary_id_attraction_id_day_number_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.itinerary_attractions
    ADD CONSTRAINT itinerary_attractions_itinerary_id_attraction_id_day_number_key UNIQUE (itinerary_id, attraction_id, day_number);


--
-- Name: itinerary_attractions itinerary_attractions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.itinerary_attractions
    ADD CONSTRAINT itinerary_attractions_pkey PRIMARY KEY (id);


--
-- Name: itinerary_cities itinerary_cities_itinerary_id_city_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.itinerary_cities
    ADD CONSTRAINT itinerary_cities_itinerary_id_city_id_key UNIQUE (itinerary_id, city_id);


--
-- Name: itinerary_cities itinerary_cities_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.itinerary_cities
    ADD CONSTRAINT itinerary_cities_pkey PRIMARY KEY (id);


--
-- Name: itinerary_types itinerary_types_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.itinerary_types
    ADD CONSTRAINT itinerary_types_pkey PRIMARY KEY (id);


--
-- Name: media media_pkey; Type: CONSTRAINT; Schema: public; Owner: omarmohamed
--

ALTER TABLE ONLY public.media
    ADD CONSTRAINT media_pkey PRIMARY KEY (id);


--
-- Name: perf_attractions perf_attractions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.perf_attractions
    ADD CONSTRAINT perf_attractions_pkey PRIMARY KEY (id);


--
-- Name: practical_info_categories practical_info_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.practical_info_categories
    ADD CONSTRAINT practical_info_categories_pkey PRIMARY KEY (id);


--
-- Name: practical_info_destinations practical_info_destinations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.practical_info_destinations
    ADD CONSTRAINT practical_info_destinations_pkey PRIMARY KEY (id);


--
-- Name: practical_info_destinations practical_info_destinations_practical_info_id_destination_i_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.practical_info_destinations
    ADD CONSTRAINT practical_info_destinations_practical_info_id_destination_i_key UNIQUE (practical_info_id, destination_id);


--
-- Name: practical_info practical_info_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.practical_info
    ADD CONSTRAINT practical_info_pkey PRIMARY KEY (id);


--
-- Name: query_cache query_cache_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.query_cache
    ADD CONSTRAINT query_cache_pkey PRIMARY KEY (cache_key);


--
-- Name: regions regions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.regions
    ADD CONSTRAINT regions_pkey PRIMARY KEY (id);


--
-- Name: restaurant_types restaurant_types_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.restaurant_types
    ADD CONSTRAINT restaurant_types_pkey PRIMARY KEY (type);


--
-- Name: restaurants restaurants_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.restaurants
    ADD CONSTRAINT restaurants_pkey PRIMARY KEY (id);


--
-- Name: reviews reviews_pkey; Type: CONSTRAINT; Schema: public; Owner: omarmohamed
--

ALTER TABLE ONLY public.reviews
    ADD CONSTRAINT reviews_pkey PRIMARY KEY (id);


--
-- Name: schema_migrations schema_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.schema_migrations
    ADD CONSTRAINT schema_migrations_pkey PRIMARY KEY (id);


--
-- Name: schema_migrations schema_migrations_version_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.schema_migrations
    ADD CONSTRAINT schema_migrations_version_key UNIQUE (version);


--
-- Name: sessions sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: user1
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT sessions_pkey PRIMARY KEY (id);


--
-- Name: test_attractions test_attractions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.test_attractions
    ADD CONSTRAINT test_attractions_pkey PRIMARY KEY (id);


--
-- Name: test_restaurants test_restaurants_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.test_restaurants
    ADD CONSTRAINT test_restaurants_pkey PRIMARY KEY (id);


--
-- Name: tour_package_attractions tour_package_attractions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tour_package_attractions
    ADD CONSTRAINT tour_package_attractions_pkey PRIMARY KEY (id);


--
-- Name: tour_package_attractions tour_package_attractions_tour_package_id_attraction_id_day__key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tour_package_attractions
    ADD CONSTRAINT tour_package_attractions_tour_package_id_attraction_id_day__key UNIQUE (tour_package_id, attraction_id, day_number);


--
-- Name: tour_package_categories tour_package_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tour_package_categories
    ADD CONSTRAINT tour_package_categories_pkey PRIMARY KEY (id);


--
-- Name: tour_package_destinations tour_package_destinations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tour_package_destinations
    ADD CONSTRAINT tour_package_destinations_pkey PRIMARY KEY (id);


--
-- Name: tour_package_destinations tour_package_destinations_tour_package_id_destination_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tour_package_destinations
    ADD CONSTRAINT tour_package_destinations_tour_package_id_destination_id_key UNIQUE (tour_package_id, destination_id);


--
-- Name: tour_packages tour_packages_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tour_packages
    ADD CONSTRAINT tour_packages_pkey PRIMARY KEY (id);


--
-- Name: tourism_faq_destinations tourism_faq_destinations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tourism_faq_destinations
    ADD CONSTRAINT tourism_faq_destinations_pkey PRIMARY KEY (id);


--
-- Name: tourism_faq_destinations tourism_faq_destinations_tourism_faq_id_destination_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tourism_faq_destinations
    ADD CONSTRAINT tourism_faq_destinations_tourism_faq_id_destination_id_key UNIQUE (tourism_faq_id, destination_id);


--
-- Name: tourism_faqs tourism_faqs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tourism_faqs
    ADD CONSTRAINT tourism_faqs_pkey PRIMARY KEY (id);


--
-- Name: transportation_route_stations transportation_route_stations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transportation_route_stations
    ADD CONSTRAINT transportation_route_stations_pkey PRIMARY KEY (route_id, station_id);


--
-- Name: transportation_routes transportation_routes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transportation_routes
    ADD CONSTRAINT transportation_routes_pkey PRIMARY KEY (id);


--
-- Name: transportation_stations transportation_stations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transportation_stations
    ADD CONSTRAINT transportation_stations_pkey PRIMARY KEY (id);


--
-- Name: transportation_types transportation_types_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transportation_types
    ADD CONSTRAINT transportation_types_pkey PRIMARY KEY (type);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: vector_indexes vector_indexes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vector_indexes
    ADD CONSTRAINT vector_indexes_pkey PRIMARY KEY (id);


--
-- Name: vector_search_metrics vector_search_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vector_search_metrics
    ADD CONSTRAINT vector_search_metrics_pkey PRIMARY KEY (id);


--
-- Name: idx_accommodations_city_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_accommodations_city_id ON public.accommodations USING btree (city_id);


--
-- Name: idx_accommodations_data_path_ops; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_accommodations_data_path_ops ON public.accommodations USING gin (data jsonb_path_ops);


--
-- Name: idx_accommodations_description_gin; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_accommodations_description_gin ON public.accommodations USING gin (description);


--
-- Name: idx_accommodations_description_jsonb; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_accommodations_description_jsonb ON public.accommodations USING gin (description jsonb_path_ops);


--
-- Name: idx_accommodations_embedding; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_accommodations_embedding ON public.accommodations USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='64');


--
-- Name: idx_accommodations_geom; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_accommodations_geom ON public.accommodations USING gist (geom);


--
-- Name: idx_accommodations_name_ar; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_accommodations_name_ar ON public.accommodations USING btree (((name -> 'ar'::text)));


--
-- Name: idx_accommodations_name_en; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_accommodations_name_en ON public.accommodations USING btree (((name -> 'en'::text)));


--
-- Name: idx_accommodations_name_gin; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_accommodations_name_gin ON public.accommodations USING gin (name);


--
-- Name: idx_accommodations_name_jsonb; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_accommodations_name_jsonb ON public.accommodations USING gin (name jsonb_path_ops);


--
-- Name: idx_accommodations_price; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_accommodations_price ON public.accommodations USING btree (price_min, price_max);


--
-- Name: idx_accommodations_stars; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_accommodations_stars ON public.accommodations USING btree (stars);


--
-- Name: idx_accommodations_type_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_accommodations_type_id ON public.accommodations USING btree (type_id);


--
-- Name: idx_analytics_event_data_gin; Type: INDEX; Schema: public; Owner: user1
--

CREATE INDEX idx_analytics_event_data_gin ON public.analytics USING gin (event_data);


--
-- Name: idx_analytics_event_type; Type: INDEX; Schema: public; Owner: user1
--

CREATE INDEX idx_analytics_event_type ON public.analytics USING btree (event_type);


--
-- Name: idx_analytics_session; Type: INDEX; Schema: public; Owner: user1
--

CREATE INDEX idx_analytics_session ON public.analytics USING btree (session_id);


--
-- Name: idx_analytics_session_id; Type: INDEX; Schema: public; Owner: user1
--

CREATE INDEX idx_analytics_session_id ON public.analytics USING btree (session_id);


--
-- Name: idx_analytics_time; Type: INDEX; Schema: public; Owner: user1
--

CREATE INDEX idx_analytics_time ON public.analytics USING btree (created_at);


--
-- Name: idx_analytics_timestamp; Type: INDEX; Schema: public; Owner: user1
--

CREATE INDEX idx_analytics_timestamp ON public.analytics USING btree (created_at);


--
-- Name: idx_analytics_type; Type: INDEX; Schema: public; Owner: user1
--

CREATE INDEX idx_analytics_type ON public.analytics USING btree (event_type);


--
-- Name: idx_analytics_user_id; Type: INDEX; Schema: public; Owner: user1
--

CREATE INDEX idx_analytics_user_id ON public.analytics USING btree (user_id);


--
-- Name: idx_attraction_relationships_attraction_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_attraction_relationships_attraction_id ON public.attraction_relationships USING btree (attraction_id);


--
-- Name: idx_attraction_relationships_related_attraction_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_attraction_relationships_related_attraction_id ON public.attraction_relationships USING btree (related_attraction_id);


--
-- Name: idx_attractions_accessibility_info_gin; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_attractions_accessibility_info_gin ON public.attractions USING gin (accessibility_info);


--
-- Name: idx_attractions_city_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_attractions_city_id ON public.attractions USING btree (city_id);


--
-- Name: idx_attractions_data_path_ops; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_attractions_data_path_ops ON public.attractions USING gin (data jsonb_path_ops);


--
-- Name: idx_attractions_description_gin; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_attractions_description_gin ON public.attractions USING gin (description);


--
-- Name: idx_attractions_description_jsonb; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_attractions_description_jsonb ON public.attractions USING gin (description jsonb_path_ops);


--
-- Name: idx_attractions_embedding; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_attractions_embedding ON public.attractions USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='64');


--
-- Name: idx_attractions_entrance_fee; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_attractions_entrance_fee ON public.attractions USING btree (entrance_fee);


--
-- Name: idx_attractions_geom; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_attractions_geom ON public.attractions USING gist (geom);


--
-- Name: idx_attractions_historical_context_gin; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_attractions_historical_context_gin ON public.attractions USING gin (historical_context);


--
-- Name: idx_attractions_name_ar; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_attractions_name_ar ON public.attractions USING btree (((name -> 'ar'::text)));


--
-- Name: idx_attractions_name_en; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_attractions_name_en ON public.attractions USING btree (((name -> 'en'::text)));


--
-- Name: idx_attractions_name_gin; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_attractions_name_gin ON public.attractions USING gin (name);


--
-- Name: idx_attractions_name_jsonb; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_attractions_name_jsonb ON public.attractions USING gin (name jsonb_path_ops);


--
-- Name: idx_attractions_popularity; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_attractions_popularity ON public.attractions USING btree (popularity);


--
-- Name: idx_attractions_related_attractions; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_attractions_related_attractions ON public.attractions USING gin (related_attractions);


--
-- Name: idx_attractions_subcategory_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_attractions_subcategory_id ON public.attractions USING btree (subcategory_id);


--
-- Name: idx_attractions_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_attractions_type ON public.attractions USING btree (type);


--
-- Name: idx_attractions_type_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_attractions_type_id ON public.attractions USING btree (type_id);


--
-- Name: idx_attractions_visiting_info_gin; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_attractions_visiting_info_gin ON public.attractions USING gin (visiting_info);


--
-- Name: idx_cities_description_gin; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_cities_description_gin ON public.cities USING gin (description);


--
-- Name: idx_cities_description_jsonb; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_cities_description_jsonb ON public.cities USING gin (description jsonb_path_ops);


--
-- Name: idx_cities_embedding; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_cities_embedding ON public.cities USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='64');


--
-- Name: idx_cities_geom; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_cities_geom ON public.cities USING gist (geom);


--
-- Name: idx_cities_name_ar; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_cities_name_ar ON public.cities USING btree (((name -> 'ar'::text)));


--
-- Name: idx_cities_name_en; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_cities_name_en ON public.cities USING btree (((name -> 'en'::text)));


--
-- Name: idx_cities_name_gin; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_cities_name_gin ON public.cities USING gin (name);


--
-- Name: idx_cities_name_jsonb; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_cities_name_jsonb ON public.cities USING gin (name jsonb_path_ops);


--
-- Name: idx_cities_region_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_cities_region_id ON public.cities USING btree (region_id);


--
-- Name: idx_connection_pool_stats_hour; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_connection_pool_stats_hour ON public.connection_pool_stats USING btree (hour);


--
-- Name: idx_destination_events_event_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_destination_events_event_type ON public.destination_events USING btree (event_type);


--
-- Name: idx_destination_events_start_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_destination_events_start_date ON public.destination_events USING btree (start_date);


--
-- Name: idx_destination_seasons_season; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_destination_seasons_season ON public.destination_seasons USING btree (season);


--
-- Name: idx_destinations_country; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_destinations_country ON public.destinations USING btree (country);


--
-- Name: idx_destinations_data_gin; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_destinations_data_gin ON public.destinations USING gin (data);


--
-- Name: idx_destinations_description_gin; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_destinations_description_gin ON public.destinations USING gin (description);


--
-- Name: idx_destinations_embedding; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_destinations_embedding ON public.destinations USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='64');


--
-- Name: idx_destinations_geom; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_destinations_geom ON public.destinations USING gist (geom);


--
-- Name: idx_destinations_name_gin; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_destinations_name_gin ON public.destinations USING gin (name);


--
-- Name: idx_destinations_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_destinations_type ON public.destinations USING btree (type);


--
-- Name: idx_events_festivals_annual_month; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_events_festivals_annual_month ON public.events_festivals USING btree (annual_month);


--
-- Name: idx_events_festivals_category_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_events_festivals_category_id ON public.events_festivals USING btree (category_id);


--
-- Name: idx_events_festivals_description_gin; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_events_festivals_description_gin ON public.events_festivals USING gin (description);


--
-- Name: idx_events_festivals_destination_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_events_festivals_destination_id ON public.events_festivals USING btree (destination_id);


--
-- Name: idx_events_festivals_embedding; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_events_festivals_embedding ON public.events_festivals USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='64');


--
-- Name: idx_events_festivals_end_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_events_festivals_end_date ON public.events_festivals USING btree (end_date);


--
-- Name: idx_events_festivals_is_annual; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_events_festivals_is_annual ON public.events_festivals USING btree (is_annual);


--
-- Name: idx_events_festivals_is_featured; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_events_festivals_is_featured ON public.events_festivals USING btree (is_featured);


--
-- Name: idx_events_festivals_name_gin; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_events_festivals_name_gin ON public.events_festivals USING gin (name);


--
-- Name: idx_events_festivals_start_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_events_festivals_start_date ON public.events_festivals USING btree (start_date);


--
-- Name: idx_events_festivals_tags; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_events_festivals_tags ON public.events_festivals USING gin (tags);


--
-- Name: idx_favorites_target; Type: INDEX; Schema: public; Owner: omarmohamed
--

CREATE INDEX idx_favorites_target ON public.favorites USING btree (target_type, target_id);


--
-- Name: idx_hotels_embedding; Type: INDEX; Schema: public; Owner: omarmohamed
--

CREATE INDEX idx_hotels_embedding ON public.hotels USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='64');


--
-- Name: idx_hotels_name_jsonb; Type: INDEX; Schema: public; Owner: omarmohamed
--

CREATE INDEX idx_hotels_name_jsonb ON public.hotels USING gin (name jsonb_path_ops);


--
-- Name: idx_itineraries_attractions; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_itineraries_attractions ON public.itineraries USING gin (attractions);


--
-- Name: idx_itineraries_cities; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_itineraries_cities ON public.itineraries USING gin (cities);


--
-- Name: idx_itineraries_description_gin; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_itineraries_description_gin ON public.itineraries USING gin (description);


--
-- Name: idx_itineraries_duration_days; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_itineraries_duration_days ON public.itineraries USING btree (duration_days);


--
-- Name: idx_itineraries_embedding; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_itineraries_embedding ON public.itineraries USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='64');


--
-- Name: idx_itineraries_is_featured; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_itineraries_is_featured ON public.itineraries USING btree (is_featured);


--
-- Name: idx_itineraries_name_gin; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_itineraries_name_gin ON public.itineraries USING gin (name);


--
-- Name: idx_itineraries_regions; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_itineraries_regions ON public.itineraries USING gin (regions);


--
-- Name: idx_itineraries_tags; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_itineraries_tags ON public.itineraries USING gin (tags);


--
-- Name: idx_itineraries_type_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_itineraries_type_id ON public.itineraries USING btree (type_id);


--
-- Name: idx_itinerary_attractions_attraction_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_itinerary_attractions_attraction_id ON public.itinerary_attractions USING btree (attraction_id);


--
-- Name: idx_itinerary_attractions_itinerary_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_itinerary_attractions_itinerary_id ON public.itinerary_attractions USING btree (itinerary_id);


--
-- Name: idx_itinerary_cities_city_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_itinerary_cities_city_id ON public.itinerary_cities USING btree (city_id);


--
-- Name: idx_itinerary_cities_itinerary_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_itinerary_cities_itinerary_id ON public.itinerary_cities USING btree (itinerary_id);


--
-- Name: idx_media_target; Type: INDEX; Schema: public; Owner: omarmohamed
--

CREATE INDEX idx_media_target ON public.media USING btree (target_type, target_id);


--
-- Name: idx_perf_attractions_city_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_perf_attractions_city_id ON public.perf_attractions USING btree (city_id);


--
-- Name: idx_perf_attractions_type_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_perf_attractions_type_id ON public.perf_attractions USING btree (type_id);


--
-- Name: idx_practical_info_category_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_practical_info_category_id ON public.practical_info USING btree (category_id);


--
-- Name: idx_practical_info_content_gin; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_practical_info_content_gin ON public.practical_info USING gin (content);


--
-- Name: idx_practical_info_destinations_destination_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_practical_info_destinations_destination_id ON public.practical_info_destinations USING btree (destination_id);


--
-- Name: idx_practical_info_destinations_practical_info_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_practical_info_destinations_practical_info_id ON public.practical_info_destinations USING btree (practical_info_id);


--
-- Name: idx_practical_info_embedding; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_practical_info_embedding ON public.practical_info USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='64');


--
-- Name: idx_practical_info_is_featured; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_practical_info_is_featured ON public.practical_info USING btree (is_featured);


--
-- Name: idx_practical_info_related_destination_ids; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_practical_info_related_destination_ids ON public.practical_info USING gin (related_destination_ids);


--
-- Name: idx_practical_info_tags; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_practical_info_tags ON public.practical_info USING gin (tags);


--
-- Name: idx_practical_info_title_gin; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_practical_info_title_gin ON public.practical_info USING gin (title);


--
-- Name: idx_query_cache_category; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_query_cache_category ON public.query_cache USING btree (category);


--
-- Name: idx_query_cache_expires_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_query_cache_expires_at ON public.query_cache USING btree (expires_at);


--
-- Name: idx_regions_country; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_regions_country ON public.regions USING btree (country);


--
-- Name: idx_regions_description_jsonb; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_regions_description_jsonb ON public.regions USING gin (description jsonb_path_ops);


--
-- Name: idx_regions_embedding; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_regions_embedding ON public.regions USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='64');


--
-- Name: idx_regions_geom; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_regions_geom ON public.regions USING gist (geom);


--
-- Name: idx_regions_name_ar; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_regions_name_ar ON public.regions USING btree (((name -> 'ar'::text)));


--
-- Name: idx_regions_name_en; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_regions_name_en ON public.regions USING btree (((name -> 'en'::text)));


--
-- Name: idx_regions_name_jsonb; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_regions_name_jsonb ON public.regions USING gin (name jsonb_path_ops);


--
-- Name: idx_restaurants_city_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_restaurants_city_id ON public.restaurants USING btree (city_id);


--
-- Name: idx_restaurants_cuisine_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_restaurants_cuisine_id ON public.restaurants USING btree (cuisine_id);


--
-- Name: idx_restaurants_data_description; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_restaurants_data_description ON public.restaurants USING btree (((data -> 'description'::text)));


--
-- Name: idx_restaurants_data_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_restaurants_data_name ON public.restaurants USING btree (((data -> 'name'::text)));


--
-- Name: idx_restaurants_data_path_ops; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_restaurants_data_path_ops ON public.restaurants USING gin (data jsonb_path_ops);


--
-- Name: idx_restaurants_description_gin; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_restaurants_description_gin ON public.restaurants USING gin (description);


--
-- Name: idx_restaurants_description_jsonb; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_restaurants_description_jsonb ON public.restaurants USING gin (description jsonb_path_ops);


--
-- Name: idx_restaurants_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_restaurants_email ON public.restaurants USING btree (email);


--
-- Name: idx_restaurants_embedding; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_restaurants_embedding ON public.restaurants USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='64');


--
-- Name: idx_restaurants_geom; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_restaurants_geom ON public.restaurants USING gist (geom);


--
-- Name: idx_restaurants_name_gin; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_restaurants_name_gin ON public.restaurants USING gin (name);


--
-- Name: idx_restaurants_name_jsonb; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_restaurants_name_jsonb ON public.restaurants USING gin (name jsonb_path_ops);


--
-- Name: idx_restaurants_phone; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_restaurants_phone ON public.restaurants USING btree (phone);


--
-- Name: idx_restaurants_price_cuisine; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_restaurants_price_cuisine ON public.restaurants USING btree (price_range, cuisine_id);


--
-- Name: idx_restaurants_price_range; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_restaurants_price_range ON public.restaurants USING btree (price_range);


--
-- Name: idx_restaurants_type_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_restaurants_type_id ON public.restaurants USING btree (type_id);


--
-- Name: idx_reviews_target; Type: INDEX; Schema: public; Owner: omarmohamed
--

CREATE INDEX idx_reviews_target ON public.reviews USING btree (target_type, target_id);


--
-- Name: idx_schema_migrations_version; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_schema_migrations_version ON public.schema_migrations USING btree (version);


--
-- Name: idx_sessions_data_gin; Type: INDEX; Schema: public; Owner: user1
--

CREATE INDEX idx_sessions_data_gin ON public.sessions USING gin (data);


--
-- Name: idx_sessions_expires; Type: INDEX; Schema: public; Owner: user1
--

CREATE INDEX idx_sessions_expires ON public.sessions USING btree (expires_at);


--
-- Name: idx_tour_package_attractions_attraction_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tour_package_attractions_attraction_id ON public.tour_package_attractions USING btree (attraction_id);


--
-- Name: idx_tour_package_attractions_tour_package_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tour_package_attractions_tour_package_id ON public.tour_package_attractions USING btree (tour_package_id);


--
-- Name: idx_tour_package_destinations_destination_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tour_package_destinations_destination_id ON public.tour_package_destinations USING btree (destination_id);


--
-- Name: idx_tour_package_destinations_tour_package_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tour_package_destinations_tour_package_id ON public.tour_package_destinations USING btree (tour_package_id);


--
-- Name: idx_tour_packages_attractions; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tour_packages_attractions ON public.tour_packages USING gin (attractions);


--
-- Name: idx_tour_packages_category_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tour_packages_category_id ON public.tour_packages USING btree (category_id);


--
-- Name: idx_tour_packages_description_gin; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tour_packages_description_gin ON public.tour_packages USING gin (description);


--
-- Name: idx_tour_packages_destinations; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tour_packages_destinations ON public.tour_packages USING gin (destinations);


--
-- Name: idx_tour_packages_duration_days; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tour_packages_duration_days ON public.tour_packages USING btree (duration_days);


--
-- Name: idx_tour_packages_embedding; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tour_packages_embedding ON public.tour_packages USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='64');


--
-- Name: idx_tour_packages_is_featured; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tour_packages_is_featured ON public.tour_packages USING btree (is_featured);


--
-- Name: idx_tour_packages_name_gin; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tour_packages_name_gin ON public.tour_packages USING gin (name);


--
-- Name: idx_tour_packages_rating; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tour_packages_rating ON public.tour_packages USING btree (rating);


--
-- Name: idx_tour_packages_tags; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tour_packages_tags ON public.tour_packages USING gin (tags);


--
-- Name: idx_tourism_faq_destinations_destination_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tourism_faq_destinations_destination_id ON public.tourism_faq_destinations USING btree (destination_id);


--
-- Name: idx_tourism_faq_destinations_tourism_faq_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tourism_faq_destinations_tourism_faq_id ON public.tourism_faq_destinations USING btree (tourism_faq_id);


--
-- Name: idx_tourism_faqs_answer_gin; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tourism_faqs_answer_gin ON public.tourism_faqs USING gin (answer);


--
-- Name: idx_tourism_faqs_category_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tourism_faqs_category_id ON public.tourism_faqs USING btree (category_id);


--
-- Name: idx_tourism_faqs_embedding; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tourism_faqs_embedding ON public.tourism_faqs USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='64');


--
-- Name: idx_tourism_faqs_is_featured; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tourism_faqs_is_featured ON public.tourism_faqs USING btree (is_featured);


--
-- Name: idx_tourism_faqs_question_gin; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tourism_faqs_question_gin ON public.tourism_faqs USING gin (question);


--
-- Name: idx_tourism_faqs_related_destination_ids; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tourism_faqs_related_destination_ids ON public.tourism_faqs USING gin (related_destination_ids);


--
-- Name: idx_tourism_faqs_tags; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tourism_faqs_tags ON public.tourism_faqs USING gin (tags);


--
-- Name: idx_transportation_route_stations_route_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_transportation_route_stations_route_id ON public.transportation_route_stations USING btree (route_id);


--
-- Name: idx_transportation_route_stations_station_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_transportation_route_stations_station_id ON public.transportation_route_stations USING btree (station_id);


--
-- Name: idx_transportation_routes_data_gin; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_transportation_routes_data_gin ON public.transportation_routes USING gin (data);


--
-- Name: idx_transportation_routes_description_gin; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_transportation_routes_description_gin ON public.transportation_routes USING gin (description);


--
-- Name: idx_transportation_routes_name_gin; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_transportation_routes_name_gin ON public.transportation_routes USING gin (name);


--
-- Name: idx_transportation_routes_transportation_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_transportation_routes_transportation_type ON public.transportation_routes USING btree (transportation_type);


--
-- Name: idx_transportation_stations_data_gin; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_transportation_stations_data_gin ON public.transportation_stations USING gin (data);


--
-- Name: idx_transportation_stations_description_gin; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_transportation_stations_description_gin ON public.transportation_stations USING gin (description);


--
-- Name: idx_transportation_stations_name_gin; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_transportation_stations_name_gin ON public.transportation_stations USING gin (name);


--
-- Name: idx_transportation_stations_station_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_transportation_stations_station_type ON public.transportation_stations USING btree (station_type);


--
-- Name: idx_users_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_users_email ON public.users USING btree (email);


--
-- Name: idx_users_role; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_users_role ON public.users USING btree (role);


--
-- Name: idx_users_username; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_users_username ON public.users USING btree (username);


--
-- Name: accommodations trg_invalidate_cache_on_accommodations_change; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_invalidate_cache_on_accommodations_change AFTER INSERT OR DELETE OR UPDATE ON public.accommodations FOR EACH STATEMENT EXECUTE FUNCTION public.invalidate_cache_on_table_change();


--
-- Name: attractions trg_invalidate_cache_on_attractions_change; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_invalidate_cache_on_attractions_change AFTER INSERT OR DELETE OR UPDATE ON public.attractions FOR EACH STATEMENT EXECUTE FUNCTION public.invalidate_cache_on_table_change();


--
-- Name: cities trg_invalidate_cache_on_cities_change; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_invalidate_cache_on_cities_change AFTER INSERT OR DELETE OR UPDATE ON public.cities FOR EACH STATEMENT EXECUTE FUNCTION public.invalidate_cache_on_table_change();


--
-- Name: regions trg_invalidate_cache_on_regions_change; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_invalidate_cache_on_regions_change AFTER INSERT OR DELETE OR UPDATE ON public.regions FOR EACH STATEMENT EXECUTE FUNCTION public.invalidate_cache_on_table_change();


--
-- Name: restaurants trg_invalidate_cache_on_restaurants_change; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_invalidate_cache_on_restaurants_change AFTER INSERT OR DELETE OR UPDATE ON public.restaurants FOR EACH STATEMENT EXECUTE FUNCTION public.invalidate_cache_on_table_change();


--
-- Name: accommodations update_timestamp; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_timestamp BEFORE UPDATE ON public.accommodations FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();


--
-- Name: attraction_subcategories update_timestamp; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_timestamp BEFORE UPDATE ON public.attraction_subcategories FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();


--
-- Name: attractions update_timestamp; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_timestamp BEFORE UPDATE ON public.attractions FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();


--
-- Name: cities update_timestamp; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_timestamp BEFORE UPDATE ON public.cities FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();


--
-- Name: cuisines update_timestamp; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_timestamp BEFORE UPDATE ON public.cuisines FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();


--
-- Name: destination_events update_timestamp; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_timestamp BEFORE UPDATE ON public.destination_events FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();


--
-- Name: destination_images update_timestamp; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_timestamp BEFORE UPDATE ON public.destination_images FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();


--
-- Name: destination_seasons update_timestamp; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_timestamp BEFORE UPDATE ON public.destination_seasons FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();


--
-- Name: destination_types update_timestamp; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_timestamp BEFORE UPDATE ON public.destination_types FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();


--
-- Name: destinations update_timestamp; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_timestamp BEFORE UPDATE ON public.destinations FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();


--
-- Name: event_categories update_timestamp; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_timestamp BEFORE UPDATE ON public.event_categories FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();


--
-- Name: events_festivals update_timestamp; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_timestamp BEFORE UPDATE ON public.events_festivals FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();


--
-- Name: faq_categories update_timestamp; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_timestamp BEFORE UPDATE ON public.faq_categories FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();


--
-- Name: hotels update_timestamp; Type: TRIGGER; Schema: public; Owner: omarmohamed
--

CREATE TRIGGER update_timestamp BEFORE UPDATE ON public.hotels FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();


--
-- Name: itineraries update_timestamp; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_timestamp BEFORE UPDATE ON public.itineraries FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();


--
-- Name: itinerary_types update_timestamp; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_timestamp BEFORE UPDATE ON public.itinerary_types FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();


--
-- Name: perf_attractions update_timestamp; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_timestamp BEFORE UPDATE ON public.perf_attractions FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();


--
-- Name: practical_info update_timestamp; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_timestamp BEFORE UPDATE ON public.practical_info FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();


--
-- Name: practical_info_categories update_timestamp; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_timestamp BEFORE UPDATE ON public.practical_info_categories FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();


--
-- Name: regions update_timestamp; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_timestamp BEFORE UPDATE ON public.regions FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();


--
-- Name: restaurant_types update_timestamp; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_timestamp BEFORE UPDATE ON public.restaurant_types FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();


--
-- Name: restaurants update_timestamp; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_timestamp BEFORE UPDATE ON public.restaurants FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();


--
-- Name: sessions update_timestamp; Type: TRIGGER; Schema: public; Owner: user1
--

CREATE TRIGGER update_timestamp BEFORE UPDATE ON public.sessions FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();


--
-- Name: test_attractions update_timestamp; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_timestamp BEFORE UPDATE ON public.test_attractions FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();


--
-- Name: test_restaurants update_timestamp; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_timestamp BEFORE UPDATE ON public.test_restaurants FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();


--
-- Name: tour_package_categories update_timestamp; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_timestamp BEFORE UPDATE ON public.tour_package_categories FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();


--
-- Name: tour_packages update_timestamp; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_timestamp BEFORE UPDATE ON public.tour_packages FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();


--
-- Name: tourism_faqs update_timestamp; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_timestamp BEFORE UPDATE ON public.tourism_faqs FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();


--
-- Name: transportation_route_stations update_timestamp; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_timestamp BEFORE UPDATE ON public.transportation_route_stations FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();


--
-- Name: transportation_routes update_timestamp; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_timestamp BEFORE UPDATE ON public.transportation_routes FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();


--
-- Name: transportation_stations update_timestamp; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_timestamp BEFORE UPDATE ON public.transportation_stations FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();


--
-- Name: transportation_types update_timestamp; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_timestamp BEFORE UPDATE ON public.transportation_types FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();


--
-- Name: users update_timestamp; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_timestamp BEFORE UPDATE ON public.users FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();


--
-- Name: vector_indexes update_timestamp; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_timestamp BEFORE UPDATE ON public.vector_indexes FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();


--
-- Name: vector_search_metrics update_timestamp; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_timestamp BEFORE UPDATE ON public.vector_search_metrics FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();


--
-- Name: accommodations accommodations_city_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.accommodations
    ADD CONSTRAINT accommodations_city_id_fkey FOREIGN KEY (city_id) REFERENCES public.cities(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: accommodations accommodations_region_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.accommodations
    ADD CONSTRAINT accommodations_region_id_fkey FOREIGN KEY (region_id) REFERENCES public.regions(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: attraction_relationships attraction_relationships_attraction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.attraction_relationships
    ADD CONSTRAINT attraction_relationships_attraction_id_fkey FOREIGN KEY (attraction_id) REFERENCES public.attractions(id) ON DELETE CASCADE;


--
-- Name: attraction_relationships attraction_relationships_related_attraction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.attraction_relationships
    ADD CONSTRAINT attraction_relationships_related_attraction_id_fkey FOREIGN KEY (related_attraction_id) REFERENCES public.attractions(id) ON DELETE CASCADE;


--
-- Name: attraction_subcategories attraction_subcategories_parent_type_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.attraction_subcategories
    ADD CONSTRAINT attraction_subcategories_parent_type_fkey FOREIGN KEY (parent_type) REFERENCES public.attraction_types(type) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: attractions attractions_city_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.attractions
    ADD CONSTRAINT attractions_city_id_fkey FOREIGN KEY (city_id) REFERENCES public.cities(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: attractions attractions_region_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.attractions
    ADD CONSTRAINT attractions_region_id_fkey FOREIGN KEY (region_id) REFERENCES public.regions(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: attractions attractions_subcategory_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.attractions
    ADD CONSTRAINT attractions_subcategory_id_fkey FOREIGN KEY (subcategory_id) REFERENCES public.attraction_subcategories(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: cities cities_region_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cities
    ADD CONSTRAINT cities_region_id_fkey FOREIGN KEY (region_id) REFERENCES public.regions(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: cities cities_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cities
    ADD CONSTRAINT cities_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: cuisines cuisines_region_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cuisines
    ADD CONSTRAINT cuisines_region_id_fkey FOREIGN KEY (region_id) REFERENCES public.regions(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: destinations destinations_parent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.destinations
    ADD CONSTRAINT destinations_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.destinations(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: destinations destinations_type_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.destinations
    ADD CONSTRAINT destinations_type_fkey FOREIGN KEY (type) REFERENCES public.destination_types(type) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: events_festivals events_festivals_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.events_festivals
    ADD CONSTRAINT events_festivals_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.event_categories(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: accommodations fk_accommodations_type; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.accommodations
    ADD CONSTRAINT fk_accommodations_type FOREIGN KEY (type_id) REFERENCES public.accommodation_types(type) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: attractions fk_attractions_type; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.attractions
    ADD CONSTRAINT fk_attractions_type FOREIGN KEY (type_id) REFERENCES public.attraction_types(type) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: hotels hotels_city_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: omarmohamed
--

ALTER TABLE ONLY public.hotels
    ADD CONSTRAINT hotels_city_id_fkey FOREIGN KEY (city_id) REFERENCES public.cities(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: hotels hotels_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: omarmohamed
--

ALTER TABLE ONLY public.hotels
    ADD CONSTRAINT hotels_type_id_fkey FOREIGN KEY (type_id) REFERENCES public.accommodation_types(type) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: itineraries itineraries_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.itineraries
    ADD CONSTRAINT itineraries_type_id_fkey FOREIGN KEY (type_id) REFERENCES public.itinerary_types(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: itinerary_attractions itinerary_attractions_attraction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.itinerary_attractions
    ADD CONSTRAINT itinerary_attractions_attraction_id_fkey FOREIGN KEY (attraction_id) REFERENCES public.attractions(id) ON DELETE CASCADE;


--
-- Name: itinerary_attractions itinerary_attractions_itinerary_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.itinerary_attractions
    ADD CONSTRAINT itinerary_attractions_itinerary_id_fkey FOREIGN KEY (itinerary_id) REFERENCES public.itineraries(id) ON DELETE CASCADE;


--
-- Name: itinerary_cities itinerary_cities_city_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.itinerary_cities
    ADD CONSTRAINT itinerary_cities_city_id_fkey FOREIGN KEY (city_id) REFERENCES public.cities(id) ON DELETE CASCADE;


--
-- Name: itinerary_cities itinerary_cities_itinerary_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.itinerary_cities
    ADD CONSTRAINT itinerary_cities_itinerary_id_fkey FOREIGN KEY (itinerary_id) REFERENCES public.itineraries(id) ON DELETE CASCADE;


--
-- Name: practical_info practical_info_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.practical_info
    ADD CONSTRAINT practical_info_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.practical_info_categories(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: practical_info_destinations practical_info_destinations_destination_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.practical_info_destinations
    ADD CONSTRAINT practical_info_destinations_destination_id_fkey FOREIGN KEY (destination_id) REFERENCES public.destinations(id) ON DELETE CASCADE;


--
-- Name: practical_info_destinations practical_info_destinations_practical_info_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.practical_info_destinations
    ADD CONSTRAINT practical_info_destinations_practical_info_id_fkey FOREIGN KEY (practical_info_id) REFERENCES public.practical_info(id) ON DELETE CASCADE;


--
-- Name: regions regions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.regions
    ADD CONSTRAINT regions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: restaurants restaurants_city_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.restaurants
    ADD CONSTRAINT restaurants_city_id_fkey FOREIGN KEY (city_id) REFERENCES public.cities(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: restaurants restaurants_cuisine_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.restaurants
    ADD CONSTRAINT restaurants_cuisine_id_fkey FOREIGN KEY (cuisine_id) REFERENCES public.cuisines(type) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: restaurants restaurants_region_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.restaurants
    ADD CONSTRAINT restaurants_region_id_fkey FOREIGN KEY (region_id) REFERENCES public.regions(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: restaurants restaurants_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.restaurants
    ADD CONSTRAINT restaurants_type_id_fkey FOREIGN KEY (type_id) REFERENCES public.restaurant_types(type) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: tour_package_attractions tour_package_attractions_attraction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tour_package_attractions
    ADD CONSTRAINT tour_package_attractions_attraction_id_fkey FOREIGN KEY (attraction_id) REFERENCES public.attractions(id) ON DELETE CASCADE;


--
-- Name: tour_package_attractions tour_package_attractions_tour_package_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tour_package_attractions
    ADD CONSTRAINT tour_package_attractions_tour_package_id_fkey FOREIGN KEY (tour_package_id) REFERENCES public.tour_packages(id) ON DELETE CASCADE;


--
-- Name: tour_package_destinations tour_package_destinations_destination_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tour_package_destinations
    ADD CONSTRAINT tour_package_destinations_destination_id_fkey FOREIGN KEY (destination_id) REFERENCES public.destinations(id) ON DELETE CASCADE;


--
-- Name: tour_package_destinations tour_package_destinations_tour_package_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tour_package_destinations
    ADD CONSTRAINT tour_package_destinations_tour_package_id_fkey FOREIGN KEY (tour_package_id) REFERENCES public.tour_packages(id) ON DELETE CASCADE;


--
-- Name: tour_packages tour_packages_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tour_packages
    ADD CONSTRAINT tour_packages_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.tour_package_categories(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: tourism_faq_destinations tourism_faq_destinations_destination_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tourism_faq_destinations
    ADD CONSTRAINT tourism_faq_destinations_destination_id_fkey FOREIGN KEY (destination_id) REFERENCES public.destinations(id) ON DELETE CASCADE;


--
-- Name: tourism_faq_destinations tourism_faq_destinations_tourism_faq_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tourism_faq_destinations
    ADD CONSTRAINT tourism_faq_destinations_tourism_faq_id_fkey FOREIGN KEY (tourism_faq_id) REFERENCES public.tourism_faqs(id) ON DELETE CASCADE;


--
-- Name: tourism_faqs tourism_faqs_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tourism_faqs
    ADD CONSTRAINT tourism_faqs_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.faq_categories(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: transportation_route_stations transportation_route_stations_route_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transportation_route_stations
    ADD CONSTRAINT transportation_route_stations_route_id_fkey FOREIGN KEY (route_id) REFERENCES public.transportation_routes(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: transportation_route_stations transportation_route_stations_station_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transportation_route_stations
    ADD CONSTRAINT transportation_route_stations_station_id_fkey FOREIGN KEY (station_id) REFERENCES public.transportation_stations(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: transportation_routes transportation_routes_transportation_type_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transportation_routes
    ADD CONSTRAINT transportation_routes_transportation_type_fkey FOREIGN KEY (transportation_type) REFERENCES public.transportation_types(type) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: TABLE analytics; Type: ACL; Schema: public; Owner: user1
--

GRANT ALL ON TABLE public.analytics TO "user";


--
-- Name: TABLE analytics_events; Type: ACL; Schema: public; Owner: omarmohamed
--

GRANT ALL ON TABLE public.analytics_events TO "user";


--
-- Name: TABLE feedback; Type: ACL; Schema: public; Owner: omarmohamed
--

GRANT ALL ON TABLE public.feedback TO "user";


--
-- Name: TABLE geography_columns; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.geography_columns TO "user";


--
-- Name: TABLE geometry_columns; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.geometry_columns TO "user";


--
-- Name: TABLE sessions; Type: ACL; Schema: public; Owner: user1
--

GRANT ALL ON TABLE public.sessions TO "user";


--
-- Name: TABLE spatial_ref_sys; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.spatial_ref_sys TO "user";


--
-- PostgreSQL database dump complete
--

