-- Migration: Add JSONB Helper Functions
-- Date: 2024-06-17
-- Adds helper functions for common JSONB operations

-- 0. Enable required extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 1. Function to get text from JSONB by language
CREATE OR REPLACE FUNCTION get_text_by_language(
    json_data JSONB,
    lang TEXT DEFAULT 'en'
) RETURNS TEXT AS $$
BEGIN
    -- Return the text for the specified language, or English if not found
    RETURN COALESCE(
        json_data->>lang,
        json_data->>'en',
        json_data->>'ar',
        json_data::TEXT
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 2. Function to search JSONB text fields by language
CREATE OR REPLACE FUNCTION search_jsonb_text(
    json_data JSONB,
    search_text TEXT,
    lang TEXT DEFAULT 'en'
) RETURNS BOOLEAN AS $$
BEGIN
    -- Check if the text for the specified language contains the search text
    RETURN (
        (json_data->>lang) ILIKE '%' || search_text || '%'
        OR
        (json_data->>'en') ILIKE '%' || search_text || '%'
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 3. Function to get all available languages in a JSONB object
CREATE OR REPLACE FUNCTION get_available_languages(
    json_data JSONB
) RETURNS TEXT[] AS $$
BEGIN
    -- Return an array of language codes
    RETURN ARRAY(
        SELECT jsonb_object_keys(json_data)
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 4. Function to merge JSONB objects with language-specific content
CREATE OR REPLACE FUNCTION merge_language_jsonb(
    json_data1 JSONB,
    json_data2 JSONB
) RETURNS JSONB AS $$
BEGIN
    -- Merge two JSONB objects, with json_data2 taking precedence
    RETURN json_data1 || json_data2;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 5. Function to create a new JSONB object with a single language
CREATE OR REPLACE FUNCTION create_language_jsonb(
    text_value TEXT,
    lang TEXT DEFAULT 'en'
) RETURNS JSONB AS $$
BEGIN
    -- Create a new JSONB object with the specified language
    RETURN jsonb_build_object(lang, text_value);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 6. Function to add a language to an existing JSONB object
CREATE OR REPLACE FUNCTION add_language_to_jsonb(
    json_data JSONB,
    text_value TEXT,
    lang TEXT
) RETURNS JSONB AS $$
BEGIN
    -- Add a new language to an existing JSONB object
    RETURN json_data || jsonb_build_object(lang, text_value);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 7. Function to get attraction by name in any language
CREATE OR REPLACE FUNCTION get_attraction_by_name(
    search_name TEXT,
    lang TEXT DEFAULT 'en'
) RETURNS TABLE (
    id TEXT,
    name JSONB,
    description JSONB,
    city TEXT,
    region TEXT,
    type TEXT
) AS $$
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
$$ LANGUAGE plpgsql STABLE;

-- 8. Function to get accommodations by city in any language
CREATE OR REPLACE FUNCTION get_accommodations_by_city(
    city_name TEXT,
    lang TEXT DEFAULT 'en'
) RETURNS TABLE (
    id TEXT,
    name JSONB,
    description JSONB,
    city TEXT,
    type TEXT,
    stars INTEGER
) AS $$
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
$$ LANGUAGE plpgsql STABLE;

-- 9. Function to search attractions by description keywords
CREATE OR REPLACE FUNCTION search_attractions_by_keywords(
    keywords TEXT,
    lang TEXT DEFAULT 'en'
) RETURNS TABLE (
    id TEXT,
    name JSONB,
    description JSONB,
    city TEXT,
    region TEXT,
    type TEXT,
    relevance FLOAT
) AS $$
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
$$ LANGUAGE plpgsql STABLE;
