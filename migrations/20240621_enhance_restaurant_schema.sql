-- Migration: Enhance Restaurant Schema
-- Date: 2024-06-21
-- Description: Enhance the restaurant schema with foreign keys and additional fields

-- 1. Create restaurant_types table
CREATE TABLE IF NOT EXISTS restaurant_types (
    type TEXT PRIMARY KEY,
    name JSONB,
    description JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Populate restaurant_types table with initial data
INSERT INTO restaurant_types (type, name, description)
VALUES
    ('fine_dining', 
     '{"en": "Fine Dining", "ar": "مطعم فاخر"}',
     '{"en": "Upscale restaurants with formal service and high-quality cuisine", "ar": "مطاعم راقية ذات خدمة رسمية ومأكولات عالية الجودة"}'),
    ('casual_dining', 
     '{"en": "Casual Dining", "ar": "مطعم غير رسمي"}',
     '{"en": "Restaurants with a relaxed atmosphere and moderate prices", "ar": "مطاعم ذات أجواء مريحة وأسعار معتدلة"}'),
    ('fast_food', 
     '{"en": "Fast Food", "ar": "وجبات سريعة"}',
     '{"en": "Quick-service restaurants with standardized food preparation", "ar": "مطاعم ذات خدمة سريعة وإعداد طعام موحد"}'),
    ('street_food', 
     '{"en": "Street Food", "ar": "طعام الشارع"}',
     '{"en": "Food vendors selling ready-to-eat meals from portable stalls", "ar": "باعة طعام يبيعون وجبات جاهزة للأكل من أكشاك متنقلة"}'),
    ('cafe', 
     '{"en": "Café", "ar": "مقهى"}',
     '{"en": "Establishments serving coffee, tea, and light meals", "ar": "منشآت تقدم القهوة والشاي والوجبات الخفيفة"}'),
    ('traditional', 
     '{"en": "Traditional Restaurant", "ar": "مطعم تقليدي"}',
     '{"en": "Restaurants serving authentic local cuisine", "ar": "مطاعم تقدم المأكولات المحلية الأصيلة"}'),
    ('family_style', 
     '{"en": "Family Style", "ar": "مطعم عائلي"}',
     '{"en": "Restaurants with a family-friendly atmosphere and shared dishes", "ar": "مطاعم ذات أجواء عائلية وأطباق مشتركة"}'),
    ('buffet', 
     '{"en": "Buffet", "ar": "بوفيه"}',
     '{"en": "Restaurants where customers serve themselves from a variety of dishes", "ar": "مطاعم حيث يخدم العملاء أنفسهم من مجموعة متنوعة من الأطباق"}'),
    ('food_court', 
     '{"en": "Food Court", "ar": "ساحة طعام"}',
     '{"en": "Common area with multiple food vendors", "ar": "منطقة مشتركة مع العديد من باعة الطعام"}'),
    ('hotel_restaurant', 
     '{"en": "Hotel Restaurant", "ar": "مطعم فندق"}',
     '{"en": "Restaurants located within hotels", "ar": "مطاعم تقع داخل الفنادق"}'
    )
ON CONFLICT (type) DO NOTHING;

-- 3. Clean up and standardize cuisines table
-- First, create a temporary table with the cleaned-up data
CREATE TEMP TABLE temp_cuisines (
    type TEXT PRIMARY KEY,
    name JSONB,
    description JSONB,
    region TEXT,
    popular_dishes JSONB
);

-- Insert standardized cuisine data
INSERT INTO temp_cuisines (type, name, description, region, popular_dishes)
VALUES
    ('egyptian', 
     '{"en": "Egyptian", "ar": "مصري"}',
     '{"en": "Traditional Egyptian cuisine featuring beans, bread, rice, and vegetables", "ar": "المطبخ المصري التقليدي الذي يتميز بالفول والخبز والأرز والخضروات"}',
     'Egypt',
     '{"en": ["Koshari", "Ful Medames", "Molokhia", "Mahshi"], "ar": ["كشري", "فول مدمس", "ملوخية", "محشي"]}'
    ),
    ('alexandrian', 
     '{"en": "Alexandrian", "ar": "إسكندراني"}',
     '{"en": "Coastal cuisine from Alexandria featuring seafood and Mediterranean influences", "ar": "مأكولات ساحلية من الإسكندرية تتميز بالمأكولات البحرية والتأثيرات المتوسطية"}',
     'Lower Egypt',
     '{"en": ["Grilled Fish", "Seafood Soup", "Alexandrian Liver", "Calamari"], "ar": ["سمك مشوي", "شوربة مأكولات بحرية", "كبدة إسكندراني", "كاليماري"]}'
    ),
    ('nubian', 
     '{"en": "Nubian", "ar": "نوبي"}',
     '{"en": "Cuisine from southern Egypt with unique spices and cooking methods", "ar": "مأكولات من جنوب مصر مع توابل وطرق طهي فريدة"}',
     'Upper Egypt',
     '{"en": ["Nubian Lamb", "Okra Stew", "Kisra", "Nubian Fish"], "ar": ["لحم ضأن نوبي", "بامية", "كسرة", "سمك نوبي"]}'
    ),
    ('bedouin', 
     '{"en": "Bedouin", "ar": "بدوي"}',
     '{"en": "Desert cuisine with simple ingredients and traditional cooking methods", "ar": "مأكولات صحراوية بمكونات بسيطة وطرق طهي تقليدية"}',
     'Sinai',
     '{"en": ["Zarb", "Bedouin Bread", "Camel Meat", "Bedouin Tea"], "ar": ["زرب", "خبز بدوي", "لحم جمل", "شاي بدوي"]}'
    ),
    ('mediterranean', 
     '{"en": "Mediterranean", "ar": "متوسطي"}',
     '{"en": "Cuisine from Mediterranean countries featuring olive oil, fresh vegetables, and seafood", "ar": "مأكولات من دول البحر المتوسط تتميز بزيت الزيتون والخضروات الطازجة والمأكولات البحرية"}',
     'Mediterranean Coast',
     '{"en": ["Greek Salad", "Hummus", "Grilled Fish", "Olives"], "ar": ["سلطة يونانية", "حمص", "سمك مشوي", "زيتون"]}'
    ),
    ('middle_eastern', 
     '{"en": "Middle Eastern", "ar": "شرق أوسطي"}',
     '{"en": "Cuisine from the Middle East featuring grilled meats, rice, and bread", "ar": "مأكولات من الشرق الأوسط تتميز باللحوم المشوية والأرز والخبز"}',
     'Middle East',
     '{"en": ["Shawarma", "Falafel", "Kebab", "Tabbouleh"], "ar": ["شاورما", "فلافل", "كباب", "تبولة"]}'
    ),
    ('seafood', 
     '{"en": "Seafood", "ar": "مأكولات بحرية"}',
     '{"en": "Cuisine featuring fish and other seafood", "ar": "مأكولات تتميز بالأسماك والمأكولات البحرية الأخرى"}',
     'Coastal Regions',
     '{"en": ["Grilled Fish", "Calamari", "Shrimp", "Seafood Soup"], "ar": ["سمك مشوي", "كاليماري", "جمبري", "شوربة مأكولات بحرية"]}'
    ),
    ('international', 
     '{"en": "International", "ar": "عالمي"}',
     '{"en": "Cuisine featuring dishes from various countries", "ar": "مأكولات تتميز بأطباق من مختلف البلدان"}',
     'Global',
     '{"en": ["Pasta", "Steak", "Sushi", "Curry"], "ar": ["باستا", "ستيك", "سوشي", "كاري"]}'
    ),
    ('italian', 
     '{"en": "Italian", "ar": "إيطالي"}',
     '{"en": "Cuisine from Italy featuring pasta, pizza, and Mediterranean ingredients", "ar": "مأكولات من إيطاليا تتميز بالمعكرونة والبيتزا والمكونات المتوسطية"}',
     'Italy',
     '{"en": ["Pizza", "Pasta", "Risotto", "Tiramisu"], "ar": ["بيتزا", "باستا", "ريزوتو", "تيراميسو"]}'
    ),
    ('asian', 
     '{"en": "Asian", "ar": "آسيوي"}',
     '{"en": "Cuisine from Asian countries featuring rice, noodles, and unique spices", "ar": "مأكولات من دول آسيوية تتميز بالأرز والمعكرونة والتوابل الفريدة"}',
     'Asia',
     '{"en": ["Sushi", "Pad Thai", "Curry", "Dim Sum"], "ar": ["سوشي", "باد تاي", "كاري", "ديم سم"]}'
    ),
    ('fusion', 
     '{"en": "Fusion", "ar": "مزيج"}',
     '{"en": "Cuisine combining elements from different culinary traditions", "ar": "مأكولات تجمع بين عناصر من تقاليد طهي مختلفة"}',
     'Global',
     '{"en": ["Fusion Tacos", "Asian-Mediterranean Bowls", "Modern Egyptian"], "ar": ["تاكو مزيج", "أطباق آسيوية-متوسطية", "مصري حديث"]}'
    )
;

-- Drop and recreate the cuisines table with the new structure
DROP TABLE IF EXISTS cuisines;
CREATE TABLE cuisines (
    type TEXT PRIMARY KEY,
    name JSONB,
    description JSONB,
    region TEXT,
    popular_dishes JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Copy data from temp table to new cuisines table
INSERT INTO cuisines (type, name, description, region, popular_dishes)
SELECT type, name, description, region, popular_dishes FROM temp_cuisines;

-- Drop temp table
DROP TABLE temp_cuisines;

-- 4. Alter restaurants table to add new columns
ALTER TABLE restaurants
    ADD COLUMN IF NOT EXISTS city_id TEXT REFERENCES cities(id),
    ADD COLUMN IF NOT EXISTS region_id TEXT REFERENCES regions(id),
    ADD COLUMN IF NOT EXISTS type_id TEXT REFERENCES restaurant_types(type),
    ADD COLUMN IF NOT EXISTS cuisine_id TEXT REFERENCES cuisines(type),
    ADD COLUMN IF NOT EXISTS price_range TEXT CHECK (price_range IN ('budget', 'mid_range', 'luxury')),
    ADD COLUMN IF NOT EXISTS rating NUMERIC(3,1) CHECK (rating >= 0 AND rating <= 5);

-- 5. Create GIN indexes for JSONB columns
CREATE INDEX IF NOT EXISTS idx_restaurants_name_gin ON restaurants USING GIN (name);
CREATE INDEX IF NOT EXISTS idx_restaurants_description_gin ON restaurants USING GIN (description);
CREATE INDEX IF NOT EXISTS idx_restaurants_data_gin ON restaurants USING GIN (data);

-- 6. Create indexes for foreign key columns
CREATE INDEX IF NOT EXISTS idx_restaurants_city_id ON restaurants (city_id);
CREATE INDEX IF NOT EXISTS idx_restaurants_region_id ON restaurants (region_id);
CREATE INDEX IF NOT EXISTS idx_restaurants_type_id ON restaurants (type_id);
CREATE INDEX IF NOT EXISTS idx_restaurants_cuisine_id ON restaurants (cuisine_id);

-- 7. Update existing restaurants with foreign keys if possible
UPDATE restaurants
SET 
    city_id = (SELECT id FROM cities WHERE name_en = restaurants.city LIMIT 1),
    region_id = (SELECT id FROM regions WHERE name_en = restaurants.region LIMIT 1),
    cuisine_id = CASE 
        WHEN cuisine LIKE 'Egyptian%' THEN 'egyptian'
        WHEN cuisine LIKE 'Nubian%' THEN 'nubian'
        WHEN cuisine LIKE '%Seafood%' THEN 'seafood'
        WHEN cuisine LIKE '%Mediterranean%' THEN 'mediterranean'
        ELSE NULL
    END,
    type_id = CASE 
        WHEN type LIKE '%Traditional%' THEN 'traditional'
        WHEN type LIKE '%Street%' THEN 'street_food'
        ELSE 'casual_dining'
    END,
    price_range = CASE 
        WHEN (data->>'price_level')::int >= 4 THEN 'luxury'
        WHEN (data->>'price_level')::int >= 2 THEN 'mid_range'
        ELSE 'budget'
    END,
    rating = (data->>'rating')::numeric;
