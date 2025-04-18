import pytest
from unittest.mock import Mock, patch, call

# Assuming KnowledgeBase is importable from its location
# Adjust the import path as necessary based on your project structure and PYTHONPATH
from src.knowledge.knowledge_base import KnowledgeBase
# We don't strictly need to import DatabaseManager if we're only mocking it

@pytest.fixture
def mock_db_manager():
    """Provides a mocked DatabaseManager instance."""
    # Create a mock object that behaves like DatabaseManager
    # We can configure specific methods later in the tests
    manager = Mock() 
    # Add specific methods that KnowledgeBase expects to call
    manager.get_attraction = Mock()
    manager.search_attractions = Mock()
    manager.get_restaurant = Mock()
    manager.search_restaurants = Mock()
    manager.get_accommodation = Mock()
    manager.search_accommodations = Mock()
    return manager

@pytest.fixture
def knowledge_base(mock_db_manager):
    """Provides a KnowledgeBase instance initialized with the mocked DB manager."""
    # Pass the mock manager during initialization
    kb = KnowledgeBase(db_manager=mock_db_manager)
    return kb

# --- Test Cases ---

def test_kb_initialization(mock_db_manager):
    """Test that KnowledgeBase initializes correctly with a db_manager."""
    kb = KnowledgeBase(db_manager=mock_db_manager)
    assert kb.db_manager is mock_db_manager

def test_get_attraction_by_id_calls_db_manager(knowledge_base, mock_db_manager):
    """Test get_attraction_by_id delegates the call to db_manager.get_attraction."""
    attraction_id = "attr_123"
    expected_result = {"id": attraction_id, "name_en": "Test Temple"}
    
    # Configure the mock method to return a specific value when called
    mock_db_manager.get_attraction.return_value = expected_result
    
    # Call the method on the KnowledgeBase instance
    result = knowledge_base.get_attraction_by_id(attraction_id)
    
    # Assert that the mock db_manager's method was called exactly once with the correct ID
    mock_db_manager.get_attraction.assert_called_once_with(attraction_id)
    
    # Assert that the result returned by KnowledgeBase is the one from the mock
    assert result == expected_result

def test_search_attractions_calls_db_manager(knowledge_base, mock_db_manager):
    """Test search_attractions delegates the call to db_manager.search_attractions."""
    query = "pyramids"
    filters = {"region": "Giza"}
    language = "en"
    limit = 5
    expected_results = [{"id": "giza_pyr", "name_en": "Giza Pyramids"}]
    
    # Configure the mock method
    mock_db_manager.search_attractions.return_value = expected_results
    
    # Call the KnowledgeBase method
    results = knowledge_base.search_attractions(query=query, filters=filters, language=language, limit=limit)
    
    # Prepare the expected query structure that KnowledgeBase should pass to db_manager
    # (Based on the logic currently in KnowledgeBase.search_attractions)
    search_term = f'%{query}%'
    expected_db_query = {
        '$and': [
            {'$or': [
                {'name_en': {'$like': search_term}},
                {'description_en': {'$like': search_term}}
            ]},
            {'region': {'$eq': 'Giza'}}
        ]
    }

    # Assert the mock was called correctly
    mock_db_manager.search_attractions.assert_called_once_with(query=expected_db_query, limit=limit)
    
    # Assert the result is correct
    assert results == expected_results

def test_search_attractions_no_query_calls_db_manager(knowledge_base, mock_db_manager):
    """Test search_attractions works correctly when no text query is provided."""
    filters = {"city": "Luxor", "type": "temple"}
    language = "en"
    limit = 10
    expected_results = [{"id": "lux_temple", "name_en": "Luxor Temple"}]
    
    mock_db_manager.search_attractions.return_value = expected_results
    
    results = knowledge_base.search_attractions(query="", filters=filters, language=language, limit=limit)
    
    # When query is empty, only the original filters should be passed
    expected_db_query = {
        '$and': [
            {'city': {'$eq': 'Luxor'}},
            {'type': {'$eq': 'temple'}}
        ]
    }
    
    mock_db_manager.search_attractions.assert_called_once_with(query=expected_db_query, limit=limit)
    assert results == expected_results

def test_search_restaurants_calls_db_manager(knowledge_base, mock_db_manager):
    """Test search_restaurants delegates the call to db_manager.search_restaurants."""
    query = "koshary"
    filters = {"city": "Cairo"}
    language = "en"
    limit = 3
    expected_results = [{"id": "kosh_1", "name_en": "Koshary El Tahrir"}]

    mock_db_manager.search_restaurants.return_value = expected_results

    results = knowledge_base.search_restaurants(query=query, filters=filters, language=language, limit=limit)

    search_term = f'%{query}%'
    expected_db_query = {
        '$and': [
            {'$or': [
                {'name_en': {'$like': search_term}},
                {'description_en': {'$like': search_term}},
                {'cuisine': {'$like': search_term}}
            ]},
            {'city': {'$eq': 'Cairo'}}
        ]
    }

    mock_db_manager.search_restaurants.assert_called_once_with(query=expected_db_query, limit=limit)
    assert results == expected_results

