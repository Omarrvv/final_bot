"""
Tests for the generic search_records method in the KnowledgeBase class.
"""
import pytest
from unittest.mock import MagicMock, patch
from src.knowledge.knowledge_base import KnowledgeBase


@pytest.fixture
def mock_db_manager():
    """Create a mock DatabaseManager with search methods."""
    db_manager = MagicMock()
    # Set up success returns for all search methods
    db_manager.search_attractions.return_value = [{"id": "attraction1", "name_en": "Test Attraction"}]
    db_manager.search_hotels.return_value = [{"id": "hotel1", "name_en": "Test Hotel"}]
    db_manager.search_restaurants.return_value = [{"id": "restaurant1", "name_en": "Test Restaurant"}]
    db_manager.search_cities.return_value = [{"id": "city1", "name_en": "Test City"}]
    
    return db_manager


@pytest.fixture
def knowledge_base(mock_db_manager):
    """Create a KnowledgeBase instance with a mock DatabaseManager."""
    return KnowledgeBase(db_manager=mock_db_manager)


def test_search_records_attractions(knowledge_base, mock_db_manager):
    """Test searching records in attractions table."""
    # Define test parameters
    table_name = "attractions"
    filters = {"city": "Cairo"}
    limit = 10
    offset = 0
    
    # Call the method
    results = knowledge_base.search_records(table_name, filters, limit, offset)
    
    # Verify the correct search method was called with the right parameters
    mock_db_manager.search_attractions.assert_called_once_with(
        query=filters, limit=limit, offset=offset
    )
    
    # Verify results are returned correctly
    assert results == [{"id": "attraction1", "name_en": "Test Attraction"}]


def test_search_records_accommodations(knowledge_base, mock_db_manager):
    """Test searching records in accommodations table."""
    # Define test parameters
    table_name = "accommodations"
    filters = {"city": "Cairo"}
    limit = 10
    offset = 0
    
    # Call the method
    results = knowledge_base.search_records(table_name, filters, limit, offset)
    
    # Verify the correct search method was called with the right parameters
    mock_db_manager.search_hotels.assert_called_once_with(
        query=filters, limit=limit, offset=offset
    )
    
    # Verify results are returned correctly
    assert results == [{"id": "hotel1", "name_en": "Test Hotel"}]


def test_search_records_restaurants(knowledge_base, mock_db_manager):
    """Test searching records in restaurants table."""
    # Define test parameters
    table_name = "restaurants"
    filters = {"cuisine": "Egyptian"}
    limit = 10
    offset = 0
    
    # Call the method
    results = knowledge_base.search_records(table_name, filters, limit, offset)
    
    # Verify the correct search method was called with the right parameters
    mock_db_manager.search_restaurants.assert_called_once_with(
        query=filters, limit=limit, offset=offset
    )
    
    # Verify results are returned correctly
    assert results == [{"id": "restaurant1", "name_en": "Test Restaurant"}]


def test_search_records_cities(knowledge_base, mock_db_manager):
    """Test searching records in cities table."""
    # Define test parameters
    table_name = "cities"
    filters = {"name": "Cairo"}
    limit = 10
    offset = 0
    
    # Use patch for hasattr specific to the instance
    # Call the method
    results = knowledge_base.search_records(table_name, filters, limit, offset)
    
    # Verify the correct search method was called with the right parameters
    mock_db_manager.search_cities.assert_called_once_with(
        query=filters, limit=limit, offset=offset
    )
    
    # Verify results are returned correctly
    assert results == [{"id": "city1", "name_en": "Test City"}]


def test_search_records_cities_method_not_exists(knowledge_base, mock_db_manager):
    """Test searching cities when search_cities method doesn't exist."""
    # Define test parameters
    table_name = "cities"
    filters = {"name": "Cairo"}
    
    # Mock hasattr for this specific test case
    with patch.object(mock_db_manager, 'search_cities', None):
        with patch('builtins.hasattr', lambda obj, attr: attr != "search_cities"):
            results = knowledge_base.search_records(table_name, filters)
    
    # Verify search_cities was not called (it doesn't have assert_not_called because it's None now)
    # But we can verify empty list is returned
    assert results == []


def test_search_records_unknown_table(knowledge_base, mock_db_manager):
    """Test searching records in an unknown table."""
    # Define test parameters
    table_name = "unknown_table"
    filters = {"name": "Test"}
    
    # Call the method
    results = knowledge_base.search_records(table_name, filters)
    
    # Verify no search methods were called
    mock_db_manager.search_attractions.assert_not_called()
    mock_db_manager.search_hotels.assert_not_called()
    mock_db_manager.search_restaurants.assert_not_called()
    mock_db_manager.search_cities.assert_not_called()
    
    # Verify empty list is returned
    assert results == []


def test_search_records_error_handling(knowledge_base, mock_db_manager):
    """Test error handling in search_records."""
    # Define test parameters
    table_name = "attractions"
    filters = {"city": "Cairo"}
    
    # Mock search_attractions to raise an exception
    mock_db_manager.search_attractions.side_effect = Exception("Database error")
    
    # Call the method
    results = knowledge_base.search_records(table_name, filters)
    
    # Verify search method was called
    mock_db_manager.search_attractions.assert_called_once()
    
    # Verify empty list is returned on error
    assert results == [] 