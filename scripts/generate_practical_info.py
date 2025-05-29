#!/usr/bin/env python3
"""
Generate practical info data for the Egypt Tourism Chatbot database.

This script:
1. Creates practical information about Egyptian tourism
2. Categorizes practical info by topic
3. Links practical info to relevant destinations
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
        # Get practical info categories
        cursor.execute("SELECT id, name FROM practical_info_categories")
        existing_data['practical_info_categories'] = cursor.fetchall()

        # Get destinations
        cursor.execute("SELECT id, name, type FROM destinations")
        existing_data['destinations'] = cursor.fetchall()

        # Get existing practical info
        cursor.execute("SELECT id, title FROM practical_info")
        existing_data['practical_info'] = cursor.fetchall()

    return existing_data

def generate_embedding():
    """Generate a random embedding vector"""
    # Generate a random 1536-dimensional vector (typical for embeddings)
    embedding = np.random.normal(0, 1, 1536)
    # Normalize to unit length
    embedding = embedding / np.linalg.norm(embedding)
    return embedding

def generate_practical_info(conn, existing_data):
    """Generate practical info data"""
    logger.info("Generating practical info data")

    # Prepare practical info data
    all_info = []
    
    # Emergency Contacts
    emergency_contacts = [
        {
            'category_id': 'emergency_contacts',
            'title': {
                'en': 'Emergency Phone Numbers in Egypt',
                'ar': 'أرقام هواتف الطوارئ في مصر'
            },
            'content': {
                'en': """
# Emergency Phone Numbers in Egypt

Keep these important emergency numbers handy during your visit to Egypt:

## General Emergency Services
- **Police Emergency**: 122
- **Ambulance**: 123
- **Fire Department**: 180
- **Tourist Police**: 126
- **Traffic Police**: 128

## Medical Emergency Services
- **Central Ambulance**: 123
- **Blood Bank**: 123
- **Poison Control Center**: +20 2 2418 7656

## Other Important Numbers
- **Electricity Emergency**: 121
- **Natural Gas Emergency**: 129
- **Directory Assistance**: 140
- **International Calls Operator**: 120

## Tourist Assistance
- **Tourism Information Hotline**: 19654
- **Egypt Tourism Authority**: +20 2 2391 3454

It's recommended to save these numbers in your phone before traveling to Egypt. Many operators speak English, but having an Arabic speaker can be helpful in some situations.
                """,
                'ar': """
# أرقام هواتف الطوارئ في مصر

احتفظ بهذه الأرقام المهمة للطوارئ خلال زيارتك لمصر:

## خدمات الطوارئ العامة
- **شرطة الطوارئ**: 122
- **الإسعاف**: 123
- **المطافئ**: 180
- **شرطة السياحة**: 126
- **شرطة المرور**: 128

## خدمات الطوارئ الطبية
- **الإسعاف المركزي**: 123
- **بنك الدم**: 123
- **مركز مكافحة السموم**: +20 2 2418 7656

## أرقام مهمة أخرى
- **طوارئ الكهرباء**: 121
- **طوارئ الغاز الطبيعي**: 129
- **دليل الهاتف**: 140
- **مشغل المكالمات الدولية**: 120

## مساعدة السياح
- **الخط الساخن للمعلومات السياحية**: 19654
- **هيئة تنشيط السياحة المصرية**: +20 2 2391 3454

يُنصح بحفظ هذه الأرقام في هاتفك قبل السفر إلى مصر. يتحدث العديد من المشغلين اللغة الإنجليزية، ولكن وجود متحدث باللغة العربية يمكن أن يكون مفيدًا في بعض المواقف.
                """
            },
            'tags': ['emergency', 'phone numbers', 'safety', 'police', 'ambulance', 'medical'],
            'is_featured': True,
            'related_destination_ids': ['egypt']
        }
    ]
    
    # Embassies & Consulates
    embassies_consulates = [
        {
            'category_id': 'embassies_consulates',
            'title': {
                'en': 'Major Foreign Embassies in Cairo',
                'ar': 'السفارات الأجنبية الرئيسية في القاهرة'
            },
            'content': {
                'en': """
