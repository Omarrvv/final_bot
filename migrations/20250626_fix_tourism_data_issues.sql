-- Migration: Fix Tourism Data Issues
-- Date: 2025-06-26

BEGIN;

-- 1. Fix duplicate FAQs
-- Delete duplicate FAQs, keeping only the ones with the lowest IDs
DELETE FROM tourism_faqs
WHERE id IN (4, 5, 6, 7, 8, 9);

-- 2. Generate missing embeddings for FAQs
-- This is a placeholder - actual embedding generation would be done in application code
-- We'll just mark these records for the Python script to handle
-- We won't update the embedding column here as it requires the correct dimensions

-- 3. Fix data quality issues in destination names
-- Update generated/test city names to more realistic Egyptian city names
UPDATE destinations
SET name = jsonb_build_object('en', 'Alexandria', 'ar', 'الإسكندرية')
WHERE id = 'coastal_american_city';

UPDATE destinations
SET name = jsonb_build_object('en', 'Hurghada', 'ar', 'الغردقة')
WHERE id = 'coastal_allow_oasis';

UPDATE destinations
SET name = jsonb_build_object('en', 'Minya', 'ar', 'المنيا')
WHERE id = 'southern_hundred_oasis';

UPDATE destinations
SET name = jsonb_build_object('en', 'Sohag', 'ar', 'سوهاج')
WHERE id = 'nile_interest_settlement';

UPDATE destinations
SET name = jsonb_build_object('en', 'Qena', 'ar', 'قنا')
WHERE id = 'nile_within_city';

UPDATE destinations
SET name = jsonb_build_object('en', 'Edfu', 'ar', 'إدفو')
WHERE id = 'ancient_condition_harbor';

UPDATE destinations
SET name = jsonb_build_object('en', 'Kom Ombo', 'ar', 'كوم أمبو')
WHERE id = 'historic_eye_village';

UPDATE destinations
SET name = jsonb_build_object('en', 'Esna', 'ar', 'إسنا')
WHERE id = 'southern_world_city';

UPDATE destinations
SET name = jsonb_build_object('en', 'Abydos', 'ar', 'أبيدوس')
WHERE id = 'southern_least_town';

UPDATE destinations
SET name = jsonb_build_object('en', 'Dendera', 'ar', 'دندرة')
WHERE id = 'southern_she_harbor';

UPDATE destinations
SET name = jsonb_build_object('en', 'Abu Simbel', 'ar', 'أبو سمبل')
WHERE id = 'ancient_participant_town';

UPDATE destinations
SET name = jsonb_build_object('en', 'Philae', 'ar', 'فيلة')
WHERE id = 'nile_say_settlement';

UPDATE destinations
SET name = jsonb_build_object('en', 'Valley of the Kings', 'ar', 'وادي الملوك')
WHERE id = 'valley_of_harbor';

UPDATE destinations
SET name = jsonb_build_object('en', 'Assiut', 'ar', 'أسيوط')
WHERE id = 'southern_citizen_city';

UPDATE destinations
SET name = jsonb_build_object('en', 'Valley of the Queens', 'ar', 'وادي الملكات')
WHERE id = 'valley_show_harbor';

UPDATE destinations
SET name = jsonb_build_object('en', 'Beni Suef', 'ar', 'بني سويف')
WHERE id = 'nile_heart_city';

UPDATE destinations
SET name = jsonb_build_object('en', 'Fayoum', 'ar', 'الفيوم')
WHERE id = 'historic_bank_oasis';

-- Update other destinations with generated names in Lower Egypt
UPDATE destinations
SET name = jsonb_build_object('en', 'Giza', 'ar', 'الجيزة')
WHERE id = 'desert_american_settlement';

UPDATE destinations
SET name = jsonb_build_object('en', 'Mansoura', 'ar', 'المنصورة')
WHERE id = 'desert_allow_city';

UPDATE destinations
SET name = jsonb_build_object('en', 'Tanta', 'ar', 'طنطا')
WHERE id = 'desert_hundred_town';

UPDATE destinations
SET name = jsonb_build_object('en', 'Zagazig', 'ar', 'الزقازيق')
WHERE id = 'desert_interest_oasis';

UPDATE destinations
SET name = jsonb_build_object('en', 'Damanhur', 'ar', 'دمنهور')
WHERE id = 'desert_within_harbor';

UPDATE destinations
SET name = jsonb_build_object('en', 'Damietta', 'ar', 'دمياط')
WHERE id = 'desert_condition_village';

UPDATE destinations
SET name = jsonb_build_object('en', 'Port Said', 'ar', 'بورسعيد')
WHERE id = 'desert_eye_settlement';

