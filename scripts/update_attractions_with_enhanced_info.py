#!/usr/bin/env python3
"""
Update attractions with enhanced information.

This script:
1. Updates attractions with subcategories
2. Adds visiting information
3. Adds accessibility information
4. Adds related attractions
5. Adds historical context
"""

import os
import json
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set random seed for reproducibility
random.seed(42)

def get_postgres_uri():
    """Get PostgreSQL connection URI from environment or use default"""
    return os.getenv("POSTGRES_URI", "postgresql://postgres:postgres@localhost:5432/egypt_chatbot")

def connect_to_db():
    """Connect to PostgreSQL database"""
    postgres_uri = get_postgres_uri()
    logger.info(f"Connecting to PostgreSQL database")
    conn = psycopg2.connect(postgres_uri)
    conn.autocommit = False
    return conn

def get_existing_data(conn):
    """Get existing data from the database"""
    existing_data = {}

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        # Get attraction types
        cursor.execute("SELECT type FROM attraction_types")
        existing_data['attraction_types'] = cursor.fetchall()

        # Get attraction subcategories
        cursor.execute("SELECT id, parent_type, name FROM attraction_subcategories")
        existing_data['attraction_subcategories'] = cursor.fetchall()

        # Get attractions
        cursor.execute("SELECT id, name, type, city_id, region_id FROM attractions")
        existing_data['attractions'] = cursor.fetchall()

    return existing_data

def update_attractions_with_subcategories(conn, existing_data):
    """Update attractions with subcategories"""
    logger.info("Updating attractions with subcategories")

    # Map attraction types to subcategories
    type_to_subcategories = {}
    for subcategory in existing_data['attraction_subcategories']:
        parent_type = subcategory['parent_type']
        if parent_type not in type_to_subcategories:
            type_to_subcategories[parent_type] = []
        type_to_subcategories[parent_type].append(subcategory['id'])

    # Update attractions with subcategories
    with conn.cursor() as cursor:
        for attraction in existing_data['attractions']:
            attraction_type = attraction['type']
            if attraction_type in type_to_subcategories:
                subcategories = type_to_subcategories[attraction_type]
                subcategory_id = random.choice(subcategories)

                cursor.execute("""
                    UPDATE attractions
                    SET subcategory_id = %s
                    WHERE id = %s
                """, (subcategory_id, attraction['id']))

    conn.commit()
    logger.info("Updated attractions with subcategories")

