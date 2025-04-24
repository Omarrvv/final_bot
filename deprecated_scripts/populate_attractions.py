#!/usr/bin/env python
"""
Script to populate the attractions table with Egyptian tourism data.
This script inserts or updates attraction data in the database.
"""

import os
import sys
import json
import logging
import datetime
from typing import Dict, List, Any, Optional

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import project modules
from src.utils.database import DatabaseManager
from src.utils.postgres_database import PostgresqlDatabaseManager
from src.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('populate_attractions')

# Define attractions data
ATTRACTIONS = [
    {
        "id": "pyramids_giza",
        "name_en": "Pyramids of Giza",
        "name_ar": "أهرامات الجيزة",
        "type": "historical",
        "city": "Giza",
        "region": "Cairo Governorate",
        "latitude": 29.9792,
        "longitude": 31.1342,
        "description_en": "The Pyramids of Giza are ancient Egyptian pyramids located on the Giza plateau, on the outskirts of Cairo. They include the Great Pyramid of Giza, which is one of the Seven Wonders of the Ancient World and the only one still largely intact. The pyramids were built as tombs for the country's pharaohs during the Old and Middle Kingdom periods.",
        "description_ar": "أهرامات الجيزة هي أهرامات مصرية قديمة تقع على هضبة الجيزة، على مشارف القاهرة. تشمل الهرم الأكبر في الجيزة، وهو إحدى عجائب الدنيا السبع القديمة والوحيد الذي لا يزال سليماً إلى حد كبير. بنيت الأهرامات كمقابر لفراعنة البلاد خلال فترات المملكة القديمة والوسطى.",
        "data": {
            "opening_hours": "8:00 AM - 5:00 PM",
            "ticket_price": {
                "adult": 240,
                "child": 120,
                "student": 120,
                "currency": "EGP"
            },
            "facilities": ["Restrooms", "Gift shops", "Tour guides", "Camel rides"],
            "best_time_to_visit": "Early morning or late afternoon",
            "history": "Built during the Fourth Dynasty of the Old Kingdom of Ancient Egypt, around 2560 BCE",
            "highlights": [
                "The Great Pyramid of Khufu",
                "The Pyramid of Khafre",
                "The Pyramid of Menkaure",
                "The Great Sphinx"
            ],
            "facts": [
                "The Great Pyramid was the tallest man-made structure in the world for more than 3,800 years",
                "The Great Pyramid consists of an estimated 2.3 million blocks",
                "The pyramids are precisely aligned with the stars"
            ],
            "images": [
                "pyramids_giza_1.jpg",
                "pyramids_giza_2.jpg",
                "pyramids_giza_3.jpg"
            ]
        }
    },
    {
        "id": "valley_kings",
        "name_en": "Valley of the Kings",
        "name_ar": "وادي الملوك",
        "type": "historical",
        "city": "Luxor",
        "region": "Luxor Governorate",
        "latitude": 25.7402,
        "longitude": 32.6014,
        "description_en": "The Valley of the Kings is a valley in Egypt where, for a period of nearly 500 years, rock-cut tombs were excavated for the pharaohs and powerful nobles of the New Kingdom. The valley stands on the west bank of the Nile, opposite Thebes (modern Luxor), within the heart of the Theban Necropolis.",
        "description_ar": "وادي الملوك هو وادٍ في مصر حيث، لفترة تقارب 500 عام، تم حفر مقابر صخرية للفراعنة والنبلاء الأقوياء في المملكة الحديثة. يقع الوادي على الضفة الغربية للنيل، مقابل طيبة (الأقصر الحديثة)، في قلب جبانة طيبة.",
        "data": {
            "opening_hours": "6:00 AM - 5:00 PM",
            "ticket_price": {
                "adult": 240,
                "child": 120,
                "student": 120,
                "currency": "EGP"
            },
            "facilities": ["Restrooms", "Gift shops", "Tour guides", "Tram service"],
            "best_time_to_visit": "Early morning",
            "history": "Used primarily between the 16th to 11th century BCE",
            "highlights": [
                "Tomb of Tutankhamun (KV62)",
                "Tomb of Ramesses VI (KV9)",
                "Tomb of Seti I (KV17)",
                "Tomb of Ramesses III (KV11)"
            ],
            "facts": [
                "Contains at least 63 tombs and chambers",
                "Tutankhamun's tomb was discovered largely intact in 1922",
                "Many tombs feature colorful wall paintings depicting Egyptian mythology"
            ],
            "images": [
                "valley_kings_1.jpg",
                "valley_kings_2.jpg",
                "valley_kings_3.jpg"
            ]
        }
    },
    {
        "id": "karnak_temple",
        "name_en": "Karnak Temple Complex",
        "name_ar": "معبد الكرنك",
        "type": "historical",
        "city": "Luxor",
        "region": "Luxor Governorate",
        "latitude": 25.7188,
        "longitude": 32.6571,
        "description_en": "The Karnak Temple Complex comprises a vast mix of decayed temples, chapels, pylons, and other buildings near Luxor, Egypt. It is part of the monumental city of Thebes. The area around Karnak was the ancient Egyptian Ipet-isut ('The Most Selected of Places') and the main place of worship of the Theban Triad.",
        "description_ar": "مجمع معبد الكرنك يضم مزيجًا واسعًا من المعابد المتداعية والكنائس والبوابات والمباني الأخرى بالقرب من الأقصر، مصر. وهو جزء من مدينة طيبة الأثرية. كانت المنطقة المحيطة بالكرنك هي المنطقة المصرية القديمة إيبت-إيسوت ('أكثر الأماكن اختيارًا') والمكان الرئيسي لعبادة ثالوث طيبة.",
        "data": {
            "opening_hours": "6:00 AM - 5:30 PM",
            "ticket_price": {
                "adult": 200,
                "child": 100,
                "student": 100,
                "currency": "EGP"
            },
            "facilities": ["Restrooms", "Gift shops", "Tour guides", "Sound and light show"],
            "best_time_to_visit": "Early morning or late afternoon",
            "history": "Temple construction began during the reign of Senusret I in the Middle Kingdom",
            "highlights": [
                "Great Hypostyle Hall",
                "Great Temple of Amun",
                "Temple of Khonsu",
                "Sacred Lake"
            ],
            "facts": [
                "The largest religious building ever constructed",
                "Features the world's largest collection of Egyptian temple architecture",
                "Construction and expansion occurred over 2,000 years"
            ],
            "images": [
                "karnak_temple_1.jpg",
                "karnak_temple_2.jpg",
                "karnak_temple_3.jpg"
            ]
        }
    },
    {
        "id": "sphinx_giza",
        "name_en": "Great Sphinx of Giza",
        "name_ar": "أبو الهول",
        "type": "historical",
        "city": "Giza",
        "region": "Cairo Governorate",
        "latitude": 29.9753,
        "longitude": 31.1376,
        "description_en": "The Great Sphinx of Giza is a limestone statue of a reclining sphinx, a mythical creature with the head of a human and the body of a lion. It stands on the Giza Plateau on the west bank of the Nile in Giza, Egypt, and is believed to have been built during the reign of Khafre (c. 2558–2532 BC).",
        "description_ar": "أبو الهول العظيم بالجيزة هو تمثال من الحجر الجيري لأبو الهول المستلقي، وهو مخلوق أسطوري برأس إنسان وجسد أسد. يقع في هضبة الجيزة على الضفة الغربية للنيل في الجيزة، مصر، ويعتقد أنه بني خلال عهد خفرع (حوالي 2558-2532 قبل الميلاد).",
        "data": {
            "opening_hours": "8:00 AM - 5:00 PM",
            "ticket_price": {
                "adult": 80,
                "child": 40,
                "student": 40,
                "currency": "EGP"
            },
            "facilities": ["Restrooms", "Gift shops", "Tour guides"],
            "best_time_to_visit": "Early morning or late afternoon",
            "history": "Built during the reign of Pharaoh Khafre (c. 2558-2532 BCE)",
            "highlights": [
                "The face of the Sphinx",
                "The Dream Stele between the paws",
                "Panoramic view with pyramids in background"
            ],
            "facts": [
                "It is the oldest known monumental sculpture in Egypt",
                "The Sphinx is 73.5 meters (241 ft) long and 20.22 meters (66.34 ft) high",
                "The nose is missing, believed to have been broken off at some point in history"
            ],
            "images": [
                "sphinx_giza_1.jpg",
                "sphinx_giza_2.jpg",
                "sphinx_giza_3.jpg"
            ]
        }
    },
    {
        "id": "alexandria_library",
        "name_en": "Library of Alexandria",
        "name_ar": "مكتبة الإسكندرية",
        "type": "cultural",
        "city": "Alexandria",
        "region": "Alexandria Governorate",
        "latitude": 31.2088,
        "longitude": 29.9092,
        "description_en": "The Bibliotheca Alexandrina is a major library and cultural center located on the shore of the Mediterranean Sea in the Egyptian city of Alexandria. It is a commemoration of the Library of Alexandria that was lost in antiquity and an attempt to rekindle the brilliance that this earlier center of study and learning represented.",
        "description_ar": "مكتبة الإسكندرية هي مكتبة رئيسية ومركز ثقافي يقع على شاطئ البحر المتوسط في مدينة الإسكندرية المصرية. وهي إحياء لذكرى مكتبة الإسكندرية التي فقدت في العصور القديمة ومحاولة لإعادة إشعال التألق الذي مثله هذا المركز السابق للدراسة والتعلم.",
        "data": {
            "opening_hours": "10:00 AM - 7:00 PM (Sat-Thu), 2:00 PM - 7:00 PM (Fri)",
            "ticket_price": {
                "adult": 70,
                "child": 35,
                "student": 35,
                "currency": "EGP"
            },
            "facilities": ["Restrooms", "Cafeteria", "Bookshop", "Exhibition spaces", "Planetarium", "Museums"],
            "best_time_to_visit": "Weekday mornings",
            "history": "Inaugurated in 2002 as a revival of the ancient Library of Alexandria",
            "highlights": [
                "Main reading room with cascading levels",
                "Planetarium Science Center",
                "Manuscript Museum",
                "Antiquities Museum",
                "Digital archives"
            ],
            "facts": [
                "Can hold up to 8 million books",
                "The main reading room covers 70,000 square meters on 11 cascading levels",
                "The exterior walls are carved with characters from 120 different human scripts"
            ],
            "images": [
                "alexandria_library_1.jpg",
                "alexandria_library_2.jpg",
                "alexandria_library_3.jpg"
            ]
        }
    }
]

