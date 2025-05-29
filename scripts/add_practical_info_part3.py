#!/usr/bin/env python3
"""
Script to add practical information to the database - Part 3.
Covers: drinking_water and photography_rules categories.
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
    # Drinking Water
    {
        "category_id": "drinking_water",
        "title": {
            "en": "Drinking Water Safety in Egypt",
            "ar": "سلامة مياه الشرب في مصر"
        },
        "content": {
            "en": """
# Drinking Water Safety in Egypt

Water safety is an important consideration for travelers to Egypt. This guide will help you make informed decisions about drinking water during your visit.

## Tap Water Safety

- **Local perspective**: Many Egyptians drink tap water, especially in major cities
- **Tourist recommendation**: Most health authorities advise tourists to avoid drinking tap water
- **Why**: While tap water is treated, it may contain different minerals than you're used to, which can cause stomach upset

## Safe Drinking Water Options

### Bottled Water
- **Availability**: Widely available throughout Egypt
- **Cost**: Very affordable (3-5 EGP for 1.5 liters)
- **Brands**: Nestlé Pure Life, Aquafina, Dasani, and local brands like Baraka and Siwa
- **Safety**: Choose sealed bottles from reputable sources

### Filtered Water
- **Hotels**: Many hotels provide filtered water dispensers
- **Restaurants**: Some restaurants offer filtered water
- **Portable filters**: Consider bringing a portable water filter or purification tablets

## Other Considerations

### Ice
- **In tourist establishments**: Usually made from filtered or bottled water
- **Elsewhere**: Exercise caution with ice in local establishments
- **Ask**: When in doubt, ask if ice is made from filtered water

### Hot Beverages
- **Tea and coffee**: Generally safe as the water is boiled
- **Egyptian tea (shai)**: A popular and safe beverage option

### Fruits and Vegetables
- **Cooked vegetables**: Safe to eat
- **Raw vegetables and fruits**: Wash with bottled or purified water, or choose fruits you can peel yourself

## Water for Brushing Teeth

- **Conservative approach**: Use bottled water for brushing teeth
- **Moderate approach**: Tap water is generally acceptable for brushing teeth in major cities and tourist areas

## Staying Hydrated

- **Climate**: Egypt's hot climate increases your water needs
- **Daily intake**: Aim for at least 2-3 liters of water daily, more when active or in summer
- **Dehydration signs**: Watch for headaches, fatigue, and dark urine

## Environmental Considerations

- **Plastic waste**: Consider bringing a reusable water bottle with a built-in filter
- **Refill stations**: Some eco-conscious hotels and restaurants offer water refill stations
- **Recycling**: Unfortunately, recycling infrastructure is limited in Egypt

## Water-Related Illnesses

- **Symptoms**: Nausea, vomiting, diarrhea, and stomach cramps
- **Treatment**: Over-the-counter medications for mild cases
- **Medical help**: Seek medical attention for severe or persistent symptoms
- **Prevention**: Stick to bottled or purified water and properly cooked foods

## Emergency Contacts

- **Tourist medical hotline**: 123
- **International SOS**: Available through travel insurance
- **Pharmacies**: Widely available and can provide basic medications
            """,
            "ar": """
# سلامة مياه الشرب في مصر

سلامة المياه اعتبار مهم للمسافرين إلى مصر. سيساعدك هذا الدليل على اتخاذ قرارات مستنيرة بشأن مياه الشرب خلال زيارتك.

## سلامة مياه الصنبور

- **المنظور المحلي**: يشرب العديد من المصريين مياه الصنبور، خاصة في المدن الكبرى
- **توصية للسياح**: تنصح معظم السلطات الصحية السياح بتجنب شرب مياه الصنبور
- **السبب**: على الرغم من معالجة مياه الصنبور، إلا أنها قد تحتوي على معادن مختلفة عما اعتدت عليه، مما قد يسبب اضطرابًا في المعدة

## خيارات مياه الشرب الآمنة

