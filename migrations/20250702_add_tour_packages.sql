-- Migration: Add Tour Packages
-- Date: 2025-07-02
-- Description: Add comprehensive tour packages to ensure better coverage

BEGIN;

-- Add classic Egypt tours
INSERT INTO tour_packages (
    category_id, 
    name, 
    description, 
    duration_days, 
    price_range, 
    included_services, 
    excluded_services, 
    itinerary, 
    destinations, 
    attractions, 
    accommodations, 
    transportation_types, 
    min_group_size, 
    max_group_size, 
    difficulty_level, 
    accessibility_info, 
    seasonal_info, 
    booking_info, 
    cancellation_policy, 
    reviews, 
    rating, 
    images, 
    tags, 
    is_featured, 
    is_private
) VALUES
    (
        'classic_tours',
        '{"en": "Cairo and Pyramids Explorer", "ar": "مستكشف القاهرة والأهرامات"}',
        '{"en": "A comprehensive 4-day tour of Cairo and the Pyramids, covering the most iconic historical sites of Egypt''s capital. Visit the Great Pyramids of Giza, the Sphinx, the Egyptian Museum, and explore Islamic and Coptic Cairo.", "ar": "جولة شاملة لمدة 4 أيام في القاهرة والأهرامات، تغطي أشهر المواقع التاريخية في عاصمة مصر. قم بزيارة أهرامات الجيزة العظيمة، وأبو الهول، والمتحف المصري، واستكشف القاهرة الإسلامية والقبطية."}',
        4,
        '{"USD": {"min": 450, "max": 650}, "EGP": {"min": 14000, "max": 20000}}',
        '{"en": ["Hotel accommodation (4-star)", "Daily breakfast", "Private guided tours", "All entrance fees", "Airport transfers", "Transportation in air-conditioned vehicle"], "ar": ["إقامة فندقية (4 نجوم)", "إفطار يومي", "جولات خاصة مع مرشد", "جميع رسوم الدخول", "النقل من وإلى المطار", "المواصلات في مركبة مكيفة"]}',
        '{"en": ["International airfare", "Visa fees", "Travel insurance", "Lunches and dinners", "Personal expenses", "Optional tours"], "ar": ["تذاكر الطيران الدولية", "رسوم التأشيرة", "تأمين السفر", "وجبات الغداء والعشاء", "النفقات الشخصية", "الجولات الاختيارية"]}',
        '{"en": [
            {"day": 1, "title": "Arrival in Cairo", "description": "Airport pickup and transfer to your hotel. Evening at leisure."},
            {"day": 2, "title": "Pyramids and Sphinx", "description": "Full day tour of the Giza Plateau, including the Great Pyramids, Sphinx, and Solar Boat Museum."},
            {"day": 3, "title": "Egyptian Museum and Old Cairo", "description": "Visit the Egyptian Museum, Citadel of Saladin, Alabaster Mosque, and Khan el-Khalili Bazaar."},
            {"day": 4, "title": "Departure", "description": "Breakfast at hotel, then transfer to Cairo International Airport for departure."}
        ], "ar": [
            {"day": 1, "title": "الوصول إلى القاهرة", "description": "الاستقبال من المطار والنقل إلى الفندق. المساء حر."},
            {"day": 2, "title": "الأهرامات وأبو الهول", "description": "جولة ليوم كامل في هضبة الجيزة، بما في ذلك الأهرامات العظيمة، وأبو الهول، ومتحف مركب الشمس."},
            {"day": 3, "title": "المتحف المصري والقاهرة القديمة", "description": "زيارة المتحف المصري، وقلعة صلاح الدين، والجامع الألباستر، وسوق خان الخليلي."},
            {"day": 4, "title": "المغادرة", "description": "الإفطار في الفندق، ثم النقل إلى مطار القاهرة الدولي للمغادرة."}
        ]}',
        ARRAY['cairo', 'giza'],
        ARRAY['great_pyramid_of_giza', 'sphinx', 'egyptian_museum', 'khan_el_khalili', 'citadel_of_saladin'],
        ARRAY['cairo_marriott', 'four_seasons_cairo'],
        ARRAY['private_car', 'walking'],
        2,
        15,
        'easy',
        '{"en": {"wheelchair_accessible": true, "elderly_friendly": true, "notes": "Some sites require walking on uneven terrain."}, "ar": {"wheelchair_accessible": true, "elderly_friendly": true, "notes": "بعض المواقع تتطلب المشي على أرض غير مستوية."}}',
        '{"en": {"best_time": "October to April", "notes": "Summer months can be extremely hot."}, "ar": {"best_time": "أكتوبر إلى أبريل", "notes": "يمكن أن تكون أشهر الصيف شديدة الحرارة."}}',
        '{"en": {"deposit": "30%", "payment_methods": ["Credit Card", "Bank Transfer"], "booking_deadline": "7 days before arrival"}, "ar": {"deposit": "30%", "payment_methods": ["بطاقة الائتمان", "التحويل المصرفي"], "booking_deadline": "7 أيام قبل الوصول"}}',
        '{"en": {"free_cancellation": "Up to 14 days before arrival", "partial_refund": "50% refund up to 7 days before arrival", "no_refund": "Less than 7 days before arrival"}, "ar": {"free_cancellation": "حتى 14 يومًا قبل الوصول", "partial_refund": "استرداد 50٪ حتى 7 أيام قبل الوصول", "no_refund": "أقل من 7 أيام قبل الوصول"}}',
        '{"en": [
            {"name": "John Smith", "rating": 5, "comment": "Excellent tour! Our guide was knowledgeable and the accommodations were comfortable."},
            {"name": "Sarah Johnson", "rating": 4, "comment": "Great experience overall. The pyramids were breathtaking."}
        ], "ar": [
            {"name": "جون سميث", "rating": 5, "comment": "جولة ممتازة! كان مرشدنا على دراية وكانت أماكن الإقامة مريحة."},
            {"name": "سارة جونسون", "rating": 4, "comment": "تجربة رائعة بشكل عام. كانت الأهرامات مذهلة."}
        ]}',
        4.5,
        '{"main_image": "cairo_pyramids_tour.jpg", "gallery": ["giza_pyramids.jpg", "egyptian_museum.jpg", "khan_el_khalili.jpg"]}',
        ARRAY['pyramids', 'cairo', 'history', 'culture', 'short trip'],
        TRUE,
        FALSE
    ),
    
    (
        'nile_cruises',
        '{"en": "Luxury Nile Cruise: Luxor to Aswan", "ar": "رحلة نيلية فاخرة: الأقصر إلى أسوان"}',
        '{"en": "Experience the magic of the Nile on this 5-day luxury cruise from Luxor to Aswan. Visit the magnificent temples and tombs along the river, including Karnak, Luxor Temple, Valley of the Kings, Temple of Hatshepsut, Edfu, Kom Ombo, and Philae Temple.", "ar": "استمتع بسحر النيل في هذه الرحلة البحرية الفاخرة لمدة 5 أيام من الأقصر إلى أسوان. قم بزيارة المعابد والمقابر الرائعة على طول النهر، بما في ذلك الكرنك، ومعبد الأقصر، ووادي الملوك، ومعبد حتشبسوت، وإدفو، وكوم أمبو، ومعبد فيلة."}',
        5,
        '{"USD": {"min": 800, "max": 1200}, "EGP": {"min": 25000, "max": 37000}}',
        '{"en": ["4 nights accommodation on 5-star Nile cruise", "All meals (breakfast, lunch, dinner)", "Guided tours to all sites", "All entrance fees", "Airport/hotel transfers", "English-speaking Egyptologist guide"], "ar": ["إقامة 4 ليالٍ على رحلة نيلية 5 نجوم", "جميع الوجبات (الإفطار والغداء والعشاء)", "جولات مع مرشد إلى جميع المواقع", "جميع رسوم الدخول", "النقل من وإلى المطار/الفندق", "مرشد مصريات يتحدث الإنجليزية"]}',
        '{"en": ["International and domestic airfare", "Visa fees", "Travel insurance", "Beverages", "Personal expenses", "Optional tours", "Gratuities"], "ar": ["تذاكر الطيران الدولية والداخلية", "رسوم التأشيرة", "تأمين السفر", "المشروبات", "النفقات الشخصية", "الجولات الاختيارية", "الإكراميات"]}',
        '{"en": [
            {"day": 1, "title": "Embarkation in Luxor", "description": "Check-in to your Nile cruise. Afternoon visit to Karnak and Luxor Temples."},
            {"day": 2, "title": "West Bank of Luxor", "description": "Visit the Valley of the Kings, Temple of Hatshepsut, and Colossi of Memnon. Sail to Edfu."},
            {"day": 3, "title": "Edfu and Kom Ombo", "description": "Morning visit to Edfu Temple. Afternoon visit to Kom Ombo Temple. Sail to Aswan."},
            {"day": 4, "title": "Aswan", "description": "Visit the High Dam, Unfinished Obelisk, and Philae Temple. Optional afternoon felucca ride around Elephantine Island."},
            {"day": 5, "title": "Disembarkation", "description": "Breakfast on board, then disembarkation and transfer to Aswan airport or hotel."}
        ], "ar": [
            {"day": 1, "title": "الصعود في الأقصر", "description": "تسجيل الوصول إلى رحلتك النيلية. زيارة بعد الظهر لمعابد الكرنك والأقصر."},
            {"day": 2, "title": "الضفة الغربية للأقصر", "description": "زيارة وادي الملوك، ومعبد حتشبسوت، وتمثالي ممنون. الإبحار إلى إدفو."},
            {"day": 3, "title": "إدفو وكوم أمبو", "description": "زيارة صباحية لمعبد إدفو. زيارة بعد الظهر لمعبد كوم أمبو. الإبحار إلى أسوان."},
            {"day": 4, "title": "أسوان", "description": "زيارة السد العالي، والمسلة غير المكتملة، ومعبد فيلة. رحلة اختيارية بعد الظهر بالفلوكة حول جزيرة إلفنتين."},
            {"day": 5, "title": "النزول من السفينة", "description": "الإفطار على متن السفينة، ثم النزول والنقل إلى مطار أسوان أو الفندق."}
        ]}',
        ARRAY['luxor', 'edfu', 'kom_ombo', 'aswan'],
        ARRAY['karnak_temple', 'luxor_temple', 'valley_of_the_kings', 'hatshepsut_temple', 'edfu_temple', 'kom_ombo_temple', 'philae_temple', 'aswan_high_dam'],
        ARRAY['nile_cruise_ship'],
        ARRAY['cruise_ship', 'private_car'],
        2,
        40,
        'easy',
        '{"en": {"wheelchair_accessible": true, "elderly_friendly": true, "notes": "Cruise ship has elevator, but some temples have limited accessibility."}, "ar": {"wheelchair_accessible": true, "elderly_friendly": true, "notes": "السفينة بها مصعد، لكن بعض المعابد لها إمكانية وصول محدودة."}}',
        '{"en": {"best_time": "October to April", "notes": "Summer months can be extremely hot, but the cruise ships are air-conditioned."}, "ar": {"best_time": "أكتوبر إلى أبريل", "notes": "يمكن أن تكون أشهر الصيف شديدة الحرارة، ولكن سفن الرحلات البحرية مكيفة الهواء."}}',
        '{"en": {"deposit": "50%", "payment_methods": ["Credit Card", "Bank Transfer"], "booking_deadline": "14 days before departure"}, "ar": {"deposit": "50%", "payment_methods": ["بطاقة الائتمان", "التحويل المصرفي"], "booking_deadline": "14 يومًا قبل المغادرة"}}',
        '{"en": {"free_cancellation": "Up to 30 days before departure", "partial_refund": "50% refund up to 14 days before departure", "no_refund": "Less than 14 days before departure"}, "ar": {"free_cancellation": "حتى 30 يومًا قبل المغادرة", "partial_refund": "استرداد 50٪ حتى 14 يومًا قبل المغادرة", "no_refund": "أقل من 14 يومًا قبل المغادرة"}}',
        '{"en": [
            {"name": "Michael Brown", "rating": 5, "comment": "The cruise was amazing! The ship was luxurious and the staff were attentive. The temples along the Nile are incredible."},
            {"name": "Emma Wilson", "rating": 5, "comment": "One of the best travel experiences of my life. The food was excellent and the guided tours were informative."}
        ], "ar": [
            {"name": "مايكل براون", "rating": 5, "comment": "كانت الرحلة البحرية مذهلة! كانت السفينة فاخرة وكان الطاقم متيقظًا. المعابد على طول النيل مذهلة."},
            {"name": "إيما ويلسون", "rating": 5, "comment": "واحدة من أفضل تجارب السفر في حياتي. كان الطعام ممتازًا وكانت الجولات المصحوبة بمرشدين مفيدة."}
        ]}',
        5.0,
        '{"main_image": "nile_cruise.jpg", "gallery": ["luxor_temple_night.jpg", "karnak_temple.jpg", "valley_of_kings.jpg", "cruise_ship_deck.jpg"]}',
        ARRAY['nile', 'cruise', 'luxor', 'aswan', 'temples', 'luxury'],
        TRUE,
        FALSE
    ),
    
    (
        'beach_holidays',
        '{"en": "Red Sea Diving Adventure: Sharm El Sheikh", "ar": "مغامرة الغوص في البحر الأحمر: شرم الشيخ"}',
        '{"en": "A 7-day diving adventure in Sharm El Sheikh, exploring the magnificent coral reefs of the Red Sea. This package includes daily diving trips to world-famous dive sites, including Ras Mohammed National Park, Tiran Island, and the SS Thistlegorm wreck.", "ar": "مغامرة غوص لمدة 7 أيام في شرم الشيخ، لاستكشاف الشعاب المرجانية الرائعة في البحر الأحمر. تتضمن هذه الباقة رحلات غوص يومية إلى مواقع غوص مشهورة عالميًا، بما في ذلك محمية رأس محمد الوطنية، وجزيرة تيران، وحطام السفينة ثيستلغورم."}',
        7,
        '{"USD": {"min": 900, "max": 1300}, "EGP": {"min": 28000, "max": 40000}}',
        '{"en": ["6 nights accommodation in 4-star beach resort", "Daily breakfast and dinner", "5 days of 2-tank diving (10 dives total)", "All diving equipment rental", "Professional dive guides", "Airport transfers", "Transportation to dive sites"], "ar": ["إقامة 6 ليالٍ في منتجع شاطئي 4 نجوم", "الإفطار والعشاء يوميًا", "5 أيام من الغوص بخزانين (10 غطسات إجمالاً)", "تأجير جميع معدات الغوص", "مرشدي غوص محترفين", "النقل من وإلى المطار", "المواصلات إلى مواقع الغوص"]}',
        '{"en": ["International and domestic airfare", "Visa fees", "Travel insurance", "Lunches", "Personal expenses", "Optional tours", "Dive insurance (mandatory)", "National park fees"], "ar": ["تذاكر الطيران الدولية والداخلية", "رسوم التأشيرة", "تأمين السفر", "وجبات الغداء", "النفقات الشخصية", "الجولات الاختيارية", "تأمين الغوص (إلزامي)", "رسوم الحديقة الوطنية"]}',
        '{"en": [
            {"day": 1, "title": "Arrival in Sharm El Sheikh", "description": "Airport pickup and transfer to your beach resort. Welcome briefing and equipment check."},
            {"day": 2, "title": "Local Dive Sites", "description": "Two dives at local sites (Ras Nasrani and Near Garden) to check buoyancy and equipment."},
            {"day": 3, "title": "Ras Mohammed National Park", "description": "Full day trip with two dives at Shark Reef and Yolanda Reef in Ras Mohammed National Park."},
            {"day": 4, "title": "Tiran Island", "description": "Full day trip with two dives around Tiran Island, exploring Jackson Reef and Thomas Reef."},
            {"day": 5, "title": "SS Thistlegorm Wreck", "description": "Full day trip to the famous WWII shipwreck SS Thistlegorm with two dives."},
            {"day": 6, "title": "Dunraven Wreck and Ras Mohammed", "description": "Full day trip with a dive at Dunraven wreck and a second dive at Ras Mohammed."},
            {"day": 7, "title": "Departure", "description": "Breakfast at resort, then transfer to Sharm El Sheikh International Airport for departure."}
        ], "ar": [
            {"day": 1, "title": "الوصول إلى شرم الشيخ", "description": "الاستقبال من المطار والنقل إلى منتجعك الشاطئي. جلسة إحاطة ترحيبية وفحص المعدات."},
            {"day": 2, "title": "مواقع الغوص المحلية", "description": "غطستان في المواقع المحلية (رأس نصراني والحديقة القريبة) للتحقق من الطفو والمعدات."},
            {"day": 3, "title": "محمية رأس محمد الوطنية", "description": "رحلة ليوم كامل مع غطستين في شعاب القرش وشعاب يولاندا في محمية رأس محمد الوطنية."},
            {"day": 4, "title": "جزيرة تيران", "description": "رحلة ليوم كامل مع غطستين حول جزيرة تيران، لاستكشاف شعاب جاكسون وشعاب توماس."},
            {"day": 5, "title": "حطام السفينة ثيستلغورم", "description": "رحلة ليوم كامل إلى حطام السفينة الشهير من الحرب العالمية الثانية ثيستلغورم مع غطستين."},
            {"day": 6, "title": "حطام دنرافن ورأس محمد", "description": "رحلة ليوم كامل مع غطسة في حطام دنرافن وغطسة ثانية في رأس محمد."},
            {"day": 7, "title": "المغادرة", "description": "الإفطار في المنتجع، ثم النقل إلى مطار شرم الشيخ الدولي للمغادرة."}
        ]}',
        ARRAY['sharm_el_sheikh', 'ras_mohammed', 'tiran_island'],
        ARRAY['ras_mohammed_national_park', 'tiran_island', 'ss_thistlegorm_wreck'],
        ARRAY['sharm_el_sheikh_resort'],
        ARRAY['dive_boat', 'private_car'],
        4,
        16,
        'moderate',
        '{"en": {"wheelchair_accessible": false, "elderly_friendly": false, "notes": "Participants must be certified divers with at least Open Water certification and 20+ logged dives."}, "ar": {"wheelchair_accessible": false, "elderly_friendly": false, "notes": "يجب أن يكون المشاركون غواصين معتمدين بشهادة المياه المفتوحة على الأقل و20+ غطسة مسجلة."}}',
        '{"en": {"best_time": "Year-round, with best visibility from April to November", "notes": "Water temperature ranges from 20°C in winter to 28°C in summer."}, "ar": {"best_time": "على مدار العام، مع أفضل رؤية من أبريل إلى نوفمبر", "notes": "تتراوح درجة حرارة الماء من 20 درجة مئوية في الشتاء إلى 28 درجة مئوية في الصيف."}}',
        '{"en": {"deposit": "30%", "payment_methods": ["Credit Card", "Bank Transfer"], "booking_deadline": "14 days before arrival"}, "ar": {"deposit": "30%", "payment_methods": ["بطاقة الائتمان", "التحويل المصرفي"], "booking_deadline": "14 يومًا قبل الوصول"}}',
        '{"en": {"free_cancellation": "Up to 30 days before arrival", "partial_refund": "50% refund up to 14 days before arrival", "no_refund": "Less than 14 days before arrival"}, "ar": {"free_cancellation": "حتى 30 يومًا قبل الوصول", "partial_refund": "استرداد 50٪ حتى 14 يومًا قبل الوصول", "no_refund": "أقل من 14 يومًا قبل الوصول"}}',
        '{"en": [
            {"name": "David Thompson", "rating": 5, "comment": "Incredible diving experience! The reefs are pristine and the dive guides were extremely professional."},
            {"name": "Lisa Chen", "rating": 4, "comment": "Great diving package. The Thistlegorm wreck was the highlight of the trip."}
        ], "ar": [
            {"name": "ديفيد طومسون", "rating": 5, "comment": "تجربة غوص لا تصدق! الشعاب المرجانية نقية ومرشدو الغوص كانوا محترفين للغاية."},
            {"name": "ليزا تشن", "rating": 4, "comment": "باقة غوص رائعة. كان حطام ثيستلغورم هو الحدث البارز في الرحلة."}
        ]}',
        4.8,
        '{"main_image": "red_sea_diving.jpg", "gallery": ["coral_reef.jpg", "thistlegorm_wreck.jpg", "diving_boat.jpg", "sharm_resort.jpg"]}',
        ARRAY['diving', 'red sea', 'marine life', 'coral reefs', 'wreck diving', 'sharm el sheikh'],
        TRUE,
        FALSE
    );

-- Verify the insertion
SELECT COUNT(*) AS new_tour_packages_count FROM tour_packages;

COMMIT;
