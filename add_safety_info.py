#!/usr/bin/env python3
"""
Script to add safety information to the Egypt Tourism Chatbot database.
This script adds a safety category to the practical_info_categories table
and adds safety information to the practical_info table.
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

def check_if_category_exists(db_manager, category_id):
    """Check if a category exists in the practical_info_categories table."""
    try:
        query = "SELECT COUNT(*) FROM practical_info_categories WHERE id = %s"
        result = db_manager.execute_query(query, (category_id,))
        return result[0]['count'] > 0 if result else False
    except Exception as e:
        logger.error(f"❌ Error checking if category exists: {str(e)}")
        return False

def add_safety_category(db_manager):
    """Add safety category to the practical_info_categories table."""
    try:
        # Check if category already exists
        if check_if_category_exists(db_manager, 'safety'):
            logger.info("Safety category already exists")
            return True
        
        # Add safety category
        query = """
        INSERT INTO practical_info_categories (
            id,
            name,
            description,
            icon,
            created_at,
            updated_at
        ) VALUES (
            'safety',
            %s,
            %s,
            'shield-alt',
            NOW(),
            NOW()
        )
        """
        
        name = json.dumps({
            "en": "Safety & Security",
            "ar": "الأمن والسلامة"
        })
        
        description = json.dumps({
            "en": "Information about safety and security for travelers in Egypt",
            "ar": "معلومات عن الأمن والسلامة للمسافرين في مصر"
        })
        
        db_manager.execute_query(query, (name, description))
        logger.info("✅ Safety category added successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Error adding safety category: {str(e)}")
        return False

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

def add_safety_info(db_manager):
    """Add safety information to the practical_info table."""
    try:
        # Check if info already exists
        if check_if_info_exists(db_manager, 'safety', 'Safety Tips for Travelers in Egypt'):
            logger.info("Safety information already exists")
            return True
        
        # Add safety information
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
            ARRAY['safety', 'security', 'travel tips', 'emergency', 'health', 'scams'],
            true
        )
        """
        
        title = json.dumps({
            "en": "Safety Tips for Travelers in Egypt",
            "ar": "نصائح السلامة للمسافرين في مصر"
        })
        
        content = json.dumps({
            "en": """# Safety Tips for Travelers in Egypt

Egypt is generally a safe destination for tourists, but like any travel destination, it's important to be aware of potential risks and take appropriate precautions.

## General Safety

- **Tourist Police**: Egypt has a dedicated tourist police force to assist visitors. They wear white uniforms and can be found at major tourist sites.
- **Emergency Numbers**: 
  - Police: 122
  - Ambulance: 123
  - Tourist Police: 126
- **Travel Documents**: Keep copies of your passport, visa, and travel insurance in a separate place from the originals.
- **Register with Embassy**: Consider registering with your country's embassy upon arrival for extended stays.

## Health and Medical Safety

- **Drinking Water**: Drink only bottled water and avoid ice in drinks unless you're sure it's made from purified water.
- **Food Safety**: Eat at reputable restaurants and avoid raw vegetables, unpeeled fruits, and street food if you have a sensitive stomach.
- **Sun Protection**: Egypt's sun can be intense. Wear sunscreen, a hat, and sunglasses, and stay hydrated.
- **Medical Facilities**: Major cities have good private hospitals. Carry basic medications and a small first-aid kit.
- **Travel Insurance**: Ensure you have comprehensive travel insurance that covers medical emergencies.

## Transportation Safety

- **Taxis**: Use official taxis or ride-sharing apps. Agree on the fare before starting your journey or insist on using the meter.
- **Public Transportation**: Be vigilant about your belongings on crowded buses and metros.
- **Road Safety**: Traffic in Egypt can be chaotic. Cross streets carefully and be cautious when walking near roadways.
- **Nile Cruises**: Choose reputable operators for Nile cruises and check that life jackets are available.

## Avoiding Scams and Harassment

- **Common Scams**: Be aware of common scams such as "free" gifts that come with pressure to buy, unofficial tour guides, or taxi drivers claiming your hotel is closed.
- **Bargaining**: Haggling is expected in markets, but do so respectfully. Start at about 50% of the initial asking price.
- **Unwanted Attention**: Female travelers may experience unwanted attention. Dress modestly (covering shoulders and knees) to minimize this.
- **Photography**: Always ask before photographing locals, and be aware that photography is restricted in some areas, including airports and military installations.

## Regional Considerations

- **North Sinai**: Avoid travel to North Sinai due to ongoing security concerns.
- **Western Desert**: Travel to remote desert areas should be with reputable tour operators and with proper permits.
- **Border Areas**: Exercise caution near border regions, particularly near Libya and Sudan.

## Cultural Sensitivity

- **Ramadan**: During the holy month of Ramadan, be respectful by not eating, drinking, or smoking in public during daylight hours.
- **Religious Sites**: Dress modestly when visiting mosques and religious sites. Women should cover their hair.
- **Local Customs**: Familiarize yourself with local customs and traditions to avoid unintentionally causing offense.

## Staying Informed

- **Local News**: Stay informed about local events and follow the advice of local authorities.
- **Travel Advisories**: Check your government's travel advisories before and during your trip.
- **Weather Alerts**: Be aware of weather conditions, especially if traveling during summer when extreme heat can pose health risks.

Remember that most visits to Egypt are trouble-free, and the Egyptian people are known for their hospitality. By taking these precautions and staying aware of your surroundings, you can enjoy a safe and memorable trip to this fascinating country.""",
            "ar": """# نصائح السلامة للمسافرين في مصر

مصر بشكل عام وجهة آمنة للسياح، ولكن مثل أي وجهة سفر، من المهم أن تكون على دراية بالمخاطر المحتملة واتخاذ الاحتياطات المناسبة.

## السلامة العامة

- **شرطة السياحة**: لدى مصر قوة شرطة سياحية مخصصة لمساعدة الزوار. يرتدون زيًا أبيض ويمكن العثور عليهم في المواقع السياحية الرئيسية.
- **أرقام الطوارئ**: 
  - الشرطة: 122
  - الإسعاف: 123
  - شرطة السياحة: 126
- **وثائق السفر**: احتفظ بنسخ من جواز سفرك وتأشيرتك وتأمين السفر في مكان منفصل عن النسخ الأصلية.
- **التسجيل لدى السفارة**: فكر في التسجيل لدى سفارة بلدك عند الوصول للإقامات الطويلة.

## الصحة والسلامة الطبية

- **مياه الشرب**: اشرب الماء المعبأ فقط وتجنب الثلج في المشروبات ما لم تكن متأكدًا من أنه مصنوع من الماء المنقى.
- **سلامة الغذاء**: تناول الطعام في المطاعم ذات السمعة الطيبة وتجنب الخضروات النيئة والفواكه غير المقشرة وطعام الشارع إذا كانت معدتك حساسة.
- **الحماية من الشمس**: شمس مصر يمكن أن تكون قوية. ضع واقي الشمس وارتدِ قبعة ونظارات شمسية، وحافظ على ترطيب جسمك.
- **المرافق الطبية**: المدن الكبرى بها مستشفيات خاصة جيدة. احمل الأدوية الأساسية وحقيبة إسعافات أولية صغيرة.
- **تأمين السفر**: تأكد من أن لديك تأمين سفر شامل يغطي حالات الطوارئ الطبية.

## سلامة النقل

- **سيارات الأجرة**: استخدم سيارات الأجرة الرسمية أو تطبيقات مشاركة الركوب. اتفق على الأجرة قبل بدء رحلتك أو أصر على استخدام العداد.
- **وسائل النقل العام**: كن يقظًا بشأن متعلقاتك في الحافلات والمترو المزدحمة.
- **السلامة على الطرق**: حركة المرور في مصر يمكن أن تكون فوضوية. اعبر الشوارع بحذر وكن حذرًا عند المشي بالقرب من الطرق.
- **رحلات النيل**: اختر مشغلين ذوي سمعة طيبة لرحلات النيل وتحقق من توفر سترات النجاة.

## تجنب عمليات الاحتيال والمضايقات

- **عمليات الاحتيال الشائعة**: كن على دراية بعمليات الاحتيال الشائعة مثل الهدايا "المجانية" التي تأتي مع الضغط للشراء، أو المرشدين السياحيين غير الرسميين، أو سائقي سيارات الأجرة الذين يدعون أن فندقك مغلق.
- **المساومة**: المساومة متوقعة في الأسواق، ولكن افعل ذلك باحترام. ابدأ بحوالي 50٪ من السعر المطلوب الأولي.
- **الاهتمام غير المرغوب فيه**: قد تواجه المسافرات اهتمامًا غير مرغوب فيه. ارتدِ ملابس محتشمة (تغطي الكتفين والركبتين) لتقليل ذلك.
- **التصوير الفوتوغرافي**: اطلب دائمًا الإذن قبل تصوير السكان المحليين، وكن على دراية بأن التصوير الفوتوغرافي مقيد في بعض المناطق، بما في ذلك المطارات والمنشآت العسكرية.

## اعتبارات إقليمية

- **شمال سيناء**: تجنب السفر إلى شمال سيناء بسبب المخاوف الأمنية المستمرة.
- **الصحراء الغربية**: يجب أن يكون السفر إلى المناطق الصحراوية النائية مع منظمي رحلات ذوي سمعة طيبة وبتصاريح مناسبة.
- **مناطق الحدود**: توخ الحذر بالقرب من المناطق الحدودية، خاصة بالقرب من ليبيا والسودان.

## الحساسية الثقافية

- **رمضان**: خلال شهر رمضان المبارك، كن محترمًا بعدم الأكل أو الشرب أو التدخين في الأماكن العامة خلال ساعات النهار.
- **المواقع الدينية**: ارتدِ ملابس محتشمة عند زيارة المساجد والمواقع الدينية. يجب على النساء تغطية شعرهن.
- **العادات المحلية**: تعرف على العادات والتقاليد المحلية لتجنب التسبب في الإساءة دون قصد.

## البقاء على اطلاع

- **الأخبار المحلية**: ابق على اطلاع بالأحداث المحلية واتبع نصيحة السلطات المحلية.
- **تحذيرات السفر**: تحقق من تحذيرات السفر الصادرة عن حكومتك قبل وأثناء رحلتك.
- **تنبيهات الطقس**: كن على دراية بظروف الطقس، خاصة إذا كنت مسافرًا خلال الصيف عندما يمكن أن تشكل الحرارة الشديدة مخاطر صحية.

تذكر أن معظم الزيارات إلى مصر تمر دون مشاكل، والشعب المصري معروف بضيافته. من خلال اتخاذ هذه الاحتياطات والبقاء على دراية بمحيطك، يمكنك الاستمتاع برحلة آمنة ولا تُنسى إلى هذا البلد الرائع."""
        })
        
        db_manager.execute_query(query, (title, content))
        logger.info("✅ Safety information added successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Error adding safety information: {str(e)}")
        return False

def main():
    """Main function to add safety information to the database."""
    logger.info("Starting to add safety information to the database")
    
    # Connect to the database
    db_manager = connect_to_database()
    if not db_manager:
        logger.error("Cannot continue without database connection")
        return
    
    # Add safety category
    if not add_safety_category(db_manager):
        logger.error("Failed to add safety category")
        return
    
    # Add safety information
    if not add_safety_info(db_manager):
        logger.error("Failed to add safety information")
        return
    
    logger.info("✅ Safety information added successfully to the database")
    
    # Test if the information was added correctly
    try:
        query = "SELECT * FROM practical_info WHERE category_id = 'safety'"
        result = db_manager.execute_query(query)
        if result:
            logger.info(f"Found {len(result)} safety information entries in the database")
        else:
            logger.warning("No safety information found in the database after adding")
    except Exception as e:
        logger.error(f"❌ Error testing safety information: {str(e)}")

if __name__ == "__main__":
    main()
