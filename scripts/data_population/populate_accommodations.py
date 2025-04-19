# populate_accommodations.py
import json
import os
from datetime import datetime

# Ensure directories exist
def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

ensure_dir("./data/accommodations")

# Define accommodation data
accommodations = [
    {
        "id": "mena_house_hotel",
        "name": {
            "en": "Marriott Mena House, Cairo",
            "ar": "ماريوت منا هاوس، القاهرة"
        },
        "type": "luxury_hotel",
        "stars": 5,
        "location": {
            "city": "Cairo",
            "city_ar": "القاهرة",
            "address": "6 Pyramids Road, Giza",
            "address_ar": "٦ طريق الأهرامات، الجيزة",
            "coordinates": {
                "latitude": 29.9902,
                "longitude": 31.1339
            }
        },
        "description": {
            "en": "Marriott Mena House is a historic hotel located at the foot of the Great Pyramids of Giza. Originally a hunting lodge built in 1869, it has hosted royalty, dignitaries, and celebrities throughout its storied history. The hotel combines luxurious modern accommodations with breathtaking views of the pyramids and extensive gardens. It features elegant rooms, multiple dining options, a spa, and a swimming pool, all while preserving its historical charm and offering an unparalleled proximity to Egypt's most iconic ancient monuments.",
            "ar": "ماريوت منا هاوس هو فندق تاريخي يقع عند سفح أهرامات الجيزة العظيمة. كان في الأصل نزلاً للصيد تم بناؤه في عام 1869، وقد استضاف ملوكًا ووجهاء ومشاهير على مر تاريخه الحافل. يجمع الفندق بين أماكن إقامة فاخرة حديثة مع إطلالات خلابة على الأهرامات وحدائق واسعة. يضم غرفًا أنيقة وخيارات متعددة لتناول الطعام ومنتجع صحي وحمام سباحة، كل ذلك مع الحفاظ على سحره التاريخي وتوفير قرب لا مثيل له من أكثر المعالم القديمة شهرة في مصر."
        },
        "amenities": [
            "Free WiFi",
            "Swimming pool",
            "Spa and wellness center",
            "Fitness center",
            "Multiple restaurants and bars",
            "24-hour room service",
            "Concierge service",
            "Business center",
            "Meeting/banquet facilities",
            "Currency exchange",
            "Tour desk",
            "Gardens",
            "Terrace",
            "Air conditioning",
            "Elevator",
            "Family rooms",
            "Non-smoking rooms",
            "Room service"
        ],
        "price_range": {
            "min": "$200",
            "max": "$1000+",
            "currency": "USD"
        },
        "rooms": [
            {
                "type": {
                    "en": "Deluxe Room",
                    "ar": "غرفة ديلوكس"
                },
                "description": {
                    "en": "Elegant rooms with modern amenities and garden views.",
                    "ar": "غرف أنيقة مع وسائل راحة حديثة وإطلالات على الحديقة."
                },
                "price": "$200-300"
            },
            {
                "type": {
                    "en": "Pyramid View Room",
                    "ar": "غرفة بإطلالة على الأهرامات"
                },
                "description": {
                    "en": "Luxurious rooms offering stunning views of the Great Pyramids of Giza.",
                    "ar": "غرف فاخرة توفر إطلالات مذهلة على أهرامات الجيزة العظيمة."
                },
                "price": "$350-500"
            },
            {
                "type": {
                    "en": "Executive Suite",
                    "ar": "جناح تنفيذي"
                },
                "description": {
                    "en": "Spacious suites with separate living areas, premium amenities, and pyramid views.",
                    "ar": "أجنحة فسيحة مع مناطق معيشة منفصلة ووسائل راحة متميزة وإطلالات على الأهرامات."
                },
                "price": "$600-800"
            },
            {
                "type": {
                    "en": "Royal Suite",
                    "ar": "الجناح الملكي"
                },
                "description": {
                    "en": "Opulent suites offering the ultimate luxury experience with panoramic pyramid views.",
                    "ar": "أجنحة فخمة توفر تجربة فاخرة مطلقة مع إطلالات بانورامية على الأهرامات."
                },
                "price": "$1000+"
            }
        ],
        "dining": [
            {
                "name": {
                    "en": "139 Pavilion",
                    "ar": "جناح ١٣٩"
                },
                "description": {
                    "en": "All-day dining restaurant offering international cuisine with outdoor seating options and views of the pyramids.",
                    "ar": "مطعم يقدم الطعام طوال اليوم ويقدم المأكولات العالمية مع خيارات جلوس في الهواء الطلق وإطلالات على الأهرامات."
                },
                "cuisine": ["International", "Mediterranean", "Egyptian"]
            },
            {
                "name": {
                    "en": "Alfredo Restaurant",
                    "ar": "مطعم الفريدو"
                },
                "description": {
                    "en": "Elegant Italian restaurant serving authentic dishes in a refined setting.",
                    "ar": "مطعم إيطالي أنيق يقدم أطباقًا أصيلة في أجواء راقية."
                },
                "cuisine": ["Italian"]
            },
            {
                "name": {
                    "en": "Sultan Bar",
                    "ar": "بار السلطان"
                },
                "description": {
                    "en": "Sophisticated lounge offering cocktails, fine wines, and light snacks with views of the pyramids.",
                    "ar": "صالة متطورة تقدم الكوكتيلات والنبيذ الفاخر والوجبات الخفيفة مع إطلالات على الأهرامات."
                },
                "cuisine": ["Snacks", "Beverages"]
            }
        ],
        "contact": {
            "phone": "+20 2 33773222",
            "email": "menahouse.reservation@marriott.com",
            "website": "https://www.marriott.com/hotels/travel/caimn-marriott-mena-house-cairo/"
        },
        "images": [
            "mena_house_exterior.jpg",
            "mena_house_pyramid_view.jpg",
            "mena_house_pool.jpg",
            "mena_house_garden.jpg",
            "mena_house_room.jpg",
            "mena_house_dining.jpg"
        ],
        "tags": ["luxury", "historical", "pyramids", "Giza", "resort", "spa", "5-star"],
        "last_updated": datetime.now().isoformat()
    },
    {
        "id": "winter_palace_luxor",
        "name": {
            "en": "Sofitel Winter Palace Luxor",
            "ar": "سوفيتيل وينتر بالاس الأقصر"
        },
        "type": "luxury_heritage_hotel",
        "stars": 5,
        "location": {
            "city": "Luxor",
            "city_ar": "الأقصر",
            "address": "Corniche El Nile Street, Luxor",
            "address_ar": "شارع كورنيش النيل، الأقصر",
            "coordinates": {
                "latitude": 25.6997,
                "longitude": 32.6383
            }
        },
        "description": {
            "en": "The Sofitel Winter Palace is a historic British colonial-era 5-star luxury hotel located on the banks of the Nile River in Luxor, Egypt. Built in 1886, this legendary hotel has hosted royalty, dignitaries, and famous figures including Agatha Christie, who wrote 'Death on the Nile' during her stay. The hotel combines Victorian splendor with modern luxury, featuring opulent interiors, lush tropical gardens, and stunning views of the Nile. With its rich history, elegant architecture, and prime location near Luxor's ancient monuments, the Winter Palace offers guests a truly unique and sophisticated Egyptian experience.",
            "ar": "سوفيتيل وينتر بالاس هو فندق فاخر تاريخي من فئة الخمس نجوم يعود للعصر الاستعماري البريطاني ويقع على ضفاف نهر النيل في الأقصر، مصر. بُني هذا الفندق الأسطوري عام 1886، وقد استضاف ملوكًا ووجهاء وشخصيات مشهورة من بينهم أجاثا كريستي، التي كتبت رواية 'موت على النيل' خلال إقامتها. يجمع الفندق بين الروعة الفيكتورية والفخامة الحديثة، ويتميز بديكورات داخلية فخمة وحدائق استوائية خضراء وإطلالات مذهلة على النيل. مع تاريخه الغني وهندسته المعمارية الأنيقة وموقعه المتميز بالقرب من المعالم الأثرية القديمة في الأقصر، يقدم وينتر بالاس للضيوف تجربة مصرية فريدة ومتطورة حقًا."
        },
        "amenities": [
            "Free WiFi",
            "Outdoor swimming pool",
            "Garden",
            "Terrace",
            "Restaurant",
            "Bar/Lounge",
            "Room service",
            "24-hour front desk",
            "Currency exchange",
            "Concierge service",
            "Laundry service",
            "Dry cleaning",
            "Meeting/banquet facilities",
            "Business center",
            "Babysitting/child services",
            "Fax/photocopying",
            "Ironing service",
            "Non-smoking rooms",
            "Elevator",
            "Air conditioning"
        ],
        "price_range": {
            "min": "$150",
            "max": "$800",
            "currency": "USD"
        },
        "rooms": [
            {
                "type": {
                    "en": "Classic Room",
                    "ar": "غرفة كلاسيك"
                },
                "description": {
                    "en": "Elegant rooms decorated in classic style with garden views and luxurious amenities.",
                    "ar": "غرف أنيقة مزينة بطراز كلاسيكي مع إطلالات على الحديقة ووسائل راحة فاخرة."
                },
                "price": "$150-200"
            },
            {
                "type": {
                    "en": "Nile View Room",
                    "ar": "غرفة بإطلالة على النيل"
                },
                "description": {
                    "en": "Luxurious rooms offering stunning views of the Nile River and historic decor.",
                    "ar": "غرف فاخرة توفر إطلالات مذهلة على نهر النيل وديكور تاريخي."
                },
                "price": "$250-350"
            },
            {
                "type": {
                    "en": "Heritage Suite",
                    "ar": "جناح التراث"
                },
                "description": {
                    "en": "Spacious suites with separate living areas, traditional colonial decor, and magnificent Nile views.",
                    "ar": "أجنحة فسيحة مع مناطق معيشة منفصلة وديكور استعماري تقليدي وإطلالات رائعة على النيل."
                },
                "price": "$400-600"
            },
            {
                "type": {
                    "en": "Royal Suite",
                    "ar": "الجناح الملكي"
                },
                "description": {
                    "en": "Opulent historical suites where famous guests have stayed, featuring antique furniture and panoramic Nile views.",
                    "ar": "أجنحة تاريخية فخمة حيث أقام ضيوف مشهورون، تتميز بأثاث عتيق وإطلالات بانورامية على النيل."
                },
                "price": "$600-800"
            }
        ],
        "dining": [
            {
                "name": {
                    "en": "1886 Restaurant",
                    "ar": "مطعم ١٨٨٦"
                },
                "description": {
                    "en": "Fine dining restaurant serving French cuisine in a magnificent historical setting, featuring crystal chandeliers and classical décor.",
                    "ar": "مطعم راقٍ يقدم المأكولات الفرنسية في محيط تاريخي رائع، يتميز بثريات كريستالية وديكور كلاسيكي."
                },
                "cuisine": ["French", "International"]
            },
            {
                "name": {
                    "en": "La Corniche",
                    "ar": "لا كورنيش"
                },
                "description": {
                    "en": "All-day dining restaurant offering international and Egyptian cuisine with views of the Nile.",
                    "ar": "مطعم يقدم الطعام طوال اليوم ويقدم المأكولات العالمية والمصرية مع إطلالات على النيل."
                },
                "cuisine": ["International", "Egyptian"]
            },
            {
                "name": {
                    "en": "Royal Bar",
                    "ar": "الرويال بار"
                },
                "description": {
                    "en": "A historical bar where many famous guests have enjoyed cocktails and beverages in a colonial atmosphere.",
                    "ar": "بار تاريخي حيث استمتع العديد من الضيوف المشهورين بالكوكتيلات والمشروبات في أجواء استعمارية."
                },
                "cuisine": ["Beverages", "Snacks"]
            }
        ],
        "contact": {
            "phone": "+20 95 2380422",
            "email": "h1661@sofitel.com",
            "website": "https://all.accor.com/hotel/1661/index.en.shtml"
        },
        "images": [
            "winter_palace_exterior.jpg",
            "winter_palace_garden.jpg",
            "winter_palace_nile_view.jpg",
            "winter_palace_lobby.jpg",
            "winter_palace_room.jpg",
            "winter_palace_dining.jpg"
        ],
        "tags": ["luxury", "historical", "heritage", "Nile", "colonial", "5-star", "Agatha Christie"],
        "last_updated": datetime.now().isoformat()
    },
    {
        "id": "four_seasons_nile_plaza",
        "name": {
            "en": "Four Seasons Hotel Cairo at Nile Plaza",
            "ar": "فندق فورسيزونز القاهرة في نايل بلازا"
        },
        "type": "luxury_hotel",
        "stars": 5,
        "location": {
            "city": "Cairo",
            "city_ar": "القاهرة",
            "address": "1089 Corniche El Nil, Garden City, Cairo",
            "address_ar": "١٠٨٩ كورنيش النيل، جاردن سيتي، القاهرة",
            "coordinates": {
                "latitude": 30.0376,
                "longitude": 31.2243
            }
        },
        "description": {
            "en": "Four Seasons Hotel Cairo at Nile Plaza is a contemporary luxury hotel offering panoramic views of the Nile River and the Pyramids in the distance. Located in the Garden City district, this elegant property combines modern sophistication with Egyptian-inspired design elements. The hotel features spacious rooms and suites, multiple restaurants serving international cuisine, a full-service spa, and multiple swimming pools. Its central location makes it an ideal base for exploring Cairo's historical attractions while enjoying world-class service and amenities.",
            "ar": "فندق فورسيزونز القاهرة في نايل بلازا هو فندق فاخر معاصر يوفر إطلالات بانورامية على نهر النيل والأهرامات في البعيد. يقع في حي جاردن سيتي، ويجمع هذا العقار الأنيق بين الرقي الحديث وعناصر التصميم المستوحاة من مصر. يضم الفندق غرفًا وأجنحة فسيحة ومطاعم متعددة تقدم المأكولات العالمية ومنتجعًا صحيًا كاملاً وحمامات سباحة متعددة. موقعه المركزي يجعله قاعدة مثالية لاستكشاف المعالم التاريخية بالقاهرة مع الاستمتاع بخدمة ومرافق عالمية المستوى."
        },
        "amenities": [
            "Free WiFi",
            "Multiple swimming pools",
            "Full-service spa",
            "Fitness center",
            "Multiple restaurants and lounges",
            "24-hour room service",
            "Business center",
            "Concierge service",
            "Valet parking",
            "Laundry service",
            "Hair salon",
            "Gift shop",
            "Babysitting service",
            "Meeting/banquet facilities",
            "Airport transfer",
            "Currency exchange",
            "Air conditioning",
            "Non-smoking rooms"
        ],
        "price_range": {
            "min": "$250",
            "max": "$1500",
            "currency": "USD"
        },
        "rooms": [
            {
                "type": {
                    "en": "Superior Room",
                    "ar": "غرفة سوبيريور"
                },
                "description": {
                    "en": "Elegant rooms with city views and luxurious Four Seasons amenities.",
                    "ar": "غرف أنيقة مع إطلالات على المدينة ووسائل راحة فاخرة من فورسيزونز."
                },
                "price": "$250-350"
            },
            {
                "type": {
                    "en": "Nile View Room",
                    "ar": "غرفة بإطلالة على النيل"
                },
                "description": {
                    "en": "Luxurious rooms offering stunning panoramic views of the Nile River.",
                    "ar": "غرف فاخرة توفر إطلالات بانورامية مذهلة على نهر النيل."
                },
                "price": "$350-500"
            },
            {
                "type": {
                    "en": "Executive Suite",
                    "ar": "جناح تنفيذي"
                },
                "description": {
                    "en": "Spacious suites with separate living areas, premium amenities, and Nile views.",
                    "ar": "أجنحة فسيحة مع مناطق معيشة منفصلة ووسائل راحة متميزة وإطلالات على النيل."
                },
                "price": "$600-900"
            },
            {
                "type": {
                    "en": "Presidential Suite",
                    "ar": "الجناح الرئاسي"
                },
                "description": {
                    "en": "Ultra-luxurious suites with multiple bedrooms, a private dining room, and panoramic Nile views.",
                    "ar": "أجنحة فائقة الفخامة مع غرف نوم متعددة وغرفة طعام خاصة وإطلالات بانورامية على النيل."
                },
                "price": "$1200-1500"
            }
        ],
        "dining": [
            {
                "name": {
                    "en": "Zitouni",
                    "ar": "زيتوني"
                },
                "description": {
                    "en": "Authentic Egyptian cuisine served in an elegant setting with Nile views.",
                    "ar": "مأكولات مصرية أصيلة تقدم في محيط أنيق مع إطلالات على النيل."
                },
                "cuisine": ["Egyptian", "Middle Eastern"]
            },
            {
                "name": {
                    "en": "Bella",
                    "ar": "بيلا"
                },
                "description": {
                    "en": "Fine Italian dining with authentic dishes prepared by Italian chefs.",
                    "ar": "مأكولات إيطالية فاخرة مع أطباق أصيلة يعدها طهاة إيطاليون."
                },
                "cuisine": ["Italian"]
            },
            {
                "name": {
                    "en": "8",
                    "ar": "٨"
                },
                "description": {
                    "en": "Contemporary Chinese restaurant offering authentic Cantonese cuisine.",
                    "ar": "مطعم صيني معاصر يقدم المأكولات الكانتونية الأصيلة."
                },
                "cuisine": ["Chinese", "Cantonese"]
            },
            {
                "name": {
                    "en": "Pool Grill",
                    "ar": "بول جريل"
                },
                "description": {
                    "en": "Casual outdoor dining by the pool offering grilled specialties and light fare.",
                    "ar": "مطعم خارجي غير رسمي بجانب حمام السباحة يقدم تخصصات مشوية ووجبات خفيفة."
                },
                "cuisine": ["Grill", "International"]
            }
        ],
        "contact": {
            "phone": "+20 2 27916900",
            "email": "reservations.cai@fourseasons.com",
            "website": "https://www.fourseasons.com/caironp/"
        },
        "images": [
            "four_seasons_exterior.jpg",
            "four_seasons_lobby.jpg",
            "four_seasons_room.jpg",
            "four_seasons_pool.jpg",
            "four_seasons_restaurant.jpg",
            "four_seasons_spa.jpg"
        ],
        "tags": ["luxury", "modern", "Nile view", "spa", "5-star", "business", "urban"],
        "last_updated": datetime.now().isoformat()
    }
]

# Save accommodations to JSON files
for accommodation in accommodations:
    with open(f"./data/accommodations/{accommodation['id']}.json", 'w', encoding='utf-8') as f:
        json.dump(accommodation, f, ensure_ascii=False, indent=2)
    print(f"Created accommodation data for {accommodation['name']['en']}")

print("Accommodation data population complete!")