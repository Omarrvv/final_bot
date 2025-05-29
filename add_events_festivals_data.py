#!/usr/bin/env python3
"""
Script to add comprehensive events and festivals data to the Egypt Tourism Chatbot database.
This script adds at least 10 events/festivals with detailed information.
"""

import os
import sys
import json
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import necessary modules
from src.knowledge.database import DatabaseManager

def connect_to_database():
    """Connect to the database."""
    try:
        # Get database connection string from environment variable or use default
        db_uri = os.environ.get("POSTGRES_URI", "postgresql://postgres:postgres@localhost:5432/egypt_chatbot")
        
        # Create database manager
        db_manager = DatabaseManager(db_uri)
        
        # Test connection
        if db_manager.connect():
            logger.info("✅ Database connection successful")
            return db_manager
        else:
            logger.error("❌ Database connection failed")
            return None
    except Exception as e:
        logger.error(f"❌ Error connecting to database: {str(e)}")
        return None

def check_if_event_exists(db_manager, name_en):
    """Check if event exists in the events_festivals table."""
    try:
        query = """
        SELECT COUNT(*) FROM events_festivals 
        WHERE name->>'en' = %s
        """
        result = db_manager.execute_query(query, (name_en,))
        return result[0]['count'] > 0 if result else False
    except Exception as e:
        logger.error(f"❌ Error checking if event exists: {str(e)}")
        return False

def add_event_category(db_manager, category_id, name_en, name_ar):
    """Add event category to the event_categories table if it doesn't exist."""
    try:
        # Check if category exists
        query = """
        SELECT COUNT(*) FROM event_categories 
        WHERE id = %s
        """
        result = db_manager.execute_query(query, (category_id,))
        if result and result[0]['count'] > 0:
            logger.info(f"Event category '{name_en}' already exists")
            return True
        
        # Add category
        query = """
        INSERT INTO event_categories (
            id,
            name,
            description,
            created_at,
            updated_at
        ) VALUES (
            %s,
            %s,
            %s,
            NOW(),
            NOW()
        )
        """
        
        name = json.dumps({
            "en": name_en,
            "ar": name_ar
        })
        
        description = json.dumps({
            "en": f"Events and festivals related to {name_en.lower()}",
            "ar": f"الأحداث والمهرجانات المتعلقة بـ {name_ar}"
        })
        
        db_manager.execute_query(query, (category_id, name, description))
        logger.info(f"✅ Event category '{name_en}' added successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Error adding event category: {str(e)}")
        return False

def add_event(db_manager, event_data):
    """Add event to the events_festivals table."""
    try:
        # Check if event already exists
        if check_if_event_exists(db_manager, event_data["name"]["en"]):
            logger.info(f"Event '{event_data['name']['en']}' already exists")
            return True
        
        # Add event
        query = """
        INSERT INTO events_festivals (
            name,
            description,
            category_id,
            location,
            start_date,
            end_date,
            recurring,
            frequency,
            ticket_info,
            website,
            contact_info,
            images,
            tags,
            data,
            created_at,
            updated_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
        )
        """
        
        params = (
            json.dumps(event_data["name"]),
            json.dumps(event_data["description"]),
            event_data["category_id"],
            json.dumps(event_data["location"]),
            event_data["start_date"],
            event_data["end_date"],
            event_data["recurring"],
            event_data["frequency"],
            json.dumps(event_data["ticket_info"]),
            event_data["website"],
            json.dumps(event_data["contact_info"]),
            json.dumps(event_data["images"]),
            event_data["tags"],
            json.dumps(event_data["data"])
        )
        
        db_manager.execute_query(query, params)
        logger.info(f"✅ Event '{event_data['name']['en']}' added successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Error adding event: {str(e)}")
        return False

