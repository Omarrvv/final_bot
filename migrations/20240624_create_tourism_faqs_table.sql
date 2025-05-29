-- Migration: Create Tourism FAQs Table
-- Date: 2024-06-24
-- Description: Create a table for frequently asked questions about Egyptian tourism

-- 1. Create faq_categories table
CREATE TABLE IF NOT EXISTS faq_categories (
    id TEXT PRIMARY KEY,
    name JSONB NOT NULL,
    description JSONB,
    icon TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Populate faq_categories table with initial data
INSERT INTO faq_categories (id, name, description, icon)
VALUES
    ('visa_immigration', 
     '{"en": "Visa & Immigration", "ar": "التأشيرة والهجرة"}',
     '{"en": "Information about visa requirements, application process, and immigration procedures", "ar": "معلومات حول متطلبات التأشيرة وعملية التقديم وإجراءات الهجرة"}',
     'passport'),
    ('health_safety', 
     '{"en": "Health & Safety", "ar": "الصحة والسلامة"}',
     '{"en": "Information about health precautions, safety tips, and emergency services", "ar": "معلومات حول الاحتياطات الصحية ونصائح السلامة وخدمات الطوارئ"}',
     'first-aid'),
    ('money_currency', 
     '{"en": "Money & Currency", "ar": "المال والعملة"}',
     '{"en": "Information about Egyptian currency, exchange rates, banking, and payment methods", "ar": "معلومات حول العملة المصرية وأسعار الصرف والخدمات المصرفية وطرق الدفع"}',
     'money'),
    ('customs_etiquette', 
     '{"en": "Customs & Etiquette", "ar": "العادات وآداب السلوك"}',
     '{"en": "Information about local customs, cultural norms, and appropriate behavior", "ar": "معلومات حول العادات المحلية والمعايير الثقافية والسلوك المناسب"}',
     'handshake'),
    ('transportation', 
     '{"en": "Transportation", "ar": "المواصلات"}',
     '{"en": "Information about getting around in Egypt, public transportation, and driving", "ar": "معلومات حول التنقل في مصر ووسائل النقل العام والقيادة"}',
     'bus'),
    ('accommodation', 
     '{"en": "Accommodation", "ar": "الإقامة"}',
     '{"en": "Information about hotels, hostels, and other accommodation options", "ar": "معلومات حول الفنادق والنزل وخيارات الإقامة الأخرى"}',
     'hotel'),
    ('food_drink', 
     '{"en": "Food & Drink", "ar": "الطعام والشراب"}',
     '{"en": "Information about Egyptian cuisine, dining etiquette, and food safety", "ar": "معلومات حول المطبخ المصري وآداب تناول الطعام وسلامة الغذاء"}',
     'utensils'),
    ('shopping_souvenirs', 
     '{"en": "Shopping & Souvenirs", "ar": "التسوق والهدايا التذكارية"}',
     '{"en": "Information about markets, bargaining, and popular souvenirs", "ar": "معلومات حول الأسواق والمساومة والهدايا التذكارية الشعبية"}',
     'shopping-bag'),
    ('religion_culture', 
     '{"en": "Religion & Culture", "ar": "الدين والثقافة"}',
     '{"en": "Information about religious sites, cultural practices, and festivals", "ar": "معلومات حول المواقع الدينية والممارسات الثقافية والمهرجانات"}',
     'mosque'),
    ('weather_climate', 
     '{"en": "Weather & Climate", "ar": "الطقس والمناخ"}',
     '{"en": "Information about seasonal weather patterns and what to pack", "ar": "معلومات حول أنماط الطقس الموسمية وما يجب إحضاره"}',
     'sun'),
    ('communication', 
     '{"en": "Communication", "ar": "الاتصالات"}',
     '{"en": "Information about language, internet access, and phone services", "ar": "معلومات حول اللغة والوصول إلى الإنترنت وخدمات الهاتف"}',
     'phone')
ON CONFLICT (id) DO NOTHING;

-- 3. Create tourism_faqs table
CREATE TABLE IF NOT EXISTS tourism_faqs (
    id SERIAL PRIMARY KEY,
    category_id TEXT NOT NULL REFERENCES faq_categories(id) ON DELETE CASCADE,
    question JSONB NOT NULL,
    answer JSONB NOT NULL,
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

-- 4. Create indexes for tourism_faqs table
CREATE INDEX IF NOT EXISTS idx_tourism_faqs_category_id ON tourism_faqs (category_id);
CREATE INDEX IF NOT EXISTS idx_tourism_faqs_question_gin ON tourism_faqs USING GIN (question);
CREATE INDEX IF NOT EXISTS idx_tourism_faqs_answer_gin ON tourism_faqs USING GIN (answer);
CREATE INDEX IF NOT EXISTS idx_tourism_faqs_tags ON tourism_faqs USING GIN (tags array_ops);
CREATE INDEX IF NOT EXISTS idx_tourism_faqs_related_destination_ids ON tourism_faqs USING GIN (related_destination_ids array_ops);
CREATE INDEX IF NOT EXISTS idx_tourism_faqs_is_featured ON tourism_faqs (is_featured);
CREATE INDEX IF NOT EXISTS idx_tourism_faqs_embedding_hnsw ON tourism_faqs USING hnsw (embedding vector_cosine_ops) WITH (m='16', ef_construction='64');

-- 5. Create function to search FAQs by text
CREATE OR REPLACE FUNCTION search_faqs(
    p_query TEXT,
    p_category_id TEXT DEFAULT NULL,
    p_destination_id TEXT DEFAULT NULL,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    id INTEGER,
    category_id TEXT,
    category_name JSONB,
    question JSONB,
    answer JSONB,
    tags TEXT[],
    is_featured BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        f.id,
        f.category_id,
        c.name AS category_name,
        f.question,
        f.answer,
        f.tags,
        f.is_featured
    FROM 
        tourism_faqs f
    JOIN
        faq_categories c ON f.category_id = c.id
    WHERE 
        (p_category_id IS NULL OR f.category_id = p_category_id)
        AND (p_destination_id IS NULL OR p_destination_id = ANY(f.related_destination_ids))
        AND (
            to_tsvector('english', f.question->>'en') @@ plainto_tsquery('english', p_query)
            OR to_tsvector('english', f.answer->>'en') @@ plainto_tsquery('english', p_query)
            OR p_query = ANY(f.tags)
        )
    ORDER BY 
        f.is_featured DESC,
        ts_rank(to_tsvector('english', f.question->>'en'), plainto_tsquery('english', p_query)) +
        ts_rank(to_tsvector('english', f.answer->>'en'), plainto_tsquery('english', p_query)) DESC,
        f.helpful_count DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- 6. Create function to get FAQs by category
CREATE OR REPLACE FUNCTION get_faqs_by_category(
    p_category_id TEXT,
    p_limit INTEGER DEFAULT 20
)
RETURNS TABLE (
    id INTEGER,
    question JSONB,
    answer JSONB,
    tags TEXT[],
    is_featured BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        f.id,
        f.question,
        f.answer,
        f.tags,
        f.is_featured
    FROM 
        tourism_faqs f
    WHERE 
        f.category_id = p_category_id
    ORDER BY 
        f.is_featured DESC,
        f.helpful_count DESC,
        f.view_count DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- 7. Create function to get FAQs by destination
CREATE OR REPLACE FUNCTION get_faqs_by_destination(
    p_destination_id TEXT,
    p_limit INTEGER DEFAULT 20
)
RETURNS TABLE (
    id INTEGER,
    category_id TEXT,
    category_name JSONB,
    question JSONB,
    answer JSONB,
    is_featured BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        f.id,
        f.category_id,
        c.name AS category_name,
        f.question,
        f.answer,
        f.is_featured
    FROM 
        tourism_faqs f
    JOIN
        faq_categories c ON f.category_id = c.id
    WHERE 
        p_destination_id = ANY(f.related_destination_ids)
    ORDER BY 
        f.is_featured DESC,
        f.helpful_count DESC,
        f.view_count DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- 8. Create function to get featured FAQs
CREATE OR REPLACE FUNCTION get_featured_faqs(
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    id INTEGER,
    category_id TEXT,
    category_name JSONB,
    question JSONB,
    answer JSONB,
    tags TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        f.id,
        f.category_id,
        c.name AS category_name,
        f.question,
        f.answer,
        f.tags
    FROM 
        tourism_faqs f
    JOIN
        faq_categories c ON f.category_id = c.id
    WHERE 
        f.is_featured = TRUE
    ORDER BY 
        f.helpful_count DESC,
        f.view_count DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;
