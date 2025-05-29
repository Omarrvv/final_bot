#!/usr/bin/env python3
"""
Script to add more itineraries data to the Egypt Tourism Chatbot database.
This script adds additional itineraries with detailed information.
"""

import os
import sys
import json
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def connect_to_database():
    """Connect to the database."""
    try:
        # Get database connection string from environment variable or use default
        db_uri = os.environ.get("POSTGRES_URI", "postgresql://postgres:postgres@localhost:5432/egypt_chatbot")

        # Connect to the database
        conn = psycopg2.connect(db_uri)
        conn.autocommit = True

        logger.info("✅ Database connection successful")
        return conn
    except Exception as e:
        logger.error(f"❌ Error connecting to database: {str(e)}")
        return None

def get_existing_itineraries(conn):
    """Get existing itineraries from the database."""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT name->>'en' as name FROM itineraries")
            itineraries = cur.fetchall()
            return [itinerary['name'] for itinerary in itineraries]
    except Exception as e:
        logger.error(f"❌ Error getting existing itineraries: {str(e)}")
        return []

def add_itinerary(conn, itinerary_data):
    """Add itinerary to the itineraries table."""
    try:
        # Check if itinerary already exists
        existing_itineraries = get_existing_itineraries(conn)
        if itinerary_data["name"]["en"] in existing_itineraries:
            logger.info(f"Itinerary '{itinerary_data['name']['en']}' already exists, skipping")
            return True

        # Add itinerary
        query = """
        INSERT INTO itineraries (
            name,
            description,
            type_id,
            duration_days,
            difficulty_level,
            target_audience,
            regions,
            cities,
            attractions,
            daily_plans,
            highlights,
            practical_tips,
            budget_range,
            best_seasons,
            images,
            tags,
            is_featured,
            created_at,
            updated_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
        )
        """

        # Convert destinations to regions, cities, attractions
        regions = []
        cities = []
        attractions = []

        if "destinations" in itinerary_data:
            if "cities" in itinerary_data["destinations"]:
                cities = itinerary_data["destinations"]["cities"]
            if "attractions" in itinerary_data["destinations"]:
                attractions = itinerary_data["destinations"]["attractions"]

        # Convert suitable_for to target_audience
        target_audience = itinerary_data.get("suitable_for", {})

        # Convert practical_info to practical_tips
        practical_tips = itinerary_data.get("practical_info", {})

        # Convert estimated_budget to budget_range
        budget_range = itinerary_data.get("estimated_budget", {})

        # Convert best_time_to_visit to best_seasons
        best_seasons = []
        if "best_time_to_visit" in itinerary_data and "seasons" in itinerary_data["best_time_to_visit"]:
            best_seasons = [s.lower().split()[0] for s in itinerary_data["best_time_to_visit"]["seasons"]["en"]]

        params = (
            json.dumps(itinerary_data["name"]),
            json.dumps(itinerary_data["description"]),
            "adventure",  # type_id - using "adventure" for the Red Sea itinerary
            itinerary_data["duration_days"],
            itinerary_data["difficulty_level"],
            json.dumps(target_audience),
            regions,
            cities,
            attractions,
            json.dumps(itinerary_data["day_plans"]),
            json.dumps(itinerary_data["highlights"]),
            json.dumps(practical_tips),
            json.dumps(budget_range),
            best_seasons,
            json.dumps(itinerary_data["images"]),
            itinerary_data["tags"],
            itinerary_data["is_featured"]
        )

        with conn.cursor() as cur:
            cur.execute(query, params)

        logger.info(f"✅ Itinerary '{itinerary_data['name']['en']}' added successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Error adding itinerary: {str(e)}")
        return False

