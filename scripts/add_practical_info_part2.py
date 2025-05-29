#!/usr/bin/env python3
"""
Script to add practical information to the database - Part 2.
Covers: electricity_plugs and internet_connectivity categories.
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
    # Electricity & Plugs
    {
        "category_id": "electricity_plugs",
        "title": {
            "en": "Electricity and Power Adapters in Egypt",
            "ar": "الكهرباء ومحولات الطاقة في مصر"
        },
        "content": {
            "en": """
# Electricity and Power Adapters in Egypt

Understanding Egypt's electrical system will help you ensure your devices work properly during your visit.

## Voltage and Frequency

- **Standard Voltage**: 220V
- **Frequency**: 50Hz
- **Comparison**: This is different from North America (120V, 60Hz) but similar to most of Europe and Asia

## Plug Types

Egypt primarily uses two types of electrical plugs:

### Type C (European 2-pin)
- Two round pins
- Most common in hotels, homes, and businesses
- Compatible with European devices

### Type F (Schuko)
- Two round pins with two earth clips on the side
- Found in newer buildings and upscale hotels
- Compatible with European Schuko plugs

## What You Need to Bring

### If you're from Europe, Africa, or most of Asia:
- Most of your devices will work without adapters
- No voltage converter needed

### If you're from North America, Japan, or other 110-120V countries:
- **Voltage converter/transformer**: Required for devices that don't support 220V
- **Plug adapter**: To fit your plugs into Egyptian sockets

### If you're from the UK, Ireland, Singapore, or Hong Kong:
- **Plug adapter**: To convert from Type G (UK) to Type C/F (Egypt)
- No voltage converter needed

## Dual Voltage Devices

Many modern electronic devices (laptops, phone chargers, cameras) are dual voltage and will work with 100-240V. Check your device's label or charger for "INPUT: 100-240V, 50/60Hz" to confirm.

## Power Reliability

- **Urban areas**: Generally reliable power with occasional brief outages
- **Rural areas**: May experience more frequent power cuts
- **Tourist facilities**: Most hotels and resorts have backup generators

## Where to Buy Adapters

- **Before travel**: Purchase universal adapters from travel stores or online
- **In Egypt**: Available at electronics shops in major cities and some hotel gift shops
- **Cairo Airport**: Several shops sell adapters in the arrival terminals

## Tips

1. **Power strips**: Bringing a power strip from your home country can be useful to charge multiple devices with just one adapter
2. **USB charging**: Many hotels now offer USB charging ports, reducing the need for adapters
3. **Surge protection**: Consider bringing a surge protector for sensitive electronics
4. **Hair dryers/straighteners**: These high-power devices are particularly vulnerable to voltage differences. Many hotels provide hair dryers
5. **Battery packs**: Useful backup for mobile devices during power outages or long excursions

Remember to check all your essential devices before traveling to determine your adapter and converter needs.
            """,
            "ar": """
# الكهرباء ومحولات الطاقة في مصر

فهم نظام الكهرباء في مصر سيساعدك على ضمان عمل أجهزتك بشكل صحيح خلال زيارتك.

## الجهد والتردد

- **الجهد القياسي**: 220 فولت
- **التردد**: 50 هرتز
- **المقارنة**: هذا يختلف عن أمريكا الشمالية (120 فولت، 60 هرتز) ولكنه مشابه لمعظم أوروبا وآسيا

## أنواع القوابس

تستخدم مصر بشكل أساسي نوعين من القوابس الكهربائية:

### النوع C (أوروبي ثنائي السن)
- سنان مستديران
- الأكثر شيوعًا في الفنادق والمنازل والشركات
- متوافق مع الأجهزة الأوروبية

### النوع F (شوكو)
- سنان مستديران مع مشبكي تأريض على الجانب
- موجود في المباني الجديدة والفنادق الراقية
- متوافق مع قوابس شوكو الأوروبية

## ما تحتاج إلى إحضاره

### إذا كنت من أوروبا أو أفريقيا أو معظم آسيا:
- ستعمل معظم أجهزتك بدون محولات
- لا حاجة لمحول الجهد

### إذا كنت من أمريكا الشمالية أو اليابان أو دول أخرى بجهد 110-120 فولت:
- **محول/محول الجهد**: مطلوب للأجهزة التي لا تدعم 220 فولت
- **محول القابس**: لتناسب قوابسك مع المقابس المصرية

### إذا كنت من المملكة المتحدة أو أيرلندا أو سنغافورة أو هونغ كونغ:
- **محول القابس**: للتحويل من النوع G (المملكة المتحدة) إلى النوع C/F (مصر)
- لا حاجة لمحول الجهد

## الأجهزة ثنائية الجهد

العديد من الأجهزة الإلكترونية الحديثة (أجهزة الكمبيوتر المحمولة، شواحن الهواتف، الكاميرات) ثنائية الجهد وستعمل مع 100-240 فولت. تحقق من ملصق جهازك أو الشاحن للتأكد من "INPUT: 100-240V, 50/60Hz".

## موثوقية الطاقة

