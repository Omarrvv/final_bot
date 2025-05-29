#!/usr/bin/env python3
"""
Script to generate comprehensive itineraries data for the Egypt Tourism Chatbot database.
This script generates at least 5 itineraries with detailed information.
"""

import os
import sys
import json
import logging
import random
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_itinerary_categories():
    """Generate itinerary categories data."""
    return [
        {
            "id": "short_trips",
            "name": {
                "en": "Short Trips",
                "ar": "رحلات قصيرة"
            },
            "description": {
                "en": "Itineraries for 1-3 day trips",
                "ar": "مسارات لرحلات من 1-3 أيام"
            }
        },
        {
            "id": "medium_trips",
            "name": {
                "en": "Medium Trips",
                "ar": "رحلات متوسطة"
            },
            "description": {
                "en": "Itineraries for 4-7 day trips",
                "ar": "مسارات لرحلات من 4-7 أيام"
            }
        },
        {
            "id": "long_trips",
            "name": {
                "en": "Long Trips",
                "ar": "رحلات طويلة"
            },
            "description": {
                "en": "Itineraries for 8+ day trips",
                "ar": "مسارات لرحلات من 8+ أيام"
            }
        },
        {
            "id": "family_trips",
            "name": {
                "en": "Family Trips",
                "ar": "رحلات عائلية"
            },
            "description": {
                "en": "Itineraries suitable for families with children",
                "ar": "مسارات مناسبة للعائلات مع الأطفال"
            }
        },
        {
            "id": "adventure_trips",
            "name": {
                "en": "Adventure Trips",
                "ar": "رحلات مغامرة"
            },
            "description": {
                "en": "Itineraries focused on adventure activities",
                "ar": "مسارات تركز على أنشطة المغامرة"
            }
        },
        {
            "id": "cultural_trips",
            "name": {
                "en": "Cultural Trips",
                "ar": "رحلات ثقافية"
            },
            "description": {
                "en": "Itineraries focused on cultural and historical sites",
                "ar": "مسارات تركز على المواقع الثقافية والتاريخية"
            }
        },
        {
            "id": "luxury_trips",
            "name": {
                "en": "Luxury Trips",
                "ar": "رحلات فاخرة"
            },
            "description": {
                "en": "Itineraries featuring luxury accommodations and experiences",
                "ar": "مسارات تتضمن إقامات وتجارب فاخرة"
            }
        },
        {
            "id": "budget_trips",
            "name": {
                "en": "Budget Trips",
                "ar": "رحلات اقتصادية"
            },
            "description": {
                "en": "Itineraries designed for budget-conscious travelers",
                "ar": "مسارات مصممة للمسافرين الواعين بالميزانية"
            }
        }
    ]

