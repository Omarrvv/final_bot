#!/usr/bin/env python3
"""
Script to add more practical information to the Egypt Tourism Chatbot database.
This script adds more variations of currency and safety information to improve search results.
"""

import os
import sys
import json
import logging
from typing import Dict, List, Any, Optional

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import necessary modules
from src.knowledge.database import DatabaseManager

def connect_to_database():
    """Connect to the database."""
    try:
        # Get database connection string from environment variable or use default
        db_uri = os.environ.get("POSTGRES_URI", "postgresql://postgres:postgres@localhost:5432/egypt_chatbot")
        
        # Create database manager
        db_manager = DatabaseManager(db_uri)
        
        # Test connection
        if db_manager.connect():
            logger.info("✅ Database connection successful")
            return db_manager
        else:
            logger.error("❌ Database connection failed")
            return None
    except Exception as e:
        logger.error(f"❌ Error connecting to database: {str(e)}")
        return None

def check_if_info_exists(db_manager, category_id, title_en):
    """Check if practical info exists in the practical_info table."""
    try:
        query = """
        SELECT COUNT(*) FROM practical_info 
        WHERE category_id = %s AND title->>'en' = %s
        """
        result = db_manager.execute_query(query, (category_id, title_en))
        return result[0]['count'] > 0 if result else False
    except Exception as e:
        logger.error(f"❌ Error checking if info exists: {str(e)}")
        return False

def add_currency_faq(db_manager):
    """Add currency FAQ to the practical_info table."""
    try:
        # Check if info already exists
        if check_if_info_exists(db_manager, 'currency', 'Currency FAQ for Egypt'):
            logger.info("Currency FAQ already exists")
            return True
        
        # Add currency FAQ
        query = """
        INSERT INTO practical_info (
            category_id,
            title,
            content,
            related_destination_ids,
            tags,
            is_featured
        ) VALUES (
            'currency',
            %s,
            %s,
            ARRAY['egypt'],
            ARRAY['currency', 'money', 'Egyptian pound', 'exchange rates', 'banking', 'ATM', 'tipping', 'FAQ'],
            true
        )
        """
        
        title = json.dumps({
            "en": "Currency FAQ for Egypt",
            "ar": "أسئلة شائعة عن العملة في مصر"
        })
        
        content = json.dumps({
            "en": """# Frequently Asked Questions About Currency in Egypt

## What is the currency used in Egypt?
The official currency of Egypt is the Egyptian Pound (EGP), often abbreviated as LE or E£.

## What are the denominations of Egyptian currency?
Egyptian currency comes in the following denominations:
- **Coins**: 25 pt, 50 pt, 1 LE
- **Notes**: 5, 10, 20, 50, 100, 200 LE

## What's the exchange rate for US dollars in Egypt?
As of May 2025, 1 USD is approximately 48 EGP. Exchange rates fluctuate, so check current rates before your trip.

## Do they accept credit cards in Egypt?
Yes, major credit cards (Visa and Mastercard) are widely accepted in hotels, restaurants, and shops in tourist areas. However, small shops and markets typically only accept cash.

## How much should I tip in Egypt?
Tipping (baksheesh) is customary in Egypt:
- Restaurants: 10-15% if service charge is not included
- Hotel staff: 5-10 LE for porters, 10-20 LE per day for housekeeping
- Tour guides: 50-100 LE per day depending on group size
- Taxi drivers: Rounding up the fare is sufficient

## Where can I exchange money in Egypt?
The best places to exchange money are banks, official exchange offices, and some hotels. Airport exchange services are available but rates are typically less favorable.

## Are there ATMs in Egypt?
Yes, ATMs are widely available in cities and tourist areas. They typically have a withdrawal limit of 2,000-3,000 LE per transaction.

## Should I bring cash to Egypt?
It's advisable to bring some cash for small purchases, taxis, and tips. A combination of cash and cards is ideal for most travelers.

## Is it better to use cash or card in Egypt?
For major expenses like hotels and tours, cards are convenient. For daily expenses, markets, and local shops, cash is essential.

## What documentation do I need to exchange currency?
Bring your passport when exchanging currency. Keep exchange receipts if you plan to convert back to your currency when leaving.""",
            "ar": """# أسئلة شائعة عن العملة في مصر

## ما هي العملة المستخدمة في مصر؟
العملة الرسمية في مصر هي الجنيه المصري (EGP)، ويختصر غالبًا بـ LE أو E£.

## ما هي فئات العملة المصرية؟
تأتي العملة المصرية في الفئات التالية:
- **العملات المعدنية**: 25 قرش، 50 قرش، 1 جنيه
- **الأوراق النقدية**: 5، 10، 20، 50، 100، 200 جنيه

## ما هو سعر صرف الدولار الأمريكي في مصر؟
اعتبارًا من مايو 2025، 1 دولار أمريكي يساوي تقريبًا 48 جنيه مصري. تتقلب أسعار الصرف، لذا تحقق من الأسعار الحالية قبل رحلتك.

## هل يقبلون بطاقات الائتمان في مصر؟
نعم، بطاقات الائتمان الرئيسية (فيزا وماستركارد) مقبولة على نطاق واسع في الفنادق والمطاعم والمتاجر في المناطق السياحية. ومع ذلك، المتاجر الصغيرة والأسواق عادة تقبل النقد فقط.

## كم يجب أن أعطي كبقشيش في مصر؟
البقشيش (الإكرامية) معتاد في مصر:
- المطاعم: 10-15% إذا لم تكن رسوم الخدمة مشمولة
- موظفو الفندق: 5-10 جنيه للحمالين، 10-20 جنيه يوميًا لخدمة الغرف
- المرشدون السياحيون: 50-100 جنيه يوميًا حسب حجم المجموعة
- سائقو سيارات الأجرة: تقريب المبلغ لأعلى يكفي

## أين يمكنني صرف الأموال في مصر؟
أفضل الأماكن لصرف الأموال هي البنوك ومكاتب الصرافة الرسمية وبعض الفنادق. خدمات الصرافة في المطار متوفرة ولكن الأسعار عادة أقل تفضيلاً.

## هل توجد أجهزة الصراف الآلي في مصر؟
نعم، أجهزة الصراف الآلي متوفرة على نطاق واسع في المدن والمناطق السياحية. عادة ما يكون لديها حد سحب من 2000-3000 جنيه مصري لكل معاملة.

## هل يجب أن أحضر نقدًا إلى مصر؟
من المستحسن إحضار بعض النقود للمشتريات الصغيرة وسيارات الأجرة والبقشيش. مزيج من النقد والبطاقات مثالي لمعظم المسافرين.

## هل من الأفضل استخدام النقد أم البطاقة في مصر؟
للنفقات الكبيرة مثل الفنادق والجولات، البطاقات مريحة. للنفقات اليومية والأسواق والمتاجر المحلية، النقد ضروري.

## ما هي الوثائق التي أحتاجها لصرف العملة؟
أحضر جواز سفرك عند صرف العملات. احتفظ بإيصالات الصرف إذا كنت تخطط لتحويل الأموال مرة أخرى إلى عملتك عند المغادرة."""
        })
        
        db_manager.execute_query(query, (title, content))
        logger.info("✅ Currency FAQ added successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Error adding currency FAQ: {str(e)}")
        return False

