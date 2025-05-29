#!/usr/bin/env python3
"""
Generate tour packages data for the Egypt Tourism Chatbot database.

This script:
1. Creates tour packages for Egyptian tourism
2. Categorizes tour packages by type
3. Links tour packages to relevant destinations and attractions
"""

import os
import json
import random
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
import numpy as np
from pgvector.psycopg2 import register_vector

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
        # Get tour package categories
        cursor.execute("SELECT id, name FROM tour_package_categories")
        existing_data['tour_package_categories'] = cursor.fetchall()

        # Get destinations
        cursor.execute("SELECT id, name, type FROM destinations")
        existing_data['destinations'] = cursor.fetchall()

        # Get attractions
        cursor.execute("SELECT id, name, type FROM attractions")
        existing_data['attractions'] = cursor.fetchall()

        # Get accommodations
        cursor.execute("SELECT id, name FROM accommodations")
        existing_data['accommodations'] = cursor.fetchall()

        # Get transportation types
        cursor.execute("SELECT type, name FROM transportation_types")
        existing_data['transportation_types'] = cursor.fetchall()

        # Get existing tour packages
        cursor.execute("SELECT id, name FROM tour_packages")
        existing_data['tour_packages'] = cursor.fetchall()

    return existing_data

def generate_embedding():
    """Generate a random embedding vector"""
    # Generate a random 1536-dimensional vector (typical for embeddings)
    embedding = np.random.normal(0, 1, 1536)
    # Normalize to unit length
    embedding = embedding / np.linalg.norm(embedding)
    return embedding

