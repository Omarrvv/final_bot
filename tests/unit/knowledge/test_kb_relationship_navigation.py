"""
Tests for Knowledge Base entity relationships and navigation features.

These tests verify that the Knowledge Base properly maps entities and resolves relationships between them,
such as finding attractions near hotels or restaurants in a specific city.
"""
import pytest
from unittest.mock import MagicMock, patch
import json
from typing import Dict, List, Any

from src.knowledge.database import DatabaseManager
from src.knowledge.knowledge_base import KnowledgeBase

@pytest.fixture
def mock_db_manager():
    """Create a mock DatabaseManager for testing."""
    mock = MagicMock(spec=DatabaseManager)
    
    # Set up basic connection check
    mock.connect.return_value = True
    mock.db_type = "postgresql"
    
    # Set up empty default returns for search methods
    mock.search_attractions.return_value = []
    mock.search_restaurants.return_value = []
    mock.search_accommodations.return_value = []
    mock.search_cities.return_value = []
    mock.get_attraction.return_value = None
    mock.get_restaurant.return_value = None
    mock.get_accommodation.return_value = None
    mock.get_city.return_value = None
    mock.enhanced_search.return_value = []
    mock.find_nearby.return_value = []
    
    return mock

@pytest.fixture
def knowledge_base(mock_db_manager):
    """Create a KnowledgeBase instance with a mocked DatabaseManager."""
    return KnowledgeBase(db_manager=mock_db_manager)

@pytest.fixture
def mock_attraction_data():
    """Sample attraction data fixture."""
    return {
        "id": "pyramids_giza",
        "name_en": "Pyramids of Giza",
        "name_ar": "أهرامات الجيزة",
        "description_en": "The Great Pyramids of Giza are ancient Egyptian pyramids.",
        "description_ar": "أهرامات الجيزة هي أهرامات مصرية قديمة",
        "city": "Cairo",
        "region": "Giza",
        "type": "historical",
        "latitude": 29.9792,
        "longitude": 31.1342,
        "data": json.dumps({
            "entrance_fee": "200 EGP",
            "opening_hours": "8:00 AM - 5:00 PM"
        })
    }

@pytest.fixture
def mock_restaurant_data():
    """Sample restaurant data fixture."""
    return {
        "id": "abou_el_sid",
        "name_en": "Abou El Sid",
        "name_ar": "أبو السيد",
        "description_en": "Traditional Egyptian cuisine restaurant",
        "description_ar": "مطعم للمأكولات المصرية التقليدية",
        "city": "Cairo",
        "region": "Zamalek",
        "type": "Egyptian",
        "latitude": 30.0571,
        "longitude": 31.2272,
        "data": json.dumps({
            "price_range": "moderate",
            "popular_dishes": ["molokheya", "koshary"]
        })
    }

@pytest.fixture
def mock_hotel_data():
    """Sample hotel/accommodation data fixture."""
    return {
        "id": "mena_house",
        "name_en": "Mena House Hotel",
        "name_ar": "فندق مينا هاوس",
        "description_en": "Luxury hotel with pyramid views",
        "description_ar": "فندق فاخر مع إطلالات على الأهرامات",
        "city": "Cairo",
        "region": "Giza",
        "type": "luxury",
        "stars": 5,
        "latitude": 29.9851,
        "longitude": 31.1376,
        "data": json.dumps({
            "amenities": ["pool", "spa", "restaurant"],
            "price_range": "high"
        })
    }

@pytest.fixture
def mock_city_data():
    """Sample city data fixture."""
    return {
        "id": "cairo",
        "name_en": "Cairo",
        "name_ar": "القاهرة",
        "description_en": "Capital city of Egypt",
        "description_ar": "عاصمة مصر",
        "region": "Greater Cairo",
        "latitude": 30.0444,
        "longitude": 31.2357,
        "data": json.dumps({
            "population": 20000000,
            "known_for": ["pyramids", "museums", "nile"]
        })
    }

def test_format_attraction_data(knowledge_base, mock_attraction_data):
    """Test that attraction data is properly formatted."""
    # Call the formatter
    result = knowledge_base._format_attraction_data(mock_attraction_data)
    
    # Verify the structure of the returned data
    assert result["id"] == mock_attraction_data["id"]
    assert result["name"]["en"] == mock_attraction_data["name_en"]
    assert result["name"]["ar"] == mock_attraction_data["name_ar"]
    assert result["description"]["en"] == mock_attraction_data["description_en"]
    assert result["description"]["ar"] == mock_attraction_data["description_ar"]
    assert result["city"] == mock_attraction_data["city"]
    assert result["region"] == mock_attraction_data["region"]
    assert result["type"] == mock_attraction_data["type"]
    assert result["latitude"] == mock_attraction_data["latitude"]
    assert result["longitude"] == mock_attraction_data["longitude"]
    assert "additional_data" in result
    assert result["additional_data"]["entrance_fee"] == "200 EGP"
    assert result["source"] == "database"