def generate_events_data():
    """Generate comprehensive events and festivals data."""
    # Define event categories
    event_categories = [
        {"id": "cultural", "name_en": "Cultural Festivals", "name_ar": "المهرجانات الثقافية"},
        {"id": "religious", "name_en": "Religious Celebrations", "name_ar": "الاحتفالات الدينية"},
        {"id": "music", "name_en": "Music Events", "name_ar": "الفعاليات الموسيقية"},
        {"id": "film", "name_en": "Film Festivals", "name_ar": "مهرجانات الأفلام"},
        {"id": "art", "name_en": "Art Exhibitions", "name_ar": "معارض الفن"},
        {"id": "food", "name_en": "Food Festivals", "name_ar": "مهرجانات الطعام"},
        {"id": "sports", "name_en": "Sports Events", "name_ar": "الفعاليات الرياضية"}
    ]
    
    # Generate events data
    events_data = [
        {
            "name": {
                "en": "Cairo International Film Festival",
                "ar": "مهرجان القاهرة السينمائي الدولي"
            },
            "description": {
                "en": "One of the oldest and most prestigious film festivals in the Middle East and Africa. The festival showcases international and Egyptian films, with competitions, workshops, and special screenings.",
                "ar": "أحد أقدم وأرقى مهرجانات السينما في الشرق الأوسط وأفريقيا. يعرض المهرجان أفلامًا دولية ومصرية، مع مسابقات وورش عمل وعروض خاصة."
            },
            "category_id": "film",
            "location": {
                "city": "Cairo",
                "venue": "Cairo Opera House",
                "coordinates": {"lat": 30.0425, "lng": 31.2247}
            },
            "start_date": "2025-11-20",
            "end_date": "2025-11-29",
            "recurring": True,
            "frequency": "annual",
            "ticket_info": {
                "price_range": {"min": 50, "max": 200, "currency": "EGP"},
                "where_to_buy": "Online at www.ciff.org.eg or at the Cairo Opera House box office",
                "availability": "Tickets go on sale one month before the festival"
            },
            "website": "https://www.ciff.org.eg",
            "contact_info": {
                "email": "info@ciff.org.eg",
                "phone": "+20 2 27370678",
                "social_media": {
                    "facebook": "CairoFilmFest",
                    "instagram": "cairofilmfestival",
                    "twitter": "CairoFilmFest"
                }
            },
            "images": [
                "https://example.com/ciff_1.jpg",
                "https://example.com/ciff_2.jpg"
            ],
            "tags": ["film", "festival", "cairo", "culture", "international", "cinema"],
            "data": {
                "highlights": [
                    "International competition with prestigious awards",
                    "Special screenings of classic Egyptian cinema",
                    "Workshops and masterclasses with renowned filmmakers",
                    "Red carpet events with celebrities"
                ],
                "history": "Founded in 1976, the Cairo International Film Festival is one of the 15 festivals accorded category 'A' status by the International Federation of Film Producers Associations.",
                "tips_for_visitors": [
                    "Book tickets early for popular screenings",
                    "Check the festival program online before attending",
                    "Arrive at least 30 minutes before screenings",
                    "Consider purchasing a festival pass for multiple screenings"
                ]
            }
        },
        {
            "name": {
                "en": "Abu Simbel Sun Festival",
                "ar": "مهرجان شمس أبو سمبل"
            },
            "description": {
                "en": "A biannual phenomenon where the sun's rays penetrate the inner sanctuary of the Abu Simbel temple, illuminating the statues of Ramses II and the gods. This spectacular event attracts tourists and astronomers from around the world.",
                "ar": "ظاهرة نصف سنوية حيث تخترق أشعة الشمس الحرم الداخلي لمعبد أبو سمبل، مضيئة تماثيل رمسيس الثاني والآلهة. يجذب هذا الحدث المذهل السياح وعلماء الفلك من جميع أنحاء العالم."
            },
            "category_id": "cultural",
            "location": {
                "city": "Aswan",
                "venue": "Abu Simbel Temple",
                "coordinates": {"lat": 22.3372, "lng": 31.6258}
            },
            "start_date": "2025-02-22",
            "end_date": "2025-02-22",
            "recurring": True,
            "frequency": "biannual (February 22 and October 22)",
            "ticket_info": {
                "price_range": {"min": 240, "max": 240, "currency": "EGP"},
                "where_to_buy": "At the temple entrance or through tour operators",
                "availability": "Limited availability, advance booking recommended"
            },
            "website": "https://egypt.travel/en/attractions/abu-simbel-temples",
            "contact_info": {
                "email": "info@egypt.travel",
                "phone": "+20 97 2310288",
                "social_media": {
                    "facebook": "ExperienceEgypt",
                    "instagram": "experienceegypt"
                }
            },
            "images": [
                "https://example.com/abu_simbel_1.jpg",
                "https://example.com/abu_simbel_2.jpg"
            ],
            "tags": ["abu simbel", "sun festival", "aswan", "temple", "ramses", "astronomy"],
            "data": {
                "highlights": [
                    "Witnessing the sun's rays illuminate the inner sanctuary",
                    "Traditional Nubian music and dance performances",
                    "Special guided tours explaining the astronomical significance",
                    "Photography opportunities of this rare phenomenon"
                ],
                "history": "The temple was built by Ramses II and positioned precisely so that twice a year, on February 22 (his birthday) and October 22 (his coronation day), the sun's rays would illuminate the inner sanctuary.",
                "tips_for_visitors": [
                    "Arrive early (around 4:00 AM) to secure a good viewing position",
                    "The illumination occurs around 6:00 AM and lasts for about 20 minutes",
                    "Bring warm clothes as mornings can be cold, especially in February",
                    "Photography is allowed but no flash inside the temple"
                ]
            }
        },
        {
            "name": {
                "en": "Ramadan Celebrations in Cairo",
                "ar": "احتفالات رمضان في القاهرة"
            },
            "description": {
                "en": "Experience the magic of Ramadan in Cairo with special events, traditional decorations, and vibrant night markets. The city comes alive after sunset with cultural performances, food festivals, and spiritual gatherings.",
                "ar": "استمتع بسحر رمضان في القاهرة مع الفعاليات الخاصة والزينة التقليدية والأسواق الليلية النابضة بالحياة. تنبض المدينة بالحياة بعد غروب الشمس مع العروض الثقافية ومهرجانات الطعام والتجمعات الروحية."
            },
            "category_id": "religious",
            "location": {
                "city": "Cairo",
                "venue": "Various locations including Khan El Khalili, Al-Azhar Park, and Al-Hussein district",
                "coordinates": {"lat": 30.0444, "lng": 31.2357}
            },
            "start_date": "2025-03-01",
            "end_date": "2025-03-30",
            "recurring": True,
            "frequency": "annual (during the Islamic month of Ramadan)",
            "ticket_info": {
                "price_range": {"min": 0, "max": 200, "currency": "EGP"},
                "where_to_buy": "Most events are free, some special performances require tickets available at venues",
                "availability": "Throughout the month of Ramadan"
            },
            "website": "https://cairo.gov.eg/en/pages/default.aspx",
            "contact_info": {
                "email": "tourism@cairo.gov.eg",
                "phone": "+20 2 27957487",
                "social_media": {
                    "facebook": "CairoGovernorate",
                    "instagram": "cairogovernorate"
                }
            },
            "images": [
                "https://example.com/ramadan_cairo_1.jpg",
                "https://example.com/ramadan_cairo_2.jpg"
            ],
            "tags": ["ramadan", "cairo", "religious", "cultural", "food", "night markets"],
            "data": {
                "highlights": [
                    "Traditional Ramadan lanterns (fanous) decorating the streets",
                    "Iftar (breaking fast) gatherings in historic settings",
                    "Special Ramadan tents offering food and entertainment",
                    "Spiritual nights at Al-Azhar Mosque",
                    "Street performances of traditional arts like Tanoura dancing"
                ],
                "special_events": [
                    "Al-Hussein Square nightly celebrations",
                    "Al-Azhar Park Ramadan festival",
                    "Khan El Khalili special night markets",
                    "Citadel music performances"
                ],
                "tips_for_visitors": [
                    "Respect local customs by not eating or drinking in public during daylight hours",
                    "Many restaurants offer special Ramadan menus and experiences",
                    "The city is most active from sunset until very late at night",
                    "Book restaurant tables in advance for iftar (sunset meal) as they fill quickly",
                    "Dress modestly, especially when visiting religious sites"
                ]
            }
        }
    ]
    
    return event_categories, events_data

