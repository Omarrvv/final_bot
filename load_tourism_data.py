#!/usr/bin/env python
"""
Tourism Data Loader for Egypt Chatbot

This script loads tourism data from JSON files in the data directory into the PostgreSQL database.
It supports loading attractions, cities, regions, accommodations, restaurants, and other tourism entities.
"""

import os
import json
import logging
import asyncio
import asyncpg
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("egypt_tourism_data_loader")

# Database connection details - Update these as needed
DATABASE_URL = "postgresql://localhost:5432/egypt_chatbot"

# Load dotenv file if it exists (for DB credentials)
try:
    from dotenv import load_dotenv
    load_dotenv()
    DATABASE_URL = os.getenv("DATABASE_URL", DATABASE_URL)
except ImportError:
    logger.warning("dotenv package not found, using default database settings")


class TourismDataLoader:
    """A class to load tourism data into the PostgreSQL database."""

    def __init__(self, db_url: str):
        """Initialize the data loader."""
        self.db_url = db_url
        self.data_dir = Path(os.path.dirname(os.path.abspath(__file__))) / "data"
        self.pool = None
        
    async def connect(self):
        """Connect to the PostgreSQL database."""
        logger.info(f"Connecting to database at {self.db_url}")
        try:
            self.pool = await asyncpg.create_pool(dsn=self.db_url)
            logger.info("Connected to database")
            return True
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            return False

    async def close(self):
        """Close the database connection."""
        if self.pool:
            await self.pool.close()
            logger.info("Closed database connection")

    async def load_all_data(self):
        """Load all tourism data into the database."""
        if not await self.connect():
            return False
        
        try:
            # Load index.json to get all entity categories and files
            index_file = self.data_dir / "index.json"
            if not index_file.exists():
                logger.error(f"Index file not found at {index_file}")
                return False
            
            with open(index_file, "r", encoding="utf-8") as f:
                index_data = json.load(f)
            
            # Process each category in the index
            categories = index_data.get("categories", {})
            for category, category_data in categories.items():
                if category in ["schemas", "egypt_chatbot.db # Primary DB for KB"]:
                    continue  # Skip schema definitions and other non-entity categories
                    
                entities = category_data.get("entities", [])
                logger.info(f"Processing {len(entities)} items in category: {category}")
                
                if category == "attractions":
                    await self.load_attractions(entities)
                elif category == "cities":
                    await self.load_cities(entities)
                elif category == "regions":
                    await self.load_regions(entities)
                elif category == "accommodations":
                    await self.load_accommodations(entities)
                elif category == "restaurants":
                    await self.load_restaurants(entities)
                elif category == "transportation":
                    await self.load_transportation(entities)
                elif category == "hotels":
                    # Hotels are similar to accommodations, but we'll use the generic loader
                    await self.load_generic_entities(entities, "hotels", "accommodations")
                else:
                    # For all other categories, load them as generic entities into the attractions table
                    # This ensures we don't miss any data
                    await self.load_generic_entities(entities, category, "attractions")
            
            logger.info("Data loading completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return False
        finally:
            await self.close()

    async def load_generic_entities(self, entities: List[Dict], category: str, target_table: str):
        """Generic method to load entities into specified target table.
        
        Args:
            entities: List of entity metadata from index.json
            category: The category name (directory name)
            target_table: The database table to load into
        """
        for entity in entities:
            try:
                file_path = self.data_dir / category / entity["file"]
                if not file_path.exists():
                    logger.warning(f"{category} file not found: {file_path}")
                    continue
                
                with open(file_path, "r", encoding="utf-8") as f:
                    entity_data = json.load(f)
                
                # Extract common data fields
                name_en = entity_data.get("name", {}).get("en", "")
                name_ar = entity_data.get("name", {}).get("ar", "")
                desc_en = entity_data.get("description", {}).get("en", "")
                desc_ar = entity_data.get("description", {}).get("ar", "")
                entity_type = entity_data.get("type", category)
                
                # Extract location info if available
                latitude = longitude = None
                region = city = ""
                
                location = entity_data.get("location", {})
                if location:
                    region = location.get("region", "")
                    city = location.get("city", "")
                    coords = location.get("coordinates", {})
                    if coords:
                        latitude = coords.get("latitude")
                        longitude = coords.get("longitude")
                
                # Package multilingual content as jsonb
                name_jsonb = json.dumps({"en": name_en, "ar": name_ar})
                desc_jsonb = json.dumps({"en": desc_en, "ar": desc_ar})
                
                # Prepare data jsonb
                data_jsonb = json.dumps(entity_data)
                
                # Generate a UUID if id is not provided
                entity_id = entity.get("id") or str(uuid.uuid4())
                
                # Insert into the target table - using attractions as default fallback
                if target_table == "attractions":
                    async with self.pool.acquire() as conn:
                        await conn.execute('''
                            INSERT INTO attractions 
                            (id, name_en, name_ar, description_en, description_ar, 
                            name, description, type, city, region, latitude, longitude, data)
                            VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7::jsonb, $8, $9, $10, $11, $12, $13::jsonb)
                            ON CONFLICT (id) DO UPDATE SET
                            name_en = $2, name_ar = $3, description_en = $4, description_ar = $5,
                            name = $6::jsonb, description = $7::jsonb, type = $8, 
                            city = $9, region = $10, latitude = $11, longitude = $12, 
                            data = $13::jsonb, updated_at = CURRENT_TIMESTAMP
                        ''', entity_id, name_en, name_ar, desc_en, desc_ar, 
                        name_jsonb, desc_jsonb, entity_type, city, region, 
                        latitude, longitude, data_jsonb)
                        
                        # Update geom field if coordinates are available
                        if latitude and longitude:
                            await conn.execute('''
                                UPDATE attractions 
                                SET geom = ST_SetSRID(ST_MakePoint($1, $2), 4326)
                                WHERE id = $3
                            ''', longitude, latitude, entity_id)
                
                logger.info(f"Loaded {category} entity: {name_en or entity_id}")
            
            except Exception as e:
                logger.error(f"Error loading {category} {entity.get('id', 'unknown')}: {e}")

    async def load_attractions(self, entities: List[Dict]):
        """Load attractions data into the database."""
        for entity in entities:
            try:
                file_path = self.data_dir / "attractions" / entity["file"]
                if not file_path.exists():
                    logger.warning(f"Attraction file not found: {file_path}")
                    continue
                
                with open(file_path, "r", encoding="utf-8") as f:
                    attraction_data = json.load(f)
                
                # Extract data from the JSON format
                name_en = attraction_data.get("name", {}).get("en", "")
                name_ar = attraction_data.get("name", {}).get("ar", "")
                desc_en = attraction_data.get("description", {}).get("en", "")
                desc_ar = attraction_data.get("description", {}).get("ar", "")
                attraction_type = attraction_data.get("type", "")
                region = attraction_data.get("location", {}).get("region", "")
                city = attraction_data.get("location", {}).get("city", region)  # Use region as fallback
                latitude = attraction_data.get("location", {}).get("coordinates", {}).get("latitude")
                longitude = attraction_data.get("location", {}).get("coordinates", {}).get("longitude")
                
                # Package multilingual name and description as jsonb
                name_jsonb = json.dumps({"en": name_en, "ar": name_ar})
                desc_jsonb = json.dumps({"en": desc_en, "ar": desc_ar})
                
                # Prepare full data jsonb
                data_jsonb = json.dumps(attraction_data)
                
                # Generate a UUID if id is not provided
                entity_id = entity.get("id") or str(uuid.uuid4())
                
                # Insert into the database
                async with self.pool.acquire() as conn:
                    await conn.execute('''
                        INSERT INTO attractions 
                        (id, name_en, name_ar, description_en, description_ar, 
                        name, description, type, city, region, latitude, longitude, data)
                        VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7::jsonb, $8, $9, $10, $11, $12, $13::jsonb)
                        ON CONFLICT (id) DO UPDATE SET
                        name_en = $2, name_ar = $3, description_en = $4, description_ar = $5,
                        name = $6::jsonb, description = $7::jsonb, type = $8, 
                        city = $9, region = $10, latitude = $11, longitude = $12, 
                        data = $13::jsonb, updated_at = CURRENT_TIMESTAMP
                    ''', entity_id, name_en, name_ar, desc_en, desc_ar, 
                    name_jsonb, desc_jsonb, attraction_type, city, region, 
                    latitude, longitude, data_jsonb)
                    
                    # If attraction has a geom field, update it from the coordinates
                    if latitude and longitude:
                        await conn.execute('''
                            UPDATE attractions 
                            SET geom = ST_SetSRID(ST_MakePoint($1, $2), 4326)
                            WHERE id = $3
                        ''', longitude, latitude, entity_id)
                
                logger.info(f"Loaded attraction: {name_en}")
            
            except Exception as e:
                logger.error(f"Error loading attraction {entity.get('id', 'unknown')}: {e}")

    async def load_cities(self, entities: List[Dict]):
        """Load cities data into the database."""
        for entity in entities:
            try:
                file_path = self.data_dir / "cities" / entity["file"]
                if not file_path.exists():
                    logger.warning(f"City file not found: {file_path}")
                    continue
                
                with open(file_path, "r", encoding="utf-8") as f:
                    city_data = json.load(f)
                
                # Extract data from the JSON format
                name_en = city_data.get("name", {}).get("en", "")
                name_ar = city_data.get("name", {}).get("ar", "")
                region = city_data.get("region", "")
                region_id = city_data.get("region_id", "")
                latitude = city_data.get("coordinates", {}).get("latitude")
                longitude = city_data.get("coordinates", {}).get("longitude")
                
                # Prepare jsonb data
                data_jsonb = json.dumps(city_data)
                
                # Generate a UUID if id is not provided
                entity_id = entity.get("id") or str(uuid.uuid4())
                
                # Insert into the database
                async with self.pool.acquire() as conn:
                    await conn.execute('''
                        INSERT INTO cities 
                        (id, name_en, name_ar, region, region_id, latitude, longitude, data)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb)
                        ON CONFLICT (id) DO UPDATE SET
                        name_en = $2, name_ar = $3, region = $4, region_id = $5,
                        latitude = $6, longitude = $7, data = $8::jsonb, 
                        updated_at = CURRENT_TIMESTAMP
                    ''', entity_id, name_en, name_ar, region, region_id, 
                    latitude, longitude, data_jsonb)
                    
                    # If city has a geom field, update it from the coordinates
                    if latitude and longitude:
                        await conn.execute('''
                            UPDATE cities 
                            SET geom = ST_SetSRID(ST_MakePoint($1, $2), 4326)
                            WHERE id = $3
                        ''', longitude, latitude, entity_id)
                
                logger.info(f"Loaded city: {name_en}")
            
            except Exception as e:
                logger.error(f"Error loading city {entity.get('id', 'unknown')}: {e}")

    async def load_regions(self, entities: List[Dict]):
        """Load regions data into the database."""
        for entity in entities:
            try:
                file_path = self.data_dir / "regions" / entity["file"]
                if not file_path.exists():
                    logger.warning(f"Region file not found: {file_path}")
                    continue
                
                with open(file_path, "r", encoding="utf-8") as f:
                    region_data = json.load(f)
                
                # Extract data from the JSON format
                name_en = region_data.get("name", {}).get("en", "")
                name_ar = region_data.get("name", {}).get("ar", "")
                country = region_data.get("country", "Egypt")
                latitude = region_data.get("coordinates", {}).get("latitude")
                longitude = region_data.get("coordinates", {}).get("longitude")
                
                # Prepare jsonb data
                data_jsonb = json.dumps(region_data)
                
                # Generate a UUID if id is not provided
                entity_id = entity.get("id") or str(uuid.uuid4())
                
                # Insert into the database
                async with self.pool.acquire() as conn:
                    await conn.execute('''
                        INSERT INTO regions 
                        (id, name_en, name_ar, country, latitude, longitude, data)
                        VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb)
                        ON CONFLICT (id) DO UPDATE SET
                        name_en = $2, name_ar = $3, country = $4,
                        latitude = $5, longitude = $6, data = $7::jsonb, 
                        updated_at = CURRENT_TIMESTAMP
                    ''', entity_id, name_en, name_ar, country, 
                    latitude, longitude, data_jsonb)
                    
                    # If region has a geom field, update it from the coordinates
                    if latitude and longitude:
                        await conn.execute('''
                            UPDATE regions 
                            SET geom = ST_SetSRID(ST_MakePoint($1, $2), 4326)
                            WHERE id = $3
                        ''', longitude, latitude, entity_id)
                
                logger.info(f"Loaded region: {name_en}")
            
            except Exception as e:
                logger.error(f"Error loading region {entity.get('id', 'unknown')}: {e}")

    async def load_accommodations(self, entities: List[Dict]):
        """Load accommodations data into the database."""
        for entity in entities:
            try:
                file_path = self.data_dir / "accommodations" / entity["file"]
                if not file_path.exists():
                    logger.warning(f"Accommodation file not found: {file_path}")
                    continue
                
                with open(file_path, "r", encoding="utf-8") as f:
                    accommodation_data = json.load(f)
                
                # Extract data from the JSON format
                name_en = accommodation_data.get("name", {}).get("en", "")
                name_ar = accommodation_data.get("name", {}).get("ar", "")
                desc_en = accommodation_data.get("description", {}).get("en", "")
                desc_ar = accommodation_data.get("description", {}).get("ar", "")
                accom_type = accommodation_data.get("type", "")
                stars = accommodation_data.get("stars", 0)
                city = accommodation_data.get("location", {}).get("city", "")
                region = accommodation_data.get("location", {}).get("region", "")
                latitude = accommodation_data.get("location", {}).get("coordinates", {}).get("latitude")
                longitude = accommodation_data.get("location", {}).get("coordinates", {}).get("longitude")
                price_range = accommodation_data.get("price", {})
                price_min = price_range.get("min", 0)
                price_max = price_range.get("max", 0)
                
                # Package multilingual name and description as jsonb
                name_jsonb = json.dumps({"en": name_en, "ar": name_ar})
                desc_jsonb = json.dumps({"en": desc_en, "ar": desc_ar})
                
                # Prepare full data jsonb
                data_jsonb = json.dumps(accommodation_data)
                
                # Generate a UUID if id is not provided
                entity_id = entity.get("id") or str(uuid.uuid4())
                
                # Ensure accommodation type exists
                if accom_type:
                    async with self.pool.acquire() as conn:
                        await conn.execute('''
                            INSERT INTO accommodation_types (type) 
                            VALUES ($1) 
                            ON CONFLICT (type) DO NOTHING
                        ''', accom_type)
                
                # Insert into the database
                async with self.pool.acquire() as conn:
                    await conn.execute('''
                        INSERT INTO accommodations 
                        (id, name_en, name_ar, description_en, description_ar, 
                        name, description, type, stars, city, region, 
                        latitude, longitude, price_min, price_max, data)
                        VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7::jsonb, $8, $9, $10, $11, 
                        $12, $13, $14, $15, $16::jsonb)
                        ON CONFLICT (id) DO UPDATE SET
                        name_en = $2, name_ar = $3, description_en = $4, description_ar = $5,
                        name = $6::jsonb, description = $7::jsonb, type = $8, stars = $9,
                        city = $10, region = $11, latitude = $12, longitude = $13,
                        price_min = $14, price_max = $15, data = $16::jsonb, 
                        updated_at = CURRENT_TIMESTAMP
                    ''', entity_id, name_en, name_ar, desc_en, desc_ar, 
                    name_jsonb, desc_jsonb, accom_type, stars, city, region, 
                    latitude, longitude, price_min, price_max, data_jsonb)
                    
                    # If accommodation has a geom field, update it from the coordinates
                    if latitude and longitude:
                        await conn.execute('''
                            UPDATE accommodations 
                            SET geom = ST_SetSRID(ST_MakePoint($1, $2), 4326)
                            WHERE id = $3
                        ''', longitude, latitude, entity_id)
                
                logger.info(f"Loaded accommodation: {name_en}")
            
            except Exception as e:
                logger.error(f"Error loading accommodation {entity.get('id', 'unknown')}: {e}")

    async def load_restaurants(self, entities: List[Dict]):
        """Load restaurants data into the database."""
        for entity in entities:
            try:
                file_path = self.data_dir / "restaurants" / entity["file"]
                if not file_path.exists():
                    logger.warning(f"Restaurant file not found: {file_path}")
                    continue
                
                with open(file_path, "r", encoding="utf-8") as f:
                    restaurant_data = json.load(f)
                
                # Extract data from the JSON format
                name_en = restaurant_data.get("name", {}).get("en", "")
                name_ar = restaurant_data.get("name", {}).get("ar", "")
                desc_en = restaurant_data.get("description", {}).get("en", "")
                desc_ar = restaurant_data.get("description", {}).get("ar", "")
                
                # Handle cuisine - could be a string or a list
                raw_cuisine = restaurant_data.get("cuisine", "")
                cuisine = raw_cuisine
                if isinstance(raw_cuisine, list):
                    # Join multiple cuisines with a comma or take the first one
                    cuisine = raw_cuisine[0] if raw_cuisine else ""
                    # Store the full list in the data JSON
                    restaurant_data["cuisines"] = raw_cuisine
                
                rest_type = restaurant_data.get("type", "")
                city = restaurant_data.get("location", {}).get("city", "")
                region = restaurant_data.get("location", {}).get("region", "")
                latitude = restaurant_data.get("location", {}).get("coordinates", {}).get("latitude")
                longitude = restaurant_data.get("location", {}).get("coordinates", {}).get("longitude")
                
                # Package multilingual name and description as jsonb
                name_jsonb = json.dumps({"en": name_en, "ar": name_ar})
                desc_jsonb = json.dumps({"en": desc_en, "ar": desc_ar})
                
                # Prepare full data jsonb
                data_jsonb = json.dumps(restaurant_data)
                
                # Generate a UUID if id is not provided
                entity_id = entity.get("id") or str(uuid.uuid4())
                
                # Ensure cuisine type exists
                if cuisine:
                    async with self.pool.acquire() as conn:
                        await conn.execute('''
                            INSERT INTO cuisines (type) 
                            VALUES ($1) 
                            ON CONFLICT (type) DO NOTHING
                        ''', cuisine)
                
                # Insert into the database
                async with self.pool.acquire() as conn:
                    await conn.execute('''
                        INSERT INTO restaurants 
                        (id, name_en, name_ar, description_en, description_ar, 
                        name, description, cuisine, type, city, region, 
                        latitude, longitude, data)
                        VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7::jsonb, $8, $9, $10, $11, 
                        $12, $13, $14::jsonb)
                        ON CONFLICT (id) DO UPDATE SET
                        name_en = $2, name_ar = $3, description_en = $4, description_ar = $5,
                        name = $6::jsonb, description = $7::jsonb, cuisine = $8, type = $9,
                        city = $10, region = $11, latitude = $12, longitude = $13,
                        data = $14::jsonb, updated_at = CURRENT_TIMESTAMP
                    ''', entity_id, name_en, name_ar, desc_en, desc_ar, 
                    name_jsonb, desc_jsonb, cuisine, rest_type, city, region, 
                    latitude, longitude, data_jsonb)
                    
                    # If restaurant has a geom field, update it from the coordinates
                    if latitude and longitude:
                        await conn.execute('''
                            UPDATE restaurants 
                            SET geom = ST_SetSRID(ST_MakePoint($1, $2), 4326)
                            WHERE id = $3
                        ''', longitude, latitude, entity_id)
                
                logger.info(f"Loaded restaurant: {name_en}")
            
            except Exception as e:
                logger.error(f"Error loading restaurant {entity.get('id', 'unknown')}: {e}")

    async def load_transportation(self, entities: List[Dict]):
        """Log transportation data as we don't have a dedicated table for it."""
        for entity in entities:
            try:
                file_path = self.data_dir / "transportation" / entity["file"]
                if not file_path.exists():
                    logger.warning(f"Transportation file not found: {file_path}")
                    continue
                
                logger.info(f"Transportation data found: {entity['name']} (saving to attractions table)")
                
                with open(file_path, "r", encoding="utf-8") as f:
                    transport_data = json.load(f)
                
                # Extract data from the JSON format - store as an attraction with type "transportation"
                name_en = transport_data.get("name", {}).get("en", "")
                name_ar = transport_data.get("name", {}).get("ar", "")
                desc_en = transport_data.get("description", {}).get("en", "")
                desc_ar = transport_data.get("description", {}).get("ar", "")
                transport_type = "transportation"
                
                # Package multilingual name and description as jsonb
                name_jsonb = json.dumps({"en": name_en, "ar": name_ar})
                desc_jsonb = json.dumps({"en": desc_en, "ar": desc_ar})
                
                # Prepare full data jsonb
                data_jsonb = json.dumps(transport_data)
                
                # Generate a UUID if id is not provided
                entity_id = entity.get("id") or str(uuid.uuid4())
                
                # Insert into the attractions table (as there's no dedicated transportation table)
                async with self.pool.acquire() as conn:
                    await conn.execute('''
                        INSERT INTO attractions 
                        (id, name_en, name_ar, description_en, description_ar, 
                        name, description, type, data)
                        VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7::jsonb, $8, $9::jsonb)
                        ON CONFLICT (id) DO UPDATE SET
                        name_en = $2, name_ar = $3, description_en = $4, description_ar = $5,
                        name = $6::jsonb, description = $7::jsonb, type = $8, 
                        data = $9::jsonb, updated_at = CURRENT_TIMESTAMP
                    ''', entity_id, name_en, name_ar, desc_en, desc_ar, 
                    name_jsonb, desc_jsonb, transport_type, data_jsonb)
                
                logger.info(f"Loaded transportation: {name_en}")
            
            except Exception as e:
                logger.error(f"Error loading transportation {entity.get('id', 'unknown')}: {e}")


async def main():
    """Run the main data loading process."""
    loader = TourismDataLoader(DATABASE_URL)
    success = await loader.load_all_data()
    if success:
        logger.info("Data loading completed successfully")
    else:
        logger.error("Data loading failed")


if __name__ == "__main__":
    asyncio.run(main())