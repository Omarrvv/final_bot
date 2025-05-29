#!/usr/bin/env python3
"""
Generate itineraries data for the Egypt Tourism Chatbot database.

This script:
1. Creates suggested itineraries that combine multiple attractions
2. Links itineraries to destinations, attractions, restaurants, and accommodations
"""

import os
import json
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
import numpy as np
from pgvector.psycopg2 import register_vector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set random seed for reproducibility
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
        # Get itinerary types
        cursor.execute("SELECT id, name FROM itinerary_types")
        existing_data['itinerary_types'] = cursor.fetchall()

        # Get regions
        cursor.execute("SELECT id, name FROM regions")
        existing_data['regions'] = cursor.fetchall()

        # Get cities
        cursor.execute("SELECT id, name, region_id FROM cities")
        existing_data['cities'] = cursor.fetchall()

        # Get attractions
        cursor.execute("SELECT id, name, city_id, region_id FROM attractions")
        existing_data['attractions'] = cursor.fetchall()

        # Get restaurants
        cursor.execute("SELECT id, name, city_id, region_id FROM restaurants")
        existing_data['restaurants'] = cursor.fetchall()

        # Get accommodations
        cursor.execute("SELECT id, name, city_id, region_id FROM accommodations")
        existing_data['accommodations'] = cursor.fetchall()

        # Get transportation types
        cursor.execute("SELECT type, name FROM transportation_types")
        existing_data['transportation_types'] = cursor.fetchall()

    return existing_data

def generate_embedding():
    """Generate a random embedding vector"""
    # Generate a random 1536-dimensional vector (typical for embeddings)
    embedding = np.random.normal(0, 1, 1536)
    # Normalize to unit length
    embedding = embedding / np.linalg.norm(embedding)
    return embedding

