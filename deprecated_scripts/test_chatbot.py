#!/usr/bin/env python3
import requests
import json
import sys

def test_chat_api():
    """Test if the chatbot can answer a basic Egypt tourism question."""
    
    # Base URL for your API (adjust if needed)
    base_url = "http://localhost:5050"
    
    # Test queries about Egypt tourism
    test_queries = [
        "What are the top attractions in Cairo?",
        "Tell me about the Pyramids of Giza"
    ]
    
    # API endpoint for chat
    chat_endpoint = f"{base_url}/api/chat"
    
    # Session ID
    session_id = "test-session-123"
    
    for query in test_queries:
        print(f"\n🔍 Testing query: \"{query}\"")
        
        # Prepare request payload
        payload = {
            "message": query,
            "session_id": session_id
        }
        
        try:
            # Send request to the API
            response = requests.post(
                chat_endpoint, 
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            # Check if request was successful
            if response.status_code == 200:
                result = response.json()
                print(f"✅ SUCCESS! Got response:")
                print(f"Full response structure: {json.dumps(result, indent=2)}")
                
                # Try different possible field names for the answer
                possible_fields = ["response", "answer", "text", "message", "reply", "content"]
                for field in possible_fields:
                    if field in result:
                        print(f"\nFound answer in '{field}' field:")
                        print(result[field])
                        return True
                
                print("\nCouldn't find answer field, but API is working.")
                return True
            else:
                print(f"❌ ERROR: API returned status code {response.status_code}")
                print(f"Response: {response.text}")
        
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
    
    return False

if __name__ == "__main__":
    print("Testing Egypt Tourism Chatbot API...")
    if test_chat_api():
        print("\n✅ TEST PASSED! Your API is responding.")
        sys.exit(0)
    else:
        print("\n❌ TEST FAILED! Check your API connection.")
        sys.exit(1)