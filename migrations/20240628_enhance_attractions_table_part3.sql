-- Migration: Enhance Attractions Table (Part 3)
-- Date: 2024-06-28
-- Description: Add religious and entertainment subcategories

-- 1. Add mosque and university subcategories
INSERT INTO attraction_subcategories (id, parent_type, name, description, icon)
VALUES
    ('historic_mosque', 'mosque_and_university',
     '{"en": "Historic Mosque", "ar": "مسجد تاريخي"}',
     '{"en": "Historically significant mosques", "ar": "المساجد ذات الأهمية التاريخية"}',
     'mosque'),
    ('islamic_university', 'mosque_and_university',
     '{"en": "Islamic University", "ar": "جامعة إسلامية"}',
     '{"en": "Traditional Islamic educational institutions", "ar": "مؤسسات التعليم الإسلامي التقليدية"}',
     'school'),
    ('madrasa', 'mosque_and_university',
     '{"en": "Madrasa", "ar": "مدرسة"}',
     '{"en": "Traditional Islamic schools", "ar": "المدارس الإسلامية التقليدية"}',
     'book'),
    ('mausoleum', 'mosque_and_university',
     '{"en": "Mausoleum", "ar": "ضريح"}',
     '{"en": "Tombs of Islamic religious or political figures", "ar": "أضرحة الشخصيات الدينية أو السياسية الإسلامية"}',
     'monument'),
    ('islamic_complex', 'mosque_and_university',
     '{"en": "Islamic Complex", "ar": "مجمع إسلامي"}',
     '{"en": "Complexes combining mosque, madrasa, and other Islamic institutions", "ar": "مجمعات تجمع بين المسجد والمدرسة وغيرها من المؤسسات الإسلامية"}',
     'landmark')
ON CONFLICT (id) DO NOTHING;

-- 2. Add bazaar subcategories
INSERT INTO attraction_subcategories (id, parent_type, name, description, icon)
VALUES
    ('traditional_market', 'bazaar',
     '{"en": "Traditional Market", "ar": "سوق تقليدي"}',
     '{"en": "Traditional markets with historical significance", "ar": "الأسواق التقليدية ذات الأهمية التاريخية"}',
     'store'),
    ('craft_market', 'bazaar',
     '{"en": "Craft Market", "ar": "سوق الحرف"}',
     '{"en": "Markets specializing in traditional crafts", "ar": "أسواق متخصصة في الحرف التقليدية"}',
     'hands'),
    ('spice_market', 'bazaar',
     '{"en": "Spice Market", "ar": "سوق التوابل"}',
     '{"en": "Markets specializing in spices and herbs", "ar": "أسواق متخصصة في التوابل والأعشاب"}',
     'pepper-hot'),
    ('gold_market', 'bazaar',
     '{"en": "Gold Market", "ar": "سوق الذهب"}',
     '{"en": "Markets specializing in gold and jewelry", "ar": "أسواق متخصصة في الذهب والمجوهرات"}',
     'gem'),
    ('textile_market', 'bazaar',
     '{"en": "Textile Market", "ar": "سوق المنسوجات"}',
     '{"en": "Markets specializing in textiles and fabrics", "ar": "أسواق متخصصة في المنسوجات والأقمشة"}',
     'shirt'),
    ('souvenir_market', 'bazaar',
     '{"en": "Souvenir Market", "ar": "سوق الهدايا التذكارية"}',
     '{"en": "Markets specializing in souvenirs and tourist items", "ar": "أسواق متخصصة في الهدايا التذكارية والعناصر السياحية"}',
     'gift')
ON CONFLICT (id) DO NOTHING;
