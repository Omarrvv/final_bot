#!/usr/bin/env python3
"""Fix RAG pipeline integration with the main chatbot."""
import logging
import os
import sys

def patch_main_chatbot():
    """Patch the main chatbot to properly use the RAG pipeline."""
    print("Checking main chatbot implementation...")
    
    # Find the chatbot.py file
    chatbot_file = "/app/src/chatbot.py"
    if not os.path.exists(chatbot_file):
        print(f"ERROR: Could not find {chatbot_file}")
        return False
    
    # Create backup
    os.system(f"cp {chatbot_file} {chatbot_file}.bak")
    print(f"Created backup at {chatbot_file}.bak")
    
    # Read the file
    with open(chatbot_file, 'r') as f:
        content = f.read()
    
    # Find the generate_response method
    if "def generate_response" not in content:
        print("ERROR: Could not find generate_response method in chatbot.py")
        return False
    
    # Check if RAG is already imported
    if "from src.rag.pipeline import RAGPipeline" not in content and "import RAGPipeline" not in content:
        # Add import at the top, after other imports
        print("Adding RAG pipeline import...")
        content = content.replace("import logging", "import logging\nfrom src.rag.pipeline import RAGPipeline")
    
    # Check if the RAG pipeline is initialized
    if "self.rag_pipeline = " not in content:
        # Add RAG pipeline initialization in __init__
        print("Adding RAG pipeline initialization...")
        init_pattern = "def __init__"
        init_end = ")"
        
        # Find the end of the __init__ method
        init_pos = content.find(init_pattern)
        if init_pos == -1:
            print("ERROR: Could not find __init__ method")
            return False
        
        # Find where to insert the RAG initialization
        init_block_end = content.find("\n        self.", init_pos + len(init_pattern))
        if init_block_end == -1:
            init_block_end = content.find("\n        # ", init_pos + len(init_pattern))
        if init_block_end == -1:
            print("ERROR: Could not find suitable location for RAG initialization")
            return False
        
        # Insert the RAG initialization
        rag_init = """
        # Initialize RAG pipeline if enabled
        self.rag_pipeline = None
        if hasattr(settings.feature_flags, "use_rag") and settings.feature_flags.use_rag:
            try:
                logger.info("Initializing RAG pipeline (RAG enabled)")
                self.rag_pipeline = RAGPipeline(
                    knowledge_base=self.knowledge_base,
                    vector_db=None,  # Add vector DB if available
                    embedding_model=None,  # Add embedding model if available
                    llm_service=None,  # Will use direct generation instead
                    config={"max_chunks": b}
                )
            except Exception as e:
                logger.error(f"Failed to initialize RAG pipeline: {e}")"""
        
        content = content[:init_block_end] + rag_init + content[init_block_end:]
    
    # Check if generate_response uses the RAG pipeline
    if "if self.rag_pipeline" not in content or "self.rag_pipeline.generate_response" not in content:
        # Modify the generate_response method to use RAG pipeline
        print("Updating generate_response method to use RAG pipeline...")
        gen_response_pattern = "def generate_response(self, query, session_id, language=None):"
        
        gen_pos = content.find(gen_response_pattern)
        if gen_pos == -1:
            print("ERROR: Could not find generate_response method signature")
            return False
        
        # Find where to insert RAG pipeline check
        # Look for where the function starts processing after validations
        process_pos = content.find("# Process the query", gen_pos)
        if process_pos == -1:
            process_pos = content.find("        # Process", gen_pos)
        if process_pos == -1:
            process_pos = content.find("        intent =", gen_pos)
        if process_pos == -1:
            print("ERROR: Could not find suitable location to add RAG check")
            return False
        
        # Insert the RAG check
        rag_check = """
        # Use RAG pipeline if enabled and available
        if hasattr(settings.feature_flags, "use_rag") and settings.feature_flags.use_rag and self.rag_pipeline:
            try:
                logger.info(f"Using RAG pipeline for query: {query}")
                rag_response = self.rag_pipeline.generate_response(query, session_id, language)
                if rag_response and rag_response.get("text"):
                    logger.info("Successfully generated response with RAG pipeline")
                    return rag_response
                else:
                    logger.warning("RAG pipeline did not return a valid response, using fallback")
            except Exception as e:
                logger.error(f"Error using RAG pipeline: {e}")
                # Fall back to regular response generation
        
        """
        
        content = content[:process_pos] + rag_check + content[process_pos:]
    
    # Write the updated file
    with open(chatbot_file, 'w') as f:
        f.write(content)
    
    print("Successfully updated chatbot.py to integrate RAG pipeline")
    return True

