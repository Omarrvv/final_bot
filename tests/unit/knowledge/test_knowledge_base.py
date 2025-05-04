import pytest
from unittest.mock import MagicMock, patch
import json
import numpy as np
from src.knowledge.knowledge_base import KnowledgeBase

@pytest.fixture
def mock_db_manager():
    db_manager = MagicMock()
    return db_manager

def test_init_requires_db_manager():
    """Test that KnowledgeBase requires a DatabaseManager."""
    with pytest.raises(ValueError):
        KnowledgeBase(db_manager=None)

def test_get_attraction_by_id(mock_db_manager):
    """Test retrieving an attraction by ID."""
    # Setup test data
    mock_attraction = {
        "id": "pyr1",
        "name_en": "Great Pyramid of Giza",
        "name_ar": "هرم خوفو",
        "description_en": "Ancient Egyptian pyramid"
    }
    mock_db_manager.get_attraction.return_value = mock_attraction

    # Initialize KnowledgeBase
    kb = KnowledgeBase(db_manager=mock_db_manager)

    # Call method
    result = kb.get_attraction_by_id("pyr1")

    # Verify correct DB call
    mock_db_manager.get_attraction.assert_called_once_with("pyr1")

    # Verify result
    assert result == mock_attraction

def test_get_attraction_not_found(mock_db_manager):
    """Test retrieving a non-existent attraction."""
    # Setup mock to return None
    mock_db_manager.get_attraction.return_value = None

    # Initialize KnowledgeBase
    kb = KnowledgeBase(db_manager=mock_db_manager)

    # Call method
    result = kb.get_attraction_by_id("nonexistent")

    # Verify correct DB call
    mock_db_manager.get_attraction.assert_called_once_with("nonexistent")

    # Verify result is None
    assert result is None

def test_search_attractions_text_query(mock_db_manager):
    """Test searching attractions with a text query."""
    # Setup test data
    mock_results = [
        {"id": "pyr1", "name_en": "Great Pyramid of Giza", "name_ar": "هرم خوفو"},
        {"id": "sph1", "name_en": "Sphinx of Giza", "name_ar": "أبو الهول"}
    ]
    mock_db_manager.enhanced_search.return_value = mock_results

    # Initialize KnowledgeBase
    kb = KnowledgeBase(db_manager=mock_db_manager)

    # Call method with text query
    result = kb.search_attractions(query="pyramid", limit=5)

    # Verify correct DB call
    mock_db_manager.enhanced_search.assert_called_once()
    args = mock_db_manager.enhanced_search.call_args[1]
    assert args["table"] == "attractions"
    assert args["search_text"] == "pyramid"
    assert args["limit"] == 5

    # Verify result
    assert result == mock_results

def test_search_attractions_structured_query(mock_db_manager):
    """Test searching attractions with a structured query."""
    # Setup test data
    mock_results = [
        {"id": "pyr1", "name_en": "Great Pyramid of Giza", "name_ar": "هرم خوفو", "city": "Cairo"}
    ]
    mock_db_manager.search_attractions.return_value = mock_results

    # Initialize KnowledgeBase
    kb = KnowledgeBase(db_manager=mock_db_manager)

    # Call method with structured query
    query = {"city": "Cairo"}
    result = kb.search_attractions(query=query, limit=5)

    # Verify correct DB call
    mock_db_manager.search_attractions.assert_called_once()
    args = mock_db_manager.search_attractions.call_args[1]
    assert args["query"] == query
    assert args["limit"] == 5

    # Verify result
    assert result == mock_results

def test_search_attractions_error_handling(mock_db_manager):
    """Test error handling in search_attractions."""
    # Setup mock to raise exception
    mock_db_manager.enhanced_search.side_effect = Exception("Database error")

    # Initialize KnowledgeBase
    kb = KnowledgeBase(db_manager=mock_db_manager)

    # Call method
    result = kb.search_attractions(query="pyramid")

    # Verify error is handled and empty list returned
    assert result == []

