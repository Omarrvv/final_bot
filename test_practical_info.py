import os
import sys
import json
from unittest.mock import MagicMock, patch

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.knowledge.knowledge_base import KnowledgeBase

def test_search_practical_info():
    """Test the search_practical_info method."""
    # Create a mock database manager
    mock_db_manager = MagicMock()
    mock_db_manager.db_type = "postgres"
    
    # Set up the mock to return a successful connection
    mock_db_manager.connect.return_value = True
    
    # Create sample practical info data
    sample_data = [
        {
            "id": 1,
            "category_id": "currency",
            "title": json.dumps({"en": "Currency Information for Egypt", "ar": "معلومات العملة في مصر"}),
            "content": json.dumps({"en": "The official currency of Egypt is the Egyptian Pound (EGP).", "ar": "العملة الرسمية في مصر هي الجنيه المصري."}),
            "related_destination_ids": ["egypt"],
            "tags": ["currency", "money", "Egyptian pound"],
            "is_featured": True,
            "data": None,
            "created_at": "2025-05-10T12:00:00Z",
            "updated_at": "2025-05-10T12:00:00Z"
        }
    ]
    
    # Set up the mock to return our sample data
    mock_db_manager.execute_query.return_value = sample_data
    
    # Create a KnowledgeBase instance with our mock
    kb = KnowledgeBase(mock_db_manager)
    
    # Test searching for currency information
    results = kb.search_practical_info(query={"category_id": "currency"})
    
    # Verify the results
    assert len(results) == 1
    assert results[0]["category_id"] == "currency"
    assert results[0]["title"]["en"] == "Currency Information for Egypt"
    assert "Egyptian Pound" in results[0]["content"]["en"]
    
    # Test the text search functionality
    mock_db_manager.execute_query.return_value = sample_data
    results = kb.search_practical_info(query={"text": "currency"})
    assert len(results) == 1
    
    # Test with no results
    mock_db_manager.execute_query.return_value = []
    results = kb.search_practical_info(query={"category_id": "nonexistent"})
    assert len(results) == 0
    
    print("All tests passed!")

if __name__ == "__main__":
    test_search_practical_info()
