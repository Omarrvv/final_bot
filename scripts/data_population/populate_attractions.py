#!/usr/bin/env python3
# populate_attractions.py - Script to populate attractions data

import json
import os
from datetime import datetime

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

# Ensure attractions directory exists
ensure_dir("./data/attractions")
ensure_dir("./data/attractions/historical")

# Define attractions data
attractions = [
    {
        "id": "abu_simbel",
        "name": {
            "en": "Abu Simbel Temples",
            "ar": "معابد أبو سمبل"
        },
        "type": "historical",
        "city": "Aswan",
        "region": "Upper Egypt",
        "coordinates": {
            "latitude": 22.3372,
            "longitude": 31.6258
        },
        "description": {
            "en": "The Abu Simbel temples are two massive rock-cut temples in southern Egypt. They are situated on the western bank of Lake Nasser, about 230 km southwest of Aswan. The twin temples were originally carved out of the mountainside in the 13th century BC, during the 19th dynasty reign of the Pharaoh Ramesses II. The temples were relocated in their entirety in 1968 to avoid being submerged during the creation of Lake Nasser.",
            "ar": "معابد أبو سمبل هي معبدان ضخمان منحوتان في الصخر في جنوب مصر. تقع على الضفة الغربية لبحيرة ناصر، على بعد حوالي 230 كم جنوب غرب أسوان. تم نحت المعبدين التوأمين في الأصل من جانب الجبل في القرن الثالث عشر قبل الميلاد، خلال حكم الأسرة التاسعة عشرة للفرعون رمسيس الثاني. تم نقل المعابد بأكملها في عام 1968 لتجنب غمرها أثناء إنشاء بحيرة ناصر."
        },
        "history": {
            "en": "Built between 1264-1244 BC by Ramesses II, the Great Temple was dedicated to the gods Ra-Horakhty, Ptah, and the deified Ramesses II himself. The Small Temple was dedicated to the goddess Hathor and Queen Nefertari. The temples were rediscovered in 1813 by Swiss explorer Johann Ludwig Burckhardt. They were threatened by submersion in Lake Nasser, and in an unprecedented feat of engineering, the temples were dismantled and reassembled in a new location.",
            "ar": "بُني بين 1264-1244 قبل الميلاد على يد رمسيس الثاني، وكان المعبد الكبير مكرساً للآلهة رع-حوراختي وبتاح ورمسيس الثاني المؤله نفسه. أما المعبد الصغير فكان مكرساً للإلهة حتحور والملكة نفرتاري. تم إعادة اكتشاف المعابد في عام 1813 على يد المستكشف السويسري يوهان لودفيج بوركهارت. كانت مهددة بالغمر في بحيرة ناصر، وفي إنجاز هندسي غير مسبوق، تم تفكيك المعابد وإعادة تجميعها في موقع جديد."
        },
        "highlights": [
            "Great Temple of Ramesses II",
            "Temple of Hathor and Nefertari",
            "Massive rock-cut facades",
            "Solar alignment phenomenon",
            "UNESCO World Heritage Site"
        ],
        "practical_info": {
            "opening_hours": "5:00 AM - 6:00 PM",
            "best_time_to_visit": "Early morning to witness the solar alignment",
            "entrance_fees": {
                "foreign_adults": "240 EGP",
                "foreign_students": "120 EGP",
                "egyptian_adults": "30 EGP",
                "egyptian_students": "10 EGP"
            },
            "guided_tours": True,
            "photography": "Permitted (extra fee for cameras)",
            "accessibility": "Moderate - some walking required",
            "duration": "2-3 hours recommended"
        },
        "tips": {
            "en": "Visit early in the morning to avoid crowds and heat. The temples are illuminated twice a year, around February 22 and October 22, when the sun's rays penetrate the sanctuary and illuminate the sculptures on the back wall. Book tours in advance as it's a 3-hour drive from Aswan.",
            "ar": "قم بالزيارة في الصباح الباكر لتجنب الزحام والحرارة. يتم إضاءة المعابد مرتين في السنة، حوالي 22 فبراير و22 أكتوبر، عندما تخترق أشعة الشمس قدس الأقداس وتضيء المنحوتات على الجدار الخلفي. احجز الجولات مسبقاً حيث تستغرق الرحلة 3 ساعات من أسوان."
        },
        "images": [
            "abu_simbel_facade.jpg",
            "abu_simbel_interior.jpg",
            "abu_simbel_nefertari.jpg"
        ],
        "tags": ["temples", "ancient egypt", "ramesses ii", "unesco", "lake nasser", "archaeology"],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
]

# Save attractions to JSON files
for attraction in attractions:
    file_path = f"./data/attractions/historical/{attraction['id']}.json"
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(attraction, f, ensure_ascii=False, indent=2)
    print(f"Created attraction data for {attraction['name']['en']}")

print("Attractions data population complete!")