- **المناطق الحضرية**: طاقة موثوقة بشكل عام مع انقطاعات قصيرة عرضية
- **المناطق الريفية**: قد تشهد انقطاعات تيار كهربائي أكثر تكرارًا
- **المرافق السياحية**: معظم الفنادق والمنتجعات لديها مولدات احتياطية

## أين تشتري المحولات

- **قبل السفر**: اشترِ محولات عالمية من متاجر السفر أو عبر الإنترنت
- **في مصر**: متوفرة في محلات الإلكترونيات في المدن الكبرى وبعض متاجر الهدايا في الفنادق
- **مطار القاهرة**: تبيع العديد من المتاجر محولات في صالات الوصول

## نصائح

1. **شرائط الطاقة**: إحضار شريط طاقة من بلدك يمكن أن يكون مفيدًا لشحن أجهزة متعددة بمحول واحد فقط
2. **شحن USB**: تقدم العديد من الفنادق الآن منافذ شحن USB، مما يقلل الحاجة إلى المحولات
3. **حماية من التيار المفاجئ**: فكر في إحضار واقي من التيار المفاجئ للإلكترونيات الحساسة
4. **مجففات الشعر/أدوات التمليس**: هذه الأجهزة عالية الطاقة معرضة بشكل خاص لاختلافات الجهد. توفر العديد من الفنادق مجففات شعر
5. **بطاريات احتياطية**: مفيدة كاحتياطي للأجهزة المحمولة أثناء انقطاع التيار الكهربائي أو الرحلات الطويلة

تذكر أن تتحقق من جميع أجهزتك الأساسية قبل السفر لتحديد احتياجاتك من المحولات والمحولات.
            """
        },
        "tags": ["electricity", "voltage", "power adapters", "plugs", "electronics"]
    },
    
    # Internet & Connectivity
    {
        "category_id": "internet_connectivity",
        "title": {
            "en": "Internet and Mobile Connectivity in Egypt",
            "ar": "الإنترنت والاتصال المحمول في مصر"
        },
        "content": {
            "en": """
# Internet and Mobile Connectivity in Egypt

Staying connected during your visit to Egypt is relatively straightforward with the right preparation.

## Mobile Networks

Egypt has four main mobile network operators:

1. **Vodafone Egypt** - Largest coverage and generally fastest speeds
2. **Orange Egypt** (formerly Mobinil) - Good coverage in urban areas
3. **Etisalat Misr** - Competitive pricing and growing coverage
4. **WE** (Telecom Egypt) - Newest operator with expanding 4G network

## Getting a SIM Card

### Where to Buy
- **Airport**: Kiosks in arrival terminals (slightly more expensive)
- **Official stores**: Vodafone, Orange, Etisalat, and WE shops in malls and city centers
- **Small mobile shops**: Found throughout cities and towns

### Requirements
- **Passport**: Required for registration
- **Registration**: Your SIM will be registered to your passport
- **Activation**: Usually immediate or within a few hours

### Recommended Packages
- **Tourist SIMs**: Special packages with data, local minutes, and sometimes international minutes
- **Data-only SIMs**: If you primarily need internet access
- **Regular prepaid**: Can be topped up as needed

## Internet Speeds and Coverage

- **Urban areas**: 4G/LTE widely available in Cairo, Alexandria, and tourist cities
- **Rural areas**: 3G more common, with some areas limited to 2G
- **Tourist sites**: Most major attractions and hotels have good coverage
- **Speed expectations**: 5-20 Mbps in urban areas, slower in remote locations

## Wi-Fi Availability

- **Hotels**: Most hotels offer free Wi-Fi, though quality varies
- **Cafes**: International chains and many local cafes offer free Wi-Fi
- **Restaurants**: Many restaurants in tourist areas provide Wi-Fi
- **Public Wi-Fi**: Limited in public spaces, but available in some malls and airports

## Internet Restrictions

- **VoIP services**: Some VoIP applications may be restricted
- **VPN**: Consider installing a VPN before arrival if you need unrestricted access
- **Social media**: Generally accessible without restrictions
- **Content restrictions**: Some political and religious content may be blocked

## Cost Guide (Approximate)

- **Tourist SIM packages**: 200-300 EGP (includes data and local minutes)
- **Data packages**: 50-200 EGP depending on data amount (5-20 GB)
- **Prepaid credit**: Available in denominations from 5-200 EGP

## Tips for Staying Connected

1. **Download offline maps**: Google Maps, Maps.me allow offline navigation
2. **Install translation apps**: Google Translate with Arabic downloaded offline
3. **Portable power banks**: Useful for long days of sightseeing
4. **Public charging**: Limited, so plan accordingly
5. **International roaming**: Check with your home provider for Egypt roaming packages as an alternative to local SIMs

## Emergency Connectivity

- **Tourist police hotline**: 126 (works without a SIM card)
- **Emergency services**: 122 (police), 123 (ambulance) work without a SIM card
- **Hotel phones**: Available if your mobile service is unavailable
            """,
            "ar": """
# الإنترنت والاتصال المحمول في مصر

