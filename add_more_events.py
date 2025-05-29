#!/usr/bin/env python3
"""
Script to add more events and festivals data to the Egypt Tourism Chatbot database.
This script adds additional events/festivals with detailed information.
"""

import os
import sys
import json
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, date

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def connect_to_database():
    """Connect to the database."""
    try:
        # Get database connection string from environment variable or use default
        db_uri = os.environ.get("POSTGRES_URI", "postgresql://postgres:postgres@localhost:5432/egypt_chatbot")

        # Connect to the database
        conn = psycopg2.connect(db_uri)
        conn.autocommit = True

        logger.info("✅ Database connection successful")
        return conn
    except Exception as e:
        logger.error(f"❌ Error connecting to database: {str(e)}")
        return None

def get_existing_events(conn):
    """Get existing events from the database."""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT name->>'en' as name FROM events_festivals")
            events = cur.fetchall()
            return [event['name'] for event in events]
    except Exception as e:
        logger.error(f"❌ Error getting existing events: {str(e)}")
        return []

def add_event(conn, event_data):
    """Add event to the events_festivals table."""
    try:
        # Check if event already exists
        existing_events = get_existing_events(conn)
        if event_data["name"]["en"] in existing_events:
            logger.info(f"Event '{event_data['name']['en']}' already exists, skipping")
            return True

        # Add event
        query = """
        INSERT INTO events_festivals (
            name,
            description,
            category_id,
            location_description,
            venue,
            start_date,
            end_date,
            is_annual,
            annual_month,
            annual_day,
            admission,
            website,
            contact_info,
            images,
            tags,
            data,
            is_featured,
            created_at,
            updated_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
        )
        """

        # Convert recurring to is_annual
        is_annual = event_data.get("recurring", False)

        # Extract month and day from start_date
        start_date = event_data["start_date"]
        annual_month = start_date.month if isinstance(start_date, date) else None
        annual_day = start_date.day if isinstance(start_date, date) else None

        # Create venue from location
        venue = {
            "name": {
                "en": event_data["location"]["venue"],
                "ar": event_data["location"]["venue"]
            },
            "address": {
                "en": f"{event_data['location']['city']}, Egypt",
                "ar": f"{event_data['location']['city']}, مصر"
            },
            "coordinates": event_data["location"]["coordinates"]
        }

        # Create admission from ticket_info
        admission = event_data.get("ticket_info", {})

        params = (
            json.dumps(event_data["name"]),
            json.dumps(event_data["description"]),
            event_data["category_id"],
            json.dumps({"en": event_data["location"]["city"], "ar": event_data["location"]["city"]}),
            json.dumps(venue),
            event_data["start_date"],
            event_data["end_date"],
            is_annual,
            annual_month,
            annual_day,
            json.dumps(admission),
            event_data["website"],
            json.dumps(event_data["contact_info"]),
            json.dumps(event_data["images"]),
            event_data["tags"],
            json.dumps(event_data["data"]),
            True  # is_featured
        )

        with conn.cursor() as cur:
            cur.execute(query, params)

        logger.info(f"✅ Event '{event_data['name']['en']}' added successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Error adding event: {str(e)}")
        return False

