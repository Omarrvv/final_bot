#!/usr/bin/env python3
"""
Generate tourism FAQs data for the Egypt Tourism Chatbot database.

This script:
1. Creates frequently asked questions about Egyptian tourism
2. Categorizes FAQs by topic
3. Links FAQs to relevant destinations
"""

import os
import sys
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

    # Extract existing FAQ IDs to avoid duplicates
    existing_faq_questions = []
    if 'faqs' in existing_data:
        existing_faq_questions = [faq.get('question', {}).get('en', '') for faq in existing_data['faqs']]

    # Prepare FAQs data
    faqs_data = []

    # Visa & Immigration FAQs
    visa_faqs = [
        {
            'question': {
                'en': 'Do I need a visa to visit Egypt?',
                'ar': 'هل أحتاج إلى تأشيرة لزيارة مصر؟'
            },
            'answer': {
                'en': 'Most visitors to Egypt need a visa. Citizens of many countries can obtain a visa on arrival at Egyptian airports for approximately $25 USD. E-visas are also available online through the official Egyptian e-visa portal. Some nationalities may need to apply for a visa in advance at an Egyptian embassy or consulate. It\'s recommended to check the specific requirements for your nationality before traveling.',
                'ar': 'يحتاج معظم الزوار إلى مصر إلى تأشيرة. يمكن لمواطني العديد من البلدان الحصول على تأشيرة عند الوصول في المطارات المصرية مقابل حوالي 25 دولارًا أمريكيًا. التأشيرات الإلكترونية متاحة أيضًا عبر الإنترنت من خلال بوابة التأشيرة الإلكترونية المصرية الرسمية. قد تحتاج بعض الجنسيات إلى التقدم بطلب للحصول على تأشيرة مسبقًا في سفارة أو قنصلية مصرية. يُنصح بالتحقق من المتطلبات المحددة لجنسيتك قبل السفر.'
            },
            'tags': ['visa', 'entry requirements', 'immigration', 'travel documents'],
            'is_featured': True,
            'related_destination_ids': ['egypt']
        },
        {
            'question': {
                'en': 'How long is the tourist visa valid for Egypt?',
                'ar': 'ما هي مدة صلاحية تأشيرة السياحة لمصر؟'
            },
            'answer': {
                'en': 'The standard tourist visa for Egypt is valid for 30 days from the date of entry. If you wish to stay longer, you can apply for an extension at the Mogamma building in Cairo or at immigration offices in other cities. Extensions are typically granted for an additional 30-90 days, depending on your circumstances.',
                'ar': 'تأشيرة السياحة القياسية لمصر صالحة لمدة 30 يومًا من تاريخ الدخول. إذا كنت ترغب في البقاء لفترة أطول، يمكنك التقدم بطلب للحصول على تمديد في مبنى المجمع في القاهرة أو في مكاتب الهجرة في المدن الأخرى. عادة ما يتم منح التمديدات لمدة 30-90 يومًا إضافية، اعتمادًا على ظروفك.'
            },
            'tags': ['visa', 'visa duration', 'visa extension', 'immigration'],
            'is_featured': False,
            'related_destination_ids': ['egypt']
        },
        {
            'question': {
                'en': 'What documents do I need to enter Egypt?',
                'ar': 'ما هي المستندات التي أحتاجها لدخول مصر؟'
            },
            'answer': {
                'en': 'To enter Egypt, you need: 1) A passport valid for at least 6 months beyond your arrival date, 2) A visa (obtained in advance, on arrival, or e-visa), 3) Proof of onward/return travel, 4) Proof of accommodation, and 5) Sufficient funds for your stay. Some visitors may also need to show a yellow fever vaccination certificate if arriving from affected countries.',
                'ar': 'لدخول مصر، تحتاج إلى: 1) جواز سفر صالح لمدة 6 أشهر على الأقل بعد تاريخ وصولك، 2) تأشيرة (تم الحصول عليها مسبقًا، عند الوصول، أو تأشيرة إلكترونية)، 3) إثبات السفر المستمر/العودة، 4) إثبات الإقامة، و 5) أموال كافية لإقامتك. قد يحتاج بعض الزوار أيضًا إلى إظهار شهادة تطعيم ضد الحمى الصفراء إذا كانوا قادمين من بلدان متأثرة.'
            },
            'tags': ['entry requirements', 'passport', 'travel documents', 'immigration'],
            'is_featured': False,
            'related_destination_ids': ['egypt']
        }
    ]

    # Health & Safety FAQs
    health_safety_faqs = [
        {
            'question': {
                'en': 'Is Egypt safe for tourists?',
                'ar': 'هل مصر آمنة للسياح؟'
            },
            'answer': {
                'en': 'Egypt is generally safe for tourists, especially in the main tourist areas. The Egyptian government places a high priority on tourist safety and there is visible security in popular destinations. As with any travel, it\'s advisable to take standard precautions: be aware of your surroundings, avoid isolated areas at night, keep valuables secure, and follow local advice. It\'s also recommended to check your government\'s travel advisories before your trip. Most tourists visit Egypt without any safety issues.',
                'ar': 'مصر آمنة بشكل عام للسياح، خاصة في المناطق السياحية الرئيسية. تضع الحكومة المصرية أولوية عالية لسلامة السياح وهناك أمن مرئي في الوجهات الشعبية. كما هو الحال مع أي سفر، من المستحسن اتخاذ احتياطات قياسية: كن على دراية بمحيطك، وتجنب المناطق المعزولة في الليل، واحتفظ بالأشياء الثمينة آمنة، واتبع النصائح المحلية. يُنصح أيضًا بالتحقق من النصائح السفرية لحكومتك قبل رحلتك. يزور معظم السياح مصر دون أي مشاكل تتعلق بالسلامة.'
            },
            'tags': ['safety', 'security', 'travel advice', 'tourist safety'],
            'is_featured': True,
            'related_destination_ids': ['egypt']
        },
        {
            'question': {
                'en': 'What vaccinations do I need for Egypt?',
                'ar': 'ما هي التطعيمات التي أحتاجها لمصر؟'
            },
            'answer': {
                'en': 'No mandatory vaccinations are required for entry to Egypt unless you\'re arriving from a country with yellow fever. However, healthcare professionals typically recommend being up-to-date on routine vaccines (MMR, diphtheria-tetanus-pertussis, varicella, polio, and flu). Some travelers may also consider hepatitis A, hepatitis B, and typhoid vaccinations. It\'s best to consult with a travel health specialist 4-8 weeks before your trip for personalized advice.',
                'ar': 'لا توجد تطعيمات إلزامية مطلوبة لدخول مصر ما لم تكن قادمًا من بلد به حمى صفراء. ومع ذلك، يوصي متخصصو الرعاية الصحية عادةً بتحديث اللقاحات الروتينية (الحصبة والنكاف والحصبة الألمانية، الدفتيريا والتيتانوس والسعال الديكي، الجديري، شلل الأطفال، والإنفلونزا). قد يفكر بعض المسافرين أيضًا في تطعيمات التهاب الكبد أ، التهاب الكبد ب، والتيفوئيد. من الأفضل استشارة أخصائي صحة السفر قبل 4-8 أسابيع من رحلتك للحصول على نصائح مخصصة.'
            },
            'tags': ['health', 'vaccinations', 'medical', 'travel health'],
            'is_featured': False,
            'related_destination_ids': ['egypt']
        },
        {
            'question': {
                'en': 'What should I do in case of a medical emergency in Egypt?',
                'ar': 'ماذا أفعل في حالة الطوارئ الطبية في مصر؟'
            },
            'answer': {
                'en': 'In case of a medical emergency in Egypt: 1) For immediate assistance, call 123 for an ambulance. 2) For less urgent care, major hotels can arrange for a doctor to visit you. 3) Private hospitals in major cities offer the best quality care (especially in Cairo and Alexandria). 4) Keep your travel insurance information and emergency contacts handy. 5) Contact your embassy or consulate if you need assistance. It\'s highly recommended to have comprehensive travel insurance that covers medical evacuation.',
                'ar': 'في حالة الطوارئ الطبية في مصر: 1) للمساعدة الفورية، اتصل بالرقم 123 للحصول على سيارة إسعاف. 2) للرعاية الأقل إلحاحًا، يمكن للفنادق الكبرى ترتيب زيارة طبيب لك. 3) توفر المستشفيات الخاصة في المدن الكبرى أفضل جودة للرعاية (خاصة في القاهرة والإسكندرية). 4) احتفظ بمعلومات تأمين السفر وجهات الاتصال في حالات الطوارئ في متناول اليد. 5) اتصل بسفارتك أو قنصليتك إذا كنت بحاجة إلى مساعدة. يوصى بشدة بالحصول على تأمين سفر شامل يغطي الإخلاء الطبي.'
            },
            'tags': ['health', 'emergency', 'medical care', 'hospitals'],
            'is_featured': False,
            'related_destination_ids': ['egypt', 'cairo', 'luxor', 'aswan']
        }
    ]

    # Money & Currency FAQs
    money_currency_faqs = [
        {
            'question': {
                'en': 'What is the currency in Egypt?',
                'ar': 'ما هي العملة في مصر؟'
            },
            'answer': {
                'en': 'The currency in Egypt is the Egyptian Pound (EGP), often abbreviated as LE or E£. Banknotes come in denominations of 1, 5, 10, 20, 50, 100, and 200 pounds. Coins are available in 25 piastres, 50 piastres, and 1 pound. While some tourist establishments may accept US dollars or euros, most transactions are conducted in Egyptian pounds. It\'s advisable to carry some local currency for small purchases, taxis, and markets.',
                'ar': 'العملة في مصر هي الجنيه المصري (EGP)، ويختصر غالبًا بـ LE أو E£. تأتي الأوراق النقدية بفئات 1 و5 و10 و20 و50 و100 و200 جنيه. العملات المعدنية متوفرة بفئات 25 قرشًا و50 قرشًا وجنيه واحد. بينما قد تقبل بعض المؤسسات السياحية الدولارات الأمريكية أو اليورو، إلا أن معظم المعاملات تتم بالجنيه المصري. من المستحسن حمل بعض العملة المحلية للمشتريات الصغيرة وسيارات الأجرة والأسواق.'
            },
            'tags': ['currency', 'money', 'egyptian pound', 'exchange'],
            'is_featured': True,
            'related_destination_ids': ['egypt']
        },
        {
            'question': {
                'en': 'Where can I exchange money in Egypt?',
                'ar': 'أين يمكنني تبديل الأموال في مصر؟'
            },
            'answer': {
                'en': 'You can exchange money in Egypt at banks, official exchange offices, major hotels, and some tourist shops. Banks generally offer the best rates but may have limited hours. ATMs are widely available in cities and tourist areas and often provide a convenient way to get Egyptian pounds directly. It\'s advisable to avoid exchanging money at unofficial exchange services or on the street. Keep your exchange receipts, as you may need them if you want to convert Egyptian pounds back to your currency when leaving.',
                'ar': 'يمكنك تبديل الأموال في مصر في البنوك ومكاتب الصرافة الرسمية والفنادق الكبرى وبعض المحلات السياحية. تقدم البنوك عمومًا أفضل الأسعار ولكن قد تكون ساعات العمل محدودة. أجهزة الصراف الآلي متوفرة على نطاق واسع في المدن والمناطق السياحية وغالبًا ما توفر طريقة مريحة للحصول على الجنيهات المصرية مباشرة. من المستحسن تجنب تبديل الأموال في خدمات الصرافة غير الرسمية أو في الشارع. احتفظ بإيصالات الصرف، فقد تحتاج إليها إذا كنت ترغب في تحويل الجنيهات المصرية مرة أخرى إلى عملتك عند المغادرة.'
            },
            'tags': ['currency exchange', 'money', 'banks', 'ATMs'],
            'is_featured': False,
            'related_destination_ids': ['egypt', 'cairo', 'luxor', 'aswan']
        },
        {
            'question': {
                'en': 'Is tipping expected in Egypt?',
                'ar': 'هل البقشيش متوقع في مصر؟'
            },
            'answer': {
                'en': 'Yes, tipping (known as "baksheesh") is an important part of Egyptian culture and economy. It\'s expected in many situations: 10-15% in restaurants (if service charge is not included), 5-10 Egyptian pounds for hotel porters per bag, 10-20% for tour guides, 5-10 pounds for housekeeping per day, and small amounts (1-5 pounds) for washroom attendants and other small services. Taxi drivers typically expect you to round up the fare. Having small denominations of Egyptian pounds ready for tipping is very useful.',
                'ar': 'نعم، البقشيش (المعروف باسم "بقشيش") هو جزء مهم من الثقافة والاقتصاد المصري. وهو متوقع في العديد من المواقف: 10-15٪ في المطاعم (إذا لم يتم تضمين رسوم الخدمة)، 5-10 جنيهات مصرية لحمالي الفنادق لكل حقيبة، 10-20٪ للمرشدين السياحيين، 5-10 جنيهات للتدبير المنزلي في اليوم، ومبالغ صغيرة (1-5 جنيهات) لمشرفي الحمامات والخدمات الصغيرة الأخرى. عادة ما يتوقع سائقو سيارات الأجرة منك تقريب الأجرة. إن وجود فئات صغيرة من الجنيهات المصرية جاهزة للبقشيش مفيد جدًا.'
            },
            'tags': ['tipping', 'baksheesh', 'money', 'local customs'],
            'is_featured': True,
            'related_destination_ids': ['egypt']
        }
    ]

    # Customs & Etiquette FAQs
    customs_etiquette_faqs = [
        {
            'question': {
                'en': 'What should I wear when visiting Egypt?',
                'ar': 'ماذا يجب أن أرتدي عند زيارة مصر؟'
            },
            'answer': {
                'en': 'Egypt is a conservative country, so modest dress is recommended, especially in non-tourist areas. For women: shoulders and knees should be covered; loose-fitting clothing like long skirts, pants, and sleeved tops are ideal. For men: shorts are acceptable in tourist areas, but long pants are better elsewhere. When visiting mosques, women should cover their hair, shoulders, and knees, and everyone should remove their shoes. In beach resorts like Sharm El Sheikh, regular swimwear is acceptable at hotel pools and beaches. During summer months (June-August), light, breathable fabrics are recommended due to the heat.',
                'ar': 'مصر بلد محافظ، لذا يُنصح بارتداء ملابس محتشمة، خاصة في المناطق غير السياحية. بالنسبة للنساء: يجب تغطية الكتفين والركبتين؛ الملابس الفضفاضة مثل التنانير الطويلة والسراويل والقمصان ذات الأكمام مثالية. بالنسبة للرجال: السراويل القصيرة مقبولة في المناطق السياحية، ولكن السراويل الطويلة أفضل في أماكن أخرى. عند زيارة المساجد، يجب على النساء تغطية شعرهن وكتفيهن وركبتيهن، ويجب على الجميع خلع أحذيتهم. في المنتجعات الشاطئية مثل شرم الشيخ، ملابس السباحة العادية مقبولة في حمامات السباحة والشواطئ الفندقية. خلال أشهر الصيف (يونيو-أغسطس)، يُنصح بالأقمشة الخفيفة والقابلة للتنفس بسبب الحرارة.'
            },
            'tags': ['dress code', 'clothing', 'cultural norms', 'modesty'],
            'is_featured': True,
            'related_destination_ids': ['egypt']
        },
        {
            'question': {
                'en': 'What are some important cultural customs to be aware of in Egypt?',
                'ar': 'ما هي بعض العادات الثقافية المهمة التي يجب أن أكون على دراية بها في مصر؟'
            },
            'answer': {
                'en': 'Important cultural customs in Egypt include: 1) Greetings are important - a handshake is common, though some may place their hand over their heart instead. 2) Use your right hand for eating, accepting items, or gesturing, as the left hand is considered unclean. 3) Public displays of affection should be minimal. 4) During Ramadan, avoid eating, drinking, or smoking in public during daylight hours. 5) Ask permission before photographing people. 6) Removing shoes before entering homes is customary. 7) Pointing the sole of your foot at someone is considered rude. 8) Egyptians value hospitality and may insist on offering food or drinks - accepting is polite.',
                'ar': 'تشمل العادات الثقافية المهمة في مصر: 1) التحيات مهمة - المصافحة شائعة، على الرغم من أن البعض قد يضع يده على قلبه بدلاً من ذلك. 2) استخدم يدك اليمنى للأكل أو قبول الأشياء أو الإشارة، حيث تعتبر اليد اليسرى غير نظيفة. 3) يجب أن تكون مظاهر المودة العامة في حدها الأدنى. 4) خلال شهر رمضان، تجنب الأكل أو الشرب أو التدخين في الأماكن العامة خلال ساعات النهار. 5) اطلب الإذن قبل تصوير الأشخاص. 6) خلع الأحذية قبل دخول المنازل أمر معتاد. 7) توجيه باطن قدمك نحو شخص ما يعتبر وقاحة. 8) يقدر المصريون الضيافة وقد يصرون على تقديم الطعام أو المشروبات - القبول مهذب.'
            },
            'tags': ['cultural norms', 'etiquette', 'customs', 'social behavior'],
            'is_featured': False,
            'related_destination_ids': ['egypt']
        },
        {
            'question': {
                'en': 'How should I behave during Ramadan in Egypt?',
                'ar': 'كيف يجب أن أتصرف خلال شهر رمضان في مصر؟'
            },
            'answer': {
                'en': 'During Ramadan in Egypt: 1) Avoid eating, drinking, or smoking in public during daylight hours out of respect for those fasting. 2) Many restaurants and cafes will be closed during the day, but tourist areas often have some venues open. 3) Dress more conservatively than usual. 4) Expect altered business hours, with many places opening later and closing during afternoon hours. 5) Traffic increases significantly before sunset as people rush home for iftar (breaking fast). 6) After sunset, the atmosphere becomes festive with special Ramadan foods and activities. 7) Be patient with service as many people are fasting. 8) It\'s a great time to experience Egyptian culture, especially evening festivities.',
                'ar': 'خلال شهر رمضان في مصر: 1) تجنب الأكل أو الشرب أو التدخين في الأماكن العامة خلال ساعات النهار احترامًا للصائمين. 2) ستكون العديد من المطاعم والمقاهي مغلقة خلال النهار، ولكن المناطق السياحية غالبًا ما يكون بها بعض الأماكن المفتوحة. 3) ارتدِ ملابس أكثر تحفظًا من المعتاد. 4) توقع ساعات عمل معدلة، مع فتح العديد من الأماكن في وقت لاحق وإغلاقها خلال ساعات بعد الظهر. 5) تزداد حركة المرور بشكل كبير قبل غروب الشمس حيث يسرع الناس إلى المنزل للإفطار. 6) بعد غروب الشمس، يصبح الجو احتفاليًا مع أطعمة وأنشطة رمضانية خاصة. 7) كن صبورًا مع الخدمة لأن الكثير من الناس صائمون. 8) إنه وقت رائع لتجربة الثقافة المصرية، خاصة الاحتفالات المسائية.'
            },
            'tags': ['ramadan', 'religious customs', 'fasting', 'cultural norms'],
            'is_featured': False,
            'related_destination_ids': ['egypt', 'cairo', 'luxor', 'aswan']
        }
    ]

    # Transportation FAQs
    transportation_faqs = [
        {
            'question': {
                'en': 'What is the best way to get around in Egypt?',
                'ar': 'ما هي أفضل طريقة للتنقل في مصر؟'
            },
            'answer': {
                'en': 'The best way to get around in Egypt depends on your destination and preferences. In cities like Cairo and Alexandria, taxis and ride-sharing apps (Uber, Careem) are convenient. For longer distances, domestic flights save time, while trains offer a comfortable and scenic option between major cities along the Nile. Buses connect most destinations and are economical. For Nile Valley destinations, Nile cruises combine transportation with sightseeing. In tourist areas, organized tours often include transportation. Renting a car is possible but challenging due to chaotic traffic, especially in Cairo. For short distances within cities, the metro in Cairo is efficient and inexpensive.',
                'ar': 'تعتمد أفضل طريقة للتنقل في مصر على وجهتك وتفضيلاتك. في مدن مثل القاهرة والإسكندرية، تعتبر سيارات الأجرة وتطبيقات مشاركة الركوب (أوبر، كريم) مريحة. للمسافات الطويلة، توفر الرحلات الجوية الداخلية الوقت، بينما توفر القطارات خيارًا مريحًا وخلابًا بين المدن الرئيسية على طول النيل. تربط الحافلات معظم الوجهات وهي اقتصادية. بالنسبة لوجهات وادي النيل، تجمع الرحلات النيلية بين النقل ومشاهدة المعالم السياحية. في المناطق السياحية، غالبًا ما تشمل الجولات المنظمة وسائل النقل. استئجار سيارة ممكن ولكنه صعب بسبب حركة المرور الفوضوية، خاصة في القاهرة. للمسافات القصيرة داخل المدن، يعتبر مترو الأنفاق في القاهرة فعالًا وغير مكلف.'
            },
            'tags': ['transportation', 'travel', 'getting around', 'public transport'],
            'is_featured': True,
            'related_destination_ids': ['egypt', 'cairo', 'luxor', 'aswan']
        },
        {
            'question': {
                'en': 'Is it safe to use taxis in Egypt?',
                'ar': 'هل من الآمن استخدام سيارات الأجرة في مصر؟'
            },
            'answer': {
                'en': 'Using taxis in Egypt is generally safe, but it\'s important to take precautions. White taxis in major cities are metered, but always confirm the meter is running or negotiate a fare before starting your journey. Ride-hailing apps like Uber and Careem are widely available in major cities and often preferred by tourists as they provide fixed pricing and tracked journeys. Hotel taxis are more expensive but reliable. Avoid unmarked or unofficial taxis. It\'s helpful to have your destination written in Arabic, know the approximate fare, and have small bills for payment. Female travelers might prefer ride-sharing apps or hotel taxis, especially at night.',
                'ar': 'استخدام سيارات الأجرة في مصر آمن بشكل عام، ولكن من المهم اتخاذ الاحتياطات. سيارات الأجرة البيضاء في المدن الكبرى مزودة بعدادات، ولكن تأكد دائمًا من تشغيل العداد أو تفاوض على الأجرة قبل بدء رحلتك. تطبيقات طلب الركوب مثل أوبر وكريم متوفرة على نطاق واسع في المدن الكبرى ويفضلها السياح غالبًا لأنها توفر أسعارًا ثابتة ورحلات متتبعة. سيارات أجرة الفنادق أكثر تكلفة ولكنها موثوقة. تجنب سيارات الأجرة غير المميزة أو غير الرسمية. من المفيد أن يكون لديك وجهتك مكتوبة باللغة العربية، ومعرفة الأجرة التقريبية، ووجود أوراق نقدية صغيرة للدفع. قد تفضل المسافرات تطبيقات مشاركة الركوب أو سيارات أجرة الفنادق، خاصة في الليل.'
            },
            'tags': ['taxis', 'transportation', 'safety', 'uber'],
            'is_featured': False,
            'related_destination_ids': ['egypt', 'cairo', 'alexandria']
        },
        {
            'question': {
                'en': 'How do I travel between Cairo and Luxor?',
                'ar': 'كيف أسافر بين القاهرة والأقصر؟'
            },
            'answer': {
                'en': 'To travel between Cairo and Luxor (approximately 670 km), you have several options: 1) Flights: The fastest option (1 hour) with multiple daily flights by EgyptAir and other carriers. 2) Overnight trains: Comfortable sleeper trains run daily (10-12 hours), offering private cabins with beds. 3) Day trains: More economical but basic (9-10 hours). 4) Buses: Several companies operate buses between the cities (9-10 hours). 5) Nile cruises: A leisurely option that includes stops at attractions along the way (typically 3-4 days). 6) Private transfers: Expensive but convenient, especially for groups. Flights and sleeper trains are the most popular options for tourists due to comfort and time efficiency.',
                'ar': 'للسفر بين القاهرة والأقصر (حوالي 670 كم)، لديك عدة خيارات: 1) الرحلات الجوية: الخيار الأسرع (ساعة واحدة) مع رحلات يومية متعددة بواسطة مصر للطيران وشركات أخرى. 2) قطارات الليل: قطارات نوم مريحة تعمل يوميًا (10-12 ساعة)، وتوفر مقصورات خاصة مع أسرّة. 3) قطارات النهار: أكثر اقتصادية ولكنها أساسية (9-10 ساعات). 4) الحافلات: تعمل العديد من الشركات حافلات بين المدن (9-10 ساعات). 5) الرحلات النيلية: خيار مريح يتضمن توقفات عند المعالم السياحية على طول الطريق (عادة 3-4 أيام). 6) النقل الخاص: مكلف ولكنه مريح، خاصة للمجموعات. الرحلات الجوية وقطارات النوم هي الخيارات الأكثر شعبية للسياح بسبب الراحة وكفاءة الوقت.'
            },
            'tags': ['transportation', 'cairo to luxor', 'trains', 'flights', 'nile cruise'],
            'is_featured': True,
            'related_destination_ids': ['egypt', 'cairo', 'luxor']
        }
    ]

    # Accommodation FAQs
    accommodation_faqs = [
        {
            'question': {
                'en': 'What types of accommodation are available in Egypt?',
                'ar': 'ما هي أنواع الإقامة المتاحة في مصر؟'
            },
            'answer': {
                'en': 'Egypt offers a wide range of accommodation options: 1) Luxury hotels and resorts, particularly in Cairo, Luxor, Aswan, and Red Sea destinations like Sharm El Sheikh and Hurghada. 2) Mid-range hotels that balance comfort and affordability. 3) Budget hotels and hostels in major cities and tourist areas. 4) Nile cruise ships that combine accommodation with transportation between Luxor and Aswan. 5) Boutique hotels, often in historic buildings in Cairo and Alexandria. 6) Eco-lodges in the Western Desert oases and Sinai. 7) Apartment rentals through platforms like Airbnb, popular in cities. 8) Traditional guesthouses (especially in rural areas and oases). International hotel chains are well-represented in tourist destinations, while locally-owned options often provide more authentic experiences.',
                'ar': 'تقدم مصر مجموعة واسعة من خيارات الإقامة: 1) الفنادق والمنتجعات الفاخرة، خاصة في القاهرة والأقصر وأسوان ووجهات البحر الأحمر مثل شرم الشيخ والغردقة. 2) الفنادق متوسطة المستوى التي توازن بين الراحة والقدرة على تحمل التكاليف. 3) الفنادق الاقتصادية والنزل في المدن الرئيسية والمناطق السياحية. 4) سفن الرحلات النيلية التي تجمع بين الإقامة والنقل بين الأقصر وأسوان. 5) الفنادق البوتيكية، غالبًا في المباني التاريخية في القاهرة والإسكندرية. 6) النزل البيئية في واحات الصحراء الغربية وسيناء. 7) تأجير الشقق من خلال منصات مثل Airbnb، وهي شائعة في المدن. 8) بيوت الضيافة التقليدية (خاصة في المناطق الريفية والواحات). سلاسل الفنادق الدولية ممثلة جيدًا في الوجهات السياحية، بينما توفر الخيارات المملوكة محليًا تجارب أكثر أصالة.'
            },
            'tags': ['accommodation', 'hotels', 'hostels', 'nile cruise', 'resorts'],
            'is_featured': True,
            'related_destination_ids': ['egypt', 'cairo', 'luxor', 'aswan']
        },
        {
            'question': {
                'en': 'When should I book accommodation in Egypt?',
                'ar': 'متى يجب أن أحجز الإقامة في مصر؟'
            },
            'answer': {
                'en': 'The best time to book accommodation in Egypt depends on when you\'re visiting: 1) For peak tourist season (October to April), book 2-3 months in advance, especially for luxury hotels and Nile cruises. 2) For Christmas, New Year, and Easter holidays, book 4-6 months ahead as these are extremely busy periods. 3) For summer months (May to September), booking 2-4 weeks ahead is usually sufficient except for beach resorts, which can still be busy with domestic and regional tourists. 4) For budget accommodations in major cities, 1-2 weeks notice is often enough during non-peak times. 5) If visiting during major Egyptian holidays or international conferences, book well in advance. Using booking platforms with free cancellation options gives you flexibility while securing your preferred options.',
                'ar': 'يعتمد أفضل وقت لحجز الإقامة في مصر على وقت زيارتك: 1) لموسم الذروة السياحية (أكتوبر إلى أبريل)، احجز قبل 2-3 أشهر، خاصة للفنادق الفاخرة والرحلات النيلية. 2) لعطلات عيد الميلاد ورأس السنة الجديدة وعيد الفصح، احجز قبل 4-6 أشهر لأن هذه فترات مزدحمة للغاية. 3) لأشهر الصيف (مايو إلى سبتمبر)، عادة ما يكون الحجز قبل 2-4 أسابيع كافيًا باستثناء المنتجعات الشاطئية، التي قد تظل مزدحمة بالسياح المحليين والإقليميين. 4) للإقامة الاقتصادية في المدن الكبرى، غالبًا ما يكون إشعار 1-2 أسبوع كافيًا خلال الأوقات غير الذروة. 5) إذا كنت تزور خلال الأعياد المصرية الرئيسية أو المؤتمرات الدولية، احجز مسبقًا بوقت كافٍ. استخدام منصات الحجز مع خيارات الإلغاء المجاني يمنحك المرونة مع تأمين خياراتك المفضلة.'
            },
            'tags': ['booking', 'accommodation', 'hotels', 'planning', 'peak season'],
            'is_featured': False,
            'related_destination_ids': ['egypt']
        },
        {
            'question': {
                'en': 'What is a Nile cruise and is it worth it?',
                'ar': 'ما هي الرحلة النيلية وهل تستحق؟'
            },
            'answer': {
                'en': 'A Nile cruise is a multi-day journey on a floating hotel that travels between Luxor and Aswan (or vice versa), typically lasting 3-7 nights. These cruises combine transportation, accommodation, meals, and guided tours to major attractions along the Nile Valley. They\'re worth it for several reasons: 1) They provide a unique perspective of ancient Egypt from the river that was its lifeblood. 2) They\'re convenient, as you unpack once while visiting multiple sites. 3) They include guided excursions to temples and tombs that might be difficult to arrange independently. 4) They offer a relaxing way to travel between destinations. 5) Higher-end cruises feature swimming pools, entertainment, and luxurious amenities. The best time for a Nile cruise is between October and April when temperatures are pleasant. Prices vary widely based on the boat\'s luxury level, from budget to ultra-luxury options.',
                'ar': 'الرحلة النيلية هي رحلة متعددة الأيام على فندق عائم يسافر بين الأقصر وأسوان (أو العكس)، وتستمر عادة 3-7 ليالٍ. تجمع هذه الرحلات بين النقل والإقامة والوجبات والجولات المصحوبة بمرشدين إلى المعالم الرئيسية على طول وادي النيل. إنها تستحق لعدة أسباب: 1) توفر منظورًا فريدًا لمصر القديمة من النهر الذي كان شريان حياتها. 2) إنها مريحة، حيث تفرغ أمتعتك مرة واحدة أثناء زيارة مواقع متعددة. 3) تشمل رحلات بمرافقة مرشدين إلى المعابد والمقابر التي قد يكون من الصعب ترتيبها بشكل مستقل. 4) توفر طريقة مريحة للسفر بين الوجهات. 5) تتميز الرحلات الأكثر فخامة بحمامات سباحة وترفيه ووسائل راحة فاخرة. أفضل وقت للرحلة النيلية هو بين أكتوبر وأبريل عندما تكون درجات الحرارة لطيفة. تختلف الأسعار على نطاق واسع بناءً على مستوى فخامة القارب، من الخيارات الاقتصادية إلى الفائقة الفخامة.'
            },
            'tags': ['nile cruise', 'accommodation', 'luxor', 'aswan', 'sightseeing'],
            'is_featured': True,
            'related_destination_ids': ['egypt', 'luxor', 'aswan']
        }
    ]

    # Food & Drink FAQs
    food_drink_faqs = [
        {
            'question': {
                'en': 'What are the must-try Egyptian dishes?',
                'ar': 'ما هي الأطباق المصرية التي يجب تجربتها؟'
            },
            'answer': {
                'en': 'Must-try Egyptian dishes include: 1) Koshari - Egypt\'s national dish of rice, lentils, pasta, and chickpeas topped with tomato sauce and fried onions. 2) Ful Medames - mashed fava beans with olive oil, lemon juice, and spices, often eaten for breakfast. 3) Ta\'ameya (Egyptian falafel) - made with fava beans rather than chickpeas. 4) Molokhia - a green soup made from jute leaves, typically served with chicken or rabbit and rice. 5) Mahshi - vegetables like bell peppers, zucchini, or grape leaves stuffed with rice and herbs. 6) Hawawshi - spiced minced meat in bread. 7) Shawarma - thinly sliced marinated meat in bread. 8) Feteer - layered pastry that can be sweet or savory. 9) Om Ali - a sweet bread pudding with nuts and raisins. 10) Kofta and Kebab - grilled spiced meat dishes. These dishes are available at restaurants ranging from street food stalls to upscale establishments.',
                'ar': 'تشمل الأطباق المصرية التي يجب تجربتها: 1) الكشري - الطبق الوطني المصري من الأرز والعدس والمعكرونة والحمص مغطى بصلصة الطماطم والبصل المقلي. 2) الفول المدمس - فول مهروس مع زيت الزيتون وعصير الليمون والتوابل، غالبًا ما يؤكل للإفطار. 3) الطعمية (الفلافل المصرية) - مصنوعة من الفول بدلاً من الحمص. 4) الملوخية - حساء أخضر مصنوع من أوراق الملوخية، عادة ما يقدم مع الدجاج أو الأرانب والأرز. 5) المحشي - خضروات مثل الفلفل والكوسة أو ورق العنب محشوة بالأرز والأعشاب. 6) الحواوشي - لحم مفروم متبل في الخبز. 7) الشاورما - شرائح رقيقة من اللحم المتبل في الخبز. 8) الفطير - معجنات طبقية يمكن أن تكون حلوة أو مالحة. 9) أم علي - حلوى بودنج الخبز مع المكسرات والزبيب. 10) الكفتة والكباب - أطباق اللحوم المشوية المتبلة. هذه الأطباق متوفرة في المطاعم بدءًا من أكشاك الطعام في الشوارع وحتى المؤسسات الراقية.'
            },
            'tags': ['food', 'egyptian cuisine', 'traditional dishes', 'local food'],
            'is_featured': True,
            'related_destination_ids': ['egypt']
        },
        {
            'question': {
                'en': 'Is it safe to drink tap water in Egypt?',
                'ar': 'هل من الآمن شرب ماء الصنبور في مصر؟'
            },
            'answer': {
                'en': 'It is not recommended to drink tap water in Egypt. While the water is treated and technically safe in some areas, the pipes and storage systems can be problematic, and the mineral content is different from what many visitors are accustomed to. Instead: 1) Drink bottled water, which is widely available and inexpensive. 2) Check that bottle seals are intact when purchasing. 3) Use bottled water for brushing teeth as well. 4) Ice in established restaurants and hotels is generally made with filtered water and is safe. 5) Hot beverages like tea and coffee are safe as the water is boiled. 6) Be cautious with fresh juices from street vendors, as they may be mixed with tap water. Most hotels provide complimentary bottled water, and many restaurants serve bottled water by default.',
                'ar': 'لا يُنصح بشرب ماء الصنبور في مصر. على الرغم من أن المياه معالجة وآمنة تقنيًا في بعض المناطق، إلا أن الأنابيب وأنظمة التخزين يمكن أن تكون إشكالية، ومحتوى المعادن مختلف عما اعتاد عليه العديد من الزوار. بدلاً من ذلك: 1) اشرب المياه المعبأة، وهي متوفرة على نطاق واسع وغير مكلفة. 2) تحقق من أن أختام الزجاجة سليمة عند الشراء. 3) استخدم المياه المعبأة لتنظيف الأسنان أيضًا. 4) الثلج في المطاعم والفنادق المعروفة يصنع عادة بمياه مفلترة وهو آمن. 5) المشروبات الساخنة مثل الشاي والقهوة آمنة لأن الماء مغلي. 6) كن حذرًا مع العصائر الطازجة من الباعة المتجولين، لأنها قد تكون مخلوطة بماء الصنبور. توفر معظم الفنادق مياه معبأة مجانية، وتقدم العديد من المطاعم مياه معبأة بشكل افتراضي.'
            },
            'tags': ['water', 'health', 'food safety', 'drinking water'],
            'is_featured': True,
            'related_destination_ids': ['egypt']
        },
        {
            'question': {
                'en': 'What are some traditional Egyptian drinks?',
                'ar': 'ما هي بعض المشروبات المصرية التقليدية؟'
            },
            'answer': {
                'en': 'Traditional Egyptian drinks include: 1) Karkade (Hibiscus tea) - a deep red, tangy tea served hot or cold. 2) Shai (Egyptian tea) - strong black tea often served with mint and lots of sugar. 3) Sahlab - a thick, sweet winter drink made from orchid root powder, milk, and topped with nuts and cinnamon. 4) Sugarcane juice (Aseer Asab) - freshly pressed and very sweet. 5) Tamarind juice (Tamr Hindi) - sweet and tangy, often served during Ramadan. 6) Licorice juice (Erk Soos) - a distinctive black drink with a unique flavor. 7) Fenugreek tea (Helba) - known for health benefits. 8) Doum palm juice - made from the fruit of the doum palm. 9) Lemon juice with mint (Lemonade baladi) - a refreshing citrus drink. 10) Turkish coffee (Ahwa) - strong coffee often flavored with cardamom. Alcoholic beverages are available primarily in tourist areas, hotels, and some restaurants, with local beers like Stella and Sakara being popular choices.',
                'ar': 'تشمل المشروبات المصرية التقليدية: 1) الكركديه (شاي الكركديه) - شاي أحمر داكن حامض يقدم ساخنًا أو باردًا. 2) الشاي (الشاي المصري) - شاي أسود قوي غالبًا ما يقدم مع النعناع والكثير من السكر. 3) السحلب - مشروب شتوي سميك وحلو مصنوع من مسحوق جذر السحلب والحليب ومغطى بالمكسرات والقرفة. 4) عصير قصب السكر (عصير قصب) - معصور طازج وحلو جدًا. 5) عصير التمر هندي - حلو وحامض، غالبًا ما يقدم خلال شهر رمضان. 6) عرق سوس - مشروب أسود مميز بنكهة فريدة. 7) شاي الحلبة - معروف بفوائده الصحية. 8) عصير الدوم - مصنوع من ثمرة نخيل الدوم. 9) عصير الليمون بالنعناع (ليموناضة بلدي) - مشروب حمضيات منعش. 10) القهوة التركية (قهوة) - قهوة قوية غالبًا ما تكون منكهة بالهيل. المشروبات الكحولية متوفرة بشكل أساسي في المناطق السياحية والفنادق وبعض المطاعم، مع البيرة المحلية مثل ستيلا وسقارة كخيارات شائعة.'
            },
            'tags': ['drinks', 'beverages', 'traditional drinks', 'egyptian cuisine'],
            'is_featured': False,
            'related_destination_ids': ['egypt']
        }
    ]

    # Shopping & Souvenirs FAQs
    shopping_faqs = [
        {
            'question': {
                'en': 'What are the best souvenirs to buy in Egypt?',
                'ar': 'ما هي أفضل الهدايا التذكارية للشراء في مصر؟'
            },
            'answer': {
                'en': 'Popular souvenirs from Egypt include: 1) Papyrus paintings - look for authentic papyrus, not banana paper. 2) Egyptian cotton products - Egypt is famous for its high-quality cotton. 3) Spices from local markets - especially saffron, hibiscus, and dukkah. 4) Alabaster items - traditional Egyptian crafts often depicting ancient symbols. 5) Cartouches - personalized name pendants in hieroglyphics. 6) Perfume oils (essence) - Egypt has a long tradition of perfumery. 7) Shisha pipes - decorative water pipes in various sizes. 8) Inlaid wooden boxes - beautiful mother-of-pearl designs. 9) Scarab beetles - ancient Egyptian symbol of rebirth. 10) Galabiya - traditional Egyptian garments. For the best quality and authentic items, shop at government-certified shops, museum gift shops, or reputable markets rather than tourist stalls.',
                'ar': 'تشمل الهدايا التذكارية الشعبية من مصر: 1) لوحات البردي - ابحث عن البردي الأصلي، وليس ورق الموز. 2) منتجات القطن المصري - مصر مشهورة بقطنها عالي الجودة. 3) التوابل من الأسواق المحلية - خاصة الزعفران والكركديه والدقة. 4) العناصر المصنوعة من الألباستر - الحرف المصرية التقليدية التي غالبًا ما تصور الرموز القديمة. 5) الخراطيش - قلادات أسماء مخصصة بالهيروغليفية. 6) زيوت العطور (الجوهر) - لدى مصر تقليد طويل في صناعة العطور. 7) الشيشة - أنابيب المياه الزخرفية بأحجام مختلفة. 8) الصناديق الخشبية المطعمة - تصاميم جميلة من الصدف. 9) خنافس الجعران - رمز مصري قديم للولادة الجديدة. 10) الجلابية - الملابس المصرية التقليدية. للحصول على أفضل جودة وعناصر أصلية، تسوق من المحلات المعتمدة من الحكومة أو متاجر الهدايا في المتاحف أو الأسواق ذات السمعة الطيبة بدلاً من أكشاك السياح.'
            },
            'tags': ['shopping', 'souvenirs', 'gifts', 'handicrafts'],
            'is_featured': True,
            'related_destination_ids': ['egypt', 'cairo', 'luxor']
        }
    ]

    # Religion & Culture FAQs
    religion_culture_faqs = [
        {
            'question': {
                'en': 'What are the main religions in Egypt?',
                'ar': 'ما هي الديانات الرئيسية في مصر؟'
            },
            'answer': {
                'en': 'Islam is the predominant religion in Egypt, with approximately 90% of the population identifying as Muslim, primarily Sunni. Christianity is the second largest religion, representing about 10% of Egyptians, with the Coptic Orthodox Church being the largest Christian denomination. There is also a small community of other Christian denominations, including Greek Orthodox, Catholic, and Protestant. Egypt has a very small Jewish community today, though historically it was much larger. Religion plays a significant role in Egyptian society and daily life, with religious holidays and traditions being widely observed. The Egyptian constitution recognizes Islam as the state religion while guaranteeing freedom of belief and religious practice.',
                'ar': 'الإسلام هو الدين السائد في مصر، حيث يعرّف حوالي 90٪ من السكان أنفسهم كمسلمين، في الغالب من السنة. المسيحية هي ثاني أكبر ديانة، تمثل حوالي 10٪ من المصريين، مع كون الكنيسة القبطية الأرثوذكسية أكبر طائفة مسيحية. هناك أيضًا مجتمع صغير من الطوائف المسيحية الأخرى، بما في ذلك الأرثوذكس اليونانيين والكاثوليك والبروتستانت. لدى مصر مجتمع يهودي صغير جدًا اليوم، على الرغم من أنه كان أكبر بكثير تاريخيًا. يلعب الدين دورًا مهمًا في المجتمع المصري والحياة اليومية، حيث يتم الاحتفال بالأعياد والتقاليد الدينية على نطاق واسع. يعترف الدستور المصري بالإسلام كدين للدولة مع ضمان حرية المعتقد وممارسة الشعائر الدينية.'
            },
            'tags': ['religion', 'islam', 'christianity', 'coptic', 'culture'],
            'is_featured': False,
            'related_destination_ids': ['egypt']
        }
    ]

    # Weather & Climate FAQs
    weather_climate_faqs = [
        {
            'question': {
                'en': 'What is the best time of year to visit Egypt?',
                'ar': 'ما هو أفضل وقت من السنة لزيارة مصر؟'
            },
            'answer': {
                'en': 'The best time to visit Egypt is during the cooler months from October to April. Within this period, November to February offers the most pleasant temperatures for sightseeing, especially in Upper Egypt (Luxor and Aswan) where summer temperatures can be extreme. December and January are peak tourist season, so expect more crowds and higher prices. Spring (March-April) and autumn (September-October) are good shoulder seasons with fewer tourists and still-comfortable temperatures. Summer (May to August) is extremely hot, particularly in Upper Egypt where temperatures can exceed 40°C (104°F), but this is when you'll find the lowest prices and fewest tourists. The Red Sea coast remains relatively pleasant year-round and is a good summer alternative. If visiting during Ramadan, be aware that some businesses may have reduced hours, though tourist sites remain open.',
                'ar': 'أفضل وقت لزيارة مصر هو خلال الأشهر الأكثر برودة من أكتوبر إلى أبريل. خلال هذه الفترة، توفر الأشهر من نوفمبر إلى فبراير درجات حرارة أكثر متعة لمشاهدة المعالم السياحية، خاصة في صعيد مصر (الأقصر وأسوان) حيث يمكن أن تكون درجات الحرارة الصيفية قاسية. ديسمبر ويناير هما ذروة موسم السياحة، لذا توقع المزيد من الحشود وارتفاع الأسعار. الربيع (مارس-أبريل) والخريف (سبتمبر-أكتوبر) هما مواسم جيدة مع عدد أقل من السياح ودرجات حرارة لا تزال مريحة. الصيف (مايو إلى أغسطس) حار للغاية، خاصة في صعيد مصر حيث يمكن أن تتجاوز درجات الحرارة 40 درجة مئوية (104 درجة فهرنهايت)، ولكن هذا هو الوقت الذي ستجد فيه أقل الأسعار وأقل عدد من السياح. يظل ساحل البحر الأحمر لطيفًا نسبيًا على مدار العام وهو بديل جيد للصيف. إذا كنت تزور خلال شهر رمضان، كن على علم بأن بعض الشركات قد يكون لديها ساعات عمل مخفضة، على الرغم من أن المواقع السياحية تظل مفتوحة.'
            },
            'tags': ['weather', 'climate', 'best time to visit', 'seasons', 'temperature'],
            'is_featured': True,
            'related_destination_ids': ['egypt']
        }
    ]

    # Communication FAQs
    communication_faqs = [
        {
            'question': {
                'en': 'What languages are spoken in Egypt?',
                'ar': 'ما هي اللغات المتحدثة في مصر؟'
            },
            'answer': {
                'en': 'Arabic is the official language of Egypt, specifically Egyptian Arabic, which is a dialect distinct from Modern Standard Arabic. English is widely spoken in tourist areas, major cities, and by professionals in the tourism industry. Many signs in tourist areas are in both Arabic and English. French is also spoken by some Egyptians, particularly among older and educated generations. In tourist areas, you'll find people who speak various European languages like German, Italian, Spanish, and Russian. The Nubian language is spoken in southern Egypt near Aswan. While learning a few basic Arabic phrases is appreciated by locals, you can generally get by with English in most tourist situations.',
                'ar': 'اللغة العربية هي اللغة الرسمية في مصر، وتحديداً اللغة العربية المصرية، وهي لهجة متميزة عن اللغة العربية الفصحى الحديثة. اللغة الإنجليزية منتشرة على نطاق واسع في المناطق السياحية والمدن الكبرى ومن قبل المهنيين في صناعة السياحة. العديد من اللافتات في المناطق السياحية باللغتين العربية والإنجليزية. يتحدث بعض المصريين أيضًا اللغة الفرنسية، خاصة بين الأجيال الأكبر سنًا والمتعلمة. في المناطق السياحية، ستجد أشخاصًا يتحدثون لغات أوروبية مختلفة مثل الألمانية والإيطالية والإسبانية والروسية. يتم التحدث باللغة النوبية في جنوب مصر بالقرب من أسوان. في حين أن تعلم بعض العبارات العربية الأساسية يقدره السكان المحليون، يمكنك عمومًا التعامل باللغة الإنجليزية في معظم المواقف السياحية.'
            },
            'tags': ['language', 'arabic', 'english', 'communication'],
            'is_featured': False,
            'related_destination_ids': ['egypt']
        }
    ]

    # Combine all FAQs
    all_faqs = []
    all_faqs.extend([{'category_id': 'visa_immigration', **faq} for faq in visa_faqs])
    all_faqs.extend([{'category_id': 'health_safety', **faq} for faq in health_safety_faqs])
    all_faqs.extend([{'category_id': 'money_currency', **faq} for faq in money_currency_faqs])
    all_faqs.extend([{'category_id': 'customs_etiquette', **faq} for faq in customs_etiquette_faqs])
    all_faqs.extend([{'category_id': 'transportation', **faq} for faq in transportation_faqs])
    all_faqs.extend([{'category_id': 'accommodation', **faq} for faq in accommodation_faqs])
    all_faqs.extend([{'category_id': 'food_drink', **faq} for faq in food_drink_faqs])
    all_faqs.extend([{'category_id': 'shopping_souvenirs', **faq} for faq in shopping_faqs])
    all_faqs.extend([{'category_id': 'religion_culture', **faq} for faq in religion_culture_faqs])
    all_faqs.extend([{'category_id': 'weather_climate', **faq} for faq in weather_climate_faqs])
    all_faqs.extend([{'category_id': 'communication', **faq} for faq in communication_faqs])

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
