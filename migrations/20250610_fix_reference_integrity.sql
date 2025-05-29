-- Migration: Fix Reference Integrity Issues
-- Date: 2025-06-10
-- Description: This migration fixes reference integrity issues in the attractions table
-- by updating the city and region text fields to match the city_id and region_id values.

-- Step 1: Update city field to match city_id
UPDATE attractions
SET city = city_id
WHERE city IS NOT NULL 
  AND city_id IS NOT NULL 
  AND city != city_id;

-- Step 2: Update region field to match region_id
UPDATE attractions
SET region = region_id
WHERE region IS NOT NULL 
  AND region_id IS NOT NULL 
  AND region != region_id;

-- Step 3: Verify the changes
-- This will return 0 rows if all mismatches are fixed
-- SELECT COUNT(*) as remaining_mismatches
-- FROM attractions
-- WHERE (city IS NOT NULL AND city_id IS NOT NULL AND city != city_id)
--    OR (region IS NOT NULL AND region_id IS NOT NULL AND region != region_id);
