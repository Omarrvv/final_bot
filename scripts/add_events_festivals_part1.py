#!/usr/bin/env python3
"""
Script to add events and festivals to the database - Part 1.
Covers: religious_festivals and cultural_festivals categories.
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
    # Religious Festivals
    {
        "category_id": "religious_festivals",
        "name": {
            "en": "Moulid El-Nabi",
            "ar": "المولد النبوي"
        },
        "description": {
            "en": "Moulid El-Nabi celebrates the birthday of Prophet Muhammad. Throughout Egypt, streets are decorated with colorful lights, banners, and special tents where Sufi chanting and religious songs are performed. Families gather to share traditional sweets, especially the sugar dolls and horses known as 'Arouset El-Moulid' and 'Housan El-Moulid'. In Cairo, the celebration centers around the Al-Hussein Mosque, with processions, dhikr ceremonies, and food stalls. It's a time of spiritual reflection and community celebration that brings together Egyptians from all walks of life.",
            "ar": "يحتفل المولد النبوي بعيد ميلاد النبي محمد. في جميع أنحاء مصر، تزين الشوارع بالأضواء الملونة واللافتات والخيام الخاصة حيث يتم أداء الإنشاد الصوفي والأغاني الدينية. تجتمع العائلات لتناول الحلويات التقليدية، خاصة دمى السكر والخيول المعروفة باسم 'عروسة المولد' و'حصان المولد'. في القاهرة، يتركز الاحتفال حول مسجد الحسين، مع المواكب وحلقات الذكر وأكشاك الطعام. إنه وقت للتأمل الروحي واحتفال المجتمع الذي يجمع المصريين من جميع مناحي الحياة."
        },
        "start_date": "2024-09-15",
        "end_date": "2024-09-16",
        "is_annual": True,
        "annual_month": None,  # Varies based on Islamic calendar
        "annual_day": None,    # Varies based on Islamic calendar
        "lunar_calendar": True,
        "location_description": {
            "en": "Nationwide, with major celebrations in Cairo, Alexandria, and Tanta",
            "ar": "على مستوى البلاد، مع احتفالات كبرى في القاهرة والإسكندرية وطنطا"
        },
        "destination_id": "egypt",
        "venue": {
            "en": "Various mosques and public squares throughout Egypt",
            "ar": "مساجد وميادين عامة مختلفة في جميع أنحاء مصر"
        },
        "organizer": {
            "en": "Ministry of Religious Endowments and local communities",
            "ar": "وزارة الأوقاف والمجتمعات المحلية"
        },
        "admission": {
            "en": "Free and open to the public",
            "ar": "مجاني ومفتوح للجمهور"
        },
        "schedule": {
            "en": "Main celebrations begin after sunset on the eve of the Prophet's birthday and continue through the following day",
            "ar": "تبدأ الاحتفالات الرئيسية بعد غروب الشمس في عشية عيد ميلاد النبي وتستمر حتى اليوم التالي"
        },
        "highlights": {
            "en": "Sufi dhikr ceremonies, religious processions, special prayers, traditional sweets, decorated streets, and community gatherings",
            "ar": "حلقات الذكر الصوفية، المواكب الدينية، الصلوات الخاصة، الحلويات التقليدية، الشوارع المزينة، والتجمعات المجتمعية"
        },
        "historical_significance": {
            "en": "This celebration has been observed in Egypt for centuries, blending religious devotion with cultural traditions. While the exact date of the Prophet's birth is debated, the celebration has become an important part of Egyptian cultural identity.",
            "ar": "تم الاحتفال بهذه المناسبة في مصر لعدة قرون، مزيجًا من التفاني الديني والتقاليد الثقافية. على الرغم من أن التاريخ الدقيق لميلاد النبي موضع نقاش، إلا أن الاحتفال أصبح جزءًا مهمًا من الهوية الثقافية المصرية."
        },
        "tips": {
            "en": "Visitors should dress modestly when attending celebrations near mosques. The areas around major celebration sites can become very crowded, so plan accordingly. This is an excellent opportunity to try traditional sweets like 'halawet el-moulid' (sesame candy) and 'hummus el-sham' (chickpea dessert).",
            "ar": "يجب على الزوار ارتداء ملابس محتشمة عند حضور الاحتفالات بالقرب من المساجد. يمكن أن تصبح المناطق المحيطة بمواقع الاحتفالات الرئيسية مزدحمة للغاية، لذا خطط وفقًا لذلك. هذه فرصة ممتازة لتجربة الحلويات التقليدية مثل 'حلاوة المولد' (حلوى السمسم) و'حمص الشام' (حلوى الحمص)."
        },
        "website": "https://egypt.travel/en/events/moulid-el-nabi",
        "contact_info": {
            "en": "For information: Egyptian Tourism Authority, +20 2 285 4509",
            "ar": "للمعلومات: هيئة تنشيط السياحة المصرية، +20 2 285 4509"
        },
        "tags": ["religious festival", "Islamic celebration", "Prophet Muhammad", "Sufi", "traditional sweets"],
        "is_featured": True
    },
    {
        "category_id": "religious_festivals",
        "name": {
            "en": "Coptic Christmas",
            "ar": "عيد الميلاد القبطي"
        },
        "description": {
            "en": "Coptic Christmas, celebrated on January 7th, is one of the most important religious holidays for Egypt's Coptic Christian community. Following a 43-day fast (the Nativity Fast), families attend midnight mass on Christmas Eve, which traditionally ends around midnight. The service at St. Mark's Cathedral in Cairo, led by the Coptic Pope, is broadcast nationwide. After mass, families gather for a feast featuring traditional dishes like fattah (rice, bread, and meat dish), accompanied by kahk (special cookies) and biscuits. Homes and churches are decorated with lights, nativity scenes, and Christmas trees. In recent years, the celebration has gained wider recognition, with government officials attending Christmas mass and public celebrations in major cities.",
            "ar": "عيد الميلاد القبطي، الذي يُحتفل به في 7 يناير، هو أحد أهم الأعياد الدينية لمجتمع الأقباط المسيحيين في مصر. بعد صيام 43 يومًا (صيام الميلاد)، تحضر العائلات قداس منتصف الليل في ليلة عيد الميلاد، والذي ينتهي تقليديًا حوالي منتصف الليل. يتم بث الخدمة في كاتدرائية القديس مرقس في القاهرة، التي يقودها البابا القبطي، على مستوى البلاد. بعد القداس، تجتمع العائلات لتناول وليمة تضم أطباقًا تقليدية مثل الفتة (طبق من الأرز والخبز واللحم)، مصحوبة بالكحك (كعك خاص) والبسكويت. تزين المنازل والكنائس بالأضواء ومشاهد المهد وأشجار عيد الميلاد. في السنوات الأخيرة، اكتسب الاحتفال اعترافًا أوسع، مع حضور المسؤولين الحكوميين لقداس عيد الميلاد والاحتفالات العامة في المدن الكبرى."
        },
        "start_date": "2025-01-06",
        "end_date": "2025-01-07",
        "is_annual": True,
        "annual_month": 1,
        "annual_day": 7,
        "lunar_calendar": False,
        "location_description": {
            "en": "Nationwide, with major celebrations in Cairo, Alexandria, Minya, and Assiut",
            "ar": "على مستوى البلاد، مع احتفالات كبرى في القاهرة والإسكندرية والمنيا وأسيوط"
        },
        "destination_id": "egypt",
        "venue": {
            "en": "Coptic churches throughout Egypt, with the main service at St. Mark's Coptic Orthodox Cathedral in Cairo",
            "ar": "الكنائس القبطية في جميع أنحاء مصر، مع الخدمة الرئيسية في كاتدرائية القديس مرقس القبطية الأرثوذكسية في القاهرة"
        },
        "organizer": {
            "en": "The Coptic Orthodox Church of Alexandria",
            "ar": "الكنيسة القبطية الأرثوذكسية بالإسكندرية"
        },
        "admission": {
            "en": "Church services are open to the public, though space may be limited",
            "ar": "خدمات الكنيسة مفتوحة للجمهور، على الرغم من أن المساحة قد تكون محدودة"
        },
        "schedule": {
            "en": "Christmas Eve services typically begin in the evening of January 6th and continue past midnight. Christmas Day celebrations continue on January 7th.",
            "ar": "تبدأ خدمات ليلة عيد الميلاد عادة في مساء 6 يناير وتستمر بعد منتصف الليل. تستمر احتفالات يوم عيد الميلاد في 7 يناير."
        },
        "highlights": {
            "en": "Midnight mass, traditional hymns, festive meals, family gatherings, and decorated churches",
            "ar": "قداس منتصف الليل، التراتيل التقليدية، الوجبات الاحتفالية، التجمعات العائلية، والكنائس المزينة"
        },
        "historical_significance": {
            "en": "The Coptic Church follows the Julian calendar, which places Christmas on January 7th rather than December 25th. Egypt's Coptic Christian community dates back to the 1st century AD, making it one of the oldest Christian communities in the world.",
            "ar": "تتبع الكنيسة القبطية التقويم اليولياني، الذي يضع عيد الميلاد في 7 يناير بدلاً من 25 ديسمبر. يعود تاريخ مجتمع الأقباط المسيحيين في مصر إلى القرن الأول الميلادي، مما يجعله أحد أقدم المجتمعات المسيحية في العالم."
        },
        "tips": {
            "en": "If you wish to attend a Christmas service, arrive early as churches become very crowded. Dress modestly when visiting churches. Many restaurants in tourist areas offer special Christmas menus. Consider visiting the historic Hanging Church (Al-Mu'allaqah) in Coptic Cairo for a particularly beautiful Christmas experience.",
            "ar": "إذا كنت ترغب في حضور خدمة عيد الميلاد، فاحضر مبكرًا لأن الكنائس تصبح مزدحمة جدًا. ارتدِ ملابس محتشمة عند زيارة الكنائس. تقدم العديد من المطاعم في المناطق السياحية قوائم خاصة بعيد الميلاد. فكر في زيارة الكنيسة المعلقة التاريخية في مصر القبطية لتجربة عيد ميلاد جميلة بشكل خاص."
        },
        "website": "https://egypt.travel/en/events/coptic-christmas",
        "contact_info": {
            "en": "For information: Coptic Orthodox Church, +20 2 2590 6065",
            "ar": "للمعلومات: الكنيسة القبطية الأرثوذكسية، +20 2 2590 6065"
        },
        "tags": ["Coptic Christmas", "Christian celebration", "religious festival", "midnight mass", "Coptic traditions"],
        "is_featured": True
    },
    
    # Cultural Festivals
    {
        "category_id": "cultural_festivals",
        "name": {
            "en": "Cairo International Book Fair",
            "ar": "معرض القاهرة الدولي للكتاب"
        },
        "description": {
            "en": "The Cairo International Book Fair is one of the largest and oldest book fairs in the Arab world, attracting publishers, writers, and book lovers from across the globe. Established in 1969, this annual cultural event showcases millions of books in various languages, with a focus on Arabic literature. Beyond book sales, the fair features a rich program of cultural activities including author signings, panel discussions, poetry readings, and workshops. Each year, the fair selects a country as the guest of honor and a prominent cultural figure to celebrate. With hundreds of publishing houses participating and millions of visitors attending, the fair transforms Cairo into a vibrant hub of intellectual exchange and cultural dialogue for nearly two weeks.",
            "ar": "معرض القاهرة الدولي للكتاب هو أحد أكبر وأقدم معارض الكتب في العالم العربي، ويجذب الناشرين والكتاب وعشاق الكتب من جميع أنحاء العالم. تأسس عام 1969، ويعرض هذا الحدث الثقافي السنوي ملايين الكتب بمختلف اللغات، مع التركيز على الأدب العربي. بالإضافة إلى بيع الكتب، يقدم المعرض برنامجًا غنيًا من الأنشطة الثقافية بما في ذلك توقيعات المؤلفين والندوات وقراءات الشعر وورش العمل. كل عام، يختار المعرض دولة كضيف شرف وشخصية ثقافية بارزة للاحتفال بها. مع مشاركة مئات دور النشر وحضور الملايين من الزوار، يحول المعرض القاهرة إلى مركز نابض بالحياة للتبادل الفكري والحوار الثقافي لمدة أسبوعين تقريبًا."
        },
        "start_date": "2025-01-22",
        "end_date": "2025-02-04",
        "is_annual": True,
        "annual_month": 1,
        "annual_day": None,  # Varies slightly each year
        "lunar_calendar": False,
        "location_description": {
            "en": "Egypt International Exhibition Center, New Cairo",
            "ar": "مركز مصر للمعارض الدولية، القاهرة الجديدة"
        },
        "destination_id": "cairo",
        "venue": {
            "en": "Egypt International Exhibition Center (EIEC)",
            "ar": "مركز مصر للمعارض الدولية"
        },
        "organizer": {
            "en": "General Egyptian Book Organization (GEBO)",
            "ar": "الهيئة المصرية العامة للكتاب"
        },
        "admission": {
            "en": "Affordable entry tickets (approximately 5 EGP), with discounts for students and free entry on certain days",
            "ar": "تذاكر دخول بأسعار معقولة (حوالي 5 جنيه مصري)، مع خصومات للطلاب ودخول مجاني في أيام معينة"
        },
        "schedule": {
            "en": "Daily from 10:00 AM to 8:00 PM, with extended hours on weekends",
            "ar": "يوميًا من الساعة 10:00 صباحًا حتى 8:00 مساءً، مع ساعات ممتدة في عطلات نهاية الأسبوع"
        },
        "highlights": {
            "en": "Millions of books from hundreds of publishers, cultural seminars, author signings, children's activities, and special exhibitions",
            "ar": "ملايين الكتب من مئات الناشرين، ندوات ثقافية، توقيعات المؤلفين، أنشطة للأطفال، ومعارض خاصة"
        },
        "historical_significance": {
            "en": "Founded in 1969, the Cairo International Book Fair is the oldest and largest book fair in the Arab world. It has played a crucial role in promoting Arabic literature and fostering cultural exchange between Egypt and the international community.",
            "ar": "تأسس معرض القاهرة الدولي للكتاب عام 1969، وهو أقدم وأكبر معرض للكتاب في العالم العربي. لعب دورًا حاسمًا في الترويج للأدب العربي وتعزيز التبادل الثقافي بين مصر والمجتمع الدولي."
        },
        "tips": {
            "en": "Visit on weekdays to avoid crowds. Bring cash as not all vendors accept cards. Use the fair's mobile app to navigate the vast exhibition space. Consider using public transportation as parking can be limited. Check the daily program for special events and author appearances.",
            "ar": "قم بالزيارة في أيام الأسبوع لتجنب الازدحام. أحضر نقودًا لأن ليس كل البائعين يقبلون البطاقات. استخدم تطبيق المعرض للهاتف المحمول للتنقل في مساحة المعرض الشاسعة. فكر في استخدام وسائل النقل العام لأن مواقف السيارات قد تكون محدودة. تحقق من البرنامج اليومي للفعاليات الخاصة وظهور المؤلفين."
        },
        "website": "https://www.cairobookfair.org",
        "contact_info": {
            "en": "Email: info@cairobookfair.org, Phone: +20 2 2576 0645",
            "ar": "البريد الإلكتروني: info@cairobookfair.org، الهاتف: +20 2 2576 0645"
        },
        "tags": ["books", "literature", "cultural event", "publishing", "authors", "reading"],
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
    logger.info("Starting to add events and festivals (Part 1)...")
    
    # Connect to database
    conn = connect_to_db()
    
    # Add events
    added_count, skipped_count = add_events(conn, EVENTS_TO_ADD)
    
    # Close connection
    conn.close()
    
    logger.info(f"Added {added_count} new events, skipped {skipped_count} existing events.")

if __name__ == "__main__":
    main()