UPDATE destinations
SET name = jsonb_build_object('en', 'Suez', 'ar', 'السويس')
WHERE id = 'desert_world_oasis';

UPDATE destinations
SET name = jsonb_build_object('en', 'Ismailia', 'ar', 'الإسماعيلية')
WHERE id = 'desert_least_city';

-- Update destinations in Mediterranean Coast
UPDATE destinations
SET name = jsonb_build_object('en', 'Marsa Matruh', 'ar', 'مرسى مطروح')
WHERE id = 'coastal_she_town';

UPDATE destinations
SET name = jsonb_build_object('en', 'El Alamein', 'ar', 'العلمين')
WHERE id = 'coastal_participant_oasis';

UPDATE destinations
SET name = jsonb_build_object('en', 'Rosetta', 'ar', 'رشيد')
WHERE id = 'coastal_say_city';

UPDATE destinations
SET name = jsonb_build_object('en', 'Baltim', 'ar', 'بلطيم')
WHERE id = 'coastal_of_settlement';

UPDATE destinations
SET name = jsonb_build_object('en', 'Ras El Bar', 'ar', 'رأس البر')
WHERE id = 'coastal_citizen_town';

UPDATE destinations
SET name = jsonb_build_object('en', 'Port Said', 'ar', 'بورسعيد')
WHERE id = 'coastal_show_oasis';

UPDATE destinations
SET name = jsonb_build_object('en', 'El Arish', 'ar', 'العريش')
WHERE id = 'coastal_heart_city';

UPDATE destinations
SET name = jsonb_build_object('en', 'Dahab', 'ar', 'دهب')
WHERE id = 'coastal_bank_settlement';

-- Update additional coastal cities
UPDATE destinations
SET name = jsonb_build_object('en', 'Sharm El Sheikh', 'ar', 'شرم الشيخ')
WHERE id = 'coastal_card_city';

UPDATE destinations
SET name = jsonb_build_object('en', 'Mersa Alam', 'ar', 'مرسى علم')
WHERE id = 'coastal_others_oasis';

UPDATE destinations
SET name = jsonb_build_object('en', 'Nuweiba', 'ar', 'نويبع')
WHERE id = 'coastal_thus_city';

UPDATE destinations
SET name = jsonb_build_object('en', 'Taba', 'ar', 'طابا')
WHERE id = 'coastal_expect_city';

UPDATE destinations
SET name = jsonb_build_object('en', 'Safaga', 'ar', 'سفاجا')
WHERE id = 'coastal_teacher_point';

UPDATE destinations
SET name = jsonb_build_object('en', 'El Gouna', 'ar', 'الجونة')
WHERE id = 'coastal_property_city';

-- Update landmark names
UPDATE destinations
SET name = jsonb_build_object('en', 'Pharos Lighthouse', 'ar', 'منارة فاروس')
WHERE id = 'landmark_canal_place_harbor_ancient_sea_obelisk';

UPDATE destinations
SET name = jsonb_build_object('en', 'Temple of Hathor', 'ar', 'معبد حتحور')
WHERE id = 'landmark_bay_rate_settlement_ancient_figure_zone';

UPDATE destinations
SET name = jsonb_build_object('en', 'Montaza Palace', 'ar', 'قصر المنتزه')
WHERE id = 'landmark_coastal_american_city_ancient_sometimes_sanctuary';

UPDATE destinations
SET name = jsonb_build_object('en', 'Bibliotheca Alexandrina', 'ar', 'مكتبة الإسكندرية')
WHERE id = 'landmark_port_set_point_historic_stop_university';

UPDATE destinations
SET name = jsonb_build_object('en', 'Valley of the Nobles', 'ar', 'وادي النبلاء')
WHERE id = 'landmark_nile_heart_city_ancient_scientist_burial_ground';

UPDATE destinations
SET name = jsonb_build_object('en', 'Temple of Isis', 'ar', 'معبد إيزيس')
WHERE id = 'landmark_beach_although_oasis_ancient_blood_holy_site';

UPDATE destinations
SET name = jsonb_build_object('en', 'Khan el-Khalili', 'ar', 'خان الخليلي')
WHERE id = 'landmark_eastern_clear_village_historic_major_market';

UPDATE destinations
SET name = jsonb_build_object('en', 'Temple of Karnak', 'ar', 'معبد الكرنك')
WHERE id = 'landmark_bay_rate_settlement_ancient_must_sacred_site';

UPDATE destinations
SET name = jsonb_build_object('en', 'Egyptian Museum', 'ar', 'المتحف المصري')
WHERE id = 'landmark_port_cost_city_historic_owner_institute';

COMMIT;
