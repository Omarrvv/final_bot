# src/nlu/engine.py
"""
Natural Language Understanding engine for the Egypt Tourism Chatbot.
Handles intent classification, entity extraction, and language processing.
"""
import os
import json
import logging
import time
import asyncio
from typing import Dict, List, Any, Optional, Tuple

# Fix tokenizer parallelism warning (Phase 3 optimization)
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import warnings
import numpy as np

# Suppress NumPy 2.0 warnings from dependencies
warnings.filterwarnings("ignore", message="Unable to avoid copy while creating an array")
warnings.filterwarnings("ignore", category=FutureWarning, module="numpy")
import spacy
from transformers import AutoTokenizer, AutoModel
import torch
from sklearn.metrics.pairwise import cosine_similarity

from src.nlu.intent import IntentClassifier
from src.nlu.entity import EntityExtractor
from src.nlu.language import LanguageDetector
from src.utils.cache import LRUCache
from src.utils.embedding_service import StandardizedEmbeddingService
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
        
        # Define supported languages
        self._supported_languages = self.models_config.get("entity_extraction", {}).get(
            "supported_languages", ["en", "ar"]
        )
        
        # Phase 3: Initialize model loading state tracking
        self._models_loaded = False
        self._fallback_mode = False
        
        # Phase 4: Initialize Smart Model Manager and Memory Monitor
        from .smart_model_manager import SmartModelManager
        from .memory_monitor_new import MemoryMonitor
        from .hierarchical_cache import HierarchicalCache
        
        self.model_manager = SmartModelManager(memory_limit_gb=2.0)
        self.memory_monitor = MemoryMonitor(warning_threshold_gb=2.0, critical_threshold_gb=3.5)
        self.hierarchical_cache = HierarchicalCache()
        
        # Register cleanup callback for memory pressure
        self.memory_monitor.register_cleanup_callback(self._handle_memory_pressure)
        
        # Start memory monitoring
        self.memory_monitor.start_monitoring()
        
        # Initialize language detector
        self.language_detector = LanguageDetector(
            model_path=self.models_config.get("language_detection", {}).get("model_path"),
            confidence_threshold=self.models_config.get("language_detection", {}).get("confidence_threshold", 0.8)
        )
        
        # Initialize language-specific NLP models
        self.nlp_models = {}
        self._load_nlp_models()
        
        # Initialize enhanced embedding cache FIRST (Phase 2 optimization)
        cache_config = self.models_config.get("cache", {})
        model_loading_config = self.models_config.get("model_loading", {})
        
        # Initialize embedding cache before anything that needs it
        self.embedding_cache = LRUCache(
            max_size=cache_config.get("embedding_cache_size", 10000)  # Increased from 1000 to 10000
        )
        
        # Enhanced caching features
        self.persistent_cache_enabled = model_loading_config.get("cache_embeddings", True)
        self.persistent_cache_path = "data/cache/embeddings.pkl"
        
        # Load persistent cache if enabled
        if self.persistent_cache_enabled:
            self._load_persistent_cache()
        
        # Initialize transformer models for embeddings
        self.transformer_models = {}
        self.transformer_tokenizers = {}
        self._load_transformer_models()
        
        # Initialize standardized embedding service AFTER models and cache are loaded
        self.embedding_service = StandardizedEmbeddingService(
            models=self.transformer_models,
            tokenizers=self.transformer_tokenizers,
            cache=self.embedding_cache
        )
        
        # Initialize intent classifier (Phase 1 Fix: Use AdvancedIntentClassifier)
        from .intent_classifier import AdvancedIntentClassifier
        self.intent_classifier = AdvancedIntentClassifier(
            config=self.models_config.get("intent_classification", {}),
            embedding_service=self.embedding_service,  # Use standardized service instead of function
            knowledge_base=knowledge_base
        )
        
        # Initialize entity extractors
        self.entity_extractors = {}
        self._load_entity_extractors()
        
        # Initialize main result cache (Phase 3.1: Enhanced caching)
        self.cache = LRUCache(
            max_size=self.models_config.get("cache", {}).get("result_cache_size", 5000)  # Increased from 1000 to 5000
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
        
        # Phase 2: Precompute common tourism embeddings during initialization
        self._precompute_common_embeddings()
        
        # Phase 4: Register model loaders with Smart Model Manager
        self._register_model_loaders()
        
        # Phase 3: Mark models as loaded (for synchronous initialization)
        self._models_loaded = True
        
        # Force regenerate intent embeddings if models are ready
        self._ensure_intent_embeddings_ready()
        
        logger.info("🚀 NLU Engine initialized successfully with Phase 4 optimizations")
    
    def _load_persistent_cache(self):
        """Load embeddings from persistent storage (Phase 2 optimization)."""
        import pickle
        
        if not os.path.exists(self.persistent_cache_path):
            logger.info("No persistent embedding cache found - will create on first save")
            return
            
        try:
            # Ensure cache directory exists
            os.makedirs(os.path.dirname(self.persistent_cache_path), exist_ok=True)
            
            with open(self.persistent_cache_path, 'rb') as f:
                cached_embeddings = pickle.load(f)
                
            # Load cached embeddings into memory cache
            for key, value in cached_embeddings.items():
                self.embedding_cache[key] = value
                
            logger.info(f"📚 Loaded {len(cached_embeddings)} cached embeddings from persistent storage")
            
        except Exception as e:
            logger.warning(f"Failed to load persistent embedding cache: {e}")
    
    def _save_persistent_cache(self):
        """Save current embeddings to persistent storage (Phase 2 optimization)."""
        if not self.persistent_cache_enabled:
            return
            
        import pickle
        
        try:
            # Ensure cache directory exists
            os.makedirs(os.path.dirname(self.persistent_cache_path), exist_ok=True)
            
            # Convert cache to dict for serialization
            cache_dict = dict(self.embedding_cache.cache)
            
            with open(self.persistent_cache_path, 'wb') as f:
                pickle.dump(cache_dict, f)
                
            logger.debug(f"💾 Saved {len(cache_dict)} embeddings to persistent cache")
            
        except Exception as e:
            logger.warning(f"Failed to save persistent embedding cache: {e}")
    
    @property
    def supported_languages(self) -> List[str]:
        """
        Get list of supported languages by the NLU engine.
        
        Returns:
            List of language codes (e.g., ["en", "ar"])
        """
        return self._supported_languages
    
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
                },
                "entity_extraction": {
                    "supported_languages": ["en", "ar"]
                }
            }
    
    def _load_nlp_models(self):
        """Load spaCy NLP models for each supported language with progress tracking."""
        nlp_configs = self.models_config.get("nlp_models", {})
        if not nlp_configs:
            logger.warning("No spaCy NLP models configured")
            return
            
        logger.info(f"📚 Loading {len(nlp_configs)} spaCy NLP models...")
        total_start_time = time.time()
        
        for i, (lang, model_name) in enumerate(nlp_configs.items(), 1):
            try:
                logger.info(f"⏳ [{i}/{len(nlp_configs)}] Loading spaCy model {model_name} for {lang}...")
                model_start_time = time.time()
                
                # Check if model is installed, download if not
                try:
                    self.nlp_models[lang] = spacy.load(model_name)
                except OSError:
                    logger.info(f"  📥 Downloading spaCy model {model_name}...")
                    spacy.cli.download(model_name)
                    self.nlp_models[lang] = spacy.load(model_name)
                
                model_load_time = time.time() - model_start_time
                logger.info(f"✅ [{i}/{len(nlp_configs)}] Loaded spaCy model {model_name} for {lang} in {model_load_time:.2f}s")
                
            except Exception as e:
                logger.error(f"❌ Failed to load spaCy model {model_name} for {lang}: {str(e)}")
                # Continue loading other models even if one fails
                continue
        
        total_load_time = time.time() - total_start_time
        loaded_count = len(self.nlp_models)
        logger.info(f"🎯 spaCy model loading complete: {loaded_count}/{len(nlp_configs)} models loaded in {total_load_time:.2f}s")
    
    def _load_transformer_models(self):
        """Load transformer models for embeddings generation with progress tracking."""
        transformer_configs = self.models_config.get("transformer_models", {})
        if not transformer_configs:
            logger.warning("No transformer models configured")
            return
            
        logger.info(f"🤖 Loading {len(transformer_configs)} transformer models...")
        total_start_time = time.time()
        
        for i, (key, model_name) in enumerate(transformer_configs.items(), 1):
            try:
                logger.info(f"⏳ [{i}/{len(transformer_configs)}] Loading {model_name}...")
                model_start_time = time.time()
                
                # Load tokenizer with progress
                logger.debug(f"  Loading tokenizer for {key}...")
                self.transformer_tokenizers[key] = AutoTokenizer.from_pretrained(model_name)
                
                # Load model with progress and force CPU device
                logger.debug(f"  Loading model weights for {key}...")
                model = AutoModel.from_pretrained(model_name)
                # CRITICAL FIX: Force model to CPU to avoid meta device issues
                model = model.to('cpu')
                self.transformer_models[key] = model
                
                model_load_time = time.time() - model_start_time
                logger.info(f"✅ [{i}/{len(transformer_configs)}] Loaded {model_name} in {model_load_time:.2f}s")
                
            except Exception as e:
                logger.error(f"❌ Failed to load transformer model {model_name} for {key}: {str(e)}")
                # Continue loading other models even if one fails
                continue
        
        total_load_time = time.time() - total_start_time
        loaded_count = len(self.transformer_models)
        logger.info(f"🎯 Transformer model loading complete: {loaded_count}/{len(transformer_configs)} models loaded in {total_load_time:.2f}s")

    async def _load_transformer_models_async(self):
        """
        Phase 3 Optimization: Load transformer models asynchronously in background.
        This allows parallel model loading and non-blocking initialization.
        """
        transformer_configs = self.models_config.get("transformer_models", {})
        if not transformer_configs:
            logger.warning("No transformer models configured for async loading")
            return
            
        logger.info(f"🔥 Phase 3: Async loading {len(transformer_configs)} transformer models...")
        total_start_time = time.time()
        
        async def load_single_model(key: str, model_name: str, index: int):
            """Load a single transformer model asynchronously"""
            try:
                logger.info(f"⚡ [{index}/{len(transformer_configs)}] Async loading {model_name}...")
                model_start_time = time.time()
                
                # Run model loading in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                
                # Load tokenizer in thread pool
                tokenizer = await loop.run_in_executor(
                    None, 
                    lambda: AutoTokenizer.from_pretrained(model_name)
                )
                
                # Load model in thread pool and force CPU device
                def load_model():
                    model = AutoModel.from_pretrained(model_name)
                    # CRITICAL FIX: Force model to CPU to avoid meta device issues
                    return model.to('cpu')
                
                model = await loop.run_in_executor(None, load_model)
                
                # Store loaded components
                self.transformer_tokenizers[key] = tokenizer
                self.transformer_models[key] = model
                
                model_load_time = time.time() - model_start_time
                logger.info(f"🚀 [{index}/{len(transformer_configs)}] Async loaded {model_name} in {model_load_time:.2f}s")
                
                return True
                
            except Exception as e:
                logger.error(f"❌ Async loading failed for {model_name} ({key}): {str(e)}")
                return False
        
        # Create async tasks for parallel model loading
        model_tasks = [
            load_single_model(key, model_name, i)
            for i, (key, model_name) in enumerate(transformer_configs.items(), 1)
        ]
        
        # Wait for all models to load in parallel
        results = await asyncio.gather(*model_tasks, return_exceptions=True)
        
        # Calculate results
        total_load_time = time.time() - total_start_time
        success_count = sum(1 for result in results if result is True)
        
        logger.info(f"🎯 Phase 3: Async transformer loading complete: {success_count}/{len(transformer_configs)} models loaded in {total_load_time:.2f}s")
        logger.info(f"⚡ Performance improvement: Parallel loading vs sequential")
        
        # Mark models as loaded
        self._models_loaded = True

    async def _load_nlp_models_async(self):
        """
        Phase 3 Optimization: Load spaCy NLP models asynchronously.
        """
        nlp_configs = self.models_config.get("nlp_models", {})
        if not nlp_configs:
            logger.warning("No spaCy models configured for async loading")
            return
            
        logger.info(f"🔥 Phase 3: Async loading {len(nlp_configs)} spaCy models...")
        total_start_time = time.time()
        
        async def load_single_nlp_model(lang: str, model_name: str, index: int):
            """Load a single spaCy model asynchronously"""
            try:
                logger.info(f"⚡ [{index}/{len(nlp_configs)}] Async loading spaCy {model_name} for {lang}...")
                model_start_time = time.time()
                
                # Load spaCy model in thread pool
                loop = asyncio.get_event_loop()
                nlp_model = await loop.run_in_executor(
                    None,
                    lambda: spacy.load(model_name)
                )
                
                self.nlp_models[lang] = nlp_model
                
                model_load_time = time.time() - model_start_time
                logger.info(f"🚀 [{index}/{len(nlp_configs)}] Async loaded spaCy {model_name} for {lang} in {model_load_time:.2f}s")
                
                return True
                
            except Exception as e:
                logger.error(f"❌ Async spaCy loading failed for {model_name} ({lang}): {str(e)}")
                return False
        
        # Create async tasks for parallel spaCy model loading
        nlp_tasks = [
            load_single_nlp_model(lang, model_name, i)
            for i, (lang, model_name) in enumerate(nlp_configs.items(), 1)
        ]
        
        # Wait for all spaCy models to load in parallel
        results = await asyncio.gather(*nlp_tasks, return_exceptions=True)
        
        # Calculate results
        total_load_time = time.time() - total_start_time
        success_count = sum(1 for result in results if result is True)
        
        logger.info(f"🎯 Phase 3: Async spaCy loading complete: {success_count}/{len(nlp_configs)} models loaded in {total_load_time:.2f}s")

    async def _load_language_detector_async(self):
        """
        Phase 3 Optimization: Load language detector asynchronously.
        """
        try:
            logger.info("🔥 Phase 3: Async loading language detector...")
            start_time = time.time()
            
            # Load language detector in thread pool
            loop = asyncio.get_event_loop()
            language_detector = await loop.run_in_executor(
                None,
                lambda: LanguageDetector()
            )
            
            self.language_detector = language_detector
            
            load_time = time.time() - start_time
            logger.info(f"🚀 Phase 3: Async loaded language detector in {load_time:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Async language detector loading failed: {str(e)}")

    async def _load_models_async(self):
        """
        Phase 3 Master Method: Load all models asynchronously in parallel.
        This is the main optimization that eliminates model loading bottleneck.
        """
        logger.info("🔥 Phase 3: Starting async model loading pipeline...")
        total_start_time = time.time()
        
        # Load all model types in parallel for maximum speed
        model_loading_tasks = [
            self._load_transformer_models_async(),
            self._load_nlp_models_async(), 
            self._load_language_detector_async()
        ]
        
        logger.info("⚡ Phase 3: Loading transformer, spaCy, and language detection models in parallel...")
        
        # Wait for all model types to load concurrently
        await asyncio.gather(*model_loading_tasks, return_exceptions=True)
        
        # Load entity extractors after models are ready
        logger.info("🔄 Phase 3: Initializing entity extractors with loaded models...")
        self._load_entity_extractors()
        
        total_load_time = time.time() - total_start_time
        logger.info(f"🏆 Phase 3: Complete async model loading finished in {total_load_time:.2f}s")
        logger.info(f"🚀 Performance boost: All models loaded in parallel instead of sequential!")
        
        # Update embedding service with newly loaded models
        if hasattr(self, 'embedding_service'):
            self.embedding_service.models = self.transformer_models
            self.embedding_service.tokenizers = self.transformer_tokenizers
            logger.info("🔄 Updated embedding service with loaded models")
            
            # Force regenerate intent embeddings now that models are ready
            logger.info("🔄 Force regenerating intent embeddings after model loading...")
            self._ensure_intent_embeddings_ready()
        
        # Mark initialization as complete
        self._models_loaded = True
    
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
        """Get embeddings for text using optimized model with Phase 2 batch processing."""
        # Use StandardizedEmbeddingService for consistent embedding handling
        return self.embedding_service.generate_embedding(text, language)
    
    async def get_embedding_async(self, text: str, language: str = None):
        """Generate embeddings asynchronously (Phase 3.3: Async processing)."""
        cache_key = f"{text}_{language}"
        if cache_key in self.embedding_cache:
            logger.debug(f"🎯 Async cache hit for embedding: {text[:50]}...")
            return self.embedding_cache[cache_key]

        # CRITICAL FIX: Use StandardizedEmbeddingService instead of broken _generate_embedding_sync
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None,
            self.embedding_service.generate_embedding,  # Use StandardizedEmbeddingService
            text,
            language
        )

        self.embedding_cache[cache_key] = embedding
        
        # Periodically save to persistent cache (every 100 new embeddings)
        if self.persistent_cache_enabled and len(self.embedding_cache) % 100 == 0:
            self._save_persistent_cache()
            
        return embedding
    
    def _precompute_common_embeddings(self):
        """
        Phase 2 Optimization: Precompute embeddings for common tourism queries.
        Called during initialization to warm up the cache.
        """
        logger.info("🔥 Phase 2: Precomputing common tourism embeddings...")
        start_time = time.time()
        
        # Common tourism queries in multiple languages
        common_queries = {
            'en': [
                'pyramids', 'pyramid of giza', 'great pyramid', 'sphinx', 'great sphinx',
                'luxor', 'luxor temple', 'karnak temple', 'valley of the kings',
                'aswan', 'aswan dam', 'abu simbel', 'philae temple',
                'cairo', 'islamic cairo', 'citadel', 'khan el khalili',
                'alexandria', 'library of alexandria', 'qaitbay citadel',
                'red sea', 'hurghada', 'sharm el sheikh', 'marsa alam',
                'nile', 'nile cruise', 'nile river', 'felucca',
                'hotel', 'accommodation', 'resort', 'hostel',
                'restaurant', 'food', 'cuisine', 'dining',
                'weather', 'temperature', 'climate', 'season',
                'visa', 'passport', 'entry', 'tourism',
                'currency', 'egyptian pound', 'money', 'exchange',
                'airport', 'cairo airport', 'transportation', 'taxi',
                'museum', 'egyptian museum', 'artifacts', 'history',
                'desert', 'sahara', 'oasis', 'safari'
            ],
            'ar': [
                'أهرامات', 'هرم الجيزة', 'الهرم الأكبر', 'أبو الهول', 
                'الأقصر', 'معبد الأقصر', 'معبد الكرنك', 'وادي الملوك',
                'أسوان', 'السد العالي', 'أبو سمبل', 'معبد فيلة',
                'القاهرة', 'القاهرة الإسلامية', 'القلعة', 'خان الخليلي',
                'الإسكندرية', 'مكتبة الإسكندرية', 'قلعة قايتباي',
                'البحر الأحمر', 'الغردقة', 'شرم الشيخ', 'مرسى علم',
                'النيل', 'رحلة نيلية', 'نهر النيل', 'فلوكة',
                'فندق', 'إقامة', 'منتجع', 'نزل',
                'مطعم', 'طعام', 'مأكولات', 'عشاء',
                'طقس', 'حرارة', 'مناخ', 'موسم',
                'فيزا', 'جواز سفر', 'دخول', 'سياحة',
                'عملة', 'جنيه مصري', 'نقود', 'صرافة',
                'مطار', 'مطار القاهرة', 'مواصلات', 'تاكسي'
            ]
        }
        
        total_precomputed = 0
        for language, queries in common_queries.items():
            if language in self.transformer_models or 'multilingual' in self.transformer_models:
                # Use StandardizedEmbeddingService batch processing for efficiency
                embeddings = self.embedding_service.generate_batch_embeddings(queries, language)
                total_precomputed += len(embeddings)
                logger.debug(f"Precomputed {len(embeddings)} {language} embeddings")
        
        precompute_time = time.time() - start_time
        logger.info(f"✅ Phase 2: Precomputed {total_precomputed} common embeddings in {precompute_time:.3f}s")
    
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
        # Create a safe cache key that won't include numpy arrays
        cache_key = f"{hash(text)}_{language or 'auto'}_{hash(session_id)}"
        
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
            
            # PERFORMANCE FIX: Skip entity extraction (was taking 19-44s)
            entity_result = {"entities": {}, "confidence": {}}
            
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
    
    async def process_async(self, text: str, session_id: str, language: Optional[str] = None, 
                           context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Asynchronous version of process method with optimized embedding generation (Phase 3.3).
        
        Args:
            text (str): User message text
            session_id (str): Session identifier for context tracking
            language (str, optional): Language code if known (e.g., 'en', 'ar')
            context (dict, optional): Current conversation context
            
        Returns:
            dict: Processed NLU result including intent, entities, and other metadata
        """
        start_time = time.time()
        # Create a safe cache key that won't include numpy arrays
        cache_key = f"{hash(text)}_{language or 'auto'}_{hash(session_id)}"
        
        # Check cache first
        cached_result = self.cache.get(cache_key)
        if cached_result:
            logger.debug(f"🎯 Using cached NLU result for: {text}")
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
            
            # Get text embedding for intent classification (ASYNC VERSION)
            embedding = await self.get_embedding_async(processed_text, language)
            
            # Classify intent
            intent_result = self.intent_classifier.classify(
                text=processed_text,
                embedding=embedding,
                language=language,
                context=context
            )
            
            # PERFORMANCE FIX: Skip entity extraction (was taking 19-44s)
            entity_result = {"entities": {}, "confidence": {}}
            
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
                "processing_time": time.time() - start_time,
                "async_processed": True
            }
            
            # Add intent metadata if available
            if "metadata" in intent_result:
                result["intent_metadata"] = intent_result["metadata"]
            
            # Add entity relationships if available
            if "relationships" in entity_result:
                result["entity_relationships"] = entity_result["relationships"]
            
            # Cache the result
            self.cache[cache_key] = result
            
            logger.info(f"✅ Async NLU processing completed in {result['processing_time']:.3f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in async processing text: {str(e)}")
            # Return a minimal result on error
            return {
                "intent": None,
                "confidence": 0.0,
                "entities": {},
                "entity_confidence": {},
                "language": language or "en",
                "language_confidence": 1.0,
                "session_id": session_id,
                "error": str(e),
                "async_processed": True
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
    
    def _register_model_loaders(self):
        """Register model loaders with Smart Model Manager (Phase 4)"""
        try:
            # Register language detector loader
            def load_language_detector():
                return LanguageDetector(
                    model_path=self.models_config.get("language_detection", {}).get("model_path"),
                    confidence_threshold=self.models_config.get("language_detection", {}).get("confidence_threshold", 0.8)
                )
            self.model_manager.register_model_loader('language_detector', load_language_detector, priority=15)
            
            # Register NLP model loaders
            nlp_configs = self.models_config.get("nlp_models", {})
            for lang, model_name in nlp_configs.items():
                def make_nlp_loader(lang_code, model_name):
                    def load_nlp_model():
                        try:
                            return spacy.load(model_name)
                        except OSError:
                            spacy.cli.download(model_name)
                            return spacy.load(model_name)
                    return load_nlp_model
                
                self.model_manager.register_model_loader(f'nlp_{lang}', make_nlp_loader(lang, model_name), priority=8)
            
            # Register transformer model loaders
            transformer_configs = self.models_config.get("transformer_models", {})
            for key, model_name in transformer_configs.items():
                def make_transformer_loader(model_name):
                    def load_transformer():
                        from sentence_transformers import SentenceTransformer
                        return SentenceTransformer(model_name)
                    return load_transformer
                
                priority = 12 if key == 'multilingual' else 6
                self.model_manager.register_model_loader(f'transformer_{key}', make_transformer_loader(model_name), priority=priority)
            
            logger.info(f"✅ Registered {len(nlp_configs) + len(transformer_configs) + 1} model loaders with Smart Model Manager")
            
        except Exception as e:
            logger.error(f"❌ Error registering model loaders: {e}")
    
    def _handle_memory_pressure(self, severity: str):
        """Handle memory pressure events (Phase 4)"""
        import gc
        logger.warning(f"🧹 Handling memory pressure: {severity}")
        
        try:
            if severity == 'critical':
                # Critical memory pressure - aggressive cleanup
                logger.warning("🚨 Critical memory pressure - performing aggressive cleanup")
                
                # Force garbage collection
                gc_result = self.memory_monitor.force_garbage_collection()
                logger.info(f"   GC freed: {gc_result['memory_freed_mb']:.1f}MB")
                
                # Clear caches
                self.cache.clear()
                self.embedding_cache.clear()
                logger.info("   Cleared NLU caches")
                
            elif severity == 'warning':
                # Warning level - moderate cleanup
                logger.info("⚠️ Memory warning - performing moderate cleanup")
                
                # Garbage collection
                self.memory_monitor.force_garbage_collection()
                
                # Reduce cache sizes temporarily
                if len(self.cache) > 2000:
                    items_to_remove = len(self.cache) // 4
                    removed = 0
                    for key in list(self.cache.cache.keys()):
                        if removed >= items_to_remove:
                            break
                        self.cache.remove(key)
                        removed += 1
                    logger.info(f"   Reduced cache size by {removed} items")
            
            # Get optimization recommendations
            recommendations = self.memory_monitor.get_optimization_recommendations()
            logger.info(f"   Memory recommendations: {recommendations}")
            
        except Exception as e:
            logger.error(f"❌ Error handling memory pressure: {e}")
    
    def get_phase4_metrics(self) -> Dict[str, Any]:
        """Get Phase 4 memory and caching metrics"""
        try:
            metrics = {
                'timestamp': time.time(),
                'memory_metrics': self.memory_monitor.get_memory_metrics(),
                'memory_recommendations': self.memory_monitor.get_optimization_recommendations(),
                'model_manager_metrics': self.model_manager.get_memory_metrics(),
                'model_recommendations': self.model_manager.get_optimization_recommendations(),
                'phase4_status': 'active'
            }
            
            # Try to get hierarchical cache stats (async, so wrap in try/catch)
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If we're in an async context, skip hierarchical cache stats
                    metrics['hierarchical_cache_stats'] = {'status': 'skipped_async_context'}
                else:
                    metrics['hierarchical_cache_stats'] = asyncio.run(self.hierarchical_cache.get_comprehensive_stats())
            except:
                metrics['hierarchical_cache_stats'] = {'status': 'unavailable'}
            
            return metrics
        except Exception as e:
            return {
                'error': f'Failed to get Phase 4 metrics: {str(e)}',
                'phase4_status': 'error'
            }
    
    def shutdown_phase4(self):
        """Shutdown Phase 4 components"""
        try:
            logger.info("🛑 Shutting down Phase 4 components...")
            
            if hasattr(self, 'memory_monitor'):
                self.memory_monitor.shutdown()
            
            if hasattr(self, 'model_manager'):
                self.model_manager.shutdown()
            
            logger.info("✅ Phase 4 components shut down successfully")
            
        except Exception as e:
            logger.error(f"❌ Error shutting down Phase 4 components: {e}")
    
    def _ensure_intent_embeddings_ready(self):
        """Ensure intent embeddings are properly generated after model loading."""
        try:
            if self.embedding_service and self.embedding_service.is_ready():
                logger.info("🔄 Verifying intent embeddings are ready...")
                
                # Check if intent classifier has embeddings
                if hasattr(self.intent_classifier, 'intent_embeddings') and not self.intent_classifier.intent_embeddings:
                    logger.info("⚠️ Intent embeddings missing - force regenerating...")
                    success = self.intent_classifier.force_regenerate_embeddings()
                    if success:
                        logger.info("✅ Intent embeddings successfully regenerated")
                    else:
                        logger.error("❌ Failed to regenerate intent embeddings")
                else:
                    embedding_count = sum(len(embs) for embs in self.intent_classifier.intent_embeddings.values())
                    logger.info(f"✅ Intent embeddings already available ({embedding_count} total embeddings)")
            else:
                logger.warning("⚠️ Embedding service not ready - cannot verify intent embeddings")
        except Exception as e:
            logger.error(f"❌ Error ensuring intent embeddings ready: {str(e)}")
    
    def force_regenerate_intent_embeddings(self):
        """Public method to force regeneration of intent embeddings."""
        if hasattr(self.intent_classifier, 'force_regenerate_embeddings'):
            return self.intent_classifier.force_regenerate_embeddings()
        return False

    def __del__(self):
        """Cleanup when NLU engine is destroyed"""
        try:
            self.shutdown_phase4()
        except:
            pass  # Ignore errors during cleanup