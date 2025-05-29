"""
Retrieval-Augmented Generation (RAG) pipeline for the Egypt Tourism Chatbot.
Enhances responses with knowledge base information by semantic search and retrieval.
"""
import logging
import re
import json
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import time
import hashlib

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
        self.cache_enabled = self.config.get("cache_enabled", True)

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

            # Extract entities from the query
            entities = self._extract_entities(query)
            logger.info(f"Extracted entities: {entities}")

            # Check for location entity
            if "location" in entities and entities["location"]:
                location = entities["location"][0]
                logger.info(f"Found location entity: {location}")

                # Search for attractions at this location
                # First get the city_id for the location
                city = self.knowledge_base.lookup_location(location, language)
                city_id = city.get("city_id") if city else None

                attractions = self.knowledge_base.search_attractions(
                    query="",
                    filters={"city_id": city_id} if city_id else {},
                    language=language,
                    limit=5
                )

                if attractions:
                    logger.info(f"Found {len(attractions)} attractions for location: {location}")
                    response_text = f"Here are some top attractions in {location}:\n\n"

                    for idx, attraction in enumerate(attractions, 1):
                        # Get name and description from JSONB fields
                        name = self._get_text_by_language(attraction.get("name"), "en") or "Unknown"
                        description = self._get_text_by_language(attraction.get("description"), "en") or "No description available."
                        # Shorten description if too long
                        if len(description) > 100:
                            description = description[:100] + "..."
                        response_text += f"{idx}. **{name}**: {description}\n\n"

                    return {
                        "text": response_text,
                        "session_id": session_id,
                        "language": language,
                        "response_type": "attraction_list",
                        "attractions": attractions
                    }

            # Process the query through the general processing method
            # Assuming a general intent to start with
            intent = "general_query"
            response = self._process_general_query(query, intent, context, language)

            # Add session ID to the response
            response["session_id"] = session_id
            response["language"] = language
            response["response_type"] = "general_info"

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

    def _extract_entities(self, query: str) -> Dict[str, List[str]]:
        """Extract entities from the query text."""
        entities = {}

        # Simple location extraction - look for common Egyptian cities
        cities = ["Cairo", "Alexandria", "Luxor", "Aswan", "Giza", "Hurghada",
                 "Sharm El Sheikh", "Dahab"]

        for city in cities:
            if city.lower() in query.lower():
                if "location" not in entities:
                    entities["location"] = []
                entities["location"].append(city)

        # Simple attraction extraction
        attractions = ["Pyramid", "Sphinx", "Museum", "Temple", "Nile"]
        for attraction in attractions:
            if attraction.lower() in query.lower():
                if "attraction" not in entities:
                    entities["attraction"] = []
                entities["attraction"].append(attraction)

        return entities

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
                return self._get_fallback_response(language)
        else:
            # No specific attraction mentioned, use search
            return self._search_attractions(query, intent, entities, language)

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
            # If we don't have vector DB and embedding model, try direct DB query
            location_entities = self._extract_entities(query).get("location", [])

            if location_entities:
                location = location_entities[0]
                # Search for attractions in this location
                # First get the city_id for the location
                city = self.knowledge_base.lookup_location(location, language)
                city_id = city.get("city_id") if city else None

                attractions = self.knowledge_base.search_attractions(
                    query="",
                    filters={"city_id": city_id} if city_id else {},
                    language=language,
                    limit=5
                )

                if attractions:
                    logger.info(f"Found {len(attractions)} attractions for location: {location}")
                    response_text = f"Here are some top attractions in {location}:\n\n"

                    for idx, attraction in enumerate(attractions, 1):
                        # Get name and description from JSONB fields
                        name = self._get_text_by_language(attraction.get("name"), "en") or "Unknown"
                        description = self._get_text_by_language(attraction.get("description"), "en") or "No description available."
                        # Shorten description if too long
                        if len(description) > 100:
                            description = description[:100] + "..."
                        response_text += f"{idx}. **{name}**: {description}\n\n"

                    return {
                        "text": response_text,
                        "attractions": attractions
                    }

            # Check if we have vector DB and embedding model
            if not self.vector_db or not self.embedding_model:
                logger.warning("Vector DB or embedding model not available, using fallback")
                return self._get_fallback_response(language)

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
                return self._get_fallback_response(language)

            # Filter results by similarity threshold
            filtered_results = []
            for item_id, similarity in search_results:
                if similarity >= self.min_similarity:
                    filtered_results.append((item_id, similarity))

            if not filtered_results:
                logger.info("No vector search results above similarity threshold")
                return self._get_fallback_response(language)

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
                return self._get_fallback_response(language)

            # Generate response from content
            return self._generate_from_content_chunks(query, content_chunks, intent, language)

        except Exception as e:
            logger.error(f"Error in general query processing: {str(e)}")
            return self._get_fallback_response(language)

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
                # Get city_id for the location
                city = self.knowledge_base.lookup_location(location, language)
                city_id = city.get("city_id") if city else None
                if city_id:
                    filters["city_id"] = city_id

            # Extract other potential filters from entities
            if "type" in entities and entities["type"]:
                # Get type_id for the type
                type_name = entities["type"][0]
                # This would need a lookup method for types
                # For now, we'll just use the type name
                filters["type"] = type_name

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

    def _generate_attraction_list_response(self, attractions, location, language):
        """Generate a response listing attractions."""
        location_text = f" in {location}" if location else ""

        if language == "ar":
            response_text = f"إليك بعض المعالم السياحية الشهيرة{location_text}:\n\n"
        else:
            response_text = f"Here are some popular attractions{location_text}:\n\n"

        for idx, attraction in enumerate(attractions, 1):
            # Get name and description from JSONB fields using the appropriate language
            name = self._get_text_by_language(attraction.get("name"), language) or "Unknown"
            description = self._get_text_by_language(attraction.get("description"), language) or ""

            # Trim description if too long
            if description and len(description) > 100:
                description = description[:100] + "..."

            response_text += f"{idx}. **{name}**: {description}\n\n"

        return {
            "text": response_text,
            "attractions": attractions
        }

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

    def _get_fallback_response(self, language: str) -> Dict[str, Any]:
        """
        Get a fallback response when no information is available.

        Args:
            language (str): Language code

        Returns:
            Dict: Fallback response
        """
        if language == "ar":
            return {
                "text": "عذراً، لا يمكنني العثور على معلومات كافية للإجابة على هذا السؤال. هل يمكنك طرح سؤالك بطريقة مختلفة؟"
            }
        else:
            return {
                "text": "I'm sorry, I couldn't find enough information to answer this question. Could you try asking in a different way?"
            }

    def _get_no_attractions_message(self, location: str, language: str) -> str:
        """Get message for when no attractions are found at a location."""
        if language == "ar":
            return f"عذراً، لم أتمكن من العثور على معالم سياحية في {location}. هل تريد البحث في مكان آخر؟"
        else:
            return f"I couldn't find any attractions in {location}. Would you like to search for attractions in another area?"

    def _get_text_by_language(self, jsonb_field: Any, language: str = "en") -> str:
        """
        Get text from a JSONB field for a specific language.

        Args:
            jsonb_field: JSONB field containing multilingual text
            language: Language code (en, ar)

        Returns:
            str: Text for the specified language or empty string if not found
        """
        if not jsonb_field:
            return ""

        # If it's a string, try to parse it as JSON
        if isinstance(jsonb_field, str):
            try:
                jsonb_field = json.loads(jsonb_field)
            except json.JSONDecodeError:
                return jsonb_field

        # If it's a dictionary, get the text for the specified language
        if isinstance(jsonb_field, dict):
            return jsonb_field.get(language, "")

        # If it's not a dictionary or string, return empty string
        return ""

    def retrieve_content(self, query: str, limit: int = 5, use_hybrid: bool = True,
                         content_types: List[str] = None, rerank: bool = True,
                         search_threshold: float = 0.65) -> List[Dict]:
        """
        Enhanced retrieval function that leverages hybrid search and optional reranking

        Args:
            query: The user query to search for
            limit: Maximum number of results to return
            use_hybrid: Whether to use hybrid search (vector + keyword) or just vector search
            content_types: List of content types to search (e.g., ['restaurants', 'hotels'])
            rerank: Whether to rerank results after retrieval
            search_threshold: Minimum similarity score threshold

        Returns:
            List of relevant content items
        """
        start_time = time.time()

        # Get embedding for the query
        query_embedding = self.get_query_embedding(query)

        if not content_types:
            content_types = ['attractions', 'restaurants', 'hotels', 'cities', 'tours', 'practical_info']

        all_results = []

        # Set cache key
        cache_key = f"rag_{hashlib.md5(query.encode()).hexdigest()}_{'_'.join(content_types)}"

        # Try to get from cache first
        if self.cache_enabled:
            cached_results = self.get_from_cache(cache_key)
            if cached_results:
                logger.info(f"Retrieved results for '{query}' from cache")
                return cached_results

        for content_type in content_types:
            try:
                # Determine search method based on content type and use_hybrid flag
                if use_hybrid:
                    # Use hybrid search combining vector and keyword search
                    method_name = f"hybrid_search_{content_type}"
                    search_method = getattr(self.db_manager, method_name, None)

                    if search_method:
                        results = search_method(
                            query=query,
                            embedding=query_embedding,
                            limit=limit,
                            threshold=search_threshold
                        )
                    else:
                        # Fallback to basic vector search if hybrid not implemented
                        logger.warning(f"Hybrid search not implemented for {content_type}, falling back to vector search")
                        method_name = f"vector_search_{content_type}"
                        search_method = getattr(self.db_manager, method_name, None)
                        if search_method:
                            results = search_method(
                                embedding=query_embedding,
                                limit=limit,
                                threshold=search_threshold
                            )
                        else:
                            logger.warning(f"Vector search not implemented for {content_type}")
                            continue
                else:
                    # Use pure vector search
                    method_name = f"vector_search_{content_type}"
                    search_method = getattr(self.db_manager, method_name, None)
                    if search_method:
                        results = search_method(
                            embedding=query_embedding,
                            limit=limit,
                            threshold=search_threshold
                        )
                    else:
                        logger.warning(f"Vector search not implemented for {content_type}")
                        continue

                # Tag results with their source
                for result in results:
                    result['source'] = content_type
                    result['source_type'] = 'database'

                all_results.extend(results)

            except Exception as e:
                logger.error(f"Error retrieving {content_type} content: {str(e)}")

        # Rerank results if requested
        if rerank and all_results and len(all_results) > 1:
            all_results = self.rerank_results(query, all_results)

        # Sort by similarity score (higher is better)
        all_results = sorted(all_results, key=lambda x: x.get('similarity', 0), reverse=True)

        # Limit total results
        all_results = all_results[:limit]

        # Save to cache if enabled
        if self.cache_enabled:
            self.save_to_cache(cache_key, all_results)

        duration = time.time() - start_time
        logger.info(f"RAG retrieval completed in {duration:.2f}s with {len(all_results)} results")

        return all_results

    def rerank_results(self, query: str, results: List[Dict]) -> List[Dict]:
        """
        Reranks results based on multiple factors including:
        - Query-text relevance
        - Geographic proximity (if applicable)
        - User preferences (if available)
        - Content freshness

        Args:
            query: Original user query
            results: List of search results to rerank

        Returns:
            Reranked results list
        """
        try:
            # Extract query terms for text matching
            query_terms = set(self._preprocess_text(query))

            for result in results:
                # Start with original similarity score (0-1)
                base_score = result.get('similarity', 0)

                # Check for text match boost using title and description
                text_match_score = 0
                title = result.get('title', '')
                description = result.get('description', '')

                if title or description:
                    # Calculate term overlap with query
                    title_terms = set(self._preprocess_text(title))
                    desc_terms = set(self._preprocess_text(description))
                    all_terms = title_terms.union(desc_terms)

                    # Calculate overlap ratio (Jaccard similarity)
                    if query_terms and all_terms:
                        overlap = len(query_terms.intersection(all_terms))
                        text_match_score = overlap / len(query_terms) * 0.15  # Max 15% boost

                # Final reranked score (base + text match boost)
                result['original_similarity'] = base_score
                result['similarity'] = min(1.0, base_score + text_match_score)
                result['reranked'] = True

            return results

        except Exception as e:
            logger.error(f"Error during result reranking: {str(e)}")
            # Return original results if reranking fails
            return results

    def _preprocess_text(self, text: str) -> List[str]:
        """Simple preprocessing for text matching"""
        if not text:
            return []

        # Convert to lowercase and remove punctuation
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)

        # Split into words and remove stopwords
        words = text.split()
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'in',
                     'to', 'for', 'of', 'with', 'by', 'at', 'from'}
        words = [w for w in words if w not in stopwords]

        return words
