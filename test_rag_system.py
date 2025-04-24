#!/usr/bin/env python3
"""
Test the RAG system with a simple query to verify it's working.
"""
import requests
import json
import time
import sys

def test_rag_query(query):
    """Test the RAG system with a query."""
    print(f"Testing query: '{query}'")
    
    # Give the server time to start up if it was just restarted
    time.sleep(5)
    
    # Prepare the payload
    payload = {
        "message": query,
        "session_id": "rag-test-session",
        "debug": True,
        "enable_rag": True
    }
    
    try:
        # Send the query to the API
        response = requests.post(
            "http://localhost:5050/api/chat",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        # Check if the request was successful
        if response.status_code == 200:
            result = response.json()
            print("\n✅ SUCCESS! Got response:")
            print(json.dumps(result, indent=2))
            
            # Check if the response mentions any specific attractions
            response_text = result.get("text", "").lower()
            
            # Look for mentions of attractions, locations, or facts mentioned in our sample data
            attraction_keywords = [
                "pyramid", "sphinx", "giza", "cairo", "luxor", "egyptian museum",
                "karnak", "pharaoh", "temple", "ancient", "tutankhamun", "mummy"
            ]
            
            # Check if any attraction keywords are in the response
            found_keywords = [keyword for keyword in attraction_keywords if keyword in response_text]
            
            if found_keywords:
                print(f"\n✅ Response mentions specific attractions: {', '.join(found_keywords)}")
                print("\nRAG SYSTEM IS WORKING CORRECTLY! The response contains specific attraction information.")
                return True
            else:
                print("\n⚠️ Response does not mention specific attractions.")
                print("RAG system may not be fully working yet.")
                return False
            
        else:
            print(f"\n❌ ERROR: API returned status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
    
    except Exception as e:
        print(f"\n❌ ERROR connecting to API: {str(e)}")
        return False

def main():
    """Main function to test the RAG system."""
    # Test with a query that should trigger location recognition
    return test_rag_query("What are the top attractions in Cairo?")

if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)
