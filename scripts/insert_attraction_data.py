#!/usr/bin/env python
"""
Script to insert attraction data, including Pyramids of Giza, into the database.
Supports both SQLite and PostgreSQL databases.
"""

import os
import sys
import json
import logging
import datetime
import argparse
from typing import Dict, List, Any, Optional

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import project modules
from src.utils.database import DatabaseManager
from src.utils.postgres_database import PostgresqlDatabaseManager
from src.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('insert_attraction_data')

# Sample attraction data
ATTRACTION_DATA = [
    {
        "id": "pyramids_giza",
        "name_en": "Pyramids of Giza",
        "name_ar": "أهرامات الجيزة",
        "type": "historical",
        "city": "Giza",
        "region": "Cairo",
        "latitude": 29.9792,
        "longitude": 31.1342,
        "description_en": (
            "The Pyramids of Giza are the most iconic monuments of ancient Egypt and the only surviving "
            "structures of the Seven Wonders of the Ancient World. Located on the outskirts of Cairo, this "
            "ancient complex includes the Great Pyramid of Khufu (Cheops), the Pyramid of Khafre (Chephren), "
            "and the Pyramid of Menkaure (Mycerinus), along with the Great Sphinx. Built during the Fourth "
            "Dynasty of the Old Kingdom of Ancient Egypt (around 2580-2560 BCE), the Great Pyramid was the "
            "tallest man-made structure in the world for nearly 4,000 years. Visitors can explore the exterior "
            "of these massive structures and even enter some of the pyramids to view the burial chambers."
        ),
        "description_ar": (
            "أهرامات الجيزة هي أشهر معالم مصر القديمة والهياكل الوحيدة الباقية من عجائب الدنيا السبع في العالم "
            "القديم. تقع في ضواحي القاهرة، وتشمل هرم خوفو الأكبر (خيوبس)، وهرم خفرع (خفرن)، وهرم منقرع (ميسرينوس)، "
            "إلى جانب تمثال أبو الهول العظيم. تم بناء الهرم الأكبر خلال الأسرة الرابعة من المملكة القديمة لمصر "
            "القديمة (حوالي 2580-2560 قبل الميلاد)، وكان أطول هيكل من صنع الإنسان في العالم لما يقرب من 4000 عام. "
            "يمكن للزوار استكشاف الهياكل الخارجية لهذه الأهرامات الضخمة وحتى دخول بعض الأهرامات لمشاهدة غرف الدفن."
        ),
        "data": {
            "opening_hours": "8:00 AM - 5:00 PM daily",
            "ticket_price": {
                "foreign_adult": "400 EGP",
                "foreign_student": "200 EGP",
                "egyptian_adult": "60 EGP",
                "egyptian_student": "30 EGP"
            },
            "best_time_to_visit": "Early morning or late afternoon to avoid crowds and heat",
            "facilities": ["Restrooms", "Cafeteria", "Parking", "Camel rides", "Horse rides"],
            "tips": [
                "Bring water and sun protection",
                "Wear comfortable shoes",
                "Be aware of aggressive vendors",
                "Consider hiring a guide for historical context"
            ],
            "nearby_attractions": ["Great Sphinx", "Solar Boat Museum", "Sound and Light Show"],
            "facts": [
                "The Great Pyramid contains an estimated 2.3 million stone blocks",
                "Each block weighs 2.5 to 15 tons",
                "The pyramids were built as tombs for the pharaohs and their consorts",
                "The Great Sphinx is believed to represent Pharaoh Khafre"
            ],
            "photo_urls": [
                "pyramids_giza_1.jpg",
                "pyramids_giza_2.jpg",
                "pyramids_giza_3.jpg"
            ]
        }
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
        "description_en": (
            "The Great Sphinx of Giza is a limestone statue of a reclining sphinx, a mythical creature with "
            "the body of a lion and the head of a human. Facing directly from west to east, it stands on the "
            "Giza Plateau on the west bank of the Nile in Giza, Egypt. The face of the Sphinx is generally "
            "believed to represent the pharaoh Khafre. Cut from the bedrock, the original shape of the Sphinx "
            "has been restored with layers of limestone blocks. It is the oldest known monumental sculpture in "
            "Egypt and is commonly believed to have been built by ancient Egyptians of the Old Kingdom during "
            "the reign of the pharaoh Khafre (c. 2558–2532 BCE)."
        ),
        "description_ar": (
            "أبو الهول العظيم في الجيزة هو تمثال من الحجر الجيري لأبو الهول المستلقي، وهو مخلوق أسطوري بجسم أسد "
            "ورأس إنسان. يقف مواجهًا مباشرة من الغرب إلى الشرق على هضبة الجيزة على الضفة الغربية للنيل في الجيزة، "
            "مصر. يُعتقد بشكل عام أن وجه أبو الهول يمثل الفرعون خفرع. تم نحته من صخور الأساس، وتمت استعادة الشكل "
            "الأصلي لأبو الهول بطبقات من كتل الحجر الجيري. وهو أقدم منحوتة ضخمة معروفة في مصر ويُعتقد بشكل شائع "
            "أنها بُنيت من قبل المصريين القدماء في المملكة القديمة خلال فترة حكم الفرعون خفرع (حوالي 2558-2532 قبل الميلاد)."
        ),
        "data": {
            "opening_hours": "8:00 AM - 5:00 PM daily",
            "ticket_price": "Included with Pyramids of Giza ticket",
            "best_time_to_visit": "Early morning or late afternoon",
            "facts": [
                "The Sphinx is about 73.5 meters (241 ft) long and 20.22 meters (66.3 ft) high",
                "It is the largest monolithic statue in the world",
                "The Sphinx has lost its nose, possibly due to erosion or deliberate vandalism",
                "Napoleon's soldiers have been blamed for shooting off the nose, but drawings from before Napoleon's time show the Sphinx without a nose"
            ],
            "photo_urls": [
                "sphinx_giza_1.jpg",
                "sphinx_giza_2.jpg"
            ]
        }
    },
    {
        "id": "egyptian_museum",
        "name_en": "Egyptian Museum",
        "name_ar": "المتحف المصري",
        "type": "museum",
        "city": "Cairo",
        "region": "Cairo",
        "latitude": 30.0478,
        "longitude": 31.2336,
        "description_en": (
            "The Museum of Egyptian Antiquities, known commonly as the Egyptian Museum or the Cairo Museum, "
            "is home to an extensive collection of ancient Egyptian antiquities. It has 120,000 items, with a "
            "representative amount on display and the remainder in storerooms. The museum's collection includes "
            "the treasures of Tutankhamun, including his golden mask, as well as mummies and artifacts spanning "
            "over 5,000 years of Egyptian history. Built in 1901, the pink, domed building is itself a historic "
            "treasure, though many artifacts are being transferred to the new Grand Egyptian Museum near the "
            "Pyramids of Giza."
        ),
        "description_ar": (
            "متحف الآثار المصرية، المعروف عمومًا باسم المتحف المصري أو متحف القاهرة، هو موطن لمجموعة واسعة من "
            "الآثار المصرية القديمة. يضم 120,000 قطعة، مع عرض كمية تمثيلية والباقي في المخازن. تشمل مجموعة المتحف "
            "كنوز توت عنخ آمون، بما في ذلك قناعه الذهبي، بالإضافة إلى المومياوات والقطع الأثرية التي تمتد لأكثر من "
            "5000 عام من التاريخ المصري. تم بناء المبنى الوردي ذو القبة في عام 1901، وهو نفسه كنز تاريخي، على الرغم "
            "من أن العديد من القطع الأثرية يتم نقلها إلى المتحف المصري الكبير الجديد بالقرب من أهرامات الجيزة."
        ),
        "data": {
            "opening_hours": "9:00 AM - 5:00 PM daily",
            "ticket_price": {
                "foreign_adult": "200 EGP",
                "foreign_student": "100 EGP",
                "egyptian_adult": "30 EGP",
                "egyptian_student": "10 EGP",
                "mummy_room": "+180 EGP"
            },
            "best_time_to_visit": "Weekday mornings",
            "facilities": ["Restrooms", "Gift shop", "Cafeteria"],
            "highlights": [
                "Tutankhamun's golden mask and treasures",
                "Royal mummies",
                "Narmer Palette",
                "Statue of Khafre",
                "Statue of Djoser"
            ],
            "tips": [
                "Allow at least 3 hours for a visit",
                "Consider hiring a guide",
                "Photography pass required for cameras"
            ],
            "photo_urls": [
                "egyptian_museum_1.jpg",
                "egyptian_museum_2.jpg"
            ]
        }
    }
]

