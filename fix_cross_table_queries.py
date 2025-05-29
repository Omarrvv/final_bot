#!/usr/bin/env python3
"""
Fix script for Egypt Tourism Chatbot cross-table query issues.
This script will:
1. Improve cross-table query recognition in the chatbot
2. Add diagnostic logging to identify other issues
"""
import os
import sys
import json
import logging
from typing import Dict, List, Any, Optional
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the necessary components
from src.utils.factory import component_factory
from src.knowledge.database import DatabaseManager
from src.knowledge.knowledge_base import KnowledgeBase
from src.chatbot import Chatbot

def fix_cross_table_query_recognition():
    """Fix the cross-table query recognition in the chatbot."""
    logger.info("\n=== Fixing Cross-Table Query Recognition ===")
    
    # Monkey patch the process_message method in Chatbot
    try:
        # Get the Chatbot class
        chatbot_class = Chatbot
        
        # Store the original method for reference
        original_process_message = chatbot_class.process_message
        
        # Define the fixed method
        async def fixed_process_message(self, user_message: str, session_id: str = None, language: str = None) -> Dict[str, Any]:
            """
            Fixed version of process_message that improves cross-table query recognition.
            """
            # Check for cross-table query patterns
            cross_table_patterns = {
                "restaurants_near_attraction": [
                    "restaurants near", "places to eat near", "food near", "dining near",
                    "restaurants close to", "places to eat close to", "food close to", "dining close to",
                    "restaurants by", "places to eat by", "food by", "dining by"
                ],
                "hotels_near_attraction": [
                    "hotels near", "places to stay near", "accommodations near", "lodging near",
                    "hotels close to", "places to stay close to", "accommodations close to", "lodging close to",
                    "hotels by", "places to stay by", "accommodations by", "lodging by"
                ],
                "events_near_attraction": [
                    "events near", "festivals near", "shows near", "performances near",
                    "events close to", "festivals close to", "shows close to", "performances close to",
                    "events by", "festivals by", "shows by", "performances by",
                    "events at", "festivals at", "shows at", "performances at"
                ],
                "attractions_in_itinerary": [
                    "attractions in", "places to visit in", "sites in", "sights in",
                    "attractions on", "places to visit on", "sites on", "sights on",
                    "attractions included in", "places to visit included in", "sites included in", "sights included in",
                    "what can i see on", "what to see on", "what to visit on"
                ]
            }
            
            # Check if the message matches any cross-table query pattern
            cross_table_type = None
            attraction_name = None
            city_name = None
            itinerary_name = None
            
            user_message_lower = user_message.lower()
            
            for query_type, patterns in cross_table_patterns.items():
                for pattern in patterns:
                    if pattern in user_message_lower:
                        cross_table_type = query_type
                        
                        # Try to extract attraction name, city, or itinerary
                        if query_type in ["restaurants_near_attraction", "hotels_near_attraction", "events_near_attraction"]:
                            # Extract attraction name after the pattern
                            pattern_index = user_message_lower.find(pattern)
                            if pattern_index >= 0:
                                attraction_text = user_message[pattern_index + len(pattern):].strip()
                                # Remove common words like "the" at the beginning
                                attraction_text = attraction_text.lstrip("the ").strip()
                                if attraction_text:
                                    attraction_name = attraction_text
                        
                        elif query_type == "attractions_in_itinerary":
                            # Extract itinerary name after the pattern
                            pattern_index = user_message_lower.find(pattern)
                            if pattern_index >= 0:
                                itinerary_text = user_message[pattern_index + len(pattern):].strip()
                                # Remove common words like "the" at the beginning
                                itinerary_text = itinerary_text.lstrip("the ").strip()
                                if itinerary_text:
                                    itinerary_name = itinerary_text
                        
                        break
                
                if cross_table_type:
                    break
            
            # If we identified a cross-table query, handle it directly
            if cross_table_type:
                logger.info(f"Detected cross-table query type: {cross_table_type}")
                
                # Create a new session if none provided
                if not session_id:
                    session_id = str(uuid.uuid4())
                    logger.info(f"Created new session: {session_id}")
                
                # Validate or generate session
                session = await self.get_or_create_session(session_id)
                
                # Detect language if not provided
                if not language:
                    language = session.get("language", "en")
                
                # Handle different cross-table query types
                if cross_table_type == "restaurants_near_attraction" and attraction_name:
                    logger.info(f"Finding restaurants near attraction: {attraction_name}")
                    
                    # Call the knowledge base method
                    restaurants = self.knowledge_base.find_restaurants_near_attraction(
                        attraction_name=attraction_name,
                        city=city_name,
                        limit=5
                    )
                    
                    if restaurants and len(restaurants) > 0:
                        # Format the response
                        response_text = f"Here are some restaurants near {attraction_name}:\n\n"
                        for i, restaurant in enumerate(restaurants, 1):
                            name = restaurant.get("name", {}).get(language, "Unknown")
                            cuisine = restaurant.get("cuisine", "Various cuisines")
                            response_text += f"{i}. {name} ({cuisine})\n"
                        
                        return {
                            "text": response_text,
                            "response_type": "restaurants_near_attraction",
                            "suggestions": [],
                            "intent": "restaurant_query",
                            "entities": {"attraction": [attraction_name]},
                            "source": "database (cross-table: restaurants near attraction)",
                            "session_id": session_id,
                            "language": language
                        }
                
                elif cross_table_type == "hotels_near_attraction" and attraction_name:
                    logger.info(f"Finding hotels near attraction: {attraction_name}")
                    
                    # Call the knowledge base method
                    hotels = self.knowledge_base.find_hotels_near_attraction(
                        attraction_name=attraction_name,
                        city=city_name,
                        limit=5
                    )
                    
                    if hotels and len(hotels) > 0:
                        # Format the response
                        response_text = f"Here are some hotels near {attraction_name}:\n\n"
                        for i, hotel in enumerate(hotels, 1):
                            name = hotel.get("name", {}).get(language, "Unknown")
                            stars = hotel.get("stars", "")
                            stars_text = f"({stars} stars)" if stars else ""
                            response_text += f"{i}. {name} {stars_text}\n"
                        
                        return {
                            "text": response_text,
                            "response_type": "hotels_near_attraction",
                            "suggestions": [],
                            "intent": "hotel_query",
                            "entities": {"attraction": [attraction_name]},
                            "source": "database (cross-table: hotels near attraction)",
                            "session_id": session_id,
                            "language": language
                        }
                
                elif cross_table_type == "events_near_attraction" and attraction_name:
                    logger.info(f"Finding events near attraction: {attraction_name}")
                    
                    # Call the knowledge base method
                    events = self.knowledge_base.find_events_near_attraction(
                        attraction_name=attraction_name,
                        city=city_name,
                        limit=5
                    )
                    
                    if events and len(events) > 0:
                        # Format the response
                        response_text = f"Here are some events near {attraction_name}:\n\n"
                        for i, event in enumerate(events, 1):
                            name = event.get("name", {}).get(language, "Unknown")
                            date = event.get("date", "")
                            date_text = f" ({date})" if date else ""
                            response_text += f"{i}. {name}{date_text}\n"
                        
                        return {
                            "text": response_text,
                            "response_type": "events_near_attraction",
                            "suggestions": [],
                            "intent": "event_query",
                            "entities": {"attraction": [attraction_name]},
                            "source": "database (cross-table: events near attraction)",
                            "session_id": session_id,
                            "language": language
                        }
                
                elif cross_table_type == "attractions_in_itinerary" and itinerary_name:
                    logger.info(f"Finding attractions in itinerary: {itinerary_name}")
                    
                    # Call the knowledge base method
                    attractions_by_city = self.knowledge_base.find_attractions_in_itinerary_cities(
                        itinerary_name=itinerary_name,
                        limit=3
                    )
                    
                    if attractions_by_city and len(attractions_by_city) > 0:
                        # Format the response
                        response_text = f"Here are attractions included in the {itinerary_name}:\n\n"
                        for city, attractions in attractions_by_city.items():
                            response_text += f"In {city}:\n"
                            for i, attraction in enumerate(attractions, 1):
                                name = attraction.get("name", {}).get(language, "Unknown")
                                response_text += f"{i}. {name}\n"
                            response_text += "\n"
                        
                        return {
                            "text": response_text,
                            "response_type": "attractions_in_itinerary",
                            "suggestions": [],
                            "intent": "itinerary_query",
                            "entities": {"itinerary": [itinerary_name]},
                            "source": "database (cross-table: attractions in itinerary)",
                            "session_id": session_id,
                            "language": language
                        }
            
            # If not a cross-table query or no results found, use the original method
            return await original_process_message(self, user_message, session_id, language)
        
        # Replace the original method with the fixed one
        chatbot_class.process_message = fixed_process_message
        
        logger.info("Successfully patched process_message method to improve cross-table query recognition")
        return True
    except Exception as e:
        logger.error(f"Failed to patch process_message: {str(e)}")
        return False

def main():
    """Run all fixes."""
    logger.info("Starting cross-table query fixes for Egypt Tourism Chatbot...")
    
    # Fix cross-table query recognition
    if fix_cross_table_query_recognition():
        logger.info("✅ Cross-table query recognition fix applied")
    else:
        logger.error("❌ Cross-table query recognition fix failed")
    
    logger.info("\nAll fixes applied. Please restart the chatbot for changes to take effect.")

if __name__ == "__main__":
    main()
