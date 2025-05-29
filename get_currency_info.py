import os
import sys
import json
from typing import Dict, Any, List

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.knowledge.knowledge_base import KnowledgeBase
from src.utils.database_factory import get_database_manager

def get_currency_info() -> List[Dict[str, Any]]:
    """
    Get currency information from the knowledge base.
    
    Returns:
        List of currency information items
    """
    # Get the database manager
    db_uri = os.environ.get("POSTGRES_URI", "postgresql://postgres:postgres@localhost:5432/egypt_chatbot")
    db_manager = get_database_manager(db_uri)
    
    # Create a KnowledgeBase instance
    kb = KnowledgeBase(db_manager)
    
    # Search for currency information
    currency_info = kb.search_practical_info(query={"category_id": "currency"})
    
    # If no results, try a text search
    if not currency_info:
        currency_info = kb.search_practical_info(query={"text": "currency"})
    
    # If still no results, try a broader search
    if not currency_info:
        currency_info = kb.search_practical_info(query={"text": "money"})
    
    return currency_info

def format_currency_info(currency_info: List[Dict[str, Any]]) -> str:
    """
    Format currency information for display.
    
    Args:
        currency_info: List of currency information items
        
    Returns:
        Formatted string with currency information
    """
    if not currency_info:
        return "No currency information available."
    
    # Get the first item (assuming it's the most relevant)
    info = currency_info[0]
    
    # Extract the content in English
    content = info.get("content", {}).get("en", "")
    
    # Remove markdown headers for a more conversational style
    content = content.replace("# ", "").replace("## ", "")
    
    return content

def main():
    """Main function to demonstrate getting currency information."""
    print("Fetching currency information...")
    currency_info = get_currency_info()
    
    if currency_info:
        print("\nCurrency Information Found:")
        print("--------------------------")
        formatted_info = format_currency_info(currency_info)
        print(formatted_info)
    else:
        print("\nNo currency information found in the database.")
        print("Please run the SQL script to add currency information:")
        print("psql -U postgres -d egypt_chatbot -f currency_info.sql")

if __name__ == "__main__":
    main()
