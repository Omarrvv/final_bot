#!/usr/bin/env python3
"""
Generate events and festivals data for the Egypt Tourism Chatbot database.

This script:
1. Creates events and festivals for Egyptian tourism
2. Categorizes events and festivals by type
3. Links events and festivals to relevant destinations
"""

import os
import json
import random
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
import numpy as np
from pgvector.psycopg2 import register_vector
from datetime import date, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set random seed for reproducibility
random.seed(42)
np.random.seed(42)

def get_postgres_uri():
    """Get PostgreSQL connection URI from environment or use default"""
    return os.getenv("POSTGRES_URI", "postgresql://postgres:postgres@localhost:5432/egypt_chatbot")

def connect_to_db():
    """Connect to PostgreSQL database"""
    postgres_uri = get_postgres_uri()
    logger.info(f"Connecting to PostgreSQL database")
    conn = psycopg2.connect(postgres_uri)
    conn.autocommit = False

    # Register pgvector extension
    register_vector(conn)

    return conn

def get_existing_data(conn):
    """Get existing data from the database"""
    existing_data = {}

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        # Get event categories
        cursor.execute("SELECT id, name FROM event_categories")
        existing_data['event_categories'] = cursor.fetchall()

        # Get destinations
        cursor.execute("SELECT id, name, type FROM destinations")
        existing_data['destinations'] = cursor.fetchall()

        # Get existing events and festivals
        cursor.execute("SELECT id, name FROM events_festivals")
        existing_data['events_festivals'] = cursor.fetchall()

    return existing_data

def generate_embedding():
    """Generate a random embedding vector"""
    # Generate a random 1536-dimensional vector (typical for embeddings)
    embedding = np.random.normal(0, 1, 1536)
    # Normalize to unit length
    embedding = embedding / np.linalg.norm(embedding)
    return embedding