def generate_tour_packages(conn, existing_data):
    """Generate tour packages data"""
    logger.info("Generating tour packages data")

    # Prepare tour packages data
    all_packages = []
    
    # Classic Egypt Tour
    classic_egypt_tour = {
        'category_id': 'classic_tours',
        'name': {
            'en': 'Classic Egypt Tour: Cairo, Luxor & Aswan',
            'ar': 'جولة مصر الكلاسيكية: القاهرة والأقصر وأسوان'
        },
        'description': {
            'en': """Experience the best of ancient Egypt on this comprehensive 8-day tour. Visit the iconic Pyramids of Giza and the Sphinx, explore the treasures of the Egyptian Museum, and discover the temples of Luxor and Karnak. Cruise along the Nile to Aswan, visiting temples along the way, and enjoy the beauty of the Nile Valley. This tour offers a perfect introduction to Egypt's rich history and culture.""",
            'ar': """استمتع بأفضل ما في مصر القديمة في هذه الجولة الشاملة التي تستغرق 8 أيام. قم بزيارة أهرامات الجيزة الشهيرة وأبو الهول، واستكشف كنوز المتحف المصري، واكتشف معابد الأقصر والكرنك. أبحر على طول نهر النيل إلى أسوان، وزر المعابد على طول الطريق، واستمتع بجمال وادي النيل. تقدم هذه الجولة مقدمة مثالية لتاريخ وثقافة مصر الغنية."""
        },
        'duration_days': 8,
        'price_range': {
            'currency': 'USD',
            'economy': 1200,
            'standard': 1800,
            'luxury': 2500
        },
        'included_services': {
            'en': [
                'Airport transfers',
                'Accommodation (3 nights in Cairo, 1 night in Luxor, 3 nights on Nile cruise)',
                'Daily breakfast, full board on cruise',
                'Guided tours with Egyptologist',
                'All entrance fees to sites mentioned in itinerary',
                'Domestic flight (Cairo to Luxor)',
                'Transportation in air-conditioned vehicles',
                'Bottled water during tours'
            ],
            'ar': [
                'النقل من وإلى المطار',
                'الإقامة (3 ليالي في القاهرة، ليلة واحدة في الأقصر، 3 ليالي على متن رحلة نيلية)',
                'إفطار يومي، إقامة كاملة على متن الرحلة النيلية',
                'جولات مع مرشد متخصص في علم المصريات',
                'جميع رسوم الدخول إلى المواقع المذكورة في خط سير الرحلة',
                'رحلة طيران داخلية (القاهرة إلى الأقصر)',
                'النقل في مركبات مكيفة',
                'مياه معبأة خلال الجولات'
            ]
        },
        'excluded_services': {
            'en': [
                'International airfare',
                'Entry visa to Egypt',
                'Travel insurance',
                'Personal expenses',
                'Gratuities',
                'Optional tours not mentioned in itinerary',
                'Beverages during meals'
            ],
            'ar': [
                'تذاكر الطيران الدولية',
                'تأشيرة الدخول إلى مصر',
                'تأمين السفر',
                'النفقات الشخصية',
                'الإكراميات',
                'الجولات الاختيارية غير المذكورة في خط سير الرحلة',
                'المشروبات خلال الوجبات'
            ]
        },
        'itinerary': {
            'en': [
                {
                    'day': 1,
                    'title': 'Arrival in Cairo',
                    'description': 'Arrive at Cairo International Airport. Meet and greet by our representative. Transfer to your hotel. Overnight in Cairo.',
                    'meals': ['None'],
                    'accommodation': 'Cairo Hotel'
                },
                {
                    'day': 2,
                    'title': 'Pyramids & Sphinx',
                    'description': 'Visit the Great Pyramids of Giza and the Sphinx. Explore the ancient capital of Memphis and the Step Pyramid at Saqqara. Overnight in Cairo.',
                    'meals': ['Breakfast', 'Lunch'],
                    'accommodation': 'Cairo Hotel'
                },
                {
                    'day': 3,
                    'title': 'Cairo Museums & Old Cairo',
                    'description': 'Visit the Egyptian Museum, Citadel of Saladin, and Khan El Khalili Bazaar. Explore Islamic and Coptic Cairo. Overnight in Cairo.',
                    'meals': ['Breakfast', 'Lunch'],
                    'accommodation': 'Cairo Hotel'
                },
                {
                    'day': 4,
                    'title': 'Cairo to Luxor',
                    'description': 'Fly to Luxor. Visit Karnak and Luxor Temples. Overnight in Luxor.',
                    'meals': ['Breakfast', 'Lunch'],
                    'accommodation': 'Luxor Hotel'
                },
                {
                    'day': 5,
                    'title': 'Luxor West Bank & Nile Cruise',
                    'description': 'Visit the Valley of the Kings, Temple of Hatshepsut, and Colossi of Memnon. Board your Nile cruise. Overnight on cruise.',
                    'meals': ['Breakfast', 'Lunch', 'Dinner'],
                    'accommodation': 'Nile Cruise'
                },
                {
                    'day': 6,
                    'title': 'Edfu & Kom Ombo',
                    'description': 'Sail to Edfu and visit the Temple of Horus. Continue to Kom Ombo and visit the Temple of Sobek. Overnight on cruise.',
                    'meals': ['Breakfast', 'Lunch', 'Dinner'],
                    'accommodation': 'Nile Cruise'
                },
                {
                    'day': 7,
                    'title': 'Aswan',
                    'description': 'Visit the High Dam, the Unfinished Obelisk, and Philae Temple. Optional tour to Abu Simbel (not included). Overnight on cruise.',
                    'meals': ['Breakfast', 'Lunch', 'Dinner'],
                    'accommodation': 'Nile Cruise'
                },
                {
                    'day': 8,
                    'title': 'Departure',
                    'description': 'Disembark from the cruise. Transfer to Aswan Airport for your departure flight or continue with an optional extension.',
                    'meals': ['Breakfast'],
                    'accommodation': 'None'
                }
            ],
            'ar': [
                {
                    'day': 1,
                    'title': 'الوصول إلى القاهرة',
                    'description': 'الوصول إلى مطار القاهرة الدولي. استقبال من قبل ممثلنا. النقل إلى الفندق. المبيت في القاهرة.',
                    'meals': ['لا شيء'],
                    'accommodation': 'فندق القاهرة'
                },
                {
                    'day': 2,
                    'title': 'الأهرامات وأبو الهول',
                    'description': 'زيارة أهرامات الجيزة العظيمة وأبو الهول. استكشاف العاصمة القديمة ممفيس والهرم المدرج في سقارة. المبيت في القاهرة.',
                    'meals': ['إفطار', 'غداء'],
                    'accommodation': 'فندق القاهرة'
                },
                {
                    'day': 3,
                    'title': 'متاحف القاهرة والقاهرة القديمة',
                    'description': 'زيارة المتحف المصري وقلعة صلاح الدين وخان الخليلي. استكشاف القاهرة الإسلامية والقبطية. المبيت في القاهرة.',
                    'meals': ['إفطار', 'غداء'],
                    'accommodation': 'فندق القاهرة'
                },
                {
                    'day': 4,
                    'title': 'القاهرة إلى الأقصر',
                    'description': 'الطيران إلى الأقصر. زيارة معابد الكرنك والأقصر. المبيت في الأقصر.',
                    'meals': ['إفطار', 'غداء'],
                    'accommodation': 'فندق الأقصر'
                },
                {
                    'day': 5,
                    'title': 'الضفة الغربية للأقصر والرحلة النيلية',
                    'description': 'زيارة وادي الملوك ومعبد حتشبسوت وتمثالي ممنون. الصعود إلى الباخرة النيلية. المبيت على متن الباخرة.',
                    'meals': ['إفطار', 'غداء', 'عشاء'],
                    'accommodation': 'الباخرة النيلية'
                },
                {
                    'day': 6,
                    'title': 'إدفو وكوم أمبو',
                    'description': 'الإبحار إلى إدفو وزيارة معبد حورس. المواصلة إلى كوم أمبو وزيارة معبد سوبك. المبيت على متن الباخرة.',
                    'meals': ['إفطار', 'غداء', 'عشاء'],
                    'accommodation': 'الباخرة النيلية'
                },
                {
                    'day': 7,
                    'title': 'أسوان',
                    'description': 'زيارة السد العالي والمسلة الناقصة ومعبد فيلة. جولة اختيارية إلى أبو سمبل (غير مشمولة). المبيت على متن الباخرة.',
                    'meals': ['إفطار', 'غداء', 'عشاء'],
                    'accommodation': 'الباخرة النيلية'
                },
                {
                    'day': 8,
                    'title': 'المغادرة',
                    'description': 'النزول من الباخرة. النقل إلى مطار أسوان لرحلة المغادرة أو المواصلة مع تمديد اختياري.',
                    'meals': ['إفطار'],
                    'accommodation': 'لا شيء'
                }
            ]
        },
        'destinations': ['cairo', 'luxor', 'aswan', 'edfu', 'kom_ombo'],
        'attractions': ['pyramids_of_giza', 'sphinx', 'egyptian_museum', 'khan_el_khalili', 'karnak_temple', 'luxor_temple', 'valley_of_the_kings', 'hatshepsut_temple', 'colossi_of_memnon', 'edfu_temple', 'kom_ombo_temple', 'philae_temple', 'high_dam', 'unfinished_obelisk'],
        'accommodations': ['cairo_marriott', 'steigenberger_nile_palace', 'movenpick_royal_lily'],
        'transportation_types': ['domestic_flight', 'nile_cruise', 'private_transfer'],
        'min_group_size': 2,
        'max_group_size': 20,
        'difficulty_level': 'easy',
        'accessibility_info': {
            'en': 'This tour involves moderate walking and standing. Some sites have uneven terrain. Not recommended for people with severe mobility issues.',
            'ar': 'تتضمن هذه الجولة المشي والوقوف بشكل معتدل. بعض المواقع بها تضاريس غير مستوية. لا يُنصح بها للأشخاص الذين يعانون من مشاكل حركة شديدة.'
        },
        'seasonal_info': {
            'best_time': ['october', 'november', 'december', 'january', 'february', 'march', 'april'],
            'peak_season': ['december', 'january'],
            'low_season': ['june', 'july', 'august'],
            'weather_notes': {
                'en': 'Best visited during the cooler months (October to April). Summer months can be extremely hot, especially in Upper Egypt.',
                'ar': 'يفضل زيارتها خلال الأشهر الأكثر برودة (أكتوبر إلى أبريل). يمكن أن تكون أشهر الصيف حارة للغاية، خاصة في صعيد مصر.'
            }
        },
        'booking_info': {
            'min_advance_booking': 30,  # days
            'availability': 'year_round',
            'booking_channels': ['online', 'travel_agent', 'phone'],
            'payment_methods': ['credit_card', 'bank_transfer', 'paypal'],
            'deposit_required': True,
            'deposit_percentage': 25
        },
        'cancellation_policy': {
            'en': [
                '60+ days before departure: Full refund minus $100 administration fee',
                '59-30 days before departure: 75% refund',
                '29-15 days before departure: 50% refund',
                '14-7 days before departure: 25% refund',
                'Less than 7 days before departure: No refund'
            ],
            'ar': [
                '60+ يومًا قبل المغادرة: استرداد كامل ناقص رسوم إدارية بقيمة 100 دولار',
                '59-30 يومًا قبل المغادرة: استرداد 75%',
                '29-15 يومًا قبل المغادرة: استرداد 50%',
                '14-7 أيام قبل المغادرة: استرداد 25%',
                'أقل من 7 أيام قبل المغادرة: لا استرداد'
            ]
        },
        'reviews': {
            'count': 245,
            'average_rating': 4.7,
            'sample_reviews': [
                {
                    'author': 'John D.',
                    'rating': 5,
                    'date': '2023-11-15',
                    'text': 'Amazing experience! Our guide Ahmed was incredibly knowledgeable and made the history come alive. The Nile cruise was the highlight of our trip.'
                },
                {
                    'author': 'Sarah M.',
                    'rating': 4,
                    'date': '2023-10-22',
                    'text': 'Great tour overall. Well organized and comprehensive. Only downside was some long travel days.'
                },
                {
                    'author': 'David L.',
                    'rating': 5,
                    'date': '2023-09-05',
                    'text': 'Exceeded our expectations. The perfect introduction to Egypt\'s incredible history and culture.'
                }
            ]
        },
        'rating': 4.7,
        'images': {
            'main': 'classic_egypt_tour_main.jpg',
            'gallery': [
                'classic_egypt_tour_pyramids.jpg',
                'classic_egypt_tour_luxor.jpg',
                'classic_egypt_tour_cruise.jpg',
                'classic_egypt_tour_aswan.jpg'
            ]
        },
        'tags': ['history', 'archaeology', 'nile cruise', 'pyramids', 'temples', 'museums', 'classic tour'],
        'is_featured': True,
        'is_private': False
    }
    
    # Combine all tour packages
    all_packages.append(classic_egypt_tour)
    
    # Insert tour packages into database
    with conn.cursor() as cursor:
        for package in all_packages:
            cursor.execute("""
                INSERT INTO tour_packages (
                    category_id, name, description, duration_days, price_range,
                    included_services, excluded_services, itinerary, destinations,
                    attractions, accommodations, transportation_types,
                    min_group_size, max_group_size, difficulty_level,
                    accessibility_info, seasonal_info, booking_info,
                    cancellation_policy, reviews, rating, images,
                    tags, is_featured, is_private, embedding,
                    created_at, updated_at, user_id
                ) VALUES (
                    %s, %s::jsonb, %s::jsonb, %s, %s::jsonb,
                    %s::jsonb, %s::jsonb, %s::jsonb, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s::jsonb, %s::jsonb, %s::jsonb,
                    %s::jsonb, %s::jsonb, %s, %s::jsonb,
                    %s, %s, %s, %s,
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'system'
                )
            """, (
                package['category_id'],
                json.dumps(package['name']),
                json.dumps(package['description']),
                package['duration_days'],
                json.dumps(package['price_range']),
                json.dumps(package['included_services']),
                json.dumps(package['excluded_services']),
                json.dumps(package['itinerary']),
                package['destinations'],
                package['attractions'],
                package['accommodations'],
                package['transportation_types'],
                package['min_group_size'],
                package['max_group_size'],
                package['difficulty_level'],
                json.dumps(package['accessibility_info']),
                json.dumps(package['seasonal_info']),
                json.dumps(package['booking_info']),
                json.dumps(package['cancellation_policy']),
                json.dumps(package['reviews']),
                package['rating'],
                json.dumps(package['images']),
                package['tags'],
                package['is_featured'],
                package['is_private'],
                generate_embedding()
            ))
    
    conn.commit()
    logger.info(f"Generated {len(all_packages)} tour packages")
    return all_packages

