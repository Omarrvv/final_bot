#!/usr/bin/env python3
"""
Generate realistic restaurant data for the Egypt Tourism Chatbot database.

This script:
1. Generates realistic restaurant data for different regions in Egypt
2. Inserts the data into the database
3. Verifies the data was inserted correctly
"""

import os
import sys
import json
import random
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timezone, time
from faker import Faker
import numpy as np
from pgvector.psycopg2 import register_vector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Faker
fake = Faker()

# Set random seed for reproducibility
random.seed(42)
np.random.seed(42)

# Target count for data generation
TARGET_RESTAURANTS = 200

def get_postgres_uri():
    """Get PostgreSQL connection URI from environment or use default"""
    return os.getenv("POSTGRES_URI", "postgresql://postgres:postgres@localhost:5432/egypt_chatbot")

def connect_to_db():
    """Connect to PostgreSQL database"""
    postgres_uri = get_postgres_uri()
    logger.info(f"Connecting to PostgreSQL database")
    conn = psycopg2.connect(postgres_uri)
    conn.autocommit = False

    # Register pgvector extension
    register_vector(conn)

    return conn

def get_existing_data(conn):
    """Get existing data from the database"""
    existing_data = {}

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        # Get regions
        cursor.execute("SELECT id, name_en, name FROM regions")
        existing_data['regions'] = cursor.fetchall()

        # Get cities
        cursor.execute("SELECT id, name_en, name, region_id, latitude, longitude FROM cities")
        existing_data['cities'] = cursor.fetchall()

        # Get restaurant types
        cursor.execute("SELECT type, name FROM restaurant_types")
        existing_data['restaurant_types'] = cursor.fetchall()

        # Get cuisines
        cursor.execute("SELECT type, name, popular_dishes FROM cuisines")
        existing_data['cuisines'] = cursor.fetchall()

        # Get existing restaurants
        cursor.execute("SELECT id FROM restaurants")
        existing_data['restaurants'] = cursor.fetchall()

    return existing_data

def generate_embedding():
    """Generate a random embedding vector"""
    # Generate a random 1536-dimensional vector (typical for embeddings)
    embedding = np.random.normal(0, 1, 1536)
    # Normalize to unit length
    embedding = embedding / np.linalg.norm(embedding)
    return embedding

def generate_opening_hours():
    """Generate realistic opening hours"""
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    # Different patterns for opening hours
    patterns = [
        # Standard hours (same every day)
        lambda: {day: {"open": "10:00", "close": "22:00"} for day in days},

        # Weekend different hours
        lambda: {
            **{day: {"open": "10:00", "close": "22:00"} for day in days[:5]},
            **{day: {"open": "12:00", "close": "00:00"} for day in days[5:]}
        },

        # Closed on one day
        lambda: {
            **{day: {"open": "10:00", "close": "22:00"} for day in days if day != "Monday"},
            "Monday": {"closed": True}
        },

        # Split hours (lunch and dinner)
        lambda: {day: {"open": [{"open": "12:00", "close": "15:00"}, {"open": "18:00", "close": "23:00"}]} for day in days}
    ]

    return random.choice(patterns)()

def generate_menu_items(cuisine_type, popular_dishes):
    """Generate menu items based on cuisine type"""
    try:
        # Extract popular dishes from JSONB
        if isinstance(popular_dishes, str):
            popular_dishes = json.loads(popular_dishes)

        # Get English dishes
        dishes = []
        if popular_dishes and 'en' in popular_dishes:
            if isinstance(popular_dishes['en'], list):
                dishes = popular_dishes['en']

        # If no dishes found, use generic ones
        if not dishes:
            dishes = ["Grilled Fish", "Rice Dish", "Vegetable Stew", "Meat Platter", "Soup"]

        # Generate menu items
        menu_items = []
        for dish in dishes:
            menu_items.append({
                "name": {"en": dish, "ar": fake.word()},
                "description": {"en": fake.sentence(), "ar": "وصف الطبق باللغة العربية"},
                "price": round(random.uniform(50, 300), 0),
                "category": random.choice(["Appetizer", "Main Course", "Dessert", "Beverage"]),
                "is_vegetarian": random.choice([True, False, False, False]),
                "is_vegan": random.choice([True, False, False, False, False]),
                "is_spicy": random.choice([True, False, False]),
                "is_signature": random.choice([True, False, False, False])
            })

        # Add some generic items
        for _ in range(5):
            menu_items.append({
                "name": {"en": fake.word().capitalize(), "ar": fake.word()},
                "description": {"en": fake.sentence(), "ar": "وصف الطبق باللغة العربية"},
                "price": round(random.uniform(50, 300), 0),
                "category": random.choice(["Appetizer", "Main Course", "Dessert", "Beverage"]),
                "is_vegetarian": random.choice([True, False, False, False]),
                "is_vegan": random.choice([True, False, False, False, False]),
                "is_spicy": random.choice([True, False, False]),
                "is_signature": random.choice([True, False, False, False])
            })

        return menu_items
    except Exception as e:
        logger.error(f"Error generating menu items: {e}")
        # Return fallback menu items
        return [
            {
                "name": {"en": "House Special", "ar": "طبق خاص"},
                "description": {"en": "Chef's special dish", "ar": "طبق الشيف الخاص"},
                "price": 150,
                "category": "Main Course",
                "is_vegetarian": False,
                "is_vegan": False,
                "is_spicy": False,
                "is_signature": True
            },
            {
                "name": {"en": "Vegetable Platter", "ar": "طبق الخضار"},
                "description": {"en": "Assorted vegetables", "ar": "تشكيلة من الخضروات"},
                "price": 100,
                "category": "Appetizer",
                "is_vegetarian": True,
                "is_vegan": True,
                "is_spicy": False,
                "is_signature": False
            }
        ]