# Major Foreign Embassies in Cairo

Below is a list of major foreign embassies and consulates in Cairo, Egypt:

## United States Embassy
- **Address**: 5 Tawfik Diab Street, Garden City, Cairo
- **Phone**: +20 2 2797 3300
- **Website**: eg.usembassy.gov
- **Email**: consularcairoacs@state.gov
- **Hours**: Sunday to Thursday, 8:00 AM to 4:30 PM

## British Embassy
- **Address**: 7 Ahmed Ragheb Street, Garden City, Cairo
- **Phone**: +20 2 2791 6000
- **Website**: www.gov.uk/world/organisations/british-embassy-cairo
- **Email**: british.embassy.cairo@fco.gov.uk
- **Hours**: Sunday to Thursday, 8:00 AM to 3:30 PM

## Canadian Embassy
- **Address**: 18 Abdel Khalek Sarwat Street, Garden City, Cairo
- **Phone**: +20 2 2791 8700
- **Website**: www.egypt.gc.ca
- **Email**: cairo@international.gc.ca
- **Hours**: Sunday to Thursday, 8:00 AM to 4:00 PM

## Australian Embassy
- **Address**: 11th Floor, World Trade Center, 1191 Corniche El Nil, Boulak, Cairo
- **Phone**: +20 2 2770 6600
- **Website**: egypt.embassy.gov.au
- **Email**: cairo.austremb@dfat.gov.au
- **Hours**: Sunday to Thursday, 8:30 AM to 4:00 PM

## German Embassy
- **Address**: 10 Hassan Sabri Street, Zamalek, Cairo
- **Phone**: +20 2 2728 2000
- **Website**: kairo.diplo.de
- **Email**: info@kairo.diplo.de
- **Hours**: Sunday to Thursday, 8:00 AM to 3:30 PM

## French Embassy
- **Address**: 29 Charles de Gaulle Street, Giza, Cairo
- **Phone**: +20 2 3567 3200
- **Website**: eg.ambafrance.org
- **Email**: questions@ambafrance-eg.org
- **Hours**: Sunday to Thursday, 8:30 AM to 4:00 PM

In case of emergency, contact your embassy immediately. It's recommended to register with your embassy upon arrival in Egypt for extended stays.
                """,
                'ar': """
# السفارات الأجنبية الرئيسية في القاهرة

فيما يلي قائمة بالسفارات والقنصليات الأجنبية الرئيسية في القاهرة، مصر:

## سفارة الولايات المتحدة
- **العنوان**: 5 شارع توفيق دياب، جاردن سيتي، القاهرة
- **الهاتف**: +20 2 2797 3300
- **الموقع الإلكتروني**: eg.usembassy.gov
- **البريد الإلكتروني**: consularcairoacs@state.gov
- **ساعات العمل**: من الأحد إلى الخميس، 8:00 صباحًا إلى 4:30 مساءً

## السفارة البريطانية
- **العنوان**: 7 شارع أحمد راغب، جاردن سيتي، القاهرة
- **الهاتف**: +20 2 2791 6000
- **الموقع الإلكتروني**: www.gov.uk/world/organisations/british-embassy-cairo
- **البريد الإلكتروني**: british.embassy.cairo@fco.gov.uk
- **ساعات العمل**: من الأحد إلى الخميس، 8:00 صباحًا إلى 3:30 مساءً

## السفارة الكندية
- **العنوان**: 18 شارع عبد الخالق ثروت، جاردن سيتي، القاهرة
- **الهاتف**: +20 2 2791 8700
- **الموقع الإلكتروني**: www.egypt.gc.ca
- **البريد الإلكتروني**: cairo@international.gc.ca
- **ساعات العمل**: من الأحد إلى الخميس، 8:00 صباحًا إلى 4:00 مساءً

## السفارة الأسترالية
- **العنوان**: الطابق 11، مركز التجارة العالمي، 1191 كورنيش النيل، بولاق، القاهرة
- **الهاتف**: +20 2 2770 6600
- **الموقع الإلكتروني**: egypt.embassy.gov.au
- **البريد الإلكتروني**: cairo.austremb@dfat.gov.au
- **ساعات العمل**: من الأحد إلى الخميس، 8:30 صباحًا إلى 4:00 مساءً

