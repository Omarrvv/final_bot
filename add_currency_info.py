#!/usr/bin/env python3
"""
Script to add currency information to the Egypt Tourism Chatbot database.
This script adds a currency category to the practical_info_categories table
and adds currency information to the practical_info table.
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

def add_currency_category(db_manager):
    """Add currency category to the practical_info_categories table."""
    try:
        # Check if category already exists
        if check_if_category_exists(db_manager, 'currency'):
            logger.info("Currency category already exists")
            return True
        
        # Add currency category
        query = """
        INSERT INTO practical_info_categories (
            id,
            name,
            description,
            icon,
            created_at,
            updated_at
        ) VALUES (
            'currency',
            %s,
            %s,
            'money-bill-wave',
            NOW(),
            NOW()
        )
        """
        
        name = json.dumps({
            "en": "Currency & Money",
            "ar": "العملة والمال"
        })
        
        description = json.dumps({
            "en": "Information about Egyptian currency, exchange rates, and money matters",
            "ar": "معلومات عن العملة المصرية وأسعار الصرف والأمور المالية"
        })
        
        db_manager.execute_query(query, (name, description))
        logger.info("✅ Currency category added successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Error adding currency category: {str(e)}")
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

def add_currency_info(db_manager):
    """Add currency information to the practical_info table."""
    try:
        # Check if info already exists
        if check_if_info_exists(db_manager, 'currency', 'Currency Information for Egypt'):
            logger.info("Currency information already exists")
            return True
        
        # Add currency information
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
            ARRAY['currency', 'money', 'Egyptian pound', 'exchange rates', 'banking', 'ATM', 'tipping'],
            true
        )
        """
        
        title = json.dumps({
            "en": "Currency Information for Egypt",
            "ar": "معلومات العملة في مصر"
        })
        
        content = json.dumps({
            "en": """# Currency Information for Egypt

The official currency of Egypt is the Egyptian Pound (EGP), often abbreviated as LE or E£.

## Egyptian Pound Basics
- **Symbol**: £E or ج.م
- **Code**: EGP
- **Denominations**: 
  - **Coins**: 25 pt, 50 pt, 1 LE
  - **Notes**: 5, 10, 20, 50, 100, 200 LE

## Currency Exchange
- **Best places to exchange**: Banks, official exchange offices, and some hotels
- **Airports**: Exchange services available but rates are typically less favorable
- **Documentation**: Bring your passport when exchanging currency
- **Receipts**: Keep exchange receipts if you plan to convert back to your currency when leaving

## ATMs and Banking
- **ATM availability**: Widely available in cities and tourist areas
- **Withdrawal limits**: Typically 2,000-3,000 LE per transaction
- **Bank cards**: Visa and Mastercard are widely accepted
- **Fees**: Check with your bank about foreign transaction fees
- **Banking hours**: Sunday to Thursday, 8:30 AM to 2:00 PM

## Credit Cards
- **Acceptance**: Major hotels, restaurants, and shops in tourist areas accept credit cards
- **Local markets**: Small shops and markets typically only accept cash
- **Notify your bank**: Inform your bank of your travel plans to prevent card blocks

## Tipping (Baksheesh)
- **Restaurants**: 10-15% if service charge is not included
- **Hotel staff**: 5-10 LE for porters, 10-20 LE per day for housekeeping
- **Tour guides**: 50-100 LE per day depending on group size
- **Taxi drivers**: Rounding up the fare is sufficient

## Money-Saving Tips
- **Compare rates**: Check multiple exchange offices for the best rates
- **Avoid street exchangers**: Stick to official establishments
- **Small denominations**: Keep small bills handy for taxis, tips, and small purchases
- **Bargaining**: Expected in markets and with taxis, but not in established stores

## Current Exchange Rates
*As of May 2025:*
- 1 USD ≈ 48 EGP
- 1 EUR ≈ 52 EGP
- 1 GBP ≈ 61 EGP

Exchange rates fluctuate, so check current rates before your trip.""",
            "ar": """# معلومات العملة في مصر

العملة الرسمية في مصر هي الجنيه المصري (EGP)، ويختصر غالبًا بـ LE أو E£.

## أساسيات الجنيه المصري
- **الرمز**: £E أو ج.م
- **الرمز الدولي**: EGP
- **الفئات**: 
  - **العملات المعدنية**: 25 قرش، 50 قرش، 1 جنيه
  - **الأوراق النقدية**: 5، 10، 20، 50، 100، 200 جنيه

## صرف العملات
- **أفضل الأماكن للصرف**: البنوك، مكاتب الصرافة الرسمية، وبعض الفنادق
- **المطارات**: خدمات الصرافة متوفرة ولكن الأسعار عادة أقل تفضيلاً
- **الوثائق**: أحضر جواز سفرك عند صرف العملات
- **الإيصالات**: احتفظ بإيصالات الصرف إذا كنت تخطط لتحويل الأموال مرة أخرى إلى عملتك عند المغادرة

## أجهزة الصراف الآلي والخدمات المصرفية
- **توفر أجهزة الصراف الآلي**: متوفرة على نطاق واسع في المدن والمناطق السياحية
- **حدود السحب**: عادة 2000-3000 جنيه مصري لكل معاملة
- **بطاقات البنوك**: فيزا وماستركارد مقبولة على نطاق واسع
- **الرسوم**: تحقق من بنكك بشأن رسوم المعاملات الأجنبية
- **ساعات عمل البنوك**: من الأحد إلى الخميس، 8:30 صباحًا إلى 2:00 مساءً

## بطاقات الائتمان
- **القبول**: الفنادق والمطاعم والمتاجر الكبرى في المناطق السياحية تقبل بطاقات الائتمان
- **الأسواق المحلية**: المتاجر الصغيرة والأسواق عادة تقبل النقد فقط
- **إخطار البنك**: أبلغ بنكك بخطط سفرك لمنع حظر البطاقة

## البقشيش (الإكرامية)
- **المطاعم**: 10-15% إذا لم تكن رسوم الخدمة مشمولة
- **موظفو الفندق**: 5-10 جنيه للحمالين، 10-20 جنيه يوميًا لخدمة الغرف
- **المرشدون السياحيون**: 50-100 جنيه يوميًا حسب حجم المجموعة
- **سائقو سيارات الأجرة**: تقريب المبلغ لأعلى يكفي

## نصائح لتوفير المال
- **قارن الأسعار**: تحقق من عدة مكاتب صرافة للحصول على أفضل الأسعار
- **تجنب الصرافين في الشوارع**: التزم بالمؤسسات الرسمية
- **الفئات الصغيرة**: احتفظ بالأوراق النقدية الصغيرة لسيارات الأجرة والبقشيش والمشتريات الصغيرة
- **المساومة**: متوقعة في الأسواق وسيارات الأجرة، ولكن ليس في المتاجر الثابتة

## أسعار الصرف الحالية
*اعتبارًا من مايو 2025:*
- 1 دولار أمريكي ≈ 48 جنيه مصري
- 1 يورو ≈ 52 جنيه مصري
- 1 جنيه إسترليني ≈ 61 جنيه مصري

تتقلب أسعار الصرف، لذا تحقق من الأسعار الحالية قبل رحلتك."""
        })
        
        db_manager.execute_query(query, (title, content))
        logger.info("✅ Currency information added successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Error adding currency information: {str(e)}")
        return False

def main():
    """Main function to add currency information to the database."""
    logger.info("Starting to add currency information to the database")
    
    # Connect to the database
    db_manager = connect_to_database()
    if not db_manager:
        logger.error("Cannot continue without database connection")
        return
    
    # Add currency category
    if not add_currency_category(db_manager):
        logger.error("Failed to add currency category")
        return
    
    # Add currency information
    if not add_currency_info(db_manager):
        logger.error("Failed to add currency information")
        return
    
    logger.info("✅ Currency information added successfully to the database")
    
    # Test if the information was added correctly
    try:
        query = "SELECT * FROM practical_info WHERE category_id = 'currency'"
        result = db_manager.execute_query(query)
        if result:
            logger.info(f"Found {len(result)} currency information entries in the database")
        else:
            logger.warning("No currency information found in the database after adding")
    except Exception as e:
        logger.error(f"❌ Error testing currency information: {str(e)}")

if __name__ == "__main__":
    main()
