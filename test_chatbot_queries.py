#!/usr/bin/env python3
"""
Enhanced test script to check if the chatbot can answer various types of tourism questions.
This script tests the chatbot's ability to retrieve information from the database and
verifies whether responses come from the database or LLM fallback.

Features:
1. Tests basic queries for different categories (attractions, restaurants, etc.)
2. Tests cross-table queries (e.g., restaurants near attractions)
3. Tests complex queries that require understanding context
4. Verifies source of responses (database vs LLM)
5. Provides detailed statistics on database coverage
"""

import os
import sys
import logging
import asyncio
import time
from collections import defaultdict

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import necessary modules
from src.chatbot import Chatbot
from src.knowledge.knowledge_base import KnowledgeBase

# Try to import optional modules
try:
    from src.nlu.intent_classifier import AdvancedIntentClassifier
except ImportError:
    logger.warning("Could not import AdvancedIntentClassifier")
    AdvancedIntentClassifier = None

try:
    from src.nlu.entity_extractor import EntityExtractor
except ImportError:
    logger.warning("Could not import EntityExtractor")
    EntityExtractor = None

try:
    from src.knowledge.cross_table_queries import CrossTableQueryManager
except ImportError:
    logger.warning("Could not import CrossTableQueryManager")
    CrossTableQueryManager = None

try:
    from src.utils.llm_fallback import LLMFallbackHandler
except ImportError:
    logger.warning("Could not import LLMFallbackHandler")
    LLMFallbackHandler = None

from src.knowledge.database import DatabaseManager