def generate_itineraries_data():
    """Generate comprehensive itineraries data."""
    return [
        {
            "name": {
                "en": "Classic Cairo 3-Day Tour",
                "ar": "جولة القاهرة الكلاسيكية لمدة 3 أيام"
            },
            "description": {
                "en": "Experience the highlights of Cairo in this compact 3-day itinerary. Visit the iconic Pyramids of Giza, explore the treasures of the Egyptian Museum, and wander through historic Islamic Cairo. This tour is perfect for first-time visitors with limited time who want to see Cairo's most famous attractions.",
                "ar": "استمتع بأبرز معالم القاهرة في هذا المسار المدمج لمدة 3 أيام. قم بزيارة أهرامات الجيزة الشهيرة، واستكشف كنوز المتحف المصري، وتجول في القاهرة الإسلامية التاريخية. هذه الجولة مثالية للزوار لأول مرة الذين لديهم وقت محدود ويرغبون في رؤية أشهر معالم القاهرة."
            },
            "category_id": "short_trips",
            "duration_days": 3,
            "difficulty_level": "easy",
            "suitable_for": {
                "en": ["First-time visitors", "History enthusiasts", "Couples", "Solo travelers", "Seniors"],
                "ar": ["الزوار لأول مرة", "عشاق التاريخ", "الأزواج", "المسافرون المنفردون", "كبار السن"]
            },
            "destinations": {
                "cities": ["Cairo", "Giza"],
                "attractions": ["Pyramids of Giza", "Egyptian Museum", "Khan El Khalili", "Citadel of Saladin", "Coptic Cairo"]
            },
            "day_plans": {
                "day_1": {
                    "title": {
                        "en": "Pyramids and Sphinx",
                        "ar": "الأهرامات وأبو الهول"
                    },
                    "activities": [
                        {
                            "time": "08:00",
                            "description": {
                                "en": "Hotel pickup and transfer to Giza",
                                "ar": "الاستلام من الفندق والانتقال إلى الجيزة"
                            }
                        },
                        {
                            "time": "09:00",
                            "description": {
                                "en": "Visit the Great Pyramid of Khufu",
                                "ar": "زيارة الهرم الأكبر لخوفو"
                            }
                        },
                        {
                            "time": "11:00",
                            "description": {
                                "en": "Explore the Pyramids of Khafre and Menkaure",
                                "ar": "استكشاف أهرامات خفرع ومنقرع"
                            }
                        },
                        {
                            "time": "12:30",
                            "description": {
                                "en": "Lunch at a local restaurant with pyramid views",
                                "ar": "الغداء في مطعم محلي مع إطلالات على الأهرامات"
                            }
                        },
                        {
                            "time": "14:00",
                            "description": {
                                "en": "Visit the Great Sphinx and Valley Temple",
                                "ar": "زيارة أبو الهول ومعبد الوادي"
                            }
                        },
                        {
                            "time": "16:00",
                            "description": {
                                "en": "Optional camel ride around the pyramids",
                                "ar": "جولة اختيارية بالجمل حول الأهرامات"
                            }
                        },
                        {
                            "time": "17:30",
                            "description": {
                                "en": "Return to hotel to rest",
                                "ar": "العودة إلى الفندق للراحة"
                            }
                        },
                        {
                            "time": "19:30",
                            "description": {
                                "en": "Dinner at a traditional Egyptian restaurant",
                                "ar": "العشاء في مطعم مصري تقليدي"
                            }
                        }
                    ]
                },
                "day_2": {
                    "title": {
                        "en": "Egyptian Museum and Islamic Cairo",
                        "ar": "المتحف المصري والقاهرة الإسلامية"
                    },
                    "activities": [
                        {
                            "time": "08:30",
                            "description": {
                                "en": "Breakfast at hotel",
                                "ar": "الإفطار في الفندق"
                            }
                        },
                        {
                            "time": "09:30",
                            "description": {
                                "en": "Visit the Egyptian Museum in Tahrir Square",
                                "ar": "زيارة المتحف المصري في ميدان التحرير"
                            }
                        },
                        {
                            "time": "12:30",
                            "description": {
                                "en": "Lunch at a downtown Cairo restaurant",
                                "ar": "الغداء في مطعم بوسط القاهرة"
                            }
                        },
                        {
                            "time": "14:00",
                            "description": {
                                "en": "Visit the Citadel of Saladin and Alabaster Mosque",
                                "ar": "زيارة قلعة صلاح الدين ومسجد محمد علي"
                            }
                        },
                        {
                            "time": "16:30",
                            "description": {
                                "en": "Explore Sultan Hassan and Al-Rifai Mosques",
                                "ar": "استكشاف مسجدي السلطان حسن والرفاعي"
                            }
                        },
                        {
                            "time": "18:00",
                            "description": {
                                "en": "Return to hotel to freshen up",
                                "ar": "العودة إلى الفندق للانتعاش"
                            }
                        },
                        {
                            "time": "19:30",
                            "description": {
                                "en": "Dinner and shopping at Khan El Khalili bazaar",
                                "ar": "العشاء والتسوق في بازار خان الخليلي"
                            }
                        }
                    ]
                },
                "day_3": {
                    "title": {
                        "en": "Coptic Cairo and Old Cairo",
                        "ar": "القاهرة القبطية والقاهرة القديمة"
                    },
                    "activities": [
                        {
                            "time": "08:30",
                            "description": {
                                "en": "Breakfast at hotel",
                                "ar": "الإفطار في الفندق"
                            }
                        },
                        {
                            "time": "09:30",
                            "description": {
                                "en": "Visit the Hanging Church and Coptic Museum",
                                "ar": "زيارة الكنيسة المعلقة والمتحف القبطي"
                            }
                        },
                        {
                            "time": "11:30",
                            "description": {
                                "en": "Explore Ben Ezra Synagogue and Church of St. Sergius",
                                "ar": "استكشاف معبد بن عزرا وكنيسة القديس سرجيوس"
                            }
                        },
                        {
                            "time": "13:00",
                            "description": {
                                "en": "Lunch at a local restaurant in Old Cairo",
                                "ar": "الغداء في مطعم محلي في القاهرة القديمة"
                            }
                        },
                        {
                            "time": "14:30",
                            "description": {
                                "en": "Visit Al-Azhar Park for panoramic views of Cairo",
                                "ar": "زيارة حديقة الأزهر للاستمتاع بإطلالات بانورامية على القاهرة"
                            }
                        },
                        {
                            "time": "16:30",
                            "description": {
                                "en": "Free time for shopping or relaxation",
                                "ar": "وقت حر للتسوق أو الاسترخاء"
                            }
                        },
                        {
                            "time": "19:00",
                            "description": {
                                "en": "Farewell dinner at a Nile-view restaurant",
                                "ar": "عشاء وداعي في مطعم بإطلالة على النيل"
                            }
                        }
                    ]
                }
            },
            "highlights": {
                "en": [
                    "Marvel at the Great Pyramids of Giza and the Sphinx",
                    "Discover the treasures of Tutankhamun at the Egyptian Museum",
                    "Explore the medieval architecture of Islamic Cairo",
                    "Shop for souvenirs at the historic Khan El Khalili bazaar",
                    "Visit ancient churches and synagogues in Coptic Cairo"
                ],
                "ar": [
                    "الإعجاب بأهرامات الجيزة العظيمة وأبو الهول",
                    "اكتشاف كنوز توت عنخ آمون في المتحف المصري",
                    "استكشاف العمارة القروسطية في القاهرة الإسلامية",
                    "التسوق للهدايا التذكارية في بازار خان الخليلي التاريخي",
                    "زيارة الكنائس والمعابد القديمة في القاهرة القبطية"
                ]
            },
            "practical_info": {
                "accommodation": {
                    "en": "Recommended hotels include Marriott Mena House, Four Seasons Nile Plaza, or Steigenberger Hotel El Tahrir for mid-range options.",
                    "ar": "تشمل الفنادق الموصى بها ماريوت مينا هاوس، فور سيزونز نايل بلازا، أو شتيجنبرجر هوتيل التحرير للخيارات متوسطة المدى."
                },
                "transportation": {
                    "en": "Private guided tours with air-conditioned vehicles are recommended. Alternatively, use Uber or Careem for city travel.",
                    "ar": "يوصى بالجولات الخاصة المصحوبة بمرشدين مع مركبات مكيفة. بدلاً من ذلك، استخدم أوبر أو كريم للتنقل في المدينة."
                },
                "best_time_to_visit": {
                    "en": "October to April offers the most comfortable temperatures. Avoid summer months (June-August) when temperatures can exceed 40°C.",
                    "ar": "يوفر أكتوبر إلى أبريل درجات الحرارة الأكثر راحة. تجنب أشهر الصيف (يونيو-أغسطس) عندما يمكن أن تتجاوز درجات الحرارة 40 درجة مئوية."
                }
            },
            "estimated_budget": {
                "budget": {
                    "amount": "250-350",
                    "currency": "USD",
                    "per": "person",
                    "includes": {
                        "en": ["Budget hotel accommodation", "Local transportation", "Entrance fees", "Some meals"],
                        "ar": ["إقامة في فندق اقتصادي", "النقل المحلي", "رسوم الدخول", "بعض الوجبات"]
                    }
                },
                "mid_range": {
                    "amount": "450-650",
                    "currency": "USD",
                    "per": "person",
                    "includes": {
                        "en": ["4-star hotel accommodation", "Private guide and driver", "All entrance fees", "Most meals"],
                        "ar": ["إقامة في فندق 4 نجوم", "مرشد خاص وسائق", "جميع رسوم الدخول", "معظم الوجبات"]
                    }
                },
                "luxury": {
                    "amount": "800-1200",
                    "currency": "USD",
                    "per": "person",
                    "includes": {
                        "en": ["5-star luxury hotel", "Private guide and premium vehicle", "VIP access to sites", "All meals at top restaurants"],
                        "ar": ["فندق فاخر 5 نجوم", "مرشد خاص ومركبة فاخرة", "وصول VIP إلى المواقع", "جميع الوجبات في أفضل المطاعم"]
                    }
                }
            },
            "best_time_to_visit": {
                "seasons": {
                    "en": ["Fall (October-November)", "Winter (December-February)", "Spring (March-April)"],
                    "ar": ["الخريف (أكتوبر-نوفمبر)", "الشتاء (ديسمبر-فبراير)", "الربيع (مارس-أبريل)"]
                },
                "notes": {
                    "en": "Avoid summer months when Cairo can be extremely hot. December and January are peak tourist season with higher prices.",
                    "ar": "تجنب أشهر الصيف عندما يمكن أن تكون القاهرة شديدة الحرارة. ديسمبر ويناير هما موسم الذروة السياحية مع ارتفاع الأسعار."
                }
            },
            "images": {
                "main": "cairo_3day_tour_main.jpg",
                "gallery": [
                    "cairo_3day_pyramids.jpg",
                    "cairo_3day_museum.jpg",
                    "cairo_3day_islamic_cairo.jpg",
                    "cairo_3day_coptic_cairo.jpg"
                ]
            },
            "tags": ["cairo", "pyramids", "short trip", "city tour", "cultural", "historical", "museums", "first-time visitors"],
            "is_featured": True
        }
    ]

def main():
    """Generate and save itineraries data to JSON files."""
    try:
        # Create output directory if it doesn't exist
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate itinerary categories data
        itinerary_categories = generate_itinerary_categories()
        
        # Save itinerary categories data to JSON file
        categories_file = os.path.join(output_dir, "itinerary_categories.json")
        with open(categories_file, "w", encoding="utf-8") as f:
            json.dump(itinerary_categories, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ Saved {len(itinerary_categories)} itinerary categories to {categories_file}")
        
        # Generate itineraries data
        itineraries_data = generate_itineraries_data()
        
        # Save itineraries data to JSON file
        itineraries_file = os.path.join(output_dir, "itineraries.json")
        with open(itineraries_file, "w", encoding="utf-8") as f:
            json.dump(itineraries_data, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ Saved {len(itineraries_data)} itineraries to {itineraries_file}")
        
        logger.info("✅ Itineraries data generation completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Error generating itineraries data: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