def test_format_restaurant_data(knowledge_base, mock_restaurant_data):
    """Test that restaurant data is properly formatted."""
    # Call the formatter
    result = knowledge_base._format_restaurant_data(mock_restaurant_data)
    
    # Verify the structure of the returned data
    assert result["id"] == mock_restaurant_data["id"]
    assert result["name"]["en"] == mock_restaurant_data["name_en"]
    assert result["name"]["ar"] == mock_restaurant_data["name_ar"]
    assert result["description"]["en"] == mock_restaurant_data["description_en"]
    assert result["description"]["ar"] == mock_restaurant_data["description_ar"]
    assert result["city"] == mock_restaurant_data["city"]
    assert result["region"] == mock_restaurant_data["region"]
    assert result["cuisine_type"] == mock_restaurant_data["type"]
    assert result["latitude"] == mock_restaurant_data["latitude"]
    assert result["longitude"] == mock_restaurant_data["longitude"]
    assert "additional_data" in result
    assert result["additional_data"]["price_range"] == "moderate"
    assert result["source"] == "database"

def test_format_accommodation_data(knowledge_base, mock_hotel_data):
    """Test that hotel/accommodation data is properly formatted."""
    # Call the formatter
    result = knowledge_base._format_accommodation_data(mock_hotel_data)
    
    # Verify the structure of the returned data
    assert result["id"] == mock_hotel_data["id"]
    assert result["name"]["en"] == mock_hotel_data["name_en"]
    assert result["name"]["ar"] == mock_hotel_data["name_ar"]
    assert result["description"]["en"] == mock_hotel_data["description_en"]
    assert result["description"]["ar"] == mock_hotel_data["description_ar"]
    assert result["city"] == mock_hotel_data["city"]
    assert result["region"] == mock_hotel_data["region"]
    assert result["accommodation_type"] == mock_hotel_data["type"]
    assert result["stars"] == mock_hotel_data["stars"]
    assert result["latitude"] == mock_hotel_data["latitude"]
    assert result["longitude"] == mock_hotel_data["longitude"]
    assert "additional_data" in result
    assert "amenities" in result["additional_data"]
    assert result["source"] == "database"

def test_format_city_data(knowledge_base, mock_city_data):
    """Test that city data is properly formatted."""
    # Call the formatter
    result = knowledge_base._format_city_data(mock_city_data)
    
    # Verify the structure of the returned data
    assert result["name"]["en"] == mock_city_data["name_en"]
    assert result["name"]["ar"] == mock_city_data["name_ar"]
    assert result["city"] == mock_city_data["id"]
    assert result["region"] == mock_city_data["region"]
    assert result["location"]["latitude"] == mock_city_data["latitude"]
    assert result["location"]["longitude"] == mock_city_data["longitude"]
    assert "data" in result
    assert result["data"]["population"] == 20000000

def test_find_nearby_attractions(knowledge_base, mock_db_manager, mock_attraction_data):
    """Test finding nearby attractions by coordinates."""
    # Set up mock to return sample attractions
    mock_db_manager.find_nearby.return_value = [mock_attraction_data]
    
    # Call the method being tested
    results = knowledge_base.find_nearby_attractions(
        latitude=30.0444, 
        longitude=31.2357,
        radius_km=5.0,
        limit=10
    )
    
    # Verify the correct method was called with right params
    mock_db_manager.find_nearby.assert_called_once_with(
        table="attractions",
        latitude=30.0444,
        longitude=31.2357,
        radius_km=5.0,
        limit=10
    )
    
    # Verify results formatting
    assert len(results) == 1
    assert results[0]["id"] == mock_attraction_data["id"]
    assert results[0]["name"]["en"] == mock_attraction_data["name_en"]

