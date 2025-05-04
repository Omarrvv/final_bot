#!/usr/bin/env python
"""
Test script for Egypt Tourism Chatbot queries.
This script sends a series of tourism-related queries to the chatbot API
and prints the responses to verify the chatbot's functionality.
"""

import requests
import json
import sys
import time
import uuid
from typing import Dict, Any, List, Optional

# Configuration
API_URL = "http://localhost:5050/api/chat"
RESET_URL = "http://localhost:5050/api/reset"
HEADERS = {"Content-Type": "application/json"}
SESSION_ID = None  # Will be set after first request or reset

# Test queries covering different aspects of Egypt tourism
TEST_QUERIES = [
    # General information
    "Tell me about Egypt",
    "What's the best time to visit Egypt?",
    "Do I need a visa to visit Egypt?",
    
    # Attractions
    "What are the must-see attractions in Egypt?",
    "Tell me about the Pyramids of Giza",
    "What can I see in Luxor?",
    "Is Alexandria worth visiting?",
    "Tell me about Abu Simbel",
    
    # Practical information
    "What currency is used in Egypt?",
    "Is Egypt safe for tourists?",
    "What should I wear when visiting Egypt?",
    "How do I get around in Egypt?",
    
    # Culture and history
    "Tell me about ancient Egyptian history",
    "What kind of food can I try in Egypt?",
    "What is koshari?",
    "What are some Egyptian cultural customs I should know about?",
    
    # Activities
    "What activities can I do in Egypt?",
    "Can I go diving in the Red Sea?",
    "Tell me about Nile cruises",
    "What's special about the White Desert?",
    
    # Accommodation
    "Where should I stay in Cairo?",
    "What are the best areas to stay in Luxor?",
    "Are there good resorts in Sharm El Sheikh?",
    
    # Specific questions
    "How much does it cost to enter the Pyramids?",
    "What's the weather like in Egypt in December?",
    "How do I get from Cairo to Luxor?",
    "What languages are spoken in Egypt?",
    "What souvenirs should I buy in Egypt?"
]

def reset_session() -> str:
    """Reset or create a new session and return the session ID."""
    try:
        response = requests.post(
            RESET_URL,
            headers=HEADERS,
            json={"create_new": True}
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("session_id", str(uuid.uuid4()))
        else:
            print(f"Failed to reset session: {response.status_code}")
            return str(uuid.uuid4())
    except Exception as e:
        print(f"Error resetting session: {e}")
        return str(uuid.uuid4())

def send_query(query: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """Send a query to the chatbot API and return the response."""
    try:
        payload = {
            "message": query,
            "session_id": session_id,
            "language": "en"
        }
        
        response = requests.post(
            API_URL,
            headers=HEADERS,
            json=payload
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: API returned status code {response.status_code}")
            print(f"Response: {response.text}")
            return {"error": f"API error: {response.status_code}", "text": "Error occurred"}
    except Exception as e:
        print(f"Exception occurred: {e}")
        return {"error": str(e), "text": "Error occurred"}

def run_tests():
    """Run all test queries and print results."""
    global SESSION_ID
    
    print("=" * 80)
    print("EGYPT TOURISM CHATBOT - QUERY TESTING")
    print("=" * 80)
    
    # Reset/create session
    SESSION_ID = reset_session()
    print(f"Created new session: {SESSION_ID}\n")
    
    # Run through all test queries
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"\n[{i}/{len(TEST_QUERIES)}] QUERY: {query}")
        print("-" * 80)
        
        # Send query
        start_time = time.time()
        response = send_query(query, SESSION_ID)
        elapsed_time = time.time() - start_time
        
        # Print response
        if "error" in response:
            print(f"ERROR: {response['error']}")
        else:
            print(f"RESPONSE ({elapsed_time:.2f}s):")
            print(response.get("text", "No text in response"))
            print(f"Response type: {response.get('response_type', 'unknown')}")
            
            # Print suggestions if available
            suggestions = response.get("suggestions", [])
            if suggestions:
                print("\nSuggestions:")
                for suggestion in suggestions:
                    if isinstance(suggestion, dict):
                        print(f"- {suggestion.get('text', '')}")
                    else:
                        print(f"- {suggestion}")
        
        # Add a small delay between requests
        time.sleep(1)
    
    print("\n" + "=" * 80)
    print("TESTING COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    run_tests()
