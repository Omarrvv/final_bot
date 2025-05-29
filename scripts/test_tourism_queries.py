#!/usr/bin/env python
"""
Test Tourism Queries

This script tests the Egypt Tourism Chatbot's ability to answer common tourism questions.
It sends a variety of tourism-related queries to the chatbot and evaluates the responses.

Usage:
    python test_tourism_queries.py [--verbose]
"""

import os
import sys
import json
import logging
import argparse
import requests
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import time
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_tourism_queries.log')
    ]
)
logger = logging.getLogger(__name__)

# API endpoint
API_URL = os.environ.get("API_URL", "http://localhost:5000/api")

# Test queries by category
TEST_QUERIES = {
    "attractions": [
        "Tell me about the Pyramids of Giza",
        "What are the opening hours for the Egyptian Museum?",
        "How much does it cost to visit Karnak Temple?",
        "What's the history of the Valley of the Kings?",
        "What are the top attractions in Luxor?",
        "Is the Sphinx worth visiting?",
        "Tell me about Islamic Cairo",
        "What's special about Abu Simbel?",
        "What can I see at Philae Temple?",
        "Tell me about the Bibliotheca Alexandrina"
    ],
    "cities": [
        "What are the best things to do in Cairo?",
        "Tell me about Alexandria",
        "What's Luxor famous for?",
        "What should I see in Aswan?",
        "Is Hurghada good for families?",
        "What's the weather like in Sharm El Sheikh?",
        "Tell me about the history of Cairo",
        "What's the local cuisine in Alexandria?",
        "How do I get around in Luxor?",
        "What's the best time to visit Aswan?"
    ],
    "accommodations": [
        "What are the best hotels in Cairo?",
        "Are there budget accommodations in Luxor?",
        "Tell me about luxury hotels in Sharm El Sheikh",
        "What's the Four Seasons Cairo like?",
        "Are there hotels near the Pyramids?",
        "What's the best area to stay in Alexandria?",
        "Are there family-friendly resorts in Hurghada?",
        "Tell me about historic hotels in Egypt",
        "What amenities do hotels in Egypt typically offer?",
        "Are there eco-friendly accommodations in Egypt?"
    ],
    "practical_info": [
        "What's the currency in Egypt?",
        "Do I need a visa to visit Egypt?",
        "What's the best time of year to visit Egypt?",
        "Is it safe to travel to Egypt?",
        "What should I wear when visiting Egypt?",
        "How do I get from Cairo to Luxor?",
        "What languages are spoken in Egypt?",
        "What's the tipping culture in Egypt?",
        "How much does a typical meal cost in Egypt?",
        "What vaccinations do I need for Egypt?"
    ],
    "cultural": [
        "Tell me about Egyptian cuisine",
        "What are important Egyptian customs?",
        "What festivals are celebrated in Egypt?",
        "Tell me about ancient Egyptian religion",
        "What's the significance of the Nile in Egyptian culture?",
        "What souvenirs should I buy in Egypt?",
        "Tell me about Egyptian music and dance",
        "What's the history of hieroglyphics?",
        "What's the significance of the scarab in Egyptian culture?",
        "Tell me about modern Egyptian art"
    ]
}

def create_session() -> Tuple[str, Dict[str, Any]]:
    """Create a new session with the chatbot"""
    try:
        response = requests.post(f"{API_URL}/sessions")
        if response.status_code == 200:
            data = response.json()
            session_id = data.get("session_id")
            logger.info(f"Created session: {session_id}")
            return session_id, data
        else:
            logger.error(f"Failed to create session: {response.status_code} - {response.text}")
            return "", {}
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        return "", {}

def send_message(session_id: str, message: str) -> Dict[str, Any]:
    """Send a message to the chatbot and get the response"""
    try:
        payload = {
            "message": message,
            "session_id": session_id
        }
        response = requests.post(f"{API_URL}/chat", json=payload)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            logger.error(f"Failed to send message: {response.status_code} - {response.text}")
            return {"error": f"Failed to send message: {response.status_code}"}
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return {"error": f"Error sending message: {e}"}

