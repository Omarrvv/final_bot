-- Migration: Add Additional Tourism FAQs
-- Date: 2025-07-01
-- Description: Add more comprehensive tourism FAQs to ensure better coverage

BEGIN;

-- Add more visa & immigration FAQs
INSERT INTO tourism_faqs (category_id, question, answer, tags, is_featured)
VALUES
    ('visa_immigration', 
     '{"en": "How long can I stay in Egypt with a tourist visa?", "ar": "كم من الوقت يمكنني البقاء في مصر بتأشيرة سياحية؟"}',
     '{"en": "A standard tourist visa for Egypt is valid for 30 days from the date of entry. If you wish to stay longer, you can apply for an extension at the Mogamma Building in Cairo or at immigration offices in other cities. Extensions are typically granted for an additional 30-90 days.", "ar": "تأشيرة السياحة القياسية لمصر صالحة لمدة 30 يومًا من تاريخ الدخول. إذا كنت ترغب في البقاء لفترة أطول، يمكنك التقدم بطلب للحصول على تمديد في مبنى المجمع في القاهرة أو في مكاتب الهجرة في المدن الأخرى. عادة ما يتم منح التمديدات لمدة 30-90 يومًا إضافية."}',
     ARRAY['visa', 'duration', 'extension', 'immigration'],
     TRUE),
     
    ('visa_immigration', 
     '{"en": "What documents do I need for an Egyptian visa?", "ar": "ما هي المستندات التي أحتاجها للحصول على تأشيرة مصرية؟"}',
     '{"en": "For an Egyptian visa, you typically need: 1) A passport valid for at least 6 months beyond your arrival date, 2) A completed visa application form, 3) One or two passport-sized photos, 4) Proof of travel arrangements (flight itinerary), 5) Hotel reservations or a letter of invitation if staying with residents. For e-visas, you need to upload digital copies of these documents.", "ar": "للحصول على تأشيرة مصرية، عادة ما تحتاج إلى: 1) جواز سفر صالح لمدة 6 أشهر على الأقل بعد تاريخ وصولك، 2) نموذج طلب تأشيرة مكتمل، 3) صورة أو صورتين بحجم جواز السفر، 4) إثبات ترتيبات السفر (مسار الرحلة)، 5) حجوزات الفندق أو خطاب دعوة إذا كنت تقيم مع المقيمين. بالنسبة للتأشيرات الإلكترونية، تحتاج إلى تحميل نسخ رقمية من هذه المستندات."}',
     ARRAY['visa', 'documents', 'passport', 'requirements'],
     FALSE),
     
    ('visa_immigration', 
     '{"en": "Can I get a visa on arrival in Egypt?", "ar": "هل يمكنني الحصول على تأشيرة عند الوصول إلى مصر؟"}',
     '{"en": "Yes, citizens of many countries can obtain a visa on arrival at Egyptian airports. The cost is approximately $25 USD, payable in cash (USD, EUR, or GBP). Countries eligible for visa on arrival include most European countries, USA, Canada, Australia, and many others. However, it''s always best to check the latest requirements before traveling as policies can change.", "ar": "نعم، يمكن لمواطني العديد من البلدان الحصول على تأشيرة عند الوصول إلى المطارات المصرية. التكلفة حوالي 25 دولارًا أمريكيًا، تدفع نقدًا (بالدولار الأمريكي أو اليورو أو الجنيه الإسترليني). تشمل البلدان المؤهلة للحصول على تأشيرة عند الوصول معظم البلدان الأوروبية والولايات المتحدة وكندا وأستراليا والعديد من البلدان الأخرى. ومع ذلك، من الأفضل دائمًا التحقق من أحدث المتطلبات قبل السفر لأن السياسات يمكن أن تتغير."}',
     ARRAY['visa', 'arrival', 'airport', 'entry'],
     TRUE),

