# populate_attractions.py
import json
import os
from datetime import datetime

# Ensure directories exist
def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

ensure_dir("./data/attractions/historical")
ensure_dir("./data/attractions/cultural")
ensure_dir("./data/attractions/religious")

# Define historical attractions data
historical_attractions = [
    {
        "id": "abu_simbel",
        "name": {
            "en": "Abu Simbel Temples",
            "ar": "معابد أبو سمبل"
        },
        "type": "ancient_monument",
        "location": {
            "city": "Aswan",
            "city_ar": "أسوان",
            "region": "Upper Egypt",
            "region_ar": "صعيد مصر",
            "coordinates": {
                "latitude": 22.3372,
                "longitude": 31.6256
            }
        },
        "description": {
            "en": "Abu Simbel consists of two massive rock-cut temples in southern Egypt near the border with Sudan. The twin temples were originally carved out of the mountainside in the 13th century BC, during the reign of Pharaoh Ramesses II, as a monument to himself and his queen Nefertari. The complex was relocated in its entirety in 1968 to avoid being submerged during the creation of Lake Nasser.",
            "ar": "يتكون أبو سمبل من معبدين ضخمين منحوتين في الصخر في جنوب مصر بالقرب من الحدود مع السودان. تم نحت المعبدين التوأمين في الأصل من جانب الجبل في القرن الثالث عشر قبل الميلاد، خلال عهد الفرعون رمسيس الثاني، كنصب تذكاري لنفسه ولملكته نفرتاري. تمت إعادة نقل المجمع بأكمله في عام 1968 لتجنب غمره أثناء إنشاء بحيرة ناصر."
        },
        "history": {
            "en": "The temples were carved during the reign of Ramesses II (c. 1279–1213 BC) as a lasting monument to himself and his queen Nefertari, and to commemorate his victory at the Battle of Kadesh. Their huge external rock relief figures have become iconic. The complex was relocated in its entirety in 1968, under the supervision of a UNESCO campaign, to avoid it being submerged during the creation of Lake Nasser following the construction of the Aswan High Dam.",
            "ar": "تم نحت المعابد خلال عهد رمسيس الثاني (حوالي 1279-1213 قبل الميلاد) كنصب تذكاري دائم لنفسه ولملكته نفرتاري، وللاحتفال بانتصاره في معركة قادش. أصبحت تماثيل النحت الصخري الخارجية الضخمة أيقونية. تمت إعادة نقل المجمع بأكمله في عام 1968، تحت إشراف حملة لليونسكو، لتجنب غمره أثناء إنشاء بحيرة ناصر بعد بناء السد العالي في أسوان."
        },
        "practical_info": {
            "opening_hours": "6:00 AM - 5:00 PM daily",
            "ticket_prices": {
                "foreigners": {
                    "adults": "240 EGP",
                    "students": "120 EGP"
                },
                "egyptians": {
                    "adults": "30 EGP",
                    "students": "15 EGP"
                }
            },
            "best_time_to_visit": "Early morning to avoid crowds and heat. October to April for more comfortable temperatures.",
            "duration": "2-3 hours for a complete visit",
            "facilities": [
                "Restrooms",
                "Cafeteria",
                "Souvenir shops",
                "Parking"
            ],
            "accessibility": {
                "en": "The site is partially accessible. There is level access to the temples, but the interiors have uneven surfaces and steps.",
                "ar": "الموقع متاح جزئياً. هناك وصول مستوٍ إلى المعابد، ولكن الأسطح الداخلية غير مستوية وبها درجات."
            },
            "visitor_tips": {
                "en": "Visit early in the morning or plan to stay for the afternoon sun alignment. Photography is allowed but no flash inside the temples. Consider joining a guided tour for historical context. The site is remote, so plan transportation accordingly.",
                "ar": "قم بالزيارة في الصباح الباكر أو خطط للبقاء لمشاهدة محاذاة شمس بعد الظهر. التصوير مسموح به ولكن بدون فلاش داخل المعابد. فكر في الانضمام إلى جولة مع مرشد للحصول على السياق التاريخي. الموقع ناءٍ، لذا خطط لوسائل النقل وفقًا لذلك."
            }
        },
        "must_see": [
            {
                "id": "great_temple",
                "name": {
                    "en": "Great Temple of Ramesses II",
                    "ar": "المعبد الكبير لرمسيس الثاني"
                },
                "description": {
                    "en": "The larger of the two temples, dedicated to Ramesses II himself and the major gods of New Kingdom Egypt. The facade features four colossal statues of the pharaoh, each over 20 meters tall. Twice a year, on February 22 and October 22, the sun penetrates the entire temple to illuminate the sanctuary and statues at the rear.",
                    "ar": "أكبر المعبدين، مخصص لرمسيس الثاني نفسه وآلهة مصر الكبرى في المملكة الحديثة. تضم الواجهة أربعة تماثيل ضخمة للفرعون، يبلغ ارتفاع كل منها أكثر من 20 متراً. مرتين في السنة، في 22 فبراير و22 أكتوبر، تخترق الشمس المعبد بأكمله لتضيء قدس الأقداس والتماثيل في الخلف."
                }
            },
            {
                "id": "small_temple",
                "name": {
                    "en": "Small Temple of Nefertari",
                    "ar": "المعبد الصغير لنفرتاري"
                },
                "description": {
                    "en": "Dedicated to Queen Nefertari and the goddess Hathor, this temple is unique because it places the queen's statues in equal size to those of the pharaoh, showing her importance. The facade has six statues, with Ramesses II and Nefertari depicted three times each.",
                    "ar": "مخصص للملكة نفرتاري والإلهة حتحور، هذا المعبد فريد لأنه يضع تماثيل الملكة بحجم مساوٍ لتماثيل الفرعون، مما يدل على أهميتها. تحتوي الواجهة على ستة تماثيل، مع تصوير رمسيس الثاني ونفرتاري ثلاث مرات لكل منهما."
                }
            },
            {
                "id": "sun_alignment",
                "name": {
                    "en": "Solar Phenomenon",
                    "ar": "ظاهرة الشمس"
                },
                "description": {
                    "en": "Twice a year, on February 22 (Ramesses II's birthday) and October 22 (his coronation day), the rising sun illuminates the inner sanctuary of the Great Temple, lighting up the statues of Ramesses II and the gods, except for Ptah, the god of darkness.",
                    "ar": "مرتين في السنة، في 22 فبراير (عيد ميلاد رمسيس الثاني) و22 أكتوبر (يوم تتويجه)، تضيء الشمس المشرقة الحرم الداخلي للمعبد الكبير، مما يضيء تماثيل رمسيس الثاني والآلهة، باستثناء بتاح، إله الظلام."
                }
            }
        ],
        "images": [
            "abu_simbel_facade.jpg",
            "abu_simbel_interior.jpg",
            "nefertari_temple.jpg",
            "abu_simbel_sunset.jpg"
        ],
        "tags": ["ancient", "temple", "Ramesses II", "monument", "UNESCO", "Nubia"],
        "last_updated": datetime.now().isoformat()
    },
    {
        "id": "valley_of_kings",
        "name": {
            "en": "Valley of the Kings",
            "ar": "وادي الملوك"
        },
        "type": "necropolis",
        "location": {
            "city": "Luxor",
            "city_ar": "الأقصر",
            "region": "Upper Egypt",
            "region_ar": "صعيد مصر",
            "coordinates": {
                "latitude": 25.7402,
                "longitude": 32.6014
            }
        },
        "description": {
            "en": "The Valley of the Kings is a valley in Egypt where, for a period of nearly 500 years from the 16th to 11th century BC, rock-cut tombs were excavated for the pharaohs and powerful nobles of the New Kingdom. The valley stands on the west bank of the Nile, opposite Thebes (modern Luxor), within the heart of the Theban Necropolis. The valley contains at least 63 tombs, beginning with Thutmose I and ending with Ramesses XI.",
            "ar": "وادي الملوك هو وادٍ في مصر حيث، لفترة تقارب 500 عام من القرن السادس عشر إلى القرن الحادي عشر قبل الميلاد، تم حفر مقابر منحوتة في الصخر للفراعنة ونبلاء المملكة الحديثة الأقوياء. يقع الوادي على الضفة الغربية للنيل، مقابل طيبة (الأقصر الحديثة)، في قلب جبانة طيبة. يحتوي الوادي على ما لا يقل عن 63 مقبرة، بدءًا من تحتمس الأول وانتهاءً برمسيس الحادي عشر."
        },
        "history": {
            "en": "The Valley of the Kings was used for primary burials from approximately 1539 BC to 1075 BC, and contains at least 63 tombs, beginning with Thutmose I and ending with Ramesses XI. It was the principal burial place of the major royal figures of the Egyptian New Kingdom, as well as a number of privileged nobles. The royal tombs are decorated with scenes from Egyptian mythology and give clues as to the beliefs and funerary practices of the period. Almost all of the tombs were opened and robbed in antiquity, but they still give an idea of the opulence and power of the pharaohs.",
            "ar": "تم استخدام وادي الملوك للدفن الأساسي من حوالي 1539 قبل الميلاد إلى 1075 قبل الميلاد، ويحتوي على ما لا يقل عن 63 مقبرة، بدءًا من تحتمس الأول وانتهاءً برمسيس الحادي عشر. كان مكان الدفن الرئيسي للشخصيات الملكية الرئيسية في المملكة المصرية الحديثة، وكذلك عدد من النبلاء المميزين. تم تزيين المقابر الملكية بمشاهد من الأساطير المصرية وتعطي أدلة حول معتقدات وممارسات الدفن في تلك الفترة. تم فتح وسرقة جميع المقابر تقريبًا في العصور القديمة، لكنها لا تزال تعطي فكرة عن ترف وقوة الفراعنة."
        },
        "practical_info": {
            "opening_hours": "6:00 AM - 5:00 PM daily",
            "ticket_prices": {
                "foreigners": {
                    "general_admission": "240 EGP (includes 3 tombs)",
                    "special_tombs": {
                        "tutankhamun": "300 EGP",
                        "ramesses_VI": "100 EGP",
                        "seti_I": "1000 EGP"
                    }
                },
                "egyptians": {
                    "general_admission": "30 EGP",
                    "special_tombs": "Various prices"
                }
            },
            "best_time_to_visit": "Early morning to avoid crowds and heat. October to April for more comfortable temperatures.",
            "duration": "2-4 hours depending on how many tombs you visit",
            "facilities": [
                "Restrooms",
                "Cafe",
                "Souvenir shops",
                "Tourist train",
                "Visitor center"
            ],
            "accessibility": {
                "en": "The site is challenging for those with mobility issues. The terrain is uneven, and most tombs require descending steep staircases or ramps. Many tombs have narrow passages and limited space.",
                "ar": "الموقع صعب لأولئك الذين يعانون من مشاكل في الحركة. التضاريس غير مستوية، وتتطلب معظم المقابر النزول عبر سلالم أو منحدرات شديدة. العديد من المقابر لها ممرات ضيقة ومساحة محدودة."
            },
            "visitor_tips": {
                "en": "Visit early in the morning to avoid crowds and heat. General tickets include entry to three tombs of your choice (excluding special tombs). Photography is prohibited inside all tombs. Bring water, sun protection, and comfortable shoes. Consider hiring a guide for historical context. The most impressive tombs are often those with additional fees.",
                "ar": "قم بالزيارة في الصباح الباكر لتجنب الزحام والحرارة. تشمل التذاكر العامة الدخول إلى ثلاثة مقابر من اختيارك (باستثناء المقابر الخاصة). التصوير محظور داخل جميع المقابر. أحضر الماء، والحماية من الشمس، وأحذية مريحة. فكر في استئجار مرشد للسياق التاريخي. المقابر الأكثر إثارة للإعجاب هي غالبًا تلك التي تتطلب رسومًا إضافية."
            }
        },
        "must_see": [
            {
                "id": "tomb_of_tutankhamun",
                "name": {
                    "en": "Tomb of Tutankhamun (KV62)",
                    "ar": "مقبرة توت عنخ آمون"
                },
                "description": {
                    "en": "The most famous tomb in the valley, discovered largely intact by Howard Carter in 1922. Though smaller than many royal tombs, it's the only tomb that was found with most of its treasures undisturbed. The tomb still contains Tutankhamun's mummy in a glass display case.",
                    "ar": "أشهر مقبرة في الوادي، اكتشفها هوارد كارتر في عام 1922 وهي سليمة إلى حد كبير. على الرغم من أنها أصغر من العديد من المقابر الملكية، إلا أنها المقبرة الوحيدة التي تم العثور عليها مع معظم كنوزها لم تمس. لا تزال المقبرة تحتوي على مومياء توت عنخ آمون في صندوق عرض زجاجي."
                }
            },
            {
                "id": "tomb_of_ramesses_VI",
                "name": {
                    "en": "Tomb of Ramesses VI (KV9)",
                    "ar": "مقبرة رمسيس السادس"
                },
                "description": {
                    "en": "One of the most impressive tombs in the valley, with extensive and well-preserved decorations. The tomb features astronomical scenes on its ceilings including the Books of the Heavens, the Book of Gates, the Book of Caverns, and the Book of the Dead.",
                    "ar": "واحدة من أكثر المقابر إثارة للإعجاب في الوادي، مع زخارف واسعة ومحفوظة جيدًا. تضم المقبرة مشاهد فلكية على سقوفها بما في ذلك كتب السماوات، وكتاب البوابات، وكتاب الكهوف، وكتاب الموتى."
                }
            },
            {
                "id": "tomb_of_seti_I",
                "name": {
                    "en": "Tomb of Seti I (KV17)",
                    "ar": "مقبرة سيتي الأول"
                },
                "description": {
                    "en": "Considered the most magnificent tomb in the valley, with exquisite relief carvings and extensive decoration throughout its many chambers. At 137 meters, it's one of the longest and deepest tombs. The burial chamber features a beautiful painted astronomical ceiling.",
                    "ar": "تعتبر أروع مقبرة في الوادي، مع نقوش بارزة رائعة وزخارف واسعة في جميع غرفها العديدة. بطول 137 مترًا، إنها واحدة من أطول وأعمق المقابر. تضم غرفة الدفن سقفاً فلكياً مرسوماً جميلاً."
                }
            }
        ],
        "components": [
            {
                "id": "royal_tombs",
                "name": {
                    "en": "Royal Tombs",
                    "ar": "المقابر الملكية"
                },
                "description": {
                    "en": "The valley contains at least 63 tombs of pharaohs, queens, high priests, and other elites from the New Kingdom period. Each tomb is assigned a number preceded by 'KV' (Kings' Valley).",
                    "ar": "يحتوي الوادي على ما لا يقل عن 63 مقبرة للفراعنة والملكات وكبار الكهنة والنخب الأخرى من فترة المملكة الحديثة. يتم تعيين رقم لكل مقبرة مسبوقًا بـ 'KV' (وادي الملوك)."
                }
            },
            {
                "id": "visitor_center",
                "name": {
                    "en": "Visitor Center",
                    "ar": "مركز الزوار"
                },
                "description": {
                    "en": "A modern facility with educational displays about the valley, tomb construction, and the ancient Egyptian afterlife. Includes a detailed model of the valley showing the locations and layouts of the tombs.",
                    "ar": "منشأة حديثة بها معروضات تعليمية حول الوادي، وبناء المقابر، والحياة الآخرة المصرية القديمة. يتضمن نموذجًا مفصلاً للوادي يوضح مواقع المقابر وتصميماتها."
                }
            }
        ],
        "images": [
            "valley_of_kings_aerial.jpg",
            "tutankhamun_tomb.jpg",
            "ramesses_VI_tomb.jpg",
            "valley_entrance.jpg"
        ],
        "tags": ["tombs", "pharaohs", "ancient", "archaeology", "New Kingdom", "necropolis"],
        "last_updated": datetime.now().isoformat()
    },
    {
        "id": "karnak_temple",
        "name": {
            "en": "Karnak Temple Complex",
            "ar": "مجمع معبد الكرنك"
        },
        "type": "temple_complex",
        "location": {
            "city": "Luxor",
            "city_ar": "الأقصر",
            "region": "Upper Egypt",
            "region_ar": "صعيد مصر",
            "coordinates": {
                "latitude": 25.7188,
                "longitude": 32.6571
            }
        },
        "description": {
            "en": "The Karnak Temple Complex is a vast collection of ruined temples, chapels, pylons, and other structures, located near Luxor. Building at the complex began in the reign of Senusret I in the Middle Kingdom and continued through the Ptolemaic period. The area around Karnak was the ancient Egyptians' main place of worship of the eighteenth dynasty Theban Triad, centered on the god Amun-Ra.",
            "ar": "مجمع معبد الكرنك هو مجموعة واسعة من المعابد المتهدمة والمصليات والأبراج والهياكل الأخرى، الواقعة بالقرب من الأقصر. بدأ البناء في المجمع في عهد سنوسرت الأول في المملكة الوسطى واستمر خلال الفترة البطلمية. كانت المنطقة المحيطة بالكرنك المكان الرئيسي للعبادة لدى المصريين القدماء للثالوث الطيبي من الأسرة الثامنة عشرة، الذي يتمحور حول الإله آمون رع."
        },
        "history": {
            "en": "The Karnak Temple Complex consists of a vast mix of temples, chapels, pylons, and other buildings dating from around 2055 BC to around 100 AD. It was the main religious center of the ancient Egyptian god Amun-Ra in Thebes during the New Kingdom. The complex developed over more than 1,000 years, principally by Amenhotep III and Ramesses II. It covers more than 100 hectares, and is the second-largest ancient religious site in the world, after Angkor Wat in Cambodia.",
            "ar": "يتكون مجمع معبد الكرنك من مزيج واسع من المعابد والمصليات والأبراج والمباني الأخرى التي يعود تاريخها من حوالي 2055 قبل الميلاد إلى حوالي 100 ميلادي. كان المركز الديني الرئيسي للإله المصري القديم آمون رع في طيبة خلال المملكة الحديثة. تطور المجمع على مدى أكثر من 1000 عام، بشكل رئيسي من قبل أمنحتب الثالث ورمسيس الثاني. يغطي أكثر من 100 هكتار، وهو ثاني أكبر موقع ديني قديم في العالم، بعد أنغكور وات في كمبوديا."
        },
        "practical_info": {
            "opening_hours": "6:00 AM - 5:30 PM (Summer), 6:00 AM - 5:00 PM (Winter)",
            "ticket_prices": {
                "foreigners": {
                    "adults": "200 EGP",
                    "students": "100 EGP"
                },
                "egyptians": {
                    "adults": "30 EGP",
                    "students": "15 EGP"
                }
            },
            "best_time_to_visit": "Early morning to avoid crowds and heat. October to April for more comfortable temperatures.",
            "duration": "3-4 hours for a complete visit",
            "facilities": [
                "Restrooms",
                "Kiosks for refreshments",
                "Souvenir shops",
                "Visitor center"
            ],
            "accessibility": {
                "en": "The site is partially accessible. Main pathways are paved, but some areas have uneven terrain and steps. The size of the complex can be challenging for those with mobility issues.",
                "ar": "الموقع متاح جزئياً. الممرات الرئيسية معبدة، ولكن بعض المناطق بها تضاريس غير مستوية ودرجات. يمكن أن يكون حجم المجمع صعبًا لأولئك الذين يعانون من مشاكل في الحركة."
            },
            "visitor_tips": {
                "en": "Visit early or late in the day to avoid the midday heat. The site is enormous, so plan your route or hire a guide. Don't miss the Sound and Light Show in the evening. Bring water, sun protection, and comfortable walking shoes. Photography is allowed but tripods may require a permit.",
                "ar": "قم بالزيارة في وقت مبكر أو متأخر من اليوم لتجنب حرارة منتصف النهار. الموقع ضخم، لذا خطط لمسارك أو استأجر مرشدًا. لا تفوت عرض الصوت والضوء في المساء. أحضر الماء، والحماية من الشمس، وأحذية مريحة للمشي. التصوير مسموح به ولكن قد تتطلب الحوامل الثلاثية تصريحًا."
            }
        },
        "must_see": [
            {
                "id": "hypostyle_hall",
                "name": {
                    "en": "Great Hypostyle Hall",
                    "ar": "قاعة الأعمدة الكبرى"
                },
                "description": {
                    "en": "One of the most impressive features of Karnak, this massive hall covers 5,000 square meters and contains 134 massive columns arranged in 16 rows. The central 12 columns are 21 meters tall. The hall was built by Seti I and completed by Ramesses II, with incredible relief carvings throughout.",
                    "ar": "واحدة من أكثر ميزات الكرنك إثارة للإعجاب، تغطي هذه القاعة الضخمة 5000 متر مربع وتحتوي على 134 عمودًا ضخمًا مرتبة في 16 صفًا. الأعمدة المركزية الـ 12 يبلغ ارتفاعها 21 مترًا. تم بناء القاعة بواسطة سيتي الأول وأكملها رمسيس الثاني، مع نقوش بارزة مذهلة في جميع أنحائها."
                }
            },
            {
                "id": "sacred_lake",
                "name": {
                    "en": "Sacred Lake",
                    "ar": "البحيرة المقدسة"
                },
                "description": {
                    "en": "A large man-made lake that was used by priests for ritual purification and sacred ceremonies. The lake is rectangle-shaped and lined with stone. Near the lake is a giant scarab statue dedicated to Khepri, the god of the rising sun.",
                    "ar": "بحيرة كبيرة من صنع الإنسان كانت تستخدم من قبل الكهنة للتطهير الطقسي والاحتفالات المقدسة. البحيرة مستطيلة الشكل ومبطنة بالحجر. بالقرب من البحيرة يوجد تمثال جعران عملاق مخصص لخبري، إله الشمس المشرقة."
                }
            },
            {
                "id": "obelisks",
                "name": {
                    "en": "Obelisks",
                    "ar": "المسلات"
                },
                "description": {
                    "en": "Karnak contains several obelisks, including the Obelisk of Hatshepsut, one of the tallest in Egypt at 29 meters. These monolithic monuments were carved from single pieces of granite and topped with gold or electrum to catch the sun's rays.",
                    "ar": "يحتوي الكرنك على العديد من المسلات، بما في ذلك مسلة حتشبسوت، واحدة من أطول المسلات في مصر بارتفاع 29 مترًا. تم نحت هذه النصب التذكارية المونوليثية من قطع واحدة من الجرانيت وتم تغطيتها بالذهب أو الإلكتروم لالتقاط أشعة الشمس."
                }
            }
        ],
        "components": [
            {
                "id": "precinct_of_amun_ra",
                "name": {
                    "en": "Precinct of Amun-Ra",
                    "ar": "منطقة آمون رع"
                },
                "description": {
                    "en": "The largest of the precincts of the temple complex, dedicated to Amun-Ra, the chief deity of the Theban Triad. This area contains most of the famous structures including the Great Hypostyle Hall.",
                    "ar": "أكبر مناطق مجمع المعبد، المخصصة لآمون رع، الإله الرئيسي للثالوث الطيبي. تحتوي هذه المنطقة على معظم الهياكل المشهورة بما في ذلك قاعة الأعمدة الكبرى."
                }
            },
            {
                "id": "precinct_of_mut",
                "name": {
                    "en": "Precinct of Mut",
                    "ar": "منطقة موت"
                },
                "description": {
                    "en": "Located to the south of the Amun-Ra precinct, this area is dedicated to the goddess Mut, wife of Amun-Ra. It contains a sacred lake in a crescent shape.",
                    "ar": "تقع جنوب منطقة آمون رع، وهذه المنطقة مخصصة للإلهة موت، زوجة آمون رع. تحتوي على بحيرة مقدسة على شكل هلال."
                }
            },
            {
                "id": "precinct_of_montu",
                "name": {
                    "en": "Precinct of Montu",
                    "ar": "منطقة مونتو"
                },
                "description": {
                    "en": "The northernmost precinct, dedicated to the falcon-headed war god Montu. This is the oldest part of the complex but less well-preserved than other areas.",
                    "ar": "المنطقة الشمالية، المخصصة لإله الحرب ذو رأس الصقر مونتو. هذا هو أقدم جزء من المجمع ولكنه أقل حفظًا من المناطق الأخرى."
                }
            }
        ],
        "images": [
            "karnak_aerial.jpg",
            "hypostyle_hall.jpg",
            "sacred_lake.jpg",
            "obelisks.jpg"
        ],
        "tags": ["temple", "ancient", "Amun-Ra", "Thebes", "UNESCO", "New Kingdom"],
        "last_updated": datetime.now().isoformat()
    }
]

# Save historical attractions
for attraction in historical_attractions:
    filename = f"./data/attractions/historical/{attraction['id']}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(attraction, f, ensure_ascii=False, indent=2)

print("Historical attractions data populated successfully.")