def generate_events_festivals(conn, existing_data):
    """Generate events and festivals data"""
    logger.info("Generating events and festivals data")

    # Prepare events and festivals data
    all_events = []

    # Abu Simbel Sun Festival
    abu_simbel_sun_festival = {
        'category_id': 'historical_commemorations',
        'name': {
            'en': 'Abu Simbel Sun Festival',
            'ar': 'مهرجان شمس أبو سمبل'
        },
        'description': {
            'en': """The Abu Simbel Sun Festival is a biannual event that takes place at the Great Temple of Ramses II in Abu Simbel. Twice a year, on February 22 and October 22, the sun's rays penetrate the temple's inner sanctuary and illuminate the statues of Ramses II and the gods Amun and Ra, leaving only the god of darkness, Ptah, in shadow. This phenomenon was engineered by the ancient Egyptians over 3,200 years ago and continues to draw visitors from around the world who gather before dawn to witness this remarkable display of ancient astronomical precision.""",
            'ar': """مهرجان شمس أبو سمبل هو حدث نصف سنوي يقام في معبد رمسيس الثاني الكبير في أبو سمبل. مرتين في السنة، في 22 فبراير و22 أكتوبر، تخترق أشعة الشمس حرم المعبد الداخلي وتضيء تماثيل رمسيس الثاني والآلهة آمون ورع، تاركة إله الظلام، بتاح، في الظل. تم تصميم هذه الظاهرة من قبل المصريين القدماء منذ أكثر من 3200 عام وما زالت تجذب الزوار من جميع أنحاء العالم الذين يتجمعون قبل الفجر لمشاهدة هذا العرض الرائع للدقة الفلكية القديمة."""
        },
        'start_date': date(2024, 2, 22),  # First occurrence in 2024
        'end_date': date(2024, 2, 22),    # One-day event
        'is_annual': True,
        'annual_month': 2,  # February
        'annual_day': 22,   # 22nd day
        'lunar_calendar': False,
        'location_description': {
            'en': 'Abu Simbel Temples, Aswan Governorate, southern Egypt',
            'ar': 'معابد أبو سمبل، محافظة أسوان، جنوب مصر'
        },
        'destination_id': 'abu_simbel',
        'venue': {
            'name': {
                'en': 'Great Temple of Ramses II',
                'ar': 'معبد رمسيس الثاني الكبير'
            },
            'address': {
                'en': 'Abu Simbel, Aswan Governorate, Egypt',
                'ar': 'أبو سمبل، محافظة أسوان، مصر'
            },
            'coordinates': {
                'latitude': 22.3372,
                'longitude': 31.6258
            }
        },
        'organizer': {
            'name': {
                'en': 'Egyptian Ministry of Tourism and Antiquities',
                'ar': 'وزارة السياحة والآثار المصرية'
            },
            'website': 'https://www.egypt.travel',
            'contact': '+20 2 27358761'
        },
        'admission': {
            'price': {
                'en': 'Regular temple admission fees apply (approximately 240 EGP for foreigners, 60 EGP for students)',
                'ar': 'تطبق رسوم دخول المعبد العادية (حوالي 240 جنيه مصري للأجانب، 60 جنيه مصري للطلاب)'
            },
            'tickets': {
                'en': 'Available at the temple entrance or through tour operators',
                'ar': 'متوفرة عند مدخل المعبد أو من خلال منظمي الرحلات'
            }
        },
        'schedule': {
            'en': [
                '03:30 - 04:30: Arrival and security check',
                '04:30 - 05:30: Gathering at the temple entrance',
                '05:30 - 06:30: Sun alignment phenomenon (exact timing varies slightly)',
                '06:30 - 09:00: Exploration of the temples and celebrations'
            ],
            'ar': [
                '03:30 - 04:30: الوصول والفحص الأمني',
                '04:30 - 05:30: التجمع عند مدخل المعبد',
                '05:30 - 06:30: ظاهرة محاذاة الشمس (التوقيت الدقيق يختلف قليلاً)',
                '06:30 - 09:00: استكشاف المعابد والاحتفالات'
            ]
        },
        'highlights': {
            'en': [
                "Witnessing the sun's rays illuminating the inner sanctuary statues",
                'Traditional Nubian music and dance performances',
                'Special guided tours explaining the astronomical and historical significance',
                'Photography opportunities of this rare phenomenon'
            ],
            'ar': [
                'مشاهدة أشعة الشمس وهي تضيء تماثيل الحرم الداخلي',
                'عروض الموسيقى والرقص النوبية التقليدية',
                'جولات إرشادية خاصة تشرح الأهمية الفلكية والتاريخية',
                'فرص التصوير الفوتوغرافي لهذه الظاهرة النادرة'
            ]
        },
        'historical_significance': {
            'en': """The Abu Simbel temples were built during the reign of Pharaoh Ramses II in the 13th century BCE as a monument to himself and his queen Nefertari. The precise alignment of the temple was an intentional design to honor the pharaoh on his birthday and coronation day (believed to be October 22), with the second alignment (February 22) marking an equally significant date. In the 1960s, the entire temple complex was relocated to higher ground to prevent it from being submerged during the creation of Lake Nasser following the construction of the Aswan High Dam. Engineers carefully preserved the solar alignment during this massive relocation project.""",
            'ar': """بنيت معابد أبو سمبل خلال عهد الفرعون رمسيس الثاني في القرن الثالث عشر قبل الميلاد كنصب تذكاري لنفسه ولملكته نفرتاري. كان المحاذاة الدقيقة للمعبد تصميمًا متعمدًا لتكريم الفرعون في عيد ميلاده ويوم تتويجه (يعتقد أنه 22 أكتوبر)، مع المحاذاة الثانية (22 فبراير) التي تميز تاريخًا مهمًا بنفس القدر. في الستينيات، تم نقل مجمع المعبد بأكمله إلى أرض أعلى لمنعه من الغمر أثناء إنشاء بحيرة ناصر بعد بناء السد العالي في أسوان. حافظ المهندسون بعناية على المحاذاة الشمسية خلال مشروع النقل الضخم هذا."""
        },
        'tips': {
            'en': [
                'Arrive early (around 4:00 AM) to secure a good viewing position',
                'Bring warm clothing as pre-dawn temperatures can be cold, especially in February',
                'Book accommodation in Aswan in advance as local options are limited',
                'Consider joining an organized tour that includes transportation from Aswan',
                'Bring a flashlight for the pre-dawn darkness',
                'Photography is allowed but tripods may require special permission'
            ],
            'ar': [
                'الوصول مبكرًا (حوالي الساعة 4:00 صباحًا) لتأمين موقع مشاهدة جيد',
                'إحضار ملابس دافئة حيث يمكن أن تكون درجات الحرارة قبل الفجر باردة، خاصة في فبراير',
                'حجز الإقامة في أسوان مقدمًا حيث أن الخيارات المحلية محدودة',
                'النظر في الانضمام إلى جولة منظمة تشمل النقل من أسوان',
                'إحضار مصباح يدوي لظلام ما قبل الفجر',
                'التصوير الفوتوغرافي مسموح به ولكن قد تتطلب الحوامل إذنًا خاصًا'
            ]
        },
        'images': {
            'main': 'abu_simbel_sun_festival_main.jpg',
            'gallery': [
                'abu_simbel_sun_festival_alignment.jpg',
                'abu_simbel_sun_festival_crowd.jpg',
                'abu_simbel_sun_festival_temple.jpg',
                'abu_simbel_sun_festival_celebration.jpg'
            ]
        },
        'website': 'https://www.egypt.travel/en/events/abu-simbel-sun-festival',
        'contact_info': {
            'phone': '+20 97 2310288',
            'email': 'info@egypt.travel',
            'social_media': {
                'facebook': 'https://www.facebook.com/experienceegypt',
                'instagram': 'https://www.instagram.com/experienceegypt',
                'twitter': 'https://twitter.com/experienceegypt'
            }
        },
        'tags': ['sun festival', 'abu simbel', 'ramses ii', 'astronomical', 'ancient egypt', 'temple', 'aswan'],
        'is_featured': True
    }

    # Cairo International Film Festival
    cairo_film_festival = {
        'category_id': 'film_festivals',
        'name': {
            'en': 'Cairo International Film Festival',
            'ar': 'مهرجان القاهرة السينمائي الدولي'
        },
        'description': {
            'en': """The Cairo International Film Festival (CIFF) is one of the oldest and most prestigious film festivals in the Middle East and Africa. Established in 1976, it is the only international film festival in the Arab world accredited by the International Federation of Film Producers Associations (FIAPF). The festival showcases a diverse selection of films from around the world, with a special focus on Arab cinema. It features international competitions, retrospectives, tributes, workshops, panel discussions, and networking opportunities for filmmakers. The festival attracts renowned directors, actors, and film industry professionals, making it a significant cultural event in Egypt's capital.""",
            'ar': """مهرجان القاهرة السينمائي الدولي هو أحد أقدم وأرقى المهرجانات السينمائية في الشرق الأوسط وأفريقيا. تأسس عام 1976، وهو المهرجان السينمائي الدولي الوحيد في العالم العربي المعتمد من قبل الاتحاد الدولي لجمعيات منتجي الأفلام (FIAPF). يعرض المهرجان مجموعة متنوعة من الأفلام من جميع أنحاء العالم، مع تركيز خاص على السينما العربية. يتضمن مسابقات دولية، واستعادات، وتكريمات، وورش عمل، وحلقات نقاش، وفرص للتواصل للمخرجين. يجذب المهرجان مخرجين وممثلين ومهنيين في صناعة السينما مشهورين، مما يجعله حدثًا ثقافيًا مهمًا في عاصمة مصر."""
        },
        'start_date': date(2024, 11, 15),  # Approximate date for 2024
        'end_date': date(2024, 11, 24),    # Typically 10 days
        'is_annual': True,
        'annual_month': 11,  # November
        'annual_day': 15,    # Approximate start day
        'lunar_calendar': False,
        'location_description': {
            'en': 'Various venues across Cairo, with the Cairo Opera House serving as the main venue',
            'ar': 'أماكن مختلفة في جميع أنحاء القاهرة، مع دار الأوبرا المصرية كمكان رئيسي'
        },
        'destination_id': 'cairo',
        'venue': {
            'name': {
                'en': 'Cairo Opera House and various cinemas',
                'ar': 'دار الأوبرا المصرية وقاعات سينما متعددة'
            },
            'address': {
                'en': 'Cairo Opera House, El Gezira, Zamalek, Cairo',
                'ar': 'دار الأوبرا المصرية، الجزيرة، الزمالك، القاهرة'
            },
            'coordinates': {
                'latitude': 30.0420,
                'longitude': 31.2244
            }
        },
        'organizer': {
            'name': {
                'en': 'Cairo International Film Festival Foundation',
                'ar': 'مؤسسة مهرجان القاهرة السينمائي الدولي'
            },
            'website': 'https://www.ciff.org.eg',
            'contact': '+20 2 27383678'
        },
        'admission': {
            'price': {
                'en': 'Ticket prices range from 50-100 EGP for regular screenings. Special events and galas may have higher prices.',
                'ar': 'تتراوح أسعار التذاكر من 50-100 جنيه مصري للعروض العادية. قد تكون للفعاليات الخاصة والعروض الاحتفالية أسعار أعلى.'
            },
            'tickets': {
                'en': 'Available online through the festival website and at venue box offices',
                'ar': 'متوفرة عبر الإنترنت من خلال موقع المهرجان وفي شبابيك التذاكر في أماكن العرض'
            }
        },
        'schedule': {
            'en': [
                'Daily film screenings from 10:00 AM to midnight',
                'Opening ceremony on the first evening',
                'Panel discussions and workshops throughout the festival',
                'Closing ceremony and awards on the final evening'
            ],
            'ar': [
                'عروض أفلام يومية من الساعة 10:00 صباحًا حتى منتصف الليل',
                'حفل الافتتاح في المساء الأول',
                'حلقات نقاش وورش عمل طوال فترة المهرجان',
                'حفل الختام وتوزيع الجوائز في المساء الأخير'
            ]
        },
        'highlights': {
            'en': [
                'International Competition for feature and short films',
                'Horizons of Arab Cinema Competition',
                'Cairo Film Connection for project development',
                'Red carpet events with Egyptian and international celebrities',
                'Retrospectives of influential filmmakers',
                'Special screenings of restored classics'
            ],
            'ar': [
                'المسابقة الدولية للأفلام الروائية والقصيرة',
                'مسابقة آفاق السينما العربية',
                'ملتقى القاهرة السينمائي لتطوير المشاريع',
                'فعاليات السجادة الحمراء مع مشاهير مصريين ودوليين',
                'استعادات لأعمال مخرجين مؤثرين',
                'عروض خاصة للكلاسيكيات المرممة'
            ]
        },
        'historical_significance': {
            'en': """The Cairo International Film Festival was established in 1976, making it one of the oldest film festivals in the Arab world. It was founded to promote cultural exchange through cinema and to showcase Egyptian and Arab films to an international audience. Over the decades, it has grown in prominence and has been attended by numerous international film luminaries. The festival has played a crucial role in supporting Arab cinema and providing a platform for emerging filmmakers from the region. It has survived political upheavals and economic challenges to remain a cornerstone of Egypt's cultural calendar.""",
            'ar': """تأسس مهرجان القاهرة السينمائي الدولي عام 1976، مما يجعله أحد أقدم المهرجانات السينمائية في العالم العربي. تم تأسيسه لتعزيز التبادل الثقافي من خلال السينما وعرض الأفلام المصرية والعربية للجمهور الدولي. على مدى العقود، نما في الأهمية وحضره العديد من مشاهير السينما الدوليين. لعب المهرجان دورًا حاسمًا في دعم السينما العربية وتوفير منصة للمخرجين الناشئين من المنطقة. لقد نجا من الاضطرابات السياسية والتحديات الاقتصادية ليظل حجر الزاوية في التقويم الثقافي لمصر."""
        },
        'tips': {
            'en': [
                'Book tickets for popular films and events in advance',
                'Check the festival website for the full program and schedule updates',
                'Consider purchasing a festival pass for access to multiple screenings',
                'Arrive early for red carpet events and gala screenings',
                'Use Cairo metro to avoid traffic when traveling between venues',
                'Dress formally for opening and closing ceremonies'
            ],
            'ar': [
                'حجز تذاكر للأفلام والفعاليات الشعبية مقدمًا',
                'مراجعة موقع المهرجان للبرنامج الكامل وتحديثات الجدول',
                'النظر في شراء تذكرة المهرجان للوصول إلى عروض متعددة',
                'الوصول مبكرًا لفعاليات السجادة الحمراء والعروض الاحتفالية',
                'استخدام مترو القاهرة لتجنب الازدحام عند التنقل بين الأماكن',
                'ارتداء ملابس رسمية لحفلات الافتتاح والختام'
            ]
        },
        'images': {
            'main': 'cairo_film_festival_main.jpg',
            'gallery': [
                'cairo_film_festival_red_carpet.jpg',
                'cairo_film_festival_screening.jpg',
                'cairo_film_festival_awards.jpg',
                'cairo_film_festival_audience.jpg'
            ]
        },
        'website': 'https://www.ciff.org.eg',
        'contact_info': {
            'phone': '+20 2 27383678',
            'email': 'info@ciff.org.eg',
            'social_media': {
                'facebook': 'https://www.facebook.com/CairoFilms',
                'instagram': 'https://www.instagram.com/cairofilms',
                'twitter': 'https://twitter.com/cairofilms'
            }
        },
        'tags': ['film festival', 'cinema', 'cairo', 'cultural event', 'international', 'arab cinema', 'red carpet'],
        'is_featured': True
    }

    # Combine all events and festivals
    all_events.append(abu_simbel_sun_festival)
    all_events.append(cairo_film_festival)

    # Insert events and festivals into database
    with conn.cursor() as cursor:
        for event in all_events:
            cursor.execute("""
                INSERT INTO events_festivals (
                    category_id, name, description, start_date, end_date,
                    is_annual, annual_month, annual_day, lunar_calendar,
                    location_description, destination_id, venue, organizer,
                    admission, schedule, highlights, historical_significance,
                    tips, images, website, contact_info, tags, is_featured,
                    embedding, created_at, updated_at, user_id
                ) VALUES (
                    %s, %s::jsonb, %s::jsonb, %s, %s,
                    %s, %s, %s, %s,
                    %s::jsonb, %s, %s::jsonb, %s::jsonb,
                    %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb,
                    %s::jsonb, %s::jsonb, %s, %s::jsonb, %s, %s,
                    %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'system'
                )
            """, (
                event['category_id'],
                json.dumps(event['name']),
                json.dumps(event['description']),
                event['start_date'],
                event['end_date'],
                event['is_annual'],
                event['annual_month'],
                event['annual_day'],
                event['lunar_calendar'],
                json.dumps(event['location_description']),
                event['destination_id'],
                json.dumps(event['venue']),
                json.dumps(event['organizer']),
                json.dumps(event['admission']),
                json.dumps(event['schedule']),
                json.dumps(event['highlights']),
                json.dumps(event['historical_significance']),
                json.dumps(event['tips']),
                json.dumps(event['images']),
                event['website'],
                json.dumps(event['contact_info']),
                event['tags'],
                event['is_featured'],
                generate_embedding()
            ))

    conn.commit()
    logger.info(f"Generated {len(all_events)} events and festivals")
    return all_events

