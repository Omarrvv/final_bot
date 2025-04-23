#!/usr/bin/env python
"""
Populate Attraction Data

This script populates the SQLite database with sample attraction data
including the Pyramids of Giza, the Great Sphinx, the Egyptian Museum,
and Karnak Temple. This ensures the Knowledge Base has data to work with
when testing queries about Egyptian attractions.
"""

import os
import sys
import json
import logging
import sqlite3
import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('db_populator')

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Default database path
DEFAULT_DB_PATH = os.path.join(project_root, 'data', 'egypt_tourism.db')

# Sample attraction data
SAMPLE_ATTRACTIONS = [
    {
        "id": "pyramids_giza",
        "name_en": "Pyramids of Giza",
        "name_ar": "أهرامات الجيزة",
        "type": "historical",
        "city": "Giza",
        "region": "Cairo",
        "latitude": 29.9792,
        "longitude": 31.1342,
        "description_en": "The Pyramids of Giza are the most iconic ancient structures in Egypt and among the most famous monuments in the world. Built during the Fourth Dynasty of the Egyptian Old Kingdom, they stand as remarkable feats of engineering and architecture. The complex includes the Great Pyramid of Khufu, the Pyramid of Khafre, and the Pyramid of Menkaure, along with associated mortuary temples and smaller pyramids for queens.",
        "description_ar": "أهرامات الجيزة هي أكثر الهياكل القديمة شهرة في مصر ومن بين أشهر المعالم في العالم. بنيت خلال الأسرة الرابعة من المملكة المصرية القديمة، وتقف كإنجازات رائعة في الهندسة والعمارة. يتضمن المجمع الهرم الأكبر لخوفو، وهرم خفرع، وهرم منقرع، إلى جانب معابد جنائزية مرتبطة وأهرامات أصغر للملكات.",
        "data": json.dumps({
            "opening_hours": "8:00 AM - 5:00 PM",
            "ticket_price": {
                "adult": {
                    "foreign": 240,
                    "egyptian": 60
                },
                "student": {
                    "foreign": 120,
                    "egyptian": 30
                },
                "currency": "EGP"
            },
            "best_time_to_visit": "October to April, early morning or late afternoon",
            "tips": [
                "Bring water and sun protection as there's little shade",
                "Comfortable shoes are recommended for walking on sand",
                "Consider hiring a guide for historical context",
                "Be aware of persistent vendors and camel ride offers"
            ],
            "nearby": ["sphinx_giza", "solar_boat_museum", "sound_light_show_giza"],
            "unesco_site": True,
            "construction_date": "c. 2550–2490 BC",
            "height": {
                "great_pyramid": 138.8,
                "unit": "meters"
            }
        }),
        "created_at": datetime.datetime.now().isoformat(),
        "updated_at": datetime.datetime.now().isoformat()
    },
    {
        "id": "sphinx_giza",
        "name_en": "Great Sphinx of Giza",
        "name_ar": "أبو الهول",
        "type": "historical",
        "city": "Giza",
        "region": "Cairo",
        "latitude": 29.9753,
        "longitude": 31.1376,
        "description_en": "The Great Sphinx of Giza is a limestone statue of a mythical creature with the body of a lion and the head of a human, which stands on the Giza Plateau on the west bank of the Nile. It is the oldest known monumental sculpture in Egypt and is commonly believed to have been built by ancient Egyptians of the Old Kingdom during the reign of Khafre (c. 2558–2532 BC).",
        "description_ar": "أبو الهول هو تمثال من الحجر الجيري لمخلوق أسطوري له جسد أسد ورأس إنسان، يقع على هضبة الجيزة على الضفة الغربية لنهر النيل. يعتبر أقدم منحوتة ضخمة معروفة في مصر ويعتقد عادة أنها بنيت من قبل المصريين القدماء في عصر المملكة القديمة خلال فترة حكم خفرع (حوالي 2558-2532 قبل الميلاد).",
        "data": json.dumps({
            "opening_hours": "8:00 AM - 5:00 PM",
            "ticket_price": {
                "info": "Included with Pyramids of Giza ticket"
            },
            "best_time_to_visit": "Early morning or late afternoon",
            "tips": [
                "Visit as part of your Pyramids of Giza tour",
                "The Sphinx is best viewed from the panoramic viewpoint",
                "Photography is allowed but tripods may require permits"
            ],
            "nearby": ["pyramids_giza", "valley_temple", "sound_light_show_giza"],
            "length": 73.5,
            "height": 20.21,
            "unit": "meters",
            "restoration": "Multiple restoration efforts throughout history, most recently in 2020"
        }),
        "created_at": datetime.datetime.now().isoformat(),
        "updated_at": datetime.datetime.now().isoformat()
    },
    {
        "id": "egyptian_museum",
        "name_en": "The Egyptian Museum",
        "name_ar": "المتحف المصري",
        "type": "museum",
        "city": "Cairo",
        "region": "Cairo",
        "latitude": 30.0478,
        "longitude": 31.2336,
        "description_en": "The Egyptian Museum in Cairo contains the world's most extensive collection of pharaonic antiquities. It houses approximately 120,000 items, with a representative amount on display and the remainder in storerooms. The museum's exhibits span from the Predynastic Period to the Greco-Roman Era, with the treasures of Tutankhamun being the most famous collection.",
        "description_ar": "يحتوي المتحف المصري في القاهرة على أكبر مجموعة في العالم من الآثار الفرعونية. يضم حوالي 120,000 قطعة، مع عرض كمية تمثيلية والباقي في غرف التخزين. تمتد معروضات المتحف من عصر ما قبل الأسرات إلى العصر اليوناني الروماني، وتعتبر كنوز توت عنخ آمون المجموعة الأكثر شهرة.",
        "data": json.dumps({
            "opening_hours": "9:00 AM - 5:00 PM, Friday 9:00 AM - 4:00 PM",
            "ticket_price": {
                "adult": {
                    "foreign": 200,
                    "egyptian": 30
                },
                "student": {
                    "foreign": 100,
                    "egyptian": 15
                },
                "mummy_room_extra": 180,
                "currency": "EGP"
            },
            "best_time_to_visit": "Weekday mornings",
            "tips": [
                "Allow at least 3 hours for a proper visit",
                "The Tutankhamun collection is a must-see",
                "Consider hiring a guide to navigate the vast collection",
                "Photography tickets are sold separately"
            ],
            "notable_artifacts": [
                "Tutankhamun's golden mask",
                "Mummy collection",
                "Narmer Palette",
                "Statues of Khafre, Hatshepsut, and Ramesses II"
            ],
            "established": 1902,
            "note": "Many artifacts are being moved to the new Grand Egyptian Museum near Giza"
        }),
        "created_at": datetime.datetime.now().isoformat(),
        "updated_at": datetime.datetime.now().isoformat()
    },
    {
        "id": "karnak_temple",
        "name_en": "Karnak Temple",
        "name_ar": "معبد الكرنك",
        "type": "historical",
        "city": "Luxor",
        "region": "Upper Egypt",
        "latitude": 25.7188,
        "longitude": 32.6571,
        "description_en": "Karnak is a vast temple complex in Luxor, Egypt, that was developed over more than 1,000 years, principally dedicated to the god Amun-Ra. It comprises a vast mix of decayed temples, pylons, chapels, and other buildings, notably the Great Temple of Amun and a massive structure begun by Pharaoh Ramesses II. Karnak is the second most visited historical site in Egypt, after the Pyramids of Giza.",
        "description_ar": "الكرنك هو مجمع معبد ضخم في الأقصر، مصر، تم تطويره على مدى أكثر من 1000 عام، وكان مخصصًا بشكل أساسي للإله آمون رع. يتكون من مزيج واسع من المعابد المتداعية والبوابات والمصليات والمباني الأخرى، لا سيما معبد آمون الكبير والهيكل الضخم الذي بدأه الفرعون رمسيس الثاني. الكرنك هو ثاني أكثر المواقع التاريخية زيارة في مصر بعد أهرامات الجيزة.",
        "data": json.dumps({
            "opening_hours": "6:00 AM - 5:30 PM",
            "ticket_price": {
                "adult": {
                    "foreign": 180,
                    "egyptian": 15
                },
                "student": {
                    "foreign": 90,
                    "egyptian": 5
                },
                "currency": "EGP"
            },
            "best_time_to_visit": "Early morning or late afternoon",
            "tips": [
                "Combine with a visit to Luxor Temple",
                "Sound and Light show in the evening is worth attending",
                "Wear a hat and bring water as there's little shade",
                "Allow at least 2-3 hours to explore the complex"
            ],
            "notable_features": [
                "Hypostyle Hall",
                "Great Temple of Amun",
                "Sacred Lake",
                "Avenue of Sphinxes"
            ],
            "unesco_site": True,
            "construction_period": "c. 2055 BC to around 100 AD",
            "sound_and_light_show": {
                "times": "Multiple showings nightly",
                "languages": ["Arabic", "English", "French", "German", "Spanish"],
                "duration": "1 hour 15 minutes"
            }
        }),
        "created_at": datetime.datetime.now().isoformat(),
        "updated_at": datetime.datetime.now().isoformat()
    }
]