-- Add health & safety FAQs
    ('health_safety', 
     '{"en": "What vaccinations do I need for Egypt?", "ar": "ما هي التطعيمات التي أحتاجها لمصر؟"}',
     '{"en": "No vaccinations are officially required for entry to Egypt unless you''re arriving from a country with yellow fever. However, healthcare professionals typically recommend being up-to-date on routine vaccinations (MMR, diphtheria-tetanus-pertussis, etc.) and considering hepatitis A and typhoid vaccinations. Consult with a travel health specialist 4-8 weeks before your trip for personalized advice.", "ar": "لا توجد تطعيمات مطلوبة رسميًا لدخول مصر ما لم تكن قادمًا من بلد به حمى صفراء. ومع ذلك، عادة ما ينصح متخصصو الرعاية الصحية بتحديث التطعيمات الروتينية (الحصبة والنكاف والحصبة الألمانية، الدفتيريا والكزاز والسعال الديكي، إلخ) والنظر في تطعيمات التهاب الكبد أ والتيفوئيد. استشر أخصائي صحة السفر قبل 4-8 أسابيع من رحلتك للحصول على نصائح مخصصة."}',
     ARRAY['health', 'vaccinations', 'medicine', 'prevention'],
     TRUE),
     
    ('health_safety', 
     '{"en": "Is tap water safe to drink in Egypt?", "ar": "هل مياه الصنبور آمنة للشرب في مصر؟"}',
     '{"en": "It''s generally recommended that tourists avoid drinking tap water in Egypt. While locals may drink it, visitors'' digestive systems aren''t accustomed to the local microorganisms. Stick to bottled water, which is widely available and inexpensive. Also avoid ice made from tap water and be cautious with raw vegetables and fruits that may have been washed in tap water.", "ar": "يُنصح عمومًا بأن يتجنب السياح شرب مياه الصنبور في مصر. بينما قد يشربها السكان المحليون، فإن أنظمة الجهاز الهضمي للزوار ليست معتادة على الكائنات الحية الدقيقة المحلية. التزم بالمياه المعبأة، وهي متوفرة على نطاق واسع وغير مكلفة. تجنب أيضًا الثلج المصنوع من مياه الصنبور وكن حذرًا مع الخضروات والفواكه النيئة التي ربما تم غسلها بمياه الصنبور."}',
     ARRAY['water', 'health', 'safety', 'drinking'],
     TRUE),
     
    ('health_safety', 
     '{"en": "What should I do in case of a medical emergency in Egypt?", "ar": "ماذا أفعل في حالة الطوارئ الطبية في مصر؟"}',
     '{"en": "In case of a medical emergency in Egypt, dial 123 for an ambulance. For less urgent situations, major cities have private hospitals with international standards, such as As-Salam International Hospital in Cairo or Alexandria International Hospital. It''s highly recommended to have comprehensive travel insurance that covers medical evacuation. Keep your embassy''s contact information handy, as they can provide assistance in locating appropriate medical facilities.", "ar": "في حالة الطوارئ الطبية في مصر، اتصل بالرقم 123 للحصول على سيارة إسعاف. بالنسبة للحالات الأقل إلحاحًا، تحتوي المدن الكبرى على مستشفيات خاصة بمعايير دولية، مثل مستشفى السلام الدولي في القاهرة أو مستشفى الإسكندرية الدولي. يوصى بشدة بالحصول على تأمين سفر شامل يغطي الإخلاء الطبي. احتفظ بمعلومات الاتصال بسفارتك في متناول اليد، حيث يمكنهم تقديم المساعدة في تحديد مواقع المرافق الطبية المناسبة."}',
     ARRAY['emergency', 'medical', 'hospital', 'healthcare'],
     TRUE),

