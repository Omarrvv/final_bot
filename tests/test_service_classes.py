"""
Tests for the service classes.

This module contains tests for the service classes and the generic CRUD operations.
"""
import os
import pytest
from unittest.mock import MagicMock, patch

from src.knowledge.database import DatabaseManager
from src.services.base_service import BaseService
from src.services.attraction_service import AttractionService
from src.services.restaurant_service import RestaurantService
from src.services.service_registry import ServiceRegistry

class TestServiceClasses:
    """Test suite for service classes."""
    
    @pytest.fixture
    def mock_db_manager(self):
        """Create a mock database manager."""
        db_manager = MagicMock(spec=DatabaseManager)
        db_manager.VALID_TABLES = {'attractions', 'restaurants', 'accommodations', 'cities',
                                'regions', 'users', 'hotels', 'vector_search_metrics', 'vector_indexes',
                                'tourism_faqs', 'practical_info', 'events_festivals', 'tour_packages',
                                'itineraries', 'itinerary_types', 'itinerary_days'}
        return db_manager
    
    @pytest.fixture
    def service_registry(self, mock_db_manager):
        """Create a service registry."""
        return ServiceRegistry(mock_db_manager)
    
    def test_service_registry(self, service_registry, mock_db_manager):
        """Test the service registry."""
        # Get a service instance
        attraction_service = service_registry.get_service(AttractionService)
        
        # Verify that the service was created with the correct database manager
        assert attraction_service.db == mock_db_manager
        
        # Get the same service again and verify that it's the same instance
        attraction_service2 = service_registry.get_service(AttractionService)
        assert attraction_service is attraction_service2
        
        # Get a different service and verify that it's a different instance
        restaurant_service = service_registry.get_service(RestaurantService)
        assert attraction_service is not restaurant_service
        
        # Clear the registry and verify that new instances are created
        service_registry.clear()
        attraction_service3 = service_registry.get_service(AttractionService)
        assert attraction_service is not attraction_service3
    
    def test_base_service(self, mock_db_manager):
        """Test the base service."""
        # Create a base service
        base_service = BaseService(mock_db_manager)
        
        # Test _validate_table
        assert base_service._validate_table('attractions') is True
        assert base_service._validate_table('invalid_table') is False
        
        # Test _parse_json_field
        record = {'data': '{"key": "value"}'}
        base_service._parse_json_field(record, 'data')
        assert record['data'] == {'key': 'value'}
        
        # Test _handle_error
        result = base_service._handle_error('test_operation', Exception('test error'))
        assert result is None
        
        result = base_service._handle_error('test_operation', Exception('test error'), return_empty_list=True)
        assert result == []
    
    def test_attraction_service(self, mock_db_manager):
        """Test the attraction service."""
        # Create an attraction service
        attraction_service = AttractionService(mock_db_manager)
        
        # Configure the mock to return a test attraction
        test_attraction = {
            'id': 'test_attraction',
            'name': '{"en": "Test Attraction", "ar": "اختبار الجذب"}',
            'description': '{"en": "Test Description", "ar": "وصف الاختبار"}',
            'type_id': 'test_type',
            'city_id': 'test_city',
            'region_id': 'test_region',
            'latitude': 30.0,
            'longitude': 31.0,
            'data': '{"key": "value"}'
        }
        mock_db_manager.generic_get.return_value = test_attraction
        
        # Test get_attraction
        result = attraction_service.get_attraction('test_attraction')
        mock_db_manager.generic_get.assert_called_once_with(
            'attractions', 'test_attraction', attraction_service.jsonb_fields
        )
        assert result == test_attraction
        
        # Configure the mock to return a list of attractions
        test_attractions = [test_attraction]
        mock_db_manager.execute_postgres_query.return_value = test_attractions
        
        # Test search_attractions
        result = attraction_service.search_attractions(
            query='test',
            type_id='test_type',
            city_id='test_city',
            region_id='test_region'
        )
        assert mock_db_manager.execute_postgres_query.called
        assert result == test_attractions
    
    def test_restaurant_service(self, mock_db_manager):
        """Test the restaurant service."""
        # Create a restaurant service
        restaurant_service = RestaurantService(mock_db_manager)
        
        # Configure the mock to return a test restaurant
        test_restaurant = {
            'id': 'test_restaurant',
            'name': '{"en": "Test Restaurant", "ar": "اختبار المطعم"}',
            'description': '{"en": "Test Description", "ar": "وصف الاختبار"}',
            'cuisine_id': 'test_cuisine',
            'city_id': 'test_city',
            'region_id': 'test_region',
            'latitude': 30.0,
            'longitude': 31.0,
            'data': '{"key": "value"}'
        }
        mock_db_manager.generic_get.return_value = test_restaurant
        
        # Test get_restaurant
        result = restaurant_service.get_restaurant('test_restaurant')
        mock_db_manager.generic_get.assert_called_once_with(
            'restaurants', 'test_restaurant', restaurant_service.jsonb_fields
        )
        assert result == test_restaurant
        
        # Configure the mock to return a list of restaurants
        test_restaurants = [test_restaurant]
        mock_db_manager.execute_postgres_query.return_value = test_restaurants
        
        # Test search_restaurants
        result = restaurant_service.search_restaurants(
            query='test',
            cuisine_id='test_cuisine',
            city_id='test_city',
            region_id='test_region'
        )
        assert mock_db_manager.execute_postgres_query.called
        assert result == test_restaurants
    
    def test_generic_methods(self, mock_db_manager):
        """Test the generic methods."""
        # Create a base service
        base_service = BaseService(mock_db_manager)
        
        # Configure the mock to return a test record
        test_record = {
            'id': 'test_record',
            'name': '{"en": "Test Record", "ar": "اختبار السجل"}',
            'description': '{"en": "Test Description", "ar": "وصف الاختبار"}',
            'data': '{"key": "value"}'
        }
        mock_db_manager.execute_postgres_query.return_value = test_record
        
        # Test generic_get
        mock_db_manager.generic_get.return_value = test_record
        result = base_service.generic_get('attractions', 'test_record', ['name', 'description', 'data'])
        mock_db_manager.generic_get.assert_called_once_with(
            'attractions', 'test_record', ['name', 'description', 'data']
        )
        assert result == test_record
        
        # Configure the mock to return a list of records
        test_records = [test_record]
        mock_db_manager.generic_search.return_value = test_records
        
        # Test generic_search
        result = base_service.generic_search(
            'attractions',
            {'type_id': 'test_type'},
            10,
            0,
            ['name', 'description', 'data']
        )
        mock_db_manager.generic_search.assert_called_once_with(
            'attractions',
            {'type_id': 'test_type'},
            10,
            0,
            ['name', 'description', 'data'],
            'en'
        )
        assert result == test_records
        
        # Configure the mock to return a record ID
        mock_db_manager.generic_create.return_value = 'test_record'
        
        # Test generic_create
        result = base_service.generic_create('attractions', test_record)
        mock_db_manager.generic_create.assert_called_once_with('attractions', test_record)
        assert result == 'test_record'
        
        # Configure the mock to return True
        mock_db_manager.generic_update.return_value = True
        
        # Test generic_update
        result = base_service.generic_update('attractions', 'test_record', test_record)
        mock_db_manager.generic_update.assert_called_once_with('attractions', 'test_record', test_record)
        assert result is True
        
        # Configure the mock to return True
        mock_db_manager.generic_delete.return_value = True
        
        # Test generic_delete
        result = base_service.generic_delete('attractions', 'test_record')
        mock_db_manager.generic_delete.assert_called_once_with('attractions', 'test_record')
        assert result is True