def initialize_db_manager(use_postgres: bool = False) -> Any:
    """Initialize the appropriate database manager based on settings."""
    if use_postgres:
        logger.info("Using PostgreSQL database...")
        return PostgresqlDatabaseManager()
    else:
        logger.info("Using SQLite database...")
        return DatabaseManager()

def check_attraction_exists(db_manager: Any, attraction_id: str) -> bool:
    """Check if an attraction with the given ID already exists in the database."""
    try:
        if hasattr(db_manager, 'execute_query'):
            # PostgreSQL implementation
            query = "SELECT COUNT(*) FROM attractions WHERE id = %s"
            result = db_manager.execute_query(query, (attraction_id,))
            count = result[0][0] if result else 0
        else:
            # SQLite implementation
            query = "SELECT COUNT(*) FROM attractions WHERE id = ?"
            result = db_manager.conn.execute(query, (attraction_id,)).fetchone()
            count = result[0] if result else 0
            
        return count > 0
    except Exception as e:
        logger.error(f"Error checking if attraction exists: {str(e)}")
        return False

def insert_attraction(db_manager: Any, attraction: Dict[str, Any]) -> bool:
    """Insert an attraction into the database."""
    try:
        # Check if attraction already exists
        if check_attraction_exists(db_manager, attraction["id"]):
            logger.info(f"Attraction '{attraction['name_en']}' already exists. Skipping...")
            return False
            
        now = datetime.datetime.utcnow().isoformat()
        
        # Convert data dictionary to JSON string
        data_json = json.dumps(attraction["data"])
        
        if hasattr(db_manager, 'execute_query'):
            # PostgreSQL implementation
            query = """
                INSERT INTO attractions 
                (id, name_en, name_ar, type, city, region, latitude, longitude, 
                description_en, description_ar, data, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            # Convert data to JSONB for PostgreSQL
            if isinstance(data_json, str):
                data_json = data_json  # PostgreSQL will handle the conversion
                
            db_manager.execute_query(
                query, 
                (
                    attraction["id"], 
                    attraction["name_en"], 
                    attraction["name_ar"], 
                    attraction["type"],
                    attraction["city"], 
                    attraction["region"], 
                    attraction["latitude"], 
                    attraction["longitude"],
                    attraction["description_en"], 
                    attraction["description_ar"], 
                    data_json, 
                    now, 
                    now
                )
            )
            
            # Add geospatial point if PostgreSQL
            if "latitude" in attraction and "longitude" in attraction:
                try:
                    geom_query = """
                        UPDATE attractions 
                        SET geom = ST_SetSRID(ST_MakePoint(%s, %s), 4326)
                        WHERE id = %s
                    """
                    db_manager.execute_query(
                        geom_query, 
                        (attraction["longitude"], attraction["latitude"], attraction["id"])
                    )
                except Exception as e:
                    logger.warning(f"Could not update geom field (PostGIS might not be enabled): {str(e)}")
        else:
            # SQLite implementation
            query = """
                INSERT INTO attractions 
                (id, name_en, name_ar, type, city, region, latitude, longitude, 
                description_en, description_ar, data, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            db_manager.conn.execute(
                query, 
                (
                    attraction["id"], 
                    attraction["name_en"], 
                    attraction["name_ar"], 
                    attraction["type"],
                    attraction["city"], 
                    attraction["region"], 
                    attraction["latitude"], 
                    attraction["longitude"],
                    attraction["description_en"], 
                    attraction["description_ar"], 
                    data_json, 
                    now, 
                    now
                )
            )
            db_manager.conn.commit()
        
        logger.info(f"✅ Successfully inserted attraction: '{attraction['name_en']}'")
        return True
    except Exception as e:
        logger.error(f"❌ Error inserting attraction '{attraction.get('name_en', 'Unknown')}': {str(e)}")
        return False

def load_attractions_from_json(json_file: str) -> List[Dict[str, Any]]:
    """Load attraction data from a JSON file."""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "attractions" in data:
            return data["attractions"]
        else:
            logger.error(f"Invalid JSON format in {json_file}")
            return []
    except Exception as e:
        logger.error(f"Error loading attractions from JSON: {str(e)}")
        return []

def insert_attractions(db_manager: Any, attractions: List[Dict[str, Any]]) -> int:
    """Insert multiple attractions into the database."""
    success_count = 0
    
    for attraction in attractions:
        if insert_attraction(db_manager, attraction):
            success_count += 1
    
    return success_count

def verify_attraction_data(db_manager: Any, attraction_id: str) -> Dict[str, Any]:
    """Verify that an attraction exists in the database and return its data."""
    try:
        if hasattr(db_manager, 'execute_query'):
            # PostgreSQL implementation
            query = "SELECT * FROM attractions WHERE id = %s"
            result = db_manager.execute_query(query, (attraction_id,))
            if result:
                columns = [desc[0] for desc in db_manager.cursor.description]
                return dict(zip(columns, result[0]))
        else:
            # SQLite implementation
            query = "SELECT * FROM attractions WHERE id = ?"
            cursor = db_manager.conn.execute(query, (attraction_id,))
            result = cursor.fetchone()
            if result:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, result))
        
        return {}
    except Exception as e:
        logger.error(f"Error verifying attraction data: {str(e)}")
        return {}

