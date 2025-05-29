-- Migration: Enhance Attractions Table (Part 2)
-- Date: 2024-06-28
-- Description: Add more subcategories for museums, natural, cultural, religious, and entertainment attractions

-- 1. Add museum subcategories
INSERT INTO attraction_subcategories (id, parent_type, name, description, icon)
VALUES
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
     'microscope')
ON CONFLICT (id) DO NOTHING;

-- 2. Add modern landmark subcategories
INSERT INTO attraction_subcategories (id, parent_type, name, description, icon)
VALUES
    ('modern_architecture', 'modern_landmark',
     '{"en": "Modern Architecture", "ar": "العمارة الحديثة"}',
     '{"en": "Contemporary architectural landmarks", "ar": "معالم معمارية معاصرة"}',
     'building'),
    ('urban_park', 'modern_landmark',
     '{"en": "Urban Park", "ar": "حديقة حضرية"}',
     '{"en": "Parks and green spaces in urban areas", "ar": "الحدائق والمساحات الخضراء في المناطق الحضرية"}',
     'tree'),
    ('monument', 'modern_landmark',
     '{"en": "Monument", "ar": "نصب تذكاري"}',
     '{"en": "Modern monuments and memorials", "ar": "النصب التذكارية والمعالم الحديثة"}',
     'monument'),
    ('bridge', 'modern_landmark',
     '{"en": "Bridge", "ar": "جسر"}',
     '{"en": "Notable bridges and crossings", "ar": "الجسور والمعابر البارزة"}',
     'bridge'),
    ('tower', 'modern_landmark',
     '{"en": "Tower", "ar": "برج"}',
     '{"en": "Observation and communication towers", "ar": "أبراج المراقبة والاتصالات"}',
     'tower'),
    ('plaza', 'modern_landmark',
     '{"en": "Plaza", "ar": "ساحة"}',
     '{"en": "Public squares and plazas", "ar": "الميادين والساحات العامة"}',
     'city')
ON CONFLICT (id) DO NOTHING;

-- 3. Add cultural center subcategories
INSERT INTO attraction_subcategories (id, parent_type, name, description, icon)
VALUES
    ('arts_center', 'cultural_center',
     '{"en": "Arts Center", "ar": "مركز فنون"}',
     '{"en": "Centers for visual and performing arts", "ar": "مراكز للفنون البصرية والأدائية"}',
     'palette'),
    ('cultural_museum', 'cultural_center',
     '{"en": "Cultural Museum", "ar": "متحف ثقافي"}',
     '{"en": "Museums showcasing cultural heritage", "ar": "متاحف تعرض التراث الثقافي"}',
     'landmark'),
    ('performance_venue', 'cultural_center',
     '{"en": "Performance Venue", "ar": "مكان العروض"}',
     '{"en": "Venues for music, dance, and theatrical performances", "ar": "أماكن للموسيقى والرقص والعروض المسرحية"}',
     'masks-theater'),
    ('educational_center', 'cultural_center',
     '{"en": "Educational Center", "ar": "مركز تعليمي"}',
     '{"en": "Centers for cultural education and workshops", "ar": "مراكز للتعليم الثقافي وورش العمل"}',
     'book')
ON CONFLICT (id) DO NOTHING;
