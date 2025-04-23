#!/usr/bin/env python
"""
API Endpoint Testing Script

This script tests key API endpoints to verify that the transition from
src/app.py to src/main.py is working correctly. It tests basic functionality,
authentication, error handling, and database connectivity.

Run this script after starting the FastAPI server to verify endpoints.
"""
import argparse
import json
import sys
import uuid
from typing import Dict, List, Optional, Union, Any

import requests

# Colors for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
ENDC = '\033[0m'

# Default API base URL
DEFAULT_BASE_URL = "http://localhost:5050"


def print_success(message: str) -> None:
    """Print a success message in green."""
    print(f"{GREEN}✓ {message}{ENDC}")


def print_error(message: str) -> None:
    """Print an error message in red."""
    print(f"{RED}✗ {message}{ENDC}")


def print_info(message: str) -> None:
    """Print an info message in blue."""
    print(f"{BLUE}ℹ {message}{ENDC}")


def print_warning(message: str) -> None:
    """Print a warning message in yellow."""
    print(f"{YELLOW}⚠ {message}{ENDC}")


def print_section(title: str) -> None:
    """Print a section title."""
    print(f"\n{BLUE}==== {title} ===={ENDC}")


def test_health_check(base_url: str) -> bool:
    """Test the health check endpoint."""
    endpoint = f"{base_url}/api/health"
    
    try:
        response = requests.get(endpoint, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "ok":
                print_success(f"Health check succeeded: {endpoint}")
                return True
            else:
                print_error(f"Health check returned unexpected data: {data}")
                return False
        else:
            print_error(f"Health check failed with status code {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print_error(f"Health check request failed: {str(e)}")
        return False


def test_chat_endpoint(base_url: str) -> bool:
    """Test the chat endpoint."""
    endpoint = f"{base_url}/api/chat"
    
    # Generate a unique session ID for testing
    session_id = str(uuid.uuid4())
    
    payload = {
        "message": "Tell me about the Pyramids of Giza",
        "session_id": session_id,
        "language": "en"
    }
    
    try:
        response = requests.post(endpoint, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "response" in data and data.get("session_id") == session_id:
                print_success(f"Chat endpoint succeeded: {endpoint}")
                print_info(f"Response snippet: \"{data['response'][:50]}...\"")
                return True
            else:
                print_error(f"Chat endpoint returned unexpected data structure: {data}")
                return False
        else:
            print_error(f"Chat endpoint failed with status code {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print_error(f"Chat endpoint request failed: {str(e)}")
        return False


def test_reset_endpoint(base_url: str) -> bool:
    """Test the session reset endpoint."""
    endpoint = f"{base_url}/api/reset"
    
    # Generate a unique session ID for testing
    session_id = str(uuid.uuid4())
    
    payload = {
        "session_id": session_id,
        "language": "en"
    }
    
    try:
        response = requests.post(endpoint, json=payload, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("session_id") == session_id and "success" in data:
                print_success(f"Reset endpoint succeeded: {endpoint}")
                return True
            else:
                print_error(f"Reset endpoint returned unexpected data: {data}")
                return False
        else:
            print_error(f"Reset endpoint failed with status code {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print_error(f"Reset endpoint request failed: {str(e)}")
        return False


def test_suggestions_endpoint(base_url: str) -> bool:
    """Test the suggestions endpoint."""
    endpoint = f"{base_url}/api/suggestions"
    
    # Generate a unique session ID for testing
    session_id = str(uuid.uuid4())
    
    params = {
        "session_id": session_id,
        "language": "en"
    }
    
    try:
        response = requests.get(endpoint, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if "suggestions" in data and isinstance(data["suggestions"], list):
                print_success(f"Suggestions endpoint succeeded: {endpoint}")
                print_info(f"Number of suggestions: {len(data['suggestions'])}")
                return True
            else:
                print_error(f"Suggestions endpoint returned unexpected data: {data}")
                return False
        else:
            print_error(f"Suggestions endpoint failed with status code {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print_error(f"Suggestions endpoint request failed: {str(e)}")
        return False


def test_languages_endpoint(base_url: str) -> bool:
    """Test the languages endpoint."""
    endpoint = f"{base_url}/api/languages"
    
    try:
        response = requests.get(endpoint, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if "languages" in data and isinstance(data["languages"], list):
                print_success(f"Languages endpoint succeeded: {endpoint}")
                print_info(f"Available languages: {', '.join(data['languages'])}")
                return True
            else:
                print_error(f"Languages endpoint returned unexpected data: {data}")
                return False
        else:
            print_error(f"Languages endpoint failed with status code {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print_error(f"Languages endpoint request failed: {str(e)}")
        return False


def test_feedback_endpoint(base_url: str) -> bool:
    """Test the feedback endpoint."""
    endpoint = f"{base_url}/api/feedback"
    
    # Generate a unique session ID for testing
    session_id = str(uuid.uuid4())
    message_id = str(uuid.uuid4())
    
    payload = {
        "session_id": session_id,
        "message_id": message_id,
        "rating": 5,
        "comment": "Test feedback from API test script"
    }
    
    try:
        response = requests.post(endpoint, json=payload, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if "success" in data and data["success"]:
                print_success(f"Feedback endpoint succeeded: {endpoint}")
                return True
            else:
                print_error(f"Feedback endpoint returned unexpected data: {data}")
                return False
        else:
            print_error(f"Feedback endpoint failed with status code {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print_error(f"Feedback endpoint request failed: {str(e)}")
        return False


def test_error_handling(base_url: str) -> bool:
    """Test error handling by making an invalid request."""
    endpoint = f"{base_url}/api/chat"
    
    # Invalid payload (missing required fields)
    payload = {
        "message": "This is a test"
        # Missing session_id and language
    }
    
    try:
        response = requests.post(endpoint, json=payload, timeout=5)
        if 400 <= response.status_code < 500:
            print_success(f"Error handling test succeeded: {endpoint}")
            print_info(f"Expected error response: {response.status_code}: {response.text[:100]}...")
            return True
        elif response.status_code == 200:
            print_error("Error handling test failed: Server accepted invalid request")
            return False
        else:
            print_error(f"Error handling test unexpected status code: {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print_error(f"Error handling test request failed: {str(e)}")
        return False


def test_knowledge_base_endpoint(base_url: str) -> bool:
    """Test the knowledge base endpoint to verify database connectivity."""
    endpoint = f"{base_url}/api/knowledge/attractions"
    
    params = {
        "limit": 5
    }
    
    try:
        response = requests.get(endpoint, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "data" in data and isinstance(data["data"], list):
                print_success(f"Knowledge base endpoint succeeded: {endpoint}")
                print_info(f"Number of attractions returned: {len(data['data'])}")
                return True
            else:
                print_error(f"Knowledge base endpoint returned unexpected data: {data}")
                return False
        else:
            print_error(f"Knowledge base endpoint failed with status code {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print_error(f"Knowledge base endpoint request failed: {str(e)}")
        return False


def test_auth_endpoint(base_url: str) -> bool:
    """Test the authentication endpoint."""
    endpoint = f"{base_url}/api/v1/auth/login"
    
    # Test credentials
    payload = {
        "username": "test_user",
        "password": "test_password"
    }
    
    try:
        response = requests.post(endpoint, json=payload, timeout=5)
        
        # Either 200 (success) or 400/401 (auth failed) is acceptable
        # We're mainly testing that the endpoint exists and responds
        if response.status_code in [200, 400, 401]:
            print_success(f"Auth endpoint is responsive: {endpoint}")
            if response.status_code == 200:
                print_info("Authentication succeeded (test user accepted)")
            else:
                print_info("Authentication failed as expected (invalid test credentials)")
            return True
        else:
            print_error(f"Auth endpoint failed with unexpected status code {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print_error(f"Auth endpoint request failed: {str(e)}")
        return False


def test_api_endpoints(base_url: str = DEFAULT_BASE_URL) -> None:
    """Test all API endpoints."""
    print_section("API Endpoint Testing")
    print_info(f"Testing against base URL: {base_url}")
    
    results = {}
    
    # Basic endpoints
    print_section("Core API")
    results["health_check"] = test_health_check(base_url)
    results["chat"] = test_chat_endpoint(base_url)
    results["reset"] = test_reset_endpoint(base_url)
    results["suggestions"] = test_suggestions_endpoint(base_url)
    results["languages"] = test_languages_endpoint(base_url)
    results["feedback"] = test_feedback_endpoint(base_url)
    
    # Error handling
    print_section("Error Handling")
    results["error_handling"] = test_error_handling(base_url)
    
    # Database connectivity
    print_section("Database Connectivity")
    results["knowledge_base"] = test_knowledge_base_endpoint(base_url)
    
    # Authentication
    print_section("Authentication")
    results["auth"] = test_auth_endpoint(base_url)
    
    # Summary
    print_section("Summary")
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    print(f"Passed {passed}/{total} tests ({passed/total*100:.1f}%)")
    
    for name, result in results.items():
        status = f"{GREEN}PASSED{ENDC}" if result else f"{RED}FAILED{ENDC}"
        print(f" - {name}: {status}")
    
    if passed == total:
        print(f"\n{GREEN}All tests passed! The API is working correctly.{ENDC}")
        print(f"{GREEN}You can proceed to Phase 3 of the architecture transition.{ENDC}")
    else:
        print(f"\n{YELLOW}Some tests failed. Review the errors before proceeding to Phase 3.{ENDC}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test API endpoints")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help=f"Base URL to test against (default: {DEFAULT_BASE_URL})")
    args = parser.parse_args()
    
    test_api_endpoints(args.base_url) 