def test_search_hotels_calls_db_manager(knowledge_base, mock_db_manager):
    """Test search_hotels delegates the call to db_manager.search_accommodations."""
    query = "nile view"
    filters = {"city": "Aswan", "rating": 5}
    language = "en"
    limit = 2
    expected_results = [{"id": "old_cat", "name_en": "Old Cataract"}]

    # Note: KB.search_hotels calls DBManager.search_accommodations
    mock_db_manager.search_accommodations.return_value = expected_results

    results = knowledge_base.search_hotels(query=query, filters=filters, language=language, limit=limit)

    search_term = f'%{query}%'
    expected_db_query = {
        '$and': [
            {'$or': [
                {'name_en': {'$like': search_term}},
                {'description_en': {'$like': search_term}},
                {'type': {'$like': search_term}},
                {'category': {'$like': search_term}}
            ]},
            {'city': {'$eq': 'Aswan'}},
            {'rating': {'$eq': 5}}
        ]
    }

    # Assert the correct DB manager method is called
    mock_db_manager.search_accommodations.assert_called_once_with(query=expected_db_query, limit=limit)
    assert results == expected_results

def test_get_restaurant_by_id_calls_db_manager(knowledge_base, mock_db_manager):
    """Test get_restaurant_by_id delegates the call to db_manager.get_restaurant."""
    restaurant_id = "rest_456"
    expected_result = {"id": restaurant_id, "name_en": "Abu Shakra"}
    
    mock_db_manager.get_restaurant.return_value = expected_result
    
    result = knowledge_base.get_restaurant_by_id(restaurant_id)
    
    mock_db_manager.get_restaurant.assert_called_once_with(restaurant_id)
    assert result == expected_result

def test_get_hotel_by_id_calls_db_manager(knowledge_base, mock_db_manager):
    """Test get_hotel_by_id delegates the call to db_manager.get_accommodation."""
    hotel_id = "hotel_789"
    expected_result = {"id": hotel_id, "name_en": "Sofitel Legend"}

    # Note: KB.get_hotel_by_id calls DBManager.get_accommodation
    mock_db_manager.get_accommodation.return_value = expected_result
    
    result = knowledge_base.get_hotel_by_id(hotel_id)
    
    # Assert the correct DB manager method is called
    mock_db_manager.get_accommodation.assert_called_once_with(hotel_id)
    assert result == expected_result

# --- Edge Case Tests ---

def test_get_attraction_by_id_returns_none_when_db_manager_returns_none(knowledge_base, mock_db_manager):
    """Test get_attraction_by_id returns None if db_manager returns None."""
    attraction_id = "not_found_attr"
    mock_db_manager.get_attraction.return_value = None
    
    result = knowledge_base.get_attraction_by_id(attraction_id)
    
    mock_db_manager.get_attraction.assert_called_once_with(attraction_id)
    assert result is None

def test_get_restaurant_by_id_returns_none_when_db_manager_returns_none(knowledge_base, mock_db_manager):
    """Test get_restaurant_by_id returns None if db_manager returns None."""
    restaurant_id = "not_found_rest"
    mock_db_manager.get_restaurant.return_value = None
    
    result = knowledge_base.get_restaurant_by_id(restaurant_id)
    
    mock_db_manager.get_restaurant.assert_called_once_with(restaurant_id)
    assert result is None

def test_get_hotel_by_id_returns_none_when_db_manager_returns_none(knowledge_base, mock_db_manager):
    """Test get_hotel_by_id returns None if db_manager (get_accommodation) returns None."""
    hotel_id = "not_found_hotel"
    mock_db_manager.get_accommodation.return_value = None
    
    result = knowledge_base.get_hotel_by_id(hotel_id)
    
    mock_db_manager.get_accommodation.assert_called_once_with(hotel_id)
    assert result is None

def test_get_attraction_by_id_handles_db_manager_exception(knowledge_base, mock_db_manager):
    """Test get_attraction_by_id returns None and logs error if db_manager raises Exception."""
    attraction_id = "error_attr"
    mock_db_manager.get_attraction.side_effect = Exception("DB connection failed")
    
    # Use patch to capture logs (might need logger configuration in tests later)
    with patch('src.knowledge.knowledge_base.logging') as mock_logging:
        result = knowledge_base.get_attraction_by_id(attraction_id)
        
        mock_db_manager.get_attraction.assert_called_once_with(attraction_id)
        assert result is None
        # Check if error was logged (basic check, refinement might be needed)
        mock_logging.error.assert_called_once()

# TODO: Add similar exception handling tests for other get/search methods
# TODO: Add tests for search methods returning empty lists

# TODO: Add similar tests for:
# - search_restaurants
# - search_hotels (calls search_accommodations on db_manager)
# - get_restaurant_by_id
# - get_hotel_by_id (calls get_accommodation on db_manager)
# - Edge cases (e.g., location not found, db_manager returning None or raising errors) 