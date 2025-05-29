-- Migration: Enhance Attractions Table
-- Date: 2024-06-28
-- Description: Add subcategories, visiting information, accessibility information, related attractions, and historical context to the attractions table

-- 1. Create attraction_subcategories table
CREATE TABLE IF NOT EXISTS attraction_subcategories (
    id TEXT PRIMARY KEY,
    parent_type TEXT NOT NULL REFERENCES attraction_types(type) ON DELETE CASCADE,
    name JSONB NOT NULL,
    description JSONB,
    icon TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Populate attraction_subcategories table with initial data
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
     'building'),
    
    -- Museum subcategories
    ('archaeological_museum', 'museum', 
     '{"en": "Archaeological Museum", "ar": "متحف أثري"}',
     '{"en": "Museums focusing on archaeological artifacts", "ar": "متاحف تركز على القطع الأثرية"}',
     'vase'),
    ('art_museum', 'museum', 
     '{"en": "Art Museum", "ar": "متحف فني"}',
     '{"en": "Museums focusing on art collections", "ar": "متاحف تركز على مجموعات فنية"}',
     'palette'),
    ('historical_museum', 'museum', 
     '{"en": "Historical Museum", "ar": "متحف تاريخي"}',
     '{"en": "Museums focusing on historical periods and events", "ar": "متاحف تركز على الفترات والأحداث التاريخية"}',
     'book-open'),
    ('specialized_museum', 'museum', 
     '{"en": "Specialized Museum", "ar": "متحف متخصص"}',
     '{"en": "Museums focusing on specific themes or subjects", "ar": "متاحف تركز على مواضيع أو موضوعات محددة"}',
     'microscope'),
    
    -- Natural subcategories
    ('desert', 'natural', 
     '{"en": "Desert", "ar": "صحراء"}',
     '{"en": "Desert landscapes and formations", "ar": "المناظر الطبيعية والتكوينات الصحراوية"}',
     'mountain'),
    ('oasis', 'natural', 
     '{"en": "Oasis", "ar": "واحة"}',
     '{"en": "Natural oases in desert regions", "ar": "واحات طبيعية في المناطق الصحراوية"}',
     'water'),
    ('river', 'natural', 
     '{"en": "River", "ar": "نهر"}',
     '{"en": "Rivers and waterways", "ar": "الأنهار والممرات المائية"}',
     'water'),
    ('beach', 'natural', 
     '{"en": "Beach", "ar": "شاطئ"}',
     '{"en": "Beaches along the Mediterranean and Red Sea", "ar": "شواطئ على البحر المتوسط والبحر الأحمر"}',
     'umbrella-beach'),
    ('mountain', 'natural', 
     '{"en": "Mountain", "ar": "جبل"}',
     '{"en": "Mountain ranges and peaks", "ar": "سلاسل جبلية وقمم"}',
     'mountain'),
    ('wildlife_area', 'natural', 
     '{"en": "Wildlife Area", "ar": "منطقة حياة برية"}',
     '{"en": "Areas known for wildlife and biodiversity", "ar": "مناطق معروفة بالحياة البرية والتنوع البيولوجي"}',
     'paw'),
    
    -- Cultural subcategories
    ('traditional_market', 'cultural', 
     '{"en": "Traditional Market", "ar": "سوق تقليدي"}',
     '{"en": "Traditional markets and bazaars", "ar": "الأسواق التقليدية والبازارات"}',
     'store'),
    ('cultural_center', 'cultural', 
     '{"en": "Cultural Center", "ar": "مركز ثقافي"}',
     '{"en": "Centers showcasing Egyptian culture and arts", "ar": "مراكز تعرض الثقافة والفنون المصرية"}',
     'palette'),
    ('traditional_craft', 'cultural', 
     '{"en": "Traditional Craft", "ar": "حرفة تقليدية"}',
     '{"en": "Locations showcasing traditional Egyptian crafts", "ar": "مواقع تعرض الحرف التقليدية المصرية"}',
     'hands'),
    ('performing_arts_venue', 'cultural', 
     '{"en": "Performing Arts Venue", "ar": "مكان فنون الأداء"}',
     '{"en": "Venues for music, dance, and theatrical performances", "ar": "أماكن للموسيقى والرقص والعروض المسرحية"}',
     'masks-theater'),
    
    -- Religious subcategories
    ('mosque', 'religious', 
     '{"en": "Mosque", "ar": "مسجد"}',
     '{"en": "Islamic places of worship", "ar": "أماكن العبادة الإسلامية"}',
     'mosque'),
    ('church', 'religious', 
     '{"en": "Church", "ar": "كنيسة"}',
     '{"en": "Christian places of worship", "ar": "أماكن العبادة المسيحية"}',
     'church'),
    ('monastery', 'religious', 
     '{"en": "Monastery", "ar": "دير"}',
     '{"en": "Christian monastic communities", "ar": "مجتمعات الرهبان المسيحية"}',
     'place-of-worship'),
    ('synagogue', 'religious', 
     '{"en": "Synagogue", "ar": "معبد يهودي"}',
     '{"en": "Jewish places of worship", "ar": "أماكن العبادة اليهودية"}',
     'star-of-david'),
    ('religious_site', 'religious', 
     '{"en": "Religious Site", "ar": "موقع ديني"}',
     '{"en": "Sites of religious significance", "ar": "مواقع ذات أهمية دينية"}',
     'place-of-worship'),
    
    -- Entertainment subcategories
    ('theme_park', 'entertainment', 
     '{"en": "Theme Park", "ar": "مدينة ملاهي"}',
     '{"en": "Amusement and theme parks", "ar": "حدائق الملاهي والترفيه"}',
     'ferris-wheel'),
    ('water_park', 'entertainment', 
     '{"en": "Water Park", "ar": "حديقة مائية"}',
     '{"en": "Water-based amusement parks", "ar": "حدائق الملاهي المائية"}',
     'water'),
    ('zoo', 'entertainment', 
     '{"en": "Zoo", "ar": "حديقة حيوان"}',
     '{"en": "Zoological gardens", "ar": "حدائق الحيوان"}',
     'paw'),
    ('aquarium', 'entertainment', 
     '{"en": "Aquarium", "ar": "حوض أسماك"}',
     '{"en": "Facilities housing aquatic life", "ar": "مرافق تضم الحياة المائية"}',
     'fish'),
    ('theater', 'entertainment', 
     '{"en": "Theater", "ar": "مسرح"}',
     '{"en": "Venues for theatrical performances", "ar": "أماكن للعروض المسرحية"}',
     'masks-theater'),
    ('cinema', 'entertainment', 
     '{"en": "Cinema", "ar": "سينما"}',
     '{"en": "Movie theaters", "ar": "دور السينما"}',
     'film')
