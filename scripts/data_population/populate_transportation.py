# populate_transportation.py
import json
import os
from datetime import datetime

# Ensure directories exist
def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

ensure_dir("./data/transportation")

# Define transportation data
transportation = [
    {
        "id": "domestic_flights",
        "name": {
            "en": "Domestic Flights in Egypt",
            "ar": "الرحلات الداخلية في مصر"
        },
        "type": "air_travel",
        "description": {
            "en": "Domestic flights are one of the fastest ways to travel between major cities in Egypt. The national carrier EgyptAir and other airlines operate regular flights connecting Cairo with tourist destinations like Luxor, Aswan, Sharm El-Sheikh, and Hurghada. Flights are particularly useful for covering longer distances such as Cairo to Aswan, saving travelers hours of travel time compared to land transportation.",
            "ar": "الرحلات الداخلية هي من أسرع الطرق للسفر بين المدن الرئيسية في مصر. تقوم شركة مصر للطيران الوطنية وشركات طيران أخرى بتشغيل رحلات منتظمة تربط القاهرة بالوجهات السياحية مثل الأقصر وأسوان وشرم الشيخ والغردقة. الرحلات الجوية مفيدة بشكل خاص لتغطية المسافات الأطول مثل القاهرة إلى أسوان، مما يوفر ساعات من وقت السفر مقارنة بالنقل البري."
        },
        "practical_info": {
            "operating_hours": "Varies by route and airline, typically 6:00 AM - 11:00 PM",
            "fares": {
                "cairo_luxor": "1,200-2,500 EGP one-way",
                "cairo_aswan": "1,500-3,000 EGP one-way",
                "cairo_sharm_el_sheikh": "1,300-2,800 EGP one-way",
                "cairo_hurghada": "1,200-2,600 EGP one-way"
            },
            "booking_info": {
                "en": "Flights can be booked directly through airline websites, travel agencies, or online booking platforms. For EgyptAir, the national carrier, bookings can be made at www.egyptair.com or through their mobile app. It's advisable to book in advance, especially during peak tourist seasons (October-April) and holidays.",
                "ar": "يمكن حجز الرحلات الجوية مباشرة من خلال مواقع شركات الطيران أو وكالات السفر أو منصات الحجز عبر الإنترنت. بالنسبة لمصر للطيران، الناقل الوطني، يمكن إجراء الحجوزات على www.egyptair.com أو من خلال تطبيق الهاتف المحمول الخاص بهم. يُنصح بالحجز مسبقًا، خاصة خلال مواسم الذروة السياحية (أكتوبر-أبريل) والعطلات."
            },
            "travel_duration": {
                "cairo_luxor": "1 hour",
                "cairo_aswan": "1.5 hours",
                "cairo_sharm_el_sheikh": "1 hour",
                "cairo_hurghada": "1 hour"
            },
            "airports": [
                {
                    "name": "Cairo International Airport",
                    "code": "CAI",
                    "location": "Cairo"
                },
                {
                    "name": "Luxor International Airport",
                    "code": "LXR",
                    "location": "Luxor"
                },
                {
                    "name": "Aswan International Airport",
                    "code": "ASW",
                    "location": "Aswan"
                },
                {
                    "name": "Sharm El-Sheikh International Airport",
                    "code": "SSH",
                    "location": "Sharm El-Sheikh"
                },
                {
                    "name": "Hurghada International Airport",
                    "code": "HRG",
                    "location": "Hurghada"
                }
            ],
            "airlines": [
                "EgyptAir",
                "Nile Air",
                "Air Cairo"
            ]
        },
        "traveler_tips": {
            "en": "Arrive at least 2 hours before domestic flights. Bring your passport for identification, even for domestic travel. Be aware that flight schedules may change during Ramadan. Consider joining the EgyptAir frequent flyer program if you plan to take multiple domestic flights. Check baggage allowance as it may differ from international standards. Some routes may have limited flight options outside of peak tourist season.",
            "ar": "احضر قبل ساعتين على الأقل من الرحلات الداخلية. أحضر جواز سفرك للتعريف، حتى للسفر الداخلي. كن على علم بأن جداول الرحلات قد تتغير خلال شهر رمضان. فكر في الانضمام إلى برنامج المسافر الدائم من مصر للطيران إذا كنت تخطط لأخذ رحلات داخلية متعددة. تحقق من السماح بالأمتعة لأنه قد يختلف عن المعايير الدولية. قد يكون لبعض المسارات خيارات محدودة للرحلات خارج موسم الذروة السياحية."
        },
        "images": [
            "egyptair_plane.jpg",
            "cairo_airport.jpg",
            "luxor_airport.jpg",
            "domestic_flight_map.jpg"
        ],
        "tags": ["air travel", "domestic flights", "transportation", "EgyptAir", "airports"],
        "last_updated": datetime.now().isoformat()
    },
    {
        "id": "nile_cruises",
        "name": {
            "en": "Nile Cruises",
            "ar": "رحلات النيل النهرية"
        },
        "type": "water_transport",
        "description": {
            "en": "Nile cruises are one of the most popular and scenic ways to travel between Luxor and Aswan while experiencing the majesty of ancient Egypt. These floating hotels allow travelers to visit multiple historical sites along the Nile River while enjoying comfortable accommodations, meals, and entertainment on board. Cruises typically range from 3 to 7 nights, with most ships offering various categories of cabins, restaurants, swimming pools, and evening entertainment programs.",
            "ar": "رحلات النيل النهرية هي من أكثر الطرق شعبية وجمالاً للسفر بين الأقصر وأسوان مع تجربة عظمة مصر القديمة. تسمح هذه الفنادق العائمة للمسافرين بزيارة مواقع تاريخية متعددة على طول نهر النيل مع الاستمتاع بأماكن إقامة مريحة ووجبات وترفيه على متن السفينة. تتراوح الرحلات عادة من 3 إلى 7 ليالٍ، مع تقديم معظم السفن لفئات مختلفة من الكبائن والمطاعم وحمامات السباحة وبرامج الترفيه المسائية."
        },
        "practical_info": {
            "operating_schedule": "Year-round, with peak season from October to April",
            "fares": {
                "standard": "1,000-2,000 EGP per night per person",
                "deluxe": "2,000-3,500 EGP per night per person",
                "luxury": "3,500+ EGP per night per person"
            },
            "booking_info": {
                "en": "Nile cruises can be booked through travel agencies, online booking platforms, or directly with cruise companies. Booking well in advance (3-6 months) is recommended during peak season. Most cruises include full board accommodation, guided tours to attractions, and some entertainment. Prices vary depending on the season, cruise duration, ship category, and cabin type.",
                "ar": "يمكن حجز رحلات النيل النهرية من خلال وكالات السفر أو منصات الحجز عبر الإنترنت أو مباشرة مع شركات الرحلات البحرية. يوصى بالحجز قبل وقت طويل (3-6 أشهر) خلال موسم الذروة. تشمل معظم الرحلات البحرية إقامة كاملة مع وجبات وجولات بمرشدين إلى المعالم السياحية وبعض الترفيه. تختلف الأسعار حسب الموسم ومدة الرحلة وفئة السفينة ونوع الكابينة."
            },
            "routes": [
                {
                    "name": "Luxor to Aswan",
                    "duration": "3-4 nights",
                    "stops": ["Esna", "Edfu", "Kom Ombo"]
                },
                {
                    "name": "Aswan to Luxor",
                    "duration": "3-4 nights",
                    "stops": ["Kom Ombo", "Edfu", "Esna"]
                },
                {
                    "name": "Luxor to Dendera and back",
                    "duration": "1-2 nights",
                    "stops": ["Dendera"]
                },
                {
                    "name": "Cairo to Aswan",
                    "duration": "11-14 nights",
                    "stops": ["Beni Suef", "Minya", "Asyut", "Sohag", "Qena", "Luxor", "Edfu", "Kom Ombo"]
                }
            ],
            "popular_attractions": [
                "Karnak Temple",
                "Luxor Temple",
                "Valley of the Kings",
                "Temple of Hatshepsut",
                "Temple of Horus at Edfu",
                "Temple of Kom Ombo",
                "Philae Temple",
                "Aswan High Dam",
                "Unfinished Obelisk"
            ]
        },
        "traveler_tips": {
            "en": "Book at least 3 months in advance during peak season. Consider the direction of your cruise (upstream requires more sailing time than downstream). Pack layers for evening temperatures on the river, which can be cooler. Bring sun protection, comfortable walking shoes, and modest clothing for temple visits. Tipping is customary for cruise staff and guides (budget around 10% of your cruise cost). Most cruises include guided tours, but entrance fees to archaeological sites are sometimes extra. Check if WiFi is available on your cruise, as connectivity varies by ship.",
            "ar": "احجز قبل 3 أشهر على الأقل خلال موسم الذروة. ضع في اعتبارك اتجاه رحلتك البحرية (التيار الصاعد يتطلب وقت إبحار أكثر من التيار الهابط). قم بإحضار طبقات للحرارة المسائية على النهر، والتي يمكن أن تكون أكثر برودة. أحضر واقي من الشمس وأحذية مريحة للمشي وملابس محتشمة لزيارات المعابد. من المعتاد إعطاء البقشيش لطاقم الرحلة والمرشدين (ميزانية حوالي 10٪ من تكلفة رحلتك). تشمل معظم الرحلات جولات بمرشدين، ولكن رسوم الدخول إلى المواقع الأثرية تكون أحيانًا إضافية. تحقق مما إذا كانت خدمة الواي فاي متوفرة في رحلتك البحرية، حيث يختلف الاتصال حسب السفينة."
        },
        "images": [
            "nile_cruise_ship.jpg",
            "nile_cruise_deck.jpg",
            "nile_cruise_cabin.jpg",
            "nile_cruise_dining.jpg",
            "nile_cruise_sunset.jpg"
        ],
        "tags": ["Nile", "cruise", "river travel", "Luxor", "Aswan", "water transport", "tourism"],
        "last_updated": datetime.now().isoformat()
    },
    {
        "id": "cairo_metro",
        "name": {
            "en": "Cairo Metro",
            "ar": "مترو القاهرة"
        },
        "type": "public_transport",
        "description": {
            "en": "The Cairo Metro is the first underground metro system in Africa and the Arab world. It serves as the backbone of public transportation in Greater Cairo, connecting various districts and suburbs of the sprawling metropolis. The system currently operates three lines with over 70 stations, serving approximately 4 million passengers daily. The metro is an efficient, affordable, and relatively quick way to navigate Cairo's notorious traffic congestion.",
            "ar": "مترو القاهرة هو أول نظام مترو تحت الأرض في أفريقيا والعالم العربي. يعمل كعمود فقري للنقل العام في القاهرة الكبرى، ويربط مختلف أحياء وضواحي العاصمة المترامية الأطراف. يعمل النظام حاليًا ثلاثة خطوط مع أكثر من 70 محطة، ويخدم حوالي 4 ملايين راكب يوميًا. المترو هو وسيلة فعالة وبأسعار معقولة وسريعة نسبيًا للتنقل عبر ازدحام المرور الشهير في القاهرة."
        },
        "practical_info": {
            "operating_hours": "5:00 AM - 1:00 AM daily",
            "fares": {
                "standard_ticket": "5-10 EGP (depending on number of stations)",
                "elderly_student_discount": "Available with proper ID"
            },
            "lines": [
                {
                    "name": "Line 1 (Blue Line)",
                    "route": "Helwan to New El-Marg",
                    "key_stations": ["Sadat (Tahrir Square)", "Giza", "Helwan", "New El-Marg"]
                },
                {
                    "name": "Line 2 (Red Line)",
                    "route": "Shobra El-Kheima to El-Mounib",
                    "key_stations": ["Sadat (Tahrir Square)", "Ramses", "Cairo University", "El-Mounib"]
                },
                {
                    "name": "Line 3 (Green Line)",
                    "route": "Adly Mansour to Kit Kat (partially completed)",
                    "key_stations": ["Adly Mansour", "Cairo Stadium", "Abbassia", "Attaba", "Kit Kat"]
                }
            ],
            "future_expansion": {
                "en": "The Cairo Metro continues to expand with Line 3 extensions under construction and plans for additional lines (Line 4, 5, and 6) to further connect Cairo's neighborhoods and suburbs.",
                "ar": "يستمر مترو القاهرة في التوسع مع امتدادات الخط 3 قيد الإنشاء وخطط لخطوط إضافية (الخط 4 و5 و6) لربط أحياء وضواحي القاهرة بشكل أكبر."
            }
        },
        "traveler_tips": {
            "en": "Purchase tickets at station booths (cash only). The first two cars of each train are reserved for women (though women can ride in any car). Metro can get extremely crowded during rush hours (8-10 AM and 3-5 PM). Keep your ticket until exiting as it's required to leave the station. Be mindful of your belongings in crowded cars. Download the Cairo Metro app for maps and schedules. The metro is the fastest way to cross the city during traffic hours. Some stations connect to important tourist attractions like the Egyptian Museum (Sadat Station) and Cairo University (Cairo University Station).",
            "ar": "شراء التذاكر من أكشاك المحطة (نقدًا فقط). العربتان الأوليان من كل قطار مخصصتان للنساء (على الرغم من أن النساء يمكنهن الركوب في أي عربة). يمكن أن يصبح المترو مزدحمًا للغاية خلال ساعات الذروة (8-10 صباحًا و3-5 مساءً). احتفظ بتذكرتك حتى الخروج لأنها مطلوبة لمغادرة المحطة. انتبه لمتعلقاتك في العربات المزدحمة. قم بتنزيل تطبيق مترو القاهرة للخرائط والجداول الزمنية. المترو هو أسرع وسيلة لعبور المدينة خلال ساعات الازدحام. تتصل بعض المحطات بمعالم سياحية مهمة مثل المتحف المصري (محطة السادات) وجامعة القاهرة (محطة جامعة القاهرة)."
        },
        "images": [
            "cairo_metro_train.jpg",
            "cairo_metro_station.jpg",
            "cairo_metro_map.jpg",
            "cairo_metro_ticket.jpg"
        ],
        "tags": ["public transport", "metro", "Cairo", "subway", "urban travel", "budget travel"],
        "last_updated": datetime.now().isoformat()
    }
]

# Save transportation data to JSON files
for transport in transportation:
    with open(f"./data/transportation/{transport['id']}.json", 'w', encoding='utf-8') as f:
        json.dump(transport, f, ensure_ascii=False, indent=2)
    print(f"Created transportation data for {transport['name']['en']}")

print("Transportation data population complete!")