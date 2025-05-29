#!/usr/bin/env python
"""
Test API Endpoints for Egypt Tourism Chatbot

This script tests the API endpoints used by the React frontend to ensure they're working correctly.
"""

import os
import sys
import json
import logging
import requests
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_api_endpoints.log')
    ]
)
logger = logging.getLogger(__name__)

# API base URL (make sure it has a trailing slash)
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:5000/")

def test_endpoint(endpoint: str, method: str = "GET", data: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Test an API endpoint

    Args:
        endpoint (str): API endpoint path
        method (str, optional): HTTP method. Defaults to "GET".
        data (Optional[Dict[str, Any]], optional): Request data. Defaults to None.
        headers (Optional[Dict[str, str]], optional): Request headers. Defaults to None.

    Returns:
        Dict[str, Any]: Test result
    """
    # Remove leading slash from endpoint if present
    if endpoint.startswith('/'):
        endpoint = endpoint[1:]

    url = f"{API_BASE_URL}{endpoint}"

    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers)
        else:
            return {
                "success": False,
                "error": f"Unsupported method: {method}"
            }

        # Check if response is JSON
        try:
            response_data = response.json()
        except:
            response_data = {"text": response.text[:100] + "..." if len(response.text) > 100 else response.text}

        return {
            "success": response.status_code < 400,
            "status_code": response.status_code,
            "data": response_data
        }
    except Exception as e:
        logger.error(f"Error testing endpoint {endpoint}: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def test_all_endpoints():
    """Test all API endpoints used by the React frontend"""
    endpoints = [
        {
            "name": "Health Check",
            "endpoint": "api/health",
            "method": "GET"
        },
        {
            "name": "CSRF Token",
            "endpoint": "api/csrf-token",
            "method": "GET"
        },
        {
            "name": "Create Session",
            "endpoint": "api/sessions",
            "method": "POST",
            "data": {}
        },
        {
            "name": "Chat",
            "endpoint": "api/chat",
            "method": "POST",
            "data": {
                "message": "Tell me about the Pyramids of Giza",
                "session_id": None,  # Will be filled in after session creation
                "language": "en"
            }
        },
        {
            "name": "Suggestions",
            "endpoint": "api/suggestions",
            "method": "GET",
            "params": {
                "language": "en"
            }
        },
        {
            "name": "Languages",
            "endpoint": "api/languages",
            "method": "GET"
        }
    ]

    results = {}
    session_id = None

    # Test each endpoint
    for endpoint_info in endpoints:
        name = endpoint_info["name"]
        endpoint = endpoint_info["endpoint"]
        method = endpoint_info["method"]
        data = endpoint_info.get("data", None)

        # If this is the chat endpoint and we have a session ID, use it
        if name == "Chat" and session_id:
            data["session_id"] = session_id

        logger.info(f"Testing endpoint: {name} ({method} {endpoint})")

        result = test_endpoint(endpoint, method, data)

        # If this is the session creation endpoint and it succeeded, save the session ID
        if name == "Create Session" and result["success"] and "session_id" in result["data"]:
            session_id = result["data"]["session_id"]
            logger.info(f"Created session: {session_id}")

        results[name] = result

        if result["success"]:
            logger.info(f"✅ {name}: Success (Status: {result['status_code']})")
        else:
            logger.error(f"❌ {name}: Failed - {result.get('error', f'Status: {result.get('status_code', 'Unknown')}')}")

    return results

def print_summary(results):
    """Print a summary of the test results"""
    print("\n" + "=" * 80)
    print("EGYPT TOURISM CHATBOT - API ENDPOINT TEST RESULTS")
    print("=" * 80)

    success_count = sum(1 for result in results.values() if result["success"])
    total_count = len(results)

    print(f"\nSuccess Rate: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")

    print("\nEndpoint Results:")
    for name, result in results.items():
        status = "✅ Success" if result["success"] else f"❌ Failed ({result.get('error', f'Status: {result.get('status_code', 'Unknown')}')}"
        print(f"  {name}: {status}")

    print("\nDetailed Results:")
    for name, result in results.items():
        print(f"\n{name}:")
        if result["success"]:
            print(f"  Status: {result['status_code']}")
            if "data" in result:
                print(f"  Data: {json.dumps(result['data'], indent=2)[:200]}...")
        else:
            print(f"  Error: {result.get('error', 'Unknown error')}")

    print("\n" + "=" * 80)

def main():
    """Main function"""
    logger.info("Starting API endpoint tests")

    # Test all endpoints
    results = test_all_endpoints()

    # Print summary
    print_summary(results)

    # Determine exit code based on results
    success_count = sum(1 for result in results.values() if result["success"])
    total_count = len(results)

    if success_count == total_count:
        logger.info("All tests passed!")
        return 0
    else:
        logger.warning(f"{total_count - success_count} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
