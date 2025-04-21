import pytest
from unittest.mock import MagicMock, patch
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
        {"id": "pyr1", "name_en": "Great Pyramid of Giza"},
        {"id": "sph1", "name_en": "Sphinx of Giza"}
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
        {"id": "pyr1", "name_en": "Great Pyramid of Giza", "city": "Cairo"}
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
