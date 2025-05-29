

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
-- Name: test_schema; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA test_schema;


--
-- Name: pg_trgm; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;


--
-- Name: EXTENSION pg_trgm; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pg_trgm IS 'text similarity measurement and index searching based on trigrams';


--
-- Name: postgis; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA public;


--
-- Name: EXTENSION postgis; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION postgis IS 'PostGIS geometry and geography spatial types and functions';


--
-- Name: vector; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;


--
-- Name: EXTENSION vector; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION vector IS 'vector data type and ivfflat and hnsw access methods';


--
-- Name: add_language_to_jsonb(jsonb, text, text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.add_language_to_jsonb(json_data jsonb, text_value text, lang text) RETURNS jsonb
    LANGUAGE plpgsql IMMUTABLE
    AS $$
BEGIN
    -- Add a new language to an existing JSONB object
    RETURN json_data || jsonb_build_object(lang, text_value);
END;
$$;


--
-- Name: create_language_jsonb(text, text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.create_language_jsonb(text_value text, lang text DEFAULT 'en'::text) RETURNS jsonb
    LANGUAGE plpgsql IMMUTABLE
    AS $$
BEGIN
    -- Create a new JSONB object with the specified language
    RETURN jsonb_build_object(lang, text_value);
END;
$$;


--
-- Name: find_related_attractions(text, integer); Type: FUNCTION; Schema: public; Owner: -
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


--
-- Name: find_routes_from_destination(text, text); Type: FUNCTION; Schema: public; Owner: -
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


--
-- Name: find_routes_to_destination(text, text); Type: FUNCTION; Schema: public; Owner: -
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


--
-- Name: find_transportation_routes(text, text, text); Type: FUNCTION; Schema: public; Owner: -
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


--
-- Name: get_accommodations_by_city(text, text); Type: FUNCTION; Schema: public; Owner: -
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


--
-- Name: get_attraction_by_name(text, text); Type: FUNCTION; Schema: public; Owner: -
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


--
-- Name: get_available_languages(jsonb); Type: FUNCTION; Schema: public; Owner: -
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


--
-- Name: get_destination_children(text); Type: FUNCTION; Schema: public; Owner: -
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


--
-- Name: get_destination_hierarchy(text); Type: FUNCTION; Schema: public; Owner: -
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


--
-- Name: get_events_festivals_by_category(text, integer); Type: FUNCTION; Schema: public; Owner: -
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


--
-- Name: get_events_festivals_by_destination(text, integer); Type: FUNCTION; Schema: public; Owner: -
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


--
-- Name: get_faqs_by_category(text, integer); Type: FUNCTION; Schema: public; Owner: -
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


--
-- Name: get_faqs_by_destination(text, integer); Type: FUNCTION; Schema: public; Owner: -
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


--
-- Name: get_featured_events_festivals(integer); Type: FUNCTION; Schema: public; Owner: -
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


--
-- Name: get_featured_faqs(integer); Type: FUNCTION; Schema: public; Owner: -
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


--
-- Name: get_featured_itineraries(integer); Type: FUNCTION; Schema: public; Owner: -
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


--
-- Name: get_featured_practical_info(integer); Type: FUNCTION; Schema: public; Owner: -
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


--
-- Name: get_featured_tour_packages(integer); Type: FUNCTION; Schema: public; Owner: -
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


--
-- Name: get_itineraries_by_region(text, integer); Type: FUNCTION; Schema: public; Owner: -
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


--
-- Name: get_itineraries_by_type(text, integer); Type: FUNCTION; Schema: public; Owner: -
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


--
-- Name: get_practical_info_by_category(text, integer); Type: FUNCTION; Schema: public; Owner: -
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


--
-- Name: get_practical_info_by_destination(text, integer); Type: FUNCTION; Schema: public; Owner: -
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


--
-- Name: get_text_by_language(jsonb, text); Type: FUNCTION; Schema: public; Owner: -
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


--
-- Name: get_tour_packages_by_category(text, integer); Type: FUNCTION; Schema: public; Owner: -
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


--
-- Name: get_tour_packages_by_destination(text, integer); Type: FUNCTION; Schema: public; Owner: -
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


--
-- Name: get_upcoming_events_festivals(integer); Type: FUNCTION; Schema: public; Owner: -
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


--
-- Name: merge_language_jsonb(jsonb, jsonb); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.merge_language_jsonb(json_data1 jsonb, json_data2 jsonb) RETURNS jsonb
    LANGUAGE plpgsql IMMUTABLE
    AS $$
BEGIN
    -- Merge two JSONB objects, with json_data2 taking precedence
    RETURN json_data1 || json_data2;
END;
$$;


--
-- Name: search_attractions_by_keywords(text, text); Type: FUNCTION; Schema: public; Owner: -
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


--
-- Name: search_events_festivals(text, text, text, date, date, boolean, integer); Type: FUNCTION; Schema: public; Owner: -
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


--
-- Name: search_faqs(text, text, text, integer); Type: FUNCTION; Schema: public; Owner: -
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


--
-- Name: search_itineraries(text, text, integer, integer, text, text, text, integer); Type: FUNCTION; Schema: public; Owner: -
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


--
-- Name: search_jsonb_text(jsonb, text, text); Type: FUNCTION; Schema: public; Owner: -
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


--
-- Name: search_practical_info(text, text, text, integer); Type: FUNCTION; Schema: public; Owner: -
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


--
-- Name: search_tour_packages(text, text, text, integer, integer, numeric, integer); Type: FUNCTION; Schema: public; Owner: -
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


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: accommodation_types; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.accommodation_types (
    type text NOT NULL
);


--
-- Name: accommodations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.accommodations (
    id text NOT NULL,
    name_en text,
    name_ar text,
    description_en text,
    description_ar text,
    type text,
    stars integer,
    city text,
    region text,
    latitude double precision,
    longitude double precision,
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
    city_id text,
    region_id text,
    type_id text
);


--
-- Name: analytics; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.analytics (
    id integer NOT NULL,
    event_type text NOT NULL,
    event_data jsonb,
    session_id text,
    user_id text,
    "timestamp" text NOT NULL
);


--
-- Name: analytics_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.analytics_events (
    id text NOT NULL,
    event_type text,
    event_data text,
    session_id text,
    user_id text,
    "timestamp" timestamp with time zone
);


--
-- Name: analytics_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.analytics_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: analytics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.analytics_id_seq OWNED BY public.analytics.id;


--
-- Name: attraction_subcategories; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: attraction_types; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.attraction_types (
    type text NOT NULL
);


--
-- Name: attractions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.attractions (
    id text NOT NULL,
    name_en text,
    name_ar text,
    description_en text,
    description_ar text,
    city text,
    region text,
    type text,
    latitude double precision,
    longitude double precision,
    data jsonb DEFAULT '{}'::jsonb,
    embedding public.vector(1536),
    geom public.geometry(Point,4326),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    user_id text,
    name jsonb,
    description jsonb,
    city_id text,
    region_id text,
    type_id text,
    subcategory_id text,
    visiting_info jsonb DEFAULT '{}'::jsonb,
    accessibility_info jsonb DEFAULT '{}'::jsonb,
    related_attractions text[] DEFAULT '{}'::text[],
    historical_context jsonb DEFAULT '{}'::jsonb
);


--
-- Name: chat_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.chat_logs (
    id text NOT NULL,
    user_id text,
    message text,
    intent text,
    response text,
    "timestamp" timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: cities; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cities (
    id text NOT NULL,
    name_en text,
    name_ar text,
    region text,
    latitude double precision,
    longitude double precision,
    data jsonb DEFAULT '{}'::jsonb,
    embedding public.vector(1536),
    geom public.geometry(Point,4326),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    user_id text,
    region_id text,
    name jsonb,
    description jsonb
);


--
-- Name: cuisines; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cuisines (
    type text NOT NULL,
    name jsonb,
    description jsonb,
    region text,
    popular_dishes jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: destination_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.destination_events (
    id integer NOT NULL,
    destination_id text NOT NULL,
    name jsonb NOT NULL,
    description jsonb,
    start_date date,
    end_date date,
    recurring boolean DEFAULT false,
    recurrence_pattern text,
    location_details jsonb,
    event_type text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: destination_events_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.destination_events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: destination_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.destination_events_id_seq OWNED BY public.destination_events.id;


--
-- Name: destination_images; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.destination_images (
    id integer NOT NULL,
    destination_id text NOT NULL,
    url text NOT NULL,
    caption jsonb,
    is_primary boolean DEFAULT false,
    credit text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    user_id text
);


--
-- Name: destination_images_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.destination_images_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: destination_images_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.destination_images_id_seq OWNED BY public.destination_images.id;


--
-- Name: destination_seasons; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.destination_seasons (
    id integer NOT NULL,
    destination_id text NOT NULL,
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
    CONSTRAINT destination_seasons_end_month_check CHECK (((end_month >= 1) AND (end_month <= 12))),
    CONSTRAINT destination_seasons_start_month_check CHECK (((start_month >= 1) AND (start_month <= 12)))
);


--
-- Name: destination_seasons_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.destination_seasons_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: destination_seasons_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.destination_seasons_id_seq OWNED BY public.destination_seasons.id;


--
-- Name: destination_types; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.destination_types (
    type text NOT NULL,
    name jsonb,
    description jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: destinations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.destinations (
    id text NOT NULL,
    name jsonb NOT NULL,
    description jsonb,
    type text NOT NULL,
    parent_id text,
    country text,
    latitude double precision,
    longitude double precision,
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
    user_id text
);


--
-- Name: event_categories; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.event_categories (
    id text NOT NULL,
    name jsonb NOT NULL,
    description jsonb,
    icon text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: events_festivals; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: events_festivals_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.events_festivals_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: events_festivals_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.events_festivals_id_seq OWNED BY public.events_festivals.id;


--
-- Name: faq_categories; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.faq_categories (
    id text NOT NULL,
    name jsonb NOT NULL,
    description jsonb,
    icon text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: favorites; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.favorites (
    id text NOT NULL,
    user_id text,
    target_id text NOT NULL,
    target_type text NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: feedback; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.feedback (
    id integer NOT NULL,
    session_id text,
    user_id text,
    message_id text,
    rating integer,
    feedback_text text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: feedback_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.feedback_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: feedback_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.feedback_id_seq OWNED BY public.feedback.id;


--
-- Name: hotels; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.hotels (
    id text NOT NULL,
    city_id text,
    type text,
    name jsonb NOT NULL,
    description jsonb,
    address text,
    latitude double precision,
    longitude double precision,
    price_range text,
    data jsonb,
    geom public.geometry(Point,4326),
    embedding public.vector(1536),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    name_en text,
    name_ar text,
    description_en text,
    description_ar text,
    city text,
    type_id text
);


--
-- Name: itineraries; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.itineraries (
    id integer NOT NULL,
    type_id text NOT NULL,
    name jsonb NOT NULL,
    description jsonb NOT NULL,
    duration_days integer NOT NULL,
    regions text[],
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


--
-- Name: itineraries_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.itineraries_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: itineraries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.itineraries_id_seq OWNED BY public.itineraries.id;


--
-- Name: itinerary_types; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.itinerary_types (
    id text NOT NULL,
    name jsonb NOT NULL,
    description jsonb,
    icon text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: media; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.media (
    id text NOT NULL,
    target_id text NOT NULL,
    target_type text NOT NULL,
    url text NOT NULL,
    type text,
    metadata jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: practical_info; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: practical_info_categories; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.practical_info_categories (
    id text NOT NULL,
    name jsonb NOT NULL,
    description jsonb,
    icon text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: practical_info_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.practical_info_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: practical_info_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.practical_info_id_seq OWNED BY public.practical_info.id;


--
-- Name: regions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.regions (
    id text NOT NULL,
    name_en text NOT NULL,
    name_ar text,
    country text,
    latitude double precision,
    longitude double precision,
    data jsonb,
    embedding public.vector(1536),
    geom public.geometry(Point,4326),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    user_id text,
    name jsonb,
    description jsonb
);


--
-- Name: restaurant_types; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.restaurant_types (
    type text NOT NULL,
    name jsonb,
    description jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: restaurants; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.restaurants (
    id text NOT NULL,
    name_en text,
    name_ar text,
    description_en text,
    description_ar text,
    cuisine text,
    type text,
    city text,
    region text,
    latitude double precision,
    longitude double precision,
    data jsonb DEFAULT '{}'::jsonb,
    embedding public.vector(1536),
    geom public.geometry(Point,4326),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    user_id text,
    name jsonb,
    description jsonb,
    city_id text,
    region_id text,
    type_id text,
    cuisine_id text,
    price_range text,
    rating numeric(3,1),
    CONSTRAINT restaurants_price_range_check CHECK ((price_range = ANY (ARRAY['budget'::text, 'mid_range'::text, 'luxury'::text]))),
    CONSTRAINT restaurants_rating_check CHECK (((rating >= (0)::numeric) AND (rating <= (5)::numeric)))
);


--
-- Name: reviews; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.reviews (
    id text NOT NULL,
    user_id text,
    target_id text NOT NULL,
    target_type text NOT NULL,
    rating integer,
    text text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: schema_migrations; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: schema_migrations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.schema_migrations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: schema_migrations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.schema_migrations_id_seq OWNED BY public.schema_migrations.id;


--
-- Name: sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sessions (
    id text NOT NULL,
    data jsonb,
    created_at text,
    updated_at text,
    expires_at text,
    user_id text
);


--
-- Name: tour_package_categories; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tour_package_categories (
    id text NOT NULL,
    name jsonb NOT NULL,
    description jsonb,
    icon text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: tour_packages; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: tour_packages_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tour_packages_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tour_packages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.tour_packages_id_seq OWNED BY public.tour_packages.id;


--
-- Name: tourism_faqs; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: tourism_faqs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tourism_faqs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tourism_faqs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.tourism_faqs_id_seq OWNED BY public.tourism_faqs.id;


--
-- Name: transportation_route_stations; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: transportation_routes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.transportation_routes (
    id integer NOT NULL,
    origin_id text NOT NULL,
    destination_id text NOT NULL,
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
    user_id text
);


--
-- Name: transportation_routes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.transportation_routes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: transportation_routes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.transportation_routes_id_seq OWNED BY public.transportation_routes.id;


--
-- Name: transportation_stations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.transportation_stations (
    id text NOT NULL,
    name jsonb NOT NULL,
    description jsonb,
    destination_id text NOT NULL,
    station_type text NOT NULL,
    latitude double precision,
    longitude double precision,
    address jsonb,
    contact_info jsonb,
    facilities jsonb,
    accessibility jsonb,
    data jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    user_id text
);


--
-- Name: transportation_types; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.transportation_types (
    type text NOT NULL,
    name jsonb,
    description jsonb,
    icon text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id text NOT NULL,
    username text NOT NULL,
    email text,
    password_hash text,
    salt text,
    role text DEFAULT 'user'::text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    last_login timestamp with time zone,
    preferences jsonb
);


--
-- Name: vector_indexes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.vector_indexes (
    id integer NOT NULL,
    table_name character varying(100) NOT NULL,
    column_name character varying(100) NOT NULL,
    index_type character varying(20) NOT NULL,
    dimension integer NOT NULL,
    creation_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    duration_seconds double precision NOT NULL
);


--
-- Name: vector_indexes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.vector_indexes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: vector_indexes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.vector_indexes_id_seq OWNED BY public.vector_indexes.id;


--
-- Name: vector_search_metrics; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.vector_search_metrics (
    id integer NOT NULL,
    "timestamp" timestamp with time zone DEFAULT now(),
    table_name character varying(255) NOT NULL,
    query_time_ms double precision NOT NULL,
    result_count integer NOT NULL,
    vector_dimension integer,
    query_type character varying(50),
    additional_info jsonb
);


--
-- Name: vector_search_metrics_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.vector_search_metrics_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: vector_search_metrics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.vector_search_metrics_id_seq OWNED BY public.vector_search_metrics.id;


--
-- Name: analytics id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analytics ALTER COLUMN id SET DEFAULT nextval('public.analytics_id_seq'::regclass);


--
-- Name: destination_events id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.destination_events ALTER COLUMN id SET DEFAULT nextval('public.destination_events_id_seq'::regclass);


--
-- Name: destination_images id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.destination_images ALTER COLUMN id SET DEFAULT nextval('public.destination_images_id_seq'::regclass);


--
-- Name: destination_seasons id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.destination_seasons ALTER COLUMN id SET DEFAULT nextval('public.destination_seasons_id_seq'::regclass);


--
-- Name: events_festivals id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.events_festivals ALTER COLUMN id SET DEFAULT nextval('public.events_festivals_id_seq'::regclass);


--
-- Name: feedback id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback ALTER COLUMN id SET DEFAULT nextval('public.feedback_id_seq'::regclass);


--
-- Name: itineraries id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.itineraries ALTER COLUMN id SET DEFAULT nextval('public.itineraries_id_seq'::regclass);


--
-- Name: practical_info id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.practical_info ALTER COLUMN id SET DEFAULT nextval('public.practical_info_id_seq'::regclass);


--
-- Name: schema_migrations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schema_migrations ALTER COLUMN id SET DEFAULT nextval('public.schema_migrations_id_seq'::regclass);


--
-- Name: tour_packages id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tour_packages ALTER COLUMN id SET DEFAULT nextval('public.tour_packages_id_seq'::regclass);


--
-- Name: tourism_faqs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tourism_faqs ALTER COLUMN id SET DEFAULT nextval('public.tourism_faqs_id_seq'::regclass);


--
-- Name: transportation_routes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transportation_routes ALTER COLUMN id SET DEFAULT nextval('public.transportation_routes_id_seq'::regclass);


--
-- Name: vector_indexes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vector_indexes ALTER COLUMN id SET DEFAULT nextval('public.vector_indexes_id_seq'::regclass);


--
-- Name: vector_search_metrics id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vector_search_metrics ALTER COLUMN id SET DEFAULT nextval('public.vector_search_metrics_id_seq'::regclass);


--
-- Name: accommodation_types accommodation_types_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.accommodation_types
    ADD CONSTRAINT accommodation_types_pkey PRIMARY KEY (type);


--
-- Name: accommodations accommodations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.accommodations
    ADD CONSTRAINT accommodations_pkey PRIMARY KEY (id);


--
-- Name: analytics_events analytics_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analytics_events
    ADD CONSTRAINT analytics_events_pkey PRIMARY KEY (id);


--
-- Name: analytics analytics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analytics
    ADD CONSTRAINT analytics_pkey PRIMARY KEY (id);


--
-- Name: attraction_subcategories attraction_subcategories_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attraction_subcategories
    ADD CONSTRAINT attraction_subcategories_pkey PRIMARY KEY (id);


--
-- Name: attraction_types attraction_types_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attraction_types
    ADD CONSTRAINT attraction_types_pkey PRIMARY KEY (type);


--
-- Name: attractions attractions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attractions
    ADD CONSTRAINT attractions_pkey PRIMARY KEY (id);


--
-- Name: chat_logs chat_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_logs
    ADD CONSTRAINT chat_logs_pkey PRIMARY KEY (id);


--
-- Name: cities cities_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cities
    ADD CONSTRAINT cities_pkey PRIMARY KEY (id);


--
-- Name: cuisines cuisines_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cuisines
    ADD CONSTRAINT cuisines_pkey PRIMARY KEY (type);


--
-- Name: destination_events destination_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.destination_events
    ADD CONSTRAINT destination_events_pkey PRIMARY KEY (id);


--
-- Name: destination_images destination_images_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.destination_images
    ADD CONSTRAINT destination_images_pkey PRIMARY KEY (id);


--
-- Name: destination_seasons destination_seasons_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.destination_seasons
    ADD CONSTRAINT destination_seasons_pkey PRIMARY KEY (id);


--
-- Name: destination_types destination_types_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.destination_types
    ADD CONSTRAINT destination_types_pkey PRIMARY KEY (type);


--
-- Name: destinations destinations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.destinations
    ADD CONSTRAINT destinations_pkey PRIMARY KEY (id);


--
-- Name: event_categories event_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_categories
    ADD CONSTRAINT event_categories_pkey PRIMARY KEY (id);


--
-- Name: events_festivals events_festivals_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.events_festivals
    ADD CONSTRAINT events_festivals_pkey PRIMARY KEY (id);


--
-- Name: faq_categories faq_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.faq_categories
    ADD CONSTRAINT faq_categories_pkey PRIMARY KEY (id);


--
-- Name: favorites favorites_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.favorites
    ADD CONSTRAINT favorites_pkey PRIMARY KEY (id);


--
-- Name: feedback feedback_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback
    ADD CONSTRAINT feedback_pkey PRIMARY KEY (id);


--
-- Name: hotels hotels_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hotels
    ADD CONSTRAINT hotels_pkey PRIMARY KEY (id);


--
-- Name: itineraries itineraries_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.itineraries
    ADD CONSTRAINT itineraries_pkey PRIMARY KEY (id);


--
-- Name: itinerary_types itinerary_types_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.itinerary_types
    ADD CONSTRAINT itinerary_types_pkey PRIMARY KEY (id);


--
-- Name: media media_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.media
    ADD CONSTRAINT media_pkey PRIMARY KEY (id);


--
-- Name: practical_info_categories practical_info_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.practical_info_categories
    ADD CONSTRAINT practical_info_categories_pkey PRIMARY KEY (id);


--
-- Name: practical_info practical_info_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.practical_info
    ADD CONSTRAINT practical_info_pkey PRIMARY KEY (id);


--
-- Name: regions regions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.regions
    ADD CONSTRAINT regions_pkey PRIMARY KEY (id);


--
-- Name: restaurant_types restaurant_types_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.restaurant_types
    ADD CONSTRAINT restaurant_types_pkey PRIMARY KEY (type);


--
-- Name: restaurants restaurants_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.restaurants
    ADD CONSTRAINT restaurants_pkey PRIMARY KEY (id);


--
-- Name: reviews reviews_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reviews
    ADD CONSTRAINT reviews_pkey PRIMARY KEY (id);


--
-- Name: schema_migrations schema_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schema_migrations
    ADD CONSTRAINT schema_migrations_pkey PRIMARY KEY (id);


--
-- Name: schema_migrations schema_migrations_version_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schema_migrations
    ADD CONSTRAINT schema_migrations_version_key UNIQUE (version);


--
-- Name: sessions sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT sessions_pkey PRIMARY KEY (id);


--
-- Name: tour_package_categories tour_package_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tour_package_categories
    ADD CONSTRAINT tour_package_categories_pkey PRIMARY KEY (id);


--
-- Name: tour_packages tour_packages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tour_packages
    ADD CONSTRAINT tour_packages_pkey PRIMARY KEY (id);


--
-- Name: tourism_faqs tourism_faqs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tourism_faqs
    ADD CONSTRAINT tourism_faqs_pkey PRIMARY KEY (id);


--
-- Name: transportation_route_stations transportation_route_stations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transportation_route_stations
    ADD CONSTRAINT transportation_route_stations_pkey PRIMARY KEY (route_id, station_id);


--
-- Name: transportation_routes transportation_routes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transportation_routes
    ADD CONSTRAINT transportation_routes_pkey PRIMARY KEY (id);


--
-- Name: transportation_stations transportation_stations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transportation_stations
    ADD CONSTRAINT transportation_stations_pkey PRIMARY KEY (id);


--
-- Name: transportation_types transportation_types_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transportation_types
    ADD CONSTRAINT transportation_types_pkey PRIMARY KEY (type);


--
-- Name: transportation_routes unique_route; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transportation_routes
    ADD CONSTRAINT unique_route UNIQUE (origin_id, destination_id, transportation_type);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: vector_indexes vector_indexes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vector_indexes
    ADD CONSTRAINT vector_indexes_pkey PRIMARY KEY (id);


--
-- Name: vector_search_metrics vector_search_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vector_search_metrics
    ADD CONSTRAINT vector_search_metrics_pkey PRIMARY KEY (id);


--
-- Name: idx_accommodations_city; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_accommodations_city ON public.accommodations USING btree (city);


--
-- Name: idx_accommodations_city_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_accommodations_city_id ON public.accommodations USING btree (city_id);


--
-- Name: idx_accommodations_data_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_accommodations_data_gin ON public.accommodations USING gin (data);


--
-- Name: idx_accommodations_description_jsonb; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_accommodations_description_jsonb ON public.accommodations USING gin (description jsonb_path_ops);


--
-- Name: idx_accommodations_embedding; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_accommodations_embedding ON public.accommodations USING ivfflat (embedding public.vector_cosine_ops);


--
-- Name: idx_accommodations_embedding_hnsw; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_accommodations_embedding_hnsw ON public.accommodations USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='64');


--
-- Name: idx_accommodations_geom; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_accommodations_geom ON public.accommodations USING gist (geom);


--
-- Name: idx_accommodations_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_accommodations_name ON public.accommodations USING btree (name_en, name_ar);


--
-- Name: idx_accommodations_name_ar; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_accommodations_name_ar ON public.accommodations USING btree (((name -> 'ar'::text)));


--
-- Name: idx_accommodations_name_en; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_accommodations_name_en ON public.accommodations USING btree (((name -> 'en'::text)));


--
-- Name: idx_accommodations_name_jsonb; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_accommodations_name_jsonb ON public.accommodations USING gin (name jsonb_path_ops);


--
-- Name: idx_accommodations_region_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_accommodations_region_id ON public.accommodations USING btree (region_id);


--
-- Name: idx_accommodations_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_accommodations_type ON public.accommodations USING btree (type);


--
-- Name: idx_accommodations_type_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_accommodations_type_id ON public.accommodations USING btree (type_id);


--
-- Name: idx_analytics_event_data_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_analytics_event_data_gin ON public.analytics USING gin (event_data);


--
-- Name: idx_analytics_event_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_analytics_event_type ON public.analytics USING btree (event_type);


--
-- Name: idx_analytics_session; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_analytics_session ON public.analytics USING btree (session_id);


--
-- Name: idx_analytics_session_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_analytics_session_id ON public.analytics USING btree (session_id);


--
-- Name: idx_analytics_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_analytics_time ON public.analytics USING btree ("timestamp");


--
-- Name: idx_analytics_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_analytics_timestamp ON public.analytics USING btree ("timestamp");


--
-- Name: idx_analytics_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_analytics_type ON public.analytics USING btree (event_type);


--
-- Name: idx_analytics_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_analytics_user_id ON public.analytics USING btree (user_id);


--
-- Name: idx_attractions_accessibility_info_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_attractions_accessibility_info_gin ON public.attractions USING gin (accessibility_info);


--
-- Name: idx_attractions_city; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_attractions_city ON public.attractions USING btree (city);


--
-- Name: idx_attractions_city_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_attractions_city_id ON public.attractions USING btree (city_id);


--
-- Name: idx_attractions_data_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_attractions_data_gin ON public.attractions USING gin (data);


--
-- Name: idx_attractions_description_jsonb; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_attractions_description_jsonb ON public.attractions USING gin (description jsonb_path_ops);


--
-- Name: idx_attractions_embedding; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_attractions_embedding ON public.attractions USING ivfflat (embedding public.vector_cosine_ops);


--
-- Name: idx_attractions_embedding_hnsw; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_attractions_embedding_hnsw ON public.attractions USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='64');


--
-- Name: idx_attractions_geom; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_attractions_geom ON public.attractions USING gist (geom);


--
-- Name: idx_attractions_historical_context_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_attractions_historical_context_gin ON public.attractions USING gin (historical_context);


--
-- Name: idx_attractions_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_attractions_name ON public.attractions USING btree (name_en, name_ar);


--
-- Name: idx_attractions_name_ar; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_attractions_name_ar ON public.attractions USING btree (((name -> 'ar'::text)));


--
-- Name: idx_attractions_name_en; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_attractions_name_en ON public.attractions USING btree (((name -> 'en'::text)));


--
-- Name: idx_attractions_name_jsonb; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_attractions_name_jsonb ON public.attractions USING gin (name jsonb_path_ops);


--
-- Name: idx_attractions_region_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_attractions_region_id ON public.attractions USING btree (region_id);


--
-- Name: idx_attractions_related_attractions; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_attractions_related_attractions ON public.attractions USING gin (related_attractions);


--
-- Name: idx_attractions_subcategory_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_attractions_subcategory_id ON public.attractions USING btree (subcategory_id);


--
-- Name: idx_attractions_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_attractions_type ON public.attractions USING btree (type);


--
-- Name: idx_attractions_type_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_attractions_type_id ON public.attractions USING btree (type_id);


--
-- Name: idx_attractions_visiting_info_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_attractions_visiting_info_gin ON public.attractions USING gin (visiting_info);


--
-- Name: idx_cities_description_jsonb; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cities_description_jsonb ON public.cities USING gin (description jsonb_path_ops);


--
-- Name: idx_cities_embedding; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cities_embedding ON public.cities USING ivfflat (embedding public.vector_cosine_ops);


--
-- Name: idx_cities_embedding_hnsw; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cities_embedding_hnsw ON public.cities USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='64');


--
-- Name: idx_cities_geom; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cities_geom ON public.cities USING gist (geom);


--
-- Name: idx_cities_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cities_name ON public.cities USING btree (name_en, name_ar);


--
-- Name: idx_cities_name_ar; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cities_name_ar ON public.cities USING btree (((name -> 'ar'::text)));


--
-- Name: idx_cities_name_en; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cities_name_en ON public.cities USING btree (((name -> 'en'::text)));


--
-- Name: idx_cities_name_jsonb; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cities_name_jsonb ON public.cities USING gin (name jsonb_path_ops);


--
-- Name: idx_cities_region; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cities_region ON public.cities USING btree (region);


--
-- Name: idx_cities_region_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cities_region_id ON public.cities USING btree (region_id);


--
-- Name: idx_destination_events_destination_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_destination_events_destination_id ON public.destination_events USING btree (destination_id);


--
-- Name: idx_destination_events_event_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_destination_events_event_type ON public.destination_events USING btree (event_type);


--
-- Name: idx_destination_events_start_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_destination_events_start_date ON public.destination_events USING btree (start_date);


--
-- Name: idx_destination_images_destination_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_destination_images_destination_id ON public.destination_images USING btree (destination_id);


--
-- Name: idx_destination_seasons_destination_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_destination_seasons_destination_id ON public.destination_seasons USING btree (destination_id);


--
-- Name: idx_destination_seasons_season; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_destination_seasons_season ON public.destination_seasons USING btree (season);


--
-- Name: idx_destinations_country; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_destinations_country ON public.destinations USING btree (country);


--
-- Name: idx_destinations_data_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_destinations_data_gin ON public.destinations USING gin (data);


--
-- Name: idx_destinations_description_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_destinations_description_gin ON public.destinations USING gin (description);


--
-- Name: idx_destinations_embedding_hnsw; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_destinations_embedding_hnsw ON public.destinations USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='64');


--
-- Name: idx_destinations_geom; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_destinations_geom ON public.destinations USING gist (geom);


--
-- Name: idx_destinations_name_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_destinations_name_gin ON public.destinations USING gin (name);


--
-- Name: idx_destinations_parent_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_destinations_parent_id ON public.destinations USING btree (parent_id);


--
-- Name: idx_destinations_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_destinations_type ON public.destinations USING btree (type);


--
-- Name: idx_events_festivals_annual_month; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_events_festivals_annual_month ON public.events_festivals USING btree (annual_month);


--
-- Name: idx_events_festivals_category_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_events_festivals_category_id ON public.events_festivals USING btree (category_id);


--
-- Name: idx_events_festivals_description_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_events_festivals_description_gin ON public.events_festivals USING gin (description);


--
-- Name: idx_events_festivals_destination_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_events_festivals_destination_id ON public.events_festivals USING btree (destination_id);


--
-- Name: idx_events_festivals_embedding_hnsw; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_events_festivals_embedding_hnsw ON public.events_festivals USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='64');


--
-- Name: idx_events_festivals_end_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_events_festivals_end_date ON public.events_festivals USING btree (end_date);


--
-- Name: idx_events_festivals_is_annual; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_events_festivals_is_annual ON public.events_festivals USING btree (is_annual);


--
-- Name: idx_events_festivals_is_featured; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_events_festivals_is_featured ON public.events_festivals USING btree (is_featured);


--
-- Name: idx_events_festivals_name_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_events_festivals_name_gin ON public.events_festivals USING gin (name);


--
-- Name: idx_events_festivals_start_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_events_festivals_start_date ON public.events_festivals USING btree (start_date);


--
-- Name: idx_events_festivals_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_events_festivals_tags ON public.events_festivals USING gin (tags);


--
-- Name: idx_hotels_city_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_hotels_city_id ON public.hotels USING btree (city_id);


--
-- Name: idx_hotels_name_jsonb; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_hotels_name_jsonb ON public.hotels USING gin (name jsonb_path_ops);


--
-- Name: idx_itineraries_attractions; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_itineraries_attractions ON public.itineraries USING gin (attractions);


--
-- Name: idx_itineraries_cities; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_itineraries_cities ON public.itineraries USING gin (cities);


--
-- Name: idx_itineraries_description_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_itineraries_description_gin ON public.itineraries USING gin (description);


--
-- Name: idx_itineraries_duration_days; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_itineraries_duration_days ON public.itineraries USING btree (duration_days);


--
-- Name: idx_itineraries_embedding_hnsw; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_itineraries_embedding_hnsw ON public.itineraries USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='64');


--
-- Name: idx_itineraries_is_featured; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_itineraries_is_featured ON public.itineraries USING btree (is_featured);


--
-- Name: idx_itineraries_name_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_itineraries_name_gin ON public.itineraries USING gin (name);


--
-- Name: idx_itineraries_regions; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_itineraries_regions ON public.itineraries USING gin (regions);


--
-- Name: idx_itineraries_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_itineraries_tags ON public.itineraries USING gin (tags);


--
-- Name: idx_itineraries_type_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_itineraries_type_id ON public.itineraries USING btree (type_id);


--
-- Name: idx_practical_info_category_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_practical_info_category_id ON public.practical_info USING btree (category_id);


--
-- Name: idx_practical_info_content_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_practical_info_content_gin ON public.practical_info USING gin (content);


--
-- Name: idx_practical_info_embedding_hnsw; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_practical_info_embedding_hnsw ON public.practical_info USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='64');


--
-- Name: idx_practical_info_is_featured; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_practical_info_is_featured ON public.practical_info USING btree (is_featured);


--
-- Name: idx_practical_info_related_destination_ids; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_practical_info_related_destination_ids ON public.practical_info USING gin (related_destination_ids);


--
-- Name: idx_practical_info_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_practical_info_tags ON public.practical_info USING gin (tags);


--
-- Name: idx_practical_info_title_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_practical_info_title_gin ON public.practical_info USING gin (title);


--
-- Name: idx_regions_country; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_regions_country ON public.regions USING btree (country);


--
-- Name: idx_regions_description_jsonb; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_regions_description_jsonb ON public.regions USING gin (description jsonb_path_ops);


--
-- Name: idx_regions_geom; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_regions_geom ON public.regions USING gist (geom);


--
-- Name: idx_regions_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_regions_name ON public.regions USING btree (name_en, name_ar);


--
-- Name: idx_regions_name_ar; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_regions_name_ar ON public.regions USING btree (((name -> 'ar'::text)));


--
-- Name: idx_regions_name_en; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_regions_name_en ON public.regions USING btree (((name -> 'en'::text)));


--
-- Name: idx_regions_name_jsonb; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_regions_name_jsonb ON public.regions USING gin (name jsonb_path_ops);


--
-- Name: idx_restaurants_city; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_restaurants_city ON public.restaurants USING btree (city);


--
-- Name: idx_restaurants_city_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_restaurants_city_id ON public.restaurants USING btree (city_id);


--
-- Name: idx_restaurants_cuisine; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_restaurants_cuisine ON public.restaurants USING btree (cuisine);


--
-- Name: idx_restaurants_cuisine_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_restaurants_cuisine_id ON public.restaurants USING btree (cuisine_id);


--
-- Name: idx_restaurants_data_description; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_restaurants_data_description ON public.restaurants USING btree (((data -> 'description'::text)));


--
-- Name: idx_restaurants_data_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_restaurants_data_gin ON public.restaurants USING gin (data);


--
-- Name: idx_restaurants_data_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_restaurants_data_name ON public.restaurants USING btree (((data -> 'name'::text)));


--
-- Name: idx_restaurants_description_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_restaurants_description_gin ON public.restaurants USING gin (description);


--
-- Name: idx_restaurants_description_jsonb; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_restaurants_description_jsonb ON public.restaurants USING gin (description jsonb_path_ops);


--
-- Name: idx_restaurants_embedding; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_restaurants_embedding ON public.restaurants USING ivfflat (embedding public.vector_cosine_ops);


--
-- Name: idx_restaurants_embedding_hnsw; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_restaurants_embedding_hnsw ON public.restaurants USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='64');


--
-- Name: idx_restaurants_geom; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_restaurants_geom ON public.restaurants USING gist (geom);


--
-- Name: idx_restaurants_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_restaurants_name ON public.restaurants USING btree (name_en, name_ar);


--
-- Name: idx_restaurants_name_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_restaurants_name_gin ON public.restaurants USING gin (name);


--
-- Name: idx_restaurants_name_jsonb; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_restaurants_name_jsonb ON public.restaurants USING gin (name jsonb_path_ops);


--
-- Name: idx_restaurants_region_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_restaurants_region_id ON public.restaurants USING btree (region_id);


--
-- Name: idx_restaurants_type_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_restaurants_type_id ON public.restaurants USING btree (type_id);


--
-- Name: idx_schema_migrations_version; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_schema_migrations_version ON public.schema_migrations USING btree (version);


--
-- Name: idx_sessions_data_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sessions_data_gin ON public.sessions USING gin (data);


--
-- Name: idx_sessions_expires; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sessions_expires ON public.sessions USING btree (expires_at);


--
-- Name: idx_sessions_expires_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sessions_expires_at ON public.sessions USING btree (expires_at);


--
-- Name: idx_tour_packages_attractions; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tour_packages_attractions ON public.tour_packages USING gin (attractions);


--
-- Name: idx_tour_packages_category_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tour_packages_category_id ON public.tour_packages USING btree (category_id);


--
-- Name: idx_tour_packages_description_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tour_packages_description_gin ON public.tour_packages USING gin (description);


--
-- Name: idx_tour_packages_destinations; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tour_packages_destinations ON public.tour_packages USING gin (destinations);


--
-- Name: idx_tour_packages_duration_days; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tour_packages_duration_days ON public.tour_packages USING btree (duration_days);


--
-- Name: idx_tour_packages_embedding_hnsw; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tour_packages_embedding_hnsw ON public.tour_packages USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='64');


--
-- Name: idx_tour_packages_is_featured; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tour_packages_is_featured ON public.tour_packages USING btree (is_featured);


--
-- Name: idx_tour_packages_name_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tour_packages_name_gin ON public.tour_packages USING gin (name);


--
-- Name: idx_tour_packages_rating; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tour_packages_rating ON public.tour_packages USING btree (rating);


--
-- Name: idx_tour_packages_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tour_packages_tags ON public.tour_packages USING gin (tags);


--
-- Name: idx_tourism_faqs_answer_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tourism_faqs_answer_gin ON public.tourism_faqs USING gin (answer);


--
-- Name: idx_tourism_faqs_category_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tourism_faqs_category_id ON public.tourism_faqs USING btree (category_id);


--
-- Name: idx_tourism_faqs_embedding_hnsw; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tourism_faqs_embedding_hnsw ON public.tourism_faqs USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='64');


--
-- Name: idx_tourism_faqs_is_featured; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tourism_faqs_is_featured ON public.tourism_faqs USING btree (is_featured);


--
-- Name: idx_tourism_faqs_question_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tourism_faqs_question_gin ON public.tourism_faqs USING gin (question);


--
-- Name: idx_tourism_faqs_related_destination_ids; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tourism_faqs_related_destination_ids ON public.tourism_faqs USING gin (related_destination_ids);


--
-- Name: idx_tourism_faqs_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tourism_faqs_tags ON public.tourism_faqs USING gin (tags);


--
-- Name: idx_transportation_route_stations_route_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transportation_route_stations_route_id ON public.transportation_route_stations USING btree (route_id);


--
-- Name: idx_transportation_route_stations_station_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transportation_route_stations_station_id ON public.transportation_route_stations USING btree (station_id);


--
-- Name: idx_transportation_routes_data_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transportation_routes_data_gin ON public.transportation_routes USING gin (data);


--
-- Name: idx_transportation_routes_description_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transportation_routes_description_gin ON public.transportation_routes USING gin (description);


--
-- Name: idx_transportation_routes_destination_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transportation_routes_destination_id ON public.transportation_routes USING btree (destination_id);


--
-- Name: idx_transportation_routes_name_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transportation_routes_name_gin ON public.transportation_routes USING gin (name);


--
-- Name: idx_transportation_routes_origin_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transportation_routes_origin_id ON public.transportation_routes USING btree (origin_id);


--
-- Name: idx_transportation_routes_transportation_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transportation_routes_transportation_type ON public.transportation_routes USING btree (transportation_type);


--
-- Name: idx_transportation_stations_data_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transportation_stations_data_gin ON public.transportation_stations USING gin (data);


--
-- Name: idx_transportation_stations_description_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transportation_stations_description_gin ON public.transportation_stations USING gin (description);


--
-- Name: idx_transportation_stations_destination_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transportation_stations_destination_id ON public.transportation_stations USING btree (destination_id);


--
-- Name: idx_transportation_stations_name_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transportation_stations_name_gin ON public.transportation_stations USING gin (name);


--
-- Name: idx_transportation_stations_station_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transportation_stations_station_type ON public.transportation_stations USING btree (station_type);


--
-- Name: idx_users_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_users_email ON public.users USING btree (email);


--
-- Name: idx_users_role; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_users_role ON public.users USING btree (role);


--
-- Name: idx_users_username; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_users_username ON public.users USING btree (username);


--
-- Name: attractions attractions_subcategory_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attractions
    ADD CONSTRAINT attractions_subcategory_id_fkey FOREIGN KEY (subcategory_id) REFERENCES public.attraction_subcategories(id);


--
-- Name: cities cities_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cities
    ADD CONSTRAINT cities_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: destination_events destination_events_destination_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.destination_events
    ADD CONSTRAINT destination_events_destination_id_fkey FOREIGN KEY (destination_id) REFERENCES public.destinations(id) ON DELETE CASCADE;


--
-- Name: destination_images destination_images_destination_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.destination_images
    ADD CONSTRAINT destination_images_destination_id_fkey FOREIGN KEY (destination_id) REFERENCES public.destinations(id) ON DELETE CASCADE;


--
-- Name: destination_seasons destination_seasons_destination_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.destination_seasons
    ADD CONSTRAINT destination_seasons_destination_id_fkey FOREIGN KEY (destination_id) REFERENCES public.destinations(id) ON DELETE CASCADE;


--
-- Name: destinations destinations_parent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.destinations
    ADD CONSTRAINT destinations_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.destinations(id);


--
-- Name: destinations destinations_type_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.destinations
    ADD CONSTRAINT destinations_type_fkey FOREIGN KEY (type) REFERENCES public.destination_types(type);


--
-- Name: events_festivals events_festivals_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.events_festivals
    ADD CONSTRAINT events_festivals_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.event_categories(id) ON DELETE CASCADE;


--
-- Name: feedback feedback_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback
    ADD CONSTRAINT feedback_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.sessions(id);


--
-- Name: accommodations fk_accommodations_city; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.accommodations
    ADD CONSTRAINT fk_accommodations_city FOREIGN KEY (city_id) REFERENCES public.cities(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: accommodations fk_accommodations_region; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.accommodations
    ADD CONSTRAINT fk_accommodations_region FOREIGN KEY (region_id) REFERENCES public.regions(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: accommodations fk_accommodations_type; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.accommodations
    ADD CONSTRAINT fk_accommodations_type FOREIGN KEY (type_id) REFERENCES public.accommodation_types(type) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: attraction_subcategories fk_attraction_subcategories_parent_type; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attraction_subcategories
    ADD CONSTRAINT fk_attraction_subcategories_parent_type FOREIGN KEY (parent_type) REFERENCES public.attraction_types(type) ON DELETE CASCADE;


--
-- Name: attractions fk_attractions_city; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attractions
    ADD CONSTRAINT fk_attractions_city FOREIGN KEY (city_id) REFERENCES public.cities(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: attractions fk_attractions_region; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attractions
    ADD CONSTRAINT fk_attractions_region FOREIGN KEY (region_id) REFERENCES public.regions(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: attractions fk_attractions_type; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attractions
    ADD CONSTRAINT fk_attractions_type FOREIGN KEY (type_id) REFERENCES public.attraction_types(type) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: cities fk_cities_region; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cities
    ADD CONSTRAINT fk_cities_region FOREIGN KEY (region_id) REFERENCES public.regions(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: cities fk_cities_user; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cities
    ADD CONSTRAINT fk_cities_user FOREIGN KEY (user_id) REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: hotels hotels_type_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hotels
    ADD CONSTRAINT hotels_type_fkey FOREIGN KEY (type) REFERENCES public.accommodation_types(type);


--
-- Name: hotels hotels_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hotels
    ADD CONSTRAINT hotels_type_id_fkey FOREIGN KEY (type_id) REFERENCES public.accommodation_types(type);


--
-- Name: itineraries itineraries_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.itineraries
    ADD CONSTRAINT itineraries_type_id_fkey FOREIGN KEY (type_id) REFERENCES public.itinerary_types(id) ON DELETE CASCADE;


--
-- Name: practical_info practical_info_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.practical_info
    ADD CONSTRAINT practical_info_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.practical_info_categories(id) ON DELETE CASCADE;


--
-- Name: regions regions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.regions
    ADD CONSTRAINT regions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: restaurants restaurants_city_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.restaurants
    ADD CONSTRAINT restaurants_city_id_fkey FOREIGN KEY (city_id) REFERENCES public.cities(id);


--
-- Name: restaurants restaurants_cuisine_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.restaurants
    ADD CONSTRAINT restaurants_cuisine_id_fkey FOREIGN KEY (cuisine_id) REFERENCES public.cuisines(type);


--
-- Name: restaurants restaurants_region_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.restaurants
    ADD CONSTRAINT restaurants_region_id_fkey FOREIGN KEY (region_id) REFERENCES public.regions(id);


--
-- Name: restaurants restaurants_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.restaurants
    ADD CONSTRAINT restaurants_type_id_fkey FOREIGN KEY (type_id) REFERENCES public.restaurant_types(type);


--
-- Name: sessions sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: tour_packages tour_packages_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tour_packages
    ADD CONSTRAINT tour_packages_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.tour_package_categories(id) ON DELETE CASCADE;


--
-- Name: tourism_faqs tourism_faqs_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tourism_faqs
    ADD CONSTRAINT tourism_faqs_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.faq_categories(id) ON DELETE CASCADE;


--
-- Name: transportation_route_stations transportation_route_stations_route_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transportation_route_stations
    ADD CONSTRAINT transportation_route_stations_route_id_fkey FOREIGN KEY (route_id) REFERENCES public.transportation_routes(id) ON DELETE CASCADE;


--
-- Name: transportation_route_stations transportation_route_stations_station_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transportation_route_stations
    ADD CONSTRAINT transportation_route_stations_station_id_fkey FOREIGN KEY (station_id) REFERENCES public.transportation_stations(id) ON DELETE CASCADE;


--
-- Name: transportation_routes transportation_routes_destination_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transportation_routes
    ADD CONSTRAINT transportation_routes_destination_id_fkey FOREIGN KEY (destination_id) REFERENCES public.destinations(id) ON DELETE CASCADE;


--
-- Name: transportation_routes transportation_routes_origin_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transportation_routes
    ADD CONSTRAINT transportation_routes_origin_id_fkey FOREIGN KEY (origin_id) REFERENCES public.destinations(id) ON DELETE CASCADE;


--
-- Name: transportation_routes transportation_routes_transportation_type_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transportation_routes
    ADD CONSTRAINT transportation_routes_transportation_type_fkey FOREIGN KEY (transportation_type) REFERENCES public.transportation_types(type);


--
-- Name: transportation_stations transportation_stations_destination_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transportation_stations
    ADD CONSTRAINT transportation_stations_destination_id_fkey FOREIGN KEY (destination_id) REFERENCES public.destinations(id) ON DELETE CASCADE;


--
-- Name: attraction_relationships; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.attraction_relationships (
    id integer NOT NULL,
    attraction_id integer NOT NULL,
    related_attraction_id integer NOT NULL,
    relationship_type character varying DEFAULT 'related'::character varying,
    description jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: attraction_relationships_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.attraction_relationships_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: attraction_relationships_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.attraction_relationships_id_seq OWNED BY public.attraction_relationships.id;


--
-- Name: itinerary_attractions; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: itinerary_attractions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.itinerary_attractions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: itinerary_attractions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.itinerary_attractions_id_seq OWNED BY public.itinerary_attractions.id;


--
-- Name: itinerary_cities; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: itinerary_cities_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.itinerary_cities_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: itinerary_cities_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.itinerary_cities_id_seq OWNED BY public.itinerary_cities.id;


--
-- Name: tour_package_attractions; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: tour_package_attractions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tour_package_attractions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tour_package_attractions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.tour_package_attractions_id_seq OWNED BY public.tour_package_attractions.id;


--
-- Name: tour_package_destinations; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: tour_package_destinations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tour_package_destinations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tour_package_destinations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.tour_package_destinations_id_seq OWNED BY public.tour_package_destinations.id;


--
-- Name: attraction_relationships id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attraction_relationships ALTER COLUMN id SET DEFAULT nextval('public.attraction_relationships_id_seq'::regclass);


--
-- Name: itinerary_attractions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.itinerary_attractions ALTER COLUMN id SET DEFAULT nextval('public.itinerary_attractions_id_seq'::regclass);


--
-- Name: itinerary_cities id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.itinerary_cities ALTER COLUMN id SET DEFAULT nextval('public.itinerary_cities_id_seq'::regclass);


--
-- Name: tour_package_attractions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tour_package_attractions ALTER COLUMN id SET DEFAULT nextval('public.tour_package_attractions_id_seq'::regclass);


--
-- Name: tour_package_destinations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tour_package_destinations ALTER COLUMN id SET DEFAULT nextval('public.tour_package_destinations_id_seq'::regclass);


--
-- Name: attraction_relationships attraction_relationships_attraction_id_related_attraction_i_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attraction_relationships
    ADD CONSTRAINT attraction_relationships_attraction_id_related_attraction_i_key UNIQUE (attraction_id, related_attraction_id);


--
-- Name: attraction_relationships attraction_relationships_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attraction_relationships
    ADD CONSTRAINT attraction_relationships_pkey PRIMARY KEY (id);


--
-- Name: itinerary_attractions itinerary_attractions_itinerary_id_attraction_id_day_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.itinerary_attractions
    ADD CONSTRAINT itinerary_attractions_itinerary_id_attraction_id_day_number_key UNIQUE (itinerary_id, attraction_id, day_number);


--
-- Name: itinerary_attractions itinerary_attractions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.itinerary_attractions
    ADD CONSTRAINT itinerary_attractions_pkey PRIMARY KEY (id);


--
-- Name: itinerary_cities itinerary_cities_itinerary_id_city_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.itinerary_cities
    ADD CONSTRAINT itinerary_cities_itinerary_id_city_id_key UNIQUE (itinerary_id, city_id);


--
-- Name: itinerary_cities itinerary_cities_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.itinerary_cities
    ADD CONSTRAINT itinerary_cities_pkey PRIMARY KEY (id);


--
-- Name: tour_package_attractions tour_package_attractions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tour_package_attractions
    ADD CONSTRAINT tour_package_attractions_pkey PRIMARY KEY (id);


--
-- Name: tour_package_attractions tour_package_attractions_tour_package_id_attraction_id_day__key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tour_package_attractions
    ADD CONSTRAINT tour_package_attractions_tour_package_id_attraction_id_day__key UNIQUE (tour_package_id, attraction_id, day_number);


--
-- Name: tour_package_destinations tour_package_destinations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tour_package_destinations
    ADD CONSTRAINT tour_package_destinations_pkey PRIMARY KEY (id);


--
-- Name: tour_package_destinations tour_package_destinations_tour_package_id_destination_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tour_package_destinations
    ADD CONSTRAINT tour_package_destinations_tour_package_id_destination_id_key UNIQUE (tour_package_id, destination_id);


--
-- Name: idx_attraction_relationships_attraction_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_attraction_relationships_attraction_id ON public.attraction_relationships USING btree (attraction_id);


--
-- Name: idx_attraction_relationships_related_attraction_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_attraction_relationships_related_attraction_id ON public.attraction_relationships USING btree (related_attraction_id);


--
-- Name: idx_itinerary_attractions_attraction_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_itinerary_attractions_attraction_id ON public.itinerary_attractions USING btree (attraction_id);


--
-- Name: idx_itinerary_attractions_itinerary_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_itinerary_attractions_itinerary_id ON public.itinerary_attractions USING btree (itinerary_id);


--
-- Name: idx_itinerary_cities_city_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_itinerary_cities_city_id ON public.itinerary_cities USING btree (city_id);


--
-- Name: idx_itinerary_cities_itinerary_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_itinerary_cities_itinerary_id ON public.itinerary_cities USING btree (itinerary_id);


--
-- Name: idx_tour_package_attractions_attraction_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tour_package_attractions_attraction_id ON public.tour_package_attractions USING btree (attraction_id);


--
-- Name: idx_tour_package_attractions_tour_package_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tour_package_attractions_tour_package_id ON public.tour_package_attractions USING btree (tour_package_id);


--
-- Name: idx_tour_package_destinations_destination_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tour_package_destinations_destination_id ON public.tour_package_destinations USING btree (destination_id);


--
-- Name: idx_tour_package_destinations_tour_package_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tour_package_destinations_tour_package_id ON public.tour_package_destinations USING btree (tour_package_id);


--
-- Name: attraction_relationships attraction_relationships_attraction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attraction_relationships
    ADD CONSTRAINT attraction_relationships_attraction_id_fkey FOREIGN KEY (attraction_id) REFERENCES public.attractions(id);


--
-- Name: attraction_relationships attraction_relationships_related_attraction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attraction_relationships
    ADD CONSTRAINT attraction_relationships_related_attraction_id_fkey FOREIGN KEY (related_attraction_id) REFERENCES public.attractions(id);


--
-- Name: itinerary_attractions itinerary_attractions_attraction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.itinerary_attractions
    ADD CONSTRAINT itinerary_attractions_attraction_id_fkey FOREIGN KEY (attraction_id) REFERENCES public.attractions(id);


--
-- Name: itinerary_attractions itinerary_attractions_itinerary_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.itinerary_attractions
    ADD CONSTRAINT itinerary_attractions_itinerary_id_fkey FOREIGN KEY (itinerary_id) REFERENCES public.itineraries(id);


--
-- Name: itinerary_cities itinerary_cities_city_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.itinerary_cities
    ADD CONSTRAINT itinerary_cities_city_id_fkey FOREIGN KEY (city_id) REFERENCES public.cities(id);


--
-- Name: itinerary_cities itinerary_cities_itinerary_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.itinerary_cities
    ADD CONSTRAINT itinerary_cities_itinerary_id_fkey FOREIGN KEY (itinerary_id) REFERENCES public.itineraries(id);


--
-- Name: tour_package_attractions tour_package_attractions_attraction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tour_package_attractions
    ADD CONSTRAINT tour_package_attractions_attraction_id_fkey FOREIGN KEY (attraction_id) REFERENCES public.attractions(id);


--
-- Name: tour_package_attractions tour_package_attractions_tour_package_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tour_package_attractions
    ADD CONSTRAINT tour_package_attractions_tour_package_id_fkey FOREIGN KEY (tour_package_id) REFERENCES public.tour_packages(id);


--
-- Name: tour_package_destinations tour_package_destinations_destination_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tour_package_destinations
    ADD CONSTRAINT tour_package_destinations_destination_id_fkey FOREIGN KEY (destination_id) REFERENCES public.destinations(id);


--
-- Name: tour_package_destinations tour_package_destinations_tour_package_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tour_package_destinations
    ADD CONSTRAINT tour_package_destinations_tour_package_id_fkey FOREIGN KEY (tour_package_id) REFERENCES public.tour_packages(id);


--
-- PostgreSQL database dump complete
--

