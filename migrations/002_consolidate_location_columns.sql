-- Migration: 002_consolidate_location_columns.sql
-- Purpose: Consolidate redundant latitude/longitude columns into the geom column
-- as the single source of truth for spatial data.
-- This migration ensures all data is preserved before removing redundant columns.

-- Begin transaction
BEGIN;

-- 1. Migrate data from lat/lon columns to geom column where geom is NULL
-- Accommodations table
DO $$
BEGIN
    -- Check if geom column exists in accommodations table
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'accommodations'
        AND column_name = 'geom'
    ) THEN
        -- Add geom column if it doesn't exist
        ALTER TABLE accommodations ADD COLUMN geom geometry(Point, 4326);
    END IF;

    -- Update geom from lat/lon
    UPDATE accommodations
    SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
    WHERE (geom IS NULL OR ST_IsEmpty(geom)) AND latitude IS NOT NULL AND longitude IS NOT NULL;
END $$;

-- Attractions table
DO $$
BEGIN
    -- Check if geom column exists in attractions table
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'attractions'
        AND column_name = 'geom'
    ) THEN
        -- Add geom column if it doesn't exist
        ALTER TABLE attractions ADD COLUMN geom geometry(Point, 4326);
    END IF;

    -- Update geom from lat/lon
    UPDATE attractions
    SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
    WHERE (geom IS NULL OR ST_IsEmpty(geom)) AND latitude IS NOT NULL AND longitude IS NOT NULL;
END $$;

-- Cities table
DO $$
BEGIN
    -- Check if geom column exists in cities table
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'cities'
        AND column_name = 'geom'
    ) THEN
        -- Add geom column if it doesn't exist
        ALTER TABLE cities ADD COLUMN geom geometry(Point, 4326);
    END IF;

    -- Update geom from lat/lon
    UPDATE cities
    SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
    WHERE (geom IS NULL OR ST_IsEmpty(geom)) AND latitude IS NOT NULL AND longitude IS NOT NULL;
END $$;

-- Hotels table
DO $$
BEGIN
    -- Check if geom column exists in hotels table
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'hotels'
        AND column_name = 'geom'
    ) THEN
        -- Add geom column if it doesn't exist
        ALTER TABLE hotels ADD COLUMN geom geometry(Point, 4326);
    END IF;

    -- Update geom from lat/lon
    UPDATE hotels
    SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
    WHERE (geom IS NULL OR ST_IsEmpty(geom)) AND latitude IS NOT NULL AND longitude IS NOT NULL;
END $$;

-- Regions table
DO $$
BEGIN
    -- Check if geom column exists in regions table
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'regions'
        AND column_name = 'geom'
    ) THEN
        -- Add geom column if it doesn't exist
        ALTER TABLE regions ADD COLUMN geom geometry(Point, 4326);
    END IF;

    -- Update geom from lat/lon
    UPDATE regions
    SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
    WHERE (geom IS NULL OR ST_IsEmpty(geom)) AND latitude IS NOT NULL AND longitude IS NOT NULL;
END $$;

-- Restaurants table
DO $$
BEGIN
    -- Check if geom column exists in restaurants table
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'restaurants'
        AND column_name = 'geom'
    ) THEN
        -- Add geom column if it doesn't exist
        ALTER TABLE restaurants ADD COLUMN geom geometry(Point, 4326);
    END IF;

    -- Update geom from lat/lon
    UPDATE restaurants
    SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
    WHERE (geom IS NULL OR ST_IsEmpty(geom)) AND latitude IS NOT NULL AND longitude IS NOT NULL;
END $$;

-- Destinations table
DO $$
BEGIN
    -- Check if geom column exists in destinations table
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'destinations'
        AND column_name = 'geom'
    ) THEN
        -- Add geom column if it doesn't exist
        ALTER TABLE destinations ADD COLUMN geom geometry(Point, 4326);
    END IF;

    -- Update geom from lat/lon
    UPDATE destinations
    SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
    WHERE (geom IS NULL OR ST_IsEmpty(geom)) AND latitude IS NOT NULL AND longitude IS NOT NULL;
END $$;

-- Transportation stations table
DO $$
BEGIN
    -- Check if geom column exists in transportation_stations table
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'transportation_stations'
        AND column_name = 'geom'
    ) THEN
        -- Add geom column if it doesn't exist
        ALTER TABLE transportation_stations ADD COLUMN geom geometry(Point, 4326);
    END IF;

    -- Update geom from lat/lon
    UPDATE transportation_stations
    SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
    WHERE (geom IS NULL OR ST_IsEmpty(geom)) AND latitude IS NOT NULL AND longitude IS NOT NULL;
END $$;

