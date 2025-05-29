#!/usr/bin/env python3
"""
Generate destination data for the Egypt Tourism Chatbot database.

This script:
1. Migrates existing regions and cities to the new destinations table
2. Creates hierarchical relationships between destinations
3. Adds landmarks based on major attractions
"""

import os
import sys
import json
import random
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
import numpy as np
from pgvector.psycopg2 import register_vector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set random seed for reproducibility
random.seed(42)
np.random.seed(42)

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
        cursor.execute("SELECT id, name_en, name, description, latitude, longitude FROM regions")
        existing_data['regions'] = cursor.fetchall()

        # Get cities
        cursor.execute("SELECT id, name_en, name, description, region_id, latitude, longitude FROM cities")
        existing_data['cities'] = cursor.fetchall()

        # Get attractions
        cursor.execute("SELECT id, name_en, name, description, city_id, region_id, latitude, longitude FROM attractions")
        existing_data['attractions'] = cursor.fetchall()

        # Get existing destinations
        cursor.execute("SELECT id FROM destinations")
        existing_data['destinations'] = cursor.fetchall()

    return existing_data

def generate_embedding():
    """Generate a random embedding vector"""
    # Generate a random 1536-dimensional vector (typical for embeddings)
    embedding = np.random.normal(0, 1, 1536)
    # Normalize to unit length
    embedding = embedding / np.linalg.norm(embedding)
    return embedding

def migrate_regions_to_destinations(conn, existing_data):
    """Migrate existing regions to destinations table"""
    logger.info("Migrating regions to destinations table")

    # Extract existing destination IDs
    existing_destination_ids = [dest['id'] for dest in existing_data['destinations']]

    # Prepare regions data
    regions_data = []
    for region in existing_data['regions']:
        region_id = region['id']

        # Skip if already exists
        if region_id in existing_destination_ids:
            continue

        # Extract name from JSONB if available
        name_en = region['name_en']
        name_ar = ""

        if region['name']:
            if isinstance(region['name'], str):
                try:
                    name_json = json.loads(region['name'])
                    if 'en' in name_json:
                        name_en = name_json['en']
                    if 'ar' in name_json:
                        name_ar = name_json['ar']
                except:
                    pass
            elif isinstance(region['name'], dict):
                if 'en' in region['name']:
                    name_en = region['name']['en']
                if 'ar' in region['name']:
                    name_ar = region['name']['ar']

        # Extract description from JSONB if available
        description_en = ""
        description_ar = ""

        if region['description']:
            if isinstance(region['description'], str):
                try:
                    desc_json = json.loads(region['description'])
                    if 'en' in desc_json:
                        description_en = desc_json['en']
                    if 'ar' in desc_json:
                        description_ar = desc_json['ar']
                except:
                    description_en = region['description']
            elif isinstance(region['description'], dict):
                if 'en' in region['description']:
                    description_en = region['description']['en']
                if 'ar' in region['description']:
                    description_ar = region['description']['ar']

        # If no description, generate one
        if not description_en:
            description_en = f"{name_en} is a region in Egypt with unique cultural and geographical features."

        if not description_ar:
            description_ar = f"{name_ar if name_ar else name_en} هي منطقة في مصر ذات ميزات ثقافية وجغرافية فريدة."

        # Create region data
        region_data = {
            'id': region_id,
            'name': json.dumps({'en': name_en, 'ar': name_ar if name_ar else name_en}),
            'description': json.dumps({'en': description_en, 'ar': description_ar}),
            'type': 'region',
            'parent_id': 'egypt',  # All regions are children of Egypt
            'country': 'Egypt',
            'latitude': region['latitude'],
            'longitude': region['longitude'],
            'data': json.dumps({
                'original_id': region_id,
                'source_table': 'regions'
            }),
            'embedding': generate_embedding()
        }

        regions_data.append(region_data)

    # Insert regions into destinations table
    with conn.cursor() as cursor:
        for region_data in regions_data:
            cursor.execute("""
                INSERT INTO destinations (
                    id, name, description, type, parent_id, country,
                    latitude, longitude, data, embedding,
                    created_at, updated_at, user_id
                ) VALUES (
                    %s, %s::jsonb, %s::jsonb, %s, %s, %s,
                    %s, %s, %s::jsonb, %s,
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'system'
                )
            """, (
                region_data['id'],
                region_data['name'],
                region_data['description'],
                region_data['type'],
                region_data['parent_id'],
                region_data['country'],
                region_data['latitude'],
                region_data['longitude'],
                region_data['data'],
                region_data['embedding']
            ))

    conn.commit()
    logger.info(f"Migrated {len(regions_data)} regions to destinations table")
    return regions_data