def generate_additional_events():
    """Generate additional events and festivals data."""
    return [
        {
            "name": {
                "en": "Cairo Jazz Festival",
                "ar": "مهرجان القاهرة للجاز"
            },
            "description": {
                "en": "The Cairo Jazz Festival is an annual international music festival that brings together jazz musicians from Egypt and around the world. Held in various venues across Cairo, the festival features live performances, workshops, and jam sessions, showcasing different jazz styles from traditional to contemporary fusion with Middle Eastern influences.",
                "ar": "مهرجان القاهرة للجاز هو مهرجان موسيقي دولي سنوي يجمع بين موسيقيي الجاز من مصر وجميع أنحاء العالم. يقام في أماكن مختلفة في جميع أنحاء القاهرة، ويتضمن المهرجان عروضًا حية وورش عمل وجلسات عزف حر، تعرض أساليب جاز مختلفة من التقليدية إلى الاندماج المعاصر مع تأثيرات الشرق الأوسط."
            },
            "category_id": "music",
            "location": {
                "city": "Cairo",
                "venue": "Multiple venues including Cairo Opera House and AUC Tahrir Cultural Center",
                "coordinates": {"lat": 30.0425, "lng": 31.2247}
            },
            "start_date": "2025-10-15",
            "end_date": "2025-10-17",
            "recurring": True,
            "frequency": "annual",
            "ticket_info": {
                "price_range": {"min": 100, "max": 500, "currency": "EGP"},
                "where_to_buy": "Online at www.cairojazzfest.com or at venue box offices",
                "availability": "Tickets go on sale one month before the festival"
            },
            "website": "https://www.cairojazzfest.com",
            "contact_info": {
                "email": "info@cairojazzfest.com",
                "phone": "+20 2 27356449",
                "social_media": {
                    "facebook": "CairoJazzFestival",
                    "instagram": "cairojazzfestival",
                    "twitter": "CairoJazzFest"
                }
            },
            "images": [
                "https://example.com/cairo_jazz_1.jpg",
                "https://example.com/cairo_jazz_2.jpg"
            ],
            "tags": ["jazz", "music", "festival", "cairo", "culture", "international", "concerts"],
            "data": {
                "highlights": [
                    "Performances by international jazz artists",
                    "Egyptian jazz musicians showcasing local talent",
                    "Fusion performances combining jazz with Arabic music",
                    "Workshops and masterclasses for aspiring musicians",
                    "Jam sessions where artists collaborate spontaneously"
                ],
                "history": "Founded in 2009, the Cairo Jazz Festival has grown to become one of the most important jazz events in the Middle East and North Africa region.",
                "tips_for_visitors": [
                    "Check the festival program online for performance schedules",
                    "Book tickets early for headline performances",
                    "Consider purchasing a festival pass for access to multiple events",
                    "Venues are spread across Cairo, so plan transportation accordingly",
                    "Some outdoor venues can get cool in the evening, bring a light jacket"
                ]
            }
        },
        {
            "name": {
                "en": "Luxor African Film Festival",
                "ar": "مهرجان الأقصر للسينما الأفريقية"
            },
            "description": {
                "en": "The Luxor African Film Festival is an annual celebration of African cinema held in the historic city of Luxor. The festival aims to support and encourage African filmmakers and strengthen cultural ties between African nations through the art of filmmaking. It features competitive sections for feature films, documentaries, and short films, along with workshops, seminars, and cultural events.",
                "ar": "مهرجان الأقصر للسينما الأفريقية هو احتفال سنوي بالسينما الأفريقية يقام في مدينة الأقصر التاريخية. يهدف المهرجان إلى دعم وتشجيع صانعي الأفلام الأفارقة وتعزيز الروابط الثقافية بين الدول الأفريقية من خلال فن صناعة الأفلام. يتضمن أقسامًا تنافسية للأفلام الروائية والوثائقية والقصيرة، إلى جانب ورش العمل والندوات والفعاليات الثقافية."
            },
            "category_id": "film_festivals",
            "location": {
                "city": "Luxor",
                "venue": "Various venues including Luxor Cultural Palace and open-air theaters near ancient temples",
                "coordinates": {"lat": 25.6872, "lng": 32.6396}
            },
            "start_date": "2025-03-15",
            "end_date": "2025-03-21",
            "recurring": True,
            "frequency": "annual",
            "ticket_info": {
                "price_range": {"min": 30, "max": 100, "currency": "EGP"},
                "where_to_buy": "Online at www.luxorafricanfilmfestival.com or at festival venues",
                "availability": "Many screenings are free to the public, special events require tickets"
            },
            "website": "https://www.luxorafricanfilmfestival.com",
            "contact_info": {
                "email": "info@luxorafricanfilmfestival.com",
                "phone": "+20 95 2374976",
                "social_media": {
                    "facebook": "LuxorAfricanFilmFestival",
                    "instagram": "luxorafricanfilmfest",
                    "twitter": "LuxorFilmFest"
                }
            },
            "images": [
                "https://example.com/luxor_film_1.jpg",
                "https://example.com/luxor_film_2.jpg"
            ],
            "tags": ["film", "festival", "luxor", "african cinema", "culture", "international", "documentary"],
            "data": {
                "highlights": [
                    "Screenings of the latest African feature films and documentaries",
                    "Competition sections with awards for best films",
                    "Special screenings against the backdrop of ancient Egyptian temples",
                    "Workshops for young filmmakers",
                    "Panel discussions with renowned directors and actors"
                ],
                "history": "Established in 2012, the Luxor African Film Festival was created to support and encourage African filmmakers and to serve as a platform for cultural exchange between Egypt and other African nations.",
                "tips_for_visitors": [
                    "Check the festival website for the full program and screening locations",
                    "Some special screenings take place in unique locations like temple courtyards",
                    "Book accommodation in Luxor well in advance as the festival attracts many visitors",
                    "Combine film screenings with visits to Luxor's ancient sites",
                    "Evening screenings can be cool, bring appropriate clothing"
                ]
            }
        },
        {
            "name": {
                "en": "Sham El-Nessim",
                "ar": "شم النسيم"
            },
            "description": {
                "en": "Sham El-Nessim is an ancient Egyptian spring festival celebrated by Egyptians regardless of religion. Dating back to pharaonic times, it always falls on the day after Eastern Christian Easter. Families typically spend the day outdoors in parks, gardens, and along the Nile, enjoying traditional foods like colored eggs, salted fish (feseekh), and green onions. The name 'Sham El-Nessim' means 'smelling the breeze,' symbolizing the renewal of life.",
                "ar": "شم النسيم هو مهرجان ربيعي مصري قديم يحتفل به المصريون بغض النظر عن الدين. يعود تاريخه إلى العصور الفرعونية، ويقع دائمًا في اليوم التالي لعيد الفصح المسيحي الشرقي. تقضي العائلات عادة اليوم في الهواء الطلق في الحدائق والمتنزهات وعلى طول نهر النيل، وتستمتع بالأطعمة التقليدية مثل البيض الملون والأسماك المملحة (الفسيخ) والبصل الأخضر. اسم 'شم النسيم' يعني 'استنشاق النسيم'، ويرمز إلى تجدد الحياة."
            },
            "category_id": "cultural_festivals",
            "location": {
                "city": "Nationwide",
                "venue": "Parks, gardens, and public spaces across Egypt",
                "coordinates": {"lat": 30.0444, "lng": 31.2357}
            },
            "start_date": "2025-04-21",
            "end_date": "2025-04-21",
            "recurring": True,
            "frequency": "annual (day after Eastern Christian Easter)",
            "ticket_info": {
                "price_range": {"min": 0, "max": 0, "currency": "EGP"},
                "where_to_buy": "No tickets required, public celebration",
                "availability": "Free and open to all"
            },
            "website": "https://egypt.travel/en/events/sham-el-nessim",
            "contact_info": {
                "email": "info@egypt.travel",
                "phone": "+20 2 27356449",
                "social_media": {
                    "facebook": "ExperienceEgypt",
                    "instagram": "experienceegypt"
                }
            },
            "images": [
                "https://example.com/sham_el_nessim_1.jpg",
                "https://example.com/sham_el_nessim_2.jpg"
            ],
            "tags": ["sham el-nessim", "spring festival", "cultural", "traditional", "family", "food", "nationwide"],
            "data": {
                "highlights": [
                    "Traditional foods including colored eggs, salted fish (feseekh), and green onions",
                    "Picnics in parks and gardens",
                    "Boat rides on the Nile",
                    "Family gatherings and outdoor activities",
                    "Cultural performances in public spaces"
                ],
                "history": "Sham El-Nessim dates back to ancient Egypt around 2700 BCE. Originally a pharaonic festival called 'Shemu' celebrating the beginning of spring, it was later adopted by Coptic Christians and Muslims alike, becoming a national holiday that transcends religious boundaries.",
                "tips_for_visitors": [
                    "Public parks and gardens become very crowded, arrive early to secure a good spot",
                    "Try the traditional foods but be cautious with feseekh (fermented salted fish) as it requires proper preparation",
                    "Visit the Nile corniche for a traditional experience with boat rides",
                    "Public transportation can be limited on this holiday, plan accordingly",
                    "Bring a picnic blanket and plenty of water for a day outdoors"
                ]
            }
        },
        {
            "name": {
                "en": "El Gouna Film Festival",
                "ar": "مهرجان الجونة السينمائي"
            },
            "description": {
                "en": "The El Gouna Film Festival is a prominent cultural event held annually in the resort town of El Gouna on Egypt's Red Sea coast. The festival showcases a diverse selection of films from around the world with a focus on Arab cinema. It features competitive sections for feature films, documentaries, and short films, along with special screenings, masterclasses, and panel discussions. The festival aims to foster cultural exchange and create opportunities for filmmakers from the region.",
                "ar": "مهرجان الجونة السينمائي هو حدث ثقافي بارز يقام سنويًا في مدينة الجونة السياحية على ساحل البحر الأحمر المصري. يعرض المهرجان مجموعة متنوعة من الأفلام من جميع أنحاء العالم مع التركيز على السينما العربية. يتضمن أقسامًا تنافسية للأفلام الروائية والوثائقية والقصيرة، إلى جانب عروض خاصة ودروس رئيسية وحلقات نقاش. يهدف المهرجان إلى تعزيز التبادل الثقافي وخلق فرص لصانعي الأفلام من المنطقة."
            },
            "category_id": "film_festivals",
            "location": {
                "city": "El Gouna",
                "venue": "Various venues throughout El Gouna resort town",
                "coordinates": {"lat": 27.3944, "lng": 33.6734}
            },
            "start_date": "2025-09-24",
            "end_date": "2025-10-02",
            "recurring": True,
            "frequency": "annual",
            "ticket_info": {
                "price_range": {"min": 100, "max": 500, "currency": "EGP"},
                "where_to_buy": "Online at www.elgounafilmfestival.com or at festival venues",
                "availability": "Tickets go on sale one month before the festival"
            },
            "website": "https://www.elgounafilmfestival.com",
            "contact_info": {
                "email": "info@elgounafilmfestival.com",
                "phone": "+20 65 3580170",
                "social_media": {
                    "facebook": "ElGounaFilmFestival",
                    "instagram": "elgounafilmfestival",
                    "twitter": "ElGounaFilm"
                }
            },
            "images": [
                "https://example.com/el_gouna_film_1.jpg",
                "https://example.com/el_gouna_film_2.jpg"
            ],
            "tags": ["film", "festival", "el gouna", "red sea", "cinema", "international", "arab cinema"],
            "data": {
                "highlights": [
                    "Red carpet events with Egyptian and international celebrities",
                    "Competitive sections with prestigious awards",
                    "Screenings of acclaimed international and Arab films",
                    "CineGouna Platform for project development and networking",
                    "Masterclasses and workshops with renowned filmmakers"
                ],
                "history": "Founded in 2017, the El Gouna Film Festival quickly established itself as one of the most prestigious film festivals in the Middle East and North Africa region.",
                "tips_for_visitors": [
                    "Book accommodation well in advance as El Gouna fills up during the festival",
                    "Check the festival website for the full program and ticket information",
                    "Dress code for evening screenings and galas is formal",
                    "The festival is spread across multiple venues in El Gouna, so plan transportation accordingly",
                    "Combine the festival with a beach holiday in this beautiful Red Sea resort"
                ]
            }
        },
        {
            "name": {
                "en": "Aswan International Sculpture Symposium",
                "ar": "سمبوزيوم أسوان الدولي للنحت"
            },
            "description": {
                "en": "The Aswan International Sculpture Symposium is a unique cultural event that brings together sculptors from around the world to create works of art from Aswan's famous granite. Held annually in an open-air setting near the ancient granite quarries, the symposium allows visitors to watch artists at work and see the creative process unfold. The completed sculptures become part of an open-air museum, enhancing Aswan's cultural landscape and creating a permanent legacy of international artistic collaboration.",
                "ar": "سمبوزيوم أسوان الدولي للنحت هو حدث ثقافي فريد يجمع النحاتين من جميع أنحاء العالم لإنشاء أعمال فنية من جرانيت أسوان الشهير. يقام سنويًا في مكان مفتوح بالقرب من محاجر الجرانيت القديمة، ويتيح السمبوزيوم للزوار مشاهدة الفنانين أثناء العمل ورؤية عملية الإبداع تتكشف. تصبح المنحوتات المكتملة جزءًا من متحف في الهواء الطلق، مما يعزز المشهد الثقافي لأسوان ويخلق إرثًا دائمًا للتعاون الفني الدولي."
            },
            "category_id": "art_exhibitions",
            "location": {
                "city": "Aswan",
                "venue": "Open-air site near the ancient granite quarries",
                "coordinates": {"lat": 24.0889, "lng": 32.8998}
            },
            "start_date": "2025-01-15",
            "end_date": "2025-02-15",
            "recurring": True,
            "frequency": "annual",
            "ticket_info": {
                "price_range": {"min": 0, "max": 0, "currency": "EGP"},
                "where_to_buy": "No tickets required, open to the public",
                "availability": "Free access to the symposium site during opening hours"
            },
            "website": "https://www.aiss.eg",
            "contact_info": {
                "email": "info@aiss.eg",
                "phone": "+20 97 2312711",
                "social_media": {
                    "facebook": "AswanSculptureSymposium",
                    "instagram": "aswansculpture"
                }
            },
            "images": [
                "https://example.com/aswan_sculpture_1.jpg",
                "https://example.com/aswan_sculpture_2.jpg"
            ],
            "tags": ["sculpture", "art", "aswan", "granite", "international", "artists", "open-air museum"],
            "data": {
                "highlights": [
                    "International sculptors creating monumental works from Aswan granite",
                    "Open-air workshop where visitors can observe the artistic process",
                    "Cultural exchange between Egyptian and international artists",
                    "Final exhibition of completed sculptures",
                    "Permanent open-air museum of sculptures from previous symposiums"
                ],
                "history": "Founded in 1996 by sculptor Adam Henein, the Aswan International Sculpture Symposium revives the ancient tradition of granite sculpture in Aswan, which dates back to pharaonic times.",
                "tips_for_visitors": [
                    "Visit multiple times throughout the symposium to see how the sculptures evolve",
                    "Morning hours offer the best light for photography",
                    "Combine with visits to the ancient granite quarries to understand the historical context",
                    "Wear comfortable shoes and sun protection for the outdoor setting",
                    "January and February offer pleasant temperatures in Aswan, perfect for outdoor activities"
                ]
            }
        }
    ]