def generate_restaurants(conn, existing_data, count=TARGET_RESTAURANTS):
    """Generate restaurant data"""
    logger.info(f"Generating {count} restaurants")

    # Extract existing restaurant IDs
    existing_restaurant_ids = [restaurant['id'] for restaurant in existing_data['restaurants']]

    # Extract cities, regions, restaurant types, and cuisines
    cities = existing_data['cities']
    restaurant_types = existing_data['restaurant_types']
    cuisines = existing_data['cuisines']

    # Famous Egyptian restaurant names
    famous_names = [
        {"en": "El Fishawy", "ar": "الفيشاوي"},
        {"en": "Abou El Sid", "ar": "أبو السيد"},
        {"en": "Koshary Abou Tarek", "ar": "كشري أبو طارق"},
        {"en": "Felfela", "ar": "فلفلة"},
        {"en": "Sequoia", "ar": "سيكويا"},
        {"en": "Zooba", "ar": "زوبة"},
        {"en": "Kebabgy", "ar": "كبابجي"},
        {"en": "Estoril", "ar": "إستوريل"},
        {"en": "Sofra", "ar": "سفرة"},
        {"en": "Naguib Mahfouz Cafe", "ar": "مقهى نجيب محفوظ"},
        {"en": "Kazaz", "ar": "كزاز"},
        {"en": "El Dahan", "ar": "الدهان"},
        {"en": "Sobhy Kaber", "ar": "صبحي كابر"},
        {"en": "El Refaey", "ar": "الرفاعي"},
        {"en": "El Shabrawy", "ar": "الشبراوي"}
    ]

    # Restaurant name prefixes and suffixes
    name_prefixes = [
        {"en": "El", "ar": "ال"},
        {"en": "Beit", "ar": "بيت"},
        {"en": "Arous", "ar": "عروس"},
        {"en": "Khan", "ar": "خان"},
        {"en": "Qasr", "ar": "قصر"},
        {"en": "Malak", "ar": "ملك"},
        {"en": "Nile", "ar": "النيل"},
        {"en": "Pyramids", "ar": "الأهرامات"},
        {"en": "Cairo", "ar": "القاهرة"},
        {"en": "Alexandria", "ar": "الإسكندرية"}
    ]

    name_suffixes = [
        {"en": "Restaurant", "ar": "مطعم"},
        {"en": "Cafe", "ar": "كافيه"},
        {"en": "Eatery", "ar": "مطعم"},
        {"en": "Kitchen", "ar": "مطبخ"},
        {"en": "Grill", "ar": "مشويات"},
        {"en": "House", "ar": "بيت"},
        {"en": "Palace", "ar": "قصر"},
        {"en": "Garden", "ar": "حديقة"},
        {"en": "Terrace", "ar": "تراس"},
        {"en": "Corner", "ar": "ركن"}
    ]

    restaurants = []

    for i in range(count):
        # Select a random city
        city = random.choice(cities)
        city_id = city['id']
        city_name_en = city['name_en']

        # Get city name from JSONB
        city_name = city_name_en
        if 'name' in city and city['name']:
            if isinstance(city['name'], str):
                try:
                    city_name_json = json.loads(city['name'])
                    if 'en' in city_name_json:
                        city_name = city_name_json['en']
                except:
                    pass
            elif isinstance(city['name'], dict) and 'en' in city['name']:
                city_name = city['name']['en']

        # Get region ID
        region_id = city['region_id']

        # Select a random restaurant type
        restaurant_type = random.choice(restaurant_types)
        type_id = restaurant_type['type']

        # Get type name from JSONB
        type_name = type_id.replace('_', ' ').title()
        if 'name' in restaurant_type and restaurant_type['name']:
            if isinstance(restaurant_type['name'], str):
                try:
                    type_name_json = json.loads(restaurant_type['name'])
                    if 'en' in type_name_json:
                        type_name = type_name_json['en']
                except:
                    pass
            elif isinstance(restaurant_type['name'], dict) and 'en' in restaurant_type['name']:
                type_name = restaurant_type['name']['en']

        # Select a random cuisine
        cuisine = random.choice(cuisines)
        cuisine_id = cuisine['type']

        # Generate a unique restaurant ID
        while True:
            # Use famous names for some restaurants
            if random.random() < 0.2:  # 20% chance for famous names
                name_json = random.choice(famous_names)
                name_en = name_json["en"]
                name_ar = name_json["ar"]
            else:
                # Generate a random name
                prefix = random.choice(name_prefixes)
                suffix = random.choice(name_suffixes)
                middle = fake.word().capitalize()
                name_en = f"{prefix['en']} {middle} {suffix['en']}"
                name_ar = f"{prefix['ar']} {middle} {suffix['ar']}"

            restaurant_id = f"{city_id}_{name_en.lower().replace(' ', '_')}"

            # Truncate if too long
            if len(restaurant_id) > 50:
                restaurant_id = restaurant_id[:50]

            if restaurant_id not in existing_restaurant_ids and restaurant_id not in [r['id'] for r in restaurants]:
                break

        # Generate coordinates near the city
        latitude = city['latitude'] + random.uniform(-0.05, 0.05)
        longitude = city['longitude'] + random.uniform(-0.05, 0.05)

        # Generate price range
        if type_id in ['fine_dining', 'hotel_restaurant']:
            price_range = 'luxury'
        elif type_id in ['casual_dining', 'traditional', 'family_style']:
            price_range = 'mid_range'
        else:
            price_range = 'budget'

        # Generate rating
        rating = round(random.uniform(3.0, 5.0), 1)

        # Generate description
        description_en = f"This {type_name.lower()} is located in {city_name}. "
        description_en += fake.paragraph(nb_sentences=2)

        description_ar = f"يقع هذا المطعم في {city_name}. "
        description_ar += "يقدم أشهى المأكولات المحلية والعالمية في أجواء مميزة."

        # Generate menu items
        menu_items = generate_menu_items(cuisine_id, cuisine.get('popular_dishes'))

        # Generate opening hours
        opening_hours = generate_opening_hours()

        # Create restaurant object
        restaurant = {
            'id': restaurant_id,
            'name_en': name_en,
            'name_ar': name_ar,
            'name': json.dumps({'en': name_en, 'ar': name_ar}),
            'description_en': description_en,
            'description_ar': description_ar,
            'description': json.dumps({'en': description_en, 'ar': description_ar}),
            'cuisine': cuisine_id,
            'cuisine_id': cuisine_id,
            'type': type_id,
            'type_id': type_id,
            'city': city_name,
            'city_id': city_id,
            'region_id': region_id,
            'latitude': latitude,
            'longitude': longitude,
            'price_range': price_range,
            'rating': rating,
            'data': json.dumps({
                'opening_hours': opening_hours,
                'menu_items': menu_items,
                'contact': {
                    'phone': f"+20 {random.randint(10, 99)} {random.randint(1000, 9999)} {random.randint(1000, 9999)}",
                    'email': f"info@{restaurant_id}.com",
                    'website': f"https://www.{restaurant_id}.com",
                    'social_media': {
                        'facebook': f"https://www.facebook.com/{restaurant_id}",
                        'instagram': f"https://www.instagram.com/{restaurant_id}"
                    }
                },
                'features': {
                    'reservations': random.choice([True, False]),
                    'delivery': random.choice([True, False]),
                    'takeout': random.choice([True, False]),
                    'outdoor_seating': random.choice([True, False]),
                    'wifi': random.choice([True, False]),
                    'parking': random.choice([True, False]),
                    'alcohol': random.choice([True, False, False]),  # Less likely in Egypt
                    'smoking': random.choice([True, False]),
                    'wheelchair_accessible': random.choice([True, False])
                },
                'dietary_options': {
                    'vegetarian': random.choice([True, False]),
                    'vegan': random.choice([True, False, False]),  # Less likely
                    'halal': True,  # Most restaurants in Egypt are halal
                    'gluten_free': random.choice([True, False, False, False])  # Less likely
                }
            }),
            'embedding': generate_embedding(),
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
            'user_id': 'system'
        }

        restaurants.append(restaurant)

    # Insert restaurants into database
    with conn.cursor() as cursor:
        for restaurant in restaurants:
            cursor.execute("""
                INSERT INTO restaurants (
                    id, name_en, name_ar, name, description_en, description_ar, description,
                    cuisine, cuisine_id, type, type_id, city, city_id, region_id,
                    latitude, longitude, price_range, rating, data, embedding,
                    created_at, updated_at, user_id
                ) VALUES (
                    %s, %s, %s, %s::jsonb, %s, %s, %s::jsonb,
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s::jsonb, %s,
                    %s, %s, %s
                )
            """, (
                restaurant['id'], restaurant['name_en'], restaurant['name_ar'], restaurant['name'],
                restaurant['description_en'], restaurant['description_ar'], restaurant['description'],
                restaurant['cuisine'], restaurant['cuisine_id'], restaurant['type'], restaurant['type_id'],
                restaurant['city'], restaurant['city_id'], restaurant['region_id'],
                restaurant['latitude'], restaurant['longitude'], restaurant['price_range'], restaurant['rating'],
                restaurant['data'], restaurant['embedding'],
                restaurant['created_at'], restaurant['updated_at'], restaurant['user_id']
            ))

    conn.commit()
    logger.info(f"Inserted {len(restaurants)} restaurants into database")
    return restaurants

