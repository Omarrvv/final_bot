# populate_restaurants.py
import json
import os
from datetime import datetime

# Ensure directories exist
def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

ensure_dir("./data/restaurants")

# Define restaurant data - Updated with famous real-world examples
restaurants = [
    {
        "id": "abou_el_sid_cairo",
        "name": {
            "en": "Abou El Sid",
            "ar": "أبو السيد"
        },
        "type": "traditional_egyptian",
        "cuisine": ["Egyptian", "Middle Eastern"],
        "location": {
            "city": "Cairo",
            "city_ar": "القاهرة",
            "address": "157 26th of July St, Zamalek",
            "address_ar": "١٥٧ شارع ٢٦ يوليو، الزمالك",
            "coordinates": {
                "latitude": 30.0571,
                "longitude": 31.2203
            }
        },
        "description": {
            "en": "A highly atmospheric restaurant offering authentic Egyptian cuisine in a setting evoking 1940s Cairo grandeur. Famous for its ambiance and traditional dishes.",
            "ar": "مطعم ذو أجواء رائعة يقدم المأكولات المصرية الأصيلة في مكان يستحضر عظمة القاهرة في الأربعينيات. يشتهر بأجوائه وأطباقه التقليدية."
        },
        "price_range": "$$ (Moderate)",
        "opening_hours": "1:00 PM - 1:00 AM daily",
        "popular_dishes": [
            {"name": {"en": "Molokhia with Chicken/Rabbit", "ar": "ملوخية بالدجاج/الأرانب"}, "price": "LE 150-200"},
            {"name": {"en": "Hamam Mahshi (Stuffed Pigeon)", "ar": "حمام محشي"}, "price": "LE 180-220"},
            {"name": {"en": "Fattah", "ar": "فتة"}, "price": "LE 160-200"}
        ],
        "contact": {
            "phone": "+20 2 27359640",
            "email": "info@abouelsid.com",
            "website": "https://www.abouelsid.com"
        },
        "images": ["abou_el_sid_interior.jpg", "abou_el_sid_molokhia.jpg"],
        "tags": ["traditional", "authentic", "ambiance", "zamalek", "cairo"],
        "last_updated": datetime.now().isoformat()
    },
    {
        "id": "abou_tarek_koshary_cairo",
        "name": {
            "en": "Abou Tarek Koshary",
            "ar": "أبو طارق للكشري"
        },
        "type": "koshary_specialty",
        "cuisine": ["Egyptian", "Street Food"],
        "location": {
            "city": "Cairo",
            "city_ar": "القاهرة",
            "address": "16 Champollion St, Downtown",
            "address_ar": "١٦ شارع شامبليون، وسط البلد",
            "coordinates": {
                "latitude": 30.0497,
                "longitude": 31.2403
            }
        },
        "description": {
            "en": "Arguably Cairo's most famous Koshary restaurant, an institution known for its bustling atmosphere and delicious, classic take on Egypt's national dish.",
            "ar": "يمكن القول إنه أشهر مطعم كشري في القاهرة، وهو مؤسسة معروفة بأجوائها الصاخبة وطعمها الكلاسيكي اللذيذ للطبق الوطني المصري."
        },
        "price_range": "$ (Inexpensive)",
        "opening_hours": "9:00 AM - 11:00 PM daily",
        "popular_dishes": [
            {"name": {"en": "Koshary (various sizes)", "ar": "كشري (أحجام مختلفة)"}, "price": "LE 15-30"},
            {"name": {"en": "Rice Pudding", "ar": "أرز باللبن"}, "price": "LE 10"}
        ],
        "contact": {
            "phone": "+20 2 25775935",
            "email": None,
            "website": None # Often has Facebook page
        },
        "images": ["abou_tarek_exterior.jpg", "abou_tarek_koshary.jpg"],
        "tags": ["koshary", "budget", "local", "iconic", "downtown", "cairo"],
        "last_updated": datetime.now().isoformat()
    },
    {
        "id": "fasahet_somaya_cairo",
        "name": {
            "en": "Fasahet Somaya",
            "ar": "فسحة سمية"
        },
        "type": "authentic_egyptian",
        "cuisine": ["Egyptian", "Home-style"],
        "location": {
            "city": "Cairo",
            "city_ar": "القاهرة",
            "address": "6 Alfy Bey St, Oraby, Ezbekeya, Downtown",
            "address_ar": "٦ شارع ألفي بك، الأوربي، الأزبكية، وسط البلد",
            "coordinates": {
                "latitude": 30.0514,
                "longitude": 31.2453
            }
        },
        "description": {
            "en": "A very popular, no-frills eatery beloved for its authentic, home-style Egyptian dishes like molokhia, fattah, liver, and sausage. Known for fresh ingredients and often has queues.",
            "ar": "مطعم شهير جدًا وبسيط، محبوب لأطباقه المصرية الأصيلة على طراز المنزل مثل الملوخية والفتة والكبدة والسجق. معروف بمكوناته الطازجة وغالبًا ما يكون به طوابير."
        },
        "price_range": "$ (Inexpensive)",
        "opening_hours": "Around 5:00 PM until sold out (limited hours)",
        "popular_dishes": [
            {"name": {"en": "Molokhia", "ar": "ملوخية"}, "price": "LE 50-70"},
            {"name": {"en": "Fattah", "ar": "فتة"}, "price": "LE 60-80"},
            {"name": {"en": "Alexandrian Liver", "ar": "كبدة اسكندراني"}, "price": "LE 50-70"}
        ],
        "contact": {
            "phone": None, # Usually no listed phone
            "email": None,
            "website": None
        },
        "images": ["fasahet_somaya_food.jpg", "fasahet_somaya_crowd.jpg"],
        "tags": ["authentic", "home-style", "local", "budget", "popular", "downtown", "cairo"],
        "last_updated": datetime.now().isoformat()
    },
    {
        "id": "kazaz_restaurant_cairo",
        "name": {
            "en": "Kazaz Restaurant",
            "ar": "مطعم قزاز"
        },
        "type": "upscale_egyptian",
        "cuisine": ["Egyptian", "Middle Eastern"],
        "location": {
            "city": "Cairo",
            "city_ar": "القاهرة",
            "address": "38 Abou El Feda St, Zamalek", # Note: Also has other branches like Garden City
            "address_ar": "٣٨ شارع أبو الفدا، الزمالك",
            "coordinates": {
                "latitude": 30.0618, # Approx Zamalek branch
                "longitude": 31.2195
            }
        },
        "description": {
            "en": "An upscale restaurant known for its classic Egyptian and Middle Eastern cuisine, particularly grilled meats and mezzes, served in an elegant setting.",
            "ar": "مطعم راقٍ معروف بمأكولاته المصرية والشرق أوسطية الكلاسيكية، وخاصة اللحوم المشوية والمقبلات، ويقدم في أجواء أنيقة."
        },
        "price_range": "$$$ (Expensive)",
        "opening_hours": "1:00 PM - 1:00 AM daily",
        "popular_dishes": [
            {"name": {"en": "Mixed Grill", "ar": "مشويات مشكلة"}, "price": "LE 300-400"},
            {"name": {"en": "Various Mezzes (Hummus, Baba Ghanoush)", "ar": "مقبلات متنوعة (حمص، بابا غنوج)"}, "price": "LE 50-80 each"},
            {"name": {"en": "Veal Fattah", "ar": "فتة باللحم البتلو"}, "price": "LE 250-300"}
        ],
        "contact": {
            "phone": "+20 2 27351111", # Example number, check specific branch
            "email": None,
            "website": None # Often has Facebook page
        },
        "images": ["kazaz_grills.jpg", "kazaz_interior.jpg"],
        "tags": ["upscale", "grills", "mezzes", "elegant", "zamalek", "cairo"],
        "last_updated": datetime.now().isoformat()
    },
    {
        "id": "fish_market_alex",
        "name": {
            "en": "Fish Market",
            "ar": "فيش ماركت"
        },
        "type": "seafood",
        "cuisine": ["Seafood", "Mediterranean"],
        "location": {
            "city": "Alexandria",
            "city_ar": "الإسكندرية",
            "address": "Corniche Road, Bahary Area (multiple locations)",
            "address_ar": "طريق الكورنيش، منطقة بحري (عدة فروع)",
            "coordinates": {
                "latitude": 31.2011, # Approx Bahary branch
                "longitude": 29.8895
            }
        },
        "description": {
            "en": "A landmark Alexandria seafood restaurant where diners choose fresh fish from a large display, which is then cooked to order (grilled, fried, baked). Known for its freshness and often great sea views.",
            "ar": "مطعم مأكولات بحرية بارز في الإسكندرية حيث يختار رواد المطعم الأسماك الطازجة من عرض كبير، ثم يتم طهيها حسب الطلب (مشوية، مقلية، مخبوزة). يشتهر بطزاجته وغالبًا ما يوفر إطلالات رائعة على البحر."
        },
        "price_range": "$$-$$$ (Moderate to Expensive, depends on fish weight)",
        "opening_hours": "12:00 PM - 1:00 AM daily",
        "popular_dishes": [
            {"name": {"en": "Grilled Sea Bass", "ar": "قاروص مشوي"}, "price": "By weight"},
            {"name": {"en": "Fried Calamari", "ar": "كاليماري مقلي"}, "price": "LE 100-150"},
            {"name": {"en": "Shrimp Tagine", "ar": "طاجن جمبري"}, "price": "LE 150-200"}
        ],
        "contact": {
            "phone": "+20 3 4805114", # Example number, check specific branch
            "email": None,
            "website": None
        },
        "images": ["fish_market_display.jpg", "fish_market_grilled_fish.jpg"],
        "tags": ["seafood", "fresh", "alexandria", "corniche", "sea view"],
        "last_updated": datetime.now().isoformat()
    },
    {
        "id": "mohamed_ahmed_alex",
        "name": {
            "en": "Mohamed Ahmed Restaurant",
            "ar": "مطعم محمد أحمد"
        },
        "type": "traditional_egyptian_breakfast",
        "cuisine": ["Egyptian", "Foul & Falafel"],
        "location": {
            "city": "Alexandria",
            "city_ar": "الإسكندرية",
            "address": "17 Shakour Basha St, Raml Station",
            "address_ar": "١٧ شارع شكور باشا، محطة الرمل",
            "coordinates": {
                "latitude": 31.1988,
                "longitude": 29.9043
            }
        },
        "description": {
            "en": "An absolute institution in Alexandria, famous for its traditional Egyptian breakfast, especially Foul (fava beans) and Ta'ameya (falafel). Always busy and very affordable.",
            "ar": "مؤسسة حقيقية في الإسكندرية، تشتهر بوجبة الإفطار المصرية التقليدية، وخاصة الفول والطعمية. دائمًا مزدحم وبأسعار معقولة جدًا."
        },
        "price_range": "$ (Very Inexpensive)",
        "opening_hours": "6:00 AM - 12:00 AM daily",
        "popular_dishes": [
            {"name": {"en": "Foul (various types)", "ar": "فول (أنواع مختلفة)"}, "price": "LE 10-20"},
            {"name": {"en": "Ta'ameya (Falafel)", "ar": "طعمية (فلافل)"}, "price": "LE 1-2 per piece"},
            {"name": {"en": "Eggah (Egyptian Omelette)", "ar": "عجة"}, "price": "LE 15-25"}
        ],
        "contact": {
            "phone": "+20 3 4873576",
            "email": None,
            "website": None
        },
        "images": ["mohamed_ahmed_foul.jpg", "mohamed_ahmed_falafel.jpg"],
        "tags": ["foul", "falafel", "breakfast", "local", "budget", "alexandria", "iconic"],
        "last_updated": datetime.now().isoformat()
    },
    {
        "id": "sofra_luxor", # Kept original ID for simplicity, added city
        "name": {
            "en": "Sofra Restaurant",
            "ar": "مطعم سفرة"
        },
        "type": "traditional_egyptian",
        "cuisine": ["Egyptian", "Nubian", "Middle Eastern"],
        "location": {
            "city": "Luxor",
            "city_ar": "الأقصر",
            "address": "90 Mohammed Farid St, Luxor East Bank",
            "address_ar": "٩٠ شارع محمد فريد، الضفة الشرقية، الأقصر",
            "coordinates": {
                "latitude": 25.7006,
                "longitude": 32.6411
            }
        },
        "description": {
            "en": "A charming restaurant in Luxor set in a restored 1930s house, offering authentic Egyptian cuisine in a traditional setting with rooftop seating.",
            "ar": "مطعم ساحر في الأقصر يقع في منزل تم ترميمه من ثلاثينيات القرن الماضي، ويقدم المأكولات المصرية الأصيلة في أجواء تقليدية مع أماكن جلوس على السطح."
        },
        "price_range": "$$ (Moderate)",
        "opening_hours": "11:00 AM - 11:00 PM daily",
        "popular_dishes": [
            {"name": {"en": "Stuffed Pigeon", "ar": "حمام محشي"}, "price": "LE 140-180"},
            {"name": {"en": "Lamb Tagine", "ar": "طاجن لحم ضأن"}, "price": "LE 150-190"},
            {"name": {"en": "Feteer Meshaltet", "ar": "فطير مشلتت"}, "price": "LE 70-90"}
        ],
        "contact": {
            "phone": "+20 95 2358181",
            "email": "info@sofra.com.eg",
            "website": "https://www.sofra.com.eg" # Check if still active
        },
        "images": ["sofra_exterior.jpg", "sofra_rooftop.jpg", "sofra_tagine.jpg"],
        "tags": ["authentic", "traditional", "local cuisine", "luxor", "rooftop", "ambiance"],
        "last_updated": datetime.now().isoformat()
    },
    {
        "id": "al_dokka_aswan",
        "name": {
            "en": "Al Dokka Restaurant",
            "ar": "مطعم الدكة"
        },
        "type": "nubian_cuisine",
        "cuisine": ["Nubian", "Egyptian", "Seafood"],
        "location": {
            "city": "Aswan",
            "city_ar": "أسوان",
            "address": "Elephantine Island (requires boat access)",
            "address_ar": "جزيرة إلفنتين (يتطلب الوصول بالقارب)",
            "coordinates": {
                "latitude": 24.0869, # Approx location on island
                "longitude": 32.8879
            }
        },
        "description": {
            "en": "Located on Elephantine Island with stunning Nile views, Al Dokka specializes in traditional Nubian cuisine, particularly fish tagines and grilled meats.",
            "ar": "يقع في جزيرة إلفنتين مع إطلالات خلابة على النيل، ويتخصص مطعم الدكة في المأكولات النوبية التقليدية، وخاصة طواجن السمك واللحوم المشوية."
        },
        "price_range": "$$ (Moderate)",
        "opening_hours": "12:00 PM - 10:00 PM daily (approx)",
        "popular_dishes": [
            {"name": {"en": "Fish Tagine", "ar": "طاجن سمك"}, "price": "LE 120-180"},
            {"name": {"en": "Nubian Chicken Casserole", "ar": "كسرولة دجاج نوبية"}, "price": "LE 130-170"},
            {"name": {"en": "Grilled Nile Perch", "ar": "سمك بياض النيل مشوي"}, "price": "By weight"}
        ],
        "contact": {
            "phone": "+20 100 568 7019", # Check number validity
            "email": None,
            "website": None
        },
        "images": ["al_dokka_view.jpg", "al_dokka_fish_tagine.jpg"],
        "tags": ["nubian", "aswan", "nile view", "island", "authentic", "fish"],
        "last_updated": datetime.now().isoformat()
    }
]

# Save restaurants to JSON files
for restaurant in restaurants:
    filename = f"./data/restaurants/{restaurant['id']}.json"
    # Create directory if it doesn't exist (redundant if ensure_dir worked, but safe)
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(restaurant, f, ensure_ascii=False, indent=2)
    print(f"Created/Updated restaurant data for {restaurant['name']['en']} ({restaurant['location']['city']})")

print("Restaurant data population complete!")