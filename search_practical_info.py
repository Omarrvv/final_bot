import os
import sys
import json
import argparse
from typing import Dict, Any, List

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.knowledge.knowledge_base import KnowledgeBase
from src.utils.database_factory import get_database_manager

def search_practical_info(query_text: str = None, category: str = None) -> List[Dict[str, Any]]:
    """
    Search for practical information in the knowledge base.
    
    Args:
        query_text: Text to search for
        category: Category ID to filter by
        
    Returns:
        List of practical information items matching the search criteria
    """
    # Get the database manager
    db_uri = os.environ.get("POSTGRES_URI", "postgresql://postgres:postgres@localhost:5432/egypt_chatbot")
    db_manager = get_database_manager(db_uri)
    
    # Create a KnowledgeBase instance
    kb = KnowledgeBase(db_manager)
    
    # Build the query
    query = {}
    if query_text:
        query["text"] = query_text
    if category:
        query["category_id"] = category
    
    # Search for practical information
    results = kb.search_practical_info(query=query)
    
    return results

def format_practical_info(info_items: List[Dict[str, Any]]) -> str:
    """
    Format practical information for display.
    
    Args:
        info_items: List of practical information items
        
    Returns:
        Formatted string with practical information
    """
    if not info_items:
        return "No practical information found matching your search criteria."
    
    output = []
    
    for item in info_items:
        title = item.get("title", {}).get("en", "Untitled")
        category = item.get("category_id", "Unknown")
        content = item.get("content", {}).get("en", "No content available.")
        
        # Remove markdown headers for a more conversational style
        content = content.replace("# ", "").replace("## ", "")
        
        # Truncate content if it's too long
        if len(content) > 300:
            content = content[:297] + "..."
        
        output.append(f"Title: {title}")
        output.append(f"Category: {category}")
        output.append(f"Content: {content}")
        output.append("-" * 50)
    
    return "\n".join(output)

def list_categories() -> List[Dict[str, Any]]:
    """
    List all practical information categories.
    
    Returns:
        List of category dictionaries
    """
    # Get the database manager
    db_uri = os.environ.get("POSTGRES_URI", "postgresql://postgres:postgres@localhost:5432/egypt_chatbot")
    db_manager = get_database_manager(db_uri)
    
    # Query the categories
    categories = db_manager.execute_query("SELECT * FROM practical_info_categories")
    
    return categories

def format_categories(categories: List[Dict[str, Any]]) -> str:
    """
    Format categories for display.
    
    Args:
        categories: List of category dictionaries
        
    Returns:
        Formatted string with categories
    """
    if not categories:
        return "No categories found."
    
    output = ["Available Categories:"]
    output.append("-" * 50)
    
    for category in categories:
        category_id = category.get("id", "unknown")
        name = category.get("name", {}).get("en", "Unnamed")
        description = category.get("description", {}).get("en", "No description")
        
        output.append(f"ID: {category_id}")
        output.append(f"Name: {name}")
        output.append(f"Description: {description}")
        output.append("-" * 50)
    
    return "\n".join(output)

def main():
    """Main function to demonstrate searching for practical information."""
    parser = argparse.ArgumentParser(description="Search for practical information in the Egypt Tourism Chatbot database.")
    parser.add_argument("--text", help="Text to search for in titles and content")
    parser.add_argument("--category", help="Category ID to filter by")
    parser.add_argument("--list-categories", action="store_true", help="List all available categories")
    
    args = parser.parse_args()
    
    if args.list_categories:
        print("Fetching categories...")
        categories = list_categories()
        print(format_categories(categories))
        return
    
    if not args.text and not args.category:
        print("Please provide either --text or --category to search, or use --list-categories to see available categories.")
        return
    
    print(f"Searching for practical information...")
    if args.text:
        print(f"Text query: {args.text}")
    if args.category:
        print(f"Category: {args.category}")
    
    results = search_practical_info(query_text=args.text, category=args.category)
    
    print("\nSearch Results:")
    print("-" * 50)
    print(format_practical_info(results))

if __name__ == "__main__":
    main()