def evaluate_response(query: str, response: Dict[str, Any], category: str) -> Dict[str, Any]:
    """Evaluate the chatbot's response"""
    # Extract the response text
    response_text = response.get("response", "")
    
    # Check if the response contains an error
    if "error" in response or not response_text:
        return {
            "query": query,
            "category": category,
            "response": response_text,
            "has_error": True,
            "is_relevant": False,
            "contains_tourism_info": False,
            "score": 0,
            "notes": "Error in response or empty response"
        }
    
    # Basic relevance check - does the response contain key terms from the query?
    query_terms = set(query.lower().split())
    response_terms = set(response_text.lower().split())
    common_terms = query_terms.intersection(response_terms)
    is_relevant = len(common_terms) > 0
    
    # Check if the response contains tourism information
    tourism_keywords = [
        "egypt", "egyptian", "cairo", "luxor", "aswan", "alexandria", "hurghada", 
        "sharm", "pyramids", "sphinx", "temple", "museum", "nile", "pharaoh", 
        "ancient", "tour", "visit", "attraction", "hotel", "accommodation", 
        "restaurant", "travel", "tourist", "guide", "history", "culture"
    ]
    
    tourism_term_count = sum(1 for term in tourism_keywords if term in response_text.lower())
    contains_tourism_info = tourism_term_count >= 2
    
    # Calculate a simple score (0-10)
    score = 0
    if is_relevant:
        score += 3
    if contains_tourism_info:
        score += 3
    
    # Add points for response length (up to 4 points)
    length_score = min(4, len(response_text) // 100)
    score += length_score
    
    return {
        "query": query,
        "category": category,
        "response": response_text,
        "has_error": False,
        "is_relevant": is_relevant,
        "contains_tourism_info": contains_tourism_info,
        "tourism_term_count": tourism_term_count,
        "score": score,
        "notes": ""
    }

def run_tests(verbose: bool = False) -> Dict[str, Any]:
    """Run all test queries and evaluate responses"""
    results = {
        "timestamp": datetime.now().isoformat(),
        "total_queries": 0,
        "successful_queries": 0,
        "failed_queries": 0,
        "average_score": 0,
        "categories": {},
        "query_results": []
    }
    
    # Create a session
    session_id, session_data = create_session()
    if not session_id:
        logger.error("Failed to create session, aborting tests")
        return results
    
    # Run tests for each category
    total_score = 0
    total_queries = 0
    
    for category, queries in TEST_QUERIES.items():
        category_results = {
            "name": category,
            "total_queries": len(queries),
            "successful_queries": 0,
            "failed_queries": 0,
            "average_score": 0
        }
        
        category_score = 0
        
        for query in queries:
            logger.info(f"Testing query: {query}")
            
            # Send the query
            response = send_message(session_id, query)
            
            # Evaluate the response
            evaluation = evaluate_response(query, response, category)
            
            # Add to results
            results["query_results"].append(evaluation)
            
            # Update statistics
            total_queries += 1
            if evaluation["has_error"]:
                category_results["failed_queries"] += 1
                results["failed_queries"] += 1
            else:
                category_results["successful_queries"] += 1
                results["successful_queries"] += 1
                category_score += evaluation["score"]
                total_score += evaluation["score"]
            
            # Print verbose output if requested
            if verbose:
                print(f"\nQuery: {query}")
                print(f"Response: {evaluation['response'][:200]}...")
                print(f"Score: {evaluation['score']}/10")
                print(f"Relevant: {evaluation['is_relevant']}")
                print(f"Tourism Info: {evaluation['contains_tourism_info']}")
                print("-" * 80)
            
            # Add a small delay to avoid rate limiting
            time.sleep(1)
        
        # Calculate category average score
        if category_results["successful_queries"] > 0:
            category_results["average_score"] = category_score / category_results["successful_queries"]
        
        # Add category results
        results["categories"][category] = category_results
    
    # Calculate overall average score
    results["total_queries"] = total_queries
    if results["successful_queries"] > 0:
        results["average_score"] = total_score / results["successful_queries"]
    
    return results

def print_summary(results: Dict[str, Any]) -> None:
    """Print a summary of the test results"""
    print("\n" + "=" * 80)
    print("EGYPT TOURISM CHATBOT - TEST RESULTS SUMMARY")
    print("=" * 80)
    
    print(f"\nTimestamp: {results['timestamp']}")
    print(f"Total Queries: {results['total_queries']}")
    print(f"Successful Queries: {results['successful_queries']} ({results['successful_queries']/results['total_queries']*100:.1f}%)")
    print(f"Failed Queries: {results['failed_queries']} ({results['failed_queries']/results['total_queries']*100:.1f}%)")
    print(f"Average Score: {results['average_score']:.1f}/10")
    
    print("\nResults by Category:")
    for category, data in results["categories"].items():
        print(f"  {category.capitalize()}: {data['average_score']:.1f}/10 ({data['successful_queries']}/{data['total_queries']} successful)")
    
    print("\nTop Performing Queries:")
    top_queries = sorted(results["query_results"], key=lambda x: x["score"], reverse=True)[:5]
    for i, query in enumerate(top_queries, 1):
        print(f"  {i}. \"{query['query']}\" (Score: {query['score']}/10)")
    
    print("\nPoorly Performing Queries:")
    bottom_queries = sorted([q for q in results["query_results"] if not q["has_error"]], key=lambda x: x["score"])[:5]
    for i, query in enumerate(bottom_queries, 1):
        print(f"  {i}. \"{query['query']}\" (Score: {query['score']}/10)")
    
    print("\n" + "=" * 80)

def save_results(results: Dict[str, Any]) -> None:
    """Save the test results to a file"""
    filename = f"tourism_query_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {filename}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Test Egypt Tourism Chatbot's query capabilities")
    parser.add_argument("--verbose", action="store_true", help="Print verbose output")
    args = parser.parse_args()
    
    logger.info("Starting tourism query tests")
    
    # Run the tests
    results = run_tests(args.verbose)
    
    # Print summary
    print_summary(results)
    
    # Save results
    save_results(results)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
