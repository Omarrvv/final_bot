#!/usr/bin/env python3
"""Add sample attraction data directly using Python."""
import os
import json
from datetime import datetime

# Sample attractions data
SAMPLE_ATTRACTIONS = [
    {
        "id": "pyr001",
        "name_en": "The Great Pyramids of Giza",
        "name_ar": "أهرامات الجيزة",
        "description_en": "The Pyramids of Giza are the only surviving structures of the Seven Wonders of the Ancient World.",
        "description_ar": "أهرامات الجيزة هي الهياكل الوحيدة الباقية من عجائب الدنيا السبع في العالم القديم.",
        "city": "Cairo",
        "location": {"lat": 29.9792, "lon": 31.1342},
        "rating": 4.8,
        "opening_hours": "Daily 8:00 AM - 5:00 PM",
        "entrance_fee": 240,
        "tags": ["ancient", "wonder", "pyramid", "pharaoh", "tomb"]
    },
    {
        "id": "mus001",
        "name_en": "The Egyptian Museum",
        "name_ar": "المتحف المصري",
        "description_en": "The Egyptian Museum houses the world's largest collection of Pharaonic antiquities.",
        "description_ar": "المتحف المصري يضم أكبر مجموعة من الآثار الفرعونية في العالم.",
        "city": "Cairo",
        "location": {"lat": 30.0478, "lon": 31.2336},
        "rating": 4.6,
        "opening_hours": "Daily 9:00 AM - 5:00 PM",
        "entrance_fee": 200,
        "tags": ["museum", "antiquities", "pharaoh", "tutankhamun"]
    }
]

# Copy and run in container
if __name__ == "__main__":
    from src.knowledge.database import DatabaseManager
    
    # Get database manager
    db = DatabaseManager()
    
    # Add attractions
    for attraction in SAMPLE_ATTRACTIONS:
        try:
            # Convert locations and tags to JSON strings
            attraction["location"] = json.dumps(attraction["location"])
            attraction["tags"] = json.dumps(attraction["tags"])
            # Add current timestamp
            attraction["created_at"] = datetime.now().isoformat()
            attraction["updated_at"] = datetime.now().isoformat()
            
            # Add to database
            db.add_attraction(attraction)
            print(f"Added: {attraction['name_en']}")
        except Exception as e:
            print(f"Error adding attraction {attraction['id']}: {e}")
    
    # Verify data
    all_attractions = db.get_all_attractions()
    print(f"Total attractions in database: {len(all_attractions)}")