def verify_restaurant_data(conn):
    """Verify the restaurant data in the database"""
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        # Check restaurant count
        cursor.execute("SELECT COUNT(*) as count FROM restaurants")
        count = cursor.fetchone()['count']
        logger.info(f"Total restaurants in database: {count}")

        # Check restaurants by region
        cursor.execute("""
            SELECT r.name_en, COUNT(*) as count
            FROM restaurants rest
            JOIN regions r ON rest.region_id = r.id
            GROUP BY r.name_en
            ORDER BY count DESC
        """)
        region_counts = cursor.fetchall()
        logger.info("Restaurants by region:")
        for region in region_counts:
            logger.info(f"  - {region['name_en']}: {region['count']} restaurants")

        # Check restaurants by type
        cursor.execute("""
            SELECT type_id, COUNT(*) as count
            FROM restaurants
            GROUP BY type_id
            ORDER BY count DESC
        """)
        type_counts = cursor.fetchall()
        logger.info("Restaurants by type:")
        for type_count in type_counts:
            logger.info(f"  - {type_count['type_id']}: {type_count['count']} restaurants")

        # Check restaurants by cuisine
        cursor.execute("""
            SELECT cuisine_id, COUNT(*) as count
            FROM restaurants
            GROUP BY cuisine_id
            ORDER BY count DESC
        """)
        cuisine_counts = cursor.fetchall()
        logger.info("Restaurants by cuisine:")
        for cuisine in cuisine_counts:
            logger.info(f"  - {cuisine['cuisine_id']}: {cuisine['count']} restaurants")

        # Check if we have enough data
        if count >= TARGET_RESTAURANTS:
            logger.info("✅ Target restaurant data volume achieved")
            return True
        else:
            logger.warning("⚠️ Target restaurant data volume not achieved")
            return False

def main():
    """Main function to generate restaurant data"""
    try:
        # Connect to database
        conn = connect_to_db()

        # Get existing data
        existing_data = get_existing_data(conn)

        # Calculate how many more restaurants we need to generate
        existing_restaurants_count = len(existing_data['restaurants'])
        restaurants_to_generate = max(0, TARGET_RESTAURANTS - existing_restaurants_count)

        logger.info(f"Existing restaurants: {existing_restaurants_count}")
        logger.info(f"Will generate: {restaurants_to_generate} restaurants")

        # Generate restaurants
        if restaurants_to_generate > 0:
            generate_restaurants(conn, existing_data, restaurants_to_generate)

        # Verify restaurant data
        verify_restaurant_data(conn)

        logger.info("Restaurant data generation completed successfully")
        return True

    except Exception as e:
        logger.error(f"Error generating restaurant data: {str(e)}", exc_info=True)
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = main()
    if success:
        sys.exit(0)
    else:
        sys.exit(1)
