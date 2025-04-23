import pytest
from unittest.mock import MagicMock, patch
from typing import Optional, Dict

# Adjust import path as necessary
from src.knowledge.knowledge_base import KnowledgeBase
from src.knowledge.database import DatabaseManager

# Sample data similar to what DatabaseManager might return
SAMPLE_ATTRACTION_DATA = [
    {"id": "att_1", "name_en": "Pyramids", "city_id": "cai", "type": "historical"},
    {"id": "att_2", "name_en": "Khan el-Khalili", "city_id": "cai", "type": "shopping"}
]

SAMPLE_HOTEL_DATA = {
    "id": "hot_1", "name_en": "Nile Hotel", "city_id": "cai", "rating": 5
}

@pytest.fixture
def mock_db_manager():
    """Fixture for a mocked DatabaseManager."""
    mock = MagicMock(spec=DatabaseManager)
    # Default return values for common methods
    mock.search_attractions.return_value = []
    mock.search_hotels.return_value = []
    mock.search_restaurants.return_value = []
    mock.search_cities.return_value = []
    mock.get_attraction.return_value = None
    mock.get_accommodation.return_value = None
    mock.enhanced_search.return_value = []
    # Configure specific methods as needed in tests
    return mock

@pytest.fixture
def knowledge_base(mock_db_manager):
    """Fixture for KnowledgeBase instance with mocked DatabaseManager."""
    # We don't need a real factory if we mock the dependency directly
    kb = KnowledgeBase(db_manager=mock_db_manager)
    return kb

# --- KnowledgeBase Query Tests ---

def test_search_attractions_success(knowledge_base, mock_db_manager):
    """Test searching for attractions successfully."""
    # Method signature is: search_attractions(self, query: str = "", filters: Optional[Dict] = None, language: str = "en", limit: int = 10)
    filters = {"city_id": "cai", "type": "historical"}
    language = "en"
    limit = 10
    
    # Configure the mock to return attraction data
    mock_db_manager.search_attractions.return_value = SAMPLE_ATTRACTION_DATA[:1] # Return only pyramids

    # Call the method with the correct parameters
    results = knowledge_base.search_attractions(query="", filters=filters, language=language, limit=limit)

    # Verify the results
    assert len(results) == 1
    assert results[0]["id"] == "att_1"
    assert results[0]["type"] == "historical"
    mock_db_manager.search_attractions.assert_called_once()

def test_search_attractions_no_results(knowledge_base, mock_db_manager):
    """Test searching for attractions when none match."""
    filters = {"type": "beach"}
    mock_db_manager.search_attractions.return_value = [] # Simulate no results found

    results = knowledge_base.search_attractions(filters=filters)

    assert results == []
    mock_db_manager.search_attractions.assert_called_once()

def test_get_attraction_by_id_found(knowledge_base, mock_db_manager):
    """Test getting a specific attraction by ID when it exists."""
    attraction_id = "att_1"
    mock_db_manager.get_attraction.return_value = SAMPLE_ATTRACTION_DATA[0]

    result = knowledge_base.get_attraction_by_id(attraction_id)

    assert result is not None
    assert result["id"] == attraction_id
    assert result["name_en"] == "Pyramids"
    mock_db_manager.get_attraction.assert_called_once_with(attraction_id)

def test_get_attraction_by_id_not_found(knowledge_base, mock_db_manager):
    """Test getting an attraction by ID when it doesn't exist."""
    attraction_id = "non_existent"
    mock_db_manager.get_attraction.return_value = None # Simulate not found

    result = knowledge_base.get_attraction_by_id(attraction_id)

    assert result is None
    mock_db_manager.get_attraction.assert_called_once_with(attraction_id)

# --- Tests for other entity types (Hotels, Restaurants, etc.) ---

def test_get_hotel_by_id_found(knowledge_base, mock_db_manager):
    """Test getting a specific hotel by ID when it exists."""
    hotel_id = "hot_1"
    mock_db_manager.get_accommodation.return_value = SAMPLE_HOTEL_DATA

    result = knowledge_base.get_hotel_by_id(hotel_id)

    assert result is not None
    assert result["id"] == hotel_id
    assert result["name_en"] == "Nile Hotel"
    mock_db_manager.get_accommodation.assert_called_once_with(hotel_id)

def test_search_hotels_success(knowledge_base, mock_db_manager):
    """Test searching for hotels successfully."""
    # Method signature is: search_hotels(self, query: Dict = None, limit: int = 10, language: str = "en")
    query = {"city_id": "cai"}
    limit = 10
    language = "en"
    
    # Configure the mock to return data
    mock_db_manager.search_accommodations.return_value = [SAMPLE_HOTEL_DATA]

    # Call the method with the correct parameters
    results = knowledge_base.search_hotels(query=query, limit=limit, language=language)

    assert len(results) == 1
    assert results[0]["id"] == "hot_1"
    mock_db_manager.search_accommodations.assert_called_once()

# --- Test Practical Info --- #

def test_get_practical_info_success(knowledge_base, mock_db_manager):
    """Test retrieving practical information."""
    # Method signature is: get_practical_info(self, category: str, language: str = "en")
    category = "visa"
    language = "en"
    
    # Configure the mock to return data
    mock_db_manager.search_attractions.return_value = [{
        "name_en": "Visa Information", 
        "description_en": "Visa info...",
        "data": {"details": "Visa details", "tips": "Visa tips"}
    }]

    # Call the method with the correct parameters
    result = knowledge_base.get_practical_info(category, language)

    assert result is not None
    assert result["title"] == "Visa Information" 
    assert "description" in result
    mock_db_manager.search_attractions.assert_called_once()

# --- Test Lookup Location --- #

def test_lookup_location_found(knowledge_base, mock_db_manager):
    """Test looking up a location successfully."""
    location_name = "Cairo"
    language = "en"
    
    # Mock what the lookup_location method actually uses
    mock_db_manager.enhanced_search.return_value = [{
        "name_en": "Cairo",
        "city": "Cairo", 
        "region": "Cairo",
        "latitude": 30.0444,
        "longitude": 31.2357
    }]
    
    result = knowledge_base.lookup_location(location_name, language)

    assert result is not None
    assert result["name"] == "Cairo"
    assert "location" in result
    assert "latitude" in result["location"] 
    assert "longitude" in result["location"]
    mock_db_manager.enhanced_search.assert_called_once()


def test_lookup_location_not_found(knowledge_base, mock_db_manager):
    """Test looking up a location that doesn't exist."""
    location_name = "Atlantis"
    language = "en"
    
    # Configure mock to return no results
    mock_db_manager.enhanced_search.return_value = []

    result = knowledge_base.lookup_location(location_name, language)

    assert result is None
    mock_db_manager.enhanced_search.assert_called_once()


# Add tests for other search/get methods (e.g., restaurants, transportation)
# Add tests for error handling if KnowledgeBase catches exceptions from db_manager
# Add tests with different filter combinations, limits, offsets 