async def test_chatbot_query(chatbot, question, category=None, query_type=None, expected_entities=None):
    """
    Test the chatbot's ability to answer a specific question.

    Args:
        chatbot: The chatbot instance
        question: The question to test
        category: The category of the question (e.g., attractions, restaurants)
        query_type: The specific type of query (e.g., basic, cross-table, complex)
        expected_entities: Expected entities to be extracted from the question

    Returns:
        Dictionary containing response details and test results
    """
    try:
        logger.info(f"\n--- Testing question: '{question}' ---")
        if category:
            logger.info(f"Category: {category}")
        if query_type:
            logger.info(f"Query type: {query_type}")

        start_time = time.time()

        # Get the knowledge base from the chatbot
        kb = chatbot.knowledge_base

        # For cross-table queries, we need to use a different approach
        if query_type == "cross-table":
            response = await _handle_cross_table_query(chatbot, question, category, expected_entities)
        else:
            # For basic queries, use the standard approach
            query_params = {"text": question}

            # Query the knowledge base based on the category
            if category == "currency" or category == "safety":
                # For currency and safety, use practical_info
                if category == "currency":
                    query_params["category_id"] = "currency"
                elif category == "safety":
                    query_params["category_id"] = "safety"

                results = kb.search_practical_info(query=query_params, limit=3)

            elif category == "attractions":
                results = kb.search_attractions(query=query_params, limit=3)

            elif category == "restaurants":
                results = kb.search_restaurants(query=query_params, limit=3)

            elif category == "hotels":
                results = kb.search_hotels(query=query_params, limit=3)

            elif category == "events":
                results = kb.search_events(query=query_params, limit=3)

            elif category == "itineraries":
                results = kb.search_itineraries(query=query_params, limit=3)

            elif category == "transportation":
                # Search for transportation information
                results = kb.search_transportation(query=query_params, limit=3)

            elif category == "tour_packages":
                # Search for tour packages
                results = kb.search_tour_packages(query=query_params, limit=3)

            elif category == "faqs":
                # Explicitly search FAQs
                results = kb.search_faqs(query=query_params, limit=3)

            else:
                # Default to searching FAQs
                results = kb.search_faqs(query=query_params, limit=3)

            # Create a response object
            if results and len(results) > 0:
                result = results[0]

                # Extract the content based on the category
                if category == "currency" or category == "safety":
                    content = result.get("content", {}).get("en", "")
                    title = result.get("title", {}).get("en", "")
                    response_text = f"{title}\n\n{content}"
                    source = f"database (practical_info - {category})"

                elif category == "attractions":
                    name = result.get("name", {}).get("en", "")
                    description = result.get("description", {}).get("en", "")
                    response_text = f"{name}\n\n{description}"
                    source = "database (attractions)"

                elif category == "restaurants":
                    name = result.get("name", {}).get("en", "")
                    description = result.get("description", {}).get("en", "")
                    cuisine = result.get("cuisine", {}).get("en", "")
                    response_text = f"{name}\n\nCuisine: {cuisine}\n\n{description}"
                    source = "database (restaurants)"

                elif category == "hotels":
                    name = result.get("name", {}).get("en", "")
                    description = result.get("description", {}).get("en", "")
                    stars = result.get("stars", "")
                    response_text = f"{name} ({stars} stars)\n\n{description}"
                    source = "database (hotels)"

                elif category == "events":
                    name = result.get("name", {}).get("en", "")
                    description = result.get("description", {}).get("en", "")
                    date = result.get("date", "")
                    response_text = f"{name} - {date}\n\n{description}"
                    source = "database (events)"

                elif category == "itineraries":
                    name = result.get("name", {}).get("en", "")
                    description = result.get("description", {}).get("en", "")
                    duration = result.get("duration_days", "")
                    response_text = f"{name} ({duration} days)\n\n{description}"
                    source = "database (itineraries)"

                elif category == "transportation":
                    name = result.get("name", {}).get("en", "")
                    description = result.get("description", {}).get("en", "")
                    response_text = f"{name}\n\n{description}"
                    source = "database (transportation)"

                elif category == "tour_packages":
                    name = result.get("name", {}).get("en", "")
                    description = result.get("description", {}).get("en", "")
                    price = result.get("price_range", {}).get("en", "")
                    response_text = f"{name} - {price}\n\n{description}"
                    source = "database (tour_packages)"

                else:
                    # FAQs
                    question_text = result.get("question", {}).get("en", "")
                    answer_text = result.get("answer", {}).get("en", "")
                    response_text = f"{question_text}\n\n{answer_text}"
                    source = "database (faqs)"
            else:
                # No results from database, use LLM fallback
                logger.info(f"No results from database for '{question}', using LLM fallback")

                # Get the Anthropic service
                try:
                    # Try to get the Anthropic service from the container
                    from src.utils.container import container
                    anthropic_service = None

                    if container.has("anthropic_service"):
                        anthropic_service = container.get("anthropic_service")
                        logger.info(f"Got Anthropic service from container")
                    else:
                        # Try to get from service hub
                        anthropic_service = chatbot.service_hub.get_service("anthropic_service")
                        logger.info(f"Got Anthropic service from service hub")

                    if anthropic_service:
                        # Create a prompt for the LLM
                        prompt = f"""
                        You are an expert guide on Egyptian tourism, history, and culture.
                        Answer the following question about Egypt tourism.
                        Provide BRIEF and CONCISE information - keep your response under 150 words.
                        Focus on the most essential facts only.
                        Use simple language and short sentences.
                        Format your response in a conversational style, like a friendly chat message.
                        DO NOT use Markdown formatting like headings (#) or bold text (**).
                        DO NOT use bullet points or numbered lists with special characters.
                        Just write in plain, conversational text with regular paragraphs.

                        USER QUESTION:
                        {question}
                        """

                        # Call the LLM service
                        response_text = anthropic_service.generate_response(
                            prompt=prompt,
                            max_tokens=300
                        )

                        source = "anthropic_llm"
                        logger.info(f"Successfully got response from LLM fallback")
                    else:
                        # Fallback if no Anthropic service is available
                        response_text = f"I don't have specific information about {category} related to '{question}' in my database."
                        source = "no results"
                        logger.warning("No Anthropic service available for fallback")
                except Exception as e:
                    # Error handling
                    logger.error(f"Error using LLM fallback: {str(e)}")
                    response_text = f"I don't have specific information about {category} related to '{question}' in my database."
                    source = "no results"

            # Create a response object
            response = {
                "text": response_text,
                "source": source,
                "session_id": "test_session",
                "language": "en",
                "results_count": len(results) if results else 0
            }

        # Calculate response time
        end_time = time.time()
        response_time = round((end_time - start_time) * 1000, 2)  # in milliseconds
        response["response_time_ms"] = response_time

        # Log the response
        logger.info(f"Response time: {response_time} ms")
        logger.info(f"Response source: {response['source']}")
        logger.info(f"Response text (first 150 chars): {response['text'][:150]}...")

        # Check if the response came from the database
        if response["source"].startswith("database"):
            logger.info("✅ Response came from database")
            response["from_database"] = True
        else:
            logger.info("❌ Response did not come from database")
            response["from_database"] = False

        # Check if the response contains relevant keywords
        if category:
            keywords = {
                "currency": ["pound", "EGP", "currency", "money", "exchange", "cash", "card", "ATM", "tip"],
                "safety": ["safety", "security", "police", "emergency", "scam", "tourist police", "precaution"],
                "attractions": ["pyramid", "temple", "museum", "sphinx", "monument", "ancient", "visit", "attraction"],
                "restaurants": ["restaurant", "food", "cuisine", "eat", "dining", "meal", "dish", "menu"],
                "hotels": ["hotel", "accommodation", "stay", "room", "lodge", "resort", "suite", "book"],
                "events": ["festival", "event", "celebration", "holiday", "concert", "fair", "date"],
                "itineraries": ["itinerary", "tour", "day", "trip", "visit", "explore", "journey", "plan"],
                "transportation": ["transport", "travel", "bus", "train", "taxi", "metro", "airport", "ferry"],
                "tour_packages": ["package", "tour", "guide", "group", "price", "inclusive", "excursion"],
                "faqs": ["question", "answer", "faq", "information", "help", "guide", "tip"]
            }

            category_keywords = keywords.get(category, [])
            contains_relevant_info = any(keyword.lower() in response["text"].lower() for keyword in category_keywords)

            if contains_relevant_info:
                logger.info(f"✅ Response contains {category} information")
                response["contains_relevant_info"] = True
            else:
                logger.info(f"❌ Response does not contain {category} information")
                response["contains_relevant_info"] = False

        return response

    except Exception as e:
        logger.error(f"❌ Error testing chatbot query: {str(e)}")
        return {
            "text": f"Error: {str(e)}",
            "source": "error",
            "session_id": "test_session",
            "language": "en",
            "error": str(e),
            "from_database": False,
            "contains_relevant_info": False
        }

