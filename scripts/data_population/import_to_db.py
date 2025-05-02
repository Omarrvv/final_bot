#!/usr/bin/env python3
"""Script to import JSON data into PostgreSQL database."""
import os
import sys
import json
from dotenv import load_dotenv

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(project_root)

# Load environment variables from .env
load_dotenv()

# Set PostgreSQL environment variables
os.environ["USE_POSTGRES"] = "true"
os.environ["POSTGRES_URI"] = f"postgresql://{os.getenv('POSTGRES_USER', 'user')}:{os.getenv('POSTGRES_PASSWORD', 'password')}@{os.getenv('POSTGRES_HOST', 'db_postgres')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DB', 'egypt_chatbot')}"

from src.knowledge.database import DatabaseManager

def import_attractions():
    """Import attractions from JSON files into database."""
    db = DatabaseManager()
    
    # Ensure we're using PostgreSQL
    if str(db.db_type) != "DatabaseType.POSTGRES":
        print(f"ERROR: PostgreSQL database not configured. Current type: {db.db_type}")
        return False
        
    print("Connected to PostgreSQL database")
    
    attractions_dir = "./data/attractions/historical"
    for filename in os.listdir(attractions_dir):
        if not filename.endswith('.json'):
            continue
            
        with open(os.path.join(attractions_dir, filename), 'r', encoding='utf-8') as f:
            attraction_data = json.load(f)
            
            # Prepare data for database insertion
            sql = """
                INSERT INTO attractions (
                    id, name_en, name_ar, type, city, region,
                    latitude, longitude, description_en, description_ar,
                    data, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (id) DO UPDATE SET
                    name_en = EXCLUDED.name_en,
                    name_ar = EXCLUDED.name_ar,
                    type = EXCLUDED.type,
                    city = EXCLUDED.city,
                    region = EXCLUDED.region,
                    latitude = EXCLUDED.latitude,
                    longitude = EXCLUDED.longitude,
                    description_en = EXCLUDED.description_en,
                    description_ar = EXCLUDED.description_ar,
                    data = EXCLUDED.data,
                    updated_at = EXCLUDED.updated_at
            """
            
            # Prepare the values
            values = (
                attraction_data['id'],
                attraction_data['name']['en'],
                attraction_data['name']['ar'],
                attraction_data['type'],
                attraction_data['city'],
                attraction_data['region'],
                attraction_data['coordinates']['latitude'],
                attraction_data['coordinates']['longitude'],
                attraction_data['description']['en'],
                attraction_data['description']['ar'],
                json.dumps({
                    'history': attraction_data.get('history', {}),
                    'highlights': attraction_data.get('highlights', []),
                    'practical_info': attraction_data.get('practical_info', {}),
                    'tips': attraction_data.get('tips', {}),
                    'images': attraction_data.get('images', []),
                    'tags': attraction_data.get('tags', [])
                }),
                attraction_data['created_at'],
                attraction_data['updated_at']
            )
            
            try:
                # Execute using connection pool
                db.execute_postgres_query(sql, values)
                print(f"Imported attraction: {attraction_data['name']['en']}")
            except Exception as e:
                print(f"Error importing {attraction_data['id']}: {str(e)}")
                continue
                
    print("Import complete!")

if __name__ == "__main__":
    import_attractions()