### المياه المعبأة
- **التوفر**: متوفرة على نطاق واسع في جميع أنحاء مصر
- **التكلفة**: بأسعار معقولة جدًا (3-5 جنيه مصري لـ 1.5 لتر)
- **العلامات التجارية**: نستله بيور لايف، أكوافينا، داساني، والعلامات التجارية المحلية مثل بركة وسيوة
- **السلامة**: اختر الزجاجات المختومة من مصادر موثوقة

### المياه المفلترة
- **الفنادق**: توفر العديد من الفنادق موزعات مياه مفلترة
- **المطاعم**: تقدم بعض المطاعم مياه مفلترة
- **المرشحات المحمولة**: فكر في إحضار مرشح مياه محمول أو أقراص تنقية

## اعتبارات أخرى

### الثلج
- **في المؤسسات السياحية**: عادة ما يصنع من مياه مفلترة أو معبأة
- **في أماكن أخرى**: توخ الحذر مع الثلج في المؤسسات المحلية
- **اسأل**: عند الشك، اسأل ما إذا كان الثلج مصنوعًا من مياه مفلترة

### المشروبات الساخنة
- **الشاي والقهوة**: آمنة عمومًا لأن الماء يغلى
- **الشاي المصري (شاي)**: خيار مشروب شائع وآمن

### الفواكه والخضروات
- **الخضروات المطبوخة**: آمنة للأكل
- **الخضروات والفواكه النيئة**: اغسلها بالمياه المعبأة أو المنقاة، أو اختر الفواكه التي يمكنك تقشيرها بنفسك

## المياه لتنظيف الأسنان

- **النهج المحافظ**: استخدم المياه المعبأة لتنظيف الأسنان
- **النهج المعتدل**: مياه الصنبور مقبولة عمومًا لتنظيف الأسنان في المدن الكبرى والمناطق السياحية

## البقاء رطبًا

- **المناخ**: مناخ مصر الحار يزيد من احتياجاتك للمياه
- **الاستهلاك اليومي**: اهدف إلى شرب 2-3 لترات من الماء يوميًا على الأقل، أكثر عند النشاط أو في الصيف
- **علامات الجفاف**: انتبه للصداع والتعب والبول الداكن

## الاعتبارات البيئية

- **النفايات البلاستيكية**: فكر في إحضار زجاجة مياه قابلة لإعادة الاستخدام مع مرشح مدمج
- **محطات إعادة التعبئة**: تقدم بعض الفنادق والمطاعم الواعية بيئيًا محطات إعادة تعبئة المياه
- **إعادة التدوير**: للأسف، البنية التحتية لإعادة التدوير محدودة في مصر

## الأمراض المتعلقة بالمياه

- **الأعراض**: الغثيان والقيء والإسهال وتشنجات المعدة
- **العلاج**: أدوية بدون وصفة طبية للحالات الخفيفة
- **المساعدة الطبية**: اطلب المساعدة الطبية للأعراض الشديدة أو المستمرة
- **الوقاية**: التزم بالمياه المعبأة أو المنقاة والأطعمة المطبوخة جيدًا

## أرقام الطوارئ

- **الخط الساخن الطبي للسياح**: 123
- **SOS الدولية**: متاحة من خلال تأمين السفر
- **الصيدليات**: متوفرة على نطاق واسع ويمكنها توفير الأدوية الأساسية
            """
        },
        "tags": ["water safety", "drinking water", "bottled water", "hydration", "health"]
    },
    
    # Photography Rules
    {
        "category_id": "photography_rules",
        "title": {
            "en": "Photography Guidelines in Egypt",
            "ar": "إرشادات التصوير في مصر"
        },
        "content": {
            "en": """
# Photography Guidelines in Egypt

Egypt offers incredible photographic opportunities, but there are important rules and cultural considerations to be aware of. This guide will help you capture memories while respecting local laws and customs.

## General Photography Rules

### Permitted Photography
- **Tourist attractions**: Most archaeological sites and museums allow photography
- **Public spaces**: Streets, markets, and public squares
- **Landscapes**: Desert scenes, the Nile, beaches, and natural areas
- **Your tour group**: Fellow travelers and your tour guide (with permission)

### Photography Requiring Permits
- **Commercial photography**: Professional shoots for advertising, films, or publications
- **Drone photography**: Strictly regulated and requires advance permits
- **Some museum interiors**: Special permits may be required for professional equipment

