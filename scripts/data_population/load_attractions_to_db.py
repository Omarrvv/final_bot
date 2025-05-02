#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

# Add the src directory to the Python path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.logger import get_logger
from src.knowledge.database import DatabaseManager, DatabaseType

logger = get_logger(__name__)

def load_attractions():
    """Load attractions from JSON files into the database."""
    db_manager = DatabaseManager()
    
    try:
        # Process each JSON file in the attractions directory
        attractions_dir = "./data/attractions"
        for subdir, _, files in os.walk(attractions_dir):
            for file in files:
                if not file.endswith('.json'):
                    continue
                    
                json_file = os.path.join(subdir, file)
                logger.info(f"Processing {json_file}")
                
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        attraction = json.load(f)
                    
                    # Extract required fields
                    attraction_id = attraction.get('id')
                    name_en = attraction.get('name_en') or attraction.get('name', {}).get('en')
                    name_ar = attraction.get('name_ar') or attraction.get('name', {}).get('ar')
                    attraction_type = attraction.get('type', 'other')
                    city = attraction.get('city', '')
                    region = attraction.get('region', '')
                    latitude = attraction.get('latitude') or attraction.get('location', {}).get('latitude')
                    longitude = attraction.get('longitude') or attraction.get('location', {}).get('longitude')
                    description_en = attraction.get('description_en') or attraction.get('description', {}).get('en')
                    description_ar = attraction.get('description_ar') or attraction.get('description', {}).get('ar')
                    
                    # Validate required fields
                    if not all([attraction_id, name_en]):
                        logger.error(f"Missing required fields in {json_file}")
                        continue
                    
                    # Build the data JSON field with additional attributes
                    data = {
                        'opening_hours': attraction.get('opening_hours'),
                        'entrance_fee': attraction.get('entrance_fee'),
                        'tags': attraction.get('tags', []),
                        'images': attraction.get('images', []),
                        'rating': attraction.get('rating'),
                        'facilities': attraction.get('facilities', []),
                        'best_time_to_visit': attraction.get('best_time_to_visit'),
                        'tips': attraction.get('tips', []),
                        'accessibility': attraction.get('accessibility', {})
                    }
                    
                    # Remove None values from data
                    data = {k: v for k, v in data.items() if v is not None}
                    
                    # Insert into database using PostgreSQL style parameters if using PostgreSQL
                    if db_manager.db_type == DatabaseType.POSTGRES:
                        query = """
                            INSERT INTO attractions (
                                id, name_en, name_ar, type, city, region,
                                latitude, longitude, description_en, description_ar,
                                data, created_at, updated_at
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s,
                                %s::jsonb, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
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
                                updated_at=CURRENT_TIMESTAMP
                        """
                    else:
                        # SQLite version
                        query = """
                            INSERT INTO attractions (
                                id, name_en, name_ar, type, city, region,
                                latitude, longitude, description_en, description_ar,
                                data, created_at, updated_at
                            ) VALUES (
                                ?, ?, ?, ?, ?, ?,
                                ?, ?, ?, ?,
                                ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                            ) ON CONFLICT(id) DO UPDATE SET
                                name_en=excluded.name_en,
                                name_ar=excluded.name_ar,
                                type=excluded.type,
                                city=excluded.city,
                                region=excluded.region,
                                latitude=excluded.latitude,
                                longitude=excluded.longitude,
                                description_en=excluded.description_en,
                                description_ar=excluded.description_ar,
                                data=excluded.data,
                                updated_at=CURRENT_TIMESTAMP
                        """
                    
                    params = (
                        attraction_id, name_en, name_ar, attraction_type,
                        city, region, latitude, longitude,
                        description_en, description_ar,
                        json.dumps(data)
                    )
                    
                    db_manager.execute_query(query, params)
                    logger.info(f"Loaded attraction: {name_en}")
                    
                except KeyError as e:
                    logger.error(f"Error loading {json_file}: Missing required field {e}")
                except json.JSONDecodeError as e:
                    logger.error(f"Error loading {json_file}: Invalid JSON - {str(e)}")
                except Exception as e:
                    logger.error(f"Error loading {json_file}: {str(e)}")
                    continue
                    
    except Exception as e:
        logger.error(f"Failed to load attractions: {str(e)}")
    finally:
        db_manager.close()

if __name__ == '__main__':
    load_attractions()