def migrate_cities_to_destinations(conn, existing_data):
    """Migrate existing cities to destinations table"""
    logger.info("Migrating cities to destinations table")

    # Extract existing destination IDs
    existing_destination_ids = [dest['id'] for dest in existing_data['destinations']]

    # Prepare cities data
    cities_data = []
    for city in existing_data['cities']:
        city_id = city['id']

        # Skip if already exists
        if city_id in existing_destination_ids:
            continue

        # Extract name from JSONB if available
        name_en = city['name_en']
        name_ar = ""

        if city['name']:
            if isinstance(city['name'], str):
                try:
                    name_json = json.loads(city['name'])
                    if 'en' in name_json:
                        name_en = name_json['en']
                    if 'ar' in name_json:
                        name_ar = name_json['ar']
                except:
                    pass
            elif isinstance(city['name'], dict):
                if 'en' in city['name']:
                    name_en = city['name']['en']
                if 'ar' in city['name']:
                    name_ar = city['name']['ar']

        # Extract description from JSONB if available
        description_en = ""
        description_ar = ""

        if city['description']:
            if isinstance(city['description'], str):
                try:
                    desc_json = json.loads(city['description'])
                    if 'en' in desc_json:
                        description_en = desc_json['en']
                    if 'ar' in desc_json:
                        description_ar = desc_json['ar']
                except:
                    description_en = city['description']
            elif isinstance(city['description'], dict):
                if 'en' in city['description']:
                    description_en = city['description']['en']
                if 'ar' in city['description']:
                    description_ar = city['description']['ar']

        # If no description, generate one
        if not description_en:
            description_en = f"{name_en} is a city in Egypt located in the {city['region_id']} region."

        if not description_ar:
            description_ar = f"{name_ar if name_ar else name_en} هي مدينة في مصر تقع في منطقة {city['region_id']}."

        # Create city data
        city_data = {
            'id': city_id,
            'name': json.dumps({'en': name_en, 'ar': name_ar if name_ar else name_en}),
            'description': json.dumps({'en': description_en, 'ar': description_ar}),
            'type': 'city',
            'parent_id': city['region_id'],  # Cities are children of regions
            'country': 'Egypt',
            'latitude': city['latitude'],
            'longitude': city['longitude'],
            'data': json.dumps({
                'original_id': city_id,
                'source_table': 'cities'
            }),
            'embedding': generate_embedding()
        }

        cities_data.append(city_data)

    # Insert cities into destinations table
    with conn.cursor() as cursor:
        for city_data in cities_data:
            cursor.execute("""
                INSERT INTO destinations (
                    id, name, description, type, parent_id, country,
                    latitude, longitude, data, embedding,
                    created_at, updated_at, user_id
                ) VALUES (
                    %s, %s::jsonb, %s::jsonb, %s, %s, %s,
                    %s, %s, %s::jsonb, %s,
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'system'
                )
            """, (
                city_data['id'],
                city_data['name'],
                city_data['description'],
                city_data['type'],
                city_data['parent_id'],
                city_data['country'],
                city_data['latitude'],
                city_data['longitude'],
                city_data['data'],
                city_data['embedding']
            ))

    conn.commit()
    logger.info(f"Migrated {len(cities_data)} cities to destinations table")
    return cities_data