def add_safety_faq(db_manager):
    """Add safety FAQ to the practical_info table."""
    try:
        # Check if info already exists
        if check_if_info_exists(db_manager, 'safety', 'Safety FAQ for Egypt'):
            logger.info("Safety FAQ already exists")
            return True
        
        # Add safety FAQ
        query = """
        INSERT INTO practical_info (
            category_id,
            title,
            content,
            related_destination_ids,
            tags,
            is_featured
        ) VALUES (
            'safety',
            %s,
            %s,
            ARRAY['egypt'],
            ARRAY['safety', 'security', 'travel tips', 'emergency', 'health', 'scams', 'FAQ'],
            true
        )
        """
        
        title = json.dumps({
            "en": "Safety FAQ for Egypt",
            "ar": "أسئلة شائعة عن السلامة في مصر"
        })
        
        content = json.dumps({
            "en": """# Frequently Asked Questions About Safety in Egypt

## Is Egypt safe for tourists?
Yes, Egypt is generally safe for tourists. The Egyptian government places a high priority on tourist safety with dedicated tourist police at major sites. Like any destination, normal travel precautions should be observed.

## What safety precautions should I take in Egypt?
- Keep copies of your passport and travel documents
- Stay aware of your surroundings, especially in crowded areas
- Use official taxis or ride-sharing apps
- Drink bottled water and be cautious with street food
- Dress modestly, especially at religious sites
- Register with your country's embassy for extended stays

## Are there any areas in Egypt I should avoid?
Most tourist destinations in Egypt are safe to visit. However, it's advisable to avoid the North Sinai region and remote desert areas near the Libyan border. Always check your government's travel advisories before your trip.

## What should I do in case of an emergency in Egypt?
Important emergency numbers in Egypt:
- Police: 122
- Ambulance: 123
- Tourist Police: 126
Contact your embassy or consulate in case of serious emergencies.

## Is it safe to walk around Cairo at night?
Major tourist areas in Cairo like Zamalek and downtown are generally safe at night, but it's advisable to take normal precautions. Women travelers may want to avoid walking alone at night in less populated areas.

## How can I avoid scams in Egypt?
- Agree on taxi fares before starting your journey
- Be wary of "free" gifts or services
- Only use official guides at tourist sites
- Be cautious of anyone claiming your hotel is closed or overbooked
- Research fair prices for souvenirs before shopping

## Is the tap water safe to drink in Egypt?
No, it's recommended to drink bottled water in Egypt. Avoid ice in drinks unless you're sure it's made from purified water.

## Do I need travel insurance for Egypt?
Yes, comprehensive travel insurance that covers medical emergencies is highly recommended for all visitors to Egypt.

## Are there good medical facilities in Egypt?
Major cities have good private hospitals with English-speaking staff. However, medical facilities may be limited in rural areas.

## Is it safe to use public transportation in Egypt?
Public transportation is generally safe but can be crowded. For tourists, using official taxis, Uber, or organized tours is often more convenient and comfortable.""",
            "ar": """# أسئلة شائعة عن السلامة في مصر

## هل مصر آمنة للسياح؟
نعم، مصر آمنة بشكل عام للسياح. تضع الحكومة المصرية أولوية عالية لسلامة السياح مع وجود شرطة سياحية مخصصة في المواقع الرئيسية. مثل أي وجهة، يجب مراعاة احتياطات السفر العادية.

## ما هي احتياطات السلامة التي يجب أن أتخذها في مصر؟
- احتفظ بنسخ من جواز سفرك ووثائق السفر
- ابق على دراية بمحيطك، خاصة في المناطق المزدحمة
- استخدم سيارات الأجرة الرسمية أو تطبيقات مشاركة الركوب
- اشرب الماء المعبأ وكن حذرًا مع طعام الشارع
- ارتدِ ملابس محتشمة، خاصة في المواقع الدينية
- سجل لدى سفارة بلدك للإقامات الطويلة

## هل هناك أي مناطق في مصر يجب أن أتجنبها؟
معظم الوجهات السياحية في مصر آمنة للزيارة. ومع ذلك، يُنصح بتجنب منطقة شمال سيناء والمناطق الصحراوية النائية بالقرب من الحدود الليبية. تحقق دائمًا من تحذيرات السفر الصادرة عن حكومتك قبل رحلتك.

## ماذا يجب أن أفعل في حالة الطوارئ في مصر؟
أرقام الطوارئ المهمة في مصر:
- الشرطة: 122
- الإسعاف: 123
- شرطة السياحة: 126
اتصل بسفارتك أو قنصليتك في حالة الطوارئ الخطيرة.

## هل من الآمن التجول في القاهرة ليلاً؟
المناطق السياحية الرئيسية في القاهرة مثل الزمالك ووسط البلد آمنة بشكل عام في الليل، ولكن يُنصح باتخاذ الاحتياطات العادية. قد ترغب المسافرات في تجنب المشي بمفردهن ليلاً في المناطق الأقل اكتظاظًا بالسكان.

## كيف يمكنني تجنب عمليات الاحتيال في مصر؟
- اتفق على أجرة سيارة الأجرة قبل بدء رحلتك
- كن حذرًا من الهدايا أو الخدمات "المجانية"
- استخدم فقط المرشدين الرسميين في المواقع السياحية
- كن حذرًا من أي شخص يدعي أن فندقك مغلق أو محجوز بالكامل
- ابحث عن الأسعار العادلة للهدايا التذكارية قبل التسوق

## هل ماء الصنبور آمن للشرب في مصر؟
لا، يوصى بشرب الماء المعبأ في مصر. تجنب الثلج في المشروبات ما لم تكن متأكدًا من أنه مصنوع من الماء المنقى.

## هل أحتاج إلى تأمين سفر لمصر؟
نعم، يوصى بشدة بتأمين سفر شامل يغطي حالات الطوارئ الطبية لجميع الزوار إلى مصر.

## هل توجد مرافق طبية جيدة في مصر؟
المدن الكبرى بها مستشفيات خاصة جيدة مع موظفين يتحدثون الإنجليزية. ومع ذلك، قد تكون المرافق الطبية محدودة في المناطق الريفية.

## هل من الآمن استخدام وسائل النقل العام في مصر؟
وسائل النقل العام آمنة بشكل عام ولكنها قد تكون مزدحمة. بالنسبة للسياح، استخدام سيارات الأجرة الرسمية أو أوبر أو الجولات المنظمة غالبًا ما يكون أكثر ملاءمة وراحة."""
        })
        
        db_manager.execute_query(query, (title, content))
        logger.info("✅ Safety FAQ added successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Error adding safety FAQ: {str(e)}")
        return False

