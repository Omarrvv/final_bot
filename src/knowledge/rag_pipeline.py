"""
Retrieval-Augmented Generation (RAG) pipeline for the Egypt Tourism Chatbot.
Enhances responses with knowledge base information by semantic search and retrieval.
"""
import logging
import re
import json
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)

class RAGPipeline:
    """
    Retrieval-Augmented Generation (RAG) pipeline for generating responses
    based on content retrieved from the knowledge base.
    """

    def __init__(self, knowledge_base, vector_db=None, embedding_model=None,
               llm_service=None, config: Optional[Dict] = None):
        """
        Initialize the RAG pipeline.

        Args:
            knowledge_base: Knowledge base for retrieval
            vector_db: Vector database for semantic search
            embedding_model: Model for embedding queries
            llm_service: LLM service for generation
            config (Dict, optional): Configuration options
        """
        self.knowledge_base = knowledge_base
        self.vector_db = vector_db
        self.embedding_model = embedding_model
        self.llm_service = llm_service
        self.config = config or {}

        # Configuration options
        self.max_chunks = self.config.get("max_chunks", 5)
        self.min_similarity = self.config.get("min_similarity", 0.6)
        self.context_window = self.config.get("context_window", 2000)

    def generate_response(self, query: str, session_id: str, language: str = "en") -> Dict[str, Any]:
        """
        Main method for generating a response using the RAG pipeline.

        Args:
            query (str): User query
            session_id (str): Session identifier
            language (str): Language code (en, ar)

        Returns:
            Dict: Generated response with retrieved context
        """
        logger.info(f"Generating RAG response for query: {query}")

        try:
            # Get context from any active session
            context = {}

            # Process the query through the general processing method
            # Assuming a general intent to start with
            intent = "general_query"
            response = self._process_general_query(query, intent, context, language)

            # Add session ID to the response
            response["session_id"] = session_id

            return response
        except Exception as e:
            logger.error(f"Error generating RAG response: {str(e)}")
            return {
                "text": f"I'm sorry, I encountered an error processing your query about '{query}'.",
                "session_id": session_id,
                "language": language,
                "error": str(e),
                "response_type": "error",
            }

    def process(self, query: str, intent: str, context: Dict[str, Any],
             language: str = "en") -> Dict[str, Any]:
        """
        Process a query using the RAG pipeline.

        Args:
            query (str): User query
            intent (str): Detected intent
            context (Dict): Conversation context
            language (str): Language code

        Returns:
            Dict: Generated response with retrieved context
        """
        # Extract entities from context
        entities = context.get("entities", {})

        # Determine retrieval strategy based on intent
        if intent in ["attraction_info", "attraction_history", "attraction_details"]:
            return self._process_attraction_query(query, intent, entities, context, language)
        elif intent in ["hotel_query", "hotel_booking", "hotel_info"]:
            return self._process_hotel_query(query, intent, entities, context, language)
        elif intent in ["restaurant_query", "food_info", "restaurant_booking"]:
            return self._process_restaurant_query(query, intent, entities, context, language)
        elif intent in ["transportation_info", "practical_info", "travel_advice"]:
            return self._process_practical_query(query, intent, entities, context, language)
        else:
            # For general queries, use semantic search
            return self._process_general_query(query, intent, context, language)

    def _process_attraction_query(self, query: str, intent: str, entities: Dict,
                              context: Dict, language: str) -> Dict[str, Any]:
        """
        Process a query about attractions.

        Args:
            query (str): User query
            intent (str): Detected intent
            entities (Dict): Extracted entities
            context (Dict): Conversation context
            language (str): Language code

        Returns:
            Dict: Generated response
        """
        # Check if we have an attraction entity
        attraction_name = None
        if "attraction" in entities and entities["attraction"]:
            attraction_name = entities["attraction"][0]

        # If no explicit attraction, check context
        if not attraction_name:
            active_entities = self._get_active_entities(context)
            if "attraction" in active_entities and active_entities["attraction"]:
                attraction_name = active_entities["attraction"][0]

        # If we have an attraction, fetch its details
        if attraction_name:
            try:
                attraction = self.knowledge_base.lookup_attraction(attraction_name, language)

                if attraction:
                    # Create a response based on the attraction details
                    return self._generate_attraction_response(query, attraction, intent, language)
                else:
                    # Attraction not found, try a semantic search
                    logger.info(f"Attraction '{attraction_name}' not found, using semantic search")
                    return self._process_general_query(query, intent, context, language)
            except Exception as e:
                logger.error(f"Error processing attraction query: {str(e)}")
                return self._get_fallback_response(language, query, context)
        else:
            # No specific attraction mentioned, use search
            return self._search_attractions(query, intent, entities, language)

    def _process_hotel_query(self, query: str, intent: str, entities: Dict,
                         context: Dict, language: str) -> Dict[str, Any]:
        """
        Process a query about hotels.

        Args:
            query (str): User query
            intent (str): Detected intent
            entities (Dict): Extracted entities
            context (Dict): Conversation context
            language (str): Language code

        Returns:
            Dict: Generated response
        """
        # Similar to _process_attraction_query but for hotels
        hotel_name = None
        if "hotel" in entities and entities["hotel"]:
            hotel_name = entities["hotel"][0]

        if not hotel_name:
            active_entities = self._get_active_entities(context)
            if "hotel" in active_entities and active_entities["hotel"]:
                hotel_name = active_entities["hotel"][0]

        if hotel_name:
            try:
                hotel = self.knowledge_base.lookup_hotel(hotel_name, language)

                if hotel:
                    return self._generate_hotel_response(query, hotel, intent, language)
                else:
                    logger.info(f"Hotel '{hotel_name}' not found, using semantic search")
                    return self._process_general_query(query, intent, context, language)
            except Exception as e:
                logger.error(f"Error processing hotel query: {str(e)}")
                return self._get_fallback_response(language, query, context)
        else:
            return self._search_hotels(query, intent, entities, language)

    def _process_restaurant_query(self, query: str, intent: str, entities: Dict,
                              context: Dict, language: str) -> Dict[str, Any]:
        """
        Process a query about restaurants.

        Args:
            query (str): User query
            intent (str): Detected intent
            entities (Dict): Extracted entities
            context (Dict): Conversation context
            language (str): Language code

        Returns:
            Dict: Generated response
        """
        # Similar to _process_attraction_query but for restaurants
        restaurant_name = None
        if "restaurant" in entities and entities["restaurant"]:
            restaurant_name = entities["restaurant"][0]

        if not restaurant_name:
            active_entities = self._get_active_entities(context)
            if "restaurant" in active_entities and active_entities["restaurant"]:
                restaurant_name = active_entities["restaurant"][0]

        if restaurant_name:
            try:
                restaurant = self.knowledge_base.lookup_restaurant(restaurant_name, language)

                if restaurant:
                    return self._generate_restaurant_response(query, restaurant, intent, language)
                else:
                    logger.info(f"Restaurant '{restaurant_name}' not found, using semantic search")
                    return self._process_general_query(query, intent, context, language)
            except Exception as e:
                logger.error(f"Error processing restaurant query: {str(e)}")
                return self._get_fallback_response(language)
        else:
            return self._search_restaurants(query, intent, entities, language)

    def _process_practical_query(self, query: str, intent: str, entities: Dict,
                             context: Dict, language: str) -> Dict[str, Any]:
        """
        Process a query about practical information.

        Args:
            query (str): User query
            intent (str): Detected intent
            entities (Dict): Extracted entities
            context (Dict): Conversation context
            language (str): Language code

        Returns:
            Dict: Generated response
        """
        try:
            # Check for specific practical info categories
            if "visa" in query.lower() or "passport" in query.lower():
                return self._generate_practical_response(query, "visa", language)
            elif "weather" in query.lower() or "climate" in query.lower():
                return self._generate_practical_response(query, "weather", language)
            elif "currency" in query.lower() or "money" in query.lower() or "exchange" in query.lower():
                return self._generate_practical_response(query, "currency", language)
            elif "safety" in query.lower() or "safe" in query.lower() or "security" in query.lower():
                return self._generate_practical_response(query, "safety", language)
            elif "transport" in query.lower() or "bus" in query.lower() or "train" in query.lower() or "taxi" in query.lower():
                return self._generate_practical_response(query, "transportation", language)
            else:
                # General practical info
                return self._generate_practical_response(query, "general", language)
        except Exception as e:
            logger.error(f"Error processing practical query: {str(e)}")
            return self._get_fallback_response(language)

    def _process_general_query(self, query: str, intent: str, context: Dict,
                           language: str) -> Dict[str, Any]:
        """
        Process a general query using semantic search.

        Args:
            query (str): User query
            intent (str): Detected intent
            context (Dict): Conversation context
            language (str): Language code

        Returns:
            Dict: Generated response
        """
        try:
            # Check if we have vector DB and embedding model
            if not self.vector_db or not self.embedding_model:
                logger.warning("Vector DB or embedding model not available, using fallback")
                return self._get_fallback_response(language, query, context)

            # Get query embedding
            query_embedding = self.embedding_model.encode([query])[0]

            # Search for relevant content
            search_results = self.vector_db.search(
                collection="general_content",
                query_vector=query_embedding,
                limit=self.max_chunks
            )

            if not search_results:
                logger.info("No vector search results found")
                return self._get_fallback_response(language, query, context)

            # Filter results by similarity threshold
            filtered_results = []
            for item_id, similarity in search_results:
                if similarity >= self.min_similarity:
                    filtered_results.append((item_id, similarity))

            if not filtered_results:
                logger.info("No vector search results above similarity threshold")
                return self._get_fallback_response(language, query, context)

            # Fetch content chunks
            content_chunks = []
            for item_id, similarity in filtered_results:
                try:
                    chunk = self.knowledge_base.get_content_chunk(item_id)
                    if chunk:
                        content_chunks.append(chunk)
                except Exception as e:
                    logger.error(f"Error fetching content chunk {item_id}: {str(e)}")

            if not content_chunks:
                return self._get_fallback_response(language, query, context)

            # Generate response from content
            return self._generate_from_content_chunks(query, content_chunks, intent, language)

        except Exception as e:
            logger.error(f"Error in general query processing: {str(e)}")
            return self._get_fallback_response(language, query, context)

    def _search_attractions(self, query: str, intent: str, entities: Dict,
                        language: str) -> Dict[str, Any]:
        """
        Search for attractions matching the query.

        Args:
            query (str): User query
            intent (str): Detected intent
            entities (Dict): Extracted entities
            language (str): Language code

        Returns:
            Dict: Generated response with search results
        """
        try:
            # Extract location if present
            location = None
            if "location" in entities and entities["location"]:
                location = entities["location"][0]

            # Prepare search filters
            filters = {}
            if location:
                filters["location"] = location

            # Extract other potential filters from entities
            if "type" in entities and entities["type"]:
                filters["type"] = entities["type"][0]

            # Search for attractions
            attractions = self.knowledge_base.search_attractions(
                query=query,
                filters=filters,
                language=language,
                limit=5
            )

            if not attractions:
                logger.info("No attractions found")

                if location:
                    return {
                        "text": self._get_no_attractions_message(location, language),
                        "attractions": []
                    }
                else:
                    return self._get_fallback_response(language)

            # Generate response with attraction list
            return self._generate_attraction_list_response(attractions, location, language)

        except Exception as e:
            logger.error(f"Error searching attractions: {str(e)}")
            return self._get_fallback_response(language)

    def _search_hotels(self, query: str, intent: str, entities: Dict,
                    language: str) -> Dict[str, Any]:
        """
        Search for hotels matching the query.

        Args:
            query (str): User query
            intent (str): Detected intent
            entities (Dict): Extracted entities
            language (str): Language code

        Returns:
            Dict: Generated response with search results
        """
        # Similar to _search_attractions but for hotels
        try:
            # Extract location if present
            location = None
            if "location" in entities and entities["location"]:
                location = entities["location"][0]

            # Prepare search filters
            filters = {}
            if location:
                filters["location"] = location

            # Extract other potential filters
            if "hotel_class" in entities and entities["hotel_class"]:
                filters["hotel_class"] = entities["hotel_class"][0]

            # Search for hotels
            hotels = self.knowledge_base.search_hotels(
                query=query,
                filters=filters,
                language=language,
                limit=5
            )

            if not hotels:
                logger.info("No hotels found")

                if location:
                    return {
                        "text": self._get_no_hotels_message(location, language),
                        "hotels": []
                    }
                else:
                    return self._get_fallback_response(language)

            # Generate response with hotel list
            return self._generate_hotel_list_response(hotels, location, language)

        except Exception as e:
            logger.error(f"Error searching hotels: {str(e)}")
            return self._get_fallback_response(language)

    def _search_restaurants(self, query: str, intent: str, entities: Dict,
                        language: str) -> Dict[str, Any]:
        """
        Search for restaurants matching the query.

        Args:
            query (str): User query
            intent (str): Detected intent
            entities (Dict): Extracted entities
            language (str): Language code

        Returns:
            Dict: Generated response with search results
        """
        # Similar to _search_attractions but for restaurants
        try:
            # Extract location if present
            location = None
            if "location" in entities and entities["location"]:
                location = entities["location"][0]

            # Prepare search filters
            filters = {}
            if location:
                filters["location"] = location

            # Extract other potential filters
            if "cuisine" in entities and entities["cuisine"]:
                filters["cuisine"] = entities["cuisine"][0]

            # Search for restaurants
            restaurants = self.knowledge_base.search_restaurants(
                query=query,
                filters=filters,
                language=language,
                limit=5
            )

            if not restaurants:
                logger.info("No restaurants found")

                if location:
                    return {
                        "text": self._get_no_restaurants_message(location, language),
                        "restaurants": []
                    }
                else:
                    return self._get_fallback_response(language)

            # Generate response with restaurant list
            return self._generate_restaurant_list_response(restaurants, location, language)

        except Exception as e:
            logger.error(f"Error searching restaurants: {str(e)}")
            return self._get_fallback_response(language)

    def _generate_attraction_response(self, query: str, attraction: Dict,
                                  intent: str, language: str) -> Dict[str, Any]:
        """
        Generate a response about a specific attraction.

        Args:
            query (str): User query
            attraction (Dict): Attraction data
            intent (str): Detected intent
            language (str): Language code

        Returns:
            Dict: Generated response
        """
        try:
            # Get attraction name in the appropriate language
            name = attraction["name"].get(language, attraction["name"].get("en", "Unknown Attraction"))

            # Determine what information to include based on the query and intent
            if "history" in query.lower() or intent == "attraction_history":
                # Focus on history
                description = attraction.get("history", {}).get(language,
                    attraction.get("history", {}).get("en", ""))

                response_text = f"**{name}** - *Historical Background*\n\n{description}"

            elif "practical" in query.lower() or "visit" in query.lower() or "hours" in query.lower():
                # Focus on practical info
                practical_info = attraction.get("practical_info", {})

                # Compile practical information
                opening_hours = practical_info.get("opening_hours", "Not specified")
                ticket_prices = practical_info.get("ticket_prices", {})
                best_time = practical_info.get("best_time_to_visit", "")
                duration = practical_info.get("duration", "")

                price_text = ""
                if ticket_prices:
                    if "foreigners" in ticket_prices:
                        price_text += f"Foreigners: Adults - {ticket_prices['foreigners'].get('adults', '')}, "
                        price_text += f"Students - {ticket_prices['foreigners'].get('students', '')}\n"
                    if "egyptians" in ticket_prices:
                        price_text += f"Egyptians: Adults - {ticket_prices['egyptians'].get('adults', '')}, "
                        price_text += f"Students - {ticket_prices['egyptians'].get('students', '')}\n"

                response_text = f"**{name}** - *Visitor Information*\n\n"
                response_text += f"**Opening Hours**: {opening_hours}\n\n"

                if price_text:
                    response_text += f"**Ticket Prices**:\n{price_text}\n"

                if best_time:
                    response_text += f"**Best Time to Visit**: {best_time}\n\n"

                if duration:
                    response_text += f"**Recommended Duration**: {duration}\n\n"

                facilities = practical_info.get("facilities", [])
                if facilities:
                    response_text += f"**Facilities**: {', '.join(facilities)}\n\n"

                tips = practical_info.get("visitor_tips", {}).get(language,
                    practical_info.get("visitor_tips", {}).get("en", ""))

                if tips:
                    response_text += f"**Visitor Tips**: {tips}"

            else:
                # General information
                description = attraction.get("description", {}).get(language,
                    attraction.get("description", {}).get("en", ""))

                response_text = f"**{name}**\n\n{description}"

            # Add media if available
            media = []
            if "images" in attraction and attraction["images"]:
                # Add first few images
                for i, image_url in enumerate(attraction["images"][:3]):
                    media.append({
                        "type": "image",
                        "url": image_url,
                        "alt": f"{name} - Image {i+1}"
                    })

            # Add map if coordinates available
            if "location" in attraction and "coordinates" in attraction["location"]:
                coords = attraction["location"]["coordinates"]
                if "latitude" in coords and "longitude" in coords:
                    map_url = f"https://maps.google.com/maps?q={coords['latitude']},{coords['longitude']}&z=15&output=embed"
                    media.append({
                        "type": "map",
                        "url": map_url,
                        "alt": f"Map of {name}"
                    })

            return {
                "text": response_text,
                "attraction": attraction,
                "media": media
            }

        except Exception as e:
            logger.error(f"Error generating attraction response: {str(e)}")
            return {
                "text": f"Here's information about {name}. Unfortunately, some details are unavailable right now."
            }

    # Additional methods for other types would be similar

    def _generate_from_content_chunks(self, query: str, chunks: List[Dict],
                                   intent: str, language: str) -> Dict[str, Any]:
        """
        Generate a response from retrieved content chunks.

        Args:
            query (str): User query
            chunks (List[Dict]): Retrieved content chunks
            intent (str): Detected intent
            language (str): Language code

        Returns:
            Dict: Generated response
        """
        try:
            # If we have an LLM service, use it to generate a response
            if self.llm_service:
                # Prepare context from chunks
                context_text = "\n\n".join([chunk.get("content", "") for chunk in chunks])

                # Truncate context if it's too long
                if len(context_text) > self.context_window:
                    context_text = context_text[:self.context_window]

                # Create prompt with query and context
                language_label = "English" if language == "en" else "Arabic"

                prompt = f"""
                Based on the following information about Egypt tourism, please answer the user's question.
                Respond in {language_label}.

                INFORMATION:
                {context_text}

                USER QUESTION:
                {query}

                RESPONSE:
                """

                # Call LLM service
                llm_result = self.llm_service.execute_service(
                    method="generate",
                    params={
                        "prompt": prompt,
                        "max_tokens": 500,
                        "temperature": 0.7
                    }
                )

                # Extract response text
                response_text = llm_result.get("text", "")

                if not response_text:
                    logger.warning("LLM returned empty response")
                    return self._get_fallback_response(language)

                return {
                    "text": response_text,
                    "sources": [chunk.get("source", "") for chunk in chunks if "source" in chunk]
                }
            else:
                # No LLM service, create a basic response from the chunks
                response_parts = []

                # Use first few chunks to create response
                for i, chunk in enumerate(chunks[:3]):
                    content = chunk.get("content", "")
                    title = chunk.get("title", f"Information {i+1}")

                    # Only use first paragraph of each chunk to keep it concise
                    paragraphs = content.split("\n\n")
                    if paragraphs:
                        first_para = paragraphs[0]
                        response_parts.append(f"**{title}**\n\n{first_para}")

                response_text = "\n\n".join(response_parts)

                return {
                    "text": response_text,
                    "sources": [chunk.get("source", "") for chunk in chunks if "source" in chunk]
                }

        except Exception as e:
            logger.error(f"Error generating response from content chunks: {str(e)}")
            return self._get_fallback_response(language)

    def _get_active_entities(self, context: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Get active entities from context for reference resolution.

        Args:
            context (Dict): Conversation context

        Returns:
            Dict: Active entities by type
        """
        # Simple implementation - just return entities from context
        return context.get("entities", {})

    def _get_fallback_response(self, language: str, query: str = None, session_data: Dict = None) -> Dict[str, Any]:
        """
        Get a fallback response when no information is available.
        Uses Anthropic LLM if available, otherwise returns a generic message.

        Args:
            language (str): Language code
            query (str, optional): The original user query
            session_data (Dict, optional): Session data containing conversation history

        Returns:
            Dict: Fallback response
        """
        # If we have an LLM service and a query, use it to generate a response
        if self.llm_service and query:
            logger.info(f"Using Anthropic LLM for fallback response to: {query}")

            try:
                # Check if the LLM service has the fallback method
                if hasattr(self.llm_service, 'generate_fallback_response'):
                    # Use the specialized fallback method
                    fallback_response = self.llm_service.generate_fallback_response(
                        query=query,
                        language=language,
                        session_data=session_data
                    )

                    # Add source information
                    fallback_response["source"] = "anthropic_llm"
                    fallback_response["fallback"] = True

                    return fallback_response
                else:
                    # Use the general execute_service method
                    language_label = "English" if language == "en" else "Arabic"

                    prompt = f"""
                    You are an expert guide on Egyptian tourism, history, and culture.
                    Answer the following question about Egypt tourism.
                    Respond in {language_label}.

                    USER QUESTION:
                    {query}
                    """

                    llm_result = self.llm_service.execute_service(
                        method="generate",
                        params={
                            "prompt": prompt,
                            "max_tokens": 500,
                            "temperature": 0.7
                        }
                    )

                    # Extract response text
                    response_text = llm_result.get("text", "")

                    if response_text:
                        return {
                            "text": response_text,
                            "source": "anthropic_llm",
                            "fallback": True
                        }
            except Exception as e:
                logger.error(f"Error using LLM for fallback: {str(e)}")
                # Continue to default fallback if LLM fails

        # Default fallback messages if LLM is not available or fails
        if language == "ar":
            return {
                "text": "عذراً، لا يمكنني العثور على معلومات كافية للإجابة على هذا السؤال. هل يمكنك طرح سؤالك بطريقة مختلفة؟",
                "fallback": True
            }
        else:
            return {
                "text": "I'm sorry, I couldn't find enough information to answer this question. Could you try asking in a different way?",
                "fallback": True
            }

    def _get_no_attractions_message(self, location: str, language: str) -> str:
        """Get message for when no attractions are found at a location."""
        if language == "ar":
            return f"عذراً، لم أتمكن من العثور على معالم سياحية في {location}. هل تريد البحث في مكان آخر؟"
        else:
            return f"I couldn't find any attractions in {location}. Would you like to search for attractions in another area?"

    def _get_no_hotels_message(self, location: str, language: str) -> str:
        """Get message for when no hotels are found at a location."""
        if language == "ar":
            return f"عذراً، لم أتمكن من العثور على فنادق في {location}. هل تريد البحث في مكان آخر؟"
        else:
            return f"I couldn't find any hotels in {location}. Would you like to search for hotels in another area?"

    def _get_no_restaurants_message(self, location: str, language: str) -> str:
        """Get message for when no restaurants are found at a location."""
        if language == "ar":
            return f"عذراً، لم أتمكن من العثور على مطاعم في {location}. هل تريد البحث في مكان آخر؟"
        else:
            return f"I couldn't find any restaurants in {location}. Would you like to search for restaurants in another area?"

    # Additional helper methods would be implemented here