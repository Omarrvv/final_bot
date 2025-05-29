-- Migration: Fix Tourism FAQ Destinations
-- Date: 2025-07-15
-- Purpose: Fix the migration of tourism_faqs.related_destination_ids to tourism_faq_destinations

BEGIN;

-- Log the migration start
DO $$
BEGIN
    RAISE NOTICE 'Starting fix for tourism_faq_destinations migration';
END $$;

-- Manually migrate data from tourism_faqs.related_destination_ids to tourism_faq_destinations
DO $$
DECLARE
    faq_record RECORD;
    destination_id INTEGER;
    destination_id_text TEXT;
BEGIN
    -- For each FAQ with related_destination_ids
    FOR faq_record IN
        SELECT id, related_destination_ids
        FROM tourism_faqs
        WHERE array_length(related_destination_ids, 1) > 0
    LOOP
        -- For each destination ID in the array
        FOREACH destination_id_text IN ARRAY faq_record.related_destination_ids
        LOOP
            -- Find the corresponding destination ID
            SELECT id INTO destination_id
            FROM destinations
            WHERE name->>'en' ILIKE '%' || destination_id_text || '%'
            LIMIT 1;

            IF destination_id IS NOT NULL THEN
                -- Insert into junction table
                INSERT INTO tourism_faq_destinations
                    (tourism_faq_id, destination_id, relevance_score, created_at, updated_at)
                VALUES
                    (faq_record.id, destination_id, 1.0, NOW(), NOW());

                RAISE NOTICE 'Inserted FAQ % destination %', faq_record.id, destination_id;

                RAISE NOTICE 'Migrated FAQ % destination % to destination ID %',
                    faq_record.id, destination_id_text, destination_id;
            ELSE
                RAISE NOTICE 'Could not find destination ID for %', destination_id_text;
            END IF;
        END LOOP;
    END LOOP;
END $$;

-- Log the migration completion
DO $$
BEGIN
    RAISE NOTICE 'Fix for tourism_faq_destinations migration completed';
END $$;

COMMIT;
