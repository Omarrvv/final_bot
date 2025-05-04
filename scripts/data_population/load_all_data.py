#!/usr/bin/env python3
"""
Data Loading Script for Egypt Tourism Chatbot

This script loads all JSON data from the data directory into the PostgreSQL database.
It processes attractions, cities, accommodations, restaurants, and other tourism entities.
"""
import json
import os
import sys
import glob
import re
from pathlib import Path
import time

# Add the src directory to the Python path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.logger import get_logger
from src.knowledge.database import DatabaseManager, DatabaseType

# Set up logging
logger = get_logger(__name__)

def clean_json_file(file_path):
    """
    Clean a JSON file by removing comments and fixing other issues.

    Args:
        file_path: Path to the JSON file

    Returns:
        Cleaned JSON content as a Python object
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Remove comments (both // and /* */ style)
        content = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)

        # Remove trailing commas
        content = re.sub(r',\s*}', '}', content)
        content = re.sub(r',\s*]', ']', content)

        # Parse the cleaned JSON
        return json.loads(content)
    except Exception as e:
        logger.error(f"Error cleaning JSON file {file_path}: {str(e)}")
        raise

def load_attractions(db_manager: DatabaseManager) -> int:
    """
    Load attractions from JSON files into the database.

    Args:
        db_manager: Database manager instance

    Returns:
        Number of attractions loaded
    """
    count = 0
    attractions_dir = "./data/attractions"

    # Process each JSON file in the attractions directory and its subdirectories
    for json_file in glob.glob(f"{attractions_dir}/**/*.json", recursive=True):
        try:
            attraction = clean_json_file(json_file)

            # Extract required fields
            attraction_id = attraction.get('id')
            if not attraction_id:
                # Use filename as ID if not specified
                attraction_id = os.path.splitext(os.path.basename(json_file))[0]

            # Handle multilingual names
            name = attraction.get('name', {})
            name_en = name.get('en', '')
            name_ar = name.get('ar', '')

            # Handle multilingual descriptions
            description = attraction.get('description', {})
            description_en = description.get('en', '')
            description_ar = description.get('ar', '')

            # Extract location information
            location = attraction.get('location', {})
            coordinates = location.get('coordinates', {})
            latitude = coordinates.get('latitude')
            longitude = coordinates.get('longitude')

            # Extract other fields
            attraction_type = attraction.get('type', '')
            city = location.get('city', '')
            region = location.get('region', '')

            # Validate required fields
            if not name_en:
                logger.warning(f"Missing name_en in {json_file}, skipping")
                continue

            # Build the data JSON field with additional attributes
            data = {k: v for k, v in attraction.items() if k not in [
                'id', 'name', 'description', 'location', 'type', 'city', 'region'
            ]}

            # Generate embedding for vector search
            combined_text = f"{name_en} {description_en} {name_ar} {description_ar}"
            embedding = db_manager.text_to_embedding(combined_text)

            # Insert into database
            if db_manager.db_type == DatabaseType.POSTGRES:
                query = """
                    INSERT INTO attractions (
                        id, name_en, name_ar, type, city, region,
                        latitude, longitude, description_en, description_ar,
                        data, embedding, name, description
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s::jsonb, %s::vector, %s::jsonb, %s::jsonb
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
                        name=EXCLUDED.name,
                        description=EXCLUDED.description,
                        updated_at=CURRENT_TIMESTAMP
                """

                params = (
                    attraction_id, name_en, name_ar, attraction_type,
                    city, region, latitude, longitude,
                    description_en, description_ar,
                    json.dumps(data), embedding,
                    json.dumps(name), json.dumps(description)
                )

                db_manager.execute_query(query, params)
                count += 1
                logger.info(f"Loaded attraction: {name_en}")

        except Exception as e:
            logger.error(f"Error loading {json_file}: {str(e)}")
            continue

    return count

def load_cities(db_manager: DatabaseManager) -> int:
    """
    Load cities from JSON files into the database.

    Args:
        db_manager: Database manager instance

    Returns:
        Number of cities loaded
    """
    count = 0
    cities_dir = "./data/cities"

    # Process each JSON file in the cities directory
    for json_file in glob.glob(f"{cities_dir}/*.json"):
        try:
            city = clean_json_file(json_file)

            # Extract required fields
            city_id = city.get('id')
            if not city_id:
                # Use filename as ID if not specified
                city_id = os.path.splitext(os.path.basename(json_file))[0]

            # Handle multilingual names
            name = city.get('name', {})
            name_en = name.get('en', '')
            name_ar = name.get('ar', '')

            # Handle multilingual descriptions
            description = city.get('description', {})
            description_en = description.get('en', '')
            description_ar = description.get('ar', '')

            # Extract location information
            coordinates = city.get('coordinates', {})
            latitude = coordinates.get('latitude')
            longitude = coordinates.get('longitude')

            # Extract other fields
            region = city.get('region', '')

            # Validate required fields
            if not name_en:
                logger.warning(f"Missing name_en in {json_file}, skipping")
                continue

            # Build the data JSON field with additional attributes
            data = {k: v for k, v in city.items() if k not in [
                'id', 'name', 'description', 'coordinates', 'region'
            ]}

            # Generate embedding for vector search
            combined_text = f"{name_en} {description_en} {name_ar} {description_ar}"
            embedding = db_manager.text_to_embedding(combined_text)

            # Insert into database
            if db_manager.db_type == DatabaseType.POSTGRES:
                query = """
                    INSERT INTO cities (
                        id, name_en, name_ar, region,
                        latitude, longitude, description_en, description_ar,
                        data, embedding, name, description
                    ) VALUES (
                        %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s::jsonb, %s::vector, %s::jsonb, %s::jsonb
                    ) ON CONFLICT(id) DO UPDATE SET
                        name_en=EXCLUDED.name_en,
                        name_ar=EXCLUDED.name_ar,
                        region=EXCLUDED.region,
                        latitude=EXCLUDED.latitude,
                        longitude=EXCLUDED.longitude,
                        description_en=EXCLUDED.description_en,
                        description_ar=EXCLUDED.description_ar,
                        data=EXCLUDED.data,
                        embedding=EXCLUDED.embedding,
                        name=EXCLUDED.name,
                        description=EXCLUDED.description,
                        updated_at=CURRENT_TIMESTAMP
                """

                params = (
                    city_id, name_en, name_ar, region,
                    latitude, longitude,
                    description_en, description_ar,
                    json.dumps(data), embedding,
                    json.dumps(name), json.dumps(description)
                )

                db_manager.execute_query(query, params)
                count += 1
                logger.info(f"Loaded city: {name_en}")

        except Exception as e:
            logger.error(f"Error loading {json_file}: {str(e)}")
            continue

    return count

def load_accommodations(db_manager: DatabaseManager) -> int:
    """
    Load accommodations from JSON files into the database.

    Args:
        db_manager: Database manager instance

    Returns:
        Number of accommodations loaded
    """
    count = 0
    accommodations_dir = "./data/accommodations"

    # Process each JSON file in the accommodations directory
    for json_file in glob.glob(f"{accommodations_dir}/*.json"):
        try:
            content = clean_json_file(json_file)

            # Handle both single accommodation and array of accommodations
            accommodations = content if isinstance(content, list) else [content]

            for accommodation in accommodations:
                # Extract required fields
                accommodation_id = accommodation.get('id')
                if not accommodation_id:
                    # Use filename as ID if not specified
                    accommodation_id = os.path.splitext(os.path.basename(json_file))[0]

                # Handle multilingual names
                name = accommodation.get('name', {})
                name_en = name.get('en', '')
                name_ar = name.get('ar', '')

                # Handle multilingual descriptions
                description = accommodation.get('description', {})
                description_en = description.get('en', '')
                description_ar = description.get('ar', '')

                # Extract location information
                location = accommodation.get('location', {})
                coordinates = location.get('coordinates', {})
                latitude = coordinates.get('latitude')
                longitude = coordinates.get('longitude')

                # Extract other fields
                accommodation_type = accommodation.get('type', '')
                city = location.get('city', '')
                region = location.get('region', '')
                stars = accommodation.get('stars', None)

                # Extract price range
                price_range = accommodation.get('price_range', {})
                price_min = price_range.get('min', '').replace('$', '') if isinstance(price_range, dict) else None
                price_max = price_range.get('max', '').replace('$', '') if isinstance(price_range, dict) else None

                # Try to convert price to numeric
                try:
                    price_min = float(price_min) if price_min else None
                except (ValueError, TypeError):
                    price_min = None

                try:
                    price_max = float(price_max) if price_max else None
                except (ValueError, TypeError):
                    price_max = None

                # Validate required fields
                if not name_en:
                    logger.warning(f"Missing name_en in {json_file}, skipping")
                    continue

                # Build the data JSON field with additional attributes
                data = {k: v for k, v in accommodation.items() if k not in [
                    'id', 'name', 'description', 'location', 'type', 'city', 'region', 'stars', 'price_range'
                ]}

                # Generate embedding for vector search
                combined_text = f"{name_en} {description_en} {name_ar} {description_ar}"
                embedding = db_manager.text_to_embedding(combined_text)

                # Insert into database
                if db_manager.db_type == DatabaseType.POSTGRES:
                    query = """
                        INSERT INTO accommodations (
                            id, name_en, name_ar, type, city, region,
                            latitude, longitude, description_en, description_ar,
                            stars, price_min, price_max, data, embedding, name, description
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s,
                            %s, %s, %s, %s::jsonb, %s::vector, %s::jsonb, %s::jsonb
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
                            name=EXCLUDED.name,
                            description=EXCLUDED.description,
                            updated_at=CURRENT_TIMESTAMP
                    """

                    params = (
                        accommodation_id, name_en, name_ar, accommodation_type,
                        city, region, latitude, longitude,
                        description_en, description_ar,
                        stars, price_min, price_max,
                        json.dumps(data), embedding,
                        json.dumps(name), json.dumps(description)
                    )

                    db_manager.execute_query(query, params)
                    count += 1
                    logger.info(f"Loaded accommodation: {name_en}")

        except Exception as e:
            logger.error(f"Error loading {json_file}: {str(e)}")
            continue

    return count

def load_restaurants(db_manager: DatabaseManager) -> int:
    """
    Load restaurants from JSON files into the database.

    Args:
        db_manager: Database manager instance

    Returns:
        Number of restaurants loaded
    """
    count = 0
    restaurants_dir = "./data/restaurants"

    # Process each JSON file in the restaurants directory
    for json_file in glob.glob(f"{restaurants_dir}/*.json"):
        try:
            content = clean_json_file(json_file)

            # Handle both single restaurant and array of restaurants
            restaurants = content if isinstance(content, list) else [content]

            for restaurant in restaurants:
                # Extract required fields
                restaurant_id = restaurant.get('id')
                if not restaurant_id:
                    # Use filename as ID if not specified
                    restaurant_id = os.path.splitext(os.path.basename(json_file))[0]

                # Handle multilingual names
                name = restaurant.get('name', {})
                name_en = name.get('en', '')
                name_ar = name.get('ar', '')

                # Handle multilingual descriptions
                description = restaurant.get('description', {})
                description_en = description.get('en', '')
                description_ar = description.get('ar', '')

                # Extract location information
                location = restaurant.get('location', {})
                coordinates = location.get('coordinates', {})
                latitude = coordinates.get('latitude')
                longitude = coordinates.get('longitude')

                # Extract other fields
                cuisine = restaurant.get('cuisine_type', [])
                if isinstance(cuisine, list) and cuisine:
                    cuisine = cuisine[0]  # Take first cuisine type
                restaurant_type = restaurant.get('type', '')
                city = location.get('city', '')
                region = location.get('region', '')
                price_range = restaurant.get('price_range', '')

                # Validate required fields
                if not name_en:
                    logger.warning(f"Missing name_en in {json_file}, skipping")
                    continue

                # Build the data JSON field with additional attributes
                data = {k: v for k, v in restaurant.items() if k not in [
                    'id', 'name', 'description', 'location', 'type', 'city', 'region', 'cuisine_type', 'price_range'
                ]}

                # Generate embedding for vector search
                combined_text = f"{name_en} {description_en} {name_ar} {description_ar}"
                if isinstance(cuisine, list):
                    combined_text += " " + " ".join(cuisine)
                else:
                    combined_text += f" {cuisine}"
                embedding = db_manager.text_to_embedding(combined_text)

                # Insert into database
                if db_manager.db_type == DatabaseType.POSTGRES:
                    query = """
                        INSERT INTO restaurants (
                            id, name_en, name_ar, cuisine, type, city, region,
                            latitude, longitude, description_en, description_ar,
                            data, embedding, name, description
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s,
                            %s::jsonb, %s::vector, %s::jsonb, %s::jsonb
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
                            name=EXCLUDED.name,
                            description=EXCLUDED.description,
                            updated_at=CURRENT_TIMESTAMP
                    """

                    # Add price_range to data if it exists
                    if price_range:
                        data['price_range'] = price_range

                    params = (
                        restaurant_id, name_en, name_ar, cuisine, restaurant_type,
                        city, region, latitude, longitude,
                        description_en, description_ar,
                        json.dumps(data), embedding,
                        json.dumps(name), json.dumps(description)
                    )

                    db_manager.execute_query(query, params)
                    count += 1
                    logger.info(f"Loaded restaurant: {name_en}")

        except Exception as e:
            logger.error(f"Error loading {json_file}: {str(e)}")
            continue

    return count

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
    """Main function to load all data into the database."""
    start_time = time.time()
    logger.info("Starting data loading process...")

    # Initialize database manager
    db_manager = DatabaseManager()

    # Ensure we're using PostgreSQL
    if db_manager.db_type != DatabaseType.POSTGRES:
        logger.error(f"PostgreSQL database not configured. Current type: {db_manager.db_type}")
        return

    logger.info("Connected to PostgreSQL database")

    # Override the text_to_embedding method to use random embeddings
    # This is a temporary solution until we can fix the embedding dimension issue
    db_manager.text_to_embedding = lambda text: generate_random_embedding(db_manager.vector_dimension)

    # Load data for each entity type
    try:
        # Load cities first (they're referenced by other entities)
        cities_count = load_cities(db_manager)
        logger.info(f"Loaded {cities_count} cities")

        # Load attractions
        attractions_count = load_attractions(db_manager)
        logger.info(f"Loaded {attractions_count} attractions")

        # Load accommodations
        accommodations_count = load_accommodations(db_manager)
        logger.info(f"Loaded {accommodations_count} accommodations")

        # Load restaurants
        restaurants_count = load_restaurants(db_manager)
        logger.info(f"Loaded {restaurants_count} restaurants")

        # TODO: Add more entity types (transportation, tours, etc.)

        elapsed_time = time.time() - start_time
        logger.info(f"Data loading completed in {elapsed_time:.2f} seconds")
        logger.info(f"Total entities loaded: {cities_count + attractions_count + accommodations_count + restaurants_count}")

    except Exception as e:
        logger.error(f"Error during data loading: {str(e)}")
    finally:
        db_manager.close()

if __name__ == '__main__':
    main()
