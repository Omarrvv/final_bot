"""
LLM fallback mechanism for the Egypt Tourism Chatbot.
Provides a consistent way to fall back to LLM when database queries fail.
"""

import logging
import json
import time
from typing import Dict, Any, Optional, List, Union, Tuple
# PHASE 0C FIX: Remove direct import from services layer to maintain architectural boundaries

# Configure logging
logger = logging.getLogger(__name__)

class LLMFallbackHandler:
    """
    LLM fallback handler for the Egypt Tourism Chatbot.
    """

    def __init__(self, anthropic_service: Optional[Any] = None):
        """
        Initialize the LLM fallback handler.

        Args:
            anthropic_service: Anthropic service instance (injected via container)
        """
        # PHASE 0C FIX: Use dependency injection from container instead of direct instantiation
        if anthropic_service is None:
            try:
                from src.core.container import container
                self.anthropic_service = container.get("anthropic_service")
            except Exception as e:
                logger.warning(f"Failed to get anthropic_service from container: {e}")
                self.anthropic_service = None
        else:
            self.anthropic_service = anthropic_service

        # Tourism knowledge for context
        self.tourism_context = """
        Egypt is a country in North Africa known for its ancient civilization, pyramids, and Nile River.
        Major cities include Cairo (capital), Alexandria, Luxor, Aswan, Hurghada, and Sharm El Sheikh.
        Popular attractions include the Pyramids of Giza, the Sphinx, Karnak Temple, Valley of the Kings,
        Abu Simbel, the Egyptian Museum, and Red Sea resorts.
        The official language is Arabic, but English is widely spoken in tourist areas.
        The currency is the Egyptian Pound (EGP).
        The best time to visit is from October to April when temperatures are milder.
        """

    def handle_query_failure(self, query: str, intent: str,
                           entities: Dict[str, Any], error: Optional[Exception] = None,
                           max_retries: int = 2) -> Dict[str, Any]:
        """
        Handle a failed database query by falling back to LLM.

        Args:
            query: Original user query
            intent: Detected intent
            entities: Extracted entities
            error: Exception that caused the failure
            max_retries: Maximum number of retry attempts for LLM

        Returns:
            LLM response
        """
        logger.info(f"Handling query failure with LLM fallback: {query}")
        if error:
            logger.error(f"Original error: {str(error)}")
            # Log detailed error information for debugging
            logger.debug(f"Error type: {type(error).__name__}")
            if hasattr(error, '__traceback__'):
                import traceback
                logger.debug(f"Traceback: {traceback.format_tb(error.__traceback__)}")

        # Create a prompt for the LLM
        prompt = self._create_fallback_prompt(query, intent, entities)

        # Implement retry logic
        for attempt in range(max_retries + 1):
            try:
                # Check if anthropic service is available
                if not self.anthropic_service:
                    logger.warning("Anthropic service not available, using generic fallback")
                    raise Exception("Anthropic service unavailable")
                
                # Get response from Anthropic with limited tokens
                response = self.anthropic_service.generate_response(prompt, max_tokens=100)

                # Format the response
                return {
                    "source": "llm_fallback",
                    "content": response,
                    "intent": intent,
                    "entities": entities,
                    "timestamp": time.time(),
                    "fallback": True,
                    "error_handled": True if error else False
                }
            except Exception as e:
                logger.error(f"Error in LLM fallback (attempt {attempt+1}/{max_retries+1}): {str(e)}")
                if attempt < max_retries:
                    # Wait before retrying (exponential backoff)
                    retry_delay = 0.5 * (2 ** attempt)  # 0.5s, 1s, 2s, etc.
                    logger.info(f"Retrying in {retry_delay:.1f} seconds...")
                    time.sleep(retry_delay)
                else:
                    # All retries failed, return generic response
                    logger.warning(f"All {max_retries+1} attempts to get LLM fallback failed")
                    return {
                        "source": "generic_fallback",
                        "content": self._get_generic_fallback_response(intent),
                        "intent": intent,
                        "entities": entities,
                        "timestamp": time.time(),
                        "fallback": True,
                        "error_handled": True
                    }

    def _create_fallback_prompt(self, query: str, intent: str, entities: Dict[str, Any]) -> str:
        """
        Create a prompt for the LLM fallback.

        Args:
            query: Original user query
            intent: Detected intent
            entities: Extracted entities

        Returns:
            Formatted prompt
        """
        # Format entities for the prompt
        entities_str = ", ".join([f"{k}: {v}" for k, v in entities.items()]) if entities else "None"

        # Add intent-specific context
        intent_context = self._get_intent_specific_context(intent, entities)

        # Create the prompt - UPDATED FOR BREVITY
        prompt = f"""
        You are an expert Egypt tourism assistant. The user has asked a question, but our database couldn't provide an answer.
        Please provide a VERY BRIEF response based on your knowledge about Egypt tourism.

        Context about Egypt:
        {self.tourism_context}

        Additional context based on the query type:
        {intent_context}

        User query: {query}
        Detected intent: {intent}
        Detected entities: {entities_str}

        KEEP YOUR RESPONSE EXTREMELY BRIEF - under 50 words maximum.
        Focus ONLY on the most essential facts.
        Use simple language and short sentences.
        Format your response in a conversational style without using markdown.

        Your response:
        """

        return prompt

    def _get_intent_specific_context(self, intent: str, entities: Dict[str, Any] = None) -> str:
        """
        Get additional context specific to the intent.

        Args:
            intent: Detected intent
            entities: Extracted entities (optional, for future use with entity-specific context)

        Returns:
            Intent-specific context
        """
        # Note: entities parameter is reserved for future enhancements
        # where we might provide more specific context based on entities
        # Map intents to specific context
        intent_contexts = {
            "attraction_info": """
                Egypt's major attractions include the Pyramids of Giza, the Sphinx, Karnak Temple,
                Luxor Temple, Valley of the Kings, Abu Simbel, the Egyptian Museum, and Islamic Cairo.
                Most historical sites are open from 8 AM to 5 PM, with some variations by season.
                Photography is usually allowed but may require a permit at some locations.
                Many sites have entrance fees ranging from 50-200 EGP for foreign visitors.
            """,

            "restaurant_info": """
                Egyptian cuisine features dishes like koshari (rice, pasta, lentils with tomato sauce),
                ful medames (fava beans), molokhia (jute leaf stew), and various grilled meats.
                Restaurants in tourist areas typically open from 11 AM to midnight.
                Tipping (10-15%) is customary in restaurants.
                Many restaurants in tourist areas accept credit cards, but smaller local places may be cash-only.
            """,

            "hotel_info": """
                Egypt offers accommodation ranging from luxury resorts to budget hostels.
                Major hotel chains are present in Cairo, Alexandria, Luxor, and Red Sea resorts.
                Peak season (October-April) typically has higher rates.
                Many hotels offer amenities like pools, restaurants, and tour booking services.
                Booking in advance is recommended during high season.
            """,

            "practical_info": """
                Visa: Most visitors need a visa, available on arrival ($25) or through Egyptian embassies.
                Currency: Egyptian Pound (EGP), with ATMs widely available in tourist areas.
                Weather: Hot summers (May-September) and mild winters (October-April).
                Transportation: Taxis, Uber, and public transport available in major cities.
                Safety: Tourist areas are generally safe but normal precautions are advised.
                Language: Arabic is official, but English is widely spoken in tourist areas.
                Electricity: 220V, European-style plugs (types C and F).
            """,

            "event_query": """
                Major events include the Abu Simbel Sun Festival (February and October),
                Cairo International Film Festival (November-December),
                Ramadan celebrations (varies by Islamic calendar),
                Coptic Christmas (January 7),
                and various music festivals throughout the year.
                Many cultural events take place at the Cairo Opera House and cultural centers.
            """,

            "itinerary_query": """
                Popular itineraries include:
                - Classic Egypt (7-10 days): Cairo, Luxor, Aswan
                - Nile Cruise (3-7 days): Luxor to Aswan or vice versa
                - Red Sea Getaway (4-7 days): Hurghada or Sharm El Sheikh
                - Complete Egypt (14+ days): Combining historical sites and beach resorts
                Most visitors spend 2-3 days in Cairo, 2-3 days in Luxor, and 1-2 days in Aswan.
            """
        }

        # Return the appropriate context or a default one
        return intent_contexts.get(intent, """
            Egypt is known for its ancient civilization, pyramids, and the Nile River.
            The country offers a mix of historical sites, beach resorts, and cultural experiences.
            Major tourist destinations include Cairo, Luxor, Aswan, Alexandria, and Red Sea resorts.
        """)

    def _get_generic_fallback_response(self, intent: str) -> str:
        """
        Get a generic fallback response based on intent.

        Args:
            intent: Detected intent

        Returns:
            Generic fallback response
        """
        # Map intents to generic responses
        intent_responses = {
            "attraction_info": "I don't have specific details about that attraction at the moment. Egypt has many fascinating historical sites including the Pyramids of Giza, Karnak Temple, Valley of the Kings, and Abu Simbel. Would you like information about these popular attractions instead?",

            "restaurant_info": "I don't have specific details about that restaurant at the moment. Egyptian cuisine offers delicious options like koshari, ful medames, molokhia, and various grilled meats. Most tourist areas have a range of dining options from local to international cuisine.",

            "hotel_info": "I don't have specific details about that accommodation at the moment. Egypt offers a wide range of accommodation options from luxury resorts to budget hostels in all major tourist destinations. Would you like recommendations for popular areas to stay?",

            "practical_info": "For practical information about visiting Egypt, it's good to know that the currency is the Egyptian Pound, Arabic is the official language (though English is widely spoken in tourist areas), and the best time to visit is from October to April. Visitors typically need a visa, which can often be obtained on arrival or in advance.",

            "event_query": "I don't have specific details about that event at the moment. Egypt hosts various cultural festivals throughout the year, including the Abu Simbel Sun Festival, Cairo International Film Festival, and various religious celebrations. Would you like to know about the major annual events?",

            "itinerary_query": "I don't have a specific itinerary to recommend at the moment. A typical Egypt trip often includes Cairo (for the Pyramids and Egyptian Museum), Luxor (for Karnak Temple and Valley of the Kings), and potentially Aswan or a Nile cruise. Many visitors also enjoy the Red Sea resorts like Hurghada or Sharm El Sheikh. How many days are you planning to visit?",
        }

        # Return the appropriate response or a default one
        return intent_responses.get(intent, "I don't have that specific information at the moment. Egypt offers a rich cultural heritage, ancient monuments, beautiful beaches, and diverse experiences for travelers. Could you please clarify what you'd like to know about Egypt?")

    def enhance_database_response(self, query: str, db_response: Dict[str, Any],
                                intent: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance a database response with LLM-generated content.

        Args:
            query: Original user query
            db_response: Database response
            intent: Detected intent
            entities: Extracted entities

        Returns:
            Enhanced response
        """
        logger.info(f"Enhancing database response with LLM: {query}")

        # Extract the database content
        db_content = db_response.get("content", "")

        # Create a prompt for enhancement - UPDATED FOR BREVITY
        prompt = f"""
        You are an expert Egypt tourism assistant. The user has asked a question, and our database has provided some information.
        Please enhance this information to create a VERY BRIEF and conversational response.

        User query: {query}
        Detected intent: {intent}
        Detected entities: {", ".join([f"{k}: {v}" for k, v in entities.items()]) if entities else "None"}

        Database information:
        {db_content}

        Please create an enhanced response that:
        1. Maintains all factual information from the database
        2. Is EXTREMELY BRIEF - under 50 words maximum
        3. Uses simple language and short sentences
        4. Is conversational and directly answers the user's query

        Your enhanced response:
        """

        try:
            # Get enhanced response from Anthropic with limited tokens
            enhanced_response = self.anthropic_service.generate_response(prompt, max_tokens=100)

            # Update the response
            enhanced_db_response = db_response.copy()
            enhanced_db_response["content"] = enhanced_response
            enhanced_db_response["enhanced"] = True

            return enhanced_db_response
        except Exception as e:
            logger.error(f"Error enhancing response with LLM: {str(e)}")
            # Return the original response if enhancement fails
            return db_response