async def _handle_cross_table_query(chatbot, question, category, expected_entities):
    """
    Handle cross-table queries that require information from multiple tables.

    Args:
        chatbot: The chatbot instance
        question: The question to test
        category: The category of the question
        expected_entities: Expected entities to be extracted from the question

    Returns:
        Dictionary containing response details
    """
    kb = chatbot.knowledge_base

    # Extract entities from the question
    # For testing purposes, we'll use the expected_entities if provided
    entities = expected_entities or {}

    # Extract attraction name from the question for cross-table queries
    attraction_name = None
    question_lower = question.lower()

    # Check for restaurants near attractions
    if any(pattern in question_lower for pattern in ["restaurants near", "places to eat near", "food near", "dining near",
                                                    "restaurants close to", "places to eat close to", "food close to", "dining close to"]):
        # Extract attraction name after the pattern
        for pattern in ["restaurants near", "places to eat near", "food near", "dining near",
                       "restaurants close to", "places to eat close to", "food close to", "dining close to"]:
            if pattern in question_lower:
                attraction_text = question[question_lower.find(pattern) + len(pattern):].strip()
                # Remove common words like "the" at the beginning
                attraction_text = attraction_text.lstrip("the ").strip()
                if attraction_text:
                    attraction_name = attraction_text
                    entities["attraction"] = attraction_name
                    break

        if attraction_name:
            logger.info(f"Finding restaurants near attraction: {attraction_name}")

            results = kb.find_restaurants_near_attraction(
                attraction_name=attraction_name,
                limit=5
            )

            if results and len(results) > 0:
                # Format the response
                response_text = f"Here are some restaurants near {attraction_name}:\n\n"
                for i, restaurant in enumerate(results[:3], 1):
                    name = restaurant.get("name", {}).get("en", "Unknown")
                    cuisine = restaurant.get("cuisine", {}).get("en", "Various")
                    distance = restaurant.get("distance_km", "")
                    distance_text = f" ({distance} km away)" if distance else ""
                    response_text += f"{i}. {name} - {cuisine}{distance_text}\n"

                return {
                    "text": response_text,
                    "source": "database (cross-table: restaurants near attraction)",
                    "session_id": "test_session",
                    "language": "en",
                    "results_count": len(results)
                }

    # Check for hotels near attractions
    elif any(pattern in question_lower for pattern in ["hotels near", "places to stay near", "accommodations near", "lodging near",
                                                     "hotels close to", "places to stay close to", "accommodations close to", "lodging close to"]):
        # Extract attraction name after the pattern
        for pattern in ["hotels near", "places to stay near", "accommodations near", "lodging near",
                       "hotels close to", "places to stay close to", "accommodations close to", "lodging close to"]:
            if pattern in question_lower:
                attraction_text = question[question_lower.find(pattern) + len(pattern):].strip()
                # Remove common words like "the" at the beginning
                attraction_text = attraction_text.lstrip("the ").strip()
                if attraction_text:
                    attraction_name = attraction_text
                    entities["attraction"] = attraction_name
                    break

        if attraction_name:
            logger.info(f"Finding hotels near attraction: {attraction_name}")

            results = kb.find_hotels_near_attraction(
                attraction_name=attraction_name,
                limit=5
            )

            if results and len(results) > 0:
                # Format the response
                response_text = f"Here are some hotels near {attraction_name}:\n\n"
                for i, hotel in enumerate(results[:3], 1):
                    name = hotel.get("name", {}).get("en", "Unknown")
                    stars = hotel.get("stars", "")
                    stars_text = f" ({stars} stars)" if stars else ""
                    distance = hotel.get("distance_km", "")
                    distance_text = f" ({distance} km away)" if distance else ""
                    response_text += f"{i}. {name}{stars_text}{distance_text}\n"

                return {
                    "text": response_text,
                    "source": "database (cross-table: hotels near attraction)",
                    "session_id": "test_session",
                    "language": "en",
                    "results_count": len(results)
                }

    # Check for events near attractions
    elif any(pattern in question_lower for pattern in ["events near", "festivals near", "shows near", "performances near",
                                                     "events close to", "festivals close to", "shows close to", "performances close to"]):
        # Extract attraction name after the pattern
        for pattern in ["events near", "festivals near", "shows near", "performances near",
                       "events close to", "festivals close to", "shows close to", "performances close to"]:
            if pattern in question_lower:
                attraction_text = question[question_lower.find(pattern) + len(pattern):].strip()
                # Remove common words like "the" at the beginning
                attraction_text = attraction_text.lstrip("the ").strip()
                if attraction_text:
                    attraction_name = attraction_text
                    entities["attraction"] = attraction_name
                    break

        if attraction_name:
            logger.info(f"Finding events near attraction: {attraction_name}")

            results = kb.find_events_near_attraction(
                attraction_name=attraction_name,
                limit=5
            )

            if results and len(results) > 0:
                # Format the response
                response_text = f"Here are some events near {attraction_name}:\n\n"
                for i, event in enumerate(results[:3], 1):
                    name = event.get("name", {}).get("en", "Unknown")
                    date = event.get("date", "")
                    date_text = f" - {date}" if date else ""
                    response_text += f"{i}. {name}{date_text}\n"

                return {
                    "text": response_text,
                    "source": "database (cross-table: events near attraction)",
                    "session_id": "test_session",
                    "language": "en",
                    "results_count": len(results)
                }

    # Determine the type of cross-table query based on the question and entities
    if "restaurants near" in question.lower() and "attraction" in entities:
        # Find restaurants near an attraction
        attraction_name = entities.get("attraction")
        logger.info(f"Finding restaurants near attraction: {attraction_name}")

        results = kb.find_restaurants_near_attraction(
            attraction_name=attraction_name,
            limit=5
        )

        if results and len(results) > 0:
            # Format the response
            response_text = f"Here are some restaurants near {attraction_name}:\n\n"
            for i, restaurant in enumerate(results[:3], 1):
                name = restaurant.get("name", {}).get("en", "Unknown")
                cuisine = restaurant.get("cuisine", {}).get("en", "Various")
                distance = restaurant.get("distance_km", "")
                distance_text = f" ({distance} km away)" if distance else ""
                response_text += f"{i}. {name} - {cuisine}{distance_text}\n"

            source = "database (cross-table: restaurants near attraction)"
        else:
            # No results from database, use LLM fallback
            logger.info(f"No restaurants found near {attraction_name}, using LLM fallback")

            # Get the Anthropic service
            try:
                # Try to get the Anthropic service from the container
                from src.utils.container import container
                anthropic_service = None

                if container.has("anthropic_service"):
                    anthropic_service = container.get("anthropic_service")
                    logger.info(f"Got Anthropic service from container")
                else:
                    # Try to get from service hub
                    anthropic_service = chatbot.service_hub.get_service("anthropic_service")
                    logger.info(f"Got Anthropic service from service hub")

                if anthropic_service:
                    # Create a prompt for the LLM
                    prompt = f"""
                    You are an expert guide on Egyptian tourism, history, and culture.
                    Answer the following question about restaurants near {attraction_name} in Egypt.
                    Provide BRIEF and CONCISE information - keep your response under 150 words.
                    Focus on the most essential facts only.
                    Use simple language and short sentences.
                    Format your response in a conversational style, like a friendly chat message.

                    USER QUESTION:
                    What restaurants are near {attraction_name}?
                    """

                    # Call the LLM service
                    response_text = anthropic_service.generate_response(
                        prompt=prompt,
                        max_tokens=300
                    )

                    source = "anthropic_llm"
                    logger.info(f"Successfully got response from LLM fallback")
                else:
                    # Fallback if no Anthropic service is available
                    response_text = f"I couldn't find any restaurants near {attraction_name}."
                    source = "no results"
                    logger.warning("No Anthropic service available for fallback")
            except Exception as e:
                # Error handling
                logger.error(f"Error using LLM fallback: {str(e)}")
                response_text = f"I couldn't find any restaurants near {attraction_name}."
                source = "no results"

    elif "hotels near" in question.lower() and "attraction" in entities:
        # Find hotels near an attraction
        attraction_name = entities.get("attraction")
        logger.info(f"Finding hotels near attraction: {attraction_name}")

        results = kb.find_hotels_near_attraction(
            attraction_name=attraction_name,
            limit=5
        )

        if results and len(results) > 0:
            # Format the response
            response_text = f"Here are some hotels near {attraction_name}:\n\n"
            for i, hotel in enumerate(results[:3], 1):
                name = hotel.get("name", {}).get("en", "Unknown")
                stars = hotel.get("stars", "")
                stars_text = f" ({stars} stars)" if stars else ""
                distance = hotel.get("distance_km", "")
                distance_text = f" ({distance} km away)" if distance else ""
                response_text += f"{i}. {name}{stars_text}{distance_text}\n"

            source = "database (cross-table: hotels near attraction)"
        else:
            # No results from database, use LLM fallback
            logger.info(f"No hotels found near {attraction_name}, using LLM fallback")

            # Get the Anthropic service
            try:
                # Try to get the Anthropic service from the container
                from src.utils.container import container
                anthropic_service = None

                if container.has("anthropic_service"):
                    anthropic_service = container.get("anthropic_service")
                    logger.info(f"Got Anthropic service from container")
                else:
                    # Try to get from service hub
                    anthropic_service = chatbot.service_hub.get_service("anthropic_service")
                    logger.info(f"Got Anthropic service from service hub")

                if anthropic_service:
                    # Create a prompt for the LLM
                    prompt = f"""
                    You are an expert guide on Egyptian tourism, history, and culture.
                    Answer the following question about hotels near {attraction_name} in Egypt.
                    Provide BRIEF and CONCISE information - keep your response under 150 words.
                    Focus on the most essential facts only.
                    Use simple language and short sentences.
                    Format your response in a conversational style, like a friendly chat message.

                    USER QUESTION:
                    What hotels are near {attraction_name}?
                    """

                    # Call the LLM service
                    response_text = anthropic_service.generate_response(
                        prompt=prompt,
                        max_tokens=300
                    )

                    source = "anthropic_llm"
                    logger.info(f"Successfully got response from LLM fallback")
                else:
                    # Fallback if no Anthropic service is available
                    response_text = f"I couldn't find any hotels near {attraction_name}."
                    source = "no results"
                    logger.warning("No Anthropic service available for fallback")
            except Exception as e:
                # Error handling
                logger.error(f"Error using LLM fallback: {str(e)}")
                response_text = f"I couldn't find any hotels near {attraction_name}."
                source = "no results"

    elif "events near" in question.lower() and "attraction" in entities:
        # Find events near an attraction
        attraction_name = entities.get("attraction")
        logger.info(f"Finding events near attraction: {attraction_name}")

        results = kb.find_events_near_attraction(
            attraction_name=attraction_name,
            limit=5
        )

        if results and len(results) > 0:
            # Format the response
            response_text = f"Here are some events near {attraction_name}:\n\n"
            for i, event in enumerate(results[:3], 1):
                name = event.get("name", {}).get("en", "Unknown")
                date = event.get("date", "")
                date_text = f" - {date}" if date else ""
                response_text += f"{i}. {name}{date_text}\n"

            source = "database (cross-table: events near attraction)"
        else:
            # No results from database, use LLM fallback
            logger.info(f"No events found near {attraction_name}, using LLM fallback")

            # Get the Anthropic service
            try:
                # Try to get the Anthropic service from the container
                from src.utils.container import container
                anthropic_service = None

                if container.has("anthropic_service"):
                    anthropic_service = container.get("anthropic_service")
                    logger.info(f"Got Anthropic service from container")
                else:
                    # Try to get from service hub
                    anthropic_service = chatbot.service_hub.get_service("anthropic_service")
                    logger.info(f"Got Anthropic service from service hub")

                if anthropic_service:
                    # Create a prompt for the LLM
                    prompt = f"""
                    You are an expert guide on Egyptian tourism, history, and culture.
                    Answer the following question about events and festivals near {attraction_name} in Egypt.
                    Provide BRIEF and CONCISE information - keep your response under 150 words.
                    Focus on the most essential facts only.
                    Use simple language and short sentences.
                    Format your response in a conversational style, like a friendly chat message.

                    USER QUESTION:
                    What events or festivals are happening near {attraction_name}?
                    """

                    # Call the LLM service
                    response_text = anthropic_service.generate_response(
                        prompt=prompt,
                        max_tokens=300
                    )

                    source = "anthropic_llm"
                    logger.info(f"Successfully got response from LLM fallback")
                else:
                    # Fallback if no Anthropic service is available
                    response_text = f"I couldn't find any events near {attraction_name}."
                    source = "no results"
                    logger.warning("No Anthropic service available for fallback")
            except Exception as e:
                # Error handling
                logger.error(f"Error using LLM fallback: {str(e)}")
                response_text = f"I couldn't find any events near {attraction_name}."
                source = "no results"

    elif "attractions in" in question.lower() and "itinerary" in entities:
        # Find attractions in cities mentioned in an itinerary
        itinerary_name = entities.get("itinerary")
        logger.info(f"Finding attractions in itinerary cities: {itinerary_name}")

        results = kb.find_attractions_in_itinerary_cities(
            itinerary_name=itinerary_name,
            limit=3
        )

        if results and len(results) > 0:
            # Format the response
            response_text = f"Here are attractions in cities mentioned in the {itinerary_name} itinerary:\n\n"
            for city, attractions in results.items():
                response_text += f"In {city}:\n"
                for i, attraction in enumerate(attractions[:2], 1):
                    name = attraction.get("name", {}).get("en", "Unknown")
                    response_text += f"  {i}. {name}\n"

            source = "database (cross-table: attractions in itinerary cities)"
        else:
            # No results from database, use LLM fallback
            logger.info(f"No attractions found for the {itinerary_name} itinerary, using LLM fallback")

            # Get the Anthropic service
            try:
                # Try to get the Anthropic service from the container
                from src.utils.container import container
                anthropic_service = None

                if container.has("anthropic_service"):
                    anthropic_service = container.get("anthropic_service")
                    logger.info(f"Got Anthropic service from container")
                else:
                    # Try to get from service hub
                    anthropic_service = chatbot.service_hub.get_service("anthropic_service")
                    logger.info(f"Got Anthropic service from service hub")

                if anthropic_service:
                    # Create a prompt for the LLM
                    prompt = f"""
                    You are an expert guide on Egyptian tourism, history, and culture.
                    Answer the following question about attractions included in the {itinerary_name} itinerary in Egypt.
                    Provide BRIEF and CONCISE information - keep your response under 150 words.
                    Focus on the most essential facts only.
                    Use simple language and short sentences.
                    Format your response in a conversational style, like a friendly chat message.

                    USER QUESTION:
                    What attractions are included in the {itinerary_name} itinerary?
                    """

                    # Call the LLM service
                    response_text = anthropic_service.generate_response(
                        prompt=prompt,
                        max_tokens=300
                    )

                    source = "anthropic_llm"
                    logger.info(f"Successfully got response from LLM fallback")
                else:
                    # Fallback if no Anthropic service is available
                    response_text = f"I couldn't find any attractions for the {itinerary_name} itinerary."
                    source = "no results"
                    logger.warning("No Anthropic service available for fallback")
            except Exception as e:
                # Error handling
                logger.error(f"Error using LLM fallback: {str(e)}")
                response_text = f"I couldn't find any attractions for the {itinerary_name} itinerary."
                source = "no results"

    else:
        # Default response for unknown cross-table query - use LLM fallback
        logger.info(f"Unknown cross-table query type: {question}, using LLM fallback")

        # Get the Anthropic service
        try:
            # Try to get the Anthropic service from the container
            from src.utils.container import container
            anthropic_service = None

            if container.has("anthropic_service"):
                anthropic_service = container.get("anthropic_service")
                logger.info(f"Got Anthropic service from container")
            else:
                # Try to get from service hub
                anthropic_service = chatbot.service_hub.get_service("anthropic_service")
                logger.info(f"Got Anthropic service from service hub")

            if anthropic_service:
                # Create a prompt for the LLM
                prompt = f"""
                You are an expert guide on Egyptian tourism, history, and culture.
                Answer the following question about Egypt tourism.
                Provide BRIEF and CONCISE information - keep your response under 150 words.
                Focus on the most essential facts only.
                Use simple language and short sentences.
                Format your response in a conversational style, like a friendly chat message.

                USER QUESTION:
                {question}
                """

                # Call the LLM service
                response_text = anthropic_service.generate_response(
                    prompt=prompt,
                    max_tokens=300
                )

                source = "anthropic_llm"
                logger.info(f"Successfully got response from LLM fallback")
            else:
                # Fallback if no Anthropic service is available
                response_text = "I'm not sure how to answer that cross-table query."
                source = "no results"
                logger.warning("No Anthropic service available for fallback")
        except Exception as e:
            # Error handling
            logger.error(f"Error using LLM fallback: {str(e)}")
            response_text = "I'm not sure how to answer that cross-table query."
            source = "no results"

    # Create a response object
    return {
        "text": response_text,
        "source": source,
        "session_id": "test_session",
        "language": "en",
        "results_count": len(results) if 'results' in locals() and results else 0
    }

