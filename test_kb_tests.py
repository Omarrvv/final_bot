import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add the project root directory to the Python path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# Import necessary components
from src.knowledge.database import DatabaseManager
from src.knowledge.knowledge_base import KnowledgeBase

class KnowledgeBaseFunctionalTests(unittest.TestCase):
    
    def setUp(self):
        # Initialize any common resources
        self.db_uri = "sqlite:///:memory:"
        self.db_manager = DatabaseManager(database_uri=self.db_uri)
        self.knowledge_base = KnowledgeBase(db_manager=self.db_manager)
    
    def tearDown(self):
        # Clean up resources
        if hasattr(self, 'db_manager') and self.db_manager.connection:
            self.db_manager.connection.close()
    
    def test_lookup_location(self):
        """Test the lookup_location function."""
        # Mock the enhanced_search method instead of search_attractions
        with patch.object(self.db_manager, 'enhanced_search') as mock_search:
            # Set up the mock to return test data
            mock_search.return_value = [
                {"id": "egyptian_museum", "name_en": "Egyptian Museum", "city": "Cairo", "region": "Cairo", "latitude": 30.0478, "longitude": 31.2336},
                {"id": "pyramids_giza", "name_en": "Pyramids of Giza", "city": "Giza", "region": "Cairo", "latitude": 29.9792, "longitude": 31.1342}
            ]
            
            # Call lookup_location with a location name
            location_info = self.knowledge_base.lookup_location("Cairo")
            
            # Verify the enhanced_search was called with correct parameters
            mock_search.assert_called_once()
            args, kwargs = mock_search.call_args
            self.assertEqual(kwargs.get('table'), "attractions")
            self.assertIn("filters", kwargs)
            self.assertIn("$or", kwargs["filters"])
            self.assertEqual(kwargs.get('limit'), 5)
            
            # Verify results
            self.assertIsNotNone(location_info)
            if location_info:  # If the method returns something
                self.assertIn("city", location_info)
                self.assertEqual(location_info["city"], "Cairo")
                self.assertIn("name", location_info)
                self.assertIn("location", location_info)
                self.assertIn("latitude", location_info["location"])
                self.assertIn("longitude", location_info["location"])
    
    def test_integration_with_real_database(self):
        """Test Knowledge Base with the actual database."""
        # Path to the actual database
        actual_db_path = Path("./data/egypt_chatbot.db")
        
        # Skip if database doesn't exist
        if not actual_db_path.exists():
            self.skipTest("Actual database not found, skipping integration test")
        
        # Create database manager for actual database
        db_uri = f"sqlite:///{actual_db_path}"
        real_db_manager = DatabaseManager(database_uri=db_uri)
        
        # Create knowledge base with real database
        real_kb = KnowledgeBase(db_manager=real_db_manager)
        
        try:
            # Test specific attraction lookup
            attraction = real_kb.get_attraction_by_id("pyramids_giza")
            
            # If not found, try a search to find some valid IDs
            if attraction is None:
                # Get some sample attractions to find valid IDs
                attractions = real_db_manager.get_all_attractions(limit=5)
                if attractions:
                    # Try the first ID
                    attraction = real_kb.get_attraction_by_id(attractions[0]["id"])
            
            # If still None, we can't run this test
            if attraction is None:
                self.skipTest("No attractions found in database")
            
            # Verify we got data from the database
            self.assertIsNotNone(attraction)
            self.assertIn("id", attraction)
            self.assertIn("name_en", attraction)
        
        finally:
            # Clean up
            real_db_manager.close()

if __name__ == "__main__":
    # Run the tests
    unittest.main() 