def migrate_attractions_to_landmarks(conn, existing_data):
    """Migrate selected attractions to landmarks in destinations table"""
    logger.info("Migrating selected attractions to landmarks")

    # Extract existing destination IDs
    existing_destination_ids = [dest['id'] for dest in existing_data['destinations']]

    # Select major attractions to convert to landmarks (about 20% of attractions)
    major_attractions = []
    for attraction in existing_data['attractions']:
        # Skip if already exists as a destination
        if attraction['id'] in existing_destination_ids:
            continue

        # Randomly select about 20% of attractions
        if random.random() < 0.2:
            major_attractions.append(attraction)

    # Prepare landmarks data
    landmarks_data = []
    for attraction in major_attractions:
        landmark_id = f"landmark_{attraction['id']}"

        # Extract name and description
        name_en = attraction['name_en']
        name_ar = ""
        description_en = ""
        description_ar = ""

        # Process name from JSONB
        if attraction['name']:
            if isinstance(attraction['name'], str):
                try:
                    name_json = json.loads(attraction['name'])
                    name_en = name_json.get('en', name_en)
                    name_ar = name_json.get('ar', "")
                except:
                    pass
            elif isinstance(attraction['name'], dict):
                name_en = attraction['name'].get('en', name_en)
                name_ar = attraction['name'].get('ar', "")

        # Process description from JSONB
        if attraction['description']:
            if isinstance(attraction['description'], str):
                try:
                    desc_json = json.loads(attraction['description'])
                    description_en = desc_json.get('en', "")
                    description_ar = desc_json.get('ar', "")
                except:
                    description_en = attraction['description']
            elif isinstance(attraction['description'], dict):
                description_en = attraction['description'].get('en', "")
                description_ar = attraction['description'].get('ar', "")

        # If no description, generate one
        if not description_en:
            description_en = f"{name_en} is a famous landmark in Egypt."
        if not description_ar:
            description_ar = f"{name_ar if name_ar else name_en} هو معلم شهير في مصر."

        # Determine parent ID (city or region)
        parent_id = attraction['city_id'] if attraction['city_id'] else attraction['region_id']

        # Create landmark data
        landmark_data = {
            'id': landmark_id,
            'name': json.dumps({'en': name_en, 'ar': name_ar if name_ar else name_en}),
            'description': json.dumps({'en': description_en, 'ar': description_ar}),
            'type': 'landmark',
            'parent_id': parent_id,
            'country': 'Egypt',
            'latitude': attraction['latitude'],
            'longitude': attraction['longitude'],
            'data': json.dumps({
                'original_id': attraction['id'],
                'source_table': 'attractions'
            }),
            'embedding': generate_embedding()
        }

        landmarks_data.append(landmark_data)

    # Insert landmarks into destinations table
    with conn.cursor() as cursor:
        for landmark_data in landmarks_data:
            cursor.execute("""
                INSERT INTO destinations (
                    id, name, description, type, parent_id, country,
                    latitude, longitude, data, embedding,
                    created_at, updated_at, user_id
                ) VALUES (
                    %s, %s::jsonb, %s::jsonb, %s, %s, %s,
                    %s, %s, %s::jsonb, %s,
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'system'
                )
            """, (
                landmark_data['id'],
                landmark_data['name'],
                landmark_data['description'],
                landmark_data['type'],
                landmark_data['parent_id'],
                landmark_data['country'],
                landmark_data['latitude'],
                landmark_data['longitude'],
                landmark_data['data'],
                landmark_data['embedding']
            ))

    conn.commit()
    logger.info(f"Migrated {len(landmarks_data)} attractions to landmarks")
    return landmarks_data