def verify_events_festivals(conn):
    """Verify the events and festivals data in the database"""
    try:
        with conn.cursor() as cursor:
            # Check event categories count
            cursor.execute("SELECT COUNT(*) FROM event_categories")
            category_count = cursor.fetchone()[0]
            logger.info(f"Total event categories in database: {category_count}")

            # Check events and festivals count
            cursor.execute("SELECT COUNT(*) FROM events_festivals")
            event_count = cursor.fetchone()[0]
            logger.info(f"Total events and festivals in database: {event_count}")

            # Check events and festivals by category
            cursor.execute("""
                SELECT category_id, COUNT(*) as count
                FROM events_festivals
                GROUP BY category_id
                ORDER BY count DESC
            """)
            category_counts = cursor.fetchall()
            logger.info("Events and festivals by category:")
            for category in category_counts:
                logger.info(f"  - {category[0]}: {category[1]} events")

            # Check if we have enough data
            if category_count > 0 and event_count > 0:
                logger.info("✅ Events and festivals data generation successful")
                return True
            else:
                logger.warning("⚠️ Events and festivals data generation failed")
                return False
    except Exception as e:
        logger.error(f"Error verifying events and festivals: {str(e)}")
        return False

def main():
    """Main function to generate events and festivals data"""
    try:
        # Connect to database
        conn = connect_to_db()

        # Get existing data
        existing_data = get_existing_data(conn)

        # Generate events and festivals
        generate_events_festivals(conn, existing_data)

        # Verify events and festivals
        verify_events_festivals(conn)

        logger.info("Events and festivals data generation completed successfully")
        return True

    except Exception as e:
        logger.error(f"Error generating events and festivals data: {str(e)}", exc_info=True)
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
