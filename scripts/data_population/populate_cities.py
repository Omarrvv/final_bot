# populate_cities.py
import json
import os
from datetime import datetime

# Ensure directories exist
def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

ensure_dir("./data/cities")

# Define city data
cities = [
    {
        "id": "cairo",
        "name": {
            "en": "Cairo",
            "ar": "القاهرة"
        },
        "region": {
            "en": "Greater Cairo",
            "ar": "القاهرة الكبرى"
        },
        "coordinates": {
            "latitude": 30.0444,
            "longitude": 31.2357
        },
        "description": {
            "en": "Cairo, Egypt's sprawling capital, is set on the Nile River. At its heart is Tahrir Square and the vast Egyptian Museum, a trove of antiquities including the royal mummies and gilded King Tutankhamun artifacts. Nearby, Giza is home to the iconic pyramids and Great Sphinx, dating to the 26th century BC. In Gezira Island's leafy Zamalek district, 187m Cairo Tower affords panoramic city views.",
            "ar": "القاهرة، عاصمة مصر المترامية الأطراف، تقع على نهر النيل. في قلبها ميدان التحرير والمتحف المصري الكبير، وهو كنز من الآثار بما في ذلك المومياوات الملكية والقطع الأثرية المذهبة للملك توت عنخ آمون. وبالقرب منها، توجد الجيزة موطن الأهرامات الشهيرة وأبو الهول العظيم، التي يعود تاريخها إلى القرن السادس والعشرين قبل الميلاد. وفي حي الزمالك بجزيرة الجزيرة المورقة، يوفر برج القاهرة البالغ ارتفاعه 187 متراً إطلالات بانورامية على المدينة."
        },
        "history": {
            "en": "Founded in 969 CE by the Fatimid dynasty, Cairo has been the capital of Egypt for over a thousand years. The city has been a center of political, cultural, and religious importance throughout its history. Cairo's historic core was designated a UNESCO World Heritage Site in 1979.",
            "ar": "تأسست القاهرة عام 969 ميلادياً على يد الدولة الفاطمية، وكانت عاصمة مصر لأكثر من ألف عام. كانت المدينة مركزاً للأهمية السياسية والثقافية والدينية طوال تاريخها. تم تصنيف نواة القاهرة التاريخية كموقع للتراث العالمي لليونسكو في عام 1979."
        },
        "practical_info": {
            "population": 21323000,
            "area": 3085,
            "timezone": "EET (UTC+2)",
            "language": "Arabic",
            "currency": "Egyptian Pound (EGP)",
            "weather": "Hot desert climate with mild winters and hot summers. Rainfall is rare.",
            "best_time_to_visit": "October to April, when temperatures are milder",
            "transportation": {
                "en": "Cairo has an extensive public transportation system including metro lines, buses, taxis, and ride-sharing services. The Cairo Metro is the most efficient way to navigate the city, especially during rush hours. Taxis and ride-sharing services like Uber and Careem are widely available.",
                "ar": "تمتلك القاهرة نظام نقل عام واسع يشمل خطوط المترو والحافلات وسيارات الأجرة وخدمات مشاركة الركوب. يعد مترو القاهرة أكثر الطرق كفاءة للتنقل في المدينة، خاصة خلال ساعات الذروة. تتوفر سيارات الأجرة وخدمات مشاركة الركوب مثل أوبر وكريم على نطاق واسع."
            }
        },
        "highlights": [
            {
                "id": "pyramids_of_giza",
                "name": {
                    "en": "Pyramids of Giza",
                    "ar": "أهرامات الجيزة"
                }
            },
            {
                "id": "egyptian_museum",
                "name": {
                    "en": "Egyptian Museum",
                    "ar": "المتحف المصري"
                }
            },
            {
                "id": "khan_el_khalili",
                "name": {
                    "en": "Khan El-Khalili",
                    "ar": "خان الخليلي"
                }
            },
            {
                "id": "cairo_citadel",
                "name": {
                    "en": "Cairo Citadel",
                    "ar": "قلعة صلاح الدين"
                }
            },
            {
                "id": "al_azhar_park",
                "name": {
                    "en": "Al-Azhar Park",
                    "ar": "حديقة الأزهر"
                }
            }
        ],
        "images": [
            "cairo_skyline.jpg",
            "cairo_downtown.jpg",
            "cairo_nile_view.jpg"
        ],
        "tags": ["capital", "urban", "historical", "pyramids", "museums", "nile"],
        "last_updated": datetime.now().isoformat()
    },
    {
        "id": "luxor",
        "name": {
            "en": "Luxor",
            "ar": "الأقصر"
        },
        "region": {
            "en": "Upper Egypt",
            "ar": "صعيد مصر"
        },
        "coordinates": {
            "latitude": 25.6872,
            "longitude": 32.6396
        },
        "description": {
            "en": "Luxor is a city in Upper Egypt and the capital of Luxor Governorate. The city is located on the east bank of the Nile River and was the ancient Egyptian city of Thebes, the glorious capital of Egypt during the New Kingdom. Luxor has frequently been called the 'world's greatest open-air museum', with ruins of temple complexes at Karnak and Luxor, and the Valley of the Kings and Valley of the Queens on the opposite bank of the Nile.",
            "ar": "الأقصر هي مدينة في صعيد مصر وعاصمة محافظة الأقصر. تقع المدينة على الضفة الشرقية لنهر النيل وكانت مدينة طيبة المصرية القديمة، العاصمة المجيدة لمصر خلال المملكة الحديثة. غالبًا ما كانت الأقصر تسمى \"أعظم متحف مفتوح في العالم\"، مع أطلال مجمعات المعابد في الكرنك والأقصر، ووادي الملوك ووادي الملكات على الضفة المقابلة للنيل."
        },
        "history": {
            "en": "Luxor was the ancient city of Thebes, the great capital of Upper Egypt during the New Kingdom. The city was dedicated to the god Amun, and was the location of the annual Opet Festival. The earliest monuments in Luxor date back to the Eleventh Dynasty of Egypt, when the city was called Wsit (\"City\") and was the capital of Upper Egypt.",
            "ar": "كانت الأقصر المدينة القديمة طيبة، العاصمة العظيمة لصعيد مصر خلال المملكة الحديثة. كانت المدينة مكرسة للإله آمون، وكانت موقع مهرجان أوبت السنوي. تعود أقدم المعالم في الأقصر إلى الأسرة الحادية عشرة المصرية، عندما كانت تسمى المدينة وسيت (\"المدينة\") وكانت عاصمة صعيد مصر."
        },
        "practical_info": {
            "population": 507000,
            "area": 416,
            "timezone": "EET (UTC+2)",
            "language": "Arabic",
            "currency": "Egyptian Pound (EGP)",
            "weather": "Hot desert climate. Very hot summers and mild winters. Almost no rainfall throughout the year.",
            "best_time_to_visit": "October to April, to avoid the extreme summer heat",
            "transportation": {
                "en": "Luxor is compact enough to walk around the east bank, but to visit the many sites on the west bank you'll need transportation. Options include taxis, horse-drawn carriages (calèches), boats to cross the Nile, and organized tours. Bicycle rental is also popular for exploring the west bank.",
                "ar": "الأقصر صغيرة بما يكفي للتجول في الضفة الشرقية سيراً على الأقدام، ولكن لزيارة المواقع العديدة في الضفة الغربية ستحتاج إلى وسيلة نقل. تشمل الخيارات سيارات الأجرة والعربات التي تجرها الخيول (الحنطور) والقوارب لعبور النيل والجولات المنظمة. يعد استئجار الدراجات شائعًا أيضًا لاستكشاف الضفة الغربية."
            }
        },
        "highlights": [
            {
                "id": "karnak_temple",
                "name": {
                    "en": "Karnak Temple",
                    "ar": "معبد الكرنك"
                }
            },
            {
                "id": "luxor_temple",
                "name": {
                    "en": "Luxor Temple",
                    "ar": "معبد الأقصر"
                }
            },
            {
                "id": "valley_of_kings",
                "name": {
                    "en": "Valley of the Kings",
                    "ar": "وادي الملوك"
                }
            },
            {
                "id": "hatshepsut_temple",
                "name": {
                    "en": "Temple of Hatshepsut",
                    "ar": "معبد حتشبسوت"
                }
            },
            {
                "id": "luxor_museum",
                "name": {
                    "en": "Luxor Museum",
                    "ar": "متحف الأقصر"
                }
            }
        ],
        "images": [
            "luxor_aerial.jpg",
            "karnak_temple.jpg",
            "valley_of_kings.jpg"
        ],
        "tags": ["ancient", "temples", "tombs", "historical", "nile", "archaeology"],
        "last_updated": datetime.now().isoformat()
    },
    {
        "id": "aswan",
        "name": {
            "en": "Aswan",
            "ar": "أسوان"
        },
        "region": {
            "en": "Upper Egypt",
            "ar": "صعيد مصر"
        },
        "coordinates": {
            "latitude": 24.0889,
            "longitude": 32.8998
        },
        "description": {
            "en": "Aswan is a city in the south of Egypt, the capital of the Aswan Governorate. It stands on the east bank of the Nile at the first cataract and is a busy market and tourist center. Aswan is considered the southern gateway to Egypt and has a more African atmosphere than other Egyptian cities. The pace of life is slower, the air is cleaner, and the city is famous for its beautiful Nile setting with feluccas sailing around the small islands.",
            "ar": "أسوان هي مدينة في جنوب مصر، عاصمة محافظة أسوان. تقع على الضفة الشرقية للنيل عند الشلال الأول وهي مركز سوق وسياحة مزدحم. تعتبر أسوان البوابة الجنوبية لمصر ولديها أجواء أفريقية أكثر من المدن المصرية الأخرى. وتيرة الحياة أبطأ، والهواء أنظف، والمدينة مشهورة بموقعها الجميل على النيل مع المراكب الشراعية التي تبحر حول الجزر الصغيرة."
        },
        "history": {
            "en": "Aswan has been southern Egypt's strategic and commercial gateway since antiquity, controlling the trade routes from Nubia to the north. It was also important for the stone quarries that supplied granite for obelisks and sculptures throughout ancient Egypt. During Greco-Roman times, it was a military outpost and was known as Syene.",
            "ar": "كانت أسوان بوابة جنوب مصر الاستراتيجية والتجارية منذ العصور القديمة، حيث تسيطر على طرق التجارة من النوبة إلى الشمال. كانت أيضًا مهمة لمحاجر الحجارة التي زودت الجرانيت للمسلات والمنحوتات في جميع أنحاء مصر القديمة. خلال العصور اليونانية الرومانية، كانت موقعًا عسكريًا وكانت تعرف باسم سيينه."
        },
        "practical_info": {
            "population": 290000,
            "area": 34.6,
            "timezone": "EET (UTC+2)",
            "language": "Arabic",
            "currency": "Egyptian Pound (EGP)",
            "weather": "Hot desert climate. Very hot summers and warm winters. Almost no rainfall throughout the year. Considered one of the sunniest places on Earth.",
            "best_time_to_visit": "October to April, when temperatures are more comfortable",
            "transportation": {
                "en": "Aswan is small enough to explore on foot, particularly around the Corniche area. Taxis and horse-drawn carriages are available for longer journeys. Ferries cross to Elephantine Island regularly, and feluccas can be hired for trips on the Nile. For trips to nearby attractions like Abu Simbel, organized tours or private drivers are the best options.",
                "ar": "أسوان صغيرة بما يكفي لاستكشافها سيراً على الأقدام، خاصة حول منطقة الكورنيش. تتوفر سيارات الأجرة والعربات التي تجرها الخيول للرحلات الأطول. تعبر العبارات إلى جزيرة الفنتين بانتظام، ويمكن استئجار المراكب الشراعية للرحلات على النيل. بالنسبة للرحلات إلى المعالم السياحية القريبة مثل أبو سمبل، فإن الجولات المنظمة أو السائقين الخاصين هي الخيارات الأفضل."
            }
        },
        "highlights": [
            {
                "id": "philae_temple",
                "name": {
                    "en": "Temple of Philae",
                    "ar": "معبد فيلة"
                }
            },
            {
                "id": "abu_simbel",
                "name": {
                    "en": "Abu Simbel Temples",
                    "ar": "معابد أبو سمبل"
                }
            },
            {
                "id": "unfinished_obelisk",
                "name": {
                    "en": "Unfinished Obelisk",
                    "ar": "المسلة الناقصة"
                }
            },
            {
                "id": "elephantine_island",
                "name": {
                    "en": "Elephantine Island",
                    "ar": "جزيرة الفنتين"
                }
            },
            {
                "id": "nubian_museum",
                "name": {
                    "en": "Nubian Museum",
                    "ar": "المتحف النوبي"
                }
            }
        ],
        "images": [
            "aswan_nile.jpg",
            "philae_temple.jpg",
            "nubian_village.jpg"
        ],
        "tags": ["nile", "nubian", "temples", "islands", "dam", "relaxing"],
        "last_updated": datetime.now().isoformat()
    }
]

# Save cities to JSON files
for city in cities:
    with open(f"./data/cities/{city['id']}.json", 'w', encoding='utf-8') as f:
        json.dump(city, f, ensure_ascii=False, indent=2)
    print(f"Created city data for {city['name']['en']}")

print("City data population complete!")