def add_seasonal_information(conn):
    """Add seasonal information for destinations"""
    logger.info("Adding seasonal information for destinations")

    # Get all destinations
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("SELECT id, name, type FROM destinations")
        destinations = cursor.fetchall()

    # Define seasons
    seasons = [
        {"season": "winter", "start_month": 12, "end_month": 2},
        {"season": "spring", "start_month": 3, "end_month": 5},
        {"season": "summer", "start_month": 6, "end_month": 8},
        {"season": "autumn", "start_month": 9, "end_month": 11}
    ]

    # Add seasonal information for each destination
    count = 0
    with conn.cursor() as cursor:
        for destination in destinations:
            # Skip landmarks
            if destination['type'] == 'landmark':
                continue

            for season in seasons:
                # Generate temperature based on region and season
                if season['season'] == 'summer':
                    temp_min = random.uniform(22, 28)
                    temp_max = random.uniform(32, 42)
                    humidity = random.uniform(40, 60)
                    precipitation = random.uniform(0, 5)
                elif season['season'] == 'winter':
                    temp_min = random.uniform(8, 15)
                    temp_max = random.uniform(18, 25)
                    humidity = random.uniform(50, 70)
                    precipitation = random.uniform(5, 20)
                elif season['season'] == 'spring':
                    temp_min = random.uniform(15, 22)
                    temp_max = random.uniform(25, 35)
                    humidity = random.uniform(40, 60)
                    precipitation = random.uniform(2, 10)
                else:  # autumn
                    temp_min = random.uniform(18, 25)
                    temp_max = random.uniform(28, 38)
                    humidity = random.uniform(45, 65)
                    precipitation = random.uniform(1, 8)

                # Generate description
                description_en = f"During {season['season']} in this area, temperatures range from {int(temp_min)}°C to {int(temp_max)}°C."
                description_ar = f"خلال فصل {season['season']} في هذه المنطقة، تتراوح درجات الحرارة من {int(temp_min)} درجة مئوية إلى {int(temp_max)} درجة مئوية."

                # Insert seasonal information
                cursor.execute("""
                    INSERT INTO destination_seasons (
                        destination_id, season, start_month, end_month,
                        description, temperature_min, temperature_max,
                        precipitation, humidity
                    ) VALUES (
                        %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s
                    )
                """, (
                    destination['id'],
                    season['season'],
                    season['start_month'],
                    season['end_month'],
                    json.dumps({'en': description_en, 'ar': description_ar}),
                    temp_min,
                    temp_max,
                    precipitation,
                    humidity
                ))
                count += 1

    conn.commit()
    logger.info(f"Added {count} seasonal information records")
    return count

def verify_destination_data(conn):
    """Verify the destination data in the database"""
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        # Check destination count
        cursor.execute("SELECT COUNT(*) as count FROM destinations")
        count = cursor.fetchone()['count']
        logger.info(f"Total destinations in database: {count}")

        # Check destinations by type
        cursor.execute("""
            SELECT type, COUNT(*) as count
            FROM destinations
            GROUP BY type
            ORDER BY count DESC
        """)
        type_counts = cursor.fetchall()
        logger.info("Destinations by type:")
        for type_count in type_counts:
            logger.info(f"  - {type_count['type']}: {type_count['count']} destinations")

        # Check seasonal information
        cursor.execute("SELECT COUNT(*) as count FROM destination_seasons")
        season_count = cursor.fetchone()['count']
        logger.info(f"Total seasonal information records: {season_count}")

        # Check if we have enough data
        if count > 0:
            logger.info("✅ Destination data migration successful")
            return True
        else:
            logger.warning("⚠️ Destination data migration failed")
            return False

def main():
    """Main function to generate destination data"""
    try:
        # Connect to database
        conn = connect_to_db()

        # Get existing data
        existing_data = get_existing_data(conn)

        # Migrate regions to destinations
        migrate_regions_to_destinations(conn, existing_data)

        # Migrate cities to destinations
        migrate_cities_to_destinations(conn, existing_data)

        # Migrate attractions to landmarks
        migrate_attractions_to_landmarks(conn, existing_data)

        # Add seasonal information
        add_seasonal_information(conn)

        # Verify destination data
        verify_destination_data(conn)

        logger.info("Destination data generation completed successfully")
        return True

    except Exception as e:
        logger.error(f"Error generating destination data: {str(e)}", exc_info=True)
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
