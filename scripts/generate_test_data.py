#!/usr/bin/env python3
"""
Generate realistic test data for the Egypt Tourism Chatbot database.

This script:
1. Generates realistic test data for cities, attractions, and accommodations
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
from datetime import datetime, timezone
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

# Target counts for data generation
TARGET_CITIES = 50
TARGET_ATTRACTIONS = 400
TARGET_ACCOMMODATIONS = 200

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
        cursor.execute("SELECT id, name_en FROM regions")
        existing_data['regions'] = cursor.fetchall()

        # Get attraction types
        cursor.execute("SELECT type FROM attraction_types")
        existing_data['attraction_types'] = cursor.fetchall()

        # Get accommodation types
        cursor.execute("SELECT type FROM accommodation_types")
        existing_data['accommodation_types'] = cursor.fetchall()

        # Get cities
        cursor.execute("SELECT id FROM cities")
        existing_data['cities'] = cursor.fetchall()

        # Get attractions
        cursor.execute("SELECT id FROM attractions")
        existing_data['attractions'] = cursor.fetchall()

        # Get accommodations
        cursor.execute("SELECT id FROM accommodations")
        existing_data['accommodations'] = cursor.fetchall()

    return existing_data

def generate_embedding():
    """Generate a random embedding vector"""
    # Generate a random 1536-dimensional vector (typical for embeddings)
    embedding = np.random.normal(0, 1, 1536)
    # Normalize to unit length
    embedding = embedding / np.linalg.norm(embedding)
    return embedding

def generate_cities(conn, existing_data, count=TARGET_CITIES):
    """Generate city data"""
    logger.info(f"Generating {count} cities")

    # Extract existing city IDs
    existing_city_ids = [city['id'] for city in existing_data['cities']]

    # Extract regions
    regions = existing_data['regions']

    # Define city name prefixes for each region
    region_city_prefixes = {
        'lower_egypt': ['Delta', 'North', 'Canal', 'Eastern', 'Western'],
        'upper_egypt': ['Southern', 'Valley', 'Nile', 'Ancient', 'Historic'],
        'mediterranean_coast': ['Coastal', 'Sea', 'Port', 'Beach', 'Bay']
    }

    # Define city name suffixes
    city_suffixes = ['City', 'Town', 'Village', 'Settlement', 'Oasis', 'Harbor', 'Point']

    # Define latitude and longitude ranges for each region
    region_coordinates = {
        'lower_egypt': {'lat': (30.0, 31.5), 'lon': (30.0, 32.0)},
        'upper_egypt': {'lat': (24.0, 28.0), 'lon': (32.0, 33.5)},
        'mediterranean_coast': {'lat': (31.0, 32.0), 'lon': (25.0, 34.0)}
    }

    cities = []

    for i in range(count):
        # Select a random region
        region = random.choice(regions)
        region_id = region['id']
        region_name = region['name_en']

        # Generate a unique city ID
        while True:
            prefix = random.choice(region_city_prefixes[region_id])
            suffix = random.choice(city_suffixes)
            name_en = f"{prefix} {fake.word().capitalize()} {suffix}"
            city_id = name_en.lower().replace(' ', '_')

            if city_id not in existing_city_ids and city_id not in [city['id'] for city in cities]:
                break

        # Generate Arabic name (simulated)
        name_ar = f"مدينة {fake.word()} {random.choice(['الشمالية', 'الجنوبية', 'الشرقية', 'الغربية'])}"

        # Generate coordinates within the region's range
        lat_range = region_coordinates[region_id]['lat']
        lon_range = region_coordinates[region_id]['lon']
        latitude = random.uniform(lat_range[0], lat_range[1])
        longitude = random.uniform(lon_range[0], lon_range[1])

        # Generate description
        description_en = fake.paragraph(nb_sentences=3) + " " + fake.paragraph(nb_sentences=2)
        description_ar = "هذه مدينة جميلة في " + region_name + ". " + "تتميز بالعديد من المعالم السياحية والتاريخية."

        # Create city object
        city = {
            'id': city_id,
            'name_en': name_en,
            'name_ar': name_ar,
            'name': json.dumps({'en': name_en, 'ar': name_ar}),
            'description': json.dumps({'en': description_en, 'ar': description_ar}),
            'region': region_name,
            'region_id': region_id,
            'latitude': latitude,
            'longitude': longitude,
            'data': json.dumps({
                'population': random.randint(5000, 500000),
                'founded': random.randint(1800, 2000),
                'area_km2': round(random.uniform(10, 500), 2)
            }),
            'embedding': generate_embedding(),
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
            'user_id': 'system'
        }

        cities.append(city)

    # Insert cities into database
    with conn.cursor() as cursor:
        for city in cities:
            cursor.execute("""
                INSERT INTO cities (
                    id, name_en, name_ar, name, description,
                    region, region_id, latitude, longitude, data, embedding,
                    created_at, updated_at, user_id
                ) VALUES (
                    %s, %s, %s, %s::jsonb, %s::jsonb,
                    %s, %s, %s, %s, %s::jsonb, %s,
                    %s, %s, %s
                )
            """, (
                city['id'], city['name_en'], city['name_ar'], city['name'], city['description'],
                city['region'], city['region_id'], city['latitude'], city['longitude'],
                city['data'], city['embedding'],
                city['created_at'], city['updated_at'], city['user_id']
            ))

    conn.commit()
    logger.info(f"Inserted {len(cities)} cities into database")
    return cities

def generate_attractions(conn, existing_data, new_cities, count=TARGET_ATTRACTIONS):
    """Generate attraction data"""
    logger.info(f"Generating {count} attractions")

    # Extract existing attraction IDs
    existing_attraction_ids = [attraction['id'] for attraction in existing_data['attractions']]

    # Extract attraction types
    attraction_types = [type_obj['type'] for type_obj in existing_data['attraction_types']]

    # Combine existing cities with newly generated cities
    all_cities = existing_data['cities'] + new_cities

    # Define attraction name prefixes for each type
    type_attraction_prefixes = {
        'ancient_monument': ['Ancient', 'Old', 'Historic', 'Pharaonic', 'Royal'],
        'mosque_and_university': ['Grand', 'Holy', 'Sacred', 'Central', 'Historic'],
        'historical': ['Historic', 'Ancient', 'Old', 'Traditional', 'Classical'],
        'historical_district': ['Old', 'Ancient', 'Historic', 'Traditional', 'Heritage'],
        'museum': ['National', 'City', 'Regional', 'Archaeological', 'Art'],
        'necropolis': ['Ancient', 'Royal', 'Sacred', 'Pharaonic', 'Noble'],
        'cultural_center': ['Modern', 'Contemporary', 'National', 'Regional', 'City'],
        'temple': ['Ancient', 'Sacred', 'Holy', 'Pharaonic', 'Royal'],
        'temple_complex': ['Grand', 'Royal', 'Sacred', 'Monumental', 'Ancient'],
        'bazaar': ['Grand', 'Old', 'Traditional', 'Historic', 'Central'],
        'modern_landmark': ['Modern', 'Contemporary', 'New', 'Iconic', 'Signature']
    }

    # Define attraction name suffixes for each type
    type_attraction_suffixes = {
        'ancient_monument': ['Monument', 'Statue', 'Obelisk', 'Pillar', 'Structure'],
        'mosque_and_university': ['Mosque', 'University', 'School', 'Institute', 'Academy'],
        'historical': ['Site', 'Building', 'Palace', 'House', 'Structure'],
        'historical_district': ['Quarter', 'District', 'Neighborhood', 'Area', 'Zone'],
        'museum': ['Museum', 'Gallery', 'Exhibition', 'Collection', 'Archive'],
        'necropolis': ['Necropolis', 'Cemetery', 'Tombs', 'Burial Ground', 'Mausoleum'],
        'cultural_center': ['Center', 'Complex', 'Institute', 'Foundation', 'Hub'],
        'temple': ['Temple', 'Shrine', 'Sanctuary', 'Sacred Site', 'Holy Place'],
        'temple_complex': ['Temple Complex', 'Sacred Complex', 'Holy Site', 'Sanctuary', 'Compound'],
        'bazaar': ['Bazaar', 'Market', 'Souk', 'Marketplace', 'Trading Post'],
        'modern_landmark': ['Tower', 'Bridge', 'Building', 'Center', 'Monument']
    }

    attractions = []

    for i in range(count):
        # Select a random city
        city = random.choice(all_cities)
        if isinstance(city, dict) and 'id' in city:
            city_id = city['id']
            if isinstance(city_id, str):
                pass
            else:
                city_id = str(city_id)
        else:
            # Skip this iteration if city doesn't have an id
            continue

        # Get city details
        city_details = None
        for c in new_cities:
            if c['id'] == city_id:
                city_details = c
                break

        if not city_details:
            # Try to get from database
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM cities WHERE id = %s", (city_id,))
                city_details = cursor.fetchone()

        if not city_details:
            # Skip this iteration if city details not found
            continue

        # Select a random attraction type
        attraction_type = random.choice(attraction_types)

        # Generate a unique attraction ID
        while True:
            prefix = random.choice(type_attraction_prefixes.get(attraction_type, ['']))
            suffix = random.choice(type_attraction_suffixes.get(attraction_type, ['']))
            name_en = f"{prefix} {fake.word().capitalize()} {suffix}"
            attraction_id = f"{city_id}_{name_en.lower().replace(' ', '_')}"

            if len(attraction_id) > 50:
                attraction_id = attraction_id[:50]

            if attraction_id not in existing_attraction_ids and attraction_id not in [a['id'] for a in attractions]:
                break

        # Generate Arabic name (simulated)
        name_ar = f"{random.choice(['القديم', 'التاريخي', 'الكبير', 'الملكي'])} {fake.word()} {random.choice(['معبد', 'متحف', 'مبنى', 'موقع'])}"

        # Generate coordinates near the city
        latitude = city_details['latitude'] + random.uniform(-0.05, 0.05)
        longitude = city_details['longitude'] + random.uniform(-0.05, 0.05)

        # Generate description
        description_en = f"This {attraction_type.replace('_', ' ')} is located in {city_details.get('name_en', city_id)}. "
        description_en += fake.paragraph(nb_sentences=3) + " " + fake.paragraph(nb_sentences=2)

        description_ar = f"يقع هذا {random.choice(['المعبد', 'المتحف', 'المبنى', 'الموقع'])} في {city_details.get('name_ar', city_id)}. "
        description_ar += "يعتبر من أهم المعالم السياحية في المنطقة ويجذب الكثير من الزوار سنوياً."

        # Create attraction object
        attraction = {
            'id': attraction_id,
            'name_en': name_en,
            'name_ar': name_ar,
            'name': json.dumps({'en': name_en, 'ar': name_ar}),
            'description_en': description_en,
            'description_ar': description_ar,
            'description': json.dumps({'en': description_en, 'ar': description_ar}),
            'city': city_details.get('name_en', city_id),
            'city_id': city_id,
            'region': city_details.get('region', ''),
            'region_id': city_details.get('region_id', ''),
            'type': attraction_type,
            'type_id': attraction_type,
            'latitude': latitude,
            'longitude': longitude,
            'data': json.dumps({
                'year_built': random.randint(-3000, 1900),
                'entrance_fee': random.randint(0, 500),
                'opening_hours': f"{random.randint(7, 10)}:00 - {random.randint(16, 20)}:00",
                'popularity': random.randint(1, 10)
            }),
            'embedding': generate_embedding(),
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
            'user_id': 'system'
        }

        attractions.append(attraction)

    # Insert attractions into database
    with conn.cursor() as cursor:
        for attraction in attractions:
            cursor.execute("""
                INSERT INTO attractions (
                    id, name_en, name_ar, name, description,
                    city, city_id, region, region_id, type, type_id,
                    latitude, longitude, data, embedding,
                    created_at, updated_at, user_id
                ) VALUES (
                    %s, %s, %s, %s::jsonb, %s::jsonb,
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s::jsonb, %s,
                    %s, %s, %s
                )
            """, (
                attraction['id'], attraction['name_en'], attraction['name_ar'], attraction['name'], attraction['description'],
                attraction['city'], attraction['city_id'], attraction['region'], attraction['region_id'],
                attraction['type'], attraction['type_id'],
                attraction['latitude'], attraction['longitude'], attraction['data'], attraction['embedding'],
                attraction['created_at'], attraction['updated_at'], attraction['user_id']
            ))

    conn.commit()
    logger.info(f"Inserted {len(attractions)} attractions into database")
    return attractions

def generate_accommodations(conn, existing_data, new_cities, count=TARGET_ACCOMMODATIONS):
    """Generate accommodation data"""
    logger.info(f"Generating {count} accommodations")

    # Extract existing accommodation IDs
    existing_accommodation_ids = [accommodation['id'] for accommodation in existing_data['accommodations']]

    # Extract accommodation types
    accommodation_types = [type_obj['type'] for type_obj in existing_data['accommodation_types']]

    # Combine existing cities with newly generated cities
    all_cities = existing_data['cities'] + new_cities

    # Define accommodation name prefixes for each type
    type_accommodation_prefixes = {
        'luxury_hotel': ['Grand', 'Royal', 'Luxury', 'Premium', 'Elite'],
        'luxury_heritage_hotel': ['Historic', 'Heritage', 'Classic', 'Traditional', 'Vintage'],
        'Hotel': ['City', 'Central', 'Modern', 'Standard', 'Comfort']
    }

    # Define accommodation name suffixes for each type
    type_accommodation_suffixes = {
        'luxury_hotel': ['Hotel', 'Resort', 'Suites', 'Palace', 'Residences'],
        'luxury_heritage_hotel': ['Hotel', 'Palace', 'House', 'Mansion', 'Residence'],
        'Hotel': ['Hotel', 'Inn', 'Suites', 'Lodge', 'Place']
    }

    accommodations = []

    for i in range(count):
        # Select a random city
        city = random.choice(all_cities)
        if isinstance(city, dict) and 'id' in city:
            city_id = city['id']
            if isinstance(city_id, str):
                pass
            else:
                city_id = str(city_id)
        else:
            # Skip this iteration if city doesn't have an id
            continue

        # Get city details
        city_details = None
        for c in new_cities:
            if c['id'] == city_id:
                city_details = c
                break

        if not city_details:
            # Try to get from database
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM cities WHERE id = %s", (city_id,))
                city_details = cursor.fetchone()

        if not city_details:
            # Skip this iteration if city details not found
            continue

        # Select a random accommodation type
        accommodation_type = random.choice(accommodation_types)

        # Generate a unique accommodation ID
        while True:
            prefix = random.choice(type_accommodation_prefixes.get(accommodation_type, ['']))
            suffix = random.choice(type_accommodation_suffixes.get(accommodation_type, ['']))
            name_en = f"{prefix} {fake.word().capitalize()} {suffix}"
            accommodation_id = f"{city_id}_{name_en.lower().replace(' ', '_')}"

            if len(accommodation_id) > 50:
                accommodation_id = accommodation_id[:50]

            if accommodation_id not in existing_accommodation_ids and accommodation_id not in [a['id'] for a in accommodations]:
                break

        # Generate Arabic name (simulated)
        name_ar = f"فندق {fake.word()} {random.choice(['الفاخر', 'الكبير', 'الجديد', 'المميز'])}"

        # Generate coordinates near the city
        latitude = city_details['latitude'] + random.uniform(-0.05, 0.05)
        longitude = city_details['longitude'] + random.uniform(-0.05, 0.05)

        # Generate stars based on type
        if accommodation_type == 'luxury_hotel' or accommodation_type == 'luxury_heritage_hotel':
            stars = random.randint(4, 5)
        else:
            stars = random.randint(2, 4)

        # Generate price range based on stars
        price_min = stars * random.randint(20, 40)
        price_max = price_min + random.randint(50, 200)

        # Generate description
        description_en = f"This {accommodation_type.replace('_', ' ')} is located in {city_details.get('name_en', city_id)}. "
        description_en += fake.paragraph(nb_sentences=2) + " " + fake.paragraph(nb_sentences=1)

        description_ar = f"يقع هذا الفندق في {city_details.get('name_ar', city_id)}. "
        description_ar += "يوفر إقامة مريحة وخدمات متميزة للنزلاء."

        # Create accommodation object
        accommodation = {
            'id': accommodation_id,
            'name_en': name_en,
            'name_ar': name_ar,
            'name': json.dumps({'en': name_en, 'ar': name_ar}),
            'description_en': description_en,
            'description_ar': description_ar,
            'description': json.dumps({'en': description_en, 'ar': description_ar}),
            'city': city_details.get('name_en', city_id),
            'city_id': city_id,
            'region': city_details.get('region', ''),
            'region_id': city_details.get('region_id', ''),
            'type': accommodation_type,
            'type_id': accommodation_type,
            'stars': stars,
            'price_min': price_min,
            'price_max': price_max,
            'latitude': latitude,
            'longitude': longitude,
            'data': json.dumps({
                'amenities': random.sample(['WiFi', 'Pool', 'Spa', 'Restaurant', 'Bar', 'Gym', 'Room Service', 'Parking', 'Airport Shuttle'], random.randint(3, 9)),
                'year_built': random.randint(1900, 2020),
                'renovated': random.randint(2010, 2023),
                'rooms': random.randint(20, 500)
            }),
            'embedding': generate_embedding(),
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
            'user_id': 'system'
        }

        accommodations.append(accommodation)

    # Insert accommodations into database
    with conn.cursor() as cursor:
        for accommodation in accommodations:
            cursor.execute("""
                INSERT INTO accommodations (
                    id, name_en, name_ar, name, description,
                    city, city_id, region, region_id, type, type_id, stars,
                    price_min, price_max, latitude, longitude, data, embedding,
                    created_at, updated_at, user_id
                ) VALUES (
                    %s, %s, %s, %s::jsonb, %s::jsonb,
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s::jsonb, %s,
                    %s, %s, %s
                )
            """, (
                accommodation['id'], accommodation['name_en'], accommodation['name_ar'], accommodation['name'], accommodation['description'],
                accommodation['city'], accommodation['city_id'], accommodation['region'], accommodation['region_id'],
                accommodation['type'], accommodation['type_id'], accommodation['stars'],
                accommodation['price_min'], accommodation['price_max'],
                accommodation['latitude'], accommodation['longitude'], accommodation['data'], accommodation['embedding'],
                accommodation['created_at'], accommodation['updated_at'], accommodation['user_id']
            ))

    conn.commit()
    logger.info(f"Inserted {len(accommodations)} accommodations into database")
    return accommodations

def verify_data_volume(conn):
    """Verify the data volume in the database"""
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        # Check data volume
        cursor.execute("""
            SELECT 'attractions' as table_name, COUNT(*) as count FROM attractions
            UNION ALL
            SELECT 'accommodations' as table_name, COUNT(*) as count FROM accommodations
            UNION ALL
            SELECT 'cities' as table_name, COUNT(*) as count FROM cities
            UNION ALL
            SELECT 'regions' as table_name, COUNT(*) as count FROM regions
            UNION ALL
            SELECT 'attraction_types' as table_name, COUNT(*) as count FROM attraction_types
            UNION ALL
            SELECT 'accommodation_types' as table_name, COUNT(*) as count FROM accommodation_types;
        """)
        counts = cursor.fetchall()

        logger.info("Data volume in database:")
        for count in counts:
            logger.info(f"  - {count['table_name']}: {count['count']} records")

        # Check if we have enough data
        attractions_count = next((int(c['count']) for c in counts if c['table_name'] == 'attractions'), 0)
        accommodations_count = next((int(c['count']) for c in counts if c['table_name'] == 'accommodations'), 0)
        cities_count = next((int(c['count']) for c in counts if c['table_name'] == 'cities'), 0)

        if attractions_count >= TARGET_ATTRACTIONS and accommodations_count >= TARGET_ACCOMMODATIONS and cities_count >= TARGET_CITIES:
            logger.info("✅ Target data volume achieved")
            return True
        else:
            logger.warning("⚠️ Target data volume not achieved")
            return False

def main():
    """Main function to generate test data"""
    try:
        # Connect to database
        conn = connect_to_db()

        # Get existing data
        existing_data = get_existing_data(conn)

        # Calculate how many more records we need to generate
        existing_cities_count = len(existing_data['cities'])
        existing_attractions_count = len(existing_data['attractions'])
        existing_accommodations_count = len(existing_data['accommodations'])

        cities_to_generate = max(0, TARGET_CITIES - existing_cities_count)
        attractions_to_generate = max(0, TARGET_ATTRACTIONS - existing_attractions_count)
        accommodations_to_generate = max(0, TARGET_ACCOMMODATIONS - existing_accommodations_count)

        logger.info(f"Existing data: {existing_cities_count} cities, {existing_attractions_count} attractions, {existing_accommodations_count} accommodations")
        logger.info(f"Will generate: {cities_to_generate} cities, {attractions_to_generate} attractions, {accommodations_to_generate} accommodations")

        # Generate cities
        new_cities = []
        if cities_to_generate > 0:
            new_cities = generate_cities(conn, existing_data, cities_to_generate)

        # Generate attractions
        if attractions_to_generate > 0:
            generate_attractions(conn, existing_data, new_cities, attractions_to_generate)

        # Generate accommodations
        if accommodations_to_generate > 0:
            generate_accommodations(conn, existing_data, new_cities, accommodations_to_generate)

        # Verify data volume
        verify_data_volume(conn)

        logger.info("Test data generation completed successfully")
        return True

    except Exception as e:
        logger.error(f"Error generating test data: {str(e)}", exc_info=True)
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