-- 2. Verify data migration
CREATE TEMPORARY TABLE location_verification AS
SELECT 'accommodations' as table_name, COUNT(*) as missing_count
FROM accommodations
WHERE geom IS NULL AND (latitude IS NOT NULL AND longitude IS NOT NULL)
UNION ALL
SELECT 'attractions' as table_name, COUNT(*) as missing_count
FROM attractions
WHERE geom IS NULL AND (latitude IS NOT NULL AND longitude IS NOT NULL)
UNION ALL
SELECT 'cities' as table_name, COUNT(*) as missing_count
FROM cities
WHERE geom IS NULL AND (latitude IS NOT NULL AND longitude IS NOT NULL)
UNION ALL
SELECT 'hotels' as table_name, COUNT(*) as missing_count
FROM hotels
WHERE geom IS NULL AND (latitude IS NOT NULL AND longitude IS NOT NULL)
UNION ALL
SELECT 'regions' as table_name, COUNT(*) as missing_count
FROM regions
WHERE geom IS NULL AND (latitude IS NOT NULL AND longitude IS NOT NULL)
UNION ALL
SELECT 'restaurants' as table_name, COUNT(*) as missing_count
FROM restaurants
WHERE geom IS NULL AND (latitude IS NOT NULL AND longitude IS NOT NULL)
UNION ALL
SELECT 'destinations' as table_name, COUNT(*) as missing_count
FROM destinations
WHERE geom IS NULL AND (latitude IS NOT NULL AND longitude IS NOT NULL)
UNION ALL
SELECT 'transportation_stations' as table_name, COUNT(*) as missing_count
FROM transportation_stations
WHERE geom IS NULL AND (latitude IS NOT NULL AND longitude IS NOT NULL);

-- Check if any verification failed
DO $$
DECLARE
    total_missing bigint;
BEGIN
    SELECT SUM(missing_count) INTO total_missing FROM location_verification;

    IF total_missing > 0 THEN
        RAISE EXCEPTION 'Location migration verification failed: % records have inconsistencies', total_missing;
    END IF;
END $$;

-- 3. Create helper functions to extract lat/lon from geom
CREATE OR REPLACE FUNCTION get_latitude(geom geometry) RETURNS double precision AS $$
BEGIN
    RETURN ST_Y(geom);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE FUNCTION get_longitude(geom geometry) RETURNS double precision AS $$
BEGIN
    RETURN ST_X(geom);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 4. Drop redundant columns (only after verification passes)
-- Accommodations table
ALTER TABLE accommodations DROP COLUMN IF EXISTS latitude;
ALTER TABLE accommodations DROP COLUMN IF EXISTS longitude;

-- Attractions table
ALTER TABLE attractions DROP COLUMN IF EXISTS latitude;
ALTER TABLE attractions DROP COLUMN IF EXISTS longitude;

-- Cities table
ALTER TABLE cities DROP COLUMN IF EXISTS latitude;
ALTER TABLE cities DROP COLUMN IF EXISTS longitude;

-- Hotels table
ALTER TABLE hotels DROP COLUMN IF EXISTS latitude;
ALTER TABLE hotels DROP COLUMN IF EXISTS longitude;

-- Regions table
ALTER TABLE regions DROP COLUMN IF EXISTS latitude;
ALTER TABLE regions DROP COLUMN IF EXISTS longitude;

-- Restaurants table
ALTER TABLE restaurants DROP COLUMN IF EXISTS latitude;
ALTER TABLE restaurants DROP COLUMN IF EXISTS longitude;

-- Destinations table
ALTER TABLE destinations DROP COLUMN IF EXISTS latitude;
ALTER TABLE destinations DROP COLUMN IF EXISTS longitude;

-- Transportation stations table
ALTER TABLE transportation_stations DROP COLUMN IF EXISTS latitude;
ALTER TABLE transportation_stations DROP COLUMN IF EXISTS longitude;

-- 5. Add comments to tables explaining how to get lat/lon from geom
COMMENT ON COLUMN accommodations.geom IS 'PostGIS geometry column. Use ST_X(geom) for longitude and ST_Y(geom) for latitude.';
COMMENT ON COLUMN attractions.geom IS 'PostGIS geometry column. Use ST_X(geom) for longitude and ST_Y(geom) for latitude.';
COMMENT ON COLUMN cities.geom IS 'PostGIS geometry column. Use ST_X(geom) for longitude and ST_Y(geom) for latitude.';
COMMENT ON COLUMN hotels.geom IS 'PostGIS geometry column. Use ST_X(geom) for longitude and ST_Y(geom) for latitude.';
COMMENT ON COLUMN regions.geom IS 'PostGIS geometry column. Use ST_X(geom) for longitude and ST_Y(geom) for latitude.';
COMMENT ON COLUMN restaurants.geom IS 'PostGIS geometry column. Use ST_X(geom) for longitude and ST_Y(geom) for latitude.';
COMMENT ON COLUMN destinations.geom IS 'PostGIS geometry column. Use ST_X(geom) for longitude and ST_Y(geom) for latitude.';
COMMENT ON COLUMN transportation_stations.geom IS 'PostGIS geometry column. Use ST_X(geom) for longitude and ST_Y(geom) for latitude.';

-- Clean up temporary objects
DROP TABLE location_verification;

-- Commit transaction
COMMIT;