-- Add transportation FAQs
    ('transportation', 
     '{"en": "What''s the best way to travel between cities in Egypt?", "ar": "ما هي أفضل طريقة للسفر بين المدن في مصر؟"}',
     '{"en": "For traveling between Egyptian cities, you have several options: 1) Domestic flights are fastest for long distances (Cairo to Luxor/Aswan/Sharm El Sheikh), 2) Trains are comfortable and affordable for travel along the Nile Valley (Cairo to Alexandria/Luxor/Aswan), 3) Buses connect most cities and are economical, 4) Nile cruises combine transportation and accommodation between Luxor and Aswan. For safety and comfort, trains and flights are generally recommended for tourists over long-distance buses.", "ar": "للسفر بين المدن المصرية، لديك عدة خيارات: 1) الرحلات الجوية الداخلية هي الأسرع للمسافات الطويلة (القاهرة إلى الأقصر/أسوان/شرم الشيخ)، 2) القطارات مريحة وبأسعار معقولة للسفر على طول وادي النيل (القاهرة إلى الإسكندرية/الأقصر/أسوان)، 3) الحافلات تربط معظم المدن وهي اقتصادية، 4) رحلات النيل النهرية تجمع بين النقل والإقامة بين الأقصر وأسوان. من أجل السلامة والراحة، يوصى عمومًا بالقطارات والرحلات الجوية للسياح بدلاً من الحافلات للمسافات الطويلة."}',
     ARRAY['transportation', 'travel', 'cities', 'intercity'],
     TRUE),
     
    ('transportation', 
     '{"en": "How do I get around Cairo?", "ar": "كيف أتنقل في القاهرة؟"}',
     '{"en": "Cairo offers multiple transportation options: 1) Metro is the fastest way to avoid traffic, with three lines covering major areas, 2) Taxis are abundant (use yellow cabs with meters or ride-hailing apps like Uber/Careem), 3) Buses and microbuses are very cheap but can be confusing for tourists, 4) Walking is possible in some areas but challenging due to traffic and lack of sidewalks. For tourists, a combination of metro for long distances and taxis for shorter trips is usually most convenient.", "ar": "توفر القاهرة خيارات نقل متعددة: 1) المترو هو أسرع وسيلة لتجنب الازدحام المروري، مع ثلاثة خطوط تغطي المناطق الرئيسية، 2) سيارات الأجرة متوفرة بكثرة (استخدم سيارات الأجرة الصفراء ذات العدادات أو تطبيقات طلب الركوب مثل أوبر/كريم)، 3) الحافلات والميكروباصات رخيصة جدًا ولكن قد تكون مربكة للسياح، 4) المشي ممكن في بعض المناطق ولكنه صعب بسبب حركة المرور وقلة الأرصفة. بالنسبة للسياح، عادة ما يكون مزيج من المترو للمسافات الطويلة وسيارات الأجرة للرحلات القصيرة هو الأكثر ملاءمة."}',
     ARRAY['transportation', 'Cairo', 'metro', 'taxi'],
     TRUE),

-- Add accommodation FAQs
    ('accommodation', 
     '{"en": "What types of accommodation are available in Egypt?", "ar": "ما هي أنواع الإقامة المتاحة في مصر؟"}',
     '{"en": "Egypt offers a wide range of accommodation options: 1) Luxury hotels and resorts, particularly in Cairo, Luxor, and Red Sea destinations, 2) Mid-range hotels with good amenities, 3) Budget hotels and hostels in major cities, 4) Nile cruise ships that serve as floating hotels, 5) Boutique hotels in historic buildings, especially in Cairo and Alexandria, 6) Eco-lodges in the Western Desert oases, 7) Apartment rentals for longer stays. Most tourist areas have international hotel chains as well as local options.", "ar": "تقدم مصر مجموعة واسعة من خيارات الإقامة: 1) الفنادق والمنتجعات الفاخرة، خاصة في القاهرة والأقصر ووجهات البحر الأحمر، 2) الفنادق متوسطة المستوى مع وسائل راحة جيدة، 3) الفنادق الاقتصادية والنزل في المدن الكبرى، 4) سفن الرحلات النيلية التي تعمل كفنادق عائمة، 5) الفنادق البوتيكية في المباني التاريخية، خاصة في القاهرة والإسكندرية، 6) النزل البيئية في واحات الصحراء الغربية، 7) شقق للإيجار للإقامات الطويلة. تحتوي معظم المناطق السياحية على سلاسل فنادق دولية بالإضافة إلى خيارات محلية."}',
     ARRAY['accommodation', 'hotels', 'resorts', 'lodging'],
     TRUE),

