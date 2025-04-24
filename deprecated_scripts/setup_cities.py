import sqlite3
import uuid
from datetime import datetime
import json

# Connect to database
conn = sqlite3.connect('data/egypt_chatbot.db')
cursor = conn.cursor()

# Check if cities table exists
cursor.execute("""
SELECT name FROM sqlite_master WHERE type='table' AND name='cities'
""")
if not cursor.fetchone():
    print('Creating cities table...')
    cursor.execute('''
    CREATE TABLE cities (
        id TEXT PRIMARY KEY,
        name_en TEXT NOT NULL,
        name_ar TEXT,
        country TEXT DEFAULT 'Egypt',
        city_type TEXT,
        latitude REAL,
        longitude REAL,
        data TEXT,
        embedding BLOB,
        created_at TEXT,
        updated_at TEXT
    )
    ''')

# Insert sample data
city_id = str(uuid.uuid4())
now = datetime.now().isoformat()
city_data = {
    'id': city_id,
    'name_en': 'Cairo',
    'name_ar': 'القاهرة',
    'country': 'Egypt',
    'city_type': 'Capital',
    'latitude': 30.0444,
    'longitude': 31.2357,
    'data': json.dumps({'population': 9500000, 'area': 3085}),
    'embedding': None,
    'created_at': now,
    'updated_at': now
}

# Check if the city already exists
cursor.execute('SELECT id FROM cities WHERE name_en = ?', ('Cairo',))
if cursor.fetchone():
    print('Cairo already exists in the database')
else:
    print('Adding Cairo to the database...')
    cursor.execute('''
    INSERT INTO cities (id, name_en, name_ar, country, city_type, latitude, longitude, data, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        city_data['id'],
        city_data['name_en'],
        city_data['name_ar'],
        city_data['country'],
        city_data['city_type'],
        city_data['latitude'],
        city_data['longitude'],
        city_data['data'],
        city_data['created_at'],
        city_data['updated_at']
    ))

# Commit and close
conn.commit()
conn.close()
print('Database operations completed') 