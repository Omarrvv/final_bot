"""
Advanced intent classification for the Egypt Tourism Chatbot.
Uses embeddings and contextual information for accurate intent detection.
"""
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class AdvancedIntentClassifier:
    """
    Advanced intent classifier with confidence scoring and contextual awareness.
    Uses semantic similarity with pre-defined intent examples.
    """
    
    def __init__(self, config=None, embedding_service=None, knowledge_base=None):
        """
        Initialize the intent classifier.
        
        Args:
            config (Dict): Configuration dictionary
            embedding_service: StandardizedEmbeddingService for generating embeddings
            knowledge_base: Knowledge base for context
        """
        self.config = config or {}
        self.embedding_service = embedding_service
        self.knowledge_base = knowledge_base
        
        # Intent definitions with examples - Load from comprehensive file
        self.intents = self._load_comprehensive_intents()
        
        # Intent examples and their embeddings
        self.intent_examples = {}
        self.intent_embeddings = {}
        
        # Default confidence threshold
        self.min_confidence = self.config.get("min_confidence", 0.65)
        
        # Contextual bias - gives preference to intents related to current context
        self.context_bias = self.config.get("context_bias", 0.1)
        
        # Initialize intent examples
        self._prepare_intent_examples()
    
    def _load_comprehensive_intents(self):
        """Load comprehensive intents from file with fallback to config."""
        import os
        import json
        
        # First try to load from the comprehensive intents file
        custom_intents_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "configs", "comprehensive_intents.json")
        if os.path.exists(custom_intents_path):
            logger.info(f"Loading intents from custom file: {custom_intents_path}")
            intents = self._load_intents_from_file(custom_intents_path)
            if intents:
                logger.info(f"Successfully loaded {len(intents)} intents from custom file")
                return intents.get("intents", intents)  # Handle both formats
            else:
                logger.warning("Failed to load intents from custom file, falling back to config")

        # If custom file doesn't exist or is empty, check if intents are directly in the config dictionary
        if "intents" in self.config and isinstance(self.config["intents"], dict):
            logger.info("Loading intents directly from config dictionary.")
            return self.config["intents"]
        else:
            # Fallback to loading from file path if specified
            intents_file_path = self.config.get("intents_file")
            logger.info(f"Attempting to load intents from file: {intents_file_path}")
            intents = self._load_intents_from_file(intents_file_path)
            if intents:
                return intents.get("intents", intents)  # Handle both formats
            else:
                logger.warning("No intents loaded! Using empty intents dictionary.")
                return {}
    
    def _load_intents_from_file(self, file_path):
        """Load intent definitions from a JSON file."""
        import os
        import json
        
        if not file_path or not os.path.exists(file_path):
            logger.error(f"Intents file not found or path not specified: {file_path}")
            return {}
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                intents = json.load(f)
                logger.info(f"Successfully loaded intents from {file_path}")
                return intents
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON from intents file: {file_path}")
            return {}
        except Exception as e:
            logger.error(f"Error loading intents file {file_path}: {e}")
            return {}
        
    def _prepare_intent_examples(self):
        """Process and prepare intent examples for classification with retry logic."""
        logger.info("🧠 Preparing intent examples with standardized embedding service")
        
        for intent_name, intent_data in self.intents.items():
            examples = intent_data.get("examples", [])
            
            if not examples:
                logger.warning(f"No examples found for intent '{intent_name}'")
                continue
                
            self.intent_examples[intent_name] = examples
            
            # Cache embeddings if embedding service is available
            if self.embedding_service and self.embedding_service.is_ready():
                self._generate_intent_embeddings_with_retry(intent_name, examples)
            else:
                logger.warning(f"⚠️ Embedding service not ready for intent '{intent_name}' - will retry later")
                
    def _generate_intent_embeddings_with_retry(self, intent_name: str, examples: List[str], max_retries: int = 3):
        """Generate embeddings for intent examples with retry logic."""
        for attempt in range(max_retries):
            try:
                logger.info(f"🔄 Generating embeddings for intent '{intent_name}' (attempt {attempt + 1}/{max_retries})")
                
                # Use batch generation for efficiency
                embedding_results = self.embedding_service.generate_batch_embeddings(examples, language='en')
                
                # Convert to numpy array for similarity calculations
                embeddings = []
                for example in examples:
                    if example in embedding_results:
                        embeddings.append(embedding_results[example])
                    else:
                        logger.warning(f"Missing embedding for example: {example}")
                        # Generate fallback embedding
                        fallback = self.embedding_service.generate_embedding(example, language='en')
                        embeddings.append(fallback)
                
                if embeddings:
                    embeddings_array = np.stack(embeddings, axis=0)
                    self.intent_embeddings[intent_name] = embeddings_array
                    logger.info(f"✅ Cached {len(embeddings)} embeddings for intent '{intent_name}' (shape: {embeddings_array.shape})")
                    return True
                else:
                    logger.error(f"❌ No valid embeddings generated for intent '{intent_name}'")
                    
            except Exception as e:
                logger.error(f"❌ Attempt {attempt + 1} failed for intent '{intent_name}': {str(e)}")
                if attempt < max_retries - 1:
                    logger.info(f"🔄 Retrying in 1 second...")
                    import time
                    time.sleep(1)
                else:
                    logger.error(f"❌ All attempts failed for intent '{intent_name}' - skipping")
                    return False
        
        return False
                    
    def force_regenerate_embeddings(self):
        """Force regeneration of all intent embeddings after models are loaded."""
        if not self.embedding_service or not self.embedding_service.is_ready():
            logger.warning("⚠️ Cannot regenerate embeddings - service not ready")
            return False
            
        logger.info("🔄 Force regenerating all intent embeddings...")
        success_count = 0
        
        for intent_name, examples in self.intent_examples.items():
            if self._generate_intent_embeddings_with_retry(intent_name, examples):
                success_count += 1
                
        logger.info(f"✅ Successfully regenerated embeddings for {success_count}/{len(self.intent_examples)} intents")
        return success_count == len(self.intent_examples)
    
    def classify(self, text: str, embedding=None, language=None, context=None) -> Dict[str, Any]:
        """
        Classify the intent of user text input with transportation debugging.
        
        Args:
            text (str): User input text
            embedding: Pre-computed text embedding (optional)
            language (str): Language code (optional)
            context (Dict): Current conversation context (optional)
            
        Returns:
            Dict: Intent classification result with scores and confidence
        """
        if not text:
            return self._get_empty_result()
            
        # Get embedding for input text
        if embedding is None and self.embedding_service and self.embedding_service.is_ready():
            try:
                embedding = self.embedding_service.generate_embedding(text, language)
            except Exception as e:
                logger.error(f"Failed to generate embedding: {str(e)}")
                return self._get_fallback_result()
        
        if embedding is None:
            logger.warning("No embedding available for intent classification")
            return self._get_fallback_result()
            
        # DEBUG: Check embedding quality
        is_fallback = len(np.unique(embedding)) == 1
        logger.debug(f"Query embedding quality - Fallback: {is_fallback}, Shape: {embedding.shape}")
        
        # DEBUG: Log embedding quality (removed transportation-specific logic)
        logger.debug(f"Processing query: '{text[:50]}...' with {'fallback' if is_fallback else 'real'} embedding")
            
        # Calculate similarity with all intent examples
        intent_scores = self._calculate_intent_scores(embedding, context)
        
        # Get top 3 intents for detailed analysis
        top_intents = sorted(intent_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        
        if not top_intents:
            return self._get_fallback_result()
            
        # Get the top intent and its score
        top_intent, top_score = top_intents[0]
        
        # Check if score meets minimum confidence threshold
        if top_score < self.min_confidence:
            # Check if we should disambiguate or fall back
            if top_score > self.min_confidence * 0.8 and len(top_intents) > 1:
                return self._get_disambiguation_result(top_intents)
            else:
                return self._get_fallback_result()
        
        # Calculate confidence differential (how much better the top intent is vs the second)
        confidence_diff = 0
        if len(top_intents) > 1:
            confidence_diff = top_score - top_intents[1][1]
        
        # DEBUG: Log classification result
        logger.debug(f"Intent classification result: {top_intent} ({top_score:.3f})")
        
        # Return classification result
        return {
            "intent": top_intent,
            "confidence": float(top_score),
            "confidence_diff": float(confidence_diff),
            "top_intents": [{"intent": i, "score": float(s)} for i, s in top_intents],
            "needs_disambiguation": confidence_diff < 0.1 and top_score < 0.8
        }
    
    def _calculate_intent_scores(self, embedding: np.ndarray, context: Optional[Dict] = None) -> Dict[str, float]:
        """
        Calculate similarity scores for all intents.
        
        Args:
            embedding (np.ndarray): Input text embedding
            context (Dict): Conversation context
            
        Returns:
            Dict: Intent names mapped to similarity scores
        """
        intent_scores = {}
        
        for intent_name, intent_embeddings in self.intent_embeddings.items():
            # Calculate cosine similarity with all examples
            similarities = cosine_similarity([embedding], intent_embeddings)[0]
            
            # Use the highest similarity score
            max_similarity = np.max(similarities)
            intent_scores[intent_name] = max_similarity
            
            # Apply context bias if context exists and has dialog_state
            if context and "dialog_state" in context:
                current_state = context["dialog_state"]
                
                # Get related intents for current state
                related_intents = self.config.get("state_intent_map", {}).get(current_state, [])
                
                # Apply bias to related intents
                if intent_name in related_intents:
                    intent_scores[intent_name] += self.context_bias
        
        return intent_scores
    
    def _get_empty_result(self) -> Dict[str, Any]:
        """Return result for empty input."""
        return {
            "intent": "greeting",
            "confidence": 1.0,
            "top_intents": [{"intent": "greeting", "score": 1.0}],
            "needs_disambiguation": False
        }
    
    def _get_fallback_result(self) -> Dict[str, Any]:
        """Return fallback result when classification fails."""
        return {
            "intent": "general_query",
            "confidence": 0.5,
            "top_intents": [{"intent": "general_query", "score": 0.5}],
            "needs_disambiguation": False
        }
    
    def _get_disambiguation_result(self, top_intents: List[Tuple[str, float]]) -> Dict[str, Any]:
        """Return disambiguation result for ambiguous intent."""
        return {
            "intent": "disambiguation_required",
            "confidence": 0.5,
            "top_intents": [{"intent": i, "score": float(s)} for i, s in top_intents],
            "needs_disambiguation": True
        }
    
    def get_all_intents(self) -> List[Dict[str, Any]]:
        """
        Get information about all available intents.
        
        Returns:
            List[Dict]: List of intent information
        """
        intent_info = []
        
        for intent_name, intent_data in self.intents.items():
            intent_info.append({
                "name": intent_name,
                "description": intent_data.get("description", ""),
                "examples": intent_data.get("examples", [])[:3],  # Just include first 3 examples
                "parameters": intent_data.get("parameters", {})
            })
            
        return intent_info
        
    def add_user_example(self, intent: str, example: str) -> bool:
        """
        Add a user example to intent for online learning.
        
        Args:
            intent (str): Intent name
            example (str): Example text
            
        Returns:
            bool: Success flag
        """
        if intent not in self.intents:
            logger.warning(f"Cannot add example: Intent '{intent}' does not exist")
            return False
            
        if not example or not isinstance(example, str):
            logger.warning(f"Cannot add invalid example to '{intent}'")
            return False
            
        # Add to examples
        if intent not in self.intent_examples:
            self.intent_examples[intent] = []
            
        self.intent_examples[intent].append(example)
        
        # Update embedding
        if self.embedding_service and self.embedding_service.is_ready():
            try:
                new_embedding = self.embedding_service.generate_embedding(example, 'en')  # Default to English
                
                if intent not in self.intent_embeddings:
                    self.intent_embeddings[intent] = np.asarray([new_embedding])
                else:
                    self.intent_embeddings[intent] = np.vstack([self.intent_embeddings[intent], new_embedding])
                    
                logger.info(f"Added new example to intent '{intent}'")
                return True
            except Exception as e:
                logger.error(f"Failed to update embeddings for '{intent}': {str(e)}")
                return False
        
        return True 