def update_pyramids_of_giza(conn):
    """Update Pyramids of Giza with enhanced information"""
    logger.info("Updating Pyramids of Giza with enhanced information")

    visiting_info = {
        'best_time_to_visit': {
            'en': 'Early morning (8:00 AM - 10:00 AM) or late afternoon (3:00 PM - 5:00 PM) to avoid the midday heat and crowds',
            'ar': 'الصباح الباكر (8:00 صباحًا - 10:00 صباحًا) أو بعد الظهر (3:00 مساءً - 5:00 مساءً) لتجنب حرارة منتصف النهار والازدحام'
        },
        'opening_hours': {
            'en': 'Daily from 8:00 AM to 5:00 PM (October to April) and 7:00 AM to 7:00 PM (May to September)',
            'ar': 'يوميًا من الساعة 8:00 صباحًا حتى 5:00 مساءً (أكتوبر إلى أبريل) ومن 7:00 صباحًا حتى 7:00 مساءً (مايو إلى سبتمبر)'
        },
        'recommended_duration': {
            'en': '3-4 hours to explore the entire complex',
            'ar': '3-4 ساعات لاستكشاف المجمع بأكمله'
        },
        'entrance_fees': {
            'en': 'Pyramids Area: 240 EGP for foreigners, 60 EGP for foreign students. Inside the Great Pyramid: 440 EGP. Inside Khafre or Menkaure Pyramid: 100 EGP each.',
            'ar': 'منطقة الأهرامات: 240 جنيه مصري للأجانب، 60 جنيه مصري للطلاب الأجانب. داخل الهرم الأكبر: 440 جنيه مصري. داخل هرم خفرع أو منقرع: 100 جنيه مصري لكل منهما.'
        },
        'tickets': {
            'en': 'Available at the entrance gate. Separate tickets required for entering the pyramids interiors.',
            'ar': 'متوفرة عند بوابة الدخول. تذاكر منفصلة مطلوبة لدخول الأهرامات من الداخل.'
        },
        'guided_tours': {
            'en': 'Official guides available at the entrance. Recommended for better understanding of the historical significance.',
            'ar': 'المرشدين الرسميين متوفرين عند المدخل. ينصح بهم لفهم أفضل للأهمية التاريخية.'
        },
        'photography': {
            'en': 'Photography is allowed in most areas. Extra fee for professional photography equipment.',
            'ar': 'التصوير مسموح به في معظم المناطق. رسوم إضافية لمعدات التصوير الاحترافية.'
        },
        'tips': {
            'en': [
                'Wear comfortable shoes and sun protection',
                'Bring plenty of water',
                'Be prepared for persistent vendors and camel ride offers',
                'Consider hiring a guide for historical context',
                'The interior of the pyramids is hot, cramped, and not recommended for those with claustrophobia or respiratory issues'
            ],
            'ar': [
                'ارتداء أحذية مريحة وواقي من الشمس',
                'إحضار الكثير من الماء',
                'كن مستعدًا للباعة المصرين وعروض ركوب الجمال',
                'فكر في استئجار مرشد للسياق التاريخي',
                'داخل الأهرامات حار وضيق ولا ينصح به للأشخاص الذين يعانون من رهاب الأماكن المغلقة أو مشاكل في الجهاز التنفسي'
            ]
        },
        'nearby_facilities': {
            'en': 'Restrooms, cafes, and souvenir shops available near the entrance',
            'ar': 'دورات المياه والمقاهي ومحلات الهدايا التذكارية متوفرة بالقرب من المدخل'
        },
        'seasonal_considerations': {
            'en': 'Avoid summer months (June-August) due to extreme heat. Winter months (December-February) offer the most comfortable temperatures.',
            'ar': 'تجنب أشهر الصيف (يونيو-أغسطس) بسبب الحرارة الشديدة. أشهر الشتاء (ديسمبر-فبراير) توفر درجات حرارة أكثر راحة.'
        }
    }

    accessibility_info = {
        'wheelchair_accessibility': {
            'en': 'Limited. The area around the pyramids has uneven terrain and sand. The interior of the pyramids is not wheelchair accessible.',
            'ar': 'محدودة. المنطقة المحيطة بالأهرامات بها تضاريس غير مستوية ورمال. داخل الأهرامات غير مناسب للكراسي المتحركة.'
        },
        'mobility_requirements': {
            'en': 'Exploring the site requires significant walking on uneven terrain. Entering the pyramids requires climbing steep, narrow passages.',
            'ar': 'استكشاف الموقع يتطلب المشي لمسافات كبيرة على أرض غير مستوية. دخول الأهرامات يتطلب تسلق ممرات ضيقة وشديدة الانحدار.'
        },
        'services_for_disabled': {
            'en': 'Limited services available. No specific facilities for visitors with disabilities.',
            'ar': 'الخدمات المتاحة محدودة. لا توجد مرافق محددة للزوار ذوي الإعاقة.'
        },
        'assistance_animals': {
            'en': "Service animals are generally permitted, but it's advisable to check in advance.",
            'ar': 'يُسمح عمومًا بحيوانات الخدمة، ولكن يُنصح بالتحقق مسبقًا.'
        },
        'sensory_considerations': {
            'en': 'The site can be very bright and hot. Inside the pyramids is dark, hot, and can trigger claustrophobia.',
            'ar': 'الموقع يمكن أن يكون ساطعًا وحارًا جدًا. داخل الأهرامات مظلم وحار ويمكن أن يثير رهاب الأماكن المغلقة.'
        },
        'rest_areas': {
            'en': 'Limited shaded areas available. Benches are scarce.',
            'ar': 'مناطق الظل المتاحة محدودة. المقاعد نادرة.'
        }
    }

    historical_context = {
        'construction_period': {
            'en': "The Great Pyramid of Khufu was built around 2560 BCE during the Fourth Dynasty of Egypt's Old Kingdom. The Pyramid of Khafre was built around 2530 BCE, and the Pyramid of Menkaure around 2510 BCE.",
            'ar': 'بُني هرم خوفو الأكبر حوالي 2560 قبل الميلاد خلال الأسرة الرابعة من المملكة القديمة في مصر. بُني هرم خفرع حوالي 2530 قبل الميلاد، وهرم منقرع حوالي 2510 قبل الميلاد.'
        },
        'builders': {
            'en': "Contrary to popular belief, the pyramids were not built by slaves but by skilled workers and farmers during the Nile's annual flood when they could not work on their fields.",
            'ar': 'على عكس الاعتقاد الشائع، لم تُبن الأهرامات من قبل العبيد بل من قبل عمال مهرة ومزارعين خلال الفيضان السنوي للنيل عندما لم يتمكنوا من العمل في حقولهم.'
        },
        'purpose': {
            'en': 'The pyramids were built as tombs for the pharaohs and their consorts. They were part of a larger funerary complex that included temples, smaller pyramids for queens, and mastaba tombs for nobles.',
            'ar': 'بُنيت الأهرامات كمقابر للفراعنة وقريناتهم. كانت جزءًا من مجمع جنائزي أكبر يشمل معابد وأهرامات أصغر للملكات ومقابر مصطبة للنبلاء.'
        },
        'construction_techniques': {
            'en': "The exact methods used to build the pyramids remain a subject of debate. They likely involved ramps, levers, and other simple machines. The precision of the construction demonstrates the Egyptians' advanced knowledge of mathematics, astronomy, and engineering.",
            'ar': 'الطرق الدقيقة المستخدمة لبناء الأهرامات لا تزال موضوع نقاش. من المحتمل أنها تضمنت منحدرات وروافع وآلات بسيطة أخرى. تُظهر دقة البناء المعرفة المتقدمة للمصريين في الرياضيات والفلك والهندسة.'
        },
        'significance': {
            'en': 'The Pyramids of Giza are the only surviving structure of the Seven Wonders of the Ancient World. They represent the pinnacle of ancient Egyptian architectural achievements and demonstrate the power and wealth of the pharaohs who commissioned them.',
            'ar': 'أهرامات الجيزة هي البنية الوحيدة الباقية من عجائب الدنيا السبع في العالم القديم. تمثل ذروة الإنجازات المعمارية المصرية القديمة وتدل على قوة وثروة الفراعنة الذين أمروا ببنائها.'
        },
        'rediscovery': {
            'en': 'While the pyramids were never truly "lost," European interest in them was rekindled during Napoleon\'s Egyptian campaign (1798-1801), which included scientific studies of the monuments.',
            'ar': 'على الرغم من أن الأهرامات لم "تُفقد" حقًا، إلا أن الاهتمام الأوروبي بها تجدد خلال الحملة المصرية لنابليون (1798-1801)، والتي شملت دراسات علمية للآثار.'
        },
        'modern_context': {
            'en': "Today, the Pyramids of Giza are Egypt's most iconic landmarks and a major tourist attraction. They continue to be studied by archaeologists and historians, with new discoveries still being made in the surrounding necropolis.",
            'ar': 'اليوم، تعد أهرامات الجيزة أكثر معالم مصر شهرة وجذبًا للسياح. لا يزال علماء الآثار والمؤرخون يدرسونها، مع استمرار اكتشافات جديدة في المقبرة المحيطة.'
        }
    }

    related_attractions = [
        'sphinx',
        'valley_of_the_kings',
        'egyptian_museum',
        'saqqara',
        'memphis'
    ]

    with conn.cursor() as cursor:
        cursor.execute("""
            UPDATE attractions
            SET
                subcategory_id = 'pyramid',
                visiting_info = %s::jsonb,
                accessibility_info = %s::jsonb,
                historical_context = %s::jsonb,
                related_attractions = %s
            WHERE id = 'pyramids_of_giza'
        """, (
            json.dumps(visiting_info),
            json.dumps(accessibility_info),
            json.dumps(historical_context),
            related_attractions
        ))

    conn.commit()
    logger.info("Updated Pyramids of Giza with enhanced information")

