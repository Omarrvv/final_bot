#!/usr/bin/env python3
"""
Populate the database with sample Egypt tourism data if it's empty.
"""
import os
import sys
import json
import psycopg2
import logging
import urllib.parse as urlparse
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("data_populator")

# Sample data - major Egypt attractions
SAMPLE_ATTRACTIONS = [
    {
        "id": "pyr001",
        "name_en": "The Great Pyramids of Giza",
        "name_ar": "أهرامات الجيزة",
        "description_en": "The Pyramids of Giza are the only surviving structures of the Seven Wonders of the Ancient World. Built over 4,500 years ago as tombs for the pharaohs Khufu, Khafre, and Menkaure.",
        "description_ar": "أهرامات الجيزة هي الهياكل الوحيدة الباقية من عجائب الدنيا السبع في العالم القديم. بنيت منذ أكثر من 4500 عام كمقابر للفراعنة خوفو وخفرع ومنقرع.",
        "city": "Cairo",
        "location": {"lat": 29.9792, "lon": 31.1342},
        "rating": 4.8,
        "opening_hours": "Daily 8:00 AM - 5:00 PM",
        "entrance_fee": 240,
        "tags": ["ancient", "wonder", "pyramid", "pharaoh", "tomb"],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    },
    {
        "id": "sph001",
        "name_en": "The Great Sphinx of Giza",
        "name_ar": "أبو الهول",
        "description_en": "The Great Sphinx is a limestone statue of a reclining sphinx, a mythical creature with the head of a human and the body of a lion. Facing directly from west to east, it stands on the Giza Plateau on the west bank of the Nile.",
        "description_ar": "أبو الهول هو تمثال من الحجر الجيري لمخلوق أسطوري برأس إنسان وجسم أسد. يواجه مباشرة من الغرب إلى الشرق، ويقع على هضبة الجيزة على الضفة الغربية للنيل.",
        "city": "Cairo",
        "location": {"lat": 29.9753, "lon": 31.1376},
        "rating": 4.7,
        "opening_hours": "Daily 8:00 AM - 5:00 PM",
        "entrance_fee": 100,
        "tags": ["ancient", "statue", "sphinx", "pharaoh", "mythology"],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    },
    {
        "id": "mus001",
        "name_en": "The Egyptian Museum",
        "name_ar": "المتحف المصري",
        "description_en": "The Museum of Egyptian Antiquities, known commonly as the Egyptian Museum, houses the world's largest collection of Pharaonic antiquities, including treasures from Tutankhamun's tomb.",
        "description_ar": "متحف الآثار المصرية، المعروف باسم المتحف المصري، يضم أكبر مجموعة من الآثار الفرعونية في العالم، بما في ذلك كنوز من مقبرة توت عنخ آمون.",
        "city": "Cairo",
        "location": {"lat": 30.0478, "lon": 31.2336},
        "rating": 4.6,
        "opening_hours": "Daily 9:00 AM - 5:00 PM",
        "entrance_fee": 200,
        "tags": ["museum", "antiquities", "pharaoh", "artifacts", "tutankhamun"],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    },
    {
        "id": "lux001",
        "name_en": "Luxor Temple",
        "name_ar": "معبد الأقصر",
        "description_en": "Luxor Temple is a large Ancient Egyptian temple complex located on the east bank of the Nile River in the city today known as Luxor (ancient Thebes).",
        "description_ar": "معبد الأقصر هو مجمع معبد مصري قديم كبير يقع على الضفة الشرقية لنهر النيل في المدينة المعروفة اليوم باسم الأقصر (طيبة القديمة).",
        "city": "Luxor",
        "location": {"lat": 25.6995, "lon": 32.6368},
        "rating": 4.7,
        "opening_hours": "Daily 6:00 AM - 10:00 PM",
        "entrance_fee": 160,
        "tags": ["temple", "ancient", "ruins", "pharaoh", "architecture"],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    },
    {
        "id": "kar001",
        "name_en": "Karnak Temple",
        "name_ar": "معبد الكرنك",
        "description_en": "The Karnak Temple Complex, commonly known as Karnak, is a vast mix of decayed temples, chapels, pylons, and other buildings near Luxor. It was the main place of worship of the Theban Triad.",
        "description_ar": "مجمع معبد الكرنك، المعروف عادة باسم الكرنك، هو مزيج واسع من المعابد المتداعية والمصليات والأبراج والمباني الأخرى بالقرب من الأقصر. كان المكان الرئيسي لعبادة الثالوث الطيبي.",
        "city": "Luxor",
        "location": {"lat": 25.7188, "lon": 32.6571},
        "rating": 4.8,
        "opening_hours": "Daily 6:00 AM - 5:30 PM",
        "entrance_fee": 150,
        "tags": ["temple", "ancient", "ruins", "pharaoh", "religious"],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
]

# Sample data - cities
SAMPLE_CITIES = [
    {
        "id": "cai001",
        "name_en": "Cairo",
        "name_ar": "القاهرة",
        "description_en": "Cairo, Egypt's sprawling capital, is set on the Nile River. At its heart is Tahrir Square and the vast Egyptian Museum, a trove of antiquities including royal mummies and gilded King Tutankhamun artifacts.",
        "description_ar": "القاهرة، عاصمة مصر المترامية الأطراف، تقع على نهر النيل. في قلبها ميدان التحرير والمتحف المصري الضخم، وهو كنز من الآثار القديمة بما في ذلك المومياوات الملكية وكنوز الملك توت عنخ آمون المذهبة.",
        "location": {"lat": 30.0444, "lon": 31.2357},
        "population": 9500000,
        "region": "Greater Cairo",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    },
    {
        "id": "lux002",
        "name_en": "Luxor",
        "name_ar": "الأقصر",
        "description_en": "Luxor is a city on the east bank of the Nile River in southern Egypt. It's on the site of ancient Thebes, the pharaohs' capital at the height of their power, during the 16th–11th centuries B.C.",
        "description_ar": "الأقصر هي مدينة تقع على الضفة الشرقية لنهر النيل في صعيد مصر. تقع على موقع طيبة القديمة، عاصمة الفراعنة في ذروة قوتهم، خلال القرن الـ 16 إلى القرن الـ 11 قبل الميلاد.",
        "location": {"lat": 25.6872, "lon": 32.6396},
        "population": 500000,
        "region": "Upper Egypt",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    },
    {
        "id": "asa001",
        "name_en": "Aswan",
        "name_ar": "أسوان",
        "description_en": "Aswan is a city in the south of Egypt, the capital of the Aswan Governorate. Aswan is a busy market and tourist center located just north of the Aswan Dam on the east bank of the Nile at the first cataract.",
        "description_ar": "أسوان هي مدينة في جنوب مصر، عاصمة محافظة أسوان. أسوان هي مركز سوق وسياحة مزدحم يقع شمال سد أسوان مباشرة على الضفة الشرقية للنيل عند الشلال الأول.",
        "location": {"lat": 24.0889, "lon": 32.8998},
        "population": 300000,
        "region": "Upper Egypt",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
]

# Sample data - hotels/accommodations
SAMPLE_ACCOMMODATIONS = [
    {
        "id": "hot001",
        "name_en": "Marriott Mena House, Cairo",
        "name_ar": "ماريوت منى هاوس، القاهرة",
        "description_en": "Luxury hotel with stunning views of the Great Pyramids. Historic property with beautiful gardens and swimming pools.",
        "description_ar": "فندق فاخر مع إطلالات رائعة على الأهرامات. ملكية تاريخية مع حدائق جميلة وحمامات سباحة.",
        "city": "Cairo",
        "location": {"lat": 29.9850, "lon": 31.1292},
        "rating": 4.6,
        "price_range": "$$$$",
        "amenities": ["pool", "restaurant", "spa", "wifi", "room service"],
        "tags": ["luxury", "pyramid view", "historic", "garden"],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    },
    {
        "id": "hot002",
        "name_en": "Four Seasons Hotel Cairo at Nile Plaza",
        "name_ar": "فندق فورسيزونز القاهرة في نايل بلازا",
        "description_en": "Upscale hotel overlooking the Nile River, offering elegant rooms, multiple dining options, a spa, and an outdoor pool.",
        "description_ar": "فندق راقي يطل على نهر النيل، ويقدم غرفًا أنيقة وخيارات متعددة لتناول الطعام ومنتجع صحي وحمام سباحة خارجي.",
        "city": "Cairo",
        "location": {"lat": 30.0410, "lon": 31.2269},
        "rating": 4.7,
        "price_range": "$$$$",
        "amenities": ["pool", "restaurant", "spa", "wifi", "room service", "fitness center"],
        "tags": ["luxury", "nile view", "business", "family friendly"],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    },
    {
        "id": "hot003",
        "name_en": "Hilton Luxor Resort & Spa",
        "name_ar": "منتجع وسبا هيلتون الأقصر",
        "description_en": "Luxurious resort on the banks of the Nile River with infinity pools overlooking the water, elegant rooms, and a spa.",
        "description_ar": "منتجع فاخر على ضفاف نهر النيل مع حمامات سباحة لا نهائية تطل على الماء وغرف أنيقة ومنتجع صحي.",
        "city": "Luxor",
        "location": {"lat": 25.7157, "lon": 32.6513},
        "rating": 4.5,
        "price_range": "$$$",
        "amenities": ["pool", "restaurant", "spa", "wifi", "room service", "fitness center"],
        "tags": ["resort", "nile view", "spa", "luxury"],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
]

# Sample data - restaurants
SAMPLE_RESTAURANTS = [
    {
        "id": "res001",
        "name_en": "Abou El Sid",
        "name_ar": "أبو السيد",
        "description_en": "Traditional Egyptian cuisine in a stylish setting with authentic décor, serving classics like molokheya, stuffed pigeon, and koshary.",
        "description_ar": "المأكولات المصرية التقليدية في مكان أنيق مع ديكور أصيل، يقدم الكلاسيكيات مثل الملوخية والحمام المحشي والكشري.",
        "city": "Cairo",
        "location": {"lat": 30.0456, "lon": 31.2347},
        "rating": 4.5,
        "price_range": "$$",
        "cuisine": ["Egyptian", "Middle Eastern"],
        "tags": ["traditional", "authentic", "local cuisine"],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    },
    {
        "id": "res002",
        "name_en": "Al Kababgy",
        "name_ar": "الكبابجي",
        "description_en": "Upscale restaurant specializing in grilled meats and traditional Egyptian kebabs with Nile River views.",
        "description_ar": "مطعم راقي متخصص في اللحوم المشوية والكباب المصري التقليدي مع إطلالات على نهر النيل.",
        "city": "Luxor",
        "location": {"lat": 25.6972, "lon": 32.6370},
        "rating": 4.6,
        "price_range": "$$$",
        "cuisine": ["Egyptian", "Grilled", "Middle Eastern"],
        "tags": ["kebab", "grilled meat", "nile view"],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    },
    {
        "id": "res003",
        "name_en": "Zooba",
        "name_ar": "زوبة",
        "description_en": "Modern street food restaurant offering Egyptian classics with a contemporary twist in a vibrant, colorful setting.",
        "description_ar": "مطعم طعام شارع عصري يقدم الكلاسيكيات المصرية بلمسة معاصرة في بيئة نابضة بالحياة وملونة.",
        "city": "Cairo",
        "location": {"lat": 30.0598, "lon": 31.2227},
        "rating": 4.4,
        "price_range": "$",
        "cuisine": ["Egyptian", "Street Food"],
        "tags": ["casual", "street food", "modern", "local cuisine"],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
]

def get_postgres_connection():
    """Get a PostgreSQL connection from environment variables."""
    # Get PostgreSQL connection info
    postgres_uri = os.environ.get("POSTGRES_URI")
    if not postgres_uri:
        logger.info("POSTGRES_URI environment variable not found")
        db_host = os.environ.get("DB_HOST", "db_postgres")
        db_port = os.environ.get("DB_PORT", "5432")
        db_name = os.environ.get("DB_NAME", "egypt_chatbot")
        db_user = os.environ.get("DB_USERNAME", "postgres")
        db_pass = os.environ.get("DB_PASSWORD", "password")
        postgres_uri = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
        logger.info(f"Using constructed URI: postgresql://{db_user}:***@{db_host}:{db_port}/{db_name}")
    else:
        # For security, print the URI without password
        url = urlparse.urlparse(postgres_uri)
        safe_uri = f"{url.scheme}://{url.username}:***@{url.hostname}:{url.port}{url.path}"
        logger.info(f"Using environment URI: {safe_uri}")
    
    try:
        logger.info("Connecting to PostgreSQL...")
        conn = psycopg2.connect(postgres_uri)
        logger.info("Connected to PostgreSQL successfully")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
        return None

def insert_sample_data(conn):
    """Insert sample data into the database."""
    cursor = conn.cursor()
    
    try:
        # Check if tables have data
        cursor.execute("SELECT COUNT(*) FROM attractions")
        attraction_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM cities")
        city_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM accommodations")
        accommodation_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM restaurants")
        restaurant_count = cursor.fetchone()[0]
        
        # Only insert if tables are empty
        if attraction_count == 0:
            logger.info("Attractions table is empty. Inserting sample data...")
            for attraction in SAMPLE_ATTRACTIONS:
                # Convert location to JSON string
                attraction['location'] = json.dumps(attraction['location'])
                attraction['tags'] = json.dumps(attraction['tags'])
                
                cursor.execute("""
                    INSERT INTO attractions (
                        id, name_en, name_ar, description_en, description_ar, 
                        city, location, rating, opening_hours, entrance_fee, tags,
                        created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    attraction['id'], attraction['name_en'], attraction['name_ar'],
                    attraction['description_en'], attraction['description_ar'],
                    attraction['city'], attraction['location'], attraction['rating'],
                    attraction['opening_hours'], attraction['entrance_fee'], attraction['tags'],
                    attraction['created_at'], attraction['updated_at']
                ))
            logger.info(f"Inserted {len(SAMPLE_ATTRACTIONS)} sample attractions")
        else:
            logger.info(f"Attractions table already has {attraction_count} records. Skipping sample data.")
        
        if city_count == 0:
            logger.info("Cities table is empty. Inserting sample data...")
            for city in SAMPLE_CITIES:
                # Convert location to JSON string
                city['location'] = json.dumps(city['location'])
                
                cursor.execute("""
                    INSERT INTO cities (
                        id, name_en, name_ar, description_en, description_ar, 
                        location, population, region, created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    city['id'], city['name_en'], city['name_ar'],
                    city['description_en'], city['description_ar'],
                    city['location'], city['population'], city['region'],
                    city['created_at'], city['updated_at']
                ))
            logger.info(f"Inserted {len(SAMPLE_CITIES)} sample cities")
        else:
            logger.info(f"Cities table already has {city_count} records. Skipping sample data.")
        
        if accommodation_count == 0:
            logger.info("Accommodations table is empty. Inserting sample data...")
            for accommodation in SAMPLE_ACCOMMODATIONS:
                # Convert location and arrays to JSON strings
                accommodation['location'] = json.dumps(accommodation['location'])
                accommodation['amenities'] = json.dumps(accommodation['amenities'])
                accommodation['tags'] = json.dumps(accommodation['tags'])
                
                cursor.execute("""
                    INSERT INTO accommodations (
                        id, name_en, name_ar, description_en, description_ar, 
                        city, location, rating, price_range, amenities, tags,
                        created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    accommodation['id'], accommodation['name_en'], accommodation['name_ar'],
                    accommodation['description_en'], accommodation['description_ar'],
                    accommodation['city'], accommodation['location'], accommodation['rating'],
                    accommodation['price_range'], accommodation['amenities'], accommodation['tags'],
                    accommodation['created_at'], accommodation['updated_at']
                ))
            logger.info(f"Inserted {len(SAMPLE_ACCOMMODATIONS)} sample accommodations")
        else:
            logger.info(f"Accommodations table already has {accommodation_count} records. Skipping sample data.")
        
        if restaurant_count == 0:
            logger.info("Restaurants table is empty. Inserting sample data...")
            for restaurant in SAMPLE_RESTAURANTS:
                # Convert location and arrays to JSON strings
                restaurant['location'] = json.dumps(restaurant['location'])
                restaurant['cuisine'] = json.dumps(restaurant['cuisine'])
                restaurant['tags'] = json.dumps(restaurant['tags'])
                
                cursor.execute("""
                    INSERT INTO restaurants (
                        id, name_en, name_ar, description_en, description_ar, 
                        city, location, rating, price_range, cuisine, tags,
                        created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    restaurant['id'], restaurant['name_en'], restaurant['name_ar'],
                    restaurant['description_en'], restaurant['description_ar'],
                    restaurant['city'], restaurant['location'], restaurant['rating'],
                    restaurant['price_range'], restaurant['cuisine'], restaurant['tags'],
                    restaurant['created_at'], restaurant['updated_at']
                ))
            logger.info(f"Inserted {len(SAMPLE_RESTAURANTS)} sample restaurants")
        else:
            logger.info(f"Restaurants table already has {restaurant_count} records. Skipping sample data.")
        
        # Commit the changes
        conn.commit()
        logger.info("Sample data committed to database")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error inserting sample data: {e}")
        return False
    finally:
        cursor.close()
    
    return True

def main():
    """Main function to populate the database with sample data."""
    # Connect to the database
    conn = get_postgres_connection()
    if not conn:
        return 1
    
    # Insert sample data
    success = insert_sample_data(conn)
    
    # Close the connection
    conn.close()
    
    if success:
        logger.info("✅ Sample data population complete")
        return 0
    else:
        logger.error("❌ Failed to populate sample data")
        return 1

if __name__ == "__main__":
    sys.exit(main())