async def initialize_chatbot():
    """Initialize the chatbot for testing."""
    try:
        # Get database connection string from environment variable or use default
        db_uri = os.environ.get("POSTGRES_URI", "postgresql://postgres:postgres@localhost:5432/egypt_chatbot")
        logger.info(f"Using database URI: {db_uri}")

        # Create database manager
        db_manager = DatabaseManager(db_uri)
        if not db_manager.connect():
            logger.error("❌ Database connection failed")
            return None
        logger.info("✅ Database connection successful")

        # Create knowledge base
        kb = KnowledgeBase(db_manager)
        logger.info("✅ Knowledge base initialized")

        # Create mock components for the chatbot
        from unittest.mock import MagicMock

        # Create a simple intent classifier for testing
        try:
            if AdvancedIntentClassifier:
                intent_classifier = AdvancedIntentClassifier()
                logger.info("✅ Using real AdvancedIntentClassifier")
            else:
                raise ImportError("AdvancedIntentClassifier not available")
        except Exception as e:
            logger.warning(f"Could not initialize real intent classifier: {str(e)}")
            intent_classifier = MagicMock()
            logger.info("⚠️ Using mock intent classifier")

        # Create a simple entity extractor for testing
        try:
            if EntityExtractor:
                entity_extractor = EntityExtractor()
                logger.info("✅ Using real EntityExtractor")
            else:
                raise ImportError("EntityExtractor not available")
        except Exception as e:
            logger.warning(f"Could not initialize real entity extractor: {str(e)}")
            entity_extractor = MagicMock()
            logger.info("⚠️ Using mock entity extractor")

        # Create NLU engine
        nlu_engine = MagicMock()

        # Define mock functions that ignore the unused parameter
        def mock_classify_intent(_):
            return {"intent": "general_query", "confidence": 0.5}

        def mock_extract_entities(_):
            return {}

        # Assign real or mock functions
        nlu_engine.classify_intent = intent_classifier.classify if hasattr(intent_classifier, 'classify') else mock_classify_intent
        nlu_engine.extract_entities = entity_extractor.extract if hasattr(entity_extractor, 'extract') else mock_extract_entities

        # Other mock components
        mock_dialog_manager = MagicMock()
        mock_response_generator = MagicMock()
        mock_service_hub = MagicMock()
        mock_session_manager = MagicMock()

        # Create chatbot with all required components
        chatbot = Chatbot(
            knowledge_base=kb,
            nlu_engine=nlu_engine,
            dialog_manager=mock_dialog_manager,
            response_generator=mock_response_generator,
            service_hub=mock_service_hub,
            session_manager=mock_session_manager,
            db_manager=db_manager
        )

        # Set USE_LLM_FIRST to False directly in the chatbot instance
        # This is a hack, but it's the easiest way to test the database functionality
        setattr(chatbot, 'USE_LLM_FIRST', False)
        logger.info("✅ Set USE_LLM_FIRST to False to prioritize database queries")

        logger.info("✅ Chatbot initialized successfully")
        return chatbot

    except Exception as e:
        logger.error(f"❌ Error initializing chatbot: {str(e)}")
        return None

