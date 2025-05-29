#!/usr/bin/env python3
"""
Script to add tourism FAQs to the database.
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

# FAQs to add
FAQS_TO_ADD = [
    # Customs & Etiquette
    {
        "category_id": "customs_etiquette",
        "question": {
            "en": "What should I wear when visiting Egypt?",
            "ar": "ماذا يجب أن أرتدي عند زيارة مصر؟"
        },
        "answer": {
            "en": "Egypt is a conservative country, especially outside tourist areas. For both men and women, it's advisable to wear modest clothing that covers shoulders and knees. In religious sites, women should cover their hair and wear long sleeves and pants/long skirts. In tourist resorts like Sharm El Sheikh and Hurghada, regular beachwear is acceptable at hotel pools and beaches.",
            "ar": "مصر بلد محافظ، خاصة خارج المناطق السياحية. بالنسبة للرجال والنساء، يُنصح بارتداء ملابس محتشمة تغطي الكتفين والركبتين. في المواقع الدينية، يجب على النساء تغطية شعرهن وارتداء أكمام طويلة وسراويل/تنانير طويلة. في المنتجعات السياحية مثل شرم الشيخ والغردقة، يمكن ارتداء ملابس الشاطئ العادية عند حمامات السباحة والشواطئ الفندقية."
        },
        "tags": ["clothing", "dress code", "modesty", "cultural norms"]
    },
    {
        "category_id": "customs_etiquette",
        "question": {
            "en": "Is it customary to tip in Egypt?",
            "ar": "هل من المعتاد إعطاء البقشيش في مصر؟"
        },
        "answer": {
            "en": "Yes, tipping (known as 'baksheesh') is an important part of Egyptian culture. It's customary to tip service workers like waiters (10-15%), hotel staff (5-10 EGP), tour guides (10%), and drivers. Many Egyptians rely on tips as a significant part of their income.",
            "ar": "نعم، البقشيش (المعروف باسم 'بقشيش') جزء مهم من الثقافة المصرية. من المعتاد إعطاء البقشيش لعمال الخدمة مثل النادلين (10-15٪)، وموظفي الفندق (5-10 جنيه مصري)، والمرشدين السياحيين (10٪)، والسائقين. يعتمد العديد من المصريين على البقشيش كجزء كبير من دخلهم."
        },
        "tags": ["tipping", "baksheesh", "service", "money"]
    },
    
    # Transportation
    {
        "category_id": "transportation",
        "question": {
            "en": "What's the best way to get around Cairo?",
            "ar": "ما هي أفضل طريقة للتنقل في القاهرة؟"
        },
        "answer": {
            "en": "Cairo has several transportation options. The metro is efficient, affordable, and avoids traffic jams. Uber and Careem are reliable and safer than traditional taxis. For short distances, taxis are convenient but agree on a price before starting the journey. For a more authentic experience, try the local microbuses, but be aware they can be crowded and confusing for tourists.",
            "ar": "تتوفر في القاهرة عدة خيارات للنقل. المترو فعال وبأسعار معقولة ويتجنب الازدحام المروري. أوبر وكريم موثوقان وأكثر أمانًا من سيارات الأجرة التقليدية. للمسافات القصيرة، تعتبر سيارات الأجرة مريحة ولكن اتفق على السعر قبل بدء الرحلة. لتجربة أكثر أصالة، جرب الميكروباصات المحلية، ولكن كن على علم بأنها قد تكون مزدحمة ومربكة للسياح."
        },
        "tags": ["Cairo", "metro", "taxi", "Uber", "public transportation"]
    },
    {
        "category_id": "transportation",
        "question": {
            "en": "How do I travel between major cities in Egypt?",
            "ar": "كيف أسافر بين المدن الرئيسية في مصر؟"
        },
        "answer": {
            "en": "For long distances, domestic flights are the fastest option, with regular services between Cairo, Luxor, Aswan, and coastal cities. Trains are comfortable and affordable for journeys along the Nile Valley (Cairo-Luxor-Aswan). Buses are economical and connect most cities. For a unique experience, consider a Nile cruise between Luxor and Aswan. Private drivers can be hired for customized itineraries.",
            "ar": "للمسافات الطويلة، تعتبر الرحلات الجوية الداخلية الخيار الأسرع، مع خدمات منتظمة بين القاهرة والأقصر وأسوان والمدن الساحلية. القطارات مريحة وبأسعار معقولة للرحلات على طول وادي النيل (القاهرة-الأقصر-أسوان). الحافلات اقتصادية وتربط معظم المدن. لتجربة فريدة، يمكنك التفكير في رحلة نيلية بين الأقصر وأسوان. يمكن استئجار سائقين خاصين لجداول سفر مخصصة."
        },
        "tags": ["intercity travel", "flights", "trains", "buses", "Nile cruise"]
    },
    
    # Accommodation
    {
        "category_id": "accommodation",
        "question": {
            "en": "What types of accommodation are available in Egypt?",
            "ar": "ما هي أنواع الإقامة المتاحة في مصر؟"
        },
        "answer": {
            "en": "Egypt offers a wide range of accommodation options. Luxury international hotel chains are present in major cities and tourist destinations. Mid-range hotels and boutique properties provide good value. Budget travelers can find hostels in tourist areas. For a unique experience, consider Nile cruises with onboard accommodation, desert camps in the Western Desert, or traditional guesthouses in places like Siwa Oasis.",
            "ar": "تقدم مصر مجموعة واسعة من خيارات الإقامة. توجد سلاسل الفنادق الدولية الفاخرة في المدن الرئيسية والوجهات السياحية. توفر الفنادق متوسطة المستوى والفنادق البوتيكية قيمة جيدة. يمكن للمسافرين ذوي الميزانية المحدودة العثور على نزل في المناطق السياحية. لتجربة فريدة، يمكنك التفكير في رحلات نيلية مع إقامة على متن السفينة، أو مخيمات صحراوية في الصحراء الغربية، أو بيوت ضيافة تقليدية في أماكن مثل واحة سيوة."
        },
        "tags": ["hotels", "hostels", "Nile cruises", "desert camps", "guesthouses"]
    },
    
    # Food & Drink
    {
        "category_id": "food_drink",
        "question": {
            "en": "What are some must-try Egyptian dishes?",
            "ar": "ما هي بعض الأطباق المصرية التي يجب تجربتها؟"
        },
        "answer": {
            "en": "Egyptian cuisine offers many delicious dishes to try. Koshari is Egypt's national dish - a mix of rice, pasta, lentils, chickpeas, and fried onions with tomato sauce. Ful medames (stewed fava beans) and ta'ameya (Egyptian falafel) are popular breakfast items. Molokhia is a nutritious green soup often served with chicken. Stuffed pigeons (hamam mahshi) are a delicacy. For dessert, try konafa or basbousa, sweet pastries soaked in syrup.",
            "ar": "يقدم المطبخ المصري العديد من الأطباق اللذيذة للتجربة. الكشري هو الطبق الوطني لمصر - مزيج من الأرز والمعكرونة والعدس والحمص والبصل المقلي مع صلصة الطماطم. الفول المدمس والطعمية (الفلافل المصرية) من وجبات الإفطار الشائعة. الملوخية هي حساء أخضر مغذي يقدم غالبًا مع الدجاج. الحمام المحشي من الأطباق الشهية. للحلوى، جرب الكنافة أو البسبوسة، وهي معجنات حلوة مغموسة في الشراب."
        },
        "tags": ["koshari", "ful medames", "ta'ameya", "molokhia", "Egyptian cuisine"]
    },
    {
        "category_id": "food_drink",
        "question": {
            "en": "Is tap water safe to drink in Egypt?",
            "ar": "هل مياه الصنبور آمنة للشرب في مصر؟"
        },
        "answer": {
            "en": "It's recommended that tourists drink bottled water in Egypt. While tap water is treated and technically safe in most urban areas, it may contain different minerals than you're used to, which can cause stomach upset. Bottled water is widely available and inexpensive. Also avoid ice made from tap water and rinse fruits and vegetables with bottled or purified water.",
            "ar": "يُنصح السياح بشرب المياه المعبأة في مصر. على الرغم من أن مياه الصنبور معالجة وآمنة تقنيًا في معظم المناطق الحضرية، إلا أنها قد تحتوي على معادن مختلفة عما اعتدت عليه، مما قد يسبب اضطرابًا في المعدة. المياه المعبأة متوفرة على نطاق واسع وغير مكلفة. تجنب أيضًا الثلج المصنوع من مياه الصنبور واشطف الفواكه والخضروات بالمياه المعبأة أو المنقاة."
        },
        "tags": ["water safety", "bottled water", "hygiene", "health"]
    },
    
    # Shopping & Souvenirs
    {
        "category_id": "shopping_souvenirs",
        "question": {
            "en": "What are popular souvenirs to buy in Egypt?",
            "ar": "ما هي الهدايا التذكارية الشائعة للشراء في مصر؟"
        },
        "answer": {
            "en": "Egypt offers many unique souvenirs. Papyrus paintings are classic Egyptian souvenirs (but beware of fake papyrus made from banana leaves). Cartouches with your name in hieroglyphics make personalized gifts. Egyptian cotton products are known for their quality. Spices from local markets are aromatic and affordable. Other options include alabaster items, perfume oils, shisha pipes, and traditional jewelry like the Eye of Horus.",
            "ar": "تقدم مصر العديد من الهدايا التذكارية الفريدة. لوحات البردي هي هدايا تذكارية مصرية كلاسيكية (ولكن احذر من البردي المزيف المصنوع من أوراق الموز). الخراطيش التي تحمل اسمك بالهيروغليفية تصنع هدايا شخصية. منتجات القطن المصري معروفة بجودتها. التوابل من الأسواق المحلية عطرية وبأسعار معقولة. تشمل الخيارات الأخرى العناصر المصنوعة من الألباستر، وزيوت العطور، وأنابيب الشيشة، والمجوهرات التقليدية مثل عين حورس."
        },
        "tags": ["papyrus", "cartouche", "Egyptian cotton", "spices", "souvenirs"]
    },
    
    # Religion & Culture
    {
        "category_id": "religion_culture",
        "question": {
            "en": "What are the main religions in Egypt?",
            "ar": "ما هي الديانات الرئيسية في مصر؟"
        },
        "answer": {
            "en": "Islam is the predominant religion in Egypt, with about 90% of the population being Muslim, primarily Sunni. Christianity is the second largest religion, with Coptic Orthodox Christians making up about 10% of the population. The Coptic Church is one of the oldest Christian denominations in the world. There is also a small Jewish community, though it has diminished significantly over the past century.",
            "ar": "الإسلام هو الدين السائد في مصر، حيث يشكل المسلمون حوالي 90٪ من السكان، ومعظمهم من السنة. المسيحية هي ثاني أكبر ديانة، حيث يشكل المسيحيون الأقباط الأرثوذكس حوالي 10٪ من السكان. الكنيسة القبطية هي واحدة من أقدم الطوائف المسيحية في العالم. هناك أيضًا مجتمع يهودي صغير، على الرغم من أنه تضاءل بشكل كبير خلال القرن الماضي."
        },
        "tags": ["Islam", "Coptic Christianity", "religion", "culture"]
    },
    
    # Weather & Climate
    {
        "category_id": "weather_climate",
        "question": {
            "en": "When is the best time to visit Egypt?",
            "ar": "ما هو أفضل وقت لزيارة مصر؟"
        },
        "answer": {
            "en": "The best time to visit Egypt is during the cooler months from October to April. Winter (December-February) offers the most pleasant temperatures for sightseeing, especially in Upper Egypt (Luxor and Aswan), though Cairo and Alexandria can be chilly in the evenings. Spring (March-April) and autumn (October-November) offer a good balance of comfortable temperatures and fewer crowds. Summer (May-September) is extremely hot, particularly in Upper Egypt, but can offer lower prices and fewer tourists.",
            "ar": "أفضل وقت لزيارة مصر هو خلال الأشهر الأكثر برودة من أكتوبر إلى أبريل. يوفر الشتاء (ديسمبر-فبراير) درجات الحرارة الأكثر متعة لمشاهدة المعالم السياحية، خاصة في صعيد مصر (الأقصر وأسوان)، على الرغم من أن القاهرة والإسكندرية يمكن أن تكون باردة في المساء. يوفر الربيع (مارس-أبريل) والخريف (أكتوبر-نوفمبر) توازنًا جيدًا بين درجات الحرارة المريحة وعدد أقل من الحشود. الصيف (مايو-سبتمبر) حار للغاية، خاصة في صعيد مصر، ولكن يمكن أن يقدم أسعارًا أقل وعددًا أقل من السياح."
        },
        "tags": ["best time to visit", "seasons", "weather", "climate"]
    },
    
    # Communication
    {
        "category_id": "communication",
        "question": {
            "en": "What languages are spoken in Egypt?",
            "ar": "ما هي اللغات المتحدثة في مصر؟"
        },
        "answer": {
            "en": "Arabic is the official language of Egypt, specifically Egyptian Arabic dialect. English is widely spoken in tourist areas, hotels, and by educated Egyptians. French is also understood by some Egyptians, especially older generations and in the hospitality industry. In tourist areas, you'll find people who speak German, Italian, Russian, and Spanish as well. Learning a few basic Arabic phrases is appreciated by locals.",
            "ar": "العربية هي اللغة الرسمية في مصر، وتحديدًا اللهجة العربية المصرية. الإنجليزية منتشرة في المناطق السياحية والفنادق وبين المصريين المتعلمين. الفرنسية مفهومة أيضًا من قبل بعض المصريين، خاصة الأجيال الأكبر سنًا وفي صناعة الضيافة. في المناطق السياحية، ستجد أشخاصًا يتحدثون الألمانية والإيطالية والروسية والإسبانية أيضًا. تعلم بعض العبارات العربية الأساسية يقدره السكان المحليون."
        },
        "tags": ["Arabic", "English", "language", "communication"]
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

def add_faqs(conn, faqs):
    """Add FAQs to the database."""
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get existing FAQs to avoid duplicates
    cursor.execute("SELECT question->>'en' as question_en FROM tourism_faqs")
    existing_questions = [row['question_en'] for row in cursor.fetchall()]
    
    # Add FAQs
    added_count = 0
    skipped_count = 0
    
    for faq in faqs:
        # Check if FAQ already exists
        if faq['question']['en'] in existing_questions:
            logger.info(f"Skipping existing FAQ: {faq['question']['en']}")
            skipped_count += 1
            continue
        
        # Prepare data
        now = datetime.now()
        
        # Insert FAQ
        try:
            cursor.execute("""
                INSERT INTO tourism_faqs 
                (category_id, question, answer, tags, is_featured, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                faq['category_id'],
                json.dumps(faq['question']),
                json.dumps(faq['answer']),
                faq.get('tags', None),
                faq.get('is_featured', False),
                now,
                now
            ))
            
            faq_id = cursor.fetchone()['id']
            logger.info(f"Added FAQ ID {faq_id}: {faq['question']['en']}")
            added_count += 1
            
        except Exception as e:
            logger.error(f"Error adding FAQ {faq['question']['en']}: {e}")
    
    cursor.close()
    return added_count, skipped_count

def main():
    """Main function."""
    logger.info("Starting to add tourism FAQs...")
    
    # Connect to database
    conn = connect_to_db()
    
    # Add FAQs
    added_count, skipped_count = add_faqs(conn, FAQS_TO_ADD)
    
    # Close connection
    conn.close()
    
    logger.info(f"Added {added_count} new FAQs, skipped {skipped_count} existing FAQs.")

if __name__ == "__main__":
    main()