def get_database_manager():
    """Get the appropriate database manager based on settings."""
    if settings.use_postgres:
        logger.info("Using PostgreSQL database manager")
        return PostgresqlDatabaseManager()
    else:
        logger.info("Using SQLite database manager")
        return DatabaseManager()

def insert_attraction(db_manager, attraction: Dict[str, Any]):
    """Insert or update an attraction in the database."""
    try:
        # Check if attraction exists
        existing = db_manager.execute_query(
            "SELECT id FROM attractions WHERE id = ?",
            (attraction["id"],)
        )
        
        now = datetime.datetime.now().isoformat()
        
        if existing:
            logger.info(f"Updating attraction: {attraction['name_en']}")
            # Convert data dictionary to JSON string
            data_json = json.dumps(attraction["data"])
            
            # Update existing attraction
            db_manager.execute_update(
                """
                UPDATE attractions
                SET name_en = ?, name_ar = ?, type = ?, city = ?, region = ?,
                    latitude = ?, longitude = ?, description_en = ?, description_ar = ?,
                    data = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    attraction["name_en"], attraction["name_ar"], attraction["type"],
                    attraction["city"], attraction["region"], attraction["latitude"],
                    attraction["longitude"], attraction["description_en"], attraction["description_ar"],
                    data_json, now, attraction["id"]
                )
            )
        else:
            logger.info(f"Inserting new attraction: {attraction['name_en']}")
            # Convert data dictionary to JSON string
            data_json = json.dumps(attraction["data"])
            
            # Insert new attraction
            db_manager.execute_update(
                """
                INSERT INTO attractions (
                    id, name_en, name_ar, type, city, region, latitude, longitude,
                    description_en, description_ar, data, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    attraction["id"], attraction["name_en"], attraction["name_ar"],
                    attraction["type"], attraction["city"], attraction["region"],
                    attraction["latitude"], attraction["longitude"], attraction["description_en"],
                    attraction["description_ar"], data_json, now, now
                )
            )
            
            # If PostgreSQL is being used, update the geometry column
            if settings.use_postgres and isinstance(db_manager, PostgresqlDatabaseManager):
                db_manager.execute_update(
                    """
                    UPDATE attractions
                    SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
                    WHERE id = ?
                    """,
                    (attraction["id"],)
                )
                
        return True
    except Exception as e:
        logger.error(f"Error inserting/updating attraction {attraction['name_en']}: {str(e)}")
        return False

def main():
    """Main function to populate attractions data."""
    logger.info("Starting attractions data population")
    
    # Get the appropriate database manager
    db_manager = get_database_manager()
    
    # Connect to the database
    try:
        db_manager.connect()
        logger.info("Connected to database successfully")
        
        # Insert or update each attraction
        success_count = 0
        for attraction in ATTRACTIONS:
            if insert_attraction(db_manager, attraction):
                success_count += 1
        
        logger.info(f"Successfully processed {success_count}/{len(ATTRACTIONS)} attractions")
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
    finally:
        # Disconnect from the database
        db_manager.disconnect()
        logger.info("Disconnected from database")

if __name__ == "__main__":
    main() 