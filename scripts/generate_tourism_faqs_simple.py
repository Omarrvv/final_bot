#!/usr/bin/env python3
"""
Generate tourism FAQs data for the Egypt Tourism Chatbot database.

This script:
1. Creates frequently asked questions about Egyptian tourism
2. Categorizes FAQs by topic
3. Links FAQs to relevant destinations
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
        # Get FAQ categories
        cursor.execute("SELECT id, name FROM faq_categories")
        existing_data['faq_categories'] = cursor.fetchall()

        # Get destinations
        cursor.execute("SELECT id, name, type FROM destinations")
        existing_data['destinations'] = cursor.fetchall()

        # Get existing FAQs
        cursor.execute("SELECT id, question FROM tourism_faqs")
        existing_data['faqs'] = cursor.fetchall()

    return existing_data

def generate_embedding():
    """Generate a random embedding vector"""
    # Generate a random 1536-dimensional vector (typical for embeddings)
    embedding = np.random.normal(0, 1, 1536)
    # Normalize to unit length
    embedding = embedding / np.linalg.norm(embedding)
    return embedding

def generate_tourism_faqs(conn, existing_data):
    """Generate tourism FAQs data"""
    logger.info("Generating tourism FAQs data")

    # Prepare FAQs data
    all_faqs = []

    # Visa & Immigration FAQs
    visa_faqs = [
        {
            'category_id': 'visa_immigration',
            'question': {
                'en': 'Do I need a visa to visit Egypt?',
                'ar': 'هل أحتاج إلى تأشيرة لزيارة مصر؟'
            },
            'answer': {
                'en': 'Most visitors to Egypt need a visa. Citizens of many countries can obtain a visa on arrival at Egyptian airports for approximately $25 USD. E-visas are also available online through the official Egyptian e-visa portal.',
                'ar': 'يحتاج معظم الزوار إلى مصر إلى تأشيرة. يمكن لمواطني العديد من البلدان الحصول على تأشيرة عند الوصول في المطارات المصرية مقابل حوالي 25 دولارًا أمريكيًا. التأشيرات الإلكترونية متاحة أيضًا عبر الإنترنت.'
            },
            'tags': ['visa', 'entry requirements', 'immigration', 'travel documents'],
            'is_featured': True,
            'related_destination_ids': ['egypt']
        }
    ]

    # Health & Safety FAQs
    health_safety_faqs = [
        {
            'category_id': 'health_safety',
            'question': {
                'en': 'Is Egypt safe for tourists?',
                'ar': 'هل مصر آمنة للسياح؟'
            },
            'answer': {
                'en': 'Egypt is generally safe for tourists, especially in the main tourist areas. The Egyptian government places a high priority on tourist safety and there is visible security in popular destinations.',
                'ar': 'مصر آمنة بشكل عام للسياح، خاصة في المناطق السياحية الرئيسية. تضع الحكومة المصرية أولوية عالية لسلامة السياح وهناك أمن مرئي في الوجهات الشعبية.'
            },
            'tags': ['safety', 'security', 'travel advice', 'tourist safety'],
            'is_featured': True,
            'related_destination_ids': ['egypt']
        }
    ]

    # Money & Currency FAQs
    money_currency_faqs = [
        {
            'category_id': 'money_currency',
            'question': {
                'en': 'What is the currency in Egypt?',
                'ar': 'ما هي العملة في مصر؟'
            },
            'answer': {
                'en': 'The currency in Egypt is the Egyptian Pound (EGP), often abbreviated as LE or E£. Banknotes come in denominations of 1, 5, 10, 20, 50, 100, and 200 pounds.',
                'ar': 'العملة في مصر هي الجنيه المصري (EGP)، ويختصر غالبًا بـ LE أو E£. تأتي الأوراق النقدية بفئات 1 و5 و10 و20 و50 و100 و200 جنيه.'
            },
            'tags': ['currency', 'money', 'egyptian pound', 'exchange'],
            'is_featured': True,
            'related_destination_ids': ['egypt']
        }
    ]

    # Combine all FAQs
    all_faqs.extend(visa_faqs)
    all_faqs.extend(health_safety_faqs)
    all_faqs.extend(money_currency_faqs)

    # Insert FAQs into database
    with conn.cursor() as cursor:
        for faq in all_faqs:
            cursor.execute("""
                INSERT INTO tourism_faqs (
                    category_id, question, answer, related_destination_ids, tags,
                    is_featured, embedding, created_at, updated_at, user_id
                ) VALUES (
                    %s, %s::jsonb, %s::jsonb, %s, %s,
                    %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'system'
                )
            """, (
                faq['category_id'],
                json.dumps(faq['question']),
                json.dumps(faq['answer']),
                faq['related_destination_ids'],
                faq['tags'],
                faq['is_featured'],
                generate_embedding()
            ))

    conn.commit()
    logger.info(f"Generated {len(all_faqs)} tourism FAQs")
    return all_faqs

def verify_tourism_faqs(conn):
    """Verify the tourism FAQs data in the database"""
    try:
        with conn.cursor() as cursor:
            # Check FAQ categories count
            cursor.execute("SELECT COUNT(*) FROM faq_categories")
            category_count = cursor.fetchone()[0]
            logger.info(f"Total FAQ categories in database: {category_count}")

            # Check tourism FAQs count
            cursor.execute("SELECT COUNT(*) FROM tourism_faqs")
            faq_count = cursor.fetchone()[0]
            logger.info(f"Total tourism FAQs in database: {faq_count}")

            # Check FAQs by category
            cursor.execute("""
                SELECT category_id, COUNT(*) as count
                FROM tourism_faqs
                GROUP BY category_id
                ORDER BY count DESC
            """)
            category_counts = cursor.fetchall()
            logger.info("Tourism FAQs by category:")
            for category in category_counts:
                logger.info(f"  - {category[0]}: {category[1]} FAQs")

            # Check if we have enough data
            if category_count > 0 and faq_count > 0:
                logger.info("✅ Tourism FAQs data generation successful")
                return True
            else:
                logger.warning("⚠️ Tourism FAQs data generation failed")
                return False
    except Exception as e:
        logger.error(f"Error verifying tourism FAQs: {str(e)}")
        return False

def main():
    """Main function to generate tourism FAQs data"""
    try:
        # Connect to database
        conn = connect_to_db()

        # Get existing data
        existing_data = get_existing_data(conn)

        # Generate tourism FAQs
        generate_tourism_faqs(conn, existing_data)

        # Verify tourism FAQs
        verify_tourism_faqs(conn)

        logger.info("Tourism FAQs data generation completed successfully")
        return True

    except Exception as e:
        logger.error(f"Error generating tourism FAQs data: {str(e)}", exc_info=True)
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
