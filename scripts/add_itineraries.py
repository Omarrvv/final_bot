#!/usr/bin/env python3
"""
Script to add itineraries to the database.
"""

import os
import sys
import json
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database connection string
DB_CONNECTION_STRING = "postgresql://postgres:postgres@localhost:5432/egypt_chatbot"

# Itineraries to add
ITINERARIES_TO_ADD = [
    # Cultural Itinerary
    {
        "type_id": "cultural",
        "name": {
            "en": "Egyptian Arts & Crafts Journey",
            "ar": "رحلة الفنون والحرف المصرية"
        },
        "description": {
            "en": "Immerse yourself in Egypt's rich artistic heritage with this 5-day journey through traditional crafts and contemporary arts. From ancient techniques preserved for generations to modern expressions of Egyptian identity, this itinerary takes you beyond the typical tourist path to connect with local artisans and creators. Visit workshops where papyrus is still made using ancient methods, explore vibrant art galleries showcasing emerging talent, and try your hand at traditional crafts under the guidance of master artisans. This cultural exploration offers unique insights into Egypt's creative soul and provides opportunities to support local craftspeople by purchasing authentic, handmade souvenirs directly from their creators.",
            "ar": "انغمس في التراث الفني الغني لمصر مع هذه الرحلة التي تستغرق 5 أيام عبر الحرف التقليدية والفنون المعاصرة. من التقنيات القديمة المحفوظة لأجيال إلى التعبيرات الحديثة عن الهوية المصرية، يأخذك هذا المسار إلى ما وراء المسار السياحي النموذجي للتواصل مع الحرفيين والمبدعين المحليين. قم بزيارة ورش العمل حيث لا يزال يتم صنع ورق البردي باستخدام الطرق القديمة، واستكشف معارض الفنون النابضة بالحياة التي تعرض المواهب الناشئة، وجرب يدك في الحرف التقليدية تحت إشراف الحرفيين المهرة. يقدم هذا الاستكشاف الثقافي رؤى فريدة لروح مصر الإبداعية ويوفر فرصًا لدعم الحرفيين المحليين من خلال شراء الهدايا التذكارية الأصلية المصنوعة يدويًا مباشرة من صانعيها."
        },
        "duration_days": 5,
        "regions": ["cairo", "alexandria", "fayoum"],
        "cities": ["cairo", "alexandria", "fayoum"],
        "attractions": [],
        "restaurants": [],
        "accommodations": [],
        "transportation_types": ["private_car", "train"],
        "daily_plans": {
            "day_1": {
                "title": {
                    "en": "Cairo's Traditional Crafts",
                    "ar": "الحرف التقليدية في القاهرة"
                },
                "description": {
                    "en": "Begin your artistic journey in Islamic Cairo, exploring the historic Khan el-Khalili bazaar and its surrounding workshops. Visit artisans creating intricate metalwork, watch as coppersmiths hammer decorative pieces, and see how traditional Egyptian lanterns (fanous) are crafted. In the afternoon, visit the Fustat Traditional Crafts Center to observe pottery making using techniques dating back to Pharaonic times. End your day with a visit to a papyrus institute to learn about this ancient Egyptian art form and try your hand at creating your own papyrus painting.",
                    "ar": "ابدأ رحلتك الفنية في القاهرة الإسلامية، واستكشف سوق خان الخليلي التاريخي وورش العمل المحيطة به. قم بزيارة الحرفيين الذين يصنعون أعمال معدنية معقدة، وشاهد كيف يقوم النحاسون بطرق القطع الزخرفية، وشاهد كيفية صنع الفوانيس المصرية التقليدية. في فترة ما بعد الظهر، قم بزيارة مركز الفسطاط للحرف التقليدية لمشاهدة صناعة الفخار باستخدام تقنيات تعود إلى العصور الفرعونية. أنهِ يومك بزيارة معهد البردي للتعرف على هذا الفن المصري القديم وتجربة يدك في إنشاء لوحة البردي الخاصة بك."
                },
                "activities": [
                    {
                        "time": "09:00 - 12:00",
                        "activity": {
                            "en": "Explore Khan el-Khalili craft workshops",
                            "ar": "استكشاف ورش الحرف في خان الخليلي"
                        }
                    },
                    {
                        "time": "12:30 - 14:00",
                        "activity": {
                            "en": "Lunch at a traditional Egyptian restaurant",
                            "ar": "الغداء في مطعم مصري تقليدي"
                        }
                    },
                    {
                        "time": "14:30 - 16:30",
                        "activity": {
                            "en": "Visit Fustat Traditional Crafts Center",
                            "ar": "زيارة مركز الفسطاط للحرف التقليدية"
                        }
                    },
                    {
                        "time": "17:00 - 19:00",
                        "activity": {
                            "en": "Papyrus making workshop",
                            "ar": "ورشة عمل صناعة البردي"
                        }
                    }
                ],
                "accommodation": {
                    "en": "Cairo hotel",
                    "ar": "فندق في القاهرة"
                },
                "meals": {
                    "en": "Breakfast at hotel, lunch at local restaurant",
                    "ar": "الإفطار في الفندق، الغداء في مطعم محلي"
                }
            },
            "day_2": {
                "title": {
                    "en": "Contemporary Art Scene in Cairo",
                    "ar": "مشهد الفن المعاصر في القاهرة"
                },
                "description": {
                    "en": "Today, discover Cairo's vibrant contemporary art scene. Begin at the Townhouse Gallery, a pioneering independent art space in downtown Cairo. Continue to Zamalek, an upscale neighborhood on Gezira Island, to visit multiple galleries including Safarkhan Gallery and Picasso Gallery. After lunch, head to the Cairo Opera House complex to explore the Museum of Modern Egyptian Art, housing over 10,000 works by Egyptian artists. End your day with a visit to Al-Masar Gallery for a glimpse of cutting-edge Egyptian art, followed by an evening cultural performance.",
                    "ar": "اليوم، اكتشف مشهد الفن المعاصر النابض بالحياة في القاهرة. ابدأ بمعرض تاون هاوس، وهو مساحة فنية مستقلة رائدة في وسط القاهرة. استمر إلى الزمالك، وهي منطقة راقية في جزيرة الجزيرة، لزيارة معارض متعددة بما في ذلك معرض سفرخان ومعرض بيكاسو. بعد الغداء، توجه إلى مجمع دار الأوبرا المصرية لاستكشاف متحف الفن المصري الحديث، الذي يضم أكثر من 10,000 عمل لفنانين مصريين. أنهِ يومك بزيارة معرض المسار للحصول على لمحة عن الفن المصري المتطور، يليه عرض ثقافي مسائي."
                },
                "activities": [
                    {
                        "time": "10:00 - 11:30",
                        "activity": {
                            "en": "Visit Townhouse Gallery",
                            "ar": "زيارة معرض تاون هاوس"
                        }
                    },
                    {
                        "time": "12:00 - 14:00",
                        "activity": {
                            "en": "Explore Zamalek art galleries",
                            "ar": "استكشاف معارض الفن في الزمالك"
                        }
                    },
                    {
                        "time": "14:00 - 15:30",
                        "activity": {
                            "en": "Lunch at a contemporary Egyptian restaurant",
                            "ar": "الغداء في مطعم مصري معاصر"
                        }
                    },
                    {
                        "time": "16:00 - 18:00",
                        "activity": {
                            "en": "Museum of Modern Egyptian Art",
                            "ar": "متحف الفن المصري الحديث"
                        }
                    },
                    {
                        "time": "18:30 - 20:00",
                        "activity": {
                            "en": "Al-Masar Gallery and evening cultural performance",
                            "ar": "معرض المسار وعرض ثقافي مسائي"
                        }
                    }
                ],
                "accommodation": {
                    "en": "Cairo hotel",
                    "ar": "فندق في القاهرة"
                },
                "meals": {
                    "en": "Breakfast at hotel, lunch at contemporary restaurant",
                    "ar": "الإفطار في الفندق، الغداء في مطعم معاصر"
                }
            },
            "day_3": {
                "title": {
                    "en": "Alexandria's Cultural Heritage",
                    "ar": "التراث الثقافي في الإسكندرية"
                },
                "description": {
                    "en": "Travel to Alexandria, Egypt's Mediterranean gem with a rich multicultural history. Visit the Bibliotheca Alexandrina, which houses several art galleries and museums. Explore the Alexandria National Museum to understand the city's diverse cultural influences. After lunch, visit local jewelry workshops specializing in traditional Alexandrian silver filigree work. End your day with a stroll along the Corniche to see street artists and performers, followed by a visit to a local cultural center for a traditional music performance.",
                    "ar": "سافر إلى الإسكندرية، جوهرة مصر المتوسطية ذات التاريخ متعدد الثقافات الغني. قم بزيارة مكتبة الإسكندرية، التي تضم العديد من المعارض الفنية والمتاحف. استكشف المتحف القومي بالإسكندرية لفهم التأثيرات الثقافية المتنوعة للمدينة. بعد الغداء، قم بزيارة ورش المجوهرات المحلية المتخصصة في أعمال الفضة الإسكندرية التقليدية. أنهِ يومك بنزهة على طول الكورنيش لرؤية فناني الشارع والمؤدين، تليها زيارة إلى مركز ثقافي محلي لحضور عرض موسيقي تقليدي."
                },
                "activities": [
                    {
                        "time": "08:00 - 10:30",
                        "activity": {
                            "en": "Train to Alexandria",
                            "ar": "القطار إلى الإسكندرية"
                        }
                    },
                    {
                        "time": "11:00 - 13:00",
                        "activity": {
                            "en": "Visit Bibliotheca Alexandrina art galleries",
                            "ar": "زيارة معارض الفن في مكتبة الإسكندرية"
                        }
                    },
                    {
                        "time": "13:30 - 14:30",
                        "activity": {
                            "en": "Lunch at a seafood restaurant",
                            "ar": "الغداء في مطعم للمأكولات البحرية"
                        }
                    },
                    {
                        "time": "15:00 - 16:30",
                        "activity": {
                            "en": "Alexandria National Museum",
                            "ar": "المتحف القومي بالإسكندرية"
                        }
                    },
                    {
                        "time": "17:00 - 18:30",
                        "activity": {
                            "en": "Visit traditional jewelry workshops",
                            "ar": "زيارة ورش المجوهرات التقليدية"
                        }
                    },
                    {
                        "time": "19:00 - 21:00",
                        "activity": {
                            "en": "Corniche walk and evening cultural performance",
                            "ar": "نزهة على الكورنيش وعرض ثقافي مسائي"
                        }
                    }
                ],
                "accommodation": {
                    "en": "Alexandria hotel",
                    "ar": "فندق في الإسكندرية"
                },
                "meals": {
                    "en": "Breakfast at hotel, lunch at seafood restaurant",
                    "ar": "الإفطار في الفندق، الغداء في مطعم للمأكولات البحرية"
                }
            },
            "day_4": {
                "title": {
                    "en": "Fayoum Oasis Crafts",
                    "ar": "حرف واحة الفيوم"
                },
                "description": {
                    "en": "Travel to Fayoum Oasis, a rural area known for its natural beauty and thriving craft traditions. Visit Tunis Village, a pottery center where local artisans create distinctive ceramics. Participate in a pottery workshop to learn traditional techniques. After lunch, explore local weaving workshops where women create colorful textiles using traditional looms. Visit a local NGO supporting the revival of traditional crafts and providing economic opportunities for local women. End your day with a sunset boat ride on Lake Qarun, the oldest natural lake in the world.",
                    "ar": "سافر إلى واحة الفيوم، وهي منطقة ريفية معروفة بجمالها الطبيعي وتقاليد الحرف المزدهرة. قم بزيارة قرية تونس، وهي مركز للفخار حيث يصنع الحرفيون المحليون السيراميك المميز. شارك في ورشة عمل للفخار لتعلم التقنيات التقليدية. بعد الغداء، استكشف ورش النسيج المحلية حيث تصنع النساء المنسوجات الملونة باستخدام أنوال تقليدية. قم بزيارة منظمة غير حكومية محلية تدعم إحياء الحرف التقليدية وتوفر فرصًا اقتصادية للنساء المحليات. أنهِ يومك برحلة قارب عند غروب الشمس في بحيرة قارون، أقدم بحيرة طبيعية في العالم."
                },
                "activities": [
                    {
                        "time": "08:00 - 10:00",
                        "activity": {
                            "en": "Drive to Fayoum Oasis",
                            "ar": "القيادة إلى واحة الفيوم"
                        }
                    },
                    {
                        "time": "10:30 - 12:30",
                        "activity": {
                            "en": "Visit Tunis Village pottery workshops",
                            "ar": "زيارة ورش الفخار في قرية تونس"
                        }
                    },
                    {
                        "time": "12:30 - 14:00",
                        "activity": {
                            "en": "Pottery making workshop",
                            "ar": "ورشة عمل صناعة الفخار"
                        }
                    },
                    {
                        "time": "14:00 - 15:00",
                        "activity": {
                            "en": "Lunch at a local restaurant",
                            "ar": "الغداء في مطعم محلي"
                        }
                    },
                    {
                        "time": "15:30 - 17:00",
                        "activity": {
                            "en": "Visit weaving workshops and local craft NGO",
                            "ar": "زيارة ورش النسيج ومنظمة الحرف المحلية غير الحكومية"
                        }
                    },
                    {
                        "time": "17:30 - 19:00",
                        "activity": {
                            "en": "Sunset boat ride on Lake Qarun",
                            "ar": "رحلة قارب عند غروب الشمس في بحيرة قارون"
                        }
                    }
                ],
                "accommodation": {
                    "en": "Fayoum ecolodge",
                    "ar": "نزل بيئي في الفيوم"
                },
                "meals": {
                    "en": "Breakfast at hotel, lunch at local restaurant, dinner at ecolodge",
                    "ar": "الإفطار في الفندق، الغداء في مطعم محلي، العشاء في النزل البيئي"
                }
            },
            "day_5": {
                "title": {
                    "en": "Return to Cairo and Farewell",
                    "ar": "العودة إلى القاهرة والوداع"
                },
                "description": {
                    "en": "On your final day, return to Cairo with a deeper appreciation of Egypt's artistic heritage. Visit the Egyptian Textile Museum to see historic fabrics and garments from various periods of Egyptian history. Spend your afternoon at the Khan el-Khalili bazaar for last-minute souvenir shopping, where you can apply your new knowledge to select authentic, high-quality crafts. End your artistic journey with a farewell dinner featuring traditional Egyptian music and dance.",
                    "ar": "في يومك الأخير، عد إلى القاهرة مع تقدير أعمق للتراث الفني المصري. قم بزيارة متحف النسيج المصري لرؤية الأقمشة والملابس التاريخية من فترات مختلفة من التاريخ المصري. اقضِ فترة ما بعد الظهر في سوق خان الخليلي للتسوق في اللحظة الأخيرة للهدايا التذكارية، حيث يمكنك تطبيق معرفتك الجديدة لاختيار الحرف الأصيلة عالية الجودة. أنهِ رحلتك الفنية بعشاء وداعي يتميز بالموسيقى والرقص المصري التقليدي."
                },
                "activities": [
                    {
                        "time": "08:00 - 10:00",
                        "activity": {
                            "en": "Return to Cairo",
                            "ar": "العودة إلى القاهرة"
                        }
                    },
                    {
                        "time": "10:30 - 12:30",
                        "activity": {
                            "en": "Visit Egyptian Textile Museum",
                            "ar": "زيارة متحف النسيج المصري"
                        }
                    },
                    {
                        "time": "12:30 - 14:00",
                        "activity": {
                            "en": "Lunch at a local restaurant",
                            "ar": "الغداء في مطعم محلي"
                        }
                    },
                    {
                        "time": "14:30 - 17:30",
                        "activity": {
                            "en": "Souvenir shopping at Khan el-Khalili",
                            "ar": "التسوق للهدايا التذكارية في خان الخليلي"
                        }
                    },
                    {
                        "time": "19:00 - 21:30",
                        "activity": {
                            "en": "Farewell dinner with traditional music and dance",
                            "ar": "عشاء وداعي مع الموسيقى والرقص التقليدي"
                        }
                    }
                ],
                "accommodation": {
                    "en": "N/A (departure day)",
                    "ar": "غير متاح (يوم المغادرة)"
                },
                "meals": {
                    "en": "Breakfast at hotel, lunch at local restaurant, farewell dinner",
                    "ar": "الإفطار في الفندق، الغداء في مطعم محلي، عشاء وداعي"
                }
            }
        },
        "budget_range": {
            "economy": {
                "min": 500,
                "max": 700,
                "currency": "USD"
            },
            "standard": {
                "min": 700,
                "max": 1000,
                "currency": "USD"
            },
            "luxury": {
                "min": 1000,
                "max": 1500,
                "currency": "USD"
            }
        },
        "best_seasons": ["fall", "winter", "spring"],
        "difficulty_level": "easy",
        "target_audience": {
            "en": "Art enthusiasts, cultural travelers, creative individuals, and those interested in traditional crafts and contemporary art",
            "ar": "عشاق الفن، المسافرين الثقافيين، الأفراد المبدعين، والمهتمين بالحرف التقليدية والفن المعاصر"
        },
        "highlights": {
            "en": "Hands-on craft workshops, visits to artists' studios, exploration of both traditional and contemporary Egyptian art, unique shopping opportunities for authentic crafts",
            "ar": "ورش عمل حرفية عملية، زيارات إلى استوديوهات الفنانين، استكشاف الفن المصري التقليدي والمعاصر، فرص تسوق فريدة للحرف الأصيلة"
        },
        "practical_tips": {
            "en": "Bring comfortable walking shoes as you'll be exploring many workshops and galleries. Consider bringing an extra bag for craft purchases. Many workshops accept credit cards, but bring cash for smaller vendors. Respect artisans by asking permission before taking photos in their workshops.",
            "ar": "أحضر أحذية مريحة للمشي لأنك ستستكشف العديد من ورش العمل والمعارض. فكر في إحضار حقيبة إضافية لمشتريات الحرف. تقبل العديد من ورش العمل بطاقات الائتمان، ولكن أحضر نقودًا للبائعين الأصغر. احترم الحرفيين من خلال طلب الإذن قبل التقاط الصور في ورش عملهم."
        },
        "tags": ["art", "crafts", "cultural", "workshops", "galleries", "pottery", "textiles", "jewelry"],
        "is_featured": True
    }
]