## السفارة الألمانية
- **العنوان**: 10 شارع حسن صبري، الزمالك، القاهرة
- **الهاتف**: +20 2 2728 2000
- **الموقع الإلكتروني**: kairo.diplo.de
- **البريد الإلكتروني**: info@kairo.diplo.de
- **ساعات العمل**: من الأحد إلى الخميس، 8:00 صباحًا إلى 3:30 مساءً

## السفارة الفرنسية
- **العنوان**: 29 شارع شارل ديغول، الجيزة، القاهرة
- **الهاتف**: +20 2 3567 3200
- **الموقع الإلكتروني**: eg.ambafrance.org
- **البريد الإلكتروني**: questions@ambafrance-eg.org
- **ساعات العمل**: من الأحد إلى الخميس، 8:30 صباحًا إلى 4:00 مساءً

في حالة الطوارئ، اتصل بسفارتك على الفور. يُنصح بالتسجيل لدى سفارتك عند وصولك إلى مصر للإقامات الطويلة.
                """
            },
            'tags': ['embassies', 'consulates', 'diplomatic missions', 'foreign representation'],
            'is_featured': False,
            'related_destination_ids': ['egypt', 'cairo']
        }
    ]
    
    # Public Holidays
    public_holidays = [
        {
            'category_id': 'public_holidays',
            'title': {
                'en': 'Egyptian Public Holidays and Observances',
                'ar': 'العطلات والمناسبات الرسمية المصرية'
            },
            'content': {
                'en': """
# Egyptian Public Holidays and Observances

Egypt observes both national holidays and Islamic religious holidays. Islamic holidays follow the lunar calendar, so their dates change each year in the Gregorian calendar.

## National Holidays (Fixed Dates)
- **January 7**: Coptic Christmas
- **January 25**: Revolution Day / National Police Day
- **April 25**: Sinai Liberation Day
- **May 1**: Labor Day
- **July 23**: Revolution Day
- **October 6**: Armed Forces Day
- **December 23**: Victory Day

## Islamic Holidays (Dates Vary)
- **Eid al-Fitr**: 3-day celebration marking the end of Ramadan
- **Eid al-Adha**: 4-day celebration of sacrifice
- **Islamic New Year**: First day of Muharram
- **Mawlid al-Nabi**: Birthday of Prophet Muhammad

## Other Significant Days
- **Sham El Nessim**: Spring festival (Monday after Coptic Easter)
- **Coptic Easter**: According to the Coptic calendar (usually in April)

### Important Notes for Travelers:
- During Islamic holidays, especially Eid al-Fitr and Eid al-Adha, many businesses, government offices, and some tourist sites may have reduced hours or be closed.
- Banks and government offices are typically closed on all public holidays.
- Transportation may be more crowded during holiday periods.
- Ramadan affects daily life throughout the country, with many restaurants closed during daylight hours and altered business hours.
- It's advisable to check the specific dates of Islamic holidays for your travel year, as they shift approximately 11 days earlier each year in the Gregorian calendar.
                """,
                'ar': """
# العطلات والمناسبات الرسمية المصرية

تحتفل مصر بالعطلات الوطنية والأعياد الدينية الإسلامية. تتبع الأعياد الإسلامية التقويم القمري، لذا تتغير تواريخها كل عام في التقويم الميلادي.

## العطلات الوطنية (تواريخ ثابتة)
- **7 يناير**: عيد الميلاد القبطي
- **25 يناير**: يوم الثورة / عيد الشرطة الوطني
- **25 أبريل**: عيد تحرير سيناء
- **1 مايو**: عيد العمال
- **23 يوليو**: عيد الثورة
- **6 أكتوبر**: عيد القوات المسلحة
- **23 ديسمبر**: يوم النصر

