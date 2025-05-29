#!/usr/bin/env python
"""
Simple API Test for Egypt Tourism Chatbot

This script tests the basic API endpoints to ensure they're working.
"""

import requests
import json

# Base URL
BASE_URL = "http://localhost:5050"

# Session to maintain cookies
session = requests.Session()

def get_csrf_token():
    """Get CSRF token"""
    try:
        response = session.get(f"{BASE_URL}/api/csrf-token")
        print(f"CSRF Token: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            token = data.get("csrf_token")
            print(f"  Success! Token: {token[:10]}...")
            return token
        else:
            print(f"  Failed: {response.text}")
            return None
    except Exception as e:
        print(f"  Error: {e}")
        return None

def test_health():
    """Test the health endpoint"""
    try:
        response = session.get(f"{BASE_URL}/api/health")
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

def test_create_session(csrf_token):
    """Test creating a session"""
    try:
        headers = {"X-CSRF-Token": csrf_token} if csrf_token else {}
        response = session.post(f"{BASE_URL}/api/sessions", headers=headers)
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

def test_chat(session_id, csrf_token):
    """Test the chat endpoint"""
    if not session_id:
        print("Chat: Skipped (no session ID)")
        return False

    try:
        headers = {"X-CSRF-Token": csrf_token} if csrf_token else {}
        data = {
            "message": "Tell me about the Pyramids of Giza",
            "session_id": session_id
        }
        response = session.post(f"{BASE_URL}/api/chat", json=data, headers=headers)
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

    # Get CSRF token
    csrf_token = get_csrf_token()

    # Test health endpoint
    health_ok = test_health()

    # Test creating a session
    session_id = test_create_session(csrf_token)

    # Test chat endpoint
    if session_id:
        chat_ok = test_chat(session_id, csrf_token)
    else:
        chat_ok = False

    # Print summary
    print("\nTest Summary:")
    print(f"  CSRF Token: {'✅ Obtained' if csrf_token else '❌ Failed'}")
    print(f"  Health Check: {'✅ Passed' if health_ok else '❌ Failed'}")
    print(f"  Create Session: {'✅ Passed' if session_id else '❌ Failed'}")
    print(f"  Chat: {'✅ Passed' if chat_ok else '❌ Failed'}")

    # Overall result
    if csrf_token and health_ok and session_id and chat_ok:
        print("\n✅ All tests passed! The API is working correctly.")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the API.")
        return 1

if __name__ == "__main__":
    main()
