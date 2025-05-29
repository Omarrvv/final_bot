-- Migration: Update Database Manager Functions for Junction Tables
-- Date: 2025-07-15
-- Purpose: Update database manager functions to use junction tables instead of array columns

BEGIN;

-- Log the migration start
DO $$
BEGIN
    RAISE NOTICE 'Starting migration to update database manager functions for junction tables';
END $$;

-- 1. Create a function to get related attractions using the junction table
CREATE OR REPLACE FUNCTION get_related_attractions(
    p_attraction_id INTEGER,
    p_limit INTEGER DEFAULT 5
)
RETURNS TABLE (
    id INTEGER,
    name JSONB,
    description JSONB,
    type_id TEXT,
    city_id INTEGER,
    region_id INTEGER,
    relationship_type TEXT,
    relationship_description JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        a.id,
        a.name,
        a.description,
        a.type_id,
        a.city_id,
        a.region_id,
        ar.relationship_type,
        ar.description AS relationship_description
    FROM 
        attraction_relationships ar
        JOIN attractions a ON ar.related_attraction_id = a.id
    WHERE 
        ar.attraction_id = p_attraction_id
    ORDER BY
        a.name->>'en'
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- 2. Create a function to get attractions in an itinerary using the junction table
CREATE OR REPLACE FUNCTION get_itinerary_attractions(
    p_itinerary_id INTEGER,
    p_limit INTEGER DEFAULT 20
)
RETURNS TABLE (
    id INTEGER,
    name JSONB,
    description JSONB,
    type_id TEXT,
    city_id INTEGER,
    region_id INTEGER,
    order_index INTEGER,
    day_number INTEGER,
    visit_duration INTEGER,
    notes JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        a.id,
        a.name,
        a.description,
        a.type_id,
        a.city_id,
        a.region_id,
        ia.order_index,
        ia.day_number,
        ia.visit_duration,
        ia.notes
    FROM 
        itinerary_attractions ia
        JOIN attractions a ON ia.attraction_id = a.id
    WHERE 
        ia.itinerary_id = p_itinerary_id
    ORDER BY
        ia.day_number, ia.order_index
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- 3. Create a function to get cities in an itinerary using the junction table
CREATE OR REPLACE FUNCTION get_itinerary_cities(
    p_itinerary_id INTEGER,
    p_limit INTEGER DEFAULT 20
)
RETURNS TABLE (
    id INTEGER,
    name JSONB,
    description JSONB,
    region_id INTEGER,
    order_index INTEGER,
    stay_duration INTEGER,
    notes JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.id,
        c.name,
        c.description,
        c.region_id,
        ic.order_index,
        ic.stay_duration,
        ic.notes
    FROM 
        itinerary_cities ic
        JOIN cities c ON ic.city_id = c.id
    WHERE 
        ic.itinerary_id = p_itinerary_id
    ORDER BY
        ic.order_index
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- 4. Create a function to get attractions in a tour package using the junction table
CREATE OR REPLACE FUNCTION get_tour_package_attractions(
    p_tour_package_id INTEGER,
    p_limit INTEGER DEFAULT 20
)
RETURNS TABLE (
    id INTEGER,
    name JSONB,
    description JSONB,
    type_id TEXT,
    city_id INTEGER,
    region_id INTEGER,
    order_index INTEGER,
    day_number INTEGER,
    visit_duration INTEGER,
    notes JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        a.id,
        a.name,
        a.description,
        a.type_id,
        a.city_id,
        a.region_id,
        tpa.order_index,
        tpa.day_number,
        tpa.visit_duration,
        tpa.notes
    FROM 
        tour_package_attractions tpa
        JOIN attractions a ON tpa.attraction_id = a.id
    WHERE 
        tpa.tour_package_id = p_tour_package_id
    ORDER BY
        tpa.day_number, tpa.order_index
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- 5. Create a function to get destinations in a tour package using the junction table
CREATE OR REPLACE FUNCTION get_tour_package_destinations(
    p_tour_package_id INTEGER,
    p_limit INTEGER DEFAULT 20
)
RETURNS TABLE (
    id INTEGER,
    name JSONB,
    description JSONB,
    type_id TEXT,
    parent_id INTEGER,
    order_index INTEGER,
    stay_duration INTEGER,
    notes JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        d.id,
        d.name,
        d.description,
        d.type_id,
        d.parent_id,
        tpd.order_index,
        tpd.stay_duration,
        tpd.notes
    FROM 
        tour_package_destinations tpd
        JOIN destinations d ON tpd.destination_id = d.id
    WHERE 
        tpd.tour_package_id = p_tour_package_id
    ORDER BY
        tpd.order_index
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- 6. Create a function to get destinations related to a tourism FAQ using the junction table
CREATE OR REPLACE FUNCTION get_tourism_faq_destinations(
    p_tourism_faq_id INTEGER,
    p_limit INTEGER DEFAULT 20
)
RETURNS TABLE (
    id INTEGER,
    name JSONB,
    description JSONB,
    type_id TEXT,
    parent_id INTEGER,
    relevance_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        d.id,
        d.name,
        d.description,
        d.type_id,
        d.parent_id,
        tfd.relevance_score
    FROM 
        tourism_faq_destinations tfd
        JOIN destinations d ON tfd.destination_id = d.id
    WHERE 
        tfd.tourism_faq_id = p_tourism_faq_id
    ORDER BY
        tfd.relevance_score DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Log the migration completion
DO $$
BEGIN
    RAISE NOTICE 'Database manager functions for junction tables updated successfully';
END $$;

COMMIT;
