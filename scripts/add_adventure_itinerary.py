#!/usr/bin/env python3
"""
Script to add an adventure itinerary to the database.
"""

import os
import sys
import json
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database connection string
DB_CONNECTION_STRING = "postgresql://postgres:postgres@localhost:5432/egypt_chatbot"

# Adventure itinerary to add
ADVENTURE_ITINERARY = {
    "type_id": "adventure",
    "name": {
        "en": "Desert Safari and Red Sea Exploration",
        "ar": "سفاري الصحراء واستكشاف البحر الأحمر"
    },
    "description": {
        "en": "Experience the thrill of Egypt's natural wonders with this 6-day adventure combining desert exploration and Red Sea marine activities. Begin your journey in the White Desert with its surreal chalk formations, camp under the stars, and enjoy exhilarating dune bashing. Then head to Hurghada on the Red Sea coast for world-class diving, snorkeling, and water sports. This itinerary is perfect for adventure seekers who want to experience both the serene beauty of Egypt's deserts and the vibrant underwater world of the Red Sea.",
        "ar": "استمتع بإثارة عجائب مصر الطبيعية مع هذه المغامرة التي تستمر 6 أيام والتي تجمع بين استكشاف الصحراء وأنشطة البحر الأحمر البحرية. ابدأ رحلتك في الصحراء البيضاء بتكويناتها الطباشيرية الخيالية، وخيم تحت النجوم، واستمتع بركوب الكثبان الرملية المثير. ثم توجه إلى الغردقة على ساحل البحر الأحمر للغوص والغطس والرياضات المائية من الدرجة الأولى. هذا المسار مثالي لعشاق المغامرة الذين يرغبون في تجربة كل من الجمال الهادئ لصحاري مصر والعالم المائي النابض بالحياة للبحر الأحمر."
    },
    "duration_days": 6,
    "regions": ["western_desert", "red_sea"],
    "cities": ["bahariya", "farafra", "hurghada"],
    "attractions": [],
    "restaurants": [],
    "accommodations": [],
    "transportation_types": ["4x4_vehicle", "private_car"],
    "daily_plans": {
        "day_1": {
            "title": {
                "en": "Cairo to Bahariya Oasis",
                "ar": "من القاهرة إلى واحة البحرية"
            },
            "description": {
                "en": "Depart from Cairo in the morning for a 4-hour drive to Bahariya Oasis. After lunch, explore the oasis including the Temple of Alexander the Great and the Valley of the Golden Mummies. Visit the Black Mountain for panoramic views of the oasis. In the evening, enjoy a traditional Bedouin dinner under the stars with local music.",
                "ar": "انطلق من القاهرة في الصباح في رحلة تستغرق 4 ساعات إلى واحة البحرية. بعد الغداء، استكشف الواحة بما في ذلك معبد الإسكندر الأكبر ووادي المومياوات الذهبية. قم بزيارة الجبل الأسود للحصول على مناظر بانورامية للواحة. في المساء، استمتع بعشاء بدوي تقليدي تحت النجوم مع الموسيقى المحلية."
            },
            "activities": [
                {
                    "time": "07:00 - 11:00",
                    "activity": {
                        "en": "Drive from Cairo to Bahariya Oasis",
                        "ar": "القيادة من القاهرة إلى واحة البحرية"
                    }
                },
                {
                    "time": "12:00 - 13:00",
                    "activity": {
                        "en": "Lunch at a local restaurant",
                        "ar": "الغداء في مطعم محلي"
                    }
                },
                {
                    "time": "14:00 - 17:00",
                    "activity": {
                        "en": "Explore Bahariya Oasis attractions",
                        "ar": "استكشاف معالم واحة البحرية"
                    }
                },
                {
                    "time": "17:30 - 19:00",
                    "activity": {
                        "en": "Visit Black Mountain for sunset views",
                        "ar": "زيارة الجبل الأسود لمشاهدة غروب الشمس"
                    }
                },
                {
                    "time": "20:00 - 22:00",
                    "activity": {
                        "en": "Bedouin dinner with local entertainment",
                        "ar": "عشاء بدوي مع ترفيه محلي"
                    }
                }
            ],
            "accommodation": {
                "en": "Bahariya Oasis hotel or desert camp",
                "ar": "فندق واحة البحرية أو مخيم صحراوي"
            },
            "meals": {
                "en": "Lunch at local restaurant, Bedouin dinner",
                "ar": "الغداء في مطعم محلي، عشاء بدوي"
            }
        },
        "day_2": {
            "title": {
                "en": "White Desert Expedition",
                "ar": "رحلة الصحراء البيضاء"
            },
            "description": {
                "en": "After breakfast, depart in 4x4 vehicles for the White Desert National Park. En route, visit the Crystal Mountain and the Valley of Agabat with its dramatic rock formations. Explore the surreal landscape of the White Desert with its chalk formations shaped like mushrooms, camels, and other figures. Enjoy a picnic lunch in the desert. In the afternoon, try sandboarding on the dunes. Set up camp in the White Desert for an unforgettable night under the stars with a campfire dinner.",
                "ar": "بعد الإفطار، انطلق في سيارات دفع رباعي إلى متنزه الصحراء البيضاء الوطني. في الطريق، قم بزيارة جبل الكريستال ووادي العجبات بتكويناته الصخرية المذهلة. استكشف المناظر الطبيعية الخيالية للصحراء البيضاء بتكويناتها الطباشيرية التي تشبه الفطر والجمال وأشكال أخرى. استمتع بتناول وجبة غداء في الصحراء. في فترة ما بعد الظهر، جرب ركوب الألواح على الكثبان الرملية. أقم مخيمًا في الصحراء البيضاء لقضاء ليلة لا تُنسى تحت النجوم مع عشاء على نار المخيم."
            },
            "activities": [
                {
                    "time": "08:00 - 09:00",
                    "activity": {
                        "en": "Breakfast at accommodation",
                        "ar": "الإفطار في مكان الإقامة"
                    }
                },
                {
                    "time": "09:30 - 11:00",
                    "activity": {
                        "en": "4x4 journey to Crystal Mountain and Valley of Agabat",
                        "ar": "رحلة بسيارة دفع رباعي إلى جبل الكريستال ووادي العجبات"
                    }
                },
                {
                    "time": "11:30 - 14:00",
                    "activity": {
                        "en": "Explore White Desert formations with picnic lunch",
                        "ar": "استكشاف تكوينات الصحراء البيضاء مع غداء في الهواء الطلق"
                    }
                },
                {
                    "time": "15:00 - 17:00",
                    "activity": {
                        "en": "Sandboarding on desert dunes",
                        "ar": "ركوب الألواح على الكثبان الصحراوية"
                    }
                },
                {
                    "time": "17:30 - 19:00",
                    "activity": {
                        "en": "Set up desert camp and watch sunset",
                        "ar": "إعداد المخيم الصحراوي ومشاهدة غروب الشمس"
                    }
                },
                {
                    "time": "19:30 - 22:00",
                    "activity": {
                        "en": "Campfire dinner and stargazing",
                        "ar": "عشاء على نار المخيم ومراقبة النجوم"
                    }
                }
            ],
            "accommodation": {
                "en": "Desert camping in the White Desert",
                "ar": "التخييم في الصحراء البيضاء"
            },
            "meals": {
                "en": "Breakfast at hotel, picnic lunch, campfire dinner",
                "ar": "الإفطار في الفندق، غداء في الهواء الطلق، عشاء على نار المخيم"
            }
        },
        "day_3": {
            "title": {
                "en": "Desert to Red Sea",
                "ar": "من الصحراء إلى البحر الأحمر"
            },
            "description": {
                "en": "Wake up early to witness the sunrise over the White Desert. After breakfast at camp, return to Bahariya Oasis. From there, depart for Hurghada on the Red Sea coast (approximately 6-7 hours drive). Check into your beachfront hotel in the afternoon and enjoy some relaxation time by the sea. In the evening, explore Hurghada's marina and enjoy dinner at a seafood restaurant.",
                "ar": "استيقظ مبكرًا لمشاهدة شروق الشمس فوق الصحراء البيضاء. بعد الإفطار في المخيم، عد إلى واحة البحرية. من هناك، انطلق إلى الغردقة على ساحل البحر الأحمر (حوالي 6-7 ساعات بالسيارة). قم بتسجيل الوصول إلى فندقك المطل على الشاطئ في فترة ما بعد الظهر واستمتع ببعض وقت الاسترخاء بجانب البحر. في المساء، استكشف مارينا الغردقة واستمتع بتناول العشاء في مطعم للمأكولات البحرية."
            },
            "activities": [
                {
                    "time": "05:30 - 06:30",
                    "activity": {
                        "en": "Desert sunrise viewing",
                        "ar": "مشاهدة شروق الشمس في الصحراء"
                    }
                },
                {
                    "time": "07:00 - 08:00",
                    "activity": {
                        "en": "Breakfast at camp",
                        "ar": "الإفطار في المخيم"
                    }
                },
                {
                    "time": "08:30 - 10:30",
                    "activity": {
                        "en": "Return to Bahariya Oasis",
                        "ar": "العودة إلى واحة البحرية"
                    }
                },
                {
                    "time": "11:00 - 17:00",
                    "activity": {
                        "en": "Drive to Hurghada with stops for lunch and rest",
                        "ar": "القيادة إلى الغردقة مع توقفات للغداء والراحة"
                    }
                },
                {
                    "time": "17:30 - 19:00",
                    "activity": {
                        "en": "Check-in and relax at beachfront hotel",
                        "ar": "تسجيل الوصول والاسترخاء في الفندق المطل على الشاطئ"
                    }
                },
                {
                    "time": "19:30 - 22:00",
                    "activity": {
                        "en": "Explore Hurghada Marina and dinner",
                        "ar": "استكشاف مارينا الغردقة والعشاء"
                    }
                }
            ],
            "accommodation": {
                "en": "Hurghada beachfront hotel",
                "ar": "فندق مطل على الشاطئ في الغردقة"
            },
            "meals": {
                "en": "Breakfast at camp, lunch en route, dinner at seafood restaurant",
                "ar": "الإفطار في المخيم، الغداء في الطريق، العشاء في مطعم للمأكولات البحرية"
            }
        }
    },
    "budget_range": {
        "economy": {
            "min": 600,
            "max": 800,
            "currency": "USD"
        },
        "standard": {
            "min": 800,
            "max": 1200,
            "currency": "USD"
        },
        "luxury": {
            "min": 1200,
            "max": 2000,
            "currency": "USD"
        }
    },
    "best_seasons": ["fall", "winter", "spring"],
    "difficulty_level": "moderate",
    "target_audience": {
        "en": "Adventure seekers, nature lovers, photography enthusiasts, and active travelers who enjoy outdoor activities",
        "ar": "الباحثون عن المغامرة، عشاق الطبيعة، هواة التصوير، والمسافرون النشطون الذين يستمتعون بالأنشطة الخارجية"
    },
    "highlights": {
        "en": "Camping under the stars in the White Desert, exploring surreal chalk formations, sandboarding on desert dunes, snorkeling or diving in the Red Sea's coral reefs, water sports activities",
        "ar": "التخييم تحت النجوم في الصحراء البيضاء، استكشاف تكوينات الطباشير الخيالية، ركوب الألواح على الكثبان الرملية، الغطس أو الغوص في الشعاب المرجانية للبحر الأحمر، أنشطة الرياضات المائية"
    },
    "practical_tips": {
        "en": "Pack for both desert and beach environments. Bring sun protection, comfortable hiking shoes, and warm clothes for cold desert nights. A headlamp is essential for the desert camping. For Red Sea activities, bring underwater camera if possible. Desert portions of this trip are not recommended during summer months (June-August) due to extreme heat.",
        "ar": "قم بالتعبئة لكل من بيئات الصحراء والشاطئ. أحضر واقي الشمس، وأحذية مريحة للمشي لمسافات طويلة، وملابس دافئة لليالي الصحراء الباردة. المصباح الأمامي ضروري للتخييم في الصحراء. لأنشطة البحر الأحمر، أحضر كاميرا تحت الماء إذا أمكن. لا يُنصح بأجزاء الصحراء من هذه الرحلة خلال أشهر الصيف (يونيو-أغسطس) بسبب الحرارة الشديدة."
    },
    "tags": ["desert", "camping", "snorkeling", "diving", "adventure", "nature", "white desert", "red sea"],
    "is_featured": True
}