def verify_tour_packages(conn):
    """Verify the tour packages data in the database"""
    try:
        with conn.cursor() as cursor:
            # Check tour package categories count
            cursor.execute("SELECT COUNT(*) FROM tour_package_categories")
            category_count = cursor.fetchone()[0]
            logger.info(f"Total tour package categories in database: {category_count}")

            # Check tour packages count
            cursor.execute("SELECT COUNT(*) FROM tour_packages")
            package_count = cursor.fetchone()[0]
            logger.info(f"Total tour packages in database: {package_count}")

            # Check tour packages by category
            cursor.execute("""
                SELECT category_id, COUNT(*) as count 
                FROM tour_packages
                GROUP BY category_id
                ORDER BY count DESC
            """)
            category_counts = cursor.fetchall()
            logger.info("Tour packages by category:")
            for category in category_counts:
                logger.info(f"  - {category[0]}: {category[1]} packages")

            # Check if we have enough data
            if category_count > 0 and package_count > 0:
                logger.info("✅ Tour packages data generation successful")
                return True
            else:
                logger.warning("⚠️ Tour packages data generation failed")
                return False
    except Exception as e:
        logger.error(f"Error verifying tour packages: {str(e)}")
        return False

def main():
    """Main function to generate tour packages data"""
    try:
        # Connect to database
        conn = connect_to_db()

        # Get existing data
        existing_data = get_existing_data(conn)

        # Generate tour packages
        generate_tour_packages(conn, existing_data)

        # Verify tour packages
        verify_tour_packages(conn)

        logger.info("Tour packages data generation completed successfully")
        return True

    except Exception as e:
        logger.error(f"Error generating tour packages data: {str(e)}", exc_info=True)
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