def connect_to_db():
    """Connect to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(DB_CONNECTION_STRING)
        conn.autocommit = True
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        sys.exit(1)

def add_itineraries(conn, itineraries_list):
    """Add itineraries to the database."""
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get existing itineraries to avoid duplicates
    cursor.execute("SELECT name->>'en' as name_en FROM itineraries")
    existing_names = [row['name_en'] for row in cursor.fetchall()]
    
    # Add itineraries
    added_count = 0
    skipped_count = 0
    
    for itinerary in itineraries_list:
        # Check if itinerary already exists
        if itinerary['name']['en'] in existing_names:
            logger.info(f"Skipping existing itinerary: {itinerary['name']['en']}")
            skipped_count += 1
            continue
        
        # Prepare data
        now = datetime.now()
        
        # Insert itinerary
        try:
            cursor.execute("""
                INSERT INTO itineraries 
                (type_id, name, description, duration_days, regions, cities, 
                attractions, restaurants, accommodations, transportation_types, 
                daily_plans, budget_range, best_seasons, difficulty_level, 
                target_audience, highlights, practical_tips, tags, is_featured, 
                created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                itinerary['type_id'],
                json.dumps(itinerary['name']),
                json.dumps(itinerary['description']),
                itinerary['duration_days'],
                itinerary.get('regions', None),
                itinerary.get('cities', None),
                itinerary.get('attractions', None),
                itinerary.get('restaurants', None),
                itinerary.get('accommodations', None),
                itinerary.get('transportation_types', None),
                json.dumps(itinerary['daily_plans']),
                json.dumps(itinerary.get('budget_range', {})),
                itinerary.get('best_seasons', None),
                itinerary.get('difficulty_level'),
                json.dumps(itinerary.get('target_audience', {})),
                json.dumps(itinerary.get('highlights', {})),
                json.dumps(itinerary.get('practical_tips', {})),
                itinerary.get('tags', None),
                itinerary.get('is_featured', False),
                now,
                now
            ))
            
            itinerary_id = cursor.fetchone()['id']
            logger.info(f"Added itinerary ID {itinerary_id}: {itinerary['name']['en']}")
            added_count += 1
            
        except Exception as e:
            logger.error(f"Error adding itinerary {itinerary['name']['en']}: {e}")
    
    cursor.close()
    return added_count, skipped_count

def main():
    """Main function."""
    logger.info("Starting to add itineraries...")
    
    # Connect to database
    conn = connect_to_db()
    
    # Add itineraries
    added_count, skipped_count = add_itineraries(conn, ITINERARIES_TO_ADD)
    
    # Close connection
    conn.close()
    
    logger.info(f"Added {added_count} new itineraries, skipped {skipped_count} existing itineraries.")

if __name__ == "__main__":
    main()