def test_find_nearby_restaurants(knowledge_base, mock_db_manager, mock_restaurant_data):
    """Test finding nearby restaurants by coordinates."""
    # Set up mock to return sample restaurants
    mock_db_manager.find_nearby.return_value = [mock_restaurant_data]
    
    # Call the method being tested
    results = knowledge_base.find_nearby_restaurants(
        latitude=30.0444, 
        longitude=31.2357,
        radius_km=2.0,
        limit=5
    )
    
    # Verify the correct method was called with right params
    mock_db_manager.find_nearby.assert_called_once_with(
        table="restaurants",
        latitude=30.0444,
        longitude=31.2357,
        radius_km=2.0,
        limit=5
    )
    
    # Verify results formatting
    assert len(results) == 1
    assert results[0]["id"] == mock_restaurant_data["id"]
    assert results[0]["name"]["en"] == mock_restaurant_data["name_en"]

def test_find_nearby_accommodations(knowledge_base, mock_db_manager, mock_hotel_data):
    """Test finding nearby accommodations by coordinates."""
    # Set up mock to return sample hotels
    mock_db_manager.find_nearby.return_value = [mock_hotel_data]
    
    # Call the method being tested
    results = knowledge_base.find_nearby_accommodations(
        latitude=30.0444, 
        longitude=31.2357,
        radius_km=3.0,
        limit=10
    )
    
    # Verify the correct method was called with right params
    mock_db_manager.find_nearby.assert_called_once_with(
        table="accommodations",
        latitude=30.0444,
        longitude=31.2357,
        radius_km=3.0,
        limit=10
    )
    
    # Verify results formatting
    assert len(results) == 1
    assert results[0]["id"] == mock_hotel_data["id"]
    assert results[0]["name"]["en"] == mock_hotel_data["name_en"]

def test_get_attractions_in_city(knowledge_base, mock_db_manager, mock_attraction_data, mock_city_data):
    """Test getting attractions within a specific city."""
    # Set up mocks
    mock_db_manager.search_cities.return_value = [mock_city_data]
    mock_db_manager.search_attractions.return_value = [mock_attraction_data]
    
    # Call the method being tested
    results = knowledge_base.get_attractions_in_city(city_name="Cairo", limit=10)
    
    # Verify city search was called
    mock_db_manager.search_cities.assert_called_once()
    
    # Verify attractions search was called with city filter
    mock_db_manager.search_attractions.assert_called_once()
    call_args = mock_db_manager.search_attractions.call_args[1]
    assert call_args["query"]["city"] == "cairo"
    
    # Verify results formatting
    assert len(results) == 1
    assert results[0]["id"] == mock_attraction_data["id"]
    assert results[0]["name"]["en"] == mock_attraction_data["name_en"]

def test_find_attractions_near_hotel(knowledge_base, mock_db_manager, mock_hotel_data, mock_attraction_data):
    """Test finding attractions near a hotel."""
    # Set up mocks
    mock_db_manager.get_accommodation.return_value = mock_hotel_data
    mock_db_manager.find_nearby.return_value = [mock_attraction_data]
    
    # Call the method being tested
    results = knowledge_base.find_attractions_near_hotel(
        hotel_id="mena_house",
        radius_km=2.0,
        limit=5
    )
    
    # Verify hotel query was called
    mock_db_manager.get_accommodation.assert_called_once_with("mena_house")
    
    # Verify nearby search was called with hotel coordinates
    mock_db_manager.find_nearby.assert_called_once()
    call_args = mock_db_manager.find_nearby.call_args[1]
    assert call_args["latitude"] == mock_hotel_data["latitude"]
    assert call_args["longitude"] == mock_hotel_data["longitude"]
    
    # Verify results formatting
    assert len(results) == 1
    assert results[0]["id"] == mock_attraction_data["id"]
    assert results[0]["name"]["en"] == mock_attraction_data["name_en"]

def test_find_restaurants_near_attraction(knowledge_base, mock_db_manager, mock_attraction_data, mock_restaurant_data):
    """Test finding restaurants near an attraction."""
    # Set up mocks
    mock_db_manager.get_attraction.return_value = mock_attraction_data
    mock_db_manager.find_nearby.return_value = [mock_restaurant_data]
    
    # Call the method being tested
    results = knowledge_base.find_restaurants_near_attraction(
        attraction_id="pyramids_giza",
        radius_km=1.0,
        limit=10
    )
    
    # Verify attraction query was called
    mock_db_manager.get_attraction.assert_called_once_with("pyramids_giza")
    
    # Verify nearby search was called with attraction coordinates
    mock_db_manager.find_nearby.assert_called_once()
    call_args = mock_db_manager.find_nearby.call_args[1]
    assert call_args["latitude"] == mock_attraction_data["latitude"]
    assert call_args["longitude"] == mock_attraction_data["longitude"]
    
    # Verify results formatting
    assert len(results) == 1
    assert results[0]["id"] == mock_restaurant_data["id"]
    assert results[0]["name"]["en"] == mock_restaurant_data["name_en"]