البقاء على اتصال خلال زيارتك لمصر أمر سهل نسبيًا مع الإعداد المناسب.

## شبكات المحمول

لدى مصر أربعة مشغلين رئيسيين لشبكات المحمول:

1. **فودافون مصر** - أكبر تغطية وسرعات أسرع بشكل عام
2. **أورانج مصر** (موبينيل سابقًا) - تغطية جيدة في المناطق الحضرية
3. **اتصالات مصر** - أسعار تنافسية وتغطية متنامية
4. **WE** (المصرية للاتصالات) - أحدث مشغل مع شبكة 4G متوسعة

## الحصول على بطاقة SIM

### أين تشتري
- **المطار**: أكشاك في صالات الوصول (أغلى قليلاً)
- **المتاجر الرسمية**: متاجر فودافون وأورانج واتصالات وWE في مراكز التسوق ومراكز المدن
- **متاجر المحمول الصغيرة**: موجودة في جميع أنحاء المدن والبلدات

### المتطلبات
- **جواز السفر**: مطلوب للتسجيل
- **التسجيل**: سيتم تسجيل بطاقة SIM الخاصة بك على جواز سفرك
- **التفعيل**: عادة فوري أو في غضون ساعات قليلة

### الباقات الموصى بها
- **بطاقات SIM للسياح**: باقات خاصة مع بيانات ودقائق محلية وأحيانًا دقائق دولية
- **بطاقات SIM للبيانات فقط**: إذا كنت تحتاج بشكل أساسي إلى الوصول إلى الإنترنت
- **الدفع المسبق العادي**: يمكن إعادة تعبئته حسب الحاجة

## سرعات وتغطية الإنترنت

- **المناطق الحضرية**: 4G/LTE متوفر على نطاق واسع في القاهرة والإسكندرية والمدن السياحية
- **المناطق الريفية**: 3G أكثر شيوعًا، مع بعض المناطق المحدودة بـ 2G
- **المواقع السياحية**: معظم المعالم السياحية والفنادق الرئيسية لديها تغطية جيدة
- **توقعات السرعة**: 5-20 ميجابت في الثانية في المناطق الحضرية، أبطأ في المواقع النائية

## توفر Wi-Fi

- **الفنادق**: تقدم معظم الفنادق خدمة Wi-Fi مجانية، على الرغم من اختلاف الجودة
- **المقاهي**: السلاسل الدولية والعديد من المقاهي المحلية تقدم خدمة Wi-Fi مجانية
- **المطاعم**: توفر العديد من المطاعم في المناطق السياحية خدمة Wi-Fi
- **Wi-Fi العام**: محدود في الأماكن العامة، ولكنه متوفر في بعض مراكز التسوق والمطارات

## قيود الإنترنت

- **خدمات VoIP**: قد تكون بعض تطبيقات VoIP مقيدة
- **VPN**: فكر في تثبيت VPN قبل الوصول إذا كنت بحاجة إلى وصول غير مقيد
- **وسائل التواصل الاجتماعي**: يمكن الوصول إليها بشكل عام دون قيود
- **قيود المحتوى**: قد يتم حظر بعض المحتوى السياسي والديني

## دليل التكلفة (تقريبي)

- **باقات بطاقات SIM للسياح**: 200-300 جنيه مصري (تشمل البيانات والدقائق المحلية)
- **باقات البيانات**: 50-200 جنيه مصري حسب كمية البيانات (5-20 جيجابايت)
- **رصيد الدفع المسبق**: متوفر بفئات من 5-200 جنيه مصري

## نصائح للبقاء على اتصال

1. **تنزيل الخرائط دون اتصال**: تسمح خرائط Google وMaps.me بالتنقل دون اتصال
2. **تثبيت تطبيقات الترجمة**: Google Translate مع تنزيل اللغة العربية دون اتصال
3. **بنوك الطاقة المحمولة**: مفيدة لأيام طويلة من مشاهدة المعالم السياحية
4. **الشحن العام**: محدود، لذا خطط وفقًا لذلك
5. **التجوال الدولي**: تحقق مع مزود الخدمة في بلدك للحصول على باقات التجوال في مصر كبديل لبطاقات SIM المحلية

## الاتصال في حالات الطوارئ

- **الخط الساخن للشرطة السياحية**: 126 (يعمل بدون بطاقة SIM)
- **خدمات الطوارئ**: 122 (الشرطة)، 123 (الإسعاف) تعمل بدون بطاقة SIM
- **هواتف الفندق**: متاحة إذا كانت خدمة الهاتف المحمول الخاصة بك غير متوفرة
            """
        },
        "tags": ["internet", "mobile", "SIM card", "Wi-Fi", "connectivity", "4G", "data"]
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
    logger.info("Starting to add practical information (Part 2)...")
    
    # Connect to database
    conn = connect_to_db()
    
    # Add practical info
    added_count, skipped_count = add_practical_info(conn, PRACTICAL_INFO_TO_ADD)
    
    # Close connection
    conn.close()
    
    logger.info(f"Added {added_count} new practical info items, skipped {skipped_count} existing items.")

if __name__ == "__main__":
    main()