-- Add food & drink FAQs
    ('food_drink', 
     '{"en": "What are the must-try Egyptian dishes?", "ar": "ما هي الأطباق المصرية التي يجب تجربتها؟"}',
     '{"en": "Essential Egyptian dishes to try include: 1) Koshari - a mix of rice, lentils, pasta, and tomato sauce, 2) Ful medames - mashed fava beans with olive oil and spices, 3) Ta''ameya (Egyptian falafel) - made with fava beans instead of chickpeas, 4) Molokhia - a green soup served with rice, 5) Hawawshi - spiced minced meat in bread, 6) Mahshi - stuffed vegetables, 7) Roz bel laban - rice pudding with cinnamon, 8) Shawarma - grilled meat in bread, 9) Om Ali - Egyptian bread pudding. Street food is delicious but choose vendors with high turnover and good hygiene practices.", "ar": "تشمل الأطباق المصرية الأساسية التي يجب تجربتها: 1) الكشري - مزيج من الأرز والعدس والمعكرونة وصلصة الطماطم، 2) الفول المدمس - فول مهروس مع زيت الزيتون والتوابل، 3) الطعمية (الفلافل المصرية) - مصنوعة من الفول بدلاً من الحمص، 4) الملوخية - حساء أخضر يقدم مع الأرز، 5) الحواوشي - لحم مفروم متبل في الخبز، 6) المحشي - خضروات محشوة، 7) الأرز باللبن - أرز بالحليب مع القرفة، 8) الشاورما - لحم مشوي في الخبز، 9) أم علي - حلوى خبز مصرية. طعام الشارع لذيذ ولكن اختر البائعين ذوي معدل دوران مرتفع وممارسات نظافة جيدة."}',
     ARRAY['food', 'cuisine', 'dishes', 'traditional'],
     TRUE),
     
    ('food_drink', 
     '{"en": "Is it safe to eat street food in Egypt?", "ar": "هل من الآمن تناول طعام الشارع في مصر؟"}',
     '{"en": "Street food in Egypt can be safe and delicious if you take precautions: 1) Choose busy stalls with high customer turnover, 2) Eat at places where locals eat, 3) Select food that''s freshly cooked and served hot, 4) Avoid raw vegetables and unpeeled fruits, 5) Be cautious with dairy products, 6) Drink only bottled water and avoid ice. Popular safe street foods include koshari, ta''ameya (falafel), hawawshi (meat-filled bread), and freshly baked bread.", "ar": "يمكن أن يكون طعام الشارع في مصر آمنًا ولذيذًا إذا اتخذت احتياطات: 1) اختر الأكشاك المزدحمة ذات معدل دوران العملاء المرتفع، 2) تناول الطعام في الأماكن التي يأكل فيها السكان المحليون، 3) اختر الطعام المطبوخ حديثًا والمقدم ساخنًا، 4) تجنب الخضروات النيئة والفواكه غير المقشرة، 5) كن حذرًا مع منتجات الألبان، 6) اشرب المياه المعبأة فقط وتجنب الثلج. تشمل أطعمة الشارع الآمنة الشائعة الكشري والطعمية (الفلافل) والحواوشي (خبز محشو باللحم) والخبز المخبوز حديثًا."}',
     ARRAY['food', 'street food', 'safety', 'eating'],
     TRUE),

