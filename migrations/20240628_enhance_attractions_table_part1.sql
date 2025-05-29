-- Migration: Enhance Attractions Table (Part 1)
-- Date: 2024-06-28
-- Description: Create attraction subcategories table

-- 1. Create attraction_subcategories table if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'attraction_subcategories') THEN
        CREATE TABLE attraction_subcategories (
            id TEXT PRIMARY KEY,
            parent_type TEXT NOT NULL,
            name JSONB NOT NULL,
            description JSONB,
            icon TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

        -- Add foreign key constraint
        ALTER TABLE attraction_subcategories
        ADD CONSTRAINT fk_attraction_subcategories_parent_type
        FOREIGN KEY (parent_type) REFERENCES attraction_types(type) ON DELETE CASCADE;
    END IF;
END
$$;

-- 3. Populate attraction_subcategories table with initial data for historical attractions
INSERT INTO attraction_subcategories (id, parent_type, name, description, icon)
VALUES
    -- Historical subcategories
    ('ancient_egyptian_temple', 'historical',
     '{"en": "Ancient Egyptian Temple", "ar": "معبد مصري قديم"}',
     '{"en": "Temples built during ancient Egyptian dynasties", "ar": "معابد بنيت خلال عصور الأسرات المصرية القديمة"}',
     'landmark'),
    ('ancient_egyptian_tomb', 'historical',
     '{"en": "Ancient Egyptian Tomb", "ar": "مقبرة مصرية قديمة"}',
     '{"en": "Tombs and burial sites from ancient Egypt", "ar": "مقابر ومواقع دفن من مصر القديمة"}',
     'monument'),
    ('pyramid', 'historical',
     '{"en": "Pyramid", "ar": "هرم"}',
     '{"en": "Pyramid structures built as tombs for pharaohs", "ar": "هياكل هرمية بنيت كمقابر للفراعنة"}',
     'triangle'),
    ('greco_roman_site', 'historical',
     '{"en": "Greco-Roman Site", "ar": "موقع يوناني روماني"}',
     '{"en": "Sites from the Greco-Roman period in Egypt", "ar": "مواقع من الفترة اليونانية الرومانية في مصر"}',
     'columns'),
    ('islamic_monument', 'historical',
     '{"en": "Islamic Monument", "ar": "أثر إسلامي"}',
     '{"en": "Monuments from the Islamic period in Egypt", "ar": "آثار من الفترة الإسلامية في مصر"}',
     'mosque'),
    ('coptic_site', 'historical',
     '{"en": "Coptic Site", "ar": "موقع قبطي"}',
     '{"en": "Sites from the Coptic Christian period in Egypt", "ar": "مواقع من الفترة المسيحية القبطية في مصر"}',
     'church'),
    ('modern_historical_site', 'historical',
     '{"en": "Modern Historical Site", "ar": "موقع تاريخي حديث"}',
     '{"en": "Historical sites from the 19th and 20th centuries", "ar": "مواقع تاريخية من القرنين التاسع عشر والعشرين"}',
     'building')
ON CONFLICT (id) DO NOTHING;
