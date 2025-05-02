"""
Unit tests for the geospatial query methods in DatabaseManager.
"""
import os
import pytest
import numpy as np
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from unittest.mock import patch, MagicMock, call

from src.knowledge.database import DatabaseManager, DatabaseType

# Test constants
TEST_DB_URI = os.environ.get("POSTGRES_URI") or "postgresql://postgres:postgres@localhost:5432/egypt_chatbot_test"
CAIRO_COORDS = (30.0444, 31.2357)  # Latitude, Longitude for Cairo
GIZA_COORDS = (29.9773, 31.1325)   # Latitude, Longitude for Giza
LUXOR_COORDS = (25.6872, 32.6396)  # Latitude, Longitude for Luxor

class TestGeospatialQueries:
    """Tests for geospatial query methods."""
    
    @pytest.fixture(autouse=True)
    def setup_db(self):
        """Set up test database manager with PostgreSQL."""
        self.db_manager = DatabaseManager(database_uri=TEST_DB_URI)
        yield
        # No teardown needed for mock-based tests
    
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
    
    @patch('src.knowledge.database.DatabaseManager._check_postgis_enabled', return_value=True)
    @patch('src.knowledge.database.DatabaseManager._postgres_column_exists', return_value=True)
    @patch('src.knowledge.database.DatabaseManager.execute_postgres_query')
    def test_find_nearby_with_filters(self, mock_execute_query, mock_column_exists, mock_check_postgis):
        """Test find_nearby with additional filters."""
        # Mock query results
        mock_execute_query.return_value = [{
            'id': 'test_attraction_1',
            'name_en': 'Test Monument',
            'type': 'monument',
            'distance_km': 2.5
        }]
        
        # Execute the find_nearby method with filters
        filters = {'type': 'monument'}
        results = self.db_manager.find_nearby(
            'attractions', 
            CAIRO_COORDS[0], 
            CAIRO_COORDS[1], 
            5.0, 
            additional_filters=filters
        )
        
        # Verify we got results
        assert len(results) == 1
        assert results[0]['id'] == 'test_attraction_1'
        assert results[0]['type'] == 'monument'
        assert 'distance_km' in results[0]
        
        # Verify the SQL query was constructed correctly
        call_args = mock_execute_query.call_args[0]
        query_str = call_args[0]
        params = call_args[1]
        
        # Check both the spatial query and type filter are applied
        assert "ST_DWithin" in query_str
        assert "type = %s" in query_str
        assert 'monument' in params
    
    @patch('src.knowledge.database.DatabaseManager.execute_postgres_query')
    def test_check_postgis_enabled(self, mock_execute_query):
        """Test checking if PostGIS is enabled."""
        # Test when PostGIS is enabled
        mock_execute_query.return_value = [{'count': 1}]
        assert self.db_manager._check_postgis_enabled() is True
        
        # Test when PostGIS is not enabled
        mock_execute_query.return_value = []
        assert self.db_manager._check_postgis_enabled() is False
    
    @patch('src.knowledge.database.DatabaseManager.execute_postgres_query')
    @patch('src.knowledge.database.DatabaseManager._check_postgis_enabled')
    @patch('src.knowledge.database.DatabaseManager._table_exists')
    @patch('src.knowledge.database.DatabaseManager._postgres_column_exists')
    def test_update_geospatial_columns(self, mock_column_exists, mock_table_exists, 
                                       mock_check_postgis, mock_execute_query):
        """Test updating geospatial columns."""
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
        assert len(update_calls) >= 1
        
        # Test when geometry column doesn't exist
        mock_column_exists.return_value = False
        mock_execute_query.reset_mock()
        
        result = self.db_manager.update_geospatial_columns(['attractions'])
        
        # Verify result
        assert result is True
        
        # Verify ALTER TABLE was called to add geometry column
        alter_calls = [call for call in mock_execute_query.call_args_list 
                     if "ALTER TABLE" in call[0][0]]
        assert len(alter_calls) >= 1
        
        # Test when PostGIS is not enabled
        mock_check_postgis.return_value = False
        
        result = self.db_manager.update_geospatial_columns()
        
        # Verify result
        assert result is False
    
    @patch('src.knowledge.database.DatabaseManager.execute_postgres_query')
    def test_postgres_column_exists(self, mock_execute_query):
        """Test checking if a column exists in PostgreSQL."""
        # Test when column exists
        mock_execute_query.return_value = [{'exists': True}]
        assert self.db_manager._postgres_column_exists('attractions', 'geom') is True
        
        # Test when column doesn't exist
        mock_execute_query.return_value = [{'exists': False}]
        assert self.db_manager._postgres_column_exists('attractions', 'geom') is False
        
        # Test with empty result
        mock_execute_query.return_value = []
        assert self.db_manager._postgres_column_exists('attractions', 'geom') is False

    # --- Real Database Tests ---
    
    @pytest.fixture
    def setup_geospatial_test_data(self):
        """Create test data with geospatial features in the actual PostgreSQL database."""
        # Only execute if PostGIS is available
        conn = psycopg2.connect(TEST_DB_URI)
        postgis_available = False
        
        try:
            with conn.cursor() as cursor:
                # Check if PostGIS is installed
                cursor.execute("SELECT COUNT(*) FROM pg_extension WHERE extname = 'postgis'")
                postgis_available = cursor.fetchone()[0] > 0
                
                if not postgis_available:
                    pytest.skip("PostGIS extension not available, skipping real database tests")
                
                # Create test table with geospatial data
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS test_locations (
                        id TEXT PRIMARY KEY,
                        name TEXT,
                        type TEXT,
                        latitude FLOAT,
                        longitude FLOAT,
                        geom GEOMETRY(Point, 4326)
                    )
                """)
                
                # Clear any existing test data
                cursor.execute("DELETE FROM test_locations")
                
                # Insert test data
                test_locations = [
                    ('cairo_tower', 'Cairo Tower', 'landmark', CAIRO_COORDS[0], CAIRO_COORDS[1]),
                    ('pyramids', 'Pyramids of Giza', 'monument', GIZA_COORDS[0], GIZA_COORDS[1]),
                    ('luxor_temple', 'Luxor Temple', 'monument', LUXOR_COORDS[0], LUXOR_COORDS[1])
                ]
                
                for location in test_locations:
                    cursor.execute("""
                        INSERT INTO test_locations (id, name, type, latitude, longitude, geom)
                        VALUES (%s, %s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
                    """, (location[0], location[1], location[2], location[3], location[4], location[4], location[3]))
                
                conn.commit()
        finally:
            conn.close()
        
        return postgis_available
    
    def test_real_postgis_find_nearby(self, setup_geospatial_test_data):
        """Test geospatial queries using a real PostgreSQL database with PostGIS."""
        if not setup_geospatial_test_data:
            pytest.skip("PostGIS setup failed")
        
        # Find nearby locations within 20km of Cairo
        results = self.db_manager.find_nearby(
            table="test_locations",
            latitude=CAIRO_COORDS[0],
            longitude=CAIRO_COORDS[1],
            radius_km=20
        )
        
        # Should find Cairo Tower and Pyramids of Giza (which are close to Cairo)
        assert len(results) == 2
        assert any(r['id'] == 'cairo_tower' for r in results)
        assert any(r['id'] == 'pyramids' for r in results)
        assert not any(r['id'] == 'luxor_temple' for r in results)  # Luxor is far from Cairo
        
        # Verify distances are calculated correctly
        for result in results:
            assert 'distance_km' in result
            
        # Find locations with filter
        results = self.db_manager.find_nearby(
            table="test_locations",
            latitude=CAIRO_COORDS[0],
            longitude=CAIRO_COORDS[1],
            radius_km=500,  # Large radius to include all test points
            additional_filters={"type": "monument"}
        )
        
        # Should find Pyramids of Giza and Luxor Temple (both are monuments)
        assert len(results) == 2
        assert any(r['id'] == 'pyramids' for r in results)
        assert any(r['id'] == 'luxor_temple' for r in results)
        assert not any(r['id'] == 'cairo_tower' for r in results)  # Not a monument
        
        # Try with a small radius from Luxor
        results = self.db_manager.find_nearby(
            table="test_locations",
            latitude=LUXOR_COORDS[0],
            longitude=LUXOR_COORDS[1],
            radius_km=10
        )
        
        # Should only find Luxor Temple
        assert len(results) == 1
        assert results[0]['id'] == 'luxor_temple'
    
    def test_real_geospatial_columns_update(self, setup_geospatial_test_data):
        """Test updating geospatial columns in a real database."""
        if not setup_geospatial_test_data:
            pytest.skip("PostGIS setup failed")
        
        # Create a test table without geom column
        conn = psycopg2.connect(TEST_DB_URI)
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS test_update_geom (
                        id TEXT PRIMARY KEY,
                        latitude FLOAT,
                        longitude FLOAT
                    )
                """)
                
                # Clear any existing data
                cursor.execute("DELETE FROM test_update_geom")
                
                # Insert test points
                cursor.execute("""
                    INSERT INTO test_update_geom (id, latitude, longitude)
                    VALUES (%s, %s, %s)
                """, ('point1', 30.0, 31.0))
                
                conn.commit()
        finally:
            conn.close()
        
        # Update geospatial columns
        result = self.db_manager.update_geospatial_columns(['test_update_geom'])
        assert result is True
        
        # Verify geom column was added and populated
        conn = psycopg2.connect(TEST_DB_URI)
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, latitude, longitude, 
                           ST_X(geom) AS geom_x, ST_Y(geom) AS geom_y 
                    FROM test_update_geom
                """)
                result = cursor.fetchone()
                
                # Verify geometry coordinates match the original lat/lon values
                assert result is not None
                assert result['id'] == 'point1'
                assert abs(result['geom_x'] - result['longitude']) < 0.0001
                assert abs(result['geom_y'] - result['latitude']) < 0.0001
                
                # Clean up
                cursor.execute("DROP TABLE test_update_geom")
                conn.commit()
        finally:
            conn.close()
    
    def teardown_class(self):
        """Clean up after all tests."""
        conn = psycopg2.connect(TEST_DB_URI)
        try:
            with conn.cursor() as cursor:
                # Drop test tables
                cursor.execute("DROP TABLE IF EXISTS test_locations")
                cursor.execute("DROP TABLE IF EXISTS test_update_geom")
                conn.commit()
        finally:
            conn.close()