## الأعياد الإسلامية (تواريخ متغيرة)
- **عيد الفطر**: احتفال يستمر 3 أيام بمناسبة نهاية شهر رمضان
- **عيد الأضحى**: احتفال التضحية الذي يستمر 4 أيام
- **رأس السنة الهجرية**: اليوم الأول من محرم
- **المولد النبوي**: ذكرى ميلاد النبي محمد

## أيام مهمة أخرى
- **شم النسيم**: مهرجان الربيع (الاثنين بعد عيد الفصح القبطي)
- **عيد الفصح القبطي**: وفقًا للتقويم القبطي (عادة في أبريل)

### ملاحظات مهمة للمسافرين:
- خلال الأعياد الإسلامية، خاصة عيد الفطر وعيد الأضحى، قد يكون للعديد من الشركات والمكاتب الحكومية وبعض المواقع السياحية ساعات عمل مخفضة أو تكون مغلقة.
- البنوك والمكاتب الحكومية مغلقة عادة في جميع العطلات الرسمية.
- قد تكون وسائل النقل أكثر ازدحامًا خلال فترات العطلات.
- يؤثر شهر رمضان على الحياة اليومية في جميع أنحاء البلاد، مع إغلاق العديد من المطاعم خلال ساعات النهار وتغيير ساعات العمل.
- يُنصح بالتحقق من التواريخ المحددة للأعياد الإسلامية لسنة سفرك، حيث تتقدم بحوالي 11 يومًا كل عام في التقويم الميلادي.
                """
            },
            'tags': ['holidays', 'festivals', 'public holidays', 'religious holidays', 'national holidays'],
            'is_featured': True,
            'related_destination_ids': ['egypt']
        }
    ]
    
    # Combine all practical info
    all_info.extend(emergency_contacts)
    all_info.extend(embassies_consulates)
    all_info.extend(public_holidays)
    
    # Insert practical info into database
    with conn.cursor() as cursor:
        for info in all_info:
            cursor.execute("""
                INSERT INTO practical_info (
                    category_id, title, content, related_destination_ids, tags,
                    is_featured, embedding, created_at, updated_at, user_id
                ) VALUES (
                    %s, %s::jsonb, %s::jsonb, %s, %s,
                    %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'system'
                )
            """, (
                info['category_id'],
                json.dumps(info['title']),
                json.dumps(info['content']),
                info['related_destination_ids'],
                info['tags'],
                info['is_featured'],
                generate_embedding()
            ))
    
    conn.commit()
    logger.info(f"Generated {len(all_info)} practical info entries")
    return all_info

def verify_practical_info(conn):
    """Verify the practical info data in the database"""
    try:
        with conn.cursor() as cursor:
            # Check practical info categories count
            cursor.execute("SELECT COUNT(*) FROM practical_info_categories")
            category_count = cursor.fetchone()[0]
            logger.info(f"Total practical info categories in database: {category_count}")

            # Check practical info count
            cursor.execute("SELECT COUNT(*) FROM practical_info")
            info_count = cursor.fetchone()[0]
            logger.info(f"Total practical info entries in database: {info_count}")

            # Check practical info by category
            cursor.execute("""
                SELECT category_id, COUNT(*) as count 
                FROM practical_info
                GROUP BY category_id
                ORDER BY count DESC
            """)
            category_counts = cursor.fetchall()
            logger.info("Practical info by category:")
            for category in category_counts:
                logger.info(f"  - {category[0]}: {category[1]} entries")

            # Check if we have enough data
            if category_count > 0 and info_count > 0:
                logger.info("✅ Practical info data generation successful")
                return True
            else:
                logger.warning("⚠️ Practical info data generation failed")
                return False
    except Exception as e:
        logger.error(f"Error verifying practical info: {str(e)}")
        return False

def main():
    """Main function to generate practical info data"""
    try:
        # Connect to database
        conn = connect_to_db()

        # Get existing data
        existing_data = get_existing_data(conn)

        # Generate practical info
        generate_practical_info(conn, existing_data)

        # Verify practical info
        verify_practical_info(conn)

        logger.info("Practical info data generation completed successfully")
        return True

    except Exception as e:
        logger.error(f"Error generating practical info data: {str(e)}", exc_info=True)
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