def test_get_restaurants_in_city(knowledge_base, mock_db_manager, mock_restaurant_data, mock_city_data):
    """Test getting restaurants within a specific city."""
    # Set up mocks
    mock_db_manager.search_cities.return_value = [mock_city_data]
    mock_db_manager.search_restaurants.return_value = [mock_restaurant_data]
    
    # Call the method being tested
    results = knowledge_base.get_restaurants_in_city(city_name="Cairo", limit=10)
    
    # Verify city search was called
    mock_db_manager.search_cities.assert_called_once()
    
    # Verify restaurants search was called with city filter
    mock_db_manager.search_restaurants.assert_called_once()
    call_args = mock_db_manager.search_restaurants.call_args[1]
    assert call_args["query"]["city"] == "cairo"
    
    # Verify results formatting
    assert len(results) == 1
    assert results[0]["id"] == mock_restaurant_data["id"]
    assert results[0]["name"]["en"] == mock_restaurant_data["name_en"]

def test_get_accommodations_in_city(knowledge_base, mock_db_manager, mock_hotel_data, mock_city_data):
    """Test getting accommodations within a specific city."""
    # Set up mocks
    mock_db_manager.search_cities.return_value = [mock_city_data]
    mock_db_manager.search_accommodations.return_value = [mock_hotel_data]
    
    # Call the method being tested
    results = knowledge_base.get_accommodations_in_city(city_name="Cairo", limit=10)
    
    # Verify city search was called
    mock_db_manager.search_cities.assert_called_once()
    
    # Verify accommodations search was called with city filter
    mock_db_manager.search_accommodations.assert_called_once()
    call_args = mock_db_manager.search_accommodations.call_args[1]
    assert call_args["query"]["city"] == "cairo"
    
    # Verify results formatting
    assert len(results) == 1
    assert results[0]["id"] == mock_hotel_data["id"]
    assert results[0]["name"]["en"] == mock_hotel_data["name_en"]

def test_entity_mapping_with_missing_data(knowledge_base):
    """Test entity formatters with incomplete data."""
    # Test attraction formatter with minimal data
    minimal_attraction = {"id": "test_attr", "name_en": "Test Attraction"}
    formatted_attr = knowledge_base._format_attraction_data(minimal_attraction)
    assert formatted_attr["id"] == "test_attr"
    assert formatted_attr["name"]["en"] == "Test Attraction"
    assert formatted_attr["name"]["ar"] == ""
    
    # Test restaurant formatter with minimal data
    minimal_restaurant = {"id": "test_rest", "name_en": "Test Restaurant"}
    formatted_rest = knowledge_base._format_restaurant_data(minimal_restaurant)
    assert formatted_rest["id"] == "test_rest"
    assert formatted_rest["name"]["en"] == "Test Restaurant"
    assert formatted_rest["name"]["ar"] == ""
    
    # Test hotel formatter with minimal data
    minimal_hotel = {"id": "test_hotel", "name_en": "Test Hotel"}
    formatted_hotel = knowledge_base._format_accommodation_data(minimal_hotel)
    assert formatted_hotel["id"] == "test_hotel"
    assert formatted_hotel["name"]["en"] == "Test Hotel"
    assert formatted_hotel["name"]["ar"] == ""

def test_error_handling_in_relationship_navigation(knowledge_base, mock_db_manager):
    """Test error handling in relationship navigation methods."""
    # Set up mock to raise exception
    mock_db_manager.find_nearby.side_effect = Exception("Database error")
    
    # Test error handling in find_nearby_attractions
    results = knowledge_base.find_nearby_attractions(latitude=0, longitude=0)
    assert results == []
    
    # Test error handling in find_attractions_near_hotel
    mock_db_manager.get_accommodation.return_value = {"id": "test", "latitude": 0, "longitude": 0}
    results = knowledge_base.find_attractions_near_hotel(hotel_id="test")
    assert results == []
    
    # Test error handling with invalid coordinates
    mock_db_manager.get_accommodation.return_value = {"id": "test", "latitude": 0, "longitude": 0}
    results = knowledge_base.find_attractions_near_hotel(hotel_id="test")
    assert results == []
    
    # Test error handling with missing entity
    mock_db_manager.get_attraction.return_value = None
    results = knowledge_base.find_restaurants_near_attraction(attraction_id="nonexistent")
    assert results == []