def create_database_structure(db_path):
    """Create the database structure if it doesn't exist."""
    logger.info(f"Setting up database at {db_path}")
    
    # Create data directory if it doesn't exist
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Connect to the database (creates it if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create attractions table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attractions (
        id TEXT PRIMARY KEY,
        name_en TEXT NOT NULL,
        name_ar TEXT,
        type TEXT,
        city TEXT,
        region TEXT,
        latitude REAL,
        longitude REAL,
        description_en TEXT,
        description_ar TEXT,
        data TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("✅ Database structure created successfully")

def populate_attractions(db_path, attractions_data):
    """Populate the attractions table with the provided data."""
    logger.info(f"Populating attractions table with {len(attractions_data)} entries")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if there are existing entries and clear them if needed
    cursor.execute("SELECT COUNT(*) FROM attractions")
    count = cursor.fetchone()[0]
    
    if count > 0:
        logger.warning(f"Found {count} existing attractions in the database")
        cursor.execute("DELETE FROM attractions")
        logger.info("Cleared existing attractions data")
    
    # Insert the attraction data
    for attraction in attractions_data:
        cursor.execute('''
        INSERT INTO attractions (
            id, name_en, name_ar, type, city, region, 
            latitude, longitude, description_en, description_ar,
            data, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            attraction['id'],
            attraction['name_en'],
            attraction['name_ar'],
            attraction['type'],
            attraction['city'],
            attraction['region'],
            attraction['latitude'],
            attraction['longitude'],
            attraction['description_en'],
            attraction['description_ar'],
            attraction['data'],
            attraction['created_at'],
            attraction['updated_at']
        ))
    
    conn.commit()
    conn.close()
    logger.info("✅ Attractions data populated successfully")

def verify_data(db_path):
    """Verify that the attraction data was successfully added."""
    logger.info("Verifying data in the database")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check attraction count
    cursor.execute("SELECT COUNT(*) FROM attractions")
    count = cursor.fetchone()[0]
    
    if count == len(SAMPLE_ATTRACTIONS):
        logger.info(f"✅ Verified {count} attractions in the database")
    else:
        logger.error(f"❌ Verification failed: Found {count} attractions, expected {len(SAMPLE_ATTRACTIONS)}")
    
    # Check for Pyramids of Giza specifically
    cursor.execute("SELECT id, name_en FROM attractions WHERE id = 'pyramids_giza'")
    result = cursor.fetchone()
    
    if result:
        logger.info(f"✅ Verified 'Pyramids of Giza' exists in the database (ID: {result[0]})")
    else:
        logger.error("❌ Verification failed: 'Pyramids of Giza' not found in the database")
    
    conn.close()
    return count == len(SAMPLE_ATTRACTIONS)

def run(db_path=DEFAULT_DB_PATH):
    """Run the database population process."""
    logger.info("Starting database population process")
    
    try:
        # Create the database structure
        create_database_structure(db_path)
        
        # Populate the attractions
        populate_attractions(db_path, SAMPLE_ATTRACTIONS)
        
        # Verify the data
        verification = verify_data(db_path)
        
        if verification:
            logger.info("\n=== Database Population Summary ===")
            logger.info(f"Database: {db_path}")
            logger.info(f"Attractions: {len(SAMPLE_ATTRACTIONS)}")
            logger.info("\n✅ Database successfully populated with sample attraction data!")
            logger.info("You can now run test_kb_connection.py to test the Knowledge Base connection")
            return True
        else:
            logger.error("\n❌ Database population completed with verification errors")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error during database population: {e}")
        return False

if __name__ == "__main__":
    # Check if a custom database path was provided
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
        success = run(db_path)
    else:
        success = run()
    
    sys.exit(0 if success else 1) 