ON CONFLICT (id) DO NOTHING;

-- 3. Add subcategory_id column to attractions table
ALTER TABLE attractions ADD COLUMN IF NOT EXISTS subcategory_id TEXT REFERENCES attraction_subcategories(id);
CREATE INDEX IF NOT EXISTS idx_attractions_subcategory_id ON attractions(subcategory_id);

-- 4. Add visiting_info column to attractions table
ALTER TABLE attractions ADD COLUMN IF NOT EXISTS visiting_info JSONB DEFAULT '{}'::jsonb;
CREATE INDEX IF NOT EXISTS idx_attractions_visiting_info_gin ON attractions USING GIN (visiting_info);

-- 5. Add accessibility_info column to attractions table
ALTER TABLE attractions ADD COLUMN IF NOT EXISTS accessibility_info JSONB DEFAULT '{}'::jsonb;
CREATE INDEX IF NOT EXISTS idx_attractions_accessibility_info_gin ON attractions USING GIN (accessibility_info);

-- 6. Add related_attractions column to attractions table
ALTER TABLE attractions ADD COLUMN IF NOT EXISTS related_attractions TEXT[] DEFAULT '{}'::text[];
CREATE INDEX IF NOT EXISTS idx_attractions_related_attractions ON attractions USING GIN (related_attractions array_ops);

-- 7. Add historical_context column to attractions table
ALTER TABLE attractions ADD COLUMN IF NOT EXISTS historical_context JSONB DEFAULT '{}'::jsonb;
CREATE INDEX IF NOT EXISTS idx_attractions_historical_context_gin ON attractions USING GIN (historical_context);

-- 8. Create function to find related attractions
CREATE OR REPLACE FUNCTION find_related_attractions(
    p_attraction_id TEXT,
    p_limit INTEGER DEFAULT 5
)
RETURNS TABLE (
    id TEXT,
    name JSONB,
    type TEXT,
    subcategory_id TEXT,
    city_id TEXT,
    region_id TEXT
) AS $$
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
$$ LANGUAGE plpgsql;
