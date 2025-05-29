#!/usr/bin/env python3
"""
Script to add events and festivals to the database - Part 2.
Covers: music_festivals and food_festivals categories.
"""

import os
import sys
import json
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, date
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

# Events and festivals to add
EVENTS_TO_ADD = [
    # Music Festivals
    {
        "category_id": "music_festivals",
        "name": {
            "en": "Cairo Jazz Festival",
            "ar": "مهرجان القاهرة للجاز"
        },
        "description": {
            "en": "The Cairo Jazz Festival is an annual international music festival that celebrates jazz and related music genres. Founded in 2009, it has grown into one of the most significant jazz events in the Middle East and Africa. The festival features performances by renowned international and local jazz musicians across multiple venues in Cairo. Beyond concerts, the festival includes workshops, masterclasses, and jam sessions, creating opportunities for cultural exchange and musical education. The event attracts jazz enthusiasts from across Egypt and neighboring countries, showcasing Cairo as a vibrant cultural hub. With its diverse lineup of traditional and contemporary jazz styles, the festival bridges cultural gaps and promotes musical dialogue between East and West.",
            "ar": "مهرجان القاهرة للجاز هو مهرجان موسيقي دولي سنوي يحتفل بموسيقى الجاز والأنواع الموسيقية ذات الصلة. تأسس عام 2009، ونما ليصبح أحد أهم فعاليات الجاز في الشرق الأوسط وأفريقيا. يضم المهرجان عروضًا لموسيقيي الجاز الدوليين والمحليين المشهورين في مواقع متعددة في القاهرة. بالإضافة إلى الحفلات الموسيقية، يتضمن المهرجان ورش عمل ودروس رئيسية وجلسات ارتجالية، مما يخلق فرصًا للتبادل الثقافي والتعليم الموسيقي. يجذب الحدث عشاق الجاز من جميع أنحاء مصر والدول المجاورة، مما يظهر القاهرة كمركز ثقافي نابض بالحياة. مع تشكيلته المتنوعة من أساليب الجاز التقليدية والمعاصرة، يجسر المهرجان الفجوات الثقافية ويعزز الحوار الموسيقي بين الشرق والغرب."
        },
        "start_date": "2024-10-10",
        "end_date": "2024-10-12",
        "is_annual": True,
        "annual_month": 10,
        "annual_day": None,  # Varies slightly each year
        "lunar_calendar": False,
        "location_description": {
            "en": "Multiple venues across Cairo, with the main stage at the American University in Cairo (AUC)",
            "ar": "مواقع متعددة في جميع أنحاء القاهرة، مع المسرح الرئيسي في الجامعة الأمريكية بالقاهرة"
        },
        "destination_id": "cairo",
        "venue": {
            "en": "American University in Cairo (AUC), Cairo Opera House, and other cultural venues",
            "ar": "الجامعة الأمريكية بالقاهرة، دار الأوبرا المصرية، ومواقع ثقافية أخرى"
        },
        "organizer": {
            "en": "Jazz Beyond Group",
            "ar": "مجموعة جاز بيوند"
        },
        "admission": {
            "en": "Ticket prices vary by venue and performance, ranging from 100-500 EGP. Festival passes available.",
            "ar": "تختلف أسعار التذاكر حسب المكان والعرض، وتتراوح من 100-500 جنيه مصري. تتوفر تذاكر المهرجان."
        },
        "schedule": {
            "en": "Performances typically run from late afternoon until midnight, with workshops and masterclasses during the day",
            "ar": "تقام العروض عادة من بعد الظهر حتى منتصف الليل، مع ورش عمل ودروس رئيسية خلال النهار"
        },
        "highlights": {
            "en": "International and local jazz performances, jam sessions, workshops, masterclasses, and cultural exchange",
            "ar": "عروض الجاز الدولية والمحلية، جلسات ارتجالية، ورش عمل، دروس رئيسية، وتبادل ثقافي"
        },
        "historical_significance": {
            "en": "Founded in 2009, the Cairo Jazz Festival has played a significant role in revitalizing Egypt's jazz scene and connecting Egyptian musicians with the international jazz community. It has become a platform for cultural dialogue and artistic expression in the region.",
            "ar": "تأسس مهرجان القاهرة للجاز عام 2009، ولعب دورًا مهمًا في إحياء مشهد الجاز في مصر وربط الموسيقيين المصريين بمجتمع الجاز الدولي. أصبح منصة للحوار الثقافي والتعبير الفني في المنطقة."
        },
        "tips": {
            "en": "Book tickets in advance as popular performances sell out quickly. Check the festival website for the full program and venue details. Consider purchasing a festival pass for access to multiple events. Arrive early to secure good seating, especially for free events. Cairo traffic can be heavy, so plan your transportation accordingly.",
            "ar": "احجز التذاكر مسبقًا لأن العروض الشعبية تنفد بسرعة. تحقق من موقع المهرجان للحصول على البرنامج الكامل وتفاصيل المكان. فكر في شراء تذكرة المهرجان للوصول إلى أحداث متعددة. احضر مبكرًا لتأمين مقاعد جيدة، خاصة للأحداث المجانية. يمكن أن تكون حركة المرور في القاهرة كثيفة، لذا خطط لوسائل النقل الخاصة بك وفقًا لذلك."
        },
        "website": "https://cairojazzfest.com",
        "contact_info": {
            "en": "Email: info@cairojazzfest.com, Phone: +20 2 2792 5224",
            "ar": "البريد الإلكتروني: info@cairojazzfest.com، الهاتف: +20 2 2792 5224"
        },
        "tags": ["jazz", "music festival", "concerts", "workshops", "cultural exchange"],
        "is_featured": True
    },
    
    # Food Festivals
    {
        "category_id": "food_festivals",
        "name": {
            "en": "Cairo Food Festival",
            "ar": "مهرجان القاهرة للطعام"
        },
        "description": {
            "en": "The Cairo Food Festival is a culinary celebration that showcases Egypt's rich and diverse food culture alongside international cuisines. This vibrant event brings together restaurants, food vendors, chefs, and food enthusiasts in a festive atmosphere filled with delicious aromas and flavors. Visitors can sample a wide variety of dishes, from traditional Egyptian street food to gourmet international cuisine. The festival features cooking demonstrations by renowned chefs, food competitions, tasting sessions, and culinary workshops. Live music, entertainment, and activities for children make it a family-friendly event. As one of Cairo's most anticipated food events, the festival highlights the city's evolving culinary scene while honoring traditional Egyptian gastronomy.",
            "ar": "مهرجان القاهرة للطعام هو احتفال طهوي يعرض ثقافة الطعام المصرية الغنية والمتنوعة إلى جانب المطابخ الدولية. يجمع هذا الحدث النابض بالحياة المطاعم وبائعي الطعام والطهاة وعشاق الطعام في جو احتفالي مليء بالروائح والنكهات اللذيذة. يمكن للزوار تذوق مجموعة واسعة من الأطباق، من أطعمة الشوارع المصرية التقليدية إلى المأكولات الدولية الفاخرة. يتضمن المهرجان عروض طهي من قبل طهاة مشهورين، ومسابقات طعام، وجلسات تذوق، وورش عمل طهي. تجعل الموسيقى الحية والترفيه والأنشطة للأطفال منه حدثًا مناسبًا للعائلة. باعتباره أحد أكثر فعاليات الطعام المنتظرة في القاهرة، يسلط المهرجان الضوء على مشهد الطهي المتطور في المدينة مع تكريم فن الطهي المصري التقليدي."
        },
        "start_date": "2024-11-07",
        "end_date": "2024-11-09",
        "is_annual": True,
        "annual_month": 11,
        "annual_day": None,  # Varies slightly each year
        "lunar_calendar": False,
        "location_description": {
            "en": "Family Park, New Cairo",
            "ar": "فاميلي بارك، القاهرة الجديدة"
        },
        "destination_id": "cairo",
        "venue": {
            "en": "Family Park, 5th Settlement, New Cairo",
            "ar": "فاميلي بارك، التجمع الخامس، القاهرة الجديدة"
        },
        "organizer": {
            "en": "Cairo Bites and local sponsors",
            "ar": "كايرو بايتس والرعاة المحليين"
        },
        "admission": {
            "en": "Entry tickets range from 50-100 EGP, with food and beverages purchased separately",
            "ar": "تتراوح تذاكر الدخول من 50-100 جنيه مصري، مع شراء الطعام والمشروبات بشكل منفصل"
        },
        "schedule": {
            "en": "Daily from 12:00 PM to 11:00 PM",
            "ar": "يوميًا من الساعة 12:00 ظهرًا حتى 11:00 مساءً"
        },
        "highlights": {
            "en": "Food stalls from top restaurants and vendors, cooking demonstrations, chef competitions, tasting sessions, live music, and family entertainment",
            "ar": "أكشاك طعام من أفضل المطاعم والبائعين، عروض طهي، مسابقات الطهاة، جلسات تذوق، موسيقى حية، وترفيه عائلي"
        },
        "historical_significance": {
            "en": "While relatively new compared to some of Egypt's traditional festivals, the Cairo Food Festival has quickly become an important cultural event that celebrates Egypt's culinary heritage while embracing global food trends. It reflects Cairo's growing status as a gastronomic destination in the Middle East.",
            "ar": "على الرغم من أنه حديث نسبيًا مقارنة ببعض المهرجانات المصرية التقليدية، أصبح مهرجان القاهرة للطعام بسرعة حدثًا ثقافيًا مهمًا يحتفل بالتراث الطهوي المصري مع احتضان اتجاهات الطعام العالمية. يعكس المكانة المتنامية للقاهرة كوجهة للطعام في الشرق الأوسط."
        },
        "tips": {
            "en": "Arrive hungry and pace yourself to try multiple vendors. Bring cash as not all vendors accept cards. Visit early in the day to avoid the largest crowds. Wear comfortable shoes as you'll be walking and standing a lot. Check the schedule for special demonstrations or competitions you might want to see.",
            "ar": "احضر وأنت جائع وتمهل لتجربة بائعين متعددين. أحضر نقودًا لأن ليس كل البائعين يقبلون البطاقات. قم بالزيارة في وقت مبكر من اليوم لتجنب الحشود الكبيرة. ارتدِ أحذية مريحة لأنك ستمشي وتقف كثيرًا. تحقق من الجدول الزمني للعروض التوضيحية الخاصة أو المسابقات التي قد ترغب في رؤيتها."
        },
        "website": "https://cairofoodfestival.com",
        "contact_info": {
            "en": "Email: info@cairofoodfestival.com, Phone: +20 2 2516 8336",
            "ar": "البريد الإلكتروني: info@cairofoodfestival.com، الهاتف: +20 2 2516 8336"
        },
        "tags": ["food festival", "culinary", "Egyptian cuisine", "international food", "cooking demonstrations"],
        "is_featured": True
    }
]

