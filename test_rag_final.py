#!/usr/bin/env python3
"""Test the RAG system one more time."""
import requests
import json
import time

def test_rag():
    """Test the RAG system with a query about Cairo attractions."""
    print("Testing RAG system...")
    time.sleep(5)  # Give the server a moment to start
    
    query = "What are the top attractions in Cairo?"
    
    try:
        response = requests.post(
            "http://localhost:5050/api/chat",
            json={
                "message": query,
                "session_id": "test-rag-final",
                "debug": True,
                "enable_rag": True
            },
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("\nResponse from chatbot:")
            print(result["text"])
            
            # Check if response mentions specific attractions
            keywords = ["pyramid", "giza", "museum", "sphinx", "cairo"]
            for keyword in keywords:
                if keyword.lower() in result["text"].lower():
                    print(f"\n✅ Response mentions '{keyword}' - RAG IS WORKING!")
                    return True
            
            print("\n⚠️ Response doesn't mention specific attractions - RAG may not be working")
            return False
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Error connecting to API: {e}")
        return False

if __name__ == "__main__":
    test_rag()
