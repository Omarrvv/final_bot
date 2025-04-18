# src/nlu/engine.py
"""
Natural Language Understanding engine for the Egypt Tourism Chatbot.
Handles intent classification, entity extraction, and language processing.
"""
import os
import json
import logging
import time
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import spacy
from transformers import AutoTokenizer, AutoModel
import torch
from sklearn.metrics.pairwise import cosine_similarity

from src.nlu.intent import IntentClassifier
from src.nlu.entity import EntityExtractor
from src.nlu.language import LanguageDetector
from src.utils.cache import LRUCache
from src.nlu.enhanced_entity import EnhancedEntityExtractor
from src.nlu.continuous_learning import EntityLearner, FeedbackCollector

logger = logging.getLogger(__name__)

class NLUEngine:
    """
    Natural Language Understanding engine for processing user queries.
    Handles language detection, intent classification, and entity extraction.
    """
    
    def __init__(self, models_config: str, knowledge_base):
        """
        Initialize the NLU engine with specified models.
        
        Args:
            models_config (str): Path to model configuration file
            knowledge_base: Reference to the knowledge base for entity lookup
        """
        self.knowledge_base = knowledge_base
        self.models_config = self._load_config(models_config)
        
        # Initialize language detector
        self.language_detector = LanguageDetector(
            model_path=self.models_config.get("language_detection", {}).get("model_path"),
            confidence_threshold=self.models_config.get("language_detection", {}).get("confidence_threshold", 0.8)
        )
        
        # Initialize language-specific NLP models
        self.nlp_models = {}
        self._load_nlp_models()
        
        # Initialize transformer models for embeddings
        self.transformer_models = {}
        self.transformer_tokenizers = {}
        self._load_transformer_models()
        
        # Initialize intent classifier
        self.intent_classifier = IntentClassifier(
            config=self.models_config.get("intent_classification", {}),
            embedding_model=self._get_embedding_model,
            knowledge_base=knowledge_base
        )
        
        # Initialize entity extractors
        self.entity_extractors = {}
        self._load_entity_extractors()
        
        # Initialize embedding cache
        self.embedding_cache = LRUCache(
            max_size=self.models_config.get("cache", {}).get("embedding_cache_size", 1000)
        )
        
        # Initialize main result cache
        self.cache = LRUCache(
            max_size=self.models_config.get("cache", {}).get("result_cache_size", 1000)
        )
        
        # Initialize continuous learning components
        self.entity_learner = EntityLearner(
            storage_path="data/learning",
            min_examples=self.models_config.get("learning", {}).get("min_examples", 3),
            confidence_threshold=self.models_config.get("learning", {}).get("confidence_threshold", 0.7)
        )
        
        self.feedback_collector = FeedbackCollector(
            entity_learner=self.entity_learner,
            storage_path="data/feedback"
        )
        
        logger.info("NLU Engine initialized successfully")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load model configuration from file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load models config: {str(e)}")
            return {
                "language_detection": {
                    "model_path": "lid.176.bin",
                    "confidence_threshold": 0.8
                },
                "nlp_models": {
                    "en": "en_core_web_md",
                    "ar": "xx_ent_wiki_sm"  # Fallback model for Arabic
                },
                "transformer_models": {
                    "multilingual": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
                    "en": "sentence-transformers/all-mpnet-base-v2",
                    "ar": "asafaya/bert-base-arabic"
                }
            }
    
    def _load_nlp_models(self):
        """Load spaCy NLP models for each supported language."""
        for lang, model_name in self.models_config.get("nlp_models", {}).items():
            try:
                # Check if model is installed, download if not
                try:
                    self.nlp_models[lang] = spacy.load(model_name)
                    logger.info(f"Loaded spaCy model {model_name} for language {lang}")
                except OSError:
                    logger.info(f"Downloading spaCy model {model_name}")
                    spacy.cli.download(model_name)
                    self.nlp_models[lang] = spacy.load(model_name)
            except Exception as e:
                logger.error(f"Failed to load spaCy model for {lang}: {str(e)}")
    
    def _load_transformer_models(self):
        """Load transformer models for embeddings generation."""
        for key, model_name in self.models_config.get("transformer_models", {}).items():
            try:
                self.transformer_tokenizers[key] = AutoTokenizer.from_pretrained(model_name)
                self.transformer_models[key] = AutoModel.from_pretrained(model_name)
                logger.info(f"Loaded transformer model {model_name} for {key}")
            except Exception as e:
                logger.error(f"Failed to load transformer model for {key}: {str(e)}")
    
    def _load_entity_extractors(self):
        """Load entity extractors for each supported language."""
        entity_config = self.models_config.get("entity_extraction", {})
        supported_languages = entity_config.get("supported_languages", ["en", "ar"])
        
        for lang in supported_languages:
            lang_config = entity_config.get(lang, {})
            self.entity_extractors[lang] = EnhancedEntityExtractor(
                language=lang,
                config=lang_config,
                nlp_model=self.nlp_models.get(lang),
                knowledge_base=self.knowledge_base,
                embedding_model=self._get_embedding_model
            )
            logger.info(f"Initialized enhanced entity extractor for {lang}")
    
    def _get_embedding_model(self, text, language=None):
        """Get embeddings for text using appropriate model."""
        # Check cache first
        cache_key = f"{text}_{language}"
        if cache_key in self.embedding_cache:
            return self.embedding_cache[cache_key]
        
        # Select appropriate model based on language
        model_key = language if language in self.transformer_models else "multilingual"
        if model_key not in self.transformer_models:
            model_key = next(iter(self.transformer_models.keys()))
        
        model = self.transformer_models[model_key]
        tokenizer = self.transformer_tokenizers[model_key]
        
        # Generate embedding
        inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
        with torch.no_grad():
            outputs = model(**inputs)
        
        # Use CLS token embedding or mean pooling depending on model type
        if hasattr(outputs, "pooler_output"):
            embedding = outputs.pooler_output.numpy()
        else:
            # Mean pooling
            attention_mask = inputs["attention_mask"]
            token_embeddings = outputs.last_hidden_state
            input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
            sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
            sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
            embedding = (sum_embeddings / sum_mask).numpy()
        
        # Cache and return
        self.embedding_cache[cache_key] = embedding
        return embedding
    
    def process(self, text: str, session_id: str, language: Optional[str] = None, 
                context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process a user message to determine intent, entities, and other metadata.
        
        Args:
            text (str): User message text
            session_id (str): Session identifier for context tracking
            language (str, optional): Language code if known (e.g., 'en', 'ar')
            context (dict, optional): Current conversation context
            
        Returns:
            dict: Processed NLU result including intent, entities, and other metadata
        """
        start_time = time.time()
        cache_key = f"{text}_{language or 'auto'}_{session_id}"
        
        # Check cache first
        cached_result = self.cache.get(cache_key)
        if cached_result:
            logger.debug(f"Using cached NLU result for: {text}")
            return cached_result
        
        try:
            # Detect language if not provided
            if not language:
                language, lang_confidence = self.language_detector.detect(text)
                logger.debug(f"Detected language: {language} (confidence: {lang_confidence:.2f})")
            else:
                # Set a default confidence if language is provided
                lang_confidence = 1.0
            
            # Default to English if unsupported language
            if language not in self.nlp_models:
                logger.warning(f"Unsupported language: {language}, falling back to English")
                language = "en"
            
            # Preprocess text
            processed_text = self._preprocess_text(text, language)
            
            # Get text embedding for intent classification
            embedding = self._get_embedding_model(processed_text, language)
            
            # Classify intent
            intent_result = self.intent_classifier.classify(
                text=processed_text,
                embedding=embedding,
                language=language,
                context=context
            )
            
            # Extract entities
            entity_extractor = self.entity_extractors.get(language)
            if entity_extractor:
                entity_result = entity_extractor.extract(
                    text=processed_text,
                    intent=intent_result.get("intent"),
                    context=context
                )
                
                # Apply continuous learning to enhance entity extraction
                enhanced_entities, enhanced_confidence = self.entity_learner.enhance_entities(
                    processed_text,
                    entity_result.get("entities", {}),
                    entity_result.get("confidence", {})
                )
                
                # Update entity result with enhanced data
                entity_result["entities"] = enhanced_entities
                entity_result["confidence"] = enhanced_confidence
            else:
                # Fallback if no entity extractor is available
                entity_result = {
                    "entities": {},
                    "confidence": {}
                }
            
            # Combine intent and entity results
            result = {
                "text": text,
                "processed_text": processed_text,
                "language": language,
                "language_confidence": lang_confidence,
                "intent": intent_result.get("intent"),
                "intent_confidence": intent_result.get("confidence", 0.0),
                "entities": entity_result.get("entities", {}),
                "entity_confidence": entity_result.get("confidence", {}),
                "session_id": session_id,
                "processing_time": time.time() - start_time
            }
            
            # Add intent metadata if available
            if "metadata" in intent_result:
                result["intent_metadata"] = intent_result["metadata"]
            
            # Add entity relationships if available
            if "relationships" in entity_result:
                result["entity_relationships"] = entity_result["relationships"]
            
            # Cache the result
            self.cache[cache_key] = result
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing text: {str(e)}")
            # Return a minimal result on error
            return {
                "intent": None,
                "confidence": 0.0,
                "entities": {},
                "entity_confidence": {},
                "language": language or "en",
                "language_confidence": 1.0,  # Default confidence to avoid KeyError
                "session_id": session_id,
                "error": str(e)
            }
    
    def _preprocess_text(self, text: str, language: str) -> str:
        """Apply language-specific preprocessing to text."""
        # Default preprocessing (lowercase, strip)
        processed = text.lower().strip()
        
        # Apply language-specific preprocessing if available
        lang_preprocessor = getattr(self, f"_preprocess_{language}", None)
        if lang_preprocessor:
            processed = lang_preprocessor(processed)
        
        return processed
    
    def _preprocess_ar(self, text: str) -> str:
        """Preprocess Arabic text."""
        # Arabic-specific preprocessing
        # This could include normalizing Arabic characters, handling diacritics, etc.
        # For now, just return the text as is
        return text

    def process_feedback(self, message_id: str, user_message: str, extracted_entities: Dict[str, List[str]],
                      correct_entities: Dict[str, List[str]], user_id: Optional[str] = None) -> bool:
        """
        Process user feedback to improve entity extraction.
        
        Args:
            message_id (str): ID of the message
            user_message (str): Original user message
            extracted_entities (Dict): Entities extracted by the system
            correct_entities (Dict): Correct entities provided by user feedback
            user_id (str, optional): User ID for tracking
            
        Returns:
            bool: Success flag
        """
        return self.feedback_collector.collect_explicit_feedback(
            message_id,
            user_message,
            extracted_entities,
            correct_entities,
            user_id
        )
        
    def process_session_feedback(self, session_id: str, messages: List[Dict], 
                             entities: List[Dict], user_id: Optional[str] = None) -> bool:
        """
        Process session feedback to improve entity extraction.
        
        Args:
            session_id (str): Session ID
            messages (List[Dict]): Messages from the session
            entities (List[Dict]): Entities extracted in each turn
            user_id (str, optional): User ID for tracking
            
        Returns:
            bool: Success flag
        """
        return self.feedback_collector.collect_implicit_feedback(
            session_id,
            messages,
            entities,
            user_id
        )
        
    def get_learning_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the continuous learning system.
        
        Returns:
            Dict: Learning statistics
        """
        return {
            "entity_learner": self.entity_learner.get_stats(),
            "feedback_collector": self.feedback_collector.get_stats()
        }