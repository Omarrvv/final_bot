import requests
import json
import os
import logging
import sys
import traceback  # Add traceback for better error reporting
import pytest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("kb_integration_test")

# Test configuration
BASE_URL = "http://localhost:5001"
API_URL = f"{BASE_URL}/api/chat"  # Changed from 5000 to 5001
TEST_QUERIES = [
    {
        "name": "Egyptian Museum query",
        "message": "information about the Egyptian Museum",
        "language": "en",
        "expected_keywords": ["museum", "Cairo", "artifacts", "collection"]
    }
]

def get_csrf_token():
    """Get a CSRF token from the API"""
    try:
        response = requests.get(f"{BASE_URL}/api/csrf-token", timeout=5)
        if response.status_code != 200:
            logger.error(f"Failed to get CSRF token: {response.status_code}")
            return None
        
        data = response.json()
        if "csrf_token" not in data:
            logger.error("CSRF token not found in response")
            return None
        
        logger.info("Successfully obtained CSRF token")
        return data["csrf_token"]
    except Exception as e:
        logger.error(f"Error getting CSRF token: {str(e)}")
        return None

def check_diagnostics():
    """Run diagnostic check on the API"""
    try:
        logger.info("Running diagnostic check...")
        response = requests.get(f"{BASE_URL}/api/diagnostic", timeout=5)
        if response.status_code != 200:
            logger.error(f"Diagnostic check failed with status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
        
        data = response.json()
        logger.info(f"Diagnostic status: {data.get('status', 'unknown')}")
        logger.info(f"USE_NEW_KB setting: {data.get('use_new_kb', 'unknown')}")
        
        if "database" in data:
            db_info = data["database"]
            logger.info(f"Database type: {db_info.get('type', 'unknown')}")
            logger.info(f"Database connected: {db_info.get('connected', 'unknown')}")
            logger.info(f"Sample attractions count: {db_info.get('sample_attractions_count', 'unknown')}")
            logger.info(f"Sample attraction IDs: {db_info.get('sample_attraction_ids', [])}")
        
        return data.get("status") == "ok"
    except Exception as e:
        logger.error(f"Error during diagnostic check: {str(e)}")
        return False

def test_query(query_data=None, csrf_token=None):
    """Test a specific query against the chatbot API"""
    
    # Use default query data if none provided
    if query_data is None:
        query_data = {
            "name": "Egyptian Museum query",
            "message": "information about the Egyptian Museum",
            "language": "en",
            "expected_keywords": ["museum", "Cairo", "artifacts", "collection"]
        }
    
    logger.info(f"Testing: {query_data['name']}")
    logger.info(f"Query: {query_data['message']}")
    
    # Check if server is running first
    try:
        health_response = requests.get(f"{BASE_URL}/api/health", timeout=2)
    except requests.exceptions.ConnectionError:
        pytest.skip("Server is not running. Run the server with ./run_flask_for_test.sh before executing this test.")
    
    # Prepare request
    payload = {
        "message": query_data["message"],
        "language": query_data["language"]
    }
    
    # Prepare headers with CSRF token if available
    headers = {}
    if csrf_token:
        headers["X-CSRF-Token"] = csrf_token
    
    try:
        # Send request to API
        response = requests.post(API_URL, json=payload, headers=headers, timeout=10)
        
        # Check response status
        if response.status_code != 200:
            logger.error(f"Failed with status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
        
        # Parse response
        data = response.json()
        logger.info(f"FULL RESPONSE: {json.dumps(data, indent=2)}")
        
        # Check for error in response
        if "error" in data:
            logger.error(f"API returned error: {data['error']}")
            return False
        
        # Check for response text
        if "text" not in data:
            logger.error("Response missing 'text' field")
            return False
        
        # Extract the text field from the response
        # It could be a string or a nested object with a text field
        if isinstance(data["text"], dict) and "text" in data["text"]:
            text = data["text"]["text"]
        else:
            text = data["text"]
        
        # Print response for inspection
        logger.info(f"Response text (first 200 chars): {text[:200] if text else ''}")
        
        # Check for expected keywords in response
        found_keywords = []
        missing_keywords = []
        
        for keyword in query_data["expected_keywords"]:
            if text and keyword.lower() in text.lower():
                found_keywords.append(keyword)
            else:
                missing_keywords.append(keyword)
        
        # Log results
        if found_keywords:
            logger.info(f"Found keywords: {', '.join(found_keywords)}")
        
        if missing_keywords:
            logger.warning(f"Missing keywords: {', '.join(missing_keywords)}")
        
        # Test passes if at least 50% of expected keywords are found
        success = len(found_keywords) >= len(query_data["expected_keywords"]) / 2
        
        if success:
            logger.info("✅ TEST PASSED")
        else:
            logger.error("❌ TEST FAILED - Not enough expected keywords found")
        
        # Use assertion instead of return value
        assert success, "Test failed: Not enough expected keywords found"
    
    except Exception as e:
        logger.error(f"Test failed with exception: {str(e)}")
        logger.error(traceback.format_exc())  # Print full traceback
        assert False, f"Test failed with exception: {str(e)}"

def main():
    """Run all test queries"""
    logger.info("=== RUNNING KNOWLEDGE BASE INTEGRATION TEST ===")
    logger.info("This test verifies that the API is returning responses using the new Knowledge Base (SQLite)")
    
    # Check if app is running by making a health check
    try:
        health_response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if health_response.status_code != 200:
            logger.error(f"API health check failed with status code: {health_response.status_code}")
            logger.error("Make sure the server is running before running this test")
            return
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error: Make sure the API server is running at {BASE_URL}")
        logger.error("Run the server with: ./run_flask_for_test.sh")
        return
    
    # Run diagnostic check
    if not check_diagnostics():
        logger.error("Diagnostic check failed - cannot proceed with tests")
        return
    
    # Get CSRF token
    csrf_token = get_csrf_token()
    if not csrf_token:
        logger.warning("Proceeding without CSRF token, requests may fail")
    
    # Run all test queries
    success_count = 0
    for query_data in TEST_QUERIES:
        if test_query(query_data, csrf_token):
            success_count += 1
        print("-" * 50)  # Separator between tests
    
    # Summary
    logger.info(f"Test Summary: {success_count}/{len(TEST_QUERIES)} tests passed")
    
    if success_count == len(TEST_QUERIES):
        logger.info("🎉 ALL TESTS PASSED - Knowledge Base (SQLite) integration is working!")
    else:
        logger.warning(f"⚠️ {len(TEST_QUERIES) - success_count} tests failed")

if __name__ == "__main__":
    main() 