def update_karnak_temple(conn):
    """Update Karnak Temple with enhanced information"""
    logger.info("Updating Karnak Temple with enhanced information")

    visiting_info = {
        'best_time_to_visit': {
            'en': 'Early morning (8:00 AM - 10:00 AM) or late afternoon (4:00 PM - 6:00 PM) to avoid the midday heat and enjoy better lighting for photography',
            'ar': 'الصباح الباكر (8:00 صباحًا - 10:00 صباحًا) أو بعد الظهر (4:00 مساءً - 6:00 مساءً) لتجنب حرارة منتصف النهار والاستمتاع بإضاءة أفضل للتصوير'
        },
        'opening_hours': {
            'en': 'Summer (April to September): 6:00 AM to 6:00 PM. Winter (October to March): 6:30 AM to 5:00 PM',
            'ar': 'الصيف (أبريل إلى سبتمبر): 6:00 صباحًا إلى 6:00 مساءً. الشتاء (أكتوبر إلى مارس): 6:30 صباحًا إلى 5:00 مساءً'
        },
        'recommended_duration': {
            'en': '2-3 hours to explore the main sections, 4-5 hours for a comprehensive visit',
            'ar': '2-3 ساعات لاستكشاف الأقسام الرئيسية، 4-5 ساعات للزيارة الشاملة'
        },
        'entrance_fees': {
            'en': '220 EGP for foreigners, 110 EGP for foreign students',
            'ar': '220 جنيه مصري للأجانب، 110 جنيه مصري للطلاب الأجانب'
        },
        'tickets': {
            'en': 'Available at the entrance gate. Combined tickets with Luxor Temple are available.',
            'ar': 'متوفرة عند بوابة الدخول. تتوفر تذاكر مشتركة مع معبد الأقصر.'
        },
        'guided_tours': {
            'en': 'Official guides available at the entrance. Highly recommended due to the size and historical complexity of the site.',
            'ar': 'المرشدين الرسميين متوفرين عند المدخل. ينصح بهم بشدة نظرًا لحجم الموقع وتعقيده التاريخي.'
        },
        'photography': {
            'en': 'Photography is allowed. Extra fee for professional equipment and tripods.',
            'ar': 'التصوير مسموح به. رسوم إضافية للمعدات الاحترافية والحوامل.'
        },
        'tips': {
            'en': [
                'Wear comfortable shoes and sun protection',
                'Bring plenty of water',
                'Consider visiting as part of a guided tour to understand the historical significance',
                "Don't miss the Sound and Light Show in the evening",
                'Visit the Sacred Lake and the massive columns in the Hypostyle Hall'
            ],
            'ar': [
                'ارتداء أحذية مريحة وواقي من الشمس',
                'إحضار الكثير من الماء',
                'فكر في الزيارة كجزء من جولة مرشدة لفهم الأهمية التاريخية',
                'لا تفوت عرض الصوت والضوء في المساء',
                'زيارة البحيرة المقدسة والأعمدة الضخمة في قاعة الأعمدة'
            ]
        },
        'nearby_facilities': {
            'en': 'Restrooms, cafes, and souvenir shops available near the entrance',
            'ar': 'دورات المياه والمقاهي ومحلات الهدايا التذكارية متوفرة بالقرب من المدخل'
        },
        'seasonal_considerations': {
            'en': 'Avoid summer months (June-August) due to extreme heat. Winter months (December-February) offer the most comfortable temperatures.',
            'ar': 'تجنب أشهر الصيف (يونيو-أغسطس) بسبب الحرارة الشديدة. أشهر الشتاء (ديسمبر-فبراير) توفر درجات حرارة أكثر راحة.'
        }
    }

    accessibility_info = {
        'wheelchair_accessibility': {
            'en': 'Partially accessible. Main pathways are paved, but some areas have uneven terrain and steps.',
            'ar': 'يمكن الوصول إليها جزئيًا. الممرات الرئيسية معبدة، لكن بعض المناطق بها تضاريس غير مستوية ودرجات.'
        },
        'mobility_requirements': {
            'en': 'Exploring the full site requires significant walking. Some areas have steps and uneven surfaces.',
            'ar': 'استكشاف الموقع بالكامل يتطلب المشي لمسافات كبيرة. بعض المناطق بها درجات وأسطح غير مستوية.'
        },
        'services_for_disabled': {
            'en': 'Limited services available. Some accessible pathways have been added in recent renovations.',
            'ar': 'الخدمات المتاحة محدودة. تمت إضافة بعض المسارات التي يمكن الوصول إليها في التجديدات الأخيرة.'
        },
        'assistance_animals': {
            'en': "Service animals are generally permitted, but it's advisable to check in advance.",
            'ar': 'يُسمح عمومًا بحيوانات الخدمة، ولكن يُنصح بالتحقق مسبقًا.'
        },
        'sensory_considerations': {
            'en': 'The site can be very bright and hot. Sound and Light Show in the evening uses loud sounds and bright lights.',
            'ar': 'الموقع يمكن أن يكون ساطعًا وحارًا جدًا. عرض الصوت والضوء في المساء يستخدم أصواتًا عالية وأضواء ساطعة.'
        },
        'rest_areas': {
            'en': 'Several shaded areas and benches available throughout the complex.',
            'ar': 'تتوفر العديد من المناطق المظللة والمقاعد في جميع أنحاء المجمع.'
        }
    }

    historical_context = {
        'construction_period': {
            'en': 'Construction began during the Middle Kingdom (around 2000 BCE) and continued for over 1,500 years until the Ptolemaic period (around 30 BCE), with each pharaoh adding or modifying structures.',
            'ar': 'بدأ البناء خلال المملكة الوسطى (حوالي 2000 قبل الميلاد) واستمر لأكثر من 1500 عام حتى العصر البطلمي (حوالي 30 قبل الميلاد)، مع قيام كل فرعون بإضافة أو تعديل الهياكل.'
        },
        'religious_significance': {
            'en': 'Karnak was the main place of worship for the Theban triad of gods: Amun, Mut, and Khonsu. The temple complex was considered the "most select of places" and the earthly home of Amun-Ra, the king of gods.',
            'ar': 'كان الكرنك المكان الرئيسي للعبادة لثالوث طيبة من الآلهة: آمون وموت وخونسو. كان مجمع المعبد يعتبر "أكثر الأماكن اختيارًا" والمنزل الأرضي لآمون-رع، ملك الآلهة.'
        },
        'architectural_features': {
            'en': 'The complex includes the Great Hypostyle Hall with 134 massive columns, the Sacred Lake, numerous temples, chapels, pylons, and obelisks. The main temple is aligned with the winter solstice sunrise.',
            'ar': 'يتضمن المجمع قاعة الأعمدة الكبرى مع 134 عمودًا ضخمًا، والبحيرة المقدسة، والعديد من المعابد والمصليات والبوابات والمسلات. المعبد الرئيسي متوافق مع شروق الشمس في الانقلاب الشتوي.'
        },
        'historical_events': {
            'en': 'Karnak witnessed many significant historical events, including the religious revolution of Akhenaten, who temporarily suppressed the cult of Amun, and the restoration of traditional religion under Tutankhamun and later pharaohs.',
            'ar': 'شهد الكرنك العديد من الأحداث التاريخية المهمة، بما في ذلك الثورة الدينية لأخناتون، الذي قمع مؤقتًا عبادة آمون، واستعادة الدين التقليدي تحت حكم توت عنخ آمون والفراعنة اللاحقين.'
        },
        'decline': {
            'en': "The temple's importance declined with the fall of the New Kingdom and the shift of power to northern Egypt. It continued to function as a religious center until the rise of Christianity in Egypt, when pagan temples were closed.",
            'ar': 'تراجعت أهمية المعبد مع سقوط المملكة الحديثة وانتقال السلطة إلى شمال مصر. استمر في العمل كمركز ديني حتى صعود المسيحية في مصر، عندما تم إغلاق المعابد الوثنية.'
        },
        'rediscovery': {
            'en': 'European travelers and scholars began documenting Karnak in the 18th and 19th centuries. Systematic archaeological work began in the late 19th century and continues to this day.',
            'ar': 'بدأ المسافرون والعلماء الأوروبيون في توثيق الكرنك في القرنين الثامن عشر والتاسع عشر. بدأ العمل الأثري المنهجي في أواخر القرن التاسع عشر ويستمر حتى يومنا هذا.'
        },
        'modern_significance': {
            'en': "Today, Karnak is one of Egypt's most visited archaeological sites and a UNESCO World Heritage Site. It provides invaluable insights into ancient Egyptian religion, art, and architecture.",
            'ar': 'اليوم، يعد الكرنك أحد أكثر المواقع الأثرية زيارة في مصر وموقعًا للتراث العالمي لليونسكو. يقدم رؤى لا تقدر بثمن في الدين والفن والعمارة المصرية القديمة.'
        }
    }

    related_attractions = [
        'luxor_temple',
        'valley_of_the_kings',
        'hatshepsut_temple',
        'colossi_of_memnon',
        'ramesseum'
    ]

    with conn.cursor() as cursor:
        cursor.execute("""
            UPDATE attractions
            SET
                subcategory_id = 'ancient_egyptian_temple',
                visiting_info = %s::jsonb,
                accessibility_info = %s::jsonb,
                historical_context = %s::jsonb,
                related_attractions = %s
            WHERE id = 'karnak_temple'
        """, (
            json.dumps(visiting_info),
            json.dumps(accessibility_info),
            json.dumps(historical_context),
            related_attractions
        ))

    conn.commit()
    logger.info("Updated Karnak Temple with enhanced information")

def main():
    """Main function to update attractions with enhanced information"""
    try:
        # Connect to database
        conn = connect_to_db()

        # Get existing data
        existing_data = get_existing_data(conn)

        # Update attractions with subcategories
        update_attractions_with_subcategories(conn, existing_data)

        # Update specific attractions with detailed information
        update_pyramids_of_giza(conn)
        update_karnak_temple(conn)

        logger.info("Successfully updated attractions with enhanced information")
        return True

    except Exception as e:
        logger.error(f"Error updating attractions with enhanced information: {str(e)}", exc_info=True)
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = main()
    if success:
        exit(0)
    else:
        exit(1)