def generate_itineraries(conn, existing_data):
    """Generate itineraries data"""
    logger.info("Generating itineraries data")

    # Prepare itineraries data
    all_itineraries = []

    # Classic Cairo and Luxor Itinerary
    classic_cairo_luxor = {
        'type_id': 'historical',
        'name': {
            'en': "Classic Cairo and Luxor: Egypt's Ancient Wonders",
            'ar': 'القاهرة والأقصر الكلاسيكية: عجائب مصر القديمة'
        },
        'description': {
            'en': """Experience the best of ancient Egypt on this 7-day journey through Cairo and Luxor. Begin in Cairo with visits to the iconic Pyramids of Giza, the enigmatic Sphinx, and the treasure-filled Egyptian Museum. Then fly to Luxor, the ancient city of Thebes, to explore the magnificent temples of Karnak and Luxor, the Valley of the Kings, and other archaeological wonders. This itinerary offers a perfect introduction to Egypt''s most famous historical sites, combining the bustling metropolis of Cairo with the open-air museum that is Luxor.""",
            'ar': """استمتع بأفضل ما في مصر القديمة في هذه الرحلة التي تستغرق 7 أيام عبر القاهرة والأقصر. ابدأ في القاهرة بزيارة أهرامات الجيزة الشهيرة، وأبو الهول الغامض، والمتحف المصري المليء بالكنوز. ثم طر إلى الأقصر، مدينة طيبة القديمة، لاستكشاف معابد الكرنك والأقصر الرائعة، ووادي الملوك، وغيرها من العجائب الأثرية. يقدم هذا المسار مقدمة مثالية لأشهر المواقع التاريخية في مصر، مع الجمع بين العاصمة الصاخبة القاهرة والمتحف المفتوح الذي هو الأقصر."""
        },
        'duration_days': 7,
        'regions': ['lower_egypt', 'upper_egypt'],
        'cities': ['cairo', 'giza', 'luxor'],
        'attractions': [
            'pyramids_of_giza',
            'sphinx',
            'egyptian_museum',
            'khan_el_khalili',
            'citadel_of_saladin',
            'karnak_temple',
            'luxor_temple',
            'valley_of_the_kings',
            'hatshepsut_temple',
            'colossi_of_memnon'
        ],
        'restaurants': [
            'abou_el_sid_cairo',
            'koshary_abou_tarek',
            'sofra_restaurant_luxor',
            'al_sahaby_lane_restaurant'
        ],
        'accommodations': [
            'cairo_marriott',
            'steigenberger_nile_palace'
        ],
        'transportation_types': [
            'domestic_flight',
            'private_transfer',
            'taxi'
        ],
        'daily_plans': {
            'en': [
                {
                    'day': 1,
                    'title': 'Arrival in Cairo',
                    'description': 'Arrive at Cairo International Airport. Meet and greet by our representative. Transfer to your hotel in Cairo. Rest and relax after your journey.',
                    'attractions': [],
                    'meals': ['Dinner'],
                    'accommodation': 'Cairo Marriott Hotel'
                },
                {
                    'day': 2,
                    'title': 'Pyramids and Sphinx',
                    'description': 'Visit the Great Pyramids of Giza and the Sphinx. Explore the Solar Boat Museum. Enjoy lunch at a local restaurant. In the afternoon, visit the Step Pyramid of Saqqara, the oldest known pyramid in Egypt.',
                    'attractions': ['pyramids_of_giza', 'sphinx'],
                    'meals': ['Breakfast', 'Lunch'],
                    'accommodation': 'Cairo Marriott Hotel'
                },
                {
                    'day': 3,
                    'title': 'Cairo Museums and Old Cairo',
                    'description': 'Visit the Egyptian Museum to see the treasures of Tutankhamun and thousands of artifacts spanning 5,000 years of Egyptian history. After lunch, explore Islamic Cairo including the Citadel of Saladin and the Alabaster Mosque. End the day with shopping at Khan El Khalili Bazaar.',
                    'attractions': ['egyptian_museum', 'citadel_of_saladin', 'khan_el_khalili'],
                    'meals': ['Breakfast', 'Lunch'],
                    'accommodation': 'Cairo Marriott Hotel'
                },
                {
                    'day': 4,
                    'title': 'Cairo to Luxor',
                    'description': 'Morning flight to Luxor. Check in at your hotel. In the afternoon, visit the magnificent Karnak Temple, the largest religious building ever constructed. Explore the Avenue of Sphinxes that once connected Karnak to Luxor Temple.',
                    'attractions': ['karnak_temple'],
                    'meals': ['Breakfast', 'Dinner'],
                    'accommodation': 'Steigenberger Nile Palace'
                },
                {
                    'day': 5,
                    'title': 'Valley of the Kings',
                    'description': 'Cross to the West Bank of Luxor to visit the Valley of the Kings, where pharaohs of the New Kingdom were buried in elaborate tombs. Explore the Temple of Hatshepsut at Deir el-Bahari. See the Colossi of Memnon. Afternoon at leisure to relax or explore Luxor on your own.',
                    'attractions': ['valley_of_the_kings', 'hatshepsut_temple', 'colossi_of_memnon'],
                    'meals': ['Breakfast', 'Lunch'],
                    'accommodation': 'Steigenberger Nile Palace'
                },
                {
                    'day': 6,
                    'title': 'Luxor Temple and Museum',
                    'description': 'Morning visit to Luxor Temple, particularly beautiful at sunrise. Visit the Luxor Museum to see a well-curated collection of antiquities. Afternoon at leisure for shopping or optional activities such as a felucca ride on the Nile or a hot air balloon ride (additional cost).',
                    'attractions': ['luxor_temple'],
                    'meals': ['Breakfast', 'Dinner'],
                    'accommodation': 'Steigenberger Nile Palace'
                },
                {
                    'day': 7,
                    'title': 'Departure',
                    'description': 'Transfer to Luxor Airport for your departure flight, or continue your journey with an optional extension to Aswan, the Red Sea, or other destinations in Egypt.',
                    'attractions': [],
                    'meals': ['Breakfast'],
                    'accommodation': 'None'
                }
            ],
            'ar': [
                {
                    'day': 1,
                    'title': 'الوصول إلى القاهرة',
                    'description': 'الوصول إلى مطار القاهرة الدولي. استقبال من قبل ممثلنا. النقل إلى الفندق في القاهرة. الراحة والاسترخاء بعد رحلتك.',
                    'attractions': [],
                    'meals': ['عشاء'],
                    'accommodation': 'فندق ماريوت القاهرة'
                },
                {
                    'day': 2,
                    'title': 'الأهرامات وأبو الهول',
                    'description': 'زيارة أهرامات الجيزة العظيمة وأبو الهول. استكشاف متحف مركب الشمس. تناول الغداء في مطعم محلي. في فترة ما بعد الظهر، زيارة هرم زوسر المدرج في سقارة، أقدم هرم معروف في مصر.',
                    'attractions': ['pyramids_of_giza', 'sphinx'],
                    'meals': ['إفطار', 'غداء'],
                    'accommodation': 'فندق ماريوت القاهرة'
                },
                {
                    'day': 3,
                    'title': 'متاحف القاهرة والقاهرة القديمة',
                    'description': 'زيارة المتحف المصري لمشاهدة كنوز توت عنخ آمون وآلاف القطع الأثرية التي تمتد على مدى 5000 عام من التاريخ المصري. بعد الغداء، استكشاف القاهرة الإسلامية بما في ذلك قلعة صلاح الدين ومسجد محمد علي. إنهاء اليوم بالتسوق في خان الخليلي.',
                    'attractions': ['egyptian_museum', 'citadel_of_saladin', 'khan_el_khalili'],
                    'meals': ['إفطار', 'غداء'],
                    'accommodation': 'فندق ماريوت القاهرة'
                },
                {
                    'day': 4,
                    'title': 'القاهرة إلى الأقصر',
                    'description': 'رحلة طيران صباحية إلى الأقصر. تسجيل الوصول في الفندق. في فترة ما بعد الظهر، زيارة معبد الكرنك الرائع، أكبر مبنى ديني تم بناؤه على الإطلاق. استكشاف طريق أبو الهول الذي كان يربط الكرنك بمعبد الأقصر.',
                    'attractions': ['karnak_temple'],
                    'meals': ['إفطار', 'عشاء'],
                    'accommodation': 'فندق شتيجنبرجر نايل بالاس'
                },
                {
                    'day': 5,
                    'title': 'وادي الملوك',
                    'description': 'عبور إلى الضفة الغربية للأقصر لزيارة وادي الملوك، حيث تم دفن فراعنة المملكة الحديثة في مقابر متقنة. استكشاف معبد حتشبسوت في الدير البحري. مشاهدة تمثالي ممنون. بعد الظهر وقت حر للاسترخاء أو استكشاف الأقصر بنفسك.',
                    'attractions': ['valley_of_the_kings', 'hatshepsut_temple', 'colossi_of_memnon'],
                    'meals': ['إفطار', 'غداء'],
                    'accommodation': 'فندق شتيجنبرجر نايل بالاس'
                },
                {
                    'day': 6,
                    'title': 'معبد الأقصر والمتحف',
                    'description': 'زيارة صباحية لمعبد الأقصر، جميل بشكل خاص عند شروق الشمس. زيارة متحف الأقصر لمشاهدة مجموعة منسقة جيدًا من القطع الأثرية. بعد الظهر وقت حر للتسوق أو أنشطة اختيارية مثل رحلة بالفلوكة على النيل أو رحلة بالمنطاد (تكلفة إضافية).',
                    'attractions': ['luxor_temple'],
                    'meals': ['إفطار', 'عشاء'],
                    'accommodation': 'فندق شتيجنبرجر نايل بالاس'
                },
                {
                    'day': 7,
                    'title': 'المغادرة',
                    'description': 'النقل إلى مطار الأقصر لرحلة المغادرة، أو مواصلة رحلتك مع تمديد اختياري إلى أسوان أو البحر الأحمر أو وجهات أخرى في مصر.',
                    'attractions': [],
                    'meals': ['إفطار'],
                    'accommodation': 'لا شيء'
                }
            ]
        },
        'budget_range': {
            'currency': 'USD',
            'economy': 800,
            'standard': 1200,
            'luxury': 2000
        },
        'best_seasons': ['october', 'november', 'december', 'january', 'february', 'march', 'april'],
        'difficulty_level': 'easy',
        'target_audience': {
            'en': [
                'First-time visitors to Egypt',
                'History enthusiasts',
                'Cultural travelers',
                'Couples',
                'Families with older children',
                'Senior travelers'
            ],
            'ar': [
                'الزوار لأول مرة إلى مصر',
                'عشاق التاريخ',
                'المسافرون الثقافيون',
                'الأزواج',
                'العائلات مع أطفال أكبر سنًا',
                'المسافرون كبار السن'
            ]
        },
        'highlights': {
            'en': [
                'Stand in awe before the Great Pyramids of Giza, the last remaining wonder of the ancient world',
                'Discover the treasures of Tutankhamun and other pharaohs at the Egyptian Museum',
                'Wander through the massive columns of Karnak Temple, the largest religious complex ever built',
                'Explore the tombs of pharaohs in the Valley of the Kings',
                'Experience the contrast between bustling Cairo and the more relaxed atmosphere of Luxor',
                'Shop for souvenirs at the historic Khan El Khalili bazaar'
            ],
            'ar': [
                'الوقوف في رهبة أمام أهرامات الجيزة العظيمة، آخر عجائب العالم القديم المتبقية',
                'اكتشاف كنوز توت عنخ آمون والفراعنة الآخرين في المتحف المصري',
                'التجول بين الأعمدة الضخمة لمعبد الكرنك، أكبر مجمع ديني تم بناؤه على الإطلاق',
                'استكشاف مقابر الفراعنة في وادي الملوك',
                'تجربة التباين بين القاهرة الصاخبة والأجواء الأكثر استرخاء في الأقصر',
                'التسوق لشراء الهدايا التذكارية في سوق خان الخليلي التاريخي'
            ]
        },
        'practical_tips': {
            'en': [
                'Dress modestly, especially when visiting religious sites',
                'Carry small Egyptian currency for tips and small purchases',
                'Stay hydrated and use sun protection',
                'Consider hiring a knowledgeable guide for historical context',
                'Book domestic flights in advance as they can fill up quickly',
                'Be prepared for early morning starts to avoid the midday heat',
                'Bargain at markets but do so respectfully'
            ],
            'ar': [
                'ارتداء ملابس محتشمة، خاصة عند زيارة المواقع الدينية',
                'حمل عملة مصرية صغيرة للإكراميات والمشتريات الصغيرة',
                'البقاء رطبًا واستخدام واقي الشمس',
                'التفكير في استئجار مرشد مطلع للسياق التاريخي',
                'حجز الرحلات الداخلية مقدمًا لأنها قد تمتلئ بسرعة',
                'الاستعداد للبدايات المبكرة في الصباح لتجنب حرارة منتصف النهار',
                'المساومة في الأسواق ولكن بطريقة محترمة'
            ]
        },
        'images': {
            'main': 'classic_cairo_luxor_main.jpg',
            'gallery': [
                'classic_cairo_luxor_pyramids.jpg',
                'classic_cairo_luxor_museum.jpg',
                'classic_cairo_luxor_karnak.jpg',
                'classic_cairo_luxor_valley_kings.jpg'
            ]
        },
        'tags': ['cairo', 'luxor', 'pyramids', 'temples', 'history', 'archaeology', 'museums', 'classic tour'],
        'is_featured': True,
        'rating': 4.8
    }

    # Combine all itineraries
    all_itineraries.append(classic_cairo_luxor)

    # Insert itineraries into database
    with conn.cursor() as cursor:
        for itinerary in all_itineraries:
            cursor.execute("""
                INSERT INTO itineraries (
                    type_id, name, description, duration_days, regions,
                    cities, attractions, restaurants, accommodations,
                    transportation_types, daily_plans, budget_range,
                    best_seasons, difficulty_level, target_audience,
                    highlights, practical_tips, images, tags, is_featured,
                    rating, embedding, created_at, updated_at, user_id
                ) VALUES (
                    %s, %s::jsonb, %s::jsonb, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s::jsonb, %s::jsonb,
                    %s, %s, %s::jsonb,
                    %s::jsonb, %s::jsonb, %s::jsonb, %s, %s,
                    %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'system'
                )
            """, (
                itinerary['type_id'],
                json.dumps(itinerary['name']),
                json.dumps(itinerary['description']),
                itinerary['duration_days'],
                itinerary['regions'],
                itinerary['cities'],
                itinerary['attractions'],
                itinerary['restaurants'],
                itinerary['accommodations'],
                itinerary['transportation_types'],
                json.dumps(itinerary['daily_plans']),
                json.dumps(itinerary['budget_range']),
                itinerary['best_seasons'],
                itinerary['difficulty_level'],
                json.dumps(itinerary['target_audience']),
                json.dumps(itinerary['highlights']),
                json.dumps(itinerary['practical_tips']),
                json.dumps(itinerary['images']),
                itinerary['tags'],
                itinerary['is_featured'],
                itinerary['rating'],
                generate_embedding()
            ))

    conn.commit()
    logger.info(f"Generated {len(all_itineraries)} itineraries")
    return all_itineraries