-- Add shopping & souvenirs FAQs
    ('shopping_souvenirs', 
     '{"en": "What are the best souvenirs to buy in Egypt?", "ar": "ما هي أفضل الهدايا التذكارية للشراء في مصر؟"}',
     '{"en": "Popular Egyptian souvenirs include: 1) Papyrus paintings (ensure they''re authentic), 2) Cartouches with your name in hieroglyphics, 3) Egyptian cotton products, 4) Spices from local markets, 5) Alabaster and marble items, 6) Hand-blown glass, 7) Brass and copper items, 8) Traditional jewelry like the Eye of Horus, 9) Perfume oils and essence bottles, 10) Shisha pipes, 11) Handmade carpets and kilims. The Khan el-Khalili bazaar in Cairo is a famous shopping destination, but you''ll find souvenirs throughout the country.", "ar": "تشمل الهدايا التذكارية المصرية الشائعة: 1) لوحات البردي (تأكد من أنها أصلية)، 2) الخراطيش مع اسمك بالهيروغليفية، 3) منتجات القطن المصري، 4) التوابل من الأسواق المحلية، 5) الألباستر والرخام، 6) الزجاج المنفوخ يدويًا، 7) النحاس والنحاس الأصفر، 8) المجوهرات التقليدية مثل عين حورس، 9) زيوت العطور وزجاجات العطور، 10) الشيشة، 11) السجاد والكليم المصنوع يدويًا. سوق خان الخليلي في القاهرة هو وجهة تسوق شهيرة، ولكنك ستجد الهدايا التذكارية في جميع أنحاء البلاد."}',
     ARRAY['shopping', 'souvenirs', 'gifts', 'markets'],
     TRUE),

-- Add religion & culture FAQs
    ('religion_culture', 
     '{"en": "What are the major religious sites to visit in Egypt?", "ar": "ما هي المواقع الدينية الرئيسية للزيارة في مصر؟"}',
     '{"en": "Egypt has significant religious sites from multiple faiths: 1) Islamic sites: Al-Azhar Mosque, Sultan Hassan Mosque, and Ibn Tulun Mosque in Cairo; 2) Coptic Christian sites: The Hanging Church, Coptic Museum, and Church of St. Sergius in Cairo; 3) Jewish sites: Ben Ezra Synagogue in Cairo; 4) Ancient Egyptian temples: Karnak and Luxor Temples, Abu Simbel, Philae Temple, and many more throughout the country. When visiting religious sites, dress modestly (covering shoulders and knees), and in mosques, women should cover their hair.", "ar": "تضم مصر مواقع دينية مهمة من ديانات متعددة: 1) المواقع الإسلامية: الجامع الأزهر، مسجد السلطان حسن، ومسجد ابن طولون في القاهرة؛ 2) المواقع المسيحية القبطية: الكنيسة المعلقة، المتحف القبطي، وكنيسة القديس سرجيوس في القاهرة؛ 3) المواقع اليهودية: معبد بن عزرا في القاهرة؛ 4) معابد مصر القديمة: معابد الكرنك والأقصر، أبو سمبل، معبد فيلة، والعديد من المواقع الأخرى في جميع أنحاء البلاد. عند زيارة المواقع الدينية، ارتدِ ملابس محتشمة (تغطي الكتفين والركبتين)، وفي المساجد، يجب على النساء تغطية شعرهن."}',
     ARRAY['religion', 'mosques', 'churches', 'temples'],
     TRUE),

