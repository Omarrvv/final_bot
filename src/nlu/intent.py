import logging
import json
import os
from sklearn.metrics.pairwise import cosine_similarity
import re # Add re import for regex compilation

logger = logging.getLogger(__name__)

class IntentClassifier:
    """Intent classification module for the Egypt Tourism Chatbot."""

    def __init__(self, config=None, embedding_model=None, knowledge_base=None):
        """
        Initialize the intent classifier.

        Args:
            config (dict, optional): Configuration for the classifier
            embedding_model: Model for creating embeddings
            knowledge_base: Knowledge base for context
        """
        self.config = config or {}
        self.embedding_model = embedding_model
        self.knowledge_base = knowledge_base

        # --- MODIFIED INTENT LOADING ---
        # First try to load from the custom intents file in src/nlu/config
        custom_intents_path = os.path.join(os.path.dirname(__file__), "config", "intents.json")
        if os.path.exists(custom_intents_path):
            logger.info(f"Loading intents from custom file: {custom_intents_path}")
            self.intents = self._load_intents_from_file(custom_intents_path)
            if self.intents:
                logger.info(f"Successfully loaded {len(self.intents)} intents from custom file")
            else:
                logger.warning("Failed to load intents from custom file, falling back to config")

        # If custom file doesn't exist or is empty, check if intents are directly in the config dictionary
        if not hasattr(self, 'intents') or not self.intents:
            if "intents" in self.config and isinstance(self.config["intents"], dict):
                logger.info("Loading intents directly from config dictionary.")
                self.intents = self.config["intents"]
            else:
                # Fallback to loading from file path if specified
                intents_file_path = self.config.get("intents_file")
                logger.info(f"Attempting to load intents from file: {intents_file_path}")
                self.intents = self._load_intents_from_file(intents_file_path)

        # Log the loaded intents
        if self.intents:
            logger.info(f"Loaded {len(self.intents)} intents: {', '.join(self.intents.keys())}")
        else:
            logger.warning("No intents loaded! Using empty intents dictionary.")
            self.intents = {}
        # --- END MODIFIED INTENT LOADING ---

        self.intent_examples = self._prepare_intent_examples()
        self.default_intent = self.config.get("default_intent", "general_query")
        self.min_confidence = self.config.get("min_confidence", 0.7)
        # Compile regex patterns on init
        self.regex_patterns = self._compile_regex_patterns()

    def _load_intents_from_file(self, file_path):
        """Load intent definitions from a JSON file."""
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

    def _compile_regex_patterns(self):
        """Compile regex patterns defined in intents."""
        compiled_patterns = {}
        for intent_name, intent_data in self.intents.items():
            patterns = intent_data.get("patterns", [])
            if patterns:
                compiled_patterns[intent_name] = []
                for pattern in patterns:
                    try:
                        # Add word boundaries for more precise matching
                        compiled = re.compile(r'\b' + pattern + r'\b', re.IGNORECASE | re.UNICODE)
                        compiled_patterns[intent_name].append(compiled)
                    except re.error as e:
                        logger.error(f"Invalid regex pattern for intent '{intent_name}': {pattern} - {e}")
        logger.info(f"Compiled {sum(len(p) for p in compiled_patterns.values())} regex patterns.")
        return compiled_patterns

    def _prepare_intent_examples(self):
        """Prepare intent examples for embedding-based matching."""
        intent_examples = {}
        for intent_name, intent_config in self.intents.items():
            examples = intent_config.get("examples", [])
            if examples:
                intent_examples[intent_name] = examples
        return intent_examples

    def classify(self, text, embedding=None, language=None, context=None):
        """
        Classify the intent of user text input.

        Args:
            text (str): User input text
            embedding (optional): Pre-computed text embedding
            language (str, optional): Language of the text
            context (dict, optional): Conversation context

        Returns:
            dict: Intent classification result with intent name and confidence
        """
        # --- Check for regex pattern matches first ---
        if hasattr(self, 'regex_patterns') and text:
            for intent_name, patterns in self.regex_patterns.items():
                for pattern in patterns:
                    if pattern.search(text):
                        logger.debug(f"Intent '{intent_name}' matched by regex: {pattern.pattern}")
                        # Regex match gets highest confidence
                        return {
                            "intent": intent_name,
                            "confidence": 1.0,
                            "match_type": "regex"
                        }

        # --- Proceed with embedding similarity if no regex match ---
        # Short-circuit if we don't have a proper embedding model
        if not self.embedding_model or not self.intent_examples:
            return {
                "intent": self.default_intent,
                "confidence": 1.0,
            }

        # Get embedding for the input text if not provided
        if embedding is None and text:
            # Pass text as a list
            embedding_result = self.embedding_model([text], language=language)
            if embedding_result is not None and len(embedding_result) > 0:
                 embedding = embedding_result[0]
            else:
                 logger.warning(f"Failed to get embedding for text: {text}")
                 embedding = None # Handle failure

        if embedding is None:
            return {
                "intent": self.default_intent,
                "confidence": 1.0,
            }

        # Find the best matching intent
        best_intent = self.default_intent
        best_confidence = 0.0

        for intent_name, examples in self.intent_examples.items():
            # Get embeddings for examples (ideally these would be cached)
            example_embeddings = self.embedding_model(examples, language=language)

            # Calculate similarities
            similarities = []
            if example_embeddings is None:
                 logger.warning(f"Failed to get embeddings for intent examples: {intent_name}")
                 continue # Skip intent if examples can't be embedded

            for example_embedding in example_embeddings:
                # Ensure we have valid embeddings to compare
                if embedding is not None and example_embedding is not None:
                     # Using dot product for cosine similarity assuming embeddings are normalized
                     # Reshape embedding to be 2D for dot product if needed
                     current_embedding = embedding.reshape(1, -1)
                     example_embedding_reshaped = example_embedding.reshape(1, -1)
                     # similarity = embedding.dot(example_embedding)
                     similarity = cosine_similarity(current_embedding, example_embedding_reshaped)[0][0]
                     similarities.append(similarity)

            # Get highest similarity for this intent
            if similarities:
                max_similarity = max(similarities)
                if max_similarity > best_confidence:
                    best_confidence = max_similarity
                    best_intent = intent_name

        # Check if we meet the minimum confidence threshold
        if best_confidence < self.min_confidence:
            best_intent = self.default_intent

        return {
            "intent": best_intent,
            "confidence": best_confidence
        }

    def _apply_context(self, classification_result, context):
        """Stub for applying context to intent classification."""
        # TODO: Implement actual context logic if needed
        # Example: If last intent was X and current is general_query, maybe stick with X?
        last_intent = context.get("last_intent")
        current_intent = classification_result.get("intent")
        current_confidence = classification_result.get("confidence", 0.0)

        # Simple rule: If current is default/low confidence and last was specific, use last intent.
        if current_intent == self.default_intent and current_confidence < self.min_confidence and last_intent and last_intent != self.default_intent:
            logger.debug(f"Context override: Using last intent '{last_intent}' instead of low-confidence default '{current_intent}'")
            # Return a modified result using the last intent
            # We might assign a default confidence or carry over something?
            # For now, let's assign a moderate confidence to indicate it's context-driven.
            return {
                **classification_result, # Keep other fields like match_type if present
                "intent": last_intent,
                "confidence": 0.75, # Assign moderate confidence for context override
                "match_type": "context_override" # Add info about the override
            }
            # pass # Placeholder for more complex logic - REMOVED

        return classification_result # Return original if context doesn't apply or confidence is high

    def get_all_intents(self):
        """
        Get all supported intents.

        Returns:
            list: List of intent names
        """
        return list(self.intents.keys())