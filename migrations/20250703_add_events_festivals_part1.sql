-- Migration: Add Events and Festivals (Part 1)
-- Date: 2025-07-03
-- Description: Add comprehensive events and festivals to ensure better coverage

BEGIN;

-- Add religious festivals
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
        'religious_festivals',
        '{"en": "Moulid El-Nabi (Prophet''s Birthday)", "ar": "المولد النبوي الشريف"}',
        '{"en": "Moulid El-Nabi celebrates the birthday of Prophet Muhammad. Throughout Egypt, streets are decorated with colorful lights, banners, and special tents where Sufi chanting and religious songs are performed. Families gather to share traditional sweets, especially the sugar dolls and horses known as ''Arouset El-Moulid'' and ''Housan El-Moulid''.", "ar": "يحتفل المولد النبوي بعيد ميلاد النبي محمد. في جميع أنحاء مصر، تزين الشوارع بالأضواء الملونة واللافتات والخيام الخاصة حيث يتم أداء الإنشاد الصوفي والأغاني الدينية. تجتمع العائلات لتناول الحلويات التقليدية، خاصة دمى السكر والخيول المعروفة باسم ''عروسة المولد'' و''حصان المولد''."}',
        NULL,
        NULL,
        TRUE,
        NULL,
        NULL,
        TRUE,
        '{"en": "Celebrated throughout Egypt, with major celebrations in Cairo, particularly in the historic Islamic districts.", "ar": "يُحتفل به في جميع أنحاء مصر، مع احتفالات كبرى في القاهرة، خاصة في الأحياء الإسلامية التاريخية."}',
        'cairo',
        '{"en": {"name": "Various locations", "address": "Islamic Cairo, especially around Al-Hussein Mosque"}, "ar": {"name": "مواقع متعددة", "address": "القاهرة الإسلامية، خاصة حول مسجد الحسين"}}',
        '{"en": {"name": "Ministry of Religious Endowments", "website": "www.awkaf.gov.eg"}, "ar": {"name": "وزارة الأوقاف", "website": "www.awkaf.gov.eg"}}',
        '{"en": {"fee": "Free", "notes": "Some Sufi performances may require tickets"}, "ar": {"fee": "مجاني", "notes": "قد تتطلب بعض العروض الصوفية تذاكر"}}',
        '{"en": [
            {"time": "All day", "activity": "Street celebrations and decorations"},
            {"time": "Evening", "activity": "Sufi chanting and religious performances"},
            {"time": "Night", "activity": "Family gatherings and sweet distribution"}
        ], "ar": [
            {"time": "طوال اليوم", "activity": "احتفالات وزينة الشوارع"},
            {"time": "المساء", "activity": "الإنشاد الصوفي والعروض الدينية"},
            {"time": "الليل", "activity": "التجمعات العائلية وتوزيع الحلويات"}
        ]}',
        '{"en": ["Colorful street decorations", "Traditional sweets", "Sufi performances", "Religious chanting", "Family gatherings"], "ar": ["زينة الشوارع الملونة", "الحلويات التقليدية", "العروض الصوفية", "الإنشاد الديني", "التجمعات العائلية"]}',
        '{"en": "The celebration of Moulid El-Nabi dates back to the Fatimid era in Egypt (10th-12th centuries). The Fatimids were known for their elaborate public celebrations of religious events, and the tradition has continued through the centuries, blending religious devotion with cultural festivities.", "ar": "يعود الاحتفال بالمولد النبوي إلى العصر الفاطمي في مصر (القرنين العاشر والثاني عشر). كان الفاطميون معروفين باحتفالاتهم العامة المفصلة بالمناسبات الدينية، واستمر التقليد عبر القرون، مازجًا بين التقوى الدينية والاحتفالات الثقافية."}',
        '{"en": ["Visit Al-Hussein Mosque area for the most authentic experience", "Try the traditional sweets from established shops", "Be respectful of religious customs", "Expect large crowds in popular areas", "The exact date changes each year as it follows the Islamic lunar calendar"], "ar": ["قم بزيارة منطقة مسجد الحسين للحصول على تجربة أصيلة", "جرب الحلويات التقليدية من المحلات المعروفة", "احترم العادات الدينية", "توقع حشودًا كبيرة في المناطق الشعبية", "يتغير التاريخ الدقيق كل عام لأنه يتبع التقويم القمري الإسلامي"]}',
        '{"main_image": "moulid_el_nabi.jpg", "gallery": ["moulid_sweets.jpg", "sufi_performance.jpg", "decorated_streets.jpg"]}',
        'https://www.egypt.travel/en/events/moulid-el-nabi',
        '{"phone": "+20 2 27358761", "email": "info@egypt.travel"}',
        ARRAY['religious', 'islamic', 'festival', 'cultural', 'traditional', 'sweets'],
        TRUE
    ),
    
    (
        'religious_festivals',
        '{"en": "Coptic Christmas", "ar": "عيد الميلاد القبطي"}',
        '{"en": "Coptic Christmas is celebrated on January 7th according to the Coptic calendar. It is a major holiday for Egypt''s Coptic Christian community, which makes up about 10-15% of the population. The celebration includes special liturgical services, family gatherings, and festive meals. The main Christmas Eve service at St. Mark''s Coptic Orthodox Cathedral in Cairo is often attended by government officials as a symbol of national unity.", "ar": "يُحتفل بعيد الميلاد القبطي في 7 يناير وفقًا للتقويم القبطي. إنه عطلة رئيسية للمجتمع المسيحي القبطي في مصر، الذي يشكل حوالي 10-15٪ من السكان. يتضمن الاحتفال خدمات ليتورجية خاصة وتجمعات عائلية ووجبات احتفالية. غالبًا ما يحضر المسؤولون الحكوميون خدمة ليلة عيد الميلاد الرئيسية في كاتدرائية القديس مرقس القبطية الأرثوذكسية في القاهرة كرمز للوحدة الوطنية."}',
        '2026-01-07',
        '2026-01-07',
        TRUE,
        1,
        7,
        FALSE,
        '{"en": "Celebrated throughout Egypt, with major services at Coptic churches, particularly St. Mark''s Cathedral in Cairo and the Church of the Nativity in Bethlehem.", "ar": "يُحتفل به في جميع أنحاء مصر، مع خدمات رئيسية في الكنائس القبطية، خاصة كاتدرائية القديس مرقس في القاهرة وكنيسة المهد في بيت لحم."}',
        'cairo',
        '{"en": {"name": "St. Mark''s Coptic Orthodox Cathedral", "address": "Abbassia, Cairo"}, "ar": {"name": "كاتدرائية القديس مرقس القبطية الأرثوذكسية", "address": "العباسية، القاهرة"}}',
        '{"en": {"name": "Coptic Orthodox Church", "website": "www.copticchurch.net"}, "ar": {"name": "الكنيسة القبطية الأرثوذكسية", "website": "www.copticchurch.net"}}',
        '{"en": {"fee": "Free", "notes": "Church services are open to all, but arrive early for Christmas Eve mass"}, "ar": {"fee": "مجاني", "notes": "خدمات الكنيسة مفتوحة للجميع، ولكن احضر مبكرًا لقداس ليلة عيد الميلاد"}}',
        '{"en": [
            {"time": "January 6, Evening", "activity": "Christmas Eve mass (starts around 10 PM and continues past midnight)"},
            {"time": "January 7, Morning", "activity": "Christmas Day services"},
            {"time": "January 7, Afternoon", "activity": "Family gatherings and festive meals"}
        ], "ar": [
            {"time": "6 يناير، المساء", "activity": "قداس ليلة عيد الميلاد (يبدأ حوالي الساعة 10 مساءً ويستمر بعد منتصف الليل)"},
            {"time": "7 يناير، الصباح", "activity": "خدمات يوم عيد الميلاد"},
            {"time": "7 يناير، بعد الظهر", "activity": "التجمعات العائلية والوجبات الاحتفالية"}
        ]}',
        '{"en": ["Midnight mass at St. Mark''s Cathedral", "Traditional Coptic hymns", "Festive decorations in Coptic neighborhoods", "Special Christmas meals featuring fatta (rice, bread, and meat dish)", "Exchange of gifts"], "ar": ["قداس منتصف الليل في كاتدرائية القديس مرقس", "التراتيل القبطية التقليدية", "الزينة الاحتفالية في الأحياء القبطية", "وجبات عيد الميلاد الخاصة التي تتضمن الفتة (طبق من الأرز والخبز واللحم)", "تبادل الهدايا"]}',
        '{"en": "The Coptic Church follows the Julian calendar, which is why Christmas is celebrated on January 7th rather than December 25th. The Coptic Orthodox Church is one of the oldest Christian churches in the world, dating back to the 1st century when St. Mark the Evangelist brought Christianity to Egypt. Coptic Christmas celebrations blend ancient Christian traditions with uniquely Egyptian cultural elements.", "ar": "تتبع الكنيسة القبطية التقويم اليولياني، ولهذا السبب يُحتفل بعيد الميلاد في 7 يناير بدلاً من 25 ديسمبر. الكنيسة القبطية الأرثوذكسية هي واحدة من أقدم الكنائس المسيحية في العالم، ويعود تاريخها إلى القرن الأول عندما جلب القديس مرقس الإنجيلي المسيحية إلى مصر. تمزج احتفالات عيد الميلاد القبطي بين التقاليد المسيحية القديمة والعناصر الثقافية المصرية الفريدة."}',
        '{"en": ["Arrive early for Christmas Eve mass as churches fill quickly", "Dress modestly when visiting churches", "Many Coptic Christians fast for 43 days before Christmas (the Nativity Fast)", "Try traditional Coptic Christmas foods like kahk (cookies) and bouri (mullet fish)", "Some areas may have security measures in place for large gatherings"], "ar": ["احضر مبكرًا لقداس ليلة عيد الميلاد حيث تمتلئ الكنائس بسرعة", "ارتدِ ملابس محتشمة عند زيارة الكنائس", "يصوم العديد من المسيحيين الأقباط لمدة 43 يومًا قبل عيد الميلاد (صوم الميلاد)", "جرب أطعمة عيد الميلاد القبطية التقليدية مثل الكحك (البسكويت) والبوري (سمك البوري)", "قد تكون هناك إجراءات أمنية في بعض المناطق للتجمعات الكبيرة"]}',
        '{"main_image": "coptic_christmas.jpg", "gallery": ["st_marks_cathedral.jpg", "christmas_mass.jpg", "coptic_decorations.jpg"]}',
        'https://www.egypt.travel/en/events/coptic-christmas',
        '{"phone": "+20 2 27358761", "email": "info@egypt.travel"}',
        ARRAY['religious', 'christian', 'coptic', 'christmas', 'cultural', 'traditional'],
        TRUE
    ),
    
    (
        'cultural_festivals',
        '{"en": "Cairo International Film Festival", "ar": "مهرجان القاهرة السينمائي الدولي"}',
        '{"en": "The Cairo International Film Festival (CIFF) is one of the oldest and most prestigious film festivals in the Arab world and Africa. Established in 1976, it is the only international film festival in the Arab world and Africa accredited by the International Federation of Film Producers Associations (FIAPF). The festival showcases a wide range of international and Egyptian films, hosts workshops, panel discussions, and masterclasses, and attracts filmmakers, actors, and industry professionals from around the world.", "ar": "مهرجان القاهرة السينمائي الدولي هو أحد أقدم وأرقى المهرجانات السينمائية في العالم العربي وأفريقيا. تأسس عام 1976، وهو المهرجان السينمائي الدولي الوحيد في العالم العربي وأفريقيا المعتمد من قبل الاتحاد الدولي لجمعيات منتجي الأفلام (FIAPF). يعرض المهرجان مجموعة واسعة من الأفلام الدولية والمصرية، ويستضيف ورش عمل ومناقشات وحلقات دراسية، ويجذب صانعي الأفلام والممثلين والمهنيين في الصناعة من جميع أنحاء العالم."}',
        '2025-11-20',
        '2025-11-29',
        TRUE,
        11,
        NULL,
        FALSE,
        '{"en": "The festival takes place at various venues across Cairo, with the Cairo Opera House serving as the main venue for opening and closing ceremonies.", "ar": "يقام المهرجان في أماكن مختلفة في جميع أنحاء القاهرة، مع دار الأوبرا المصرية كمكان رئيسي لحفلات الافتتاح والختام."}',
        'cairo',
        '{"en": {"name": "Cairo Opera House", "address": "El Borg Gezira, Zamalek, Cairo"}, "ar": {"name": "دار الأوبرا المصرية", "address": "البرج، الجزيرة، الزمالك، القاهرة"}}',
        '{"en": {"name": "Cairo International Film Festival", "website": "www.ciff.org.eg"}, "ar": {"name": "مهرجان القاهرة السينمائي الدولي", "website": "www.ciff.org.eg"}}',
        '{"en": {"fee": "Varies by screening", "notes": "Tickets available online and at venue box offices"}, "ar": {"fee": "تختلف حسب العرض", "notes": "التذاكر متاحة عبر الإنترنت وفي شبابيك التذاكر في مكان الحدث"}}',
        '{"en": [
            {"time": "Day 1", "activity": "Opening ceremony and gala screening"},
            {"time": "Days 2-9", "activity": "Film screenings, workshops, and panel discussions"},
            {"time": "Day 10", "activity": "Closing ceremony and awards presentation"}
        ], "ar": [
            {"time": "اليوم الأول", "activity": "حفل الافتتاح والعرض الاحتفالي"},
            {"time": "الأيام 2-9", "activity": "عروض الأفلام وورش العمل والمناقشات"},
            {"time": "اليوم العاشر", "activity": "حفل الختام وتقديم الجوائز"}
        ]}',
        '{"en": ["International competition for feature films", "Arab film competition", "Red carpet events with celebrities", "Masterclasses with renowned filmmakers", "Retrospectives of influential directors", "Focus on emerging talents"], "ar": ["المسابقة الدولية للأفلام الروائية الطويلة", "مسابقة الأفلام العربية", "فعاليات السجادة الحمراء مع المشاهير", "حلقات دراسية مع صانعي أفلام مشهورين", "استعادة أعمال المخرجين المؤثرين", "التركيز على المواهب الناشئة"]}',
        '{"en": "The Cairo International Film Festival was established in 1976, making it one of the oldest film festivals in the Arab world. It has played a significant role in promoting Egyptian and Arab cinema internationally and has hosted numerous world-renowned filmmakers and actors over the decades. The festival has faced challenges, including a brief suspension in the early 2010s due to political unrest, but has since been revitalized and continues to be a major cultural event in the region.", "ar": "تأسس مهرجان القاهرة السينمائي الدولي عام 1976، مما يجعله أحد أقدم المهرجانات السينمائية في العالم العربي. لعب دورًا مهمًا في الترويج للسينما المصرية والعربية دوليًا واستضاف العديد من صانعي الأفلام والممثلين المشهورين عالميًا على مدى العقود. واجه المهرجان تحديات، بما في ذلك تعليق قصير في أوائل العقد الثاني من القرن الحادي والعشرين بسبب الاضطرابات السياسية، لكنه تمت إعادة إحيائه منذ ذلك الحين ولا يزال حدثًا ثقافيًا رئيسيًا في المنطقة."}',
        '{"en": ["Book tickets in advance for popular screenings", "Check the festival website for the full program and schedule", "Arrive early for red carpet events", "Some films may have subtitles in Arabic or English only", "Dress formally for opening and closing ceremonies", "Cairo traffic can be heavy, so plan travel time accordingly"], "ar": ["احجز التذاكر مسبقًا للعروض الشعبية", "تحقق من موقع المهرجان للحصول على البرنامج الكامل والجدول الزمني", "احضر مبكرًا لفعاليات السجادة الحمراء", "قد تحتوي بعض الأفلام على ترجمات باللغة العربية أو الإنجليزية فقط", "ارتدِ ملابس رسمية لحفلات الافتتاح والختام", "يمكن أن تكون حركة المرور في القاهرة كثيفة، لذا خطط لوقت السفر وفقًا لذلك"]}',
        '{"main_image": "cairo_film_festival.jpg", "gallery": ["red_carpet.jpg", "film_screening.jpg", "awards_ceremony.jpg"]}',
        'https://www.ciff.org.eg',
        '{"phone": "+20 2 27383678", "email": "info@ciff.org.eg"}',
        ARRAY['film', 'festival', 'culture', 'arts', 'international', 'cairo'],
        TRUE
    ),
    
    (
        'music_festivals',
        '{"en": "Cairo Jazz Festival", "ar": "مهرجان القاهرة للجاز"}',
        '{"en": "The Cairo Jazz Festival is an annual international music festival that celebrates jazz and related music genres. Founded in 2009, it has grown to become one of the most significant jazz events in the Middle East and Africa. The festival features performances by local and international jazz musicians, workshops, jam sessions, and masterclasses. It aims to promote cultural exchange and introduce Egyptian audiences to diverse jazz traditions while showcasing Egyptian jazz talents to the world.", "ar": "مهرجان القاهرة للجاز هو مهرجان موسيقي دولي سنوي يحتفل بموسيقى الجاز والأنواع الموسيقية ذات الصلة. تأسس عام 2009، ونما ليصبح أحد أهم فعاليات الجاز في الشرق الأوسط وأفريقيا. يتضمن المهرجان عروضًا لموسيقيي الجاز المحليين والدوليين، وورش عمل، وجلسات عزف حر، وحلقات دراسية. يهدف إلى تعزيز التبادل الثقافي وتعريف الجمهور المصري بتقاليد الجاز المتنوعة مع عرض مواهب الجاز المصرية للعالم."}',
        '2025-10-15',
        '2025-10-17',
        TRUE,
        10,
        NULL,
        FALSE,
        '{"en": "The festival is primarily held at the American University in Cairo''s Greek Campus in downtown Cairo, with additional performances at various cultural venues across the city.", "ar": "يقام المهرجان بشكل أساسي في الحرم اليوناني للجامعة الأمريكية بالقاهرة في وسط القاهرة، مع عروض إضافية في أماكن ثقافية مختلفة في جميع أنحاء المدينة."}',
        'cairo',
        '{"en": {"name": "The Greek Campus", "address": "28 Falaki Street, Bab El Louk, Downtown Cairo"}, "ar": {"name": "الحرم اليوناني", "address": "28 شارع فلكي، باب اللوق، وسط البلد، القاهرة"}}',
        '{"en": {"name": "Cairo Jazz Festival", "website": "www.cairojazzfest.com"}, "ar": {"name": "مهرجان القاهرة للجاز", "website": "www.cairojazzfest.com"}}',
        '{"en": {"fee": "Day passes: 200-300 EGP, Festival pass: 500-700 EGP", "notes": "Some workshops and masterclasses may require separate registration"}, "ar": {"fee": "تذاكر اليوم: 200-300 جنيه مصري، تذكرة المهرجان: 500-700 جنيه مصري", "notes": "قد تتطلب بعض ورش العمل والحلقات الدراسية تسجيلًا منفصلًا"}}',
        '{"en": [
            {"time": "Afternoon", "activity": "Workshops and masterclasses"},
            {"time": "Evening", "activity": "Main stage performances"},
            {"time": "Late Night", "activity": "Jam sessions at partner venues"}
        ], "ar": [
            {"time": "بعد الظهر", "activity": "ورش العمل والحلقات الدراسية"},
            {"time": "المساء", "activity": "عروض المسرح الرئيسي"},
            {"time": "وقت متأخر من الليل", "activity": "جلسات العزف الحر في الأماكن الشريكة"}
        ]}',
        '{"en": ["Performances by international jazz stars", "Showcases of Egyptian jazz talents", "Fusion performances blending jazz with traditional Egyptian music", "Interactive workshops for musicians", "Jam sessions", "Children''s jazz program"], "ar": ["عروض من نجوم الجاز الدوليين", "عروض لمواهب الجاز المصرية", "عروض اندماج تمزج الجاز بالموسيقى المصرية التقليدية", "ورش عمل تفاعلية للموسيقيين", "جلسات عزف حر", "برنامج جاز للأطفال"]}',
        '{"en": "The Cairo Jazz Festival was founded in 2009 by Egyptian jazz musician Amro Salah with the aim of creating a platform for jazz music in Egypt and the Middle East. Despite the challenges of organizing an international music festival in a region where jazz is not mainstream, the festival has grown steadily and has featured renowned international artists alongside emerging local talents. It has become an important cultural bridge between Egypt and the international jazz community.", "ar": "تأسس مهرجان القاهرة للجاز عام 2009 على يد موسيقي الجاز المصري عمرو صلاح بهدف إنشاء منصة لموسيقى الجاز في مصر والشرق الأوسط. على الرغم من تحديات تنظيم مهرجان موسيقي دولي في منطقة لا تعتبر فيها موسيقى الجاز سائدة، نما المهرجان باطراد وضم فنانين دوليين مشهورين إلى جانب المواهب المحلية الناشئة. أصبح جسرًا ثقافيًا مهمًا بين مصر ومجتمع الجاز الدولي."}',
        '{"en": ["Purchase tickets in advance as popular performances sell out quickly", "Check the festival website for the full program and schedule", "The Greek Campus has multiple stages, so plan your schedule accordingly", "Food and beverages are available at the venue", "Downtown Cairo can be crowded, so consider using ride-sharing apps or taxis", "Bring a light jacket for evening performances as it can get cool in October"], "ar": ["اشترِ التذاكر مسبقًا حيث تنفد العروض الشعبية بسرعة", "تحقق من موقع المهرجان للحصول على البرنامج الكامل والجدول الزمني", "يحتوي الحرم اليوناني على مسارح متعددة، لذا خطط لجدولك الزمني وفقًا لذلك", "الطعام والمشروبات متوفرة في المكان", "يمكن أن يكون وسط القاهرة مزدحمًا، لذا فكر في استخدام تطبيقات مشاركة الركوب أو سيارات الأجرة", "أحضر سترة خفيفة للعروض المسائية حيث يمكن أن يصبح الجو باردًا في أكتوبر"]}',
        '{"main_image": "cairo_jazz_festival.jpg", "gallery": ["jazz_performance.jpg", "audience.jpg", "workshop.jpg"]}',
        'https://www.cairojazzfest.com',
        '{"phone": "+20 2 25984190", "email": "info@cairojazzfest.com"}',
        ARRAY['music', 'jazz', 'festival', 'culture', 'arts', 'cairo'],
        TRUE
    );

-- Verify the insertion
SELECT COUNT(*) AS new_events_count FROM events_festivals;

COMMIT;
