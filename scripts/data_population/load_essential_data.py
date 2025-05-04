#!/usr/bin/env python3
"""
Essential Data Loading Script for Egypt Tourism Chatbot

This script loads essential tourism data into the PostgreSQL database.
It creates a minimal set of attractions, cities, accommodations, and restaurants.
"""
import sys
import time
import json
from pathlib import Path

# Add the src directory to the Python path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.logger import get_logger
from src.knowledge.database import DatabaseManager, DatabaseType

# Set up logging
logger = get_logger(__name__)

def generate_random_embedding(dimension=1536):
    """
    Generate a random embedding vector for testing.

    Args:
        dimension: Dimensionality of the embedding vector

    Returns:
        Random embedding vector
    """
    import numpy as np
    # Generate random values and convert to a Python list of floats
    return [float(x) for x in np.random.rand(dimension)]

def main():
    """Main function to load essential data into the database."""
    start_time = time.time()
    logger.info("Starting essential data loading process...")

    # Initialize database manager
    db_manager = DatabaseManager()

    # Ensure we're using PostgreSQL
    if db_manager.db_type != DatabaseType.POSTGRES:
        logger.error(f"PostgreSQL database not configured. Current type: {db_manager.db_type}")
        return

    logger.info("Connected to PostgreSQL database")

    # Override the text_to_embedding method to use random embeddings
    db_manager.text_to_embedding = lambda text: generate_random_embedding(1536)

    # Essential data to load
    essential_data = {
        "cities": [
            {
                "id": "cairo",
                "name_en": "Cairo",
                "name_ar": "القاهرة",
                "region": "Lower Egypt",
                "latitude": 30.0444,
                "longitude": 31.2357,
                "description_en": "Cairo is the capital of Egypt and the largest city in the Arab world. It's famous for its ancient monuments, museums, and vibrant culture.",
                "description_ar": "القاهرة هي عاصمة مصر وأكبر مدينة في العالم العربي. تشتهر بآثارها القديمة ومتاحفها وثقافتها النابضة بالحياة."
            },
            {
                "id": "luxor",
                "name_en": "Luxor",
                "name_ar": "الأقصر",
                "region": "Upper Egypt",
                "latitude": 25.6872,
                "longitude": 32.6396,
                "description_en": "Luxor is known as the world's greatest open-air museum, with the ruins of the temple complexes at Karnak and Luxor.",
                "description_ar": "تُعرف الأقصر بأنها أعظم متحف مفتوح في العالم، مع أطلال مجمعات المعابد في الكرنك والأقصر."
            },
            {
                "id": "aswan",
                "name_en": "Aswan",
                "name_ar": "أسوان",
                "region": "Upper Egypt",
                "latitude": 24.0889,
                "longitude": 32.8998,
                "description_en": "Aswan is a city on the Nile River, known for its beautiful Nile Valley scenery, significant archaeological sites, and its peaceful atmosphere.",
                "description_ar": "أسوان هي مدينة على نهر النيل، تشتهر بمناظر وادي النيل الجميلة، والمواقع الأثرية المهمة، وأجوائها الهادئة."
            },
            {
                "id": "alexandria",
                "name_en": "Alexandria",
                "name_ar": "الإسكندرية",
                "region": "Mediterranean Coast",
                "latitude": 31.2001,
                "longitude": 29.9187,
                "description_en": "Alexandria is a Mediterranean port city in Egypt, founded by Alexander the Great. It's known for its Bibliotheca Alexandrina and Greco-Roman ruins.",
                "description_ar": "الإسكندرية هي مدينة ميناء متوسطية في مصر، أسسها الإسكندر الأكبر. تشتهر بمكتبة الإسكندرية وآثارها اليونانية الرومانية."
            }
        ],
        "attractions": [
            {
                "id": "pyramids_of_giza",
                "name_en": "Pyramids of Giza",
                "name_ar": "أهرامات الجيزة",
                "type": "historical",
                "city": "Cairo",
                "region": "Lower Egypt",
                "latitude": 29.9792,
                "longitude": 31.1342,
                "description_en": "The Pyramids of Giza are the only remaining structures of the Seven Wonders of the Ancient World. They were built as tombs for the pharaohs Khufu, Khafre, and Menkaure.",
                "description_ar": "أهرامات الجيزة هي الهياكل المتبقية الوحيدة من عجائب الدنيا السبع في العالم القديم. بنيت كمقابر للفراعنة خوفو وخفرع ومنقرع."
            },
            {
                "id": "karnak_temple",
                "name_en": "Karnak Temple",
                "name_ar": "معبد الكرنك",
                "type": "historical",
                "city": "Luxor",
                "region": "Upper Egypt",
                "latitude": 25.7188,
                "longitude": 32.6571,
                "description_en": "Karnak Temple is a vast temple complex dedicated primarily to Amun-Ra, a form of the sun god. It's one of the largest religious buildings ever constructed.",
                "description_ar": "معبد الكرنك هو مجمع معبد ضخم مخصص بشكل أساسي لآمون رع، أحد أشكال إله الشمس. وهو أحد أكبر المباني الدينية التي تم بناؤها على الإطلاق."
            },
            {
                "id": "abu_simbel",
                "name_en": "Abu Simbel Temples",
                "name_ar": "معابد أبو سمبل",
                "type": "historical",
                "city": "Aswan",
                "region": "Upper Egypt",
                "latitude": 22.3372,
                "longitude": 31.6258,
                "description_en": "Abu Simbel temples are two massive rock-cut temples in southern Egypt, built by Pharaoh Ramesses II. They were relocated in the 1960s to avoid being submerged by Lake Nasser.",
                "description_ar": "معابد أبو سمبل هي معبدان ضخمان منحوتان في الصخر في جنوب مصر، بناهما الفرعون رمسيس الثاني. تم نقلهما في الستينيات لتجنب غمرهما ببحيرة ناصر."
            },
            {
                "id": "bibliotheca_alexandrina",
                "name_en": "Bibliotheca Alexandrina",
                "name_ar": "مكتبة الإسكندرية",
                "type": "cultural",
                "city": "Alexandria",
                "region": "Mediterranean Coast",
                "latitude": 31.2089,
                "longitude": 29.9092,
                "description_en": "The Bibliotheca Alexandrina is a major library and cultural center located on the shore of the Mediterranean Sea. It's a commemoration of the ancient Library of Alexandria.",
                "description_ar": "مكتبة الإسكندرية هي مكتبة رئيسية ومركز ثقافي يقع على شاطئ البحر المتوسط. وهي تخليد لمكتبة الإسكندرية القديمة."
            }
        ],
        "accommodations": [
            {
                "id": "mena_house_hotel",
                "name_en": "Marriott Mena House",
                "name_ar": "ماريوت منا هاوس",
                "type": "luxury",
                "city": "Cairo",
                "region": "Lower Egypt",
                "latitude": 29.9852,
                "longitude": 31.1301,
                "description_en": "Historic luxury hotel with stunning views of the Pyramids of Giza. Features elegant rooms, multiple restaurants, and a swimming pool.",
                "description_ar": "فندق فاخر تاريخي مع إطلالات رائعة على أهرامات الجيزة. يضم غرفًا أنيقة ومطاعم متعددة وحمام سباحة.",
                "stars": 5,
                "price_min": 200,
                "price_max": 500
            },
            {
                "id": "winter_palace_luxor",
                "name_en": "Sofitel Winter Palace Luxor",
                "name_ar": "سوفيتيل وينتر بالاس الأقصر",
                "type": "luxury",
                "city": "Luxor",
                "region": "Upper Egypt",
                "latitude": 25.6961,
                "longitude": 32.6372,
                "description_en": "Historic luxury hotel built in 1886 on the banks of the Nile, near Luxor Temple. Features Victorian architecture, lush gardens, and multiple restaurants.",
                "description_ar": "فندق تاريخي فاخر بني عام 1886 على ضفاف النيل بالقرب من معبد الأقصر. يتميز بالهندسة المعمارية الفيكتورية وحدائق غناء ومطاعم متعددة.",
                "stars": 5,
                "price_min": 150,
                "price_max": 400
            }
        ],
        "restaurants": [
            {
                "id": "abou_el_sid_cairo",
                "name_en": "Abou El Sid",
                "name_ar": "أبو السيد",
                "cuisine": "Egyptian",
                "type": "restaurant",
                "city": "Cairo",
                "region": "Lower Egypt",
                "latitude": 30.0459,
                "longitude": 31.2243,
                "description_en": "Traditional Egyptian restaurant serving authentic local cuisine in a nostalgic atmosphere with vintage decor.",
                "description_ar": "مطعم مصري تقليدي يقدم المأكولات المحلية الأصيلة في أجواء حنين إلى الماضي مع ديكور عتيق."
            },
            {
                "id": "sofra_luxor",
                "name_en": "Sofra Restaurant",
                "name_ar": "مطعم سفرة",
                "cuisine": "Egyptian",
                "type": "restaurant",
                "city": "Luxor",
                "region": "Upper Egypt",
                "latitude": 25.6995,
                "longitude": 32.6421,
                "description_en": "Authentic Egyptian restaurant located in a restored 1930s house, serving traditional dishes in a charming setting.",
                "description_ar": "مطعم مصري أصيل يقع في منزل تم ترميمه من ثلاثينيات القرن الماضي، يقدم أطباقًا تقليدية في أجواء ساحرة."
            }
        ]
    }

    # Load cities
    for city in essential_data["cities"]:
        try:
            # Generate embedding
            combined_text = f"{city['name_en']} {city['description_en']} {city['name_ar']} {city['description_ar']}"
            embedding = db_manager.text_to_embedding(combined_text)

            # Prepare data for JSON fields
            data_json = json.dumps({
                "name": {"en": city["name_en"], "ar": city["name_ar"]},
                "description": {"en": city["description_en"], "ar": city["description_ar"]}
            })

            # Insert into database
            query = """
                INSERT INTO cities (
                    id, name_en, name_ar, region,
                    latitude, longitude,
                    data, embedding
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s,
                    %s::jsonb, %s::vector
                ) ON CONFLICT(id) DO UPDATE SET
                    name_en=EXCLUDED.name_en,
                    name_ar=EXCLUDED.name_ar,
                    region=EXCLUDED.region,
                    latitude=EXCLUDED.latitude,
                    longitude=EXCLUDED.longitude,
                    data=EXCLUDED.data,
                    embedding=EXCLUDED.embedding,
                    updated_at=CURRENT_TIMESTAMP
            """

            params = (
                city["id"], city["name_en"], city["name_ar"], city["region"],
                city["latitude"], city["longitude"],
                data_json, embedding
            )

            db_manager.execute_query(query, params)
            logger.info(f"Loaded city: {city['name_en']}")
        except Exception as e:
            logger.error(f"Error loading city {city.get('name_en', 'unknown')}: {str(e)}")

    # Load attractions
    for attraction in essential_data["attractions"]:
        try:
            # Generate embedding
            combined_text = f"{attraction['name_en']} {attraction['description_en']} {attraction['name_ar']} {attraction['description_ar']}"
            embedding = db_manager.text_to_embedding(combined_text)

            # Prepare data for JSON fields
            data_json = json.dumps({
                "name": {"en": attraction["name_en"], "ar": attraction["name_ar"]},
                "description": {"en": attraction["description_en"], "ar": attraction["description_ar"]}
            })

            # Insert into database
            query = """
                INSERT INTO attractions (
                    id, name_en, name_ar, type, city, region,
                    latitude, longitude, description_en, description_ar,
                    data, embedding
                ) VALUES (
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s::jsonb, %s::vector
                ) ON CONFLICT(id) DO UPDATE SET
                    name_en=EXCLUDED.name_en,
                    name_ar=EXCLUDED.name_ar,
                    type=EXCLUDED.type,
                    city=EXCLUDED.city,
                    region=EXCLUDED.region,
                    latitude=EXCLUDED.latitude,
                    longitude=EXCLUDED.longitude,
                    description_en=EXCLUDED.description_en,
                    description_ar=EXCLUDED.description_ar,
                    data=EXCLUDED.data,
                    embedding=EXCLUDED.embedding,
                    updated_at=CURRENT_TIMESTAMP
            """

            params = (
                attraction["id"], attraction["name_en"], attraction["name_ar"], attraction["type"],
                attraction["city"], attraction["region"], attraction["latitude"], attraction["longitude"],
                attraction["description_en"], attraction["description_ar"],
                data_json, embedding
            )

            db_manager.execute_query(query, params)
            logger.info(f"Loaded attraction: {attraction['name_en']}")
        except Exception as e:
            logger.error(f"Error loading attraction {attraction.get('name_en', 'unknown')}: {str(e)}")

    # Load accommodations
    for accommodation in essential_data["accommodations"]:
        try:
            # Generate embedding
            combined_text = f"{accommodation['name_en']} {accommodation['description_en']} {accommodation['name_ar']} {accommodation['description_ar']}"
            embedding = db_manager.text_to_embedding(combined_text)

            # Prepare data for JSON fields
            data_json = json.dumps({
                "name": {"en": accommodation["name_en"], "ar": accommodation["name_ar"]},
                "description": {"en": accommodation["description_en"], "ar": accommodation["description_ar"]}
            })

            # Insert into database
            query = """
                INSERT INTO accommodations (
                    id, name_en, name_ar, type, city, region,
                    latitude, longitude, description_en, description_ar,
                    stars, price_min, price_max, data, embedding
                ) VALUES (
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s::jsonb, %s::vector
                ) ON CONFLICT(id) DO UPDATE SET
                    name_en=EXCLUDED.name_en,
                    name_ar=EXCLUDED.name_ar,
                    type=EXCLUDED.type,
                    city=EXCLUDED.city,
                    region=EXCLUDED.region,
                    latitude=EXCLUDED.latitude,
                    longitude=EXCLUDED.longitude,
                    description_en=EXCLUDED.description_en,
                    description_ar=EXCLUDED.description_ar,
                    stars=EXCLUDED.stars,
                    price_min=EXCLUDED.price_min,
                    price_max=EXCLUDED.price_max,
                    data=EXCLUDED.data,
                    embedding=EXCLUDED.embedding,
                    updated_at=CURRENT_TIMESTAMP
            """

            params = (
                accommodation["id"], accommodation["name_en"], accommodation["name_ar"], accommodation["type"],
                accommodation["city"], accommodation["region"], accommodation["latitude"], accommodation["longitude"],
                accommodation["description_en"], accommodation["description_ar"],
                accommodation["stars"], accommodation["price_min"], accommodation["price_max"],
                data_json, embedding
            )

            db_manager.execute_query(query, params)
            logger.info(f"Loaded accommodation: {accommodation['name_en']}")
        except Exception as e:
            logger.error(f"Error loading accommodation {accommodation.get('name_en', 'unknown')}: {str(e)}")

    # Load restaurants
    for restaurant in essential_data["restaurants"]:
        try:
            # Generate embedding
            combined_text = f"{restaurant['name_en']} {restaurant['description_en']} {restaurant['name_ar']} {restaurant['description_ar']}"
            embedding = db_manager.text_to_embedding(combined_text)

            # Prepare data for JSON fields
            data_json = json.dumps({
                "name": {"en": restaurant["name_en"], "ar": restaurant["name_ar"]},
                "description": {"en": restaurant["description_en"], "ar": restaurant["description_ar"]}
            })

            # Insert into database
            query = """
                INSERT INTO restaurants (
                    id, name_en, name_ar, cuisine, type, city, region,
                    latitude, longitude, description_en, description_ar,
                    data, embedding
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s::jsonb, %s::vector
                ) ON CONFLICT(id) DO UPDATE SET
                    name_en=EXCLUDED.name_en,
                    name_ar=EXCLUDED.name_ar,
                    cuisine=EXCLUDED.cuisine,
                    type=EXCLUDED.type,
                    city=EXCLUDED.city,
                    region=EXCLUDED.region,
                    latitude=EXCLUDED.latitude,
                    longitude=EXCLUDED.longitude,
                    description_en=EXCLUDED.description_en,
                    description_ar=EXCLUDED.description_ar,
                    data=EXCLUDED.data,
                    embedding=EXCLUDED.embedding,
                    updated_at=CURRENT_TIMESTAMP
            """

            params = (
                restaurant["id"], restaurant["name_en"], restaurant["name_ar"], restaurant["cuisine"],
                restaurant["type"], restaurant["city"], restaurant["region"], restaurant["latitude"],
                restaurant["longitude"], restaurant["description_en"], restaurant["description_ar"],
                data_json, embedding
            )

            db_manager.execute_query(query, params)
            logger.info(f"Loaded restaurant: {restaurant['name_en']}")
        except Exception as e:
            logger.error(f"Error loading restaurant {restaurant.get('name_en', 'unknown')}: {str(e)}")

    elapsed_time = time.time() - start_time
    logger.info(f"Data loading completed in {elapsed_time:.2f} seconds")
    logger.info(f"Total entities loaded: {len(essential_data['cities']) + len(essential_data['attractions']) + len(essential_data['accommodations']) + len(essential_data['restaurants'])}")

if __name__ == '__main__':
    main()
