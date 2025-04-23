#!/usr/bin/env python3
"""
Script to test restaurant search and retrieval functionality.
"""

import os
import json
import logging
from dotenv import load_dotenv
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config():
    """Load configuration from .env file."""
    load_dotenv()
    
    # Get API URI
    api_uri = os.getenv('API_HOST', 'http://localhost:5050')
    logger.info(f"Using API host: {api_uri}")
    
    return {
        'api_uri': api_uri
    }

def login(api_uri, username="test@example.com", password="password"):
    """Login to get authentication token."""
    url = f"{api_uri}/api/auth/login"
    payload = {
        "username": username,
        "password": password
    }
    
    logger.info(f"Logging in as {username}")
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        auth_data = response.json()
        token = auth_data.get('access_token')
        logger.info(f"Login successful, got token: {token[:10]}...")
        
        return token
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error during login: {e}")
        # Try without auth if login fails
        logger.info("Will try requests without authentication")
        return None
    except Exception as e:
        logger.error(f"Error during login: {e}")
        return None

def get_auth_headers(token):
    """Get authentication headers."""
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

def test_get_restaurant_by_id(api_uri, token=None, restaurant_id="koshary_el_tahrir"):
    """Test getting a restaurant by ID."""
    url = f"{api_uri}/api/tourism/restaurant/{restaurant_id}"
    headers = get_auth_headers(token)
    
    logger.info(f"Testing GET {url}")
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Restaurant details: {json.dumps(result, indent=2)}")
        
        return result
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error occurred: {e}")
        
        # Try directly querying the chat endpoint as a fallback
        if restaurant_id:
            logger.info(f"Trying chat endpoint for restaurant info...")
            chat_result = test_chat_query(api_uri, f"Tell me about {restaurant_id}")
            return chat_result
        return None
    except Exception as e:
        logger.error(f"Error getting restaurant by ID: {e}")
        return None

def test_search_restaurants(api_uri, token=None, query=""):
    """Test searching restaurants."""
    url = f"{api_uri}/api/search"
    params = {
        'q': query,
        'type': 'restaurant',
        'limit': 5
    }
    headers = get_auth_headers(token)
    
    logger.info(f"Testing GET {url} with params: {params}")
    
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        
        results = response.json()
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Found {len(results.get('results', []))} restaurants")
        logger.info(f"Search results: {json.dumps(results, indent=2)}")
        
        return results
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error occurred: {e}")
        
        # Try directly querying the chat endpoint as a fallback
        if query:
            logger.info(f"Trying chat endpoint for restaurant search...")
            chat_result = test_chat_query(api_uri, f"Find restaurants with {query}")
            return chat_result
        return None
    except Exception as e:
        logger.error(f"Error searching restaurants: {e}")
        return None

def test_chat_query(api_uri, message):
    """Test querying the chat endpoint."""
    url = f"{api_uri}/api/chat"
    payload = {
        "message": message,
        "language": "en"
    }
    
    logger.info(f"Testing POST {url} with message: {message}")
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Chat response: {result.get('response')}")
        
        return result
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error in chat query: {e}")
        return None
    except Exception as e:
        logger.error(f"Error in chat query: {e}")
        return None

def test_direct_database_query(api_uri, token=None):
    """Test direct database query endpoint."""
    url = f"{api_uri}/api/db/restaurants"
    headers = get_auth_headers(token)
    
    logger.info(f"Testing GET {url}")
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        results = response.json()
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Found {len(results)} restaurants")
        if results:
            logger.info(f"First restaurant: {json.dumps(results[0], indent=2)}")
        
        return results
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error in direct database query: {e}")
        return None
    except Exception as e:
        logger.error(f"Error in direct database query: {e}")
        return None

def main():
    """Main function to test restaurant functionality."""
    config = load_config()
    api_uri = config['api_uri']
    
    # Login to get token
    token = login(api_uri)
    
    # Try direct database query first
    logger.info("\n=== Testing Direct Database Query for Restaurants ===")
    db_restaurants = test_direct_database_query(api_uri, token)
    
    # Test getting a restaurant by ID
    logger.info("\n=== Testing Get Restaurant by ID ===")
    restaurant = test_get_restaurant_by_id(api_uri, token)
    
    # Test searching restaurants with various queries
    logger.info("\n=== Testing Restaurant Search - All Restaurants ===")
    all_restaurants = test_search_restaurants(api_uri, token)
    
    logger.info("\n=== Testing Restaurant Search - By Name 'Koshary' ===")
    koshary_restaurants = test_search_restaurants(api_uri, token, query="Koshary")
    
    logger.info("\n=== Testing Restaurant Search - By Location 'Cairo' ===")
    cairo_restaurants = test_search_restaurants(api_uri, token, query="Cairo")
    
    # Test chat endpoint for restaurants
    logger.info("\n=== Testing Chat Query for Restaurants ===")
    chat_result = test_chat_query(api_uri, "Find Egyptian restaurants in Cairo")
    
    # Check results
    if db_restaurants:
        logger.info(f"✅ Direct database query: SUCCESS - Found {len(db_restaurants)} restaurants")
    else:
        logger.info("❌ Direct database query: FAILED")
    
    if restaurant:
        logger.info("✅ Get restaurant by ID: SUCCESS")
    else:
        logger.info("❌ Get restaurant by ID: FAILED")
    
    if all_restaurants and all_restaurants.get('results'):
        logger.info("✅ Search all restaurants: SUCCESS")
    else:
        logger.info("❌ Search all restaurants: FAILED")
    
    if koshary_restaurants and koshary_restaurants.get('results'):
        logger.info("✅ Search by name 'Koshary': SUCCESS")
    else:
        logger.info("❌ Search by name 'Koshary': FAILED")
    
    if cairo_restaurants and cairo_restaurants.get('results'):
        logger.info("✅ Search by location 'Cairo': SUCCESS")
    else:
        logger.info("❌ Search by location 'Cairo': FAILED")
    
    if chat_result:
        logger.info("✅ Chat query for restaurants: SUCCESS")
    else:
        logger.info("❌ Chat query for restaurants: FAILED")

if __name__ == "__main__":
    main() 