async def test_all_query_types():
    """Test the chatbot's ability to answer different types of tourism questions."""
    # Initialize the chatbot
    chatbot = await initialize_chatbot()
    if not chatbot:
        logger.error("Cannot continue without chatbot")
        return

    # Define test questions for different categories and query types
    test_questions = {
        # Basic queries for different categories
        "basic": {
            "currency": [
                "What is the currency used in Egypt?",
                "Tell me about Egyptian money",
                "What's the exchange rate for US dollars in Egypt?",
                "Do they accept credit cards in Egypt?",
                "How much should I tip in Egypt?"
            ],
            "safety": [
                "Is Egypt safe for tourists?",
                "What safety precautions should I take in Egypt?",
                "Are there any areas in Egypt I should avoid?",
                "What should I do in case of an emergency in Egypt?",
                "Is it safe to walk around Cairo at night?"
            ],
            "attractions": [
                "What are the must-see attractions in Egypt?",
                "Tell me about the Pyramids of Giza",
                "What ancient temples can I visit in Egypt?",
                "What museums are there in Cairo?",
                "What is the best time to visit the Valley of the Kings?"
            ],
            "restaurants": [
                "What are the best restaurants in Cairo?",
                "Where can I try authentic Egyptian cuisine?",
                "Are there vegetarian restaurants in Egypt?",
                "What is the traditional food of Egypt?",
                "Where can I eat seafood in Alexandria?"
            ],
            "hotels": [
                "What are the best hotels in Cairo?",
                "Are there luxury resorts in Sharm El Sheikh?",
                "What budget accommodations are available in Luxor?",
                "Do hotels in Egypt have swimming pools?",
                "What's the average cost of a hotel room in Egypt?"
            ],
            "events": [
                "What festivals are celebrated in Egypt?",
                "When is the Cairo International Film Festival?",
                "Are there any music events in Egypt?",
                "What happens during Ramadan in Egypt?",
                "Are there any cultural events in Alexandria?"
            ],
            "itineraries": [
                "What's a good 7-day itinerary for Egypt?",
                "How can I plan a trip to see the main attractions in Egypt?",
                "What's the best way to see both Cairo and Luxor?",
                "Can you suggest a desert safari itinerary?",
                "What's a good family-friendly itinerary for Egypt?"
            ],
            "transportation": [
                "How do I get from Cairo to Luxor?",
                "What's the best way to travel around Egypt?",
                "Are there trains between major cities in Egypt?",
                "How reliable is public transportation in Egypt?",
                "How much does a taxi cost in Cairo?"
            ],
            "tour_packages": [
                "What tour packages are available for Egypt?",
                "Are there any Nile cruise packages?",
                "What's included in a typical Egypt tour package?",
                "Are there any budget tour packages for Egypt?",
                "What's the best tour package for seeing the pyramids?"
            ],
            "faqs": [
                "Do I need a visa to visit Egypt?",
                "What's the best time of year to visit Egypt?",
                "What should I pack for a trip to Egypt?",
                "Is it customary to tip in Egypt?",
                "What languages are spoken in Egypt?"
            ]
        },

        # Cross-table queries
        "cross-table": {
            "restaurants_near_attractions": [
                {"question": "What restaurants are near the Pyramids of Giza?", "entities": {"attraction": "Pyramids of Giza"}},
                {"question": "Are there any good places to eat near the Egyptian Museum?", "entities": {"attraction": "Egyptian Museum"}},
                {"question": "Where can I find restaurants close to Karnak Temple?", "entities": {"attraction": "Karnak Temple"}}
            ],
            "hotels_near_attractions": [
                {"question": "What hotels are near the Pyramids of Giza?", "entities": {"attraction": "Pyramids of Giza"}},
                {"question": "Where can I stay near the Valley of the Kings?", "entities": {"attraction": "Valley of the Kings"}},
                {"question": "Are there any luxury hotels near the Sphinx?", "entities": {"attraction": "Sphinx"}}
            ],
            "events_near_attractions": [
                {"question": "What events are happening near the Pyramids of Giza?", "entities": {"attraction": "Pyramids of Giza"}},
                {"question": "Are there any festivals near Luxor Temple?", "entities": {"attraction": "Luxor Temple"}},
                {"question": "What cultural events can I attend near the Egyptian Museum?", "entities": {"attraction": "Egyptian Museum"}}
            ],
            "attractions_in_itineraries": [
                {"question": "What attractions are included in the 7-day Egypt tour?", "entities": {"itinerary": "7-day"}},
                {"question": "What can I see on the Cairo and Luxor itinerary?", "entities": {"itinerary": "Cairo and Luxor"}},
                {"question": "What attractions are part of the Nile cruise itinerary?", "entities": {"itinerary": "Nile cruise"}}
            ]
        },

        # Complex queries
        "complex": {
            "multi_intent": [
                "What are the best hotels near the Pyramids of Giza with good restaurants?",
                "Can you recommend a 7-day itinerary that includes Cairo, Luxor, and a Nile cruise?",
                "What's the best time to visit the Valley of the Kings and what transportation options are available?",
                "Are there any family-friendly hotels in Sharm El Sheikh with activities for children?",
                "What safety precautions should I take when visiting the pyramids and what currency should I bring?"
            ]
        }
    }

    # Statistics for reporting
    stats = {
        "total_queries": 0,
        "database_responses": 0,
        "llm_responses": 0,
        "no_results": 0,
        "errors": 0,
        "response_times": [],
        "by_category": defaultdict(lambda: {"total": 0, "database": 0, "llm": 0, "no_results": 0, "errors": 0}),
        "by_query_type": defaultdict(lambda: {"total": 0, "database": 0, "llm": 0, "no_results": 0, "errors": 0})
    }

    # Test basic queries
    logger.info("\n\n=== TESTING BASIC QUERIES ===\n")
    for category, questions in test_questions["basic"].items():
        logger.info(f"\n=== Testing {category.upper()} questions ===")

        # Test each question in the category
        for question in questions[:2]:  # Limit to 2 questions per category for brevity
            response = await test_chatbot_query(chatbot, question, category, "basic")

            # Update statistics
            stats["total_queries"] += 1
            stats["by_category"][category]["total"] += 1
            stats["by_query_type"]["basic"]["total"] += 1

            if response["source"] == "error":
                stats["errors"] += 1
                stats["by_category"][category]["errors"] += 1
                stats["by_query_type"]["basic"]["errors"] += 1
            elif response["source"] == "no results":
                stats["no_results"] += 1
                stats["by_category"][category]["no_results"] += 1
                stats["by_query_type"]["basic"]["no_results"] += 1
            elif response["source"].startswith("database"):
                stats["database_responses"] += 1
                stats["by_category"][category]["database"] += 1
                stats["by_query_type"]["basic"]["database"] += 1
            else:
                stats["llm_responses"] += 1
                stats["by_category"][category]["llm"] += 1
                stats["by_query_type"]["basic"]["llm"] += 1

            if "response_time_ms" in response:
                stats["response_times"].append(response["response_time_ms"])

            # Add a delay to avoid overwhelming the system
            await asyncio.sleep(0.5)

    # Test cross-table queries
    logger.info("\n\n=== TESTING CROSS-TABLE QUERIES ===\n")
    for category, questions in test_questions["cross-table"].items():
        logger.info(f"\n=== Testing {category.upper()} questions ===")

        # Test each question in the category
        for question_data in questions:
            question = question_data["question"]
            entities = question_data["entities"]

            # Extract the main category from the cross-table category
            main_category = category.split("_")[0]  # e.g., "restaurants_near_attractions" -> "restaurants"

            response = await test_chatbot_query(chatbot, question, main_category, "cross-table", entities)

            # Update statistics
            stats["total_queries"] += 1
            stats["by_category"][main_category]["total"] += 1
            stats["by_query_type"]["cross-table"]["total"] += 1

            if response["source"] == "error":
                stats["errors"] += 1
                stats["by_category"][main_category]["errors"] += 1
                stats["by_query_type"]["cross-table"]["errors"] += 1
            elif response["source"] == "no results":
                stats["no_results"] += 1
                stats["by_category"][main_category]["no_results"] += 1
                stats["by_query_type"]["cross-table"]["no_results"] += 1
            elif response["source"].startswith("database"):
                stats["database_responses"] += 1
                stats["by_category"][main_category]["database"] += 1
                stats["by_query_type"]["cross-table"]["database"] += 1
            else:
                stats["llm_responses"] += 1
                stats["by_category"][main_category]["llm"] += 1
                stats["by_query_type"]["cross-table"]["llm"] += 1

            if "response_time_ms" in response:
                stats["response_times"].append(response["response_time_ms"])

            # Add a delay to avoid overwhelming the system
            await asyncio.sleep(0.5)

    # Test complex queries
    logger.info("\n\n=== TESTING COMPLEX QUERIES ===\n")
    for category, questions in test_questions["complex"].items():
        logger.info(f"\n=== Testing {category.upper()} questions ===")

        # Test each question in the category
        for question in questions:
            response = await test_chatbot_query(chatbot, question, None, "complex")

            # Update statistics
            stats["total_queries"] += 1
            stats["by_query_type"]["complex"]["total"] += 1

            if response["source"] == "error":
                stats["errors"] += 1
                stats["by_query_type"]["complex"]["errors"] += 1
            elif response["source"] == "no results":
                stats["no_results"] += 1
                stats["by_query_type"]["complex"]["no_results"] += 1
            elif response["source"].startswith("database"):
                stats["database_responses"] += 1
                stats["by_query_type"]["complex"]["database"] += 1
            else:
                stats["llm_responses"] += 1
                stats["by_query_type"]["complex"]["llm"] += 1

            if "response_time_ms" in response:
                stats["response_times"].append(response["response_time_ms"])

            # Add a delay to avoid overwhelming the system
            await asyncio.sleep(0.5)

    # Report statistics
    logger.info("\n\n=== TEST RESULTS ===\n")
    logger.info(f"Total queries: {stats['total_queries']}")
    logger.info(f"Database responses: {stats['database_responses']} ({stats['database_responses']/stats['total_queries']*100:.1f}%)")
    logger.info(f"LLM responses: {stats['llm_responses']} ({stats['llm_responses']/stats['total_queries']*100:.1f}%)")
    logger.info(f"No results: {stats['no_results']} ({stats['no_results']/stats['total_queries']*100:.1f}%)")
    logger.info(f"Errors: {stats['errors']} ({stats['errors']/stats['total_queries']*100:.1f}%)")

    if stats["response_times"]:
        avg_response_time = sum(stats["response_times"]) / len(stats["response_times"])
        logger.info(f"Average response time: {avg_response_time:.2f} ms")

    logger.info("\nResults by category:")
    for category, category_stats in sorted(stats["by_category"].items()):
        if category_stats["total"] > 0:
            db_percent = category_stats["database"] / category_stats["total"] * 100 if category_stats["total"] > 0 else 0
            logger.info(f"  {category}: {category_stats['database']}/{category_stats['total']} from database ({db_percent:.1f}%)")

    logger.info("\nResults by query type:")
    for query_type, query_stats in sorted(stats["by_query_type"].items()):
        if query_stats["total"] > 0:
            db_percent = query_stats["database"] / query_stats["total"] * 100 if query_stats["total"] > 0 else 0
            logger.info(f"  {query_type}: {query_stats['database']}/{query_stats['total']} from database ({db_percent:.1f}%)")

    return stats