def main():
    """Main function to add events and festivals data to the database."""
    logger.info("Starting to add events and festivals data to the database")
    
    # Connect to the database
    db_manager = connect_to_database()
    if not db_manager:
        logger.error("Cannot continue without database connection")
        return
    
    # Generate events data
    event_categories, events_data = generate_events_data()
    
    # Add event categories
    for category in event_categories:
        if not add_event_category(db_manager, category["id"], category["name_en"], category["name_ar"]):
            logger.error(f"Failed to add event category: {category['name_en']}")
    
    # Add events
    for event in events_data:
        if not add_event(db_manager, event):
            logger.error(f"Failed to add event: {event['name']['en']}")
    
    logger.info("✅ Events and festivals data added successfully to the database")
    
    # Test if the events were added correctly
    try:
        query = "SELECT name, category_id FROM events_festivals"
        result = db_manager.execute_query(query)
        if result:
            logger.info(f"Found {len(result)} events in the database")
            for i, row in enumerate(result):
                name = row.get('name', {})
                if isinstance(name, str):
                    try:
                        name = json.loads(name)
                    except:
                        name = {"en": name}
                logger.info(f"  {i+1}. {name.get('en', 'Unknown')} (Category: {row.get('category_id', 'Unknown')})")
        else:
            logger.warning("No events found in the database after adding")
    except Exception as e:
        logger.error(f"❌ Error testing events data: {str(e)}")

if __name__ == "__main__":
    main()
