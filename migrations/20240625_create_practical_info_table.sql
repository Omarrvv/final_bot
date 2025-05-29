-- Migration: Create Practical Info Table
-- Date: 2024-06-25
-- Description: Create a table for practical information about Egyptian tourism

-- 1. Create practical_info_categories table
CREATE TABLE IF NOT EXISTS practical_info_categories (
    id TEXT PRIMARY KEY,
    name JSONB NOT NULL,
    description JSONB,
    icon TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Populate practical_info_categories table with initial data
INSERT INTO practical_info_categories (id, name, description, icon)
VALUES
    ('emergency_contacts', 
     '{"en": "Emergency Contacts", "ar": "أرقام الطوارئ"}',
     '{"en": "Important emergency contact numbers and services in Egypt", "ar": "أرقام وخدمات الطوارئ المهمة في مصر"}',
     'phone-volume'),
    ('embassies_consulates', 
     '{"en": "Embassies & Consulates", "ar": "السفارات والقنصليات"}',
     '{"en": "Information about foreign embassies and consulates in Egypt", "ar": "معلومات عن السفارات والقنصليات الأجنبية في مصر"}',
     'flag'),
    ('public_holidays', 
     '{"en": "Public Holidays", "ar": "العطلات الرسمية"}',
     '{"en": "Information about Egyptian public holidays and observances", "ar": "معلومات عن العطلات الرسمية والمناسبات المصرية"}',
     'calendar'),
    ('business_hours', 
     '{"en": "Business Hours", "ar": "ساعات العمل"}',
     '{"en": "Typical business hours for shops, banks, and government offices", "ar": "ساعات العمل النموذجية للمتاجر والبنوك والمكاتب الحكومية"}',
     'clock'),
    ('tipping_customs', 
     '{"en": "Tipping Customs", "ar": "عادات البقشيش"}',
     '{"en": "Information about tipping practices and expectations in Egypt", "ar": "معلومات عن ممارسات وتوقعات البقشيش في مصر"}',
     'hand-holding-dollar'),
    ('electricity_plugs', 
     '{"en": "Electricity & Plugs", "ar": "الكهرباء والمقابس"}',
     '{"en": "Information about electrical voltage, frequency, and plug types in Egypt", "ar": "معلومات عن الجهد الكهربائي والتردد وأنواع المقابس في مصر"}',
     'plug'),
    ('internet_connectivity', 
     '{"en": "Internet & Connectivity", "ar": "الإنترنت والاتصال"}',
     '{"en": "Information about internet access, SIM cards, and connectivity in Egypt", "ar": "معلومات عن الوصول إلى الإنترنت وبطاقات SIM والاتصال في مصر"}',
     'wifi'),
    ('drinking_water', 
     '{"en": "Drinking Water", "ar": "مياه الشرب"}',
     '{"en": "Information about water safety and access to drinking water", "ar": "معلومات عن سلامة المياه والوصول إلى مياه الشرب"}',
     'glass-water'),
    ('photography_rules', 
     '{"en": "Photography Rules", "ar": "قواعد التصوير"}',
     '{"en": "Information about photography permissions and restrictions in Egypt", "ar": "معلومات عن أذونات وقيود التصوير في مصر"}',
     'camera')
ON CONFLICT (id) DO NOTHING;

-- 3. Create practical_info table
CREATE TABLE IF NOT EXISTS practical_info (
    id SERIAL PRIMARY KEY,
    category_id TEXT NOT NULL REFERENCES practical_info_categories(id) ON DELETE CASCADE,
    title JSONB NOT NULL,
    content JSONB NOT NULL,
    related_destination_ids TEXT[],
    tags TEXT[],
    is_featured BOOLEAN DEFAULT FALSE,
    view_count INTEGER DEFAULT 0,
    helpful_count INTEGER DEFAULT 0,
    not_helpful_count INTEGER DEFAULT 0,
    data JSONB DEFAULT '{}'::jsonb,
    embedding VECTOR(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_id TEXT
);

-- 4. Create indexes for practical_info table
CREATE INDEX IF NOT EXISTS idx_practical_info_category_id ON practical_info (category_id);
CREATE INDEX IF NOT EXISTS idx_practical_info_title_gin ON practical_info USING GIN (title);
CREATE INDEX IF NOT EXISTS idx_practical_info_content_gin ON practical_info USING GIN (content);
CREATE INDEX IF NOT EXISTS idx_practical_info_tags ON practical_info USING GIN (tags array_ops);
CREATE INDEX IF NOT EXISTS idx_practical_info_related_destination_ids ON practical_info USING GIN (related_destination_ids array_ops);
CREATE INDEX IF NOT EXISTS idx_practical_info_is_featured ON practical_info (is_featured);
CREATE INDEX IF NOT EXISTS idx_practical_info_embedding_hnsw ON practical_info USING hnsw (embedding vector_cosine_ops) WITH (m='16', ef_construction='64');

-- 5. Create function to search practical info by text
CREATE OR REPLACE FUNCTION search_practical_info(
    p_query TEXT,
    p_category_id TEXT DEFAULT NULL,
    p_destination_id TEXT DEFAULT NULL,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    id INTEGER,
    category_id TEXT,
    category_name JSONB,
    title JSONB,
    content JSONB,
    tags TEXT[],
    is_featured BOOLEAN
) AS $$
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
$$ LANGUAGE plpgsql;

-- 6. Create function to get practical info by category
CREATE OR REPLACE FUNCTION get_practical_info_by_category(
    p_category_id TEXT,
    p_limit INTEGER DEFAULT 20
)
RETURNS TABLE (
    id INTEGER,
    title JSONB,
    content JSONB,
    tags TEXT[],
    is_featured BOOLEAN
) AS $$
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
$$ LANGUAGE plpgsql;

-- 7. Create function to get practical info by destination
CREATE OR REPLACE FUNCTION get_practical_info_by_destination(
    p_destination_id TEXT,
    p_limit INTEGER DEFAULT 20
)
RETURNS TABLE (
    id INTEGER,
    category_id TEXT,
    category_name JSONB,
    title JSONB,
    content JSONB,
    is_featured BOOLEAN
) AS $$
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
$$ LANGUAGE plpgsql;

-- 8. Create function to get featured practical info
CREATE OR REPLACE FUNCTION get_featured_practical_info(
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    id INTEGER,
    category_id TEXT,
    category_name JSONB,
    title JSONB,
    content JSONB,
    tags TEXT[]
) AS $$
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
$$ LANGUAGE plpgsql;
