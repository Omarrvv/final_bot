#!/usr/bin/env python3
"""Add sample attraction data using SQL."""
import os

# Create SQL commands to insert data
sql_commands = """
-- Insert sample attractions
INSERT INTO attractions (id, name_en, name_ar, description_en, description_ar, city, location, rating, opening_hours, entrance_fee, tags)
VALUES
('pyr001', 'The Great Pyramids of Giza', 'أهرامات الجيزة', 
 'The Pyramids of Giza are the only surviving structures of the Seven Wonders of the Ancient World.', 
 'أهرامات الجيزة هي الهياكل الوحيدة الباقية من عجائب الدنيا السبع في العالم القديم.',
 'Cairo', '{"lat": 29.9792, "lon": 31.1342}', 4.8, 'Daily 8:00 AM - 5:00 PM', 240, 
 '["ancient", "wonder", "pyramid", "pharaoh", "tomb"]')
ON CONFLICT (id) DO NOTHING;

INSERT INTO attractions (id, name_en, name_ar, description_en, description_ar, city, location, rating, opening_hours, entrance_fee, tags)
VALUES
('mus001', 'The Egyptian Museum', 'المتحف المصري', 
 'The Egyptian Museum houses the world''s largest collection of Pharaonic antiquities.', 
 'المتحف المصري يضم أكبر مجموعة من الآثار الفرعونية في العالم.',
 'Cairo', '{"lat": 30.0478, "lon": 31.2336}', 4.6, 'Daily 9:00 AM - 5:00 PM', 200, 
 '["museum", "antiquities", "pharaoh", "tutankhamun"]')
ON CONFLICT (id) DO NOTHING;

-- Display what's in the database
SELECT id, name_en FROM attractions;
"""

# Save SQL to file
with open('sample_data.sql', 'w') as f:
    f.write(sql_commands)

print("Created SQL file with sample data. Run it with:")
print("docker exec -it egypt-chatbot-wind-cursor-app-1 bash -c 'psql -h db_postgres -U postgres -d egypt_chatbot -f /app/sample_data.sql'")