def generate_additional_itineraries():
    """Generate additional itineraries data."""
    return [
        {
            "name": {
                "en": "Egypt's Red Sea Adventure: Hurghada and Sharm El Sheikh",
                "ar": "مغامرة البحر الأحمر المصري: الغردقة وشرم الشيخ"
            },
            "description": {
                "en": "Experience the best of Egypt's Red Sea coast with this 8-day adventure through Hurghada and Sharm El Sheikh. Enjoy world-class diving and snorkeling among vibrant coral reefs, relax on pristine beaches, and embark on exciting desert safaris. This itinerary combines water activities, desert adventures, and luxurious relaxation for the perfect beach holiday with a touch of Egyptian culture.",
                "ar": "استمتع بأفضل ما في ساحل البحر الأحمر المصري مع هذه المغامرة التي تستمر 8 أيام عبر الغردقة وشرم الشيخ. استمتع بالغوص والغطس من الدرجة العالمية بين الشعاب المرجانية النابضة بالحياة، واسترخ على الشواطئ البكر، وانطلق في رحلات سفاري صحراوية مثيرة. يجمع هذا المسار بين أنشطة المياه ومغامرات الصحراء والاسترخاء الفاخر لقضاء عطلة شاطئية مثالية مع لمسة من الثقافة المصرية."
            },
            "category_id": "adventure",
            "duration_days": 8,
            "difficulty_level": "moderate",
            "suitable_for": {
                "en": ["Beach lovers", "Diving enthusiasts", "Adventure seekers", "Couples", "Families with older children"],
                "ar": ["عشاق الشاطئ", "هواة الغوص", "الباحثون عن المغامرة", "الأزواج", "العائلات مع أطفال أكبر سنًا"]
            },
            "destinations": {
                "cities": ["Hurghada", "Sharm El Sheikh"],
                "attractions": ["Giftun Island", "Ras Mohammed National Park", "Tiran Island", "Colored Canyon", "Bedouin Villages"]
            },
            "day_plans": {
                "day_1": {
                    "title": {
                        "en": "Arrival in Hurghada",
                        "ar": "الوصول إلى الغردقة"
                    },
                    "activities": [
                        {
                            "time": "Afternoon",
                            "description": {
                                "en": "Arrive at Hurghada International Airport. Transfer to your beachfront resort.",
                                "ar": "الوصول إلى مطار الغردقة الدولي. الانتقال إلى منتجعك على الشاطئ."
                            }
                        },
                        {
                            "time": "Evening",
                            "description": {
                                "en": "Welcome dinner at the resort with views of the Red Sea. Briefing about the upcoming activities.",
                                "ar": "عشاء ترحيبي في المنتجع مع إطلالات على البحر الأحمر. إحاطة حول الأنشطة القادمة."
                            }
                        }
                    ]
                },
                "day_2": {
                    "title": {
                        "en": "Snorkeling and Beach Day",
                        "ar": "الغطس ويوم الشاطئ"
                    },
                    "activities": [
                        {
                            "time": "Morning",
                            "description": {
                                "en": "After breakfast, join a snorkeling trip to nearby coral reefs. Introduction to Red Sea marine life.",
                                "ar": "بعد الإفطار، انضم إلى رحلة غطس إلى الشعاب المرجانية القريبة. مقدمة للحياة البحرية في البحر الأحمر."
                            }
                        },
                        {
                            "time": "Afternoon",
                            "description": {
                                "en": "Lunch at a beachside restaurant. Free time to relax on the beach or by the pool.",
                                "ar": "الغداء في مطعم على الشاطئ. وقت حر للاسترخاء على الشاطئ أو بجانب حمام السباحة."
                            }
                        },
                        {
                            "time": "Evening",
                            "description": {
                                "en": "Dinner at the resort. Optional evening entertainment.",
                                "ar": "العشاء في المنتجع. ترفيه مسائي اختياري."
                            }
                        }
                    ]
                },
                "day_3": {
                    "title": {
                        "en": "Giftun Island Excursion",
                        "ar": "رحلة إلى جزيرة جفتون"
                    },
                    "activities": [
                        {
                            "time": "Morning",
                            "description": {
                                "en": "Full-day boat trip to Giftun Island National Park. Snorkeling at multiple sites with vibrant coral gardens.",
                                "ar": "رحلة بالقارب ليوم كامل إلى منتزه جزيرة جفتون الوطني. الغطس في مواقع متعددة مع حدائق مرجانية نابضة بالحياة."
                            }
                        },
                        {
                            "time": "Midday",
                            "description": {
                                "en": "Beach time on the pristine white sand beaches of Giftun Island. Lunch served on the boat.",
                                "ar": "وقت الشاطئ على شواطئ الرمال البيضاء البكر في جزيرة جفتون. يتم تقديم الغداء على القارب."
                            }
                        },
                        {
                            "time": "Afternoon",
                            "description": {
                                "en": "More snorkeling opportunities at different reef sites. Return to Hurghada.",
                                "ar": "المزيد من فرص الغطس في مواقع الشعاب المرجانية المختلفة. العودة إلى الغردقة."
                            }
                        },
                        {
                            "time": "Evening",
                            "description": {
                                "en": "Dinner at a local seafood restaurant in Hurghada Marina.",
                                "ar": "العشاء في مطعم محلي للمأكولات البحرية في مارينا الغردقة."
                            }
                        }
                    ]
                },
                "day_4": {
                    "title": {
                        "en": "Desert Safari Adventure",
                        "ar": "مغامرة سفاري الصحراء"
                    },
                    "activities": [
                        {
                            "time": "Morning",
                            "description": {
                                "en": "After breakfast, depart for a desert safari. Quad biking across the Eastern Desert landscapes.",
                                "ar": "بعد الإفطار، المغادرة لرحلة سفاري صحراوية. ركوب الدراجات الرباعية عبر مناظر الصحراء الشرقية."
                            }
                        },
                        {
                            "time": "Midday",
                            "description": {
                                "en": "Visit a Bedouin village. Learn about traditional desert life. Enjoy Bedouin tea and bread.",
                                "ar": "زيارة قرية بدوية. تعرف على الحياة الصحراوية التقليدية. استمتع بالشاي والخبز البدوي."
                            }
                        },
                        {
                            "time": "Afternoon",
                            "description": {
                                "en": "Camel ride in the desert. Return to Hurghada.",
                                "ar": "ركوب الجمال في الصحراء. العودة إلى الغردقة."
                            }
                        },
                        {
                            "time": "Evening",
                            "description": {
                                "en": "Dinner at the resort. Pack for tomorrow's transfer to Sharm El Sheikh.",
                                "ar": "العشاء في المنتجع. التحضير لنقل الغد إلى شرم الشيخ."
                            }
                        }
                    ]
                },
                "day_5": {
                    "title": {
                        "en": "Transfer to Sharm El Sheikh",
                        "ar": "الانتقال إلى شرم الشيخ"
                    },
                    "activities": [
                        {
                            "time": "Morning",
                            "description": {
                                "en": "After breakfast, check out from your Hurghada resort. Transfer to Sharm El Sheikh by domestic flight or ferry (depending on availability).",
                                "ar": "بعد الإفطار، المغادرة من منتجع الغردقة. الانتقال إلى شرم الشيخ بواسطة رحلة داخلية أو عبارة (حسب التوفر)."
                            }
                        },
                        {
                            "time": "Afternoon",
                            "description": {
                                "en": "Arrive in Sharm El Sheikh. Check in at your resort. Free time to explore the resort facilities.",
                                "ar": "الوصول إلى شرم الشيخ. تسجيل الوصول في المنتجع. وقت حر لاستكشاف مرافق المنتجع."
                            }
                        },
                        {
                            "time": "Evening",
                            "description": {
                                "en": "Dinner at the resort. Optional walk through Naama Bay or SOHO Square for shopping and entertainment.",
                                "ar": "العشاء في المنتجع. نزهة اختيارية عبر خليج نعمة أو ساحة سوهو للتسوق والترفيه."
                            }
                        }
                    ]
                },
                "day_6": {
                    "title": {
                        "en": "Ras Mohammed National Park",
                        "ar": "منتزه رأس محمد الوطني"
                    },
                    "activities": [
                        {
                            "time": "Morning",
                            "description": {
                                "en": "Early departure for a boat trip to Ras Mohammed National Park, one of the world's most famous diving destinations.",
                                "ar": "المغادرة المبكرة لرحلة بالقارب إلى منتزه رأس محمد الوطني، أحد أشهر وجهات الغوص في العالم."
                            }
                        },
                        {
                            "time": "Midday",
                            "description": {
                                "en": "Snorkeling or diving at multiple sites within the park. Lunch served on the boat.",
                                "ar": "الغطس أو الغوص في مواقع متعددة داخل المنتزه. يتم تقديم الغداء على القارب."
                            }
                        },
                        {
                            "time": "Afternoon",
                            "description": {
                                "en": "More water activities and relaxation time. Return to Sharm El Sheikh.",
                                "ar": "المزيد من الأنشطة المائية ووقت الاسترخاء. العودة إلى شرم الشيخ."
                            }
                        },
                        {
                            "time": "Evening",
                            "description": {
                                "en": "Dinner at a local restaurant in Sharm El Sheikh.",
                                "ar": "العشاء في مطعم محلي في شرم الشيخ."
                            }
                        }
                    ]
                },
                "day_7": {
                    "title": {
                        "en": "Colored Canyon and Blue Hole",
                        "ar": "الوادي الملون والثقب الأزرق"
                    },
                    "activities": [
                        {
                            "time": "Morning",
                            "description": {
                                "en": "Excursion to the Colored Canyon in the Sinai Peninsula. Guided hike through the spectacular rock formations.",
                                "ar": "رحلة إلى الوادي الملون في شبه جزيرة سيناء. نزهة مع مرشد عبر تكوينات الصخور المذهلة."
                            }
                        },
                        {
                            "time": "Midday",
                            "description": {
                                "en": "Continue to Dahab for lunch at a beachside restaurant.",
                                "ar": "الاستمرار إلى دهب لتناول الغداء في مطعم على الشاطئ."
                            }
                        },
                        {
                            "time": "Afternoon",
                            "description": {
                                "en": "Visit the famous Blue Hole for snorkeling (safe areas only). Free time to explore Dahab's bohemian atmosphere.",
                                "ar": "زيارة الثقب الأزرق الشهير للغطس (المناطق الآمنة فقط). وقت حر لاستكشاف أجواء دهب البوهيمية."
                            }
                        },
                        {
                            "time": "Evening",
                            "description": {
                                "en": "Return to Sharm El Sheikh. Farewell dinner at a premium restaurant.",
                                "ar": "العودة إلى شرم الشيخ. عشاء وداعي في مطعم فاخر."
                            }
                        }
                    ]
                },
                "day_8": {
                    "title": {
                        "en": "Departure",
                        "ar": "المغادرة"
                    },
                    "activities": [
                        {
                            "time": "Morning",
                            "description": {
                                "en": "Free time depending on your departure schedule. Last-minute shopping or beach time.",
                                "ar": "وقت حر حسب جدول مغادرتك. تسوق اللحظة الأخيرة أو وقت الشاطئ."
                            }
                        },
                        {
                            "time": "Afternoon",
                            "description": {
                                "en": "Transfer to Sharm El Sheikh International Airport for your departure flight.",
                                "ar": "الانتقال إلى مطار شرم الشيخ الدولي لرحلة المغادرة."
                            }
                        }
                    ]
                }
            },
            "highlights": {
                "en": [
                    "Snorkel or dive in some of the world's most beautiful coral reefs",
                    "Relax on the pristine beaches of Giftun Island",
                    "Experience the thrill of quad biking in the Eastern Desert",
                    "Visit authentic Bedouin communities and learn about their way of life",
                    "Explore the underwater wonders of Ras Mohammed National Park",
                    "Hike through the colorful rock formations of the Colored Canyon",
                    "Discover the famous Blue Hole, one of the world's most renowned diving sites"
                ],
                "ar": [
                    "الغطس أو الغوص في بعض من أجمل الشعاب المرجانية في العالم",
                    "الاسترخاء على الشواطئ البكر لجزيرة جفتون",
                    "تجربة إثارة ركوب الدراجات الرباعية في الصحراء الشرقية",
                    "زيارة المجتمعات البدوية الأصيلة والتعرف على طريقة حياتهم",
                    "استكشاف عجائب تحت الماء في منتزه رأس محمد الوطني",
                    "المشي لمسافات طويلة عبر تكوينات الصخور الملونة في الوادي الملون",
                    "اكتشاف الثقب الأزرق الشهير، أحد أشهر مواقع الغوص في العالم"
                ]
            },
            "practical_info": {
                "accommodation": {
                    "en": "Recommended accommodations include 4-5 star beach resorts in Hurghada and Sharm El Sheikh. Options range from family-friendly resorts to adults-only luxury properties.",
                    "ar": "تشمل أماكن الإقامة الموصى بها منتجعات شاطئية من فئة 4-5 نجوم في الغردقة وشرم الشيخ. تتراوح الخيارات من منتجعات مناسبة للعائلات إلى عقارات فاخرة للبالغين فقط."
                },
                "transportation": {
                    "en": "Transfers between airports and hotels are included. The transfer from Hurghada to Sharm El Sheikh can be by domestic flight (45 minutes) or ferry (2-3 hours) depending on availability and preference.",
                    "ar": "يتم تضمين التنقلات بين المطارات والفنادق. يمكن أن يكون النقل من الغردقة إلى شرم الشيخ بواسطة رحلة داخلية (45 دقيقة) أو عبارة (2-3 ساعات) حسب التوفر والتفضيل."
                },
                "best_time_to_visit": {
                    "en": "The Red Sea coast can be visited year-round. Spring (March-May) and autumn (September-November) offer the most pleasant temperatures. Summer (June-August) can be very hot but is ideal for water activities.",
                    "ar": "يمكن زيارة ساحل البحر الأحمر على مدار السنة. يوفر الربيع (مارس-مايو) والخريف (سبتمبر-نوفمبر) درجات الحرارة الأكثر متعة. يمكن أن يكون الصيف (يونيو-أغسطس) حارًا جدًا ولكنه مثالي للأنشطة المائية."
                }
            },
            "estimated_budget": {
                "budget": {
                    "amount": "800-1200",
                    "currency": "USD",
                    "per": "person",
                    "includes": {
                        "en": ["3-star accommodations", "Some activities", "Basic transportation", "Some meals"],
                        "ar": ["إقامة 3 نجوم", "بعض الأنشطة", "النقل الأساسي", "بعض الوجبات"]
                    }
                },
                "mid_range": {
                    "amount": "1500-2500",
                    "currency": "USD",
                    "per": "person",
                    "includes": {
                        "en": ["4-star beach resorts", "Most activities and excursions", "All transportation", "Most meals"],
                        "ar": ["منتجعات شاطئية 4 نجوم", "معظم الأنشطة والرحلات", "جميع وسائل النقل", "معظم الوجبات"]
                    }
                },
                "luxury": {
                    "amount": "3000-5000",
                    "currency": "USD",
                    "per": "person",
                    "includes": {
                        "en": ["5-star luxury resorts", "Private guides and excursions", "Premium transportation", "All meals at top restaurants", "Additional spa treatments and premium activities"],
                        "ar": ["منتجعات فاخرة 5 نجوم", "مرشدين خاصين ورحلات", "نقل متميز", "جميع الوجبات في أفضل المطاعم", "علاجات سبا إضافية وأنشطة متميزة"]
                    }
                }
            },
            "best_time_to_visit": {
                "seasons": {
                    "en": ["Spring (March-May)", "Fall (September-November)", "Winter (December-February)"],
                    "ar": ["الربيع (مارس-مايو)", "الخريف (سبتمبر-نوفمبر)", "الشتاء (ديسمبر-فبراير)"]
                },
                "notes": {
                    "en": "The Red Sea coast enjoys warm weather year-round. Water temperatures are comfortable for swimming even in winter. Summer months can be extremely hot (35-45°C) but are still popular for beach holidays.",
                    "ar": "يتمتع ساحل البحر الأحمر بطقس دافئ على مدار السنة. درجات حرارة الماء مريحة للسباحة حتى في فصل الشتاء. يمكن أن تكون أشهر الصيف شديدة الحرارة (35-45 درجة مئوية) ولكنها لا تزال شائعة لقضاء العطلات الشاطئية."
                }
            },
            "images": {
                "main": "red_sea_adventure_main.jpg",
                "gallery": [
                    "red_sea_adventure_hurghada.jpg",
                    "red_sea_adventure_giftun.jpg",
                    "red_sea_adventure_ras_mohammed.jpg",
                    "red_sea_adventure_colored_canyon.jpg"
                ]
            },
            "tags": ["red sea", "hurghada", "sharm el sheikh", "diving", "snorkeling", "beach", "desert", "adventure"],
            "is_featured": True
        }
    ]

def main():
    """Main function to add more itineraries data to the database."""
    logger.info("Starting to add more itineraries data to the database")

    # Connect to the database
    conn = connect_to_database()
    if not conn:
        logger.error("Cannot continue without database connection")
        return

    # Generate additional itineraries data
    additional_itineraries = generate_additional_itineraries()

    # Add itineraries
    added_count = 0
    for itinerary in additional_itineraries:
        if add_itinerary(conn, itinerary):
            added_count += 1

    logger.info(f"✅ Added {added_count} new itineraries to the database")

    # Test if the itineraries were added correctly
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT COUNT(*) FROM itineraries")
            total_count = cur.fetchone()["count"]
            logger.info(f"Total itineraries in the database: {total_count}")

            cur.execute("SELECT name->>'en' as name, category_id FROM itineraries ORDER BY name->>'en'")
            itineraries = cur.fetchall()
            logger.info("Itineraries in the database:")
            for i, itinerary in enumerate(itineraries):
                logger.info(f"  {i+1}. {itinerary['name']} (Category: {itinerary['category_id']})")
    except Exception as e:
        logger.error(f"❌ Error testing itineraries data: {str(e)}")

    # Close the database connection
    conn.close()

if __name__ == "__main__":
    main()