def test_lookup_location(mock_db_manager):
    """Test location lookup functionality."""
    # Setup test data
    mock_results = [
        {
            "id": "cairo_location",
            "name_en": "Cairo",
            "name_ar": "القاهرة",
            "city": "Cairo",
            "region": "Cairo",
            "latitude": 30.0444,
            "longitude": 31.2357
        }
    ]
    mock_db_manager.enhanced_search.return_value = mock_results

    # Initialize KnowledgeBase
    kb = KnowledgeBase(db_manager=mock_db_manager)

    # Call method
    result = kb.lookup_location("Cairo", language="en")

    # Verify DB call
    mock_db_manager.enhanced_search.assert_called_once()
    args = mock_db_manager.enhanced_search.call_args[1]
    assert "table" in args
    assert args["table"] == "cities"

    # Verify result format
    assert result is not None
    assert "name" in result
    assert "name_en" in result
    assert "region" in result
    assert "location" in result
    assert "latitude" in result["location"]
    assert "longitude" in result["location"]

def test_lookup_location_not_found(mock_db_manager):
    """Test location lookup when location not found."""
    # Setup mock to return empty results for both enhanced_search and get_city
    mock_db_manager.enhanced_search.return_value = []
    mock_db_manager.get_city.return_value = None

    # Initialize KnowledgeBase
    kb = KnowledgeBase(db_manager=mock_db_manager)

    # Call method
    result = kb.lookup_location("NonexistentLocation")

    # Verify result is None
    assert result is None

def test_lookup_location_error_handling(mock_db_manager):
    """Test error handling in lookup_location."""
    # Setup mock to raise exception
    mock_db_manager.enhanced_search.side_effect = Exception("Database error")
    # Initialize KnowledgeBase
    kb = KnowledgeBase(db_manager=mock_db_manager)
    # Call method
    result = kb.lookup_location("Cairo")
    # Verify error is handled and None returned
    assert result is None

def test_get_restaurant_by_id(mock_db_manager):
    """Test retrieving a restaurant by ID."""
    # Setup test data
    mock_restaurant = {
        "id": "rest1",
        "name_en": "Khan El Khalili Restaurant",
        "name_ar": "مطعم خان الخليلي",
        "city": "Cairo",
        "cuisine": "Egyptian"
    }
    mock_db_manager.get_restaurant.return_value = mock_restaurant

    # Initialize KnowledgeBase
    kb = KnowledgeBase(db_manager=mock_db_manager)

    # Call method
    result = kb.get_restaurant_by_id("rest1")

    # Verify correct DB call
    mock_db_manager.get_restaurant.assert_called_once_with("rest1")

    # Verify result
    assert result == mock_restaurant

def test_get_restaurant_not_found(mock_db_manager):
    """Test retrieving a non-existent restaurant."""
    # Setup mock to return None
    mock_db_manager.get_restaurant.return_value = None

    # Initialize KnowledgeBase
    kb = KnowledgeBase(db_manager=mock_db_manager)

    # Call method
    result = kb.get_restaurant_by_id("nonexistent")

    # Verify result is None
    assert result is None

def test_search_restaurants(mock_db_manager):
    """Test searching restaurants."""
    # Setup test data
    mock_results = [
        {"id": "rest1", "name_en": "Khan El Khalili Restaurant"},
        {"id": "rest2", "name_en": "Nile View Restaurant"}
    ]
    mock_db_manager.enhanced_search.return_value = mock_results

    # Initialize KnowledgeBase
    kb = KnowledgeBase(db_manager=mock_db_manager)

    # Call method with text query
    result = kb.search_restaurants(query="restaurant", limit=5)

    # Verify correct DB call
    mock_db_manager.enhanced_search.assert_called_once()
    args = mock_db_manager.enhanced_search.call_args[1]
    assert args["table"] == "restaurants"
    assert args["search_text"] == "restaurant"
    assert args["limit"] == 5

    # Verify result
    assert result == mock_results

def test_search_restaurants_with_dict_query(mock_db_manager):
    """Test searching restaurants with a dictionary query."""
    # Setup test data
    mock_results = [
        {"id": "rest1", "name_en": "Khan El Khalili Restaurant", "city": "Cairo"}
    ]
    mock_db_manager.search_restaurants.return_value = mock_results

    # Initialize KnowledgeBase
    kb = KnowledgeBase(db_manager=mock_db_manager)

    # Call method with structured query
    query = {"city": "Cairo"}
    result = kb.search_restaurants(query=query, limit=5)

    # Verify correct DB call
    mock_db_manager.search_restaurants.assert_called_once()
    args = mock_db_manager.search_restaurants.call_args[1]
    assert args["filters"] == query
    assert args["limit"] == 5

    # Verify result
    assert result == mock_results