def connect_to_db():
    """Connect to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(DB_CONNECTION_STRING)
        conn.autocommit = True
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        sys.exit(1)

def add_itinerary(conn, itinerary):
    """Add an itinerary to the database."""
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get existing itineraries to avoid duplicates
    cursor.execute("SELECT name->>'en' as name_en FROM itineraries")
    existing_names = [row['name_en'] for row in cursor.fetchall()]
    
    # Check if itinerary already exists
    if itinerary['name']['en'] in existing_names:
        logger.info(f"Skipping existing itinerary: {itinerary['name']['en']}")
        cursor.close()
        return False
    
    # Prepare data
    now = datetime.now()
    
    # Insert itinerary
    try:
        cursor.execute("""
            INSERT INTO itineraries 
            (type_id, name, description, duration_days, regions, cities, 
            attractions, restaurants, accommodations, transportation_types, 
            daily_plans, budget_range, best_seasons, difficulty_level, 
            target_audience, highlights, practical_tips, tags, is_featured, 
            created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            itinerary['type_id'],
            json.dumps(itinerary['name']),
            json.dumps(itinerary['description']),
            itinerary['duration_days'],
            itinerary.get('regions', None),
            itinerary.get('cities', None),
            itinerary.get('attractions', None),
            itinerary.get('restaurants', None),
            itinerary.get('accommodations', None),
            itinerary.get('transportation_types', None),
            json.dumps(itinerary['daily_plans']),
            json.dumps(itinerary.get('budget_range', {})),
            itinerary.get('best_seasons', None),
            itinerary.get('difficulty_level'),
            json.dumps(itinerary.get('target_audience', {})),
            json.dumps(itinerary.get('highlights', {})),
            json.dumps(itinerary.get('practical_tips', {})),
            itinerary.get('tags', None),
            itinerary.get('is_featured', False),
            now,
            now
        ))
        
        itinerary_id = cursor.fetchone()['id']
        logger.info(f"Added itinerary ID {itinerary_id}: {itinerary['name']['en']}")
        cursor.close()
        return True
        
    except Exception as e:
        logger.error(f"Error adding itinerary {itinerary['name']['en']}: {e}")
        cursor.close()
        return False

def main():
    """Main function."""
    logger.info("Starting to add adventure itinerary...")
    
    # Connect to database
    conn = connect_to_db()
    
    # Add itinerary
    success = add_itinerary(conn, ADVENTURE_ITINERARY)
    
    # Close connection
    conn.close()
    
    if success:
        logger.info("Successfully added adventure itinerary.")
    else:
        logger.info("Failed to add adventure itinerary or it already exists.")

if __name__ == "__main__":
    main()
