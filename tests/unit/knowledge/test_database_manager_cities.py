"""
Tests for city-related methods in the DatabaseManager.
"""
import unittest
import uuid
import os
import sqlite3
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from src.knowledge.database import DatabaseManager

class TestDatabaseManagerCities(unittest.TestCase):
    """Tests for city-related methods in the DatabaseManager class."""
    
    def setUp(self):
        """Set up test environment before each test."""
        # Create a test database file
        self.test_db_path = os.path.abspath("test_cities_db.sqlite")
        
        # Create DatabaseManager instance with test database
        self.db_manager = DatabaseManager(database_uri=f"sqlite:///{self.test_db_path}")
        
        # Create the connection directly to ensure it exists
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        # Create cities table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cities (
                id TEXT PRIMARY KEY,
                name_en TEXT,
                name_ar TEXT,
                country TEXT,
                city_type TEXT,
                latitude REAL,
                longitude REAL,
                data TEXT,
                embedding BLOB,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        # Insert test city
        self.test_city_id = str(uuid.uuid4())
        self.test_city = {
            "id": self.test_city_id,
            "name_en": "Cairo",
            "name_ar": "القاهرة",
            "country": "Egypt",
            "city_type": "Capital",
            "latitude": 30.0444,
            "longitude": 31.2357,
            "data": '{"population": 9500000, "area": 3085}',
            "embedding": b'',  # Empty blob for testing
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        cursor.execute('''
            INSERT INTO cities
            (id, name_en, name_ar, country, city_type, latitude, longitude, data, embedding, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            self.test_city["id"],
            self.test_city["name_en"],
            self.test_city["name_ar"],
            self.test_city["country"],
            self.test_city["city_type"],
            self.test_city["latitude"],
            self.test_city["longitude"],
            self.test_city["data"],
            self.test_city["embedding"],
            self.test_city["created_at"],
            self.test_city["updated_at"]
        ))
        
        # Insert additional cities for search tests
        for city_name in ["Alexandria", "Luxor", "Aswan", "Giza"]:
            city_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO cities
                (id, name_en, name_ar, country, city_type, latitude, longitude, data, embedding, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                city_id,
                city_name,
                f"Arabic {city_name}",  # Placeholder for Arabic names
                "Egypt",
                "City",
                30.0,  # Placeholder coordinates
                31.0,
                '{"population": 500000}',
                b'',
                datetime.now(timezone.utc).isoformat(),
                datetime.now(timezone.utc).isoformat()
            ))
            
        conn.commit()
        conn.close()
        
        # Reconnect the database manager to ensure it's using the populated database
        self.db_manager.close()
        self.db_manager = DatabaseManager(database_uri=f"sqlite:///{self.test_db_path}")
    
    def tearDown(self):
        """Clean up test environment after each test."""
        # Close database connection
        self.db_manager.close()
        
        # Remove test database file
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
    
    def test_get_city_by_id(self):
        """Test retrieving a city by ID."""
        # Call the method
        city = self.db_manager.get_city(self.test_city_id)
        
        # Verify the result
        self.assertIsNotNone(city)
        self.assertEqual(city["id"], self.test_city_id)
        self.assertEqual(city["name_en"], "Cairo")
        self.assertEqual(city["country"], "Egypt")
    
    def test_get_city_nonexistent_id(self):
        """Test retrieving a city with a non-existent ID."""
        # Call the method with a non-existent ID
        city = self.db_manager.get_city("nonexistent-id")
        
        # Verify the result is None
        self.assertIsNone(city)
    
    def test_search_cities_by_name(self):
        """Test searching cities by name."""
        # Call the method
        cities = self.db_manager.search_cities({"name_en": "Cairo"})
        
        # Verify the result
        self.assertEqual(len(cities), 1)
        self.assertEqual(cities[0]["name_en"], "Cairo")
    
    def test_search_cities_partial_match(self):
        """Test searching cities with partial name match."""
        # Call the method with partial name
        cities = self.db_manager.search_cities({"name_en": {"$like": "%Ca%"}})
        
        # Verify the result
        self.assertGreaterEqual(len(cities), 1)
        self.assertTrue(any(city["name_en"] == "Cairo" for city in cities))
    
    def test_search_cities_limit(self):
        """Test limiting the number of cities returned."""
        # Insert additional cities to ensure we have more than the limit
        
        # Call the method with limit
        cities = self.db_manager.search_cities(query={}, limit=2)
        
        # Verify the result
        self.assertLessEqual(len(cities), 2)
    
    def test_search_cities_with_error(self):
        """Test error handling in search_cities method."""
        # Mock the execute method to raise an exception
        with patch.object(self.db_manager, 'connection') as mock_conn:
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.execute.side_effect = sqlite3.Error("Test error")
            
            # Call the method - fix parameter to match the method signature
            cities = self.db_manager.search_cities(query="Cairo")
            
            # Verify the result is an empty list
            self.assertEqual(cities, [])

if __name__ == '__main__':
    unittest.main() 