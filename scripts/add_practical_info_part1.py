#!/usr/bin/env python3
"""
Script to add practical information to the database - Part 1.
Covers: business_hours and tipping_customs categories.
"""

import os
import sys
import json
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
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

# Practical info to add
PRACTICAL_INFO_TO_ADD = [
    # Business Hours
    {
        "category_id": "business_hours",
        "title": {
            "en": "Standard Business Hours in Egypt",
            "ar": "ساعات العمل القياسية في مصر"
        },
        "content": {
            "en": """
# Standard Business Hours in Egypt

Understanding business hours in Egypt will help you plan your activities efficiently during your visit.

## Government Offices
- **Hours**: Sunday to Thursday, 8:00 AM to 2:00 PM
- **Closed**: Friday and Saturday
- **Notes**: Some government offices may close earlier during Ramadan

## Banks
- **Hours**: Sunday to Thursday, 8:30 AM to 2:00 PM
- **Closed**: Friday and Saturday
- **ATMs**: Available 24/7 throughout major cities and tourist areas
- **Notes**: Some banks in malls may have extended hours until 5:00 PM

## Shopping Malls
- **Hours**: Daily from 10:00 AM to 10:00 PM or 11:00 PM
- **Peak times**: Evenings, especially on weekends (Friday and Saturday)
- **Notes**: During Ramadan, malls often stay open until after midnight

## Local Shops and Markets
- **Small shops**: Generally open from 10:00 AM until 10:00 PM
- **Markets (souks)**: Usually busiest in the afternoons and evenings
- **Khan el-Khalili and other tourist markets**: Open until late evening (around 11:00 PM)

## Restaurants and Cafes
- **Breakfast**: 7:00 AM to 11:00 AM
- **Lunch**: 12:00 PM to 4:00 PM
- **Dinner**: 7:00 PM to midnight
- **Cafes**: Often open from mid-morning until midnight or later
- **Notes**: During Ramadan, many restaurants close during daylight hours and reopen after sunset

## Tourist Attractions
- **Archaeological sites**: Usually open from 8:00 AM or 9:00 AM until 4:00 PM or 5:00 PM
- **Museums**: Typically open from 9:00 AM to 5:00 PM, closed on certain weekdays (varies by museum)
- **Religious sites**: May close during prayer times; non-Muslims cannot enter mosques during prayer times

## Important Notes
- Friday is the main day of prayer for Muslims, so expect reduced hours or closures, especially from 11:00 AM to 2:00 PM
- During Ramadan, business hours change significantly, with many places opening later and closing later
- Summer and winter hours may vary for some attractions, especially outdoor archaeological sites
- Always check specific opening hours for attractions you plan to visit, as they may change seasonally or for special events
            """,
            "ar": """
# ساعات العمل القياسية في مصر

فهم ساعات العمل في مصر سيساعدك على تخطيط أنشطتك بكفاءة خلال زيارتك.

## المكاتب الحكومية
- **الساعات**: من الأحد إلى الخميس، 8:00 صباحًا إلى 2:00 ظهرًا
- **مغلق**: الجمعة والسبت
- **ملاحظات**: قد تغلق بعض المكاتب الحكومية مبكرًا خلال شهر رمضان

## البنوك
- **الساعات**: من الأحد إلى الخميس، 8:30 صباحًا إلى 2:00 ظهرًا
- **مغلق**: الجمعة والسبت
- **أجهزة الصراف الآلي**: متاحة على مدار 24 ساعة في المدن الرئيسية والمناطق السياحية
- **ملاحظات**: قد تمتد ساعات عمل بعض البنوك في مراكز التسوق حتى الساعة 5:00 مساءً

## مراكز التسوق
- **الساعات**: يوميًا من 10:00 صباحًا إلى 10:00 مساءً أو 11:00 مساءً
- **أوقات الذروة**: المساء، خاصة في عطلات نهاية الأسبوع (الجمعة والسبت)
- **ملاحظات**: خلال شهر رمضان، غالبًا ما تبقى مراكز التسوق مفتوحة حتى ما بعد منتصف الليل

## المتاجر المحلية والأسواق
- **المتاجر الصغيرة**: عادة مفتوحة من 10:00 صباحًا حتى 10:00 مساءً
- **الأسواق (الأسواق التقليدية)**: عادة ما تكون أكثر ازدحامًا في فترة ما بعد الظهر والمساء
- **خان الخليلي وغيرها من الأسواق السياحية**: مفتوحة حتى وقت متأخر من المساء (حوالي 11:00 مساءً)

## المطاعم والمقاهي
- **الإفطار**: 7:00 صباحًا إلى 11:00 صباحًا
- **الغداء**: 12:00 ظهرًا إلى 4:00 عصرًا
- **العشاء**: 7:00 مساءً إلى منتصف الليل
- **المقاهي**: غالبًا ما تكون مفتوحة من منتصف الصباح حتى منتصف الليل أو بعد ذلك
- **ملاحظات**: خلال شهر رمضان، تغلق العديد من المطاعم خلال ساعات النهار وتعيد فتح أبوابها بعد غروب الشمس

## المعالم السياحية
- **المواقع الأثرية**: عادة مفتوحة من 8:00 صباحًا أو 9:00 صباحًا حتى 4:00 مساءً أو 5:00 مساءً
- **المتاحف**: عادة مفتوحة من 9:00 صباحًا إلى 5:00 مساءً، مغلقة في أيام معينة من الأسبوع (تختلف حسب المتحف)
- **المواقع الدينية**: قد تغلق خلال أوقات الصلاة؛ لا يمكن لغير المسلمين دخول المساجد خلال أوقات الصلاة

## ملاحظات مهمة
- الجمعة هو اليوم الرئيسي للصلاة للمسلمين، لذا توقع ساعات عمل مخفضة أو إغلاق، خاصة من 11:00 صباحًا إلى 2:00 ظهرًا
- خلال شهر رمضان، تتغير ساعات العمل بشكل كبير، حيث تفتح العديد من الأماكن في وقت لاحق وتغلق في وقت لاحق
- قد تختلف ساعات الصيف والشتاء لبعض المعالم، خاصة المواقع الأثرية الخارجية
- تحقق دائمًا من ساعات الفتح المحددة للمعالم التي تخطط لزيارتها، لأنها قد تتغير موسميًا أو للمناسبات الخاصة
            """
        },
        "tags": ["business hours", "opening times", "government offices", "banks", "shopping", "tourist attractions"]
    },
    
    # Tipping Customs
    {
        "category_id": "tipping_customs",
        "title": {
            "en": "Tipping Guide for Egypt",
            "ar": "دليل البقشيش في مصر"
        },
        "content": {
            "en": """
# Tipping Guide for Egypt

Tipping (baksheesh) is an important part of Egyptian culture and the service economy. This guide will help you navigate tipping expectations during your visit.

## Hotels

### Porters/Bellhops
- **Amount**: 5-10 EGP per bag
- **When**: Upon delivery of luggage to your room

### Housekeeping
- **Amount**: 5-10 EGP per day
- **When**: Daily or at the end of your stay
- **Tip**: Leave the tip in your room in an obvious place (on the pillow or with a note)

### Room Service
- **Amount**: 5-10% of the bill
- **When**: Upon delivery of your order
- **Note**: Check if a service charge is already included in your bill

### Concierge
- **Amount**: 20-50 EGP
- **When**: After they provide a special service (restaurant reservations, tour arrangements, etc.)

## Restaurants

### Waiters
- **Amount**: 10-15% of the bill
- **When**: When paying your bill
- **Note**: Check if a service charge is already included (often 12%). If so, an additional 5% is still appreciated for good service

### Bathroom Attendants
- **Amount**: 1-5 EGP
- **When**: After using the facilities

## Transportation

### Taxi Drivers
- **Amount**: Round up the fare or add 10%
- **When**: When paying your fare
- **Note**: Agree on the fare before starting the journey

### Private Drivers/Tour Drivers
- **Amount**: 50-100 EGP per day
- **When**: At the end of the day or tour

## Tourism

### Tour Guides
- **Amount**: 100-150 EGP per person for a full day tour
- **When**: At the end of the tour
- **Note**: For exceptional service, consider tipping more

### Temple/Museum Attendants
- **Amount**: 5-10 EGP
- **When**: If they show you something special or take photos for you

### Nile Cruise Staff
- **Amount**: Consider a tipping pool of about 60-80 EGP per person per day
- **When**: At the end of the cruise
- **Note**: This is typically distributed among all staff

## General Services

### Shoeshine
- **Amount**: 5-10 EGP
- **When**: After the service

### Henna Artists/Street Performers
- **Amount**: 10-20 EGP
- **When**: After the service/performance

## Important Tips

1. **Carry small bills** - Always keep a supply of small denomination bills (5, 10, 20 EGP) for tipping
2. **Be discreet** - Hand tips directly and discreetly
3. **Adjust for inflation** - These amounts may need to be adjusted based on current economic conditions
4. **Quality matters** - Tip more for exceptional service
5. **No coins** - Tipping with coins is generally not appreciated

Remember that many service workers in Egypt rely heavily on tips as a significant portion of their income. While tipping is not mandatory, it is an expected part of the culture and helps support those in the service industry.
            """,
            "ar": """
# دليل البقشيش في مصر

البقشيش (البخشيش) جزء مهم من الثقافة المصرية واقتصاد الخدمات. سيساعدك هذا الدليل على فهم توقعات البقشيش خلال زيارتك.

## الفنادق

### حاملو الحقائب
- **المبلغ**: 5-10 جنيه مصري لكل حقيبة
- **متى**: عند توصيل الأمتعة إلى غرفتك

### خدمة تنظيف الغرف
- **المبلغ**: 5-10 جنيه مصري في اليوم
- **متى**: يوميًا أو في نهاية إقامتك
- **نصيحة**: اترك البقشيش في غرفتك في مكان واضح (على الوسادة أو مع ملاحظة)

### خدمة الغرف
- **المبلغ**: 5-10٪ من الفاتورة
- **متى**: عند توصيل طلبك
- **ملاحظة**: تحقق مما إذا كانت رسوم الخدمة مدرجة بالفعل في فاتورتك

### الكونسيرج
- **المبلغ**: 20-50 جنيه مصري
- **متى**: بعد تقديمهم خدمة خاصة (حجوزات المطاعم، ترتيبات الجولات، إلخ)

## المطاعم

### النادلون
- **المبلغ**: 10-15٪ من الفاتورة
- **متى**: عند دفع فاتورتك
- **ملاحظة**: تحقق مما إذا كانت رسوم الخدمة مدرجة بالفعل (غالبًا 12٪). إذا كان الأمر كذلك، فإن إضافة 5٪ إضافية لا تزال مقدرة للخدمة الجيدة

### عمال المراحيض
- **المبلغ**: 1-5 جنيه مصري
- **متى**: بعد استخدام المرافق

## المواصلات

### سائقو سيارات الأجرة
- **المبلغ**: قم بتقريب الأجرة أو أضف 10٪
- **متى**: عند دفع الأجرة
- **ملاحظة**: اتفق على الأجرة قبل بدء الرحلة

### السائقون الخاصون/سائقو الجولات
- **المبلغ**: 50-100 جنيه مصري في اليوم
- **متى**: في نهاية اليوم أو الجولة

## السياحة

### المرشدون السياحيون
- **المبلغ**: 100-150 جنيه مصري للشخص الواحد لجولة يوم كامل
- **متى**: في نهاية الجولة
- **ملاحظة**: للخدمة الاستثنائية، فكر في إعطاء بقشيش أكثر

### موظفو المعابد/المتاحف
- **المبلغ**: 5-10 جنيه مصري
- **متى**: إذا أظهروا لك شيئًا خاصًا أو التقطوا صورًا لك

### طاقم الرحلات النيلية
- **المبلغ**: فكر في تجميع بقشيش بحوالي 60-80 جنيه مصري للشخص الواحد في اليوم
- **متى**: في نهاية الرحلة
- **ملاحظة**: يتم توزيع هذا عادة بين جميع الموظفين

## الخدمات العامة

### تلميع الأحذية
- **المبلغ**: 5-10 جنيه مصري
- **متى**: بعد الخدمة

### فناني الحناء/المؤدين في الشوارع
- **المبلغ**: 10-20 جنيه مصري
- **متى**: بعد الخدمة/العرض

## نصائح مهمة

1. **احمل أوراق نقدية صغيرة** - احتفظ دائمًا بمخزون من الأوراق النقدية ذات الفئات الصغيرة (5، 10، 20 جنيه مصري) للبقشيش
2. **كن متحفظًا** - سلم البقشيش مباشرة وبشكل متحفظ
3. **تعديل للتضخم** - قد تحتاج هذه المبالغ إلى تعديل بناءً على الظروف الاقتصادية الحالية
4. **الجودة مهمة** - قدم بقشيشًا أكثر للخدمة الاستثنائية
5. **لا عملات معدنية** - البقشيش بالعملات المعدنية غير مقدر عمومًا

تذكر أن العديد من عمال الخدمة في مصر يعتمدون بشكل كبير على البقشيش كجزء كبير من دخلهم. على الرغم من أن البقشيش ليس إلزاميًا، إلا أنه جزء متوقع من الثقافة ويساعد في دعم العاملين في صناعة الخدمات.
            """
        },
        "tags": ["tipping", "baksheesh", "service", "hotels", "restaurants", "tourism"]
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

def add_practical_info(conn, info_list):
    """Add practical information to the database."""
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get existing info to avoid duplicates
    cursor.execute("SELECT title->>'en' as title_en FROM practical_info")
    existing_titles = [row['title_en'] for row in cursor.fetchall()]
    
    # Add practical info
    added_count = 0
    skipped_count = 0
    
    for info in info_list:
        # Check if info already exists
        if info['title']['en'] in existing_titles:
            logger.info(f"Skipping existing info: {info['title']['en']}")
            skipped_count += 1
            continue
        
        # Prepare data
        now = datetime.now()
        
        # Insert info
        try:
            cursor.execute("""
                INSERT INTO practical_info 
                (category_id, title, content, tags, is_featured, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                info['category_id'],
                json.dumps(info['title']),
                json.dumps(info['content']),
                info.get('tags', None),
                info.get('is_featured', False),
                now,
                now
            ))
            
            info_id = cursor.fetchone()['id']
            logger.info(f"Added practical info ID {info_id}: {info['title']['en']}")
            added_count += 1
            
        except Exception as e:
            logger.error(f"Error adding practical info {info['title']['en']}: {e}")
    
    cursor.close()
    return added_count, skipped_count

def main():
    """Main function."""
    logger.info("Starting to add practical information (Part 1)...")
    
    # Connect to database
    conn = connect_to_db()
    
    # Add practical info
    added_count, skipped_count = add_practical_info(conn, PRACTICAL_INFO_TO_ADD)
    
    # Close connection
    conn.close()
    
    logger.info(f"Added {added_count} new practical info items, skipped {skipped_count} existing items.")

if __name__ == "__main__":
    main()