def test_get_hotel_by_id(mock_db_manager):
    """Test retrieving a hotel by ID."""
    # Setup test data
    mock_hotel = {
        "id": "hotel1",
        "name_en": "Marriott Mena House",
        "city": "Cairo",
        "stars": 5
    }
    mock_db_manager.get_accommodation.return_value = mock_hotel

    # Initialize KnowledgeBase
    kb = KnowledgeBase(db_manager=mock_db_manager)

    # Call method
    result = kb.get_hotel_by_id("hotel1")

    # Verify correct DB call
    mock_db_manager.get_accommodation.assert_called_once_with("hotel1")

    # Verify result
    assert result == mock_hotel

def test_search_hotels(mock_db_manager):
    """Test searching hotels."""
    # Setup test data
    mock_results = [
        {"id": "hotel1", "name_en": "Marriott Mena House", "stars": 5},
        {"id": "hotel2", "name_en": "Sofitel Nile El Gezirah", "stars": 5}
    ]
    mock_db_manager.enhanced_search.return_value = mock_results

    # Initialize KnowledgeBase
    kb = KnowledgeBase(db_manager=mock_db_manager)

    # Call method with text query
    result = kb.search_hotels(query="luxury", limit=5)

    # Verify correct DB call
    mock_db_manager.enhanced_search.assert_called_once()
    args = mock_db_manager.enhanced_search.call_args[1]
    assert args["table"] == "accommodations"
    assert args["search_text"] == "luxury"
    assert args["limit"] == 5

    # Verify result
    assert result == mock_results

def test_get_practical_info(mock_db_manager):
    """Test retrieving practical information."""
    # Setup test data with PostgreSQL-style JSONB format
    mock_attraction = {
        "name_en": "Visa Information",
        "description_en": "Tourist visas are required for most visitors.",
        "name_ar": "معلومات التأشيرة",
        "description_ar": "تأشيرات السياحة مطلوبة لمعظم الزوار.",
        "data": json.dumps({
            "details": "Available at airport and online",
            "tips": "Apply at least 2 weeks before travel"
        })
    }

    # Mock the database call
    mock_db_manager.search_attractions.return_value = [mock_attraction]

    # Initialize KnowledgeBase
    kb = KnowledgeBase(db_manager=mock_db_manager)

    # Test getting practical info in English
    result = kb.get_practical_info(category="visa", language="en")

    # Verify the database was called with the right parameters
    mock_db_manager.search_attractions.assert_called_with(filters={"type": "visa"}, limit=1)

    # Verify results
    assert result is not None
    assert result["title"] == "Visa Information"
    assert result["description"] == "Tourist visas are required for most visitors."
    assert result["category"] == "visa"
    assert result["source"] == "database"
    assert result["details"] == "Available at airport and online"
    assert result["tips"] == "Apply at least 2 weeks before travel"

    # Test with Arabic language
    mock_db_manager.search_attractions.reset_mock()
    result_ar = kb.get_practical_info(category="visa", language="ar")

    # Verify result has Arabic content
    assert result_ar["title"] == "معلومات التأشيرة"
    assert result_ar["description"] == "تأشيرات السياحة مطلوبة لمعظم الزوار."

    # Test with no results
    mock_db_manager.search_attractions.return_value = []
    result_none = kb.get_practical_info(category="nonexistent", language="en")
    assert result_none is None

    # Test with exception handling
    mock_db_manager.search_attractions.side_effect = Exception("Database error")
    result_error = kb.get_practical_info(category="visa", language="en")
    assert result_error is None

# ----- PostgreSQL Specific Tests -----

def test_search_with_jsonb_filters(mock_db_manager):
    """Test searching with PostgreSQL JSONB filters."""
    # Setup test data
    mock_results = [
        {
            "id": "hotel1",
            "name_en": "Luxury Hotel",
            "data": json.dumps({"amenities": ["pool", "spa", "restaurant"]})
        },
        {
            "id": "hotel2",
            "name_en": "Resort Hotel",
            "data": json.dumps({"amenities": ["pool", "beach", "kids club"]})
        }
    ]
    mock_db_manager.search_accommodations.return_value = mock_results

    # Initialize KnowledgeBase
    kb = KnowledgeBase(db_manager=mock_db_manager)

    # Call method with JSONB filter
    query = {"data": {"$jsonb_contains": {"amenities": ["pool"]}}}
    result = kb.search_hotels(query=query)

    # Verify correct DB call with JSONB filter
    mock_db_manager.search_accommodations.assert_called_once()
    args = mock_db_manager.search_accommodations.call_args[1]
    assert args["filters"] == query

    # Verify result
    assert result == mock_results