def main():
    """Main function to add more events and festivals data to the database."""
    logger.info("Starting to add more events and festivals data to the database")

    # Connect to the database
    conn = connect_to_database()
    if not conn:
        logger.error("Cannot continue without database connection")
        return

    # Get existing events
    existing_events = get_existing_events(conn)
    logger.info(f"Found {len(existing_events)} existing events: {existing_events}")

    # Generate additional events data
    additional_events = generate_additional_events()
    logger.info(f"Generated {len(additional_events)} additional events")

    # Add events
    added_count = 0
    for event in additional_events:
        logger.info(f"Attempting to add event: {event['name']['en']}")
        if event['name']['en'] not in existing_events:
            try:
                if add_event(conn, event):
                    added_count += 1
                    logger.info(f"Successfully added event: {event['name']['en']}")
                else:
                    logger.error(f"Failed to add event: {event['name']['en']}")
            except Exception as e:
                logger.error(f"Exception adding event {event['name']['en']}: {str(e)}")
        else:
            logger.info(f"Event already exists, skipping: {event['name']['en']}")

    logger.info(f"✅ Added {added_count} new events and festivals to the database")

    # Test if the events were added correctly
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT COUNT(*) FROM events_festivals")
            total_count = cur.fetchone()["count"]
            logger.info(f"Total events and festivals in the database: {total_count}")

            cur.execute("SELECT name->>'en' as name, category_id FROM events_festivals ORDER BY name->>'en'")
            events = cur.fetchall()
            logger.info("Events and festivals in the database:")
            for i, event in enumerate(events):
                logger.info(f"  {i+1}. {event['name']} (Category: {event['category_id']})")
    except Exception as e:
        logger.error(f"❌ Error testing events data: {str(e)}")

    # Close the database connection
    conn.close()

if __name__ == "__main__":
    main()