-- Add weather & climate FAQs
    ('weather_climate', 
     '{"en": "When is the best time to visit Egypt?", "ar": "ما هو أفضل وقت لزيارة مصر؟"}',
     '{"en": "The best time to visit Egypt is during the cooler months from October to April. Winter (December-February) offers the most pleasant temperatures for sightseeing in Cairo, Luxor, and Aswan, though evenings can be cool. Spring (March-April) and autumn (October-November) offer warm days and cool nights. Summer (May-September) is extremely hot, especially in Upper Egypt (Luxor/Aswan), with temperatures regularly exceeding 40°C (104°F). The Red Sea coast remains pleasant year-round. Ramadan dates vary each year and may affect opening hours and services.", "ar": "أفضل وقت لزيارة مصر هو خلال الأشهر الأكثر برودة من أكتوبر إلى أبريل. يوفر الشتاء (ديسمبر-فبراير) درجات الحرارة الأكثر متعة لمشاهدة المعالم السياحية في القاهرة والأقصر وأسوان، على الرغم من أن الأمسيات يمكن أن تكون باردة. يوفر الربيع (مارس-أبريل) والخريف (أكتوبر-نوفمبر) أيامًا دافئة وليالي باردة. الصيف (مايو-سبتمبر) حار للغاية، خاصة في صعيد مصر (الأقصر/أسوان)، حيث تتجاوز درجات الحرارة بانتظام 40 درجة مئوية (104 درجة فهرنهايت). يظل ساحل البحر الأحمر لطيفًا على مدار العام. تختلف تواريخ رمضان كل عام وقد تؤثر على ساعات الفتح والخدمات."}',
     ARRAY['weather', 'climate', 'seasons', 'best time'],
     TRUE),

-- Add communication FAQs
    ('communication', 
     '{"en": "Will my phone work in Egypt?", "ar": "هل سيعمل هاتفي في مصر؟"}',
     '{"en": "Most international phones will work in Egypt, which has good mobile coverage in urban areas and tourist destinations. For the best rates, consider: 1) Purchasing a local SIM card from providers like Vodafone, Orange, or Etisalat (you''ll need an unlocked phone and your passport for registration), 2) Using an international roaming plan from your home provider (check rates beforehand), 3) Relying on WiFi, which is available in most hotels and many cafes. 4G coverage is available in major cities and tourist areas, with 5G being introduced in select locations.", "ar": "ستعمل معظم الهواتف الدولية في مصر، التي تتمتع بتغطية جيدة للهاتف المحمول في المناطق الحضرية والوجهات السياحية. للحصول على أفضل الأسعار، ضع في اعتبارك: 1) شراء بطاقة SIM محلية من مزودي الخدمة مثل فودافون أو أورانج أو اتصالات (ستحتاج إلى هاتف غير مقفل وجواز سفرك للتسجيل)، 2) استخدام خطة تجوال دولية من مزود الخدمة في بلدك (تحقق من الأسعار مسبقًا)، 3) الاعتماد على WiFi، المتوفر في معظم الفنادق والعديد من المقاهي. تتوفر تغطية 4G في المدن الرئيسية والمناطق السياحية، مع إدخال 5G في مواقع مختارة."}',
     ARRAY['communication', 'phone', 'internet', 'SIM card'],
     TRUE),
     
    ('communication', 
     '{"en": "What languages are spoken in Egypt?", "ar": "ما هي اللغات المتحدثة في مصر؟"}',
     '{"en": "Arabic is the official language of Egypt, specifically Egyptian Arabic dialect. In tourist areas, English is widely spoken, especially in hotels, restaurants, and attractions. French is also common among older Egyptians and in some upscale establishments. Other languages you might encounter include German, Italian, Russian, and Spanish, particularly in popular tourist destinations. Learning a few basic Arabic phrases like ''shukran'' (thank you) and ''min fadlak'' (please) is appreciated by locals.", "ar": "العربية هي اللغة الرسمية في مصر، وتحديداً اللهجة العربية المصرية. في المناطق السياحية، تنتشر اللغة الإنجليزية، خاصة في الفنادق والمطاعم والمعالم السياحية. الفرنسية شائعة أيضًا بين المصريين الأكبر سنًا وفي بعض المؤسسات الراقية. اللغات الأخرى التي قد تصادفها تشمل الألمانية والإيطالية والروسية والإسبانية، خاصة في الوجهات السياحية الشهيرة. يقدر السكان المحليون تعلم بعض العبارات العربية الأساسية مثل ''شكراً'' و ''من فضلك''."}',
     ARRAY['communication', 'language', 'Arabic', 'English'],
     TRUE);

-- Add more FAQs for other categories as needed

-- Verify the insertion
SELECT COUNT(*) AS new_faqs_count FROM tourism_faqs;

COMMIT;
