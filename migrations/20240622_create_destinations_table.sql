-- Migration: Create Destinations Table
-- Date: 2024-06-22
-- Description: Create a hierarchical destinations table for tourism locations

-- 1. Create destination_types table
CREATE TABLE IF NOT EXISTS destination_types (
    type TEXT PRIMARY KEY,
    name JSONB,
    description JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Populate destination_types table with initial data
INSERT INTO destination_types (type, name, description)
VALUES
    ('country', 
     '{"en": "Country", "ar": "دولة"}',
     '{"en": "A nation with its own government and defined territory", "ar": "أمة ذات حكومة خاصة بها وأراضي محددة"}'),
    ('region', 
     '{"en": "Region", "ar": "منطقة"}',
     '{"en": "A large area of land with distinct geographical, cultural, or administrative characteristics", "ar": "منطقة كبيرة من الأرض ذات خصائص جغرافية أو ثقافية أو إدارية مميزة"}'),
    ('governorate', 
     '{"en": "Governorate", "ar": "محافظة"}',
     '{"en": "An administrative division in Egypt, similar to a province or state", "ar": "تقسيم إداري في مصر، مشابه للمقاطعة أو الولاية"}'),
    ('city', 
     '{"en": "City", "ar": "مدينة"}',
     '{"en": "A large urban area with a significant population and infrastructure", "ar": "منطقة حضرية كبيرة ذات عدد سكان وبنية تحتية كبيرة"}'),
    ('town', 
     '{"en": "Town", "ar": "بلدة"}',
     '{"en": "A built-up area that is smaller than a city but larger than a village", "ar": "منطقة مبنية أصغر من المدينة ولكن أكبر من القرية"}'),
    ('village', 
     '{"en": "Village", "ar": "قرية"}',
     '{"en": "A small rural community, typically with a few hundred to a few thousand inhabitants", "ar": "مجتمع ريفي صغير، عادة ما يضم بضع مئات إلى بضعة آلاف من السكان"}'),
    ('district', 
     '{"en": "District", "ar": "حي"}',
     '{"en": "A division of a city or town, especially one with a particular character or purpose", "ar": "قسم من مدينة أو بلدة، خاصة ذات طابع أو غرض معين"}'),
    ('area', 
     '{"en": "Area", "ar": "منطقة"}',
     '{"en": "A part of a city, town, or countryside with a particular character or use", "ar": "جزء من مدينة أو بلدة أو ريف ذات طابع أو استخدام معين"}'),
    ('landmark', 
     '{"en": "Landmark", "ar": "معلم"}',
     '{"en": "A significant building or place with historical or cultural importance", "ar": "مبنى أو مكان مهم ذو أهمية تاريخية أو ثقافية"}'),
    ('natural_area', 
     '{"en": "Natural Area", "ar": "منطقة طبيعية"}',
     '{"en": "A geographical area with distinct natural features like deserts, oases, or coastlines", "ar": "منطقة جغرافية ذات ميزات طبيعية مميزة مثل الصحاري أو الواحات أو السواحل"}')
ON CONFLICT (type) DO NOTHING;

-- 3. Create destinations table with hierarchical structure
CREATE TABLE IF NOT EXISTS destinations (
    id TEXT PRIMARY KEY,
    name JSONB NOT NULL,
    description JSONB,
    type TEXT NOT NULL REFERENCES destination_types(type),
    parent_id TEXT REFERENCES destinations(id),
    country TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    elevation DOUBLE PRECISION,
    population INTEGER,
    area_km2 DOUBLE PRECISION,
    timezone TEXT,
    local_language TEXT,
    currency TEXT,
    best_time_to_visit JSONB,
    weather JSONB,
    safety_info JSONB,
    local_customs JSONB,
    travel_tips JSONB,
    unesco_site BOOLEAN DEFAULT FALSE,
    data JSONB DEFAULT '{}'::jsonb,
    embedding VECTOR(1536),
    geom GEOMETRY(Point, 4326),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_id TEXT
);

-- 4. Create indexes for destinations table
CREATE INDEX IF NOT EXISTS idx_destinations_type ON destinations (type);
CREATE INDEX IF NOT EXISTS idx_destinations_parent_id ON destinations (parent_id);
CREATE INDEX IF NOT EXISTS idx_destinations_country ON destinations (country);
CREATE INDEX IF NOT EXISTS idx_destinations_name_gin ON destinations USING GIN (name);
CREATE INDEX IF NOT EXISTS idx_destinations_description_gin ON destinations USING GIN (description);
CREATE INDEX IF NOT EXISTS idx_destinations_data_gin ON destinations USING GIN (data);
CREATE INDEX IF NOT EXISTS idx_destinations_geom ON destinations USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_destinations_embedding_hnsw ON destinations USING hnsw (embedding vector_cosine_ops) WITH (m='16', ef_construction='64');

-- 5. Create destination_images table for storing images related to destinations
CREATE TABLE IF NOT EXISTS destination_images (
    id SERIAL PRIMARY KEY,
    destination_id TEXT NOT NULL REFERENCES destinations(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    caption JSONB,
    is_primary BOOLEAN DEFAULT FALSE,
    credit TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_id TEXT
);

CREATE INDEX IF NOT EXISTS idx_destination_images_destination_id ON destination_images (destination_id);

-- 6. Create destination_seasons table for seasonal information
CREATE TABLE IF NOT EXISTS destination_seasons (
    id SERIAL PRIMARY KEY,
    destination_id TEXT NOT NULL REFERENCES destinations(id) ON DELETE CASCADE,
    season TEXT NOT NULL,
    start_month INTEGER NOT NULL CHECK (start_month BETWEEN 1 AND 12),
    end_month INTEGER NOT NULL CHECK (end_month BETWEEN 1 AND 12),
    description JSONB,
    temperature_min DOUBLE PRECISION,
    temperature_max DOUBLE PRECISION,
    precipitation DOUBLE PRECISION,
    humidity DOUBLE PRECISION,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_destination_seasons_destination_id ON destination_seasons (destination_id);
CREATE INDEX IF NOT EXISTS idx_destination_seasons_season ON destination_seasons (season);

-- 7. Create destination_events table for events at destinations
CREATE TABLE IF NOT EXISTS destination_events (
    id SERIAL PRIMARY KEY,
    destination_id TEXT NOT NULL REFERENCES destinations(id) ON DELETE CASCADE,
    name JSONB NOT NULL,
    description JSONB,
    start_date DATE,
    end_date DATE,
    recurring BOOLEAN DEFAULT FALSE,
    recurrence_pattern TEXT,
    location_details JSONB,
    event_type TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_destination_events_destination_id ON destination_events (destination_id);
CREATE INDEX IF NOT EXISTS idx_destination_events_start_date ON destination_events (start_date);
CREATE INDEX IF NOT EXISTS idx_destination_events_event_type ON destination_events (event_type);

-- 8. Create function to get destination hierarchy
CREATE OR REPLACE FUNCTION get_destination_hierarchy(p_destination_id TEXT)
RETURNS TABLE (
    id TEXT,
    name JSONB,
    type TEXT,
    level INTEGER
) AS $$
WITH RECURSIVE destination_tree AS (
    -- Base case: the destination itself
    SELECT 
        d.id,
        d.name,
        d.type,
        0 AS level
    FROM 
        destinations d
    WHERE 
        d.id = p_destination_id
    
    UNION ALL
    
    -- Recursive case: parent destinations
    SELECT 
        d.id,
        d.name,
        d.type,
        dt.level + 1
    FROM 
        destinations d
    JOIN 
        destination_tree dt ON d.id = dt.id
    JOIN 
        destinations parent ON dt.id = parent.parent_id
)
SELECT 
    id, 
    name, 
    type, 
    level
FROM 
    destination_tree
ORDER BY 
    level DESC;
$$ LANGUAGE SQL;

-- 9. Create function to get destination children
CREATE OR REPLACE FUNCTION get_destination_children(p_parent_id TEXT)
RETURNS TABLE (
    id TEXT,
    name JSONB,
    type TEXT,
    level INTEGER
) AS $$
WITH RECURSIVE destination_tree AS (
    -- Base case: immediate children
    SELECT 
        d.id,
        d.name,
        d.type,
        1 AS level
    FROM 
        destinations d
    WHERE 
        d.parent_id = p_parent_id
    
    UNION ALL
    
    -- Recursive case: children of children
    SELECT 
        d.id,
        d.name,
        d.type,
        dt.level + 1
    FROM 
        destinations d
    JOIN 
        destination_tree dt ON d.parent_id = dt.id
)
SELECT 
    id, 
    name, 
    type, 
    level
FROM 
    destination_tree
ORDER BY 
    level, type, name->>'en';
$$ LANGUAGE SQL;

-- 10. Create initial country record for Egypt
INSERT INTO destinations (
    id, 
    name, 
    description, 
    type, 
    parent_id, 
    country, 
    latitude, 
    longitude, 
    population, 
    area_km2, 
    timezone, 
    local_language, 
    currency,
    best_time_to_visit,
    weather,
    safety_info,
    local_customs,
    travel_tips,
    data,
    user_id
)
VALUES (
    'egypt',
    '{"en": "Egypt", "ar": "مصر"}',
    '{"en": "Egypt, a country linking northeast Africa with the Middle East, dates to the time of the pharaohs. Millennia-old monuments still sit along the fertile Nile River Valley, including the colossal Pyramids and Sphinx at Giza and the hieroglyph-lined Karnak Temple and Valley of the Kings tombs in Luxor.", "ar": "مصر، دولة تربط شمال شرق أفريقيا بالشرق الأوسط، تعود إلى عصر الفراعنة. لا تزال الآثار التي يبلغ عمرها آلاف السنين قائمة على طول وادي نهر النيل الخصيب، بما في ذلك أهرامات الجيزة الضخمة وأبو الهول ومعبد الكرنك المبطن بالهيروغليفية ومقابر وادي الملوك في الأقصر."}',
    'country',
    NULL,
    'Egypt',
    26.8206,
    30.8025,
    104000000,
    1001450,
    'Africa/Cairo',
    'Arabic',
    'Egyptian Pound (EGP)',
    '{"en": {"best_months": [10, 11, 12, 1, 2, 3, 4], "peak_season": [12, 1], "low_season": [6, 7, 8], "notes": "The best time to visit Egypt is from October to April when temperatures are cooler. Avoid the summer months (June to August) when temperatures can exceed 40°C (104°F)."}, "ar": {"best_months": [10, 11, 12, 1, 2, 3, 4], "peak_season": [12, 1], "low_season": [6, 7, 8], "notes": "أفضل وقت لزيارة مصر هو من أكتوبر إلى أبريل عندما تكون درجات الحرارة أكثر برودة. تجنب أشهر الصيف (يونيو إلى أغسطس) عندما يمكن أن تتجاوز درجات الحرارة 40 درجة مئوية."}}',
    '{"en": {"summer": {"months": [6, 7, 8], "temperature": {"min": 22, "max": 40}, "description": "Hot and dry with very high temperatures, especially in Upper Egypt and desert areas."}, "winter": {"months": [12, 1, 2], "temperature": {"min": 10, "max": 24}, "description": "Mild and pleasant in most parts, though Cairo and the north can be cool in the evenings."}, "spring": {"months": [3, 4, 5], "temperature": {"min": 15, "max": 32}, "description": "Warm and comfortable, though spring sandstorms (khamsin) can occur."}, "autumn": {"months": [9, 10, 11], "temperature": {"min": 17, "max": 35}, "description": "Gradually cooling from summer heat, with pleasant temperatures and clear skies."}}, "ar": {"summer": {"months": [6, 7, 8], "temperature": {"min": 22, "max": 40}, "description": "حار وجاف مع درجات حرارة مرتفعة جدًا، خاصة في صعيد مصر والمناطق الصحراوية."}, "winter": {"months": [12, 1, 2], "temperature": {"min": 10, "max": 24}, "description": "معتدل ولطيف في معظم المناطق، رغم أن القاهرة والشمال يمكن أن يكونا باردين في المساء."}, "spring": {"months": [3, 4, 5], "temperature": {"min": 15, "max": 32}, "description": "دافئ ومريح، رغم أن عواصف الرمال الربيعية (الخماسين) يمكن أن تحدث."}, "autumn": {"months": [9, 10, 11], "temperature": {"min": 17, "max": 35}, "description": "تبرد تدريجيًا من حرارة الصيف، مع درجات حرارة لطيفة وسماء صافية."}}}',
    '{"en": {"safety_level": "Moderate", "emergency_numbers": {"police": "122", "ambulance": "123", "tourist_police": "126"}, "areas_to_avoid": "North Sinai is currently not recommended for travel. Exercise increased caution in the Western Desert and near the Libyan border.", "common_scams": "Be aware of aggressive vendors, inflated prices for tourists, and unofficial tour guides. Always agree on prices before services.", "health_concerns": "Drink only bottled water. Use sunscreen and stay hydrated, especially in summer months."}, "ar": {"safety_level": "متوسط", "emergency_numbers": {"police": "122", "ambulance": "123", "tourist_police": "126"}, "areas_to_avoid": "لا يُنصح حاليًا بالسفر إلى شمال سيناء. توخى الحذر المتزايد في الصحراء الغربية وبالقرب من الحدود الليبية.", "common_scams": "كن على دراية بالبائعين العدوانيين والأسعار المرتفعة للسياح والمرشدين السياحيين غير الرسميين. اتفق دائمًا على الأسعار قبل الخدمات.", "health_concerns": "اشرب الماء المعبأ فقط. استخدم واقي الشمس وابق رطبًا، خاصة في أشهر الصيف."}}',
    '{"en": {"greetings": "Egyptians are known for their hospitality. A handshake is the common greeting. Use right hand for eating and greeting as the left hand is considered unclean.", "dress_code": "Dress modestly, especially when visiting religious sites. Women should cover shoulders and knees. Men should avoid shorts in religious areas.", "tipping": "Tipping (baksheesh) is expected for most services. 10-15% is standard in restaurants if service charge is not included.", "ramadan": "During Ramadan, avoid eating, drinking, or smoking in public during daylight hours out of respect for those fasting.", "photography": "Ask permission before photographing people. Photography may be restricted at some sites or require an additional fee."}, "ar": {"greetings": "يُعرف المصريون بكرم ضيافتهم. المصافحة هي التحية الشائعة. استخدم اليد اليمنى للأكل والتحية لأن اليد اليسرى تعتبر غير نظيفة.", "dress_code": "ارتدِ ملابس محتشمة، خاصة عند زيارة المواقع الدينية. يجب على النساء تغطية الكتفين والركبتين. يجب على الرجال تجنب ارتداء السراويل القصيرة في المناطق الدينية.", "tipping": "يُتوقع البقشيش لمعظم الخدمات. 10-15٪ هو المعيار في المطاعم إذا لم يتم تضمين رسوم الخدمة.", "ramadan": "خلال شهر رمضان، تجنب الأكل أو الشرب أو التدخين في الأماكن العامة خلال ساعات النهار احترامًا للصائمين.", "photography": "اطلب الإذن قبل تصوير الأشخاص. قد يكون التصوير مقيدًا في بعض المواقع أو يتطلب رسومًا إضافية."}}',
    '{"en": {"visa": "Most visitors need a visa, which can be obtained on arrival at Egyptian airports or in advance from Egyptian embassies. E-visas are also available online.", "currency": "The Egyptian Pound (EGP) is the local currency. ATMs are widely available in cities and tourist areas. Credit cards are accepted at major establishments.", "transportation": "Use official taxis or ride-sharing apps. Consider domestic flights for long distances. Trains connect major cities along the Nile.", "bargaining": "Bargaining is expected in markets (souks). Start at about 50% of the initial asking price and negotiate from there.", "communication": "Arabic is the official language, but English is widely spoken in tourist areas. Learning a few Arabic phrases is appreciated."}, "ar": {"visa": "يحتاج معظم الزوار إلى تأشيرة، والتي يمكن الحصول عليها عند الوصول إلى المطارات المصرية أو مسبقًا من السفارات المصرية. التأشيرات الإلكترونية متاحة أيضًا عبر الإنترنت.", "currency": "الجنيه المصري (EGP) هو العملة المحلية. أجهزة الصراف الآلي متوفرة على نطاق واسع في المدن والمناطق السياحية. بطاقات الائتمان مقبولة في المؤسسات الكبرى.", "transportation": "استخدم سيارات الأجرة الرسمية أو تطبيقات مشاركة الركوب. فكر في الرحلات الجوية الداخلية للمسافات الطويلة. القطارات تربط المدن الرئيسية على طول النيل.", "bargaining": "المساومة متوقعة في الأسواق. ابدأ بحوالي 50٪ من السعر المطلوب الأولي وتفاوض من هناك.", "communication": "اللغة العربية هي اللغة الرسمية، ولكن اللغة الإنجليزية منتشرة في المناطق السياحية. تعلم بعض العبارات العربية يكون محل تقدير."}}',
    '{"official_name": "Arab Republic of Egypt", "capital": "Cairo", "government": "Presidential Republic", "calling_code": "+20", "driving_side": "right", "electricity": "220V, 50Hz", "plug_types": ["C", "F"], "unesco_sites": 7, "major_airports": ["Cairo International Airport (CAI)", "Hurghada International Airport (HRG)", "Sharm El Sheikh International Airport (SSH)", "Luxor International Airport (LXR)", "Alexandria International Airport (ALY)"], "major_holidays": ["Coptic Christmas (January 7)", "Ramadan", "Eid al-Fitr", "Eid al-Adha", "Sham El Nessim (Spring Festival)", "Revolution Day (July 23)"], "internet_domain": ".eg"}',
    'system'
)
ON CONFLICT (id) DO UPDATE
SET 
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    best_time_to_visit = EXCLUDED.best_time_to_visit,
    weather = EXCLUDED.weather,
    safety_info = EXCLUDED.safety_info,
    local_customs = EXCLUDED.local_customs,
    travel_tips = EXCLUDED.travel_tips,
    data = EXCLUDED.data,
    updated_at = CURRENT_TIMESTAMP;