def main():
    """Main function to add more practical information to the database."""
    logger.info("Starting to add more practical information to the database")
    
    # Connect to the database
    db_manager = connect_to_database()
    if not db_manager:
        logger.error("Cannot continue without database connection")
        return
    
    # Add currency FAQ
    if not add_currency_faq(db_manager):
        logger.error("Failed to add currency FAQ")
        return
    
    # Add safety FAQ
    if not add_safety_faq(db_manager):
        logger.error("Failed to add safety FAQ")
        return
    
    logger.info("✅ More practical information added successfully to the database")
    
    # Test if the information was added correctly
    try:
        query = "SELECT category_id, title FROM practical_info WHERE title->>'en' LIKE '%FAQ%'"
        result = db_manager.execute_query(query)
        if result:
            logger.info(f"Found {len(result)} FAQ entries in the database")
            for i, row in enumerate(result):
                title = row.get('title', {})
                if isinstance(title, str):
                    try:
                        title = json.loads(title)
                    except:
                        title = {"en": title}
                logger.info(f"  {i+1}. {row.get('category_id')}: {title.get('en', 'Unknown')}")
        else:
            logger.warning("No FAQ information found in the database after adding")
    except Exception as e:
        logger.error(f"❌ Error testing FAQ information: {str(e)}")

if __name__ == "__main__":
    main()
