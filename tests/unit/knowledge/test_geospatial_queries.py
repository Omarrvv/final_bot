"""
Unit tests for the geospatial query methods in DatabaseManager.
"""
import os
import pytest
import numpy as np
from unittest.mock import patch, MagicMock

from src.knowledge.database import DatabaseManager, DatabaseType

# Test constants
TEST_DB_URI = "sqlite:///:memory:"
CAIRO_COORDS = (30.0444, 31.2357)  # Latitude, Longitude for Cairo
GIZA_COORDS = (29.9773, 31.1325)   # Latitude, Longitude for Giza
LUXOR_COORDS = (25.6872, 32.6396)  # Latitude, Longitude for Luxor

class TestGeospatialQueries:
    """Tests for geospatial query methods."""
    
    def setup_method(self):
        """Set up test database manager."""
        self.db_manager = DatabaseManager(database_uri=TEST_DB_URI)
        
        # Create in-memory test tables for SQLite tests
        self.db_manager.connection.execute("""
            CREATE TABLE IF NOT EXISTS attractions (
                id TEXT PRIMARY KEY,
                name_en TEXT,
                name_ar TEXT,
                type TEXT,
                city TEXT,
                latitude REAL,
                longitude REAL,
                description_en TEXT
            )
        """)
        
        # Insert test data
        self.db_manager.connection.execute("""
            INSERT INTO attractions (id, name_en, city, latitude, longitude)
            VALUES ('cairo_tower', 'Cairo Tower', 'Cairo', ?, ?)
        """, CAIRO_COORDS)
        
        self.db_manager.connection.execute("""
            INSERT INTO attractions (id, name_en, city, latitude, longitude)
            VALUES ('pyramids', 'Pyramids of Giza', 'Giza', ?, ?)
        """, GIZA_COORDS)
        
        self.db_manager.connection.execute("""
            INSERT INTO attractions (id, name_en, city, latitude, longitude)
            VALUES ('karnak', 'Karnak Temple', 'Luxor', ?, ?)
        """, LUXOR_COORDS)
        
        self.db_manager.connection.commit()
    
    def teardown_method(self):
        """Clean up after tests."""
        self.db_manager.connection.close()
    
    def test_find_nearby_sqlite(self):
        """Test finding attractions near a point using SQLite."""
        # Find attractions near Cairo (should include Cairo Tower and Pyramids but not Luxor)
        results = self.db_manager.find_nearby(
            table="attractions", 
            latitude=CAIRO_COORDS[0], 
            longitude=CAIRO_COORDS[1], 
            radius_km=50
        )
        
        # Verify results
        assert len(results) == 2
        assert any(r['id'] == 'cairo_tower' for r in results)
        assert any(r['id'] == 'pyramids' for r in results)
        assert all(r['id'] != 'karnak' for r in results)
        
        # Check if distance is calculated
        assert all('distance_km' in r for r in results)
        
        # Nearest should be Cairo Tower
        assert sorted(results, key=lambda r: r['distance_km'])[0]['id'] == 'cairo_tower'
    
    def test_find_nearby_with_filters_sqlite(self):
        """Test finding attractions near a point with additional filters."""
        # Find attractions near Cairo with city filter
        results = self.db_manager.find_nearby(
            table="attractions", 
            latitude=CAIRO_COORDS[0], 
            longitude=CAIRO_COORDS[1], 
            radius_km=50,
            additional_filters={"city": "Cairo"}
        )
        
        # Verify results
        assert len(results) == 1
        assert results[0]['id'] == 'cairo_tower'
    
    @patch('src.knowledge.database.DatabaseManager._check_postgis_enabled')
    @patch('src.knowledge.database.DatabaseManager.execute_postgres_query')
    @patch('src.knowledge.database.DatabaseManager._postgres_column_exists')
    def test_find_nearby_postgis(self, mock_column_exists, mock_execute_query, mock_check_postgis):
        """Test finding attractions near a point using PostGIS."""
        # Configure mocks
        mock_check_postgis.return_value = True
        mock_column_exists.return_value = True
        
        # Mock PostgreSQL query results
        mock_results = [
            {
                'id': 'cairo_tower',
                'name_en': 'Cairo Tower',
                'city': 'Cairo',
                'latitude': CAIRO_COORDS[0],
                'longitude': CAIRO_COORDS[1],
                'distance_km': 0.1
            },
            {
                'id': 'pyramids',
                'name_en': 'Pyramids of Giza',
                'city': 'Giza',
                'latitude': GIZA_COORDS[0],
                'longitude': GIZA_COORDS[1],
                'distance_km': 15.7
            }
        ]
        mock_execute_query.return_value = mock_results
        
        # Set database type to PostgreSQL
        self.db_manager.db_type = DatabaseType.POSTGRES
        
        # Find attractions near Cairo
        results = self.db_manager.find_nearby(
            table="attractions", 
            latitude=CAIRO_COORDS[0], 
            longitude=CAIRO_COORDS[1], 
            radius_km=50
        )
        
        # Verify results
        assert len(results) == 2
        assert any(r['id'] == 'cairo_tower' for r in results)
        assert any(r['id'] == 'pyramids' for r in results)
        
        # Verify PostGIS query was called
        mock_execute_query.assert_called_once()
        call_args = mock_execute_query.call_args[0]
        
        # Check that the query includes PostGIS functions
        assert "ST_Distance" in call_args[0]
        assert "ST_SetSRID" in call_args[0]
        assert "ST_MakePoint" in call_args[0]
        assert "ST_DWithin" in call_args[0]
        
        # Verify parameters
        params = call_args[1]
        assert params[0] == CAIRO_COORDS[1]  # Longitude first in PostGIS
        assert params[1] == CAIRO_COORDS[0]  # Latitude second
    
    @patch('src.knowledge.database.DatabaseManager.execute_postgres_query')
    def test_check_postgis_enabled(self, mock_execute_query):
        """Test checking if PostGIS is enabled."""
        # Set database type to PostgreSQL
        self.db_manager.db_type = DatabaseType.POSTGRES
        
        # Test when PostGIS is enabled
        mock_execute_query.return_value = {'count': 1}
        assert self.db_manager._check_postgis_enabled() is True
        
        # Test when PostGIS is not enabled
        mock_execute_query.return_value = None
        assert self.db_manager._check_postgis_enabled() is False
        
        # Test when database type is not PostgreSQL
        self.db_manager.db_type = DatabaseType.SQLITE
        assert self.db_manager._check_postgis_enabled() is False
    
    @patch('src.knowledge.database.DatabaseManager.execute_postgres_query')
    @patch('src.knowledge.database.DatabaseManager._check_postgis_enabled')
    @patch('src.knowledge.database.DatabaseManager._table_exists')
    @patch('src.knowledge.database.DatabaseManager._postgres_column_exists')
    def test_update_geospatial_columns(self, mock_column_exists, mock_table_exists, 
                                       mock_check_postgis, mock_execute_query):
        """Test updating geospatial columns."""
        # Set database type to PostgreSQL
        self.db_manager.db_type = DatabaseType.POSTGRES
        
        # Configure mocks
        mock_check_postgis.return_value = True
        mock_table_exists.return_value = True
        
        # Test when geometry column exists
        mock_column_exists.return_value = True
        mock_execute_query.return_value = 10  # 10 rows updated
        
        result = self.db_manager.update_geospatial_columns(['attractions'])
        
        # Verify result
        assert result is True
        
        # Verify update was called
        update_calls = [call for call in mock_execute_query.call_args_list 
                      if "UPDATE" in call[0][0]]
        assert len(update_calls) == 1
        
        # Test when geometry column doesn't exist
        mock_column_exists.return_value = False
        mock_execute_query.reset_mock()
        
        result = self.db_manager.update_geospatial_columns(['attractions'])
        
        # Verify result
        assert result is True
        
        # Verify ALTER TABLE was called to add geometry column
        alter_calls = [call for call in mock_execute_query.call_args_list 
                     if "ALTER TABLE" in call[0][0]]
        assert len(alter_calls) == 1
        
        # Test when PostGIS is not enabled
        mock_check_postgis.return_value = False
        
        result = self.db_manager.update_geospatial_columns()
        
        # Verify result
        assert result is False 