def verify_itineraries(conn):
    """Verify the itineraries data in the database"""
    try:
        with conn.cursor() as cursor:
            # Check itinerary types count
            cursor.execute("SELECT COUNT(*) FROM itinerary_types")
            type_count = cursor.fetchone()[0]
            logger.info(f"Total itinerary types in database: {type_count}")

            # Check itineraries count
            cursor.execute("SELECT COUNT(*) FROM itineraries")
            itinerary_count = cursor.fetchone()[0]
            logger.info(f"Total itineraries in database: {itinerary_count}")

            # Check itineraries by type
            cursor.execute("""
                SELECT type_id, COUNT(*) as count
                FROM itineraries
                GROUP BY type_id
                ORDER BY count DESC
            """)
            type_counts = cursor.fetchall()
            logger.info("Itineraries by type:")
            for type_count in type_counts:
                logger.info(f"  - {type_count[0]}: {type_count[1]} itineraries")

            # Check if we have enough data
            if type_count > 0 and itinerary_count > 0:
                logger.info("✅ Itineraries data generation successful")
                return True
            else:
                logger.warning("⚠️ Itineraries data generation failed")
                return False
    except Exception as e:
        logger.error(f"Error verifying itineraries: {str(e)}")
        return False

def main():
    """Main function to generate itineraries data"""
    try:
        # Connect to database
        conn = connect_to_db()

        # Get existing data
        existing_data = get_existing_data(conn)

        # Generate itineraries
        generate_itineraries(conn, existing_data)

        # Verify itineraries
        verify_itineraries(conn)

        logger.info("Itineraries data generation completed successfully")
        return True

    except Exception as e:
        logger.error(f"Error generating itineraries data: {str(e)}", exc_info=True)
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