def test_vector_search_integration(mock_db_manager):
    """Test vector search integration with Knowledge Base."""
    # Create mock vector embedding
    mock_embedding = [0.1] * 1536  # 1536-dimensional vector

    # Setup mock results for vector search
    mock_results = [
        {"id": "attr1", "name_en": "Great Pyramid", "similarity": 0.95},
        {"id": "attr2", "name_en": "Sphinx", "similarity": 0.85},
    ]

    # Mock text_to_embedding and vector_search methods
    mock_db_manager.text_to_embedding.return_value = mock_embedding
    mock_db_manager.vector_search.return_value = mock_results

    # Initialize KnowledgeBase
    kb = KnowledgeBase(db_manager=mock_db_manager)

    # Call semantic search method
    results = kb.semantic_search("ancient pyramids", "attractions", limit=5)

    # Verify embedding conversion was called
    mock_db_manager.text_to_embedding.assert_called_once_with("ancient pyramids")

    # Verify vector search was called with correct parameters
    mock_db_manager.vector_search.assert_called_once()
    args = mock_db_manager.vector_search.call_args[1]
    assert args["table_name"] == "attractions"
    assert args["embedding"] == mock_embedding
    assert args["limit"] == 5

    # Verify results
    assert results == mock_results

def test_hybrid_search(mock_db_manager):
    """Test hybrid search combining vector and keyword search."""
    # Mock vector search results
    mock_vector_results = [
        {"id": "attr1", "name_en": "Great Pyramid", "similarity": 0.95},
        {"id": "attr3", "name_en": "Valley of the Kings", "similarity": 0.75},
    ]

    # Mock keyword search results
    mock_keyword_results = [
        {"id": "attr1", "name_en": "Great Pyramid"},
        {"id": "attr2", "name_en": "Pyramid of Khafre"},
    ]

    # Setup mocks
    mock_db_manager.text_to_embedding.return_value = [0.1] * 1536
    mock_db_manager.vector_search.return_value = mock_vector_results
    mock_db_manager.enhanced_search.return_value = mock_keyword_results

    # Initialize KnowledgeBase
    kb = KnowledgeBase(db_manager=mock_db_manager)

    # Call hybrid search method (if implemented)
    results = kb.hybrid_search("pyramid ancient egypt", "attractions", limit=5)

    # Verify both search methods were called
    mock_db_manager.vector_search.assert_called_once()
    mock_db_manager.enhanced_search.assert_called_once()

    # Verify results contain items from both searches, with vector search prioritized
    assert len(results) >= 1
    assert any(r["id"] == "attr1" for r in results)

    # Check if attr1 (common in both results) is prioritized
    if hasattr(kb, 'rerank_results'):
        # First result should be the one found in both searches
        assert results[0]["id"] == "attr1"

def test_nearby_attractions_search(mock_db_manager):
    """Test searching for attractions near a location."""
    # Mock nearby attractions
    mock_results = [
        {
            "id": "attr1",
            "name_en": "Pyramid of Khufu",
            "city": "Giza",
            "distance_km": 1.2
        },
        {
            "id": "attr2",
            "name_en": "Sphinx",
            "city": "Giza",
            "distance_km": 1.5
        }
    ]

    # Setup mock
    mock_db_manager.find_nearby.return_value = mock_results

    # Initialize KnowledgeBase
    kb = KnowledgeBase(db_manager=mock_db_manager)

    # Call method to find nearby attractions
    results = kb.find_nearby_attractions(29.9792, 31.1342, radius_km=5)

    # Verify correct DB call
    mock_db_manager.find_nearby.assert_called_once()
    args = mock_db_manager.find_nearby.call_args[1]
    assert args["table"] == "attractions"
    assert args["latitude"] == 29.9792
    assert args["longitude"] == 31.1342
    assert args["radius_km"] == 5

    # Verify results
    assert results == mock_results
