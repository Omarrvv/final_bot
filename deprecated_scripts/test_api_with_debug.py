#!/usr/bin/env python3
"""
Test the chat API with debug info to see what's happening inside the RAG pipeline.
"""
import requests
import json
import sys

def test_chat_api_with_debug():
    """Test the chat API with debug mode enabled."""
    # Base URL for your API
    base_url = "http://localhost:5050"
    
    # Chat endpoint
    chat_endpoint = f"{base_url}/api/chat"
    
    # Test queries
    test_queries = [
        {
            "message": "What are the top attractions in Cairo?",
            "session_id": "test-debug-123",
            "debug": True
        },
        {
            "message": "Tell me about the Egyptian Museum",
            "session_id": "test-debug-123",
            "debug": True,
            "enable_rag": True  # Try to force RAG if supported
        }
    ]
    
    for payload in test_queries:
        query = payload["message"]
        print(f"\n🔍 Testing query with debug: \"{query}\"")
        
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
                print(f"✅ SUCCESS! Got response with debug info:")
                print(json.dumps(result, indent=2))
                
                # Check if debug info contains any retrieval data
                debug_info = result.get("debug_info", {})
                if debug_info and any(k in str(debug_info).lower() for k in ["retriev", "knowledge", "database", "rag"]):
                    print("✅ Debug info contains retrieval information!")
                    return True
            else:
                print(f"❌ ERROR: API returned status code {response.status_code}")
                print(f"Response: {response.text}")
        
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
    
    return False

if __name__ == "__main__":
    print("Testing chat API with debug info...")
    if test_chat_api_with_debug():
        print("\n✅ API debug test passed! Found retrieval information.")
        sys.exit(0)
    else:
        print("\n❌ API debug test passed but no retrieval information found.")
        sys.exit(1)