def main():
    """Main function to insert attraction data into the database."""
    parser = argparse.ArgumentParser(description="Insert attraction data into the database.")
    parser.add_argument('--postgres', action='store_true', help='Use PostgreSQL database')
    parser.add_argument('--json-file', type=str, help='JSON file containing attraction data')
    parser.add_argument('--verify', action='store_true', help='Verify data after insertion')
    args = parser.parse_args()
    
    # Determine which database to use
    use_postgres = args.postgres or settings.use_postgres
    db_manager = initialize_db_manager(use_postgres)
    
    # Load attractions from JSON file or use default data
    if args.json_file:
        attractions = load_attractions_from_json(args.json_file)
        if not attractions:
            logger.error("Failed to load attractions from JSON. Using default data.")
            attractions = ATTRACTION_DATA
    else:
        attractions = ATTRACTION_DATA
    
    # Insert attractions
    logger.info(f"Inserting {len(attractions)} attractions into the database...")
    success_count = insert_attractions(db_manager, attractions)
    logger.info(f"Successfully inserted {success_count} out of {len(attractions)} attractions.")
    
    # Verify data
    if args.verify:
        logger.info("\nVerifying inserted data...")
        for attraction in attractions:
            data = verify_attraction_data(db_manager, attraction["id"])
            if data:
                logger.info(f"✅ Verified attraction: '{data.get('name_en', 'Unknown')}'")
            else:
                logger.error(f"❌ Could not verify attraction: '{attraction.get('name_en', 'Unknown')}'")
    
    logger.info("Done!")

if __name__ == "__main__":
    main() 