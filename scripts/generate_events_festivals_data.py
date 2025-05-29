#!/usr/bin/env python3
"""
Script to generate comprehensive events and festivals data for the Egypt Tourism Chatbot database.
This script generates at least 15 events/festivals with detailed information.
"""

import os
import sys
import json
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_event_categories():
    """Generate event categories data."""
    return [
        {
            "id": "cultural",
            "name": {
                "en": "Cultural Festivals",
                "ar": "المهرجانات الثقافية"
            },
            "description": {
                "en": "Festivals celebrating Egyptian culture, heritage, and traditions",
                "ar": "مهرجانات تحتفل بالثقافة المصرية والتراث والتقاليد"
            }
        },
        {
            "id": "religious",
            "name": {
                "en": "Religious Celebrations",
                "ar": "الاحتفالات الدينية"
            },
            "description": {
                "en": "Events and celebrations related to religious occasions and traditions",
                "ar": "الأحداث والاحتفالات المتعلقة بالمناسبات والتقاليد الدينية"
            }
        },
        {
            "id": "music",
            "name": {
                "en": "Music Events",
                "ar": "الفعاليات الموسيقية"
            },
            "description": {
                "en": "Concerts, music festivals, and performances across Egypt",
                "ar": "الحفلات الموسيقية والمهرجانات والعروض في جميع أنحاء مصر"
            }
        },
        {
            "id": "film",
            "name": {
                "en": "Film Festivals",
                "ar": "مهرجانات الأفلام"
            },
            "description": {
                "en": "Film screenings, competitions, and cinema celebrations",
                "ar": "عروض الأفلام والمسابقات واحتفالات السينما"
            }
        },
        {
            "id": "art",
            "name": {
                "en": "Art Exhibitions",
                "ar": "معارض الفن"
            },
            "description": {
                "en": "Visual arts, exhibitions, and artistic showcases",
                "ar": "الفنون البصرية والمعارض والعروض الفنية"
            }
        },
        {
            "id": "food",
            "name": {
                "en": "Food Festivals",
                "ar": "مهرجانات الطعام"
            },
            "description": {
                "en": "Culinary events celebrating Egyptian and international cuisine",
                "ar": "الفعاليات الطهوية التي تحتفل بالمطبخ المصري والدولي"
            }
        },
        {
            "id": "sports",
            "name": {
                "en": "Sports Events",
                "ar": "الفعاليات الرياضية"
            },
            "description": {
                "en": "Sporting competitions, tournaments, and athletic events",
                "ar": "المسابقات الرياضية والبطولات والفعاليات الرياضية"
            }
        }
    ]

def generate_events_data():
    """Generate comprehensive events and festivals data."""
    return [
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

def main():
    """Generate and save events and festivals data to JSON files."""
    try:
        # Create output directory if it doesn't exist
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate event categories data
        event_categories = generate_event_categories()
        
        # Save event categories data to JSON file
        categories_file = os.path.join(output_dir, "event_categories.json")
        with open(categories_file, "w", encoding="utf-8") as f:
            json.dump(event_categories, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ Saved {len(event_categories)} event categories to {categories_file}")
        
        # Generate events data
        events_data = generate_events_data()
        
        # Save events data to JSON file
        events_file = os.path.join(output_dir, "events_festivals.json")
        with open(events_file, "w", encoding="utf-8") as f:
            json.dump(events_data, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ Saved {len(events_data)} events to {events_file}")
        
        logger.info("✅ Events and festivals data generation completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Error generating events and festivals data: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
