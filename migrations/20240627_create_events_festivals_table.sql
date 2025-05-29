-- Migration: Create Events and Festivals Table
-- Date: 2024-06-27
-- Description: Create a table for events and festivals in Egypt

-- 1. Create event_categories table
CREATE TABLE IF NOT EXISTS event_categories (
    id TEXT PRIMARY KEY,
    name JSONB NOT NULL,
    description JSONB,
    icon TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Populate event_categories table with initial data
INSERT INTO event_categories (id, name, description, icon)
VALUES
    ('cultural_festivals', 
     '{"en": "Cultural Festivals", "ar": "المهرجانات الثقافية"}',
     '{"en": "Celebrations of Egyptian culture, arts, and heritage", "ar": "احتفالات بالثقافة والفنون والتراث المصري"}',
     'masks-theater'),
    ('religious_festivals', 
     '{"en": "Religious Festivals", "ar": "المهرجانات الدينية"}',
     '{"en": "Islamic, Coptic, and other religious celebrations", "ar": "الاحتفالات الإسلامية والقبطية وغيرها من الاحتفالات الدينية"}',
     'place-of-worship'),
    ('music_festivals', 
     '{"en": "Music Festivals", "ar": "مهرجانات الموسيقى"}',
     '{"en": "Concerts and music events featuring Egyptian and international artists", "ar": "الحفلات والفعاليات الموسيقية التي تضم فنانين مصريين ودوليين"}',
     'music'),
    ('film_festivals', 
     '{"en": "Film Festivals", "ar": "مهرجانات الأفلام"}',
     '{"en": "Celebrations of Egyptian and international cinema", "ar": "احتفالات بالسينما المصرية والدولية"}',
     'film'),
    ('food_festivals', 
     '{"en": "Food Festivals", "ar": "مهرجانات الطعام"}',
     '{"en": "Events celebrating Egyptian cuisine and culinary traditions", "ar": "فعاليات تحتفي بالمطبخ المصري والتقاليد الطهوية"}',
     'utensils'),
    ('sports_events', 
     '{"en": "Sports Events", "ar": "الفعاليات الرياضية"}',
     '{"en": "Major sporting competitions and tournaments", "ar": "المسابقات والبطولات الرياضية الكبرى"}',
     'trophy'),
    ('historical_commemorations', 
     '{"en": "Historical Commemorations", "ar": "الاحتفالات التاريخية"}',
     '{"en": "Events marking significant historical dates and achievements", "ar": "فعاليات تحيي ذكرى تواريخ وإنجازات تاريخية مهمة"}',
     'monument'),
    ('seasonal_celebrations', 
     '{"en": "Seasonal Celebrations", "ar": "الاحتفالات الموسمية"}',
     '{"en": "Events tied to seasons, harvests, and natural phenomena", "ar": "فعاليات مرتبطة بالمواسم والحصاد والظواهر الطبيعية"}',
     'sun'),
    ('art_exhibitions', 
     '{"en": "Art Exhibitions", "ar": "المعارض الفنية"}',
     '{"en": "Displays of Egyptian and international visual arts", "ar": "عروض للفنون البصرية المصرية والدولية"}',
     'palette')
ON CONFLICT (id) DO NOTHING;

-- 3. Create events_festivals table
CREATE TABLE IF NOT EXISTS events_festivals (
    id SERIAL PRIMARY KEY,
    category_id TEXT NOT NULL REFERENCES event_categories(id) ON DELETE CASCADE,
    name JSONB NOT NULL,
    description JSONB NOT NULL,
    start_date DATE,
    end_date DATE,
    is_annual BOOLEAN DEFAULT TRUE,
    annual_month INTEGER,  -- 1-12 for January-December
    annual_day INTEGER,    -- 1-31 for day of month
    lunar_calendar BOOLEAN DEFAULT FALSE,  -- Whether dates follow lunar calendar
    location_description JSONB,
    destination_id TEXT,
    venue JSONB,
    organizer JSONB,
    admission JSONB,
    schedule JSONB,
    highlights JSONB,
    historical_significance JSONB,
    tips JSONB,
    images JSONB,
    website TEXT,
    contact_info JSONB,
    tags TEXT[],
    is_featured BOOLEAN DEFAULT FALSE,
    view_count INTEGER DEFAULT 0,
    data JSONB DEFAULT '{}'::jsonb,
    embedding VECTOR(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_id TEXT
);

-- 4. Create indexes for events_festivals table
CREATE INDEX IF NOT EXISTS idx_events_festivals_category_id ON events_festivals (category_id);
CREATE INDEX IF NOT EXISTS idx_events_festivals_name_gin ON events_festivals USING GIN (name);
CREATE INDEX IF NOT EXISTS idx_events_festivals_description_gin ON events_festivals USING GIN (description);
CREATE INDEX IF NOT EXISTS idx_events_festivals_start_date ON events_festivals (start_date);
CREATE INDEX IF NOT EXISTS idx_events_festivals_end_date ON events_festivals (end_date);
CREATE INDEX IF NOT EXISTS idx_events_festivals_is_annual ON events_festivals (is_annual);
CREATE INDEX IF NOT EXISTS idx_events_festivals_annual_month ON events_festivals (annual_month);
CREATE INDEX IF NOT EXISTS idx_events_festivals_destination_id ON events_festivals (destination_id);
CREATE INDEX IF NOT EXISTS idx_events_festivals_tags ON events_festivals USING GIN (tags array_ops);
CREATE INDEX IF NOT EXISTS idx_events_festivals_is_featured ON events_festivals (is_featured);
CREATE INDEX IF NOT EXISTS idx_events_festivals_embedding_hnsw ON events_festivals USING hnsw (embedding vector_cosine_ops) WITH (m='16', ef_construction='64');

-- 5. Create function to search events and festivals by text
CREATE OR REPLACE FUNCTION search_events_festivals(
    p_query TEXT,
    p_category_id TEXT DEFAULT NULL,
    p_destination_id TEXT DEFAULT NULL,
    p_start_date DATE DEFAULT NULL,
    p_end_date DATE DEFAULT NULL,
    p_is_annual BOOLEAN DEFAULT NULL,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    id INTEGER,
    category_id TEXT,
    category_name JSONB,
    name JSONB,
    description JSONB,
    start_date DATE,
    end_date DATE,
    is_annual BOOLEAN,
    destination_id TEXT,
    venue JSONB,
    tags TEXT[],
    is_featured BOOLEAN
) AS $$
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
$$ LANGUAGE plpgsql;

-- 6. Create function to get events and festivals by category
CREATE OR REPLACE FUNCTION get_events_festivals_by_category(
    p_category_id TEXT,
    p_limit INTEGER DEFAULT 20
)
RETURNS TABLE (
    id INTEGER,
    name JSONB,
    description JSONB,
    start_date DATE,
    end_date DATE,
    is_annual BOOLEAN,
    destination_id TEXT,
    venue JSONB,
    is_featured BOOLEAN
) AS $$
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
$$ LANGUAGE plpgsql;

-- 7. Create function to get events and festivals by destination
CREATE OR REPLACE FUNCTION get_events_festivals_by_destination(
    p_destination_id TEXT,
    p_limit INTEGER DEFAULT 20
)
RETURNS TABLE (
    id INTEGER,
    category_id TEXT,
    category_name JSONB,
    name JSONB,
    description JSONB,
    start_date DATE,
    end_date DATE,
    is_annual BOOLEAN,
    venue JSONB,
    is_featured BOOLEAN
) AS $$
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
$$ LANGUAGE plpgsql;

-- 8. Create function to get upcoming events and festivals
CREATE OR REPLACE FUNCTION get_upcoming_events_festivals(
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    id INTEGER,
    category_id TEXT,
    category_name JSONB,
    name JSONB,
    description JSONB,
    start_date DATE,
    end_date DATE,
    destination_id TEXT,
    venue JSONB,
    is_featured BOOLEAN
) AS $$
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
$$ LANGUAGE plpgsql;

-- 9. Create function to get featured events and festivals
CREATE OR REPLACE FUNCTION get_featured_events_festivals(
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    id INTEGER,
    category_id TEXT,
    category_name JSONB,
    name JSONB,
    description JSONB,
    start_date DATE,
    end_date DATE,
    destination_id TEXT,
    venue JSONB,
    is_annual BOOLEAN
) AS $$
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
$$ LANGUAGE plpgsql;