### Prohibited Photography
- **Military installations**: Strictly forbidden
- **Police checkpoints**: Never photograph security personnel or checkpoints
- **Government buildings**: Including embassies and official residences
- **Bridges**: Many bridges are considered strategic infrastructure
- **Airports**: Security areas and checkpoints
- **The Suez Canal**: Considered a strategic area

## Photography at Specific Locations

### Museums
- **Egyptian Museum (Cairo)**: Photography ticket required (50 EGP), no flash
- **Grand Egyptian Museum**: Check current policy as it may change
- **Special exhibits**: Some special exhibits prohibit photography
- **Mummy rooms**: Often prohibit photography or require an additional ticket

### Archaeological Sites
- **Pyramids exterior**: Freely permitted
- **Pyramid interiors**: Often prohibited or requires an additional ticket
- **Temples**: Generally allowed, but some interior chambers may restrict photography
- **Valley of the Kings**: Photography inside tombs requires a photo pass (300 EGP)
- **Abu Simbel**: Photography inside the temples requires a photo pass

### Religious Sites
- **Mosques**: Photography generally allowed outside prayer times
- **Churches**: Ask permission before photographing interiors or services
- **Active worship**: Never disrupt religious activities for photos

## Cultural Considerations

### Photographing People
- **Always ask permission**: Especially for close-up portraits
- **Children**: Always ask parents' permission before photographing children
- **Respect refusals**: Some people may decline for religious or personal reasons
- **Compensation expectations**: In tourist areas, some people may expect a small tip (5-10 EGP)

### Respectful Photography
- **Modest dress**: Dress respectfully when photographing religious sites
- **Appropriate timing**: Avoid photographing during prayer times
- **Sensitivity**: Be mindful of poverty or difficult living conditions

## Technical Tips

### Equipment Considerations
- **Dust protection**: Bring protective gear for desert locations
- **Heat protection**: Cameras can overheat in extreme temperatures
- **Security**: Keep equipment secure and consider insurance
- **Backup**: Regularly back up your photos

### Photography Passes
- **Where to buy**: Usually available at the ticket office of the site
- **Cost**: Varies by location (50-300 EGP)
- **Verification**: Staff may check your pass inside the site

## Legal Implications

- **Ignoring restrictions**: Can result in confiscation of equipment, deletion of photos, fines, or even detention
- **Security concerns**: Photography of sensitive areas may be considered a security threat
- **Respect official instructions**: Always comply with requests from security personnel or site officials

Remember that photography rules can change, so it's always best to verify current policies at each location you visit.
            """,
            "ar": """
# إرشادات التصوير في مصر

توفر مصر فرصًا رائعة للتصوير الفوتوغرافي، ولكن هناك قواعد واعتبارات ثقافية مهمة يجب أن تكون على دراية بها. سيساعدك هذا الدليل على التقاط الذكريات مع احترام القوانين والعادات المحلية.

## قواعد التصوير العامة

### التصوير المسموح به
- **المعالم السياحية**: تسمح معظم المواقع الأثرية والمتاحف بالتصوير
- **الأماكن العامة**: الشوارع والأسواق والميادين العامة
- **المناظر الطبيعية**: مشاهد الصحراء والنيل والشواطئ والمناطق الطبيعية
- **مجموعة الرحلة الخاصة بك**: زملاء المسافرين والمرشد السياحي (بإذن)

### التصوير الذي يتطلب تصاريح
- **التصوير التجاري**: التصوير الاحترافي للإعلانات أو الأفلام أو المنشورات
- **تصوير الدرون**: منظم بشكل صارم ويتطلب تصاريح مسبقة
- **بعض المتاحف الداخلية**: قد تكون هناك حاجة إلى تصاريح خاصة للمعدات المهنية

### التصوير المحظور
- **المنشآت العسكرية**: محظور بشدة
- **نقاط التفتيش الأمنية**: لا تقم أبدًا بتصوير أفراد الأمن أو نقاط التفتيش
- **المباني الحكومية**: بما في ذلك السفارات والمساكن الرسمية
- **الجسور**: تعتبر العديد من الجسور بنية تحتية استراتيجية
- **المطارات**: المناطق الأمنية ونقاط التفتيش
- **قناة السويس**: تعتبر منطقة استراتيجية

