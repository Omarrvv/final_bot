#!/usr/bin/env python3
"""Test the RAG system."""
import requests
import sys

def test_rag():
    print("Testing RAG system...")
    query = "What are the top attractions in Cairo?"
    
    try:
        # Send request to API
        response = requests.post(
            "http://localhost:5050/api/chat",
            json={
                "message": query,
                "session_id": "test-session-123",
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
            for keyword in ["pyramid", "giza", "museum", "sphinx"]:
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
