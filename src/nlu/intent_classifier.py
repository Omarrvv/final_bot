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
    
    def __init__(self, config=None, embedding_model=None, knowledge_base=None):
        """
        Initialize the intent classifier.
        
        Args:
            config (Dict): Configuration dictionary
            embedding_model: Model for embedding text
            knowledge_base: Knowledge base for context
        """
        self.config = config or {}
        self.embedding_model = embedding_model
        self.knowledge_base = knowledge_base
        
        # Intent definitions with examples
        self.intents = self.config.get("intents", {})
        
        # Intent examples and their embeddings
        self.intent_examples = {}
        self.intent_embeddings = {}
        
        # Default confidence threshold
        self.min_confidence = self.config.get("min_confidence", 0.65)
        
        # Contextual bias - gives preference to intents related to current context
        self.context_bias = self.config.get("context_bias", 0.1)
        
        # Initialize intent examples
        self._prepare_intent_examples()
        
    def _prepare_intent_examples(self):
        """Process and prepare intent examples for classification."""
        logger.info("Preparing intent examples")
        
        for intent_name, intent_data in self.intents.items():
            examples = intent_data.get("examples", [])
            
            if not examples:
                logger.warning(f"No examples found for intent '{intent_name}'")
                continue
                
            self.intent_examples[intent_name] = examples
            
            # Cache embeddings if embedding model is available
            if self.embedding_model:
                try:
                    embeddings = self.embedding_model.encode(examples)
                    self.intent_embeddings[intent_name] = embeddings
                    logger.debug(f"Cached {len(embeddings)} embeddings for intent '{intent_name}'")
                except Exception as e:
                    logger.error(f"Failed to generate embeddings for '{intent_name}': {str(e)}")
    
    def classify(self, text: str, embedding=None, language=None, context=None) -> Dict[str, Any]:
        """
        Classify the intent of user text input.
        
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
        if embedding is None and self.embedding_model:
            try:
                embedding = self.embedding_model.encode([text])[0]
            except Exception as e:
                logger.error(f"Failed to generate embedding: {str(e)}")
                return self._get_fallback_result()
        
        if embedding is None:
            logger.warning("No embedding available for intent classification")
            return self._get_fallback_result()
            
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
        
        # Ensure embedding has proper dimensions
                                if embedding.ndim == 0 or (embedding.ndim == 1 and embedding.size == 1):
                                    logger.warning(f"Detected scalar embedding in intent classifier, expanding to standard dimension")
                                    standard_dim = 768  # Standard embedding dimension
                                    expanded = np.zeros(standard_dim)
                                    if embedding.size > 0:
                                        scalar_value = float(embedding.item() if hasattr(embedding, 'item') else embedding)
                                        expanded.fill(scalar_value)
                                    embedding = expanded
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
        if self.embedding_model:
            try:
                new_embedding = self.embedding_model.encode([example])[0]
                
                if intent not in self.intent_embeddings:
                    self.intent_embeddings[intent] = np.array([new_embedding])
                else:
                    self.intent_embeddings[intent] = np.vstack([self.intent_embeddings[intent], new_embedding])
                    
                logger.info(f"Added new example to intent '{intent}'")
                return True
            except Exception as e:
                logger.error(f"Failed to update embeddings for '{intent}': {str(e)}")
                return False
        
        return True 