## التصوير في مواقع محددة

### المتاحف
- **المتحف المصري (القاهرة)**: تذكرة تصوير مطلوبة (50 جنيه مصري)، بدون فلاش
- **المتحف المصري الكبير**: تحقق من السياسة الحالية لأنها قد تتغير
- **المعارض الخاصة**: قد تحظر بعض المعارض الخاصة التصوير
- **غرف المومياوات**: غالبًا ما تحظر التصوير أو تتطلب تذكرة إضافية

### المواقع الأثرية
- **خارج الأهرامات**: مسموح به بحرية
- **داخل الأهرامات**: غالبًا ما يكون محظورًا أو يتطلب تذكرة إضافية
- **المعابد**: مسموح به عمومًا، ولكن قد تقيد بعض الغرف الداخلية التصوير
- **وادي الملوك**: يتطلب التصوير داخل المقابر تصريح تصوير (300 جنيه مصري)
- **أبو سمبل**: يتطلب التصوير داخل المعابد تصريح تصوير

### المواقع الدينية
- **المساجد**: يُسمح بالتصوير عمومًا خارج أوقات الصلاة
- **الكنائس**: اطلب الإذن قبل تصوير الداخل أو الخدمات
- **العبادة النشطة**: لا تعطل أبدًا الأنشطة الدينية للصور

## الاعتبارات الثقافية

### تصوير الناس
- **اطلب الإذن دائمًا**: خاصة للصور القريبة
- **الأطفال**: اطلب دائمًا إذن الوالدين قبل تصوير الأطفال
- **احترام الرفض**: قد يرفض بعض الناس لأسباب دينية أو شخصية
- **توقعات التعويض**: في المناطق السياحية، قد يتوقع بعض الناس بقشيشًا صغيرًا (5-10 جنيه مصري)

### التصوير المحترم
- **اللباس المحتشم**: ارتدِ ملابس محترمة عند تصوير المواقع الدينية
- **التوقيت المناسب**: تجنب التصوير خلال أوقات الصلاة
- **الحساسية**: كن مدركًا للفقر أو ظروف المعيشة الصعبة

## نصائح تقنية

### اعتبارات المعدات
- **حماية من الغبار**: أحضر معدات واقية للمواقع الصحراوية
- **حماية من الحرارة**: يمكن أن ترتفع درجة حرارة الكاميرات في درجات الحرارة القصوى
- **الأمان**: حافظ على أمان المعدات وفكر في التأمين
- **النسخ الاحتياطي**: قم بعمل نسخ احتياطية لصورك بانتظام

### تصاريح التصوير
- **أين تشتري**: متوفرة عادة في مكتب التذاكر بالموقع
- **التكلفة**: تختلف حسب الموقع (50-300 جنيه مصري)
- **التحقق**: قد يتحقق الموظفون من تصريحك داخل الموقع

## الآثار القانونية

- **تجاهل القيود**: يمكن أن يؤدي إلى مصادرة المعدات، وحذف الصور، والغرامات، أو حتى الاحتجاز
- **المخاوف الأمنية**: قد يعتبر تصوير المناطق الحساسة تهديدًا أمنيًا
- **احترام التعليمات الرسمية**: امتثل دائمًا لطلبات أفراد الأمن أو مسؤولي الموقع

تذكر أن قواعد التصوير يمكن أن تتغير، لذا من الأفضل دائمًا التحقق من السياسات الحالية في كل موقع تزوره.
            """
        },
        "tags": ["photography", "camera rules", "museums", "archaeological sites", "cultural sensitivity"]
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
    logger.info("Starting to add practical information (Part 3)...")
    
    # Connect to database
    conn = connect_to_db()
    
    # Add practical info
    added_count, skipped_count = add_practical_info(conn, PRACTICAL_INFO_TO_ADD)
    
    # Close connection
    conn.close()
    
    logger.info(f"Added {added_count} new practical info items, skipped {skipped_count} existing items.")

if __name__ == "__main__":
    main()