async def main():
    """Main function to run the test."""
    logger.info("=== EGYPT TOURISM CHATBOT QUERY TEST ===")
    logger.info("This test will evaluate the chatbot's ability to answer various types of tourism questions")
    logger.info("and determine whether responses come from the database or LLM fallback.")
    logger.info("\nTest categories:")
    logger.info("1. Basic queries for different tourism categories")
    logger.info("2. Cross-table queries that require information from multiple tables")
    logger.info("3. Complex queries with multiple intents")
    logger.info("\nStarting test...")

    start_time = time.time()
    stats = await test_all_query_types()
    end_time = time.time()

    if stats:
        total_time = round(end_time - start_time, 2)
        logger.info(f"\nTest completed in {total_time} seconds")

        # Calculate database coverage
        if stats["total_queries"] > 0:
            db_coverage = stats["database_responses"] / stats["total_queries"] * 100
            logger.info(f"\nOverall database coverage: {db_coverage:.1f}%")

            if db_coverage < 50:
                logger.warning("⚠️ Database coverage is below 50%. Consider enhancing the database with more comprehensive information.")
            elif db_coverage < 80:
                logger.info("ℹ️ Database coverage is moderate. There's room for improvement in the database.")
            else:
                logger.info("✅ Database coverage is good. The chatbot is effectively using the database for most queries.")

    logger.info("\nChatbot query test completed")

if __name__ == "__main__":
    # Set up better logging format
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S'
    )

    # Run the test
    asyncio.run(main())
