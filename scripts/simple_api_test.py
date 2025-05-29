#!/usr/bin/env python
"""
Simple API Test for Egypt Tourism Chatbot

This script tests the basic API endpoints to ensure they're working.
"""

import requests
import json

# Base URL
BASE_URL = "http://localhost:5000"

def test_health():
    """Test the health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        print(f"Health Check: {response.status_code}")
        if response.status_code == 200:
            print("  Success!")
            return True
        else:
            print(f"  Failed: {response.text}")
            return False
    except Exception as e:
        print(f"  Error: {e}")
        return False

def test_create_session():
    """Test creating a session"""
    try:
        response = requests.post(f"{BASE_URL}/api/sessions")
        print(f"Create Session: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            session_id = data.get("session_id")
            print(f"  Success! Session ID: {session_id}")
            return session_id
        else:
            print(f"  Failed: {response.text}")
            return None
    except Exception as e:
        print(f"  Error: {e}")
        return None

def test_chat(session_id):
    """Test the chat endpoint"""
    if not session_id:
        print("Chat: Skipped (no session ID)")
        return False
    
    try:
        data = {
            "message": "Tell me about the Pyramids of Giza",
            "session_id": session_id
        }
        response = requests.post(f"{BASE_URL}/api/chat", json=data)
        print(f"Chat: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Success! Response: {data.get('response', '')[:100]}...")
            return True
        else:
            print(f"  Failed: {response.text}")
            return False
    except Exception as e:
        print(f"  Error: {e}")
        return False

def main():
    """Main function"""
    print("=== Egypt Tourism Chatbot API Test ===")
    
    # Test health endpoint
    health_ok = test_health()
    
    # Test creating a session
    session_id = test_create_session()
    
    # Test chat endpoint
    if session_id:
        chat_ok = test_chat(session_id)
    else:
        chat_ok = False
    
    # Print summary
    print("\nTest Summary:")
    print(f"  Health Check: {'✅ Passed' if health_ok else '❌ Failed'}")
    print(f"  Create Session: {'✅ Passed' if session_id else '❌ Failed'}")
    print(f"  Chat: {'✅ Passed' if chat_ok else '❌ Failed'}")
    
    # Overall result
    if health_ok and session_id and chat_ok:
        print("\n✅ All tests passed! The API is working correctly.")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the API.")
        return 1

if __name__ == "__main__":
    main()