def connect_to_db():
    """Connect to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(DB_CONNECTION_STRING)
        conn.autocommit = True
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        sys.exit(1)

def add_events(conn, events_list):
    """Add events and festivals to the database."""
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get existing events to avoid duplicates
    cursor.execute("SELECT name->>'en' as name_en FROM events_festivals")
    existing_names = [row['name_en'] for row in cursor.fetchall()]
    
    # Add events
    added_count = 0
    skipped_count = 0
    
    for event in events_list:
        # Check if event already exists
        if event['name']['en'] in existing_names:
            logger.info(f"Skipping existing event: {event['name']['en']}")
            skipped_count += 1
            continue
        
        # Prepare data
        now = datetime.now()
        
        # Insert event
        try:
            cursor.execute("""
                INSERT INTO events_festivals 
                (category_id, name, description, start_date, end_date, is_annual, 
                annual_month, annual_day, lunar_calendar, location_description, 
                destination_id, venue, organizer, admission, schedule, highlights, 
                historical_significance, tips, website, contact_info, tags, 
                is_featured, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                event['category_id'],
                json.dumps(event['name']),
                json.dumps(event['description']),
                event.get('start_date'),
                event.get('end_date'),
                event.get('is_annual', False),
                event.get('annual_month'),
                event.get('annual_day'),
                event.get('lunar_calendar', False),
                json.dumps(event.get('location_description', {})),
                event.get('destination_id'),
                json.dumps(event.get('venue', {})),
                json.dumps(event.get('organizer', {})),
                json.dumps(event.get('admission', {})),
                json.dumps(event.get('schedule', {})),
                json.dumps(event.get('highlights', {})),
                json.dumps(event.get('historical_significance', {})),
                json.dumps(event.get('tips', {})),
                event.get('website'),
                json.dumps(event.get('contact_info', {})),
                event.get('tags'),
                event.get('is_featured', False),
                now,
                now
            ))
            
            event_id = cursor.fetchone()['id']
            logger.info(f"Added event ID {event_id}: {event['name']['en']}")
            added_count += 1
            
        except Exception as e:
            logger.error(f"Error adding event {event['name']['en']}: {e}")
    
    cursor.close()
    return added_count, skipped_count

def main():
    """Main function."""
    logger.info("Starting to add events and festivals (Part 2)...")
    
    # Connect to database
    conn = connect_to_db()
    
    # Add events
    added_count, skipped_count = add_events(conn, EVENTS_TO_ADD)
    
    # Close connection
    conn.close()
    
    logger.info(f"Added {added_count} new events, skipped {skipped_count} existing events.")

if __name__ == "__main__":
    main()