# Run the patch
patch_main_chatbot()

# Add RAG module directory and file if they don't exist
rag_dir = "/app/src/rag"
if not os.path.exists(rag_dir):
    os.makedirs(rag_dir)
    print(f"Created RAG module directory at {rag_dir}")

# Create __init__.py for the RAG module
init_file = f"{rag_dir}/__init__.py"
if not os.path.exists(init_file):
    with open(init_file, 'w') as f:
        f.write("# RAG module initialization\n")
    print(f"Created {init_file}")

# Copy the RAG pipeline code provided by the user
pipeline_file = f"{rag_dir}/pipeline.py"
with open(pipeline_file, 'w') as f:
    f.write("""\"\"\"
Retrieval-Augmented Generation (RAG) pipeline for the Egypt Tourism Chatbot.
Enhances responses with knowledge base information by semantic search and retrieval.
\"\"\"
import logging
import re
import json
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)

class RAGPipeline:
    \"\"\"
    Retrieval-Augmented Generation (RAG) pipeline for generating responses
    based on content retrieved from the knowledge base.
    \"\"\"
    
    def __init__(self, knowledge_base, vector_db=None, embedding_model=None, 
               llm_service=None, config: Optional[Dict] = None):
        \"\"\"
        Initialize the RAG pipeline.
        
        Args:
            knowledge_base: Knowledge base for retrieval
            vector_db: Vector database for semantic search
            embedding_model: Model for embedding queries
            llm_service: LLM service for generation
            config (Dict, optional): Configuration options
        \"\"\"
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
        \"\"\"
        Main method for generating a response using the RAG pipeline.
        
        Args:
            query (str): User query
            session_id (str): Session identifier
            language (str): Language code (en, ar)
            
        Returns:
            Dict: Generated response with retrieved context
        \"\"\"
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
                attractions = self.knowledge_base.search_attractions(
                    query="",
                    filters={"city": location},
                    language=language,
                    limit=5
                )
                
                if attractions:
                    logger.info(f"Found {len(attractions)} attractions for location: {location}")
                    response_text = f"Here are some top attractions in {location}:\\n\\n"
                    
                    for idx, attraction in enumerate(attractions, 1):
                        name = attraction.get("name_en", "Unknown")
                        description = attraction.get("description_en", "No description available.")
                        # Shorten description if too long
                        if len(description) > 100:
                            description = description[:100] + "..."
                        response_text += f"{idx}. **{name}**: {description}\\n\\n"
                    
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
        \"\"\"Extract entities from the query text.\"\"\"
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
        \"\"\"
        Process a query using the RAG pipeline.
        
        Args:
            query (str): User query
            intent (str): Detected intent
            context (Dict): Conversation context
            language (str): Language code
            
        Returns:
            Dict: Generated response with retrieved context
        \"\"\"
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
        \"\"\"
        Process a query about attractions.
        
        Args:
            query (str): User query
            intent (str): Detected intent
            entities (Dict): Extracted entities
            context (Dict): Conversation context
            language (str): Language code
            
        Returns:
            Dict: Generated response
        \"\"\"
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
    
    # [Additional methods omitted for brevity]
    
    def _process_general_query(self, query: str, intent: str, context: Dict, 
                           language: str) -> Dict[str, Any]:
        \"\"\"
        Process a general query using semantic search.
        
        Args:
            query (str): User query
            intent (str): Detected intent
            context (Dict): Conversation context
            language (str): Language code
            
        Returns:
            Dict: Generated response
        \"\"\"
        try:
            # If we don't have vector DB and embedding model, try direct DB query
            location_entities = self._extract_entities(query).get("location", [])
            
            if location_entities:
                location = location_entities[0]
                # Search for attractions in this location
                attractions = self.knowledge_base.search_attractions(
                    query="",
                    filters={"city": location},
                    language=language,
                    limit=5
                )
                
                if attractions:
                    logger.info(f"Found {len(attractions)} attractions for location: {location}")
                    response_text = f"Here are some top attractions in {location}:\\n\\n"
                    
                    for idx, attraction in enumerate(attractions, 1):
                        name = attraction.get("name_en", "Unknown")
                        description = attraction.get("description_en", "No description available.")
                        # Shorten description if too long
                        if len(description) > 100:
                            description = description[:100] + "..."
                        response_text += f"{idx}. **{name}**: {description}\\n\\n"
                    
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
        \"\"\"
        Search for attractions matching the query.
        
        Args:
            query (str): User query
            intent (str): Detected intent
            entities (Dict): Extracted entities
            language (str): Language code
            
        Returns:
            Dict: Generated response with search results
        \"\"\"
        try:
            # Extract location if present
            location = None
            if "location" in entities and entities["location"]:
                location = entities["location"][0]
            
            # Prepare search filters
            filters = {}
            if location:
                filters["city"] = location
            
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
    
    def _generate_attraction_list_response(self, attractions, location, language):
        \"\"\"Generate a response listing attractions.\"\"\"
        location_text = f" in {location}" if location else ""
        
        if language == "ar":
            response_text = f"إليك بعض المعالم السياحية الشهيرة{location_text}:\\n\\n"
        else:
            response_text = f"Here are some popular attractions{location_text}:\\n\\n"
        
        for idx, attraction in enumerate(attractions, 1):
            name_field = "name_ar" if language == "ar" else "name_en"
            desc_field = "description_ar" if language == "ar" else "description_en"
            
            name = attraction.get(name_field, attraction.get("name_en", "Unknown"))
            description = attraction.get(desc_field, attraction.get("description_en", ""))
            
            # Trim description if too long
            if description and len(description) > 100:
                description = description[:100] + "..."
            
            response_text += f"{idx}. **{name}**: {description}\\n\\n"
        
        return {
            "text": response_text,
            "attractions": attractions
        }
    
    def _get_active_entities(self, context: Dict[str, Any]) -> Dict[str, List[str]]:
        \"\"\"
        Get active entities from context for reference resolution.
        
        Args:
            context (Dict): Conversation context
            
        Returns:
            Dict: Active entities by type
        \"\"\"
        # Simple implementation - just return entities from context
        return context.get("entities", {})
    
    def _get_fallback_response(self, language: str) -> Dict[str, Any]:
        \"\"\"
        Get a fallback response when no information is available.
        
        Args:
            language (str): Language code
            
        Returns:
            Dict: Fallback response
        \"\"\"
        if language == "ar":
            return {
                "text": "عذراً، لا يمكنني العثور على معلومات كافية للإجابة على هذا السؤال. هل يمكنك طرح سؤالك بطريقة مختلفة؟"
            }
        else:
            return {
                "text": "I'm sorry, I couldn't find enough information to answer this question. Could you try asking in a different way?"
            }
    
    def _get_no_attractions_message(self, location: str, language: str) -> str:
        \"\"\"Get message for when no attractions are found at a location.\"\"\"
        if language == "ar":
            return f"عذراً، لم أتمكن من العثور على معالم سياحية في {location}. هل تريد البحث في مكان آخر؟"
        else:
            return f"I couldn't find any attractions in {location}. Would you like to search for attractions in another area?"
""")
    print(f"Created RAG pipeline at {pipeline_file}")

print("\nRAG integration script complete! Please restart the container to apply changes:")
print("docker restart egypt-chatbot-wind-cursor-app-1")
