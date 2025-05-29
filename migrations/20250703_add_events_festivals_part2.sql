-- Migration: Add Events and Festivals (Part 2)
-- Date: 2025-07-03
-- Description: Add more events and festivals to ensure better coverage

BEGIN;

-- Add more events and festivals
INSERT INTO events_festivals (
    category_id, 
    name, 
    description, 
    start_date, 
    end_date, 
    is_annual, 
    annual_month, 
    annual_day, 
    lunar_calendar, 
    location_description, 
    destination_id, 
    venue, 
    organizer, 
    admission, 
    schedule, 
    highlights, 
    historical_significance, 
    tips, 
    images, 
    website, 
    contact_info, 
    tags, 
    is_featured
) VALUES
    (
        'seasonal_celebrations',
        '{"en": "Sham El-Nessim", "ar": "شم النسيم"}',
        '{"en": "Sham El-Nessim is an ancient Egyptian spring festival celebrated since approximately 2700 BCE. The name means ''smelling the breeze'' in Arabic. It is celebrated on the day after Eastern Christian Easter, regardless of whether one is Christian or Muslim. Egyptians traditionally spend the day outdoors in parks and gardens, enjoying picnics with family and friends. Traditional foods include colored boiled eggs, salted fish (feseekh), lettuce, and green onions.", "ar": "شم النسيم هو مهرجان ربيعي مصري قديم يُحتفل به منذ حوالي 2700 قبل الميلاد. يعني الاسم ''شم النسيم'' باللغة العربية. يُحتفل به في اليوم التالي لعيد الفصح المسيحي الشرقي، بغض النظر عما إذا كان الشخص مسيحيًا أو مسلمًا. يقضي المصريون تقليديًا اليوم في الهواء الطلق في الحدائق والمتنزهات، ويستمتعون بالنزهات مع العائلة والأصدقاء. تشمل الأطعمة التقليدية البيض المسلوق الملون والسمك المملح (الفسيخ) والخس والبصل الأخضر."}',
        '2026-04-20',
        '2026-04-20',
        TRUE,
        NULL,
        NULL,
        FALSE,
        '{"en": "Celebrated throughout Egypt, with families gathering in public parks, gardens, and along the Nile.", "ar": "يُحتفل به في جميع أنحاء مصر، حيث تتجمع العائلات في الحدائق العامة والمتنزهات وعلى طول نهر النيل."}',
        'nationwide',
        '{"en": {"name": "Various parks and public spaces", "address": "Throughout Egypt"}, "ar": {"name": "حدائق ومساحات عامة متنوعة", "address": "في جميع أنحاء مصر"}}',
        '{"en": {"name": "Traditional celebration", "website": null}, "ar": {"name": "احتفال تقليدي", "website": null}}',
        '{"en": {"fee": "Free", "notes": "Some parks may charge entrance fees"}, "ar": {"fee": "مجاني", "notes": "قد تفرض بعض الحدائق رسوم دخول"}}',
        '{"en": [
            {"time": "Morning", "activity": "Families prepare picnic baskets with traditional foods"},
            {"time": "Daytime", "activity": "Outings to parks, gardens, and the Nile"},
            {"time": "Evening", "activity": "Return home after a day outdoors"}
        ], "ar": [
            {"time": "الصباح", "activity": "تعد العائلات سلال النزهة بالأطعمة التقليدية"},
            {"time": "النهار", "activity": "رحلات إلى الحدائق والمتنزهات والنيل"},
            {"time": "المساء", "activity": "العودة إلى المنزل بعد يوم في الهواء الطلق"}
        ]}',
        '{"en": ["Colored eggs symbolizing new life", "Feseekh (salted fermented fish)", "Family gatherings in parks", "Boat rides on the Nile", "Flying kites"], "ar": ["البيض الملون الذي يرمز إلى الحياة الجديدة", "الفسيخ (سمك مخمر مملح)", "تجمعات عائلية في الحدائق", "رحلات بالقوارب على النيل", "الطائرات الورقية"]}',
        '{"en": "Sham El-Nessim dates back to ancient Egypt, around 2700 BCE during the Third Dynasty. It was originally associated with agriculture and fertility, celebrating the spring harvest. The name comes from the ancient Egyptian harvest season ''Shemu.'' After the arrival of Christianity in Egypt, the festival became associated with Easter, though it maintained its pharaonic traditions. Today, it is celebrated by all Egyptians regardless of religion, making it a truly national festival that transcends religious boundaries.", "ar": "يعود شم النسيم إلى مصر القديمة، حوالي 2700 قبل الميلاد خلال الأسرة الثالثة. كان مرتبطًا في الأصل بالزراعة والخصوبة، احتفالًا بحصاد الربيع. يأتي الاسم من موسم الحصاد المصري القديم ''شمو''. بعد وصول المسيحية إلى مصر، أصبح المهرجان مرتبطًا بعيد الفصح، على الرغم من أنه حافظ على تقاليده الفرعونية. اليوم، يحتفل به جميع المصريين بغض النظر عن الدين، مما يجعله مهرجانًا وطنيًا حقًا يتجاوز الحدود الدينية."}',
        '{"en": ["Popular parks get very crowded, so arrive early to secure a good spot", "Be cautious with feseekh (salted fish) as it can cause food poisoning if not properly prepared", "Bring a picnic blanket, sunscreen, and plenty of water", "Al-Azhar Park, Giza Zoo, and the Nile Corniche are popular spots in Cairo", "Traffic can be extremely heavy on this holiday"], "ar": ["تزدحم الحدائق الشعبية بشدة، لذا احضر مبكرًا لتأمين مكان جيد", "كن حذرًا مع الفسيخ (السمك المملح) لأنه قد يسبب تسممًا غذائيًا إذا لم يتم إعداده بشكل صحيح", "أحضر بطانية للنزهة وواقي من الشمس والكثير من الماء", "حديقة الأزهر وحديقة حيوان الجيزة وكورنيش النيل هي أماكن شعبية في القاهرة", "يمكن أن تكون حركة المرور شديدة للغاية في هذه العطلة"]}',
        '{"main_image": "sham_el_nessim.jpg", "gallery": ["colored_eggs.jpg", "family_picnic.jpg", "nile_boats.jpg"]}',
        'https://www.egypt.travel/en/events/sham-el-nessim',
        '{"phone": "+20 2 27358761", "email": "info@egypt.travel"}',
        ARRAY['spring', 'festival', 'cultural', 'traditional', 'family', 'food'],
        TRUE
    ),
    
    (
        'historical_commemorations',
        '{"en": "Abu Simbel Sun Festival", "ar": "مهرجان شمس أبو سمبل"}',
        '{"en": "The Abu Simbel Sun Festival occurs twice a year when the sun''s rays penetrate the inner sanctuary of the Abu Simbel temple and illuminate three of the four statues inside (Ramses II, Ra, and Amun, leaving Ptah in darkness as he was associated with the underworld). This phenomenon happens only on February 22 (Ramses II''s birthday) and October 22 (his coronation day). The temple was precisely designed to create this effect, demonstrating the ancient Egyptians'' astronomical knowledge.", "ar": "يحدث مهرجان شمس أبو سمبل مرتين في السنة عندما تخترق أشعة الشمس الحرم الداخلي لمعبد أبو سمبل وتضيء ثلاثة من التماثيل الأربعة بالداخل (رمسيس الثاني، رع، وآمون، تاركة بتاح في الظلام لأنه كان مرتبطًا بالعالم السفلي). تحدث هذه الظاهرة فقط في 22 فبراير (عيد ميلاد رمسيس الثاني) و22 أكتوبر (يوم تتويجه). تم تصميم المعبد بدقة لإنشاء هذا التأثير، مما يدل على المعرفة الفلكية للمصريين القدماء."}',
        '2025-10-22',
        '2025-10-22',
        TRUE,
        10,
        22,
        FALSE,
        '{"en": "The festival takes place at the Abu Simbel temple complex in southern Egypt, near the border with Sudan, about 290 km southwest of Aswan.", "ar": "يقام المهرجان في مجمع معبد أبو سمبل في جنوب مصر، بالقرب من الحدود مع السودان، على بعد حوالي 290 كم جنوب غرب أسوان."}',
        'abu_simbel',
        '{"en": {"name": "Abu Simbel Temple Complex", "address": "Abu Simbel, Aswan Governorate"}, "ar": {"name": "مجمع معبد أبو سمبل", "address": "أبو سمبل، محافظة أسوان"}}',
        '{"en": {"name": "Ministry of Tourism and Antiquities", "website": "www.egypt.travel"}, "ar": {"name": "وزارة السياحة والآثار", "website": "www.egypt.travel"}}',
        '{"en": {"fee": "Adult: 240 EGP, Student: 120 EGP", "notes": "Additional fees may apply for photography"}, "ar": {"fee": "البالغين: 240 جنيه مصري، الطلاب: 120 جنيه مصري", "notes": "قد تنطبق رسوم إضافية للتصوير الفوتوغرافي"}}',
        '{"en": [
            {"time": "Early Morning (4-5 AM)", "activity": "Visitors gather at the temple"},
            {"time": "Sunrise (around 6 AM)", "activity": "Sun alignment phenomenon occurs"},
            {"time": "Morning", "activity": "Cultural performances and celebrations outside the temple"},
            {"time": "Daytime", "activity": "Exploration of the temple complex"}
        ], "ar": [
            {"time": "الصباح الباكر (4-5 صباحًا)", "activity": "يتجمع الزوار في المعبد"},
            {"time": "شروق الشمس (حوالي الساعة 6 صباحًا)", "activity": "تحدث ظاهرة محاذاة الشمس"},
            {"time": "الصباح", "activity": "العروض الثقافية والاحتفالات خارج المعبد"},
            {"time": "النهار", "activity": "استكشاف مجمع المعبد"}
        ]}',
        '{"en": ["Sun alignment illuminating the statues", "Traditional Nubian music and dance performances", "Sound and light show", "Viewing the colossal statues of Ramses II", "Exploring both temples (Ramses II and Nefertari)"], "ar": ["محاذاة الشمس التي تضيء التماثيل", "عروض الموسيقى والرقص النوبية التقليدية", "عرض الصوت والضوء", "مشاهدة التماثيل الضخمة لرمسيس الثاني", "استكشاف كلا المعبدين (رمسيس الثاني ونفرتاري)"]}',
        '{"en": "The Abu Simbel temples were originally carved into a mountainside during the reign of Pharaoh Ramses II (c. 1279-1213 BCE) as a monument to himself and his queen Nefertari. In the 1960s, the temples were threatened by the rising waters of Lake Nasser, created by the construction of the Aswan High Dam. In a remarkable feat of engineering, the temples were dismantled and relocated to higher ground in a UNESCO-led project. During the relocation, engineers maintained the solar alignment, ensuring that the sun festival would continue to occur on the same dates.", "ar": "تم نحت معابد أبو سمبل في الأصل في جانب جبل خلال عهد الفرعون رمسيس الثاني (حوالي 1279-1213 قبل الميلاد) كنصب تذكاري لنفسه ولملكته نفرتاري. في الستينيات، كانت المعابد مهددة بارتفاع مياه بحيرة ناصر، التي أنشئت ببناء السد العالي في أسوان. في إنجاز رائع في الهندسة، تم تفكيك المعابد ونقلها إلى أرض أعلى في مشروع بقيادة اليونسكو. خلال عملية النقل، حافظ المهندسون على المحاذاة الشمسية، مما ضمن استمرار حدوث مهرجان الشمس في نفس التواريخ."}',
        '{"en": ["Book accommodation in Aswan well in advance as options near Abu Simbel are limited", "Most visitors arrive via organized tours from Aswan (3-4 hour drive each way)", "Flights from Aswan to Abu Simbel are available but book quickly", "Arrive at the temple by 4-5 AM to secure a good viewing position", "Photography inside the temple may require a special ticket", "Bring warm clothes for the early morning as desert temperatures can be cool", "October is generally more comfortable than February in terms of temperature"], "ar": ["احجز الإقامة في أسوان قبل وقت طويل لأن الخيارات بالقرب من أبو سمبل محدودة", "يصل معظم الزوار عبر جولات منظمة من أسوان (3-4 ساعات قيادة في كل اتجاه)", "تتوفر رحلات جوية من أسوان إلى أبو سمبل ولكنها تُحجز بسرعة", "صل إلى المعبد بحلول الساعة 4-5 صباحًا لتأمين موقع مشاهدة جيد", "قد يتطلب التصوير داخل المعبد تذكرة خاصة", "أحضر ملابس دافئة للصباح الباكر حيث يمكن أن تكون درجات حرارة الصحراء باردة", "أكتوبر أكثر راحة بشكل عام من فبراير من حيث درجة الحرارة"]}',
        '{"main_image": "abu_simbel_sun_festival.jpg", "gallery": ["sun_alignment.jpg", "temple_facade.jpg", "nubian_performance.jpg"]}',
        'https://www.egypt.travel/en/attractions/abu-simbel-temples',
        '{"phone": "+20 97 3310288", "email": "info@egypt.travel"}',
        ARRAY['historical', 'archaeological', 'astronomical', 'cultural', 'nubian', 'ramses'],
        TRUE
    ),
    
    (
        'food_festivals',
        '{"en": "Alexandria Food Festival", "ar": "مهرجان الإسكندرية للطعام"}',
        '{"en": "The Alexandria Food Festival is an annual celebration of Mediterranean and Egyptian cuisine held in Egypt''s second-largest city. The festival showcases Alexandria''s unique culinary heritage, which blends Egyptian, Greek, Italian, Lebanese, and other Mediterranean influences. Visitors can enjoy food tastings, cooking demonstrations, chef competitions, and cultural performances. The festival highlights both traditional Alexandrian specialties and innovative contemporary dishes.", "ar": "مهرجان الإسكندرية للطعام هو احتفال سنوي بالمطبخ المتوسطي والمصري يقام في ثاني أكبر مدينة في مصر. يعرض المهرجان التراث الطهي الفريد للإسكندرية، الذي يمزج بين التأثيرات المصرية واليونانية والإيطالية واللبنانية وغيرها من تأثيرات البحر المتوسط. يمكن للزوار الاستمتاع بتذوق الطعام وعروض الطهي ومسابقات الطهاة والعروض الثقافية. يسلط المهرجان الضوء على كل من التخصصات السكندرية التقليدية والأطباق المعاصرة المبتكرة."}',
        '2025-09-15',
        '2025-09-20',
        TRUE,
        9,
        NULL,
        FALSE,
        '{"en": "The festival is held along the Corniche and in various venues throughout Alexandria, with the main events taking place at Bibliotheca Alexandrina and Montaza Palace gardens.", "ar": "يقام المهرجان على طول الكورنيش وفي أماكن مختلفة في جميع أنحاء الإسكندرية، مع إقامة الفعاليات الرئيسية في مكتبة الإسكندرية وحدائق قصر المنتزه."}',
        'alexandria',
        '{"en": {"name": "Multiple venues", "address": "Alexandria Corniche, Bibliotheca Alexandrina, Montaza Palace"}, "ar": {"name": "أماكن متعددة", "address": "كورنيش الإسكندرية، مكتبة الإسكندرية، قصر المنتزه"}}',
        '{"en": {"name": "Alexandria Culinary Association", "website": "www.alexandriafoodfest.com"}, "ar": {"name": "جمعية الإسكندرية للطهي", "website": "www.alexandriafoodfest.com"}}',
        '{"en": {"fee": "General admission: 100 EGP, Food tasting passes: 200-500 EGP", "notes": "Some special events and workshops require separate tickets"}, "ar": {"fee": "الدخول العام: 100 جنيه مصري، تذاكر تذوق الطعام: 200-500 جنيه مصري", "notes": "تتطلب بعض الفعاليات الخاصة وورش العمل تذاكر منفصلة"}}',
        '{"en": [
            {"time": "Morning", "activity": "Cooking workshops and demonstrations"},
            {"time": "Afternoon", "activity": "Food tastings and market stalls"},
            {"time": "Evening", "activity": "Chef competitions and cultural performances"}
        ], "ar": [
            {"time": "الصباح", "activity": "ورش عمل وعروض الطهي"},
            {"time": "بعد الظهر", "activity": "تذوق الطعام وأكشاك السوق"},
            {"time": "المساء", "activity": "مسابقات الطهاة والعروض الثقافية"}
        ]}',
        '{"en": ["Seafood showcase featuring Alexandria''s famous fish dishes", "Mediterranean street food market", "Chef competitions", "Cooking classes for traditional Alexandrian dishes", "Food and history tours of the city", "Evening gala dinners with celebrity chefs"], "ar": ["عرض المأكولات البحرية الذي يضم أطباق السمك الشهيرة في الإسكندرية", "سوق أطعمة الشارع المتوسطية", "مسابقات الطهاة", "دروس الطبخ للأطباق السكندرية التقليدية", "جولات الطعام والتاريخ في المدينة", "عشاء احتفالي مسائي مع طهاة مشهورين"]}',
        '{"en": "Alexandria has a rich culinary heritage dating back to its founding by Alexander the Great in 331 BCE. As a major Mediterranean port city, it has absorbed influences from Greek, Roman, Ottoman, French, Italian, and Levantine cuisines over the centuries. The city was known for its cosmopolitan character throughout the 19th and early 20th centuries, with large Greek, Italian, Jewish, and other communities contributing to its diverse food culture. The Alexandria Food Festival was established to celebrate this unique culinary heritage and promote the city as a gastronomic destination.", "ar": "تتمتع الإسكندرية بتراث طهي غني يعود تاريخه إلى تأسيسها على يد الإسكندر الأكبر عام 331 قبل الميلاد. كمدينة ميناء متوسطية رئيسية، استوعبت تأثيرات من المطابخ اليونانية والرومانية والعثمانية والفرنسية والإيطالية واللفانتية على مر القرون. كانت المدينة معروفة بطابعها العالمي طوال القرن التاسع عشر وأوائل القرن العشرين، مع مجتمعات كبيرة من اليونانيين والإيطاليين واليهود وغيرهم ساهمت في ثقافتها الغذائية المتنوعة. تم إنشاء مهرجان الإسكندرية للطعام للاحتفال بهذا التراث الطهي الفريد وتعزيز المدينة كوجهة للطعام."}',
        '{"en": ["Purchase food tasting passes in advance as they sell out quickly", "Wear comfortable shoes as venues are spread throughout the city", "September weather in Alexandria is pleasant but can be humid", "Try the local specialties like Greek-influenced grilled fish, seafood soup (shorbet el samak), and Alexandria-style liver (kebda Iskandarani)", "Some events offer English translations, but having basic Arabic phrases is helpful", "The Corniche can get very crowded during festival evenings"], "ar": ["اشترِ تذاكر تذوق الطعام مسبقًا لأنها تنفد بسرعة", "ارتدِ أحذية مريحة لأن الأماكن منتشرة في جميع أنحاء المدينة", "طقس سبتمبر في الإسكندرية لطيف ولكن يمكن أن يكون رطبًا", "جرب التخصصات المحلية مثل السمك المشوي المتأثر باليونانية، وشوربة المأكولات البحرية (شوربة السمك)، والكبدة على الطريقة السكندرية (كبدة إسكندراني)", "تقدم بعض الفعاليات ترجمات إنجليزية، ولكن معرفة العبارات العربية الأساسية مفيدة", "يمكن أن يزدحم الكورنيش بشدة خلال أمسيات المهرجان"]}',
        '{"main_image": "alexandria_food_festival.jpg", "gallery": ["seafood_display.jpg", "cooking_demonstration.jpg", "corniche_stalls.jpg"]}',
        'https://www.alexandriafoodfest.com',
        '{"phone": "+20 3 4876543", "email": "info@alexandriafoodfest.com"}',
        ARRAY['food', 'culinary', 'festival', 'mediterranean', 'alexandria', 'seafood'],
        TRUE
    );

-- Verify the insertion
SELECT COUNT(*) AS new_events_count FROM events_festivals;

COMMIT;
