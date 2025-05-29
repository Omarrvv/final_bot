-- Migration to improve polymorphic associations
-- This script adds comments, indexes, and check constraints to polymorphic association tables

-- Add comments to explain polymorphic associations
COMMENT ON COLUMN favorites.target_id IS 'ID of the target entity (attraction, restaurant, etc.)';
COMMENT ON COLUMN favorites.target_type IS 'Type of the target entity (attraction, restaurant, etc.)';

COMMENT ON COLUMN media.target_id IS 'ID of the target entity (attraction, restaurant, etc.)';
COMMENT ON COLUMN media.target_type IS 'Type of the target entity (attraction, restaurant, etc.)';

COMMENT ON COLUMN reviews.target_id IS 'ID of the target entity (attraction, restaurant, etc.)';
COMMENT ON COLUMN reviews.target_type IS 'Type of the target entity (attraction, restaurant, etc.)';

-- Create indexes on (target_type, target_id) for better query performance
CREATE INDEX IF NOT EXISTS idx_favorites_target ON favorites(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_media_target ON media(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_reviews_target ON reviews(target_type, target_id);

-- Add check constraints to validate target_type values
ALTER TABLE favorites 
ADD CONSTRAINT chk_favorites_target_type 
CHECK (target_type IN ('attraction', 'restaurant', 'accommodation', 'city', 'region', 'event', 'tour_package'));

ALTER TABLE media 
ADD CONSTRAINT chk_media_target_type 
CHECK (target_type IN ('attraction', 'restaurant', 'accommodation', 'city', 'region', 'event', 'tour_package'));

ALTER TABLE reviews 
ADD CONSTRAINT chk_reviews_target_type 
CHECK (target_type IN ('attraction', 'restaurant', 'accommodation', 'city', 'region', 'event', 'tour_package'));
