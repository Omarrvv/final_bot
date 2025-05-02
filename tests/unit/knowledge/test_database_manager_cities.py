"""
Tests for city-related methods in the DatabaseManager.
"""
import unittest
import uuid
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
import json

from src.knowledge.database import DatabaseManager

class TestDatabaseManagerCities(unittest.TestCase):

    def setUp(self):
        """Set up test environment before each test."""
        # Create a test database file
        self.test_db_uri = os.environ.get("POSTGRES_URI") or "postgresql://postgres:postgres@localhost:5432/egypt_chatbot"
    
        # Create DatabaseManager instance with test database
        self.db_manager = DatabaseManager(database_uri=self.test_db_uri)

        # Create test data in PostgreSQL
        conn = self.db_manager._get_pg_connection()
        if conn:
            try:
                with conn.cursor() as cursor:
                    # Create cities table if it doesn't exist
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS cities (
                            id TEXT PRIMARY KEY,
                            name_en TEXT NOT NULL,
                            name_ar TEXT,
                            region TEXT,
                            latitude DOUBLE PRECISION,
                            longitude DOUBLE PRECISION,
                            data JSONB,
                            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    # Clear any existing test data
                    cursor.execute("DELETE FROM cities WHERE id LIKE 'test_city%'")
                    
                    # Insert test data
                    test_cities = [
                        ('test_city1', 'Cairo', 'القاهرة', 'Cairo', 30.0444, 31.2357, 
                         json.dumps({"description": "Capital of Egypt", "population": 9500000})),
                        ('test_city2', 'Alexandria', 'الإسكندرية', 'Alexandria', 31.2001, 29.9187, 
                         json.dumps({"description": "Mediterranean port city", "population": 5200000})),
                        ('test_city3', 'Luxor', 'الأقصر', 'Luxor', 25.6872, 32.6396, 
                         json.dumps({"description": "Ancient city", "population": 507000}))
                    ]
                    
                    cursor.executemany(
                        """INSERT INTO cities (id, name_en, name_ar, region, latitude, longitude, data)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING""",
                        test_cities
                    )
                    conn.commit()
            finally:
                self.db_manager._return_pg_connection(conn)

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
        city = self.db_manager.get_city("test_city1")
        
        # Verify the result
        self.assertIsNotNone(city)
        self.assertEqual(city["id"], "test_city1")
        name_obj = json.loads(city["name"])
        self.assertEqual(name_obj["en"], "Cairo")
    
    def test_get_city_nonexistent_id(self):
        """Test retrieving a city with a non-existent ID."""
        # Call the method with a non-existent ID
        city = self.db_manager.get_city("nonexistent-id")
        
        # Verify the result is None
        self.assertIsNone(city)
    
    def test_search_cities_by_name(self):
        """Test searching cities by name."""
        # Call the method
        cities = self.db_manager.search_cities({"name": '{"en": "Cairo"}'})
        
        # Verify the result
        self.assertEqual(len(cities), 1)
        name_obj = json.loads(cities[0]["name"])
        self.assertEqual(name_obj["en"], "Cairo")
    
    def test_search_cities_partial_match(self):
        """Test searching cities with partial name match."""
        # Call the method with partial name
        cities = self.db_manager.search_cities({"name": {"$like": "%Cairo%"}})
        
        # Verify the result
        self.assertGreaterEqual(len(cities), 1)
        self.assertTrue(any(json.loads(city["name"]).get("en") == "Cairo" for city in cities))
    
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
            mock_cursor.execute.side_effect = Exception("Test error")
            
            # Call the method - fix parameter to match the method signature
            cities = self.db_manager.search_cities(query="Cairo")
            
            # Verify the result is an empty list
            self.assertEqual(cities, [])

if __name__ == '__main__':
    unittest.main()