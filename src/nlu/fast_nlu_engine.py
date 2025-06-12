"""
Phase 3 Optimization: Fast NLU Engine for immediate responses.
This lightweight engine provides instant responses using pattern matching
while the full NLU models load in the background.
"""

import time
import re
import logging
from typing import Dict, Any, Optional, List
import numpy as np

logger = logging.getLogger(__name__)


class FastNLUEngine:
    """
    Lightweight NLU engine for immediate responses during model loading.
    Uses pattern-based processing only - no heavy models required.
    """
    
    def __init__(self):
        """Initialize fast NLU engine with pattern-based processing."""
        logger.info("🚀 Phase 3: Initializing FastNLUEngine for immediate responses...")
        
        # Fast-path patterns from Phase 1 (enhanced for Phase 3)
        self.simple_patterns = {
            # Greetings & Social
            r'\b(hi|hello|hey|greetings|مرحبا|أهلا|السلام عليكم)\b': 'greeting',
            r'\b(bye|goodbye|farewell|وداعا|مع السلامة|إلى اللقاء)\b': 'farewell',
            r'\b(thanks?|thank you|شكرا|متشكر|ممنون)\b': 'gratitude',
            
            # Help & Information
            r'\b(help|info|information|معلومات|مساعدة|إزاي|كيف)\b': 'help_request',
            r'\b(what can you do|what do you know|ايه اللي تقدر|ايه خدماتك)\b': 'capabilities',
            
            # Major Attractions (Most Common Tourism Queries)
            r'\b(pyramid|pyramids?|هرم|أهرامات|giza)\b': 'attraction_pyramids',
            r'\b(sphinx|أبو الهول)\b': 'attraction_sphinx', 
            r'\b(luxor|الأقصر|temple|معبد)\b': 'attraction_luxor',
            r'\b(karnak|الكرنك)\b': 'attraction_luxor',
            r'\b(aswan|أسوان|dam|السد)\b': 'attraction_aswan',
            r'\b(abu simbel|أبو سمبل)\b': 'attraction_aswan',
            r'\b(alexandria|الإسكندرية|library|مكتبة)\b': 'attraction_alexandria',
            
            # Tourism Services
            r'\b(hotel|accommodation|stay|فندق|إقامة|منتجع)\b': 'service_hotel',
            r'\b(restaurant|food|eat|مطعم|طعام|أكل)\b': 'service_restaurant',
            
            # Cities & Destinations  
            r'\b(cairo|القاهرة|capital|عاصمة)\b': 'destination_cairo',
            r'\b(hurghada|الغردقة|red sea|البحر الأحمر)\b': 'destination_redsea',
            r'\b(sharm|شرم الشيخ)\b': 'destination_redsea',
            
            # Practical Information
            r'\b(weather|temperature|climate|طقس|حرارة|مناخ)\b': 'practical_weather',
            r'\b(visa|passport|entry|فيزا|جواز|دخول)\b': 'practical_visa',
            r'\b(currency|money|جنيه|نقود|صرافة)\b': 'practical_currency',
            r'\b(price|cost|how much|كام|سعر|تكلفة)\b': 'inquiry_price',
        }
        
        # Fast entity extraction patterns
        self.entity_patterns = {
            'location': [
                r'\b(cairo|giza|luxor|aswan|alexandria|hurghada|sharm|marsa alam)\b',
                r'\b(القاهرة|الجيزة|الأقصر|أسوان|الإسكندرية|الغردقة|شرم الشيخ)\b'
            ],
            'attraction': [
                r'\b(pyramid|sphinx|temple|museum|citadel|library)\b',
                r'\b(هرم|أبو الهول|معبد|متحف|قلعة|مكتبة)\b'
            ],
            'accommodation': [
                r'\b(hotel|resort|hostel|accommodation)\b',
                r'\b(فندق|منتجع|نزل|إقامة)\b'
            ]
        }
        
        # Fast response templates
        self.quick_responses = {
            'greeting': [
                "Hello! Welcome to Egypt Tourism Assistant! 🇪🇬",
                "مرحبا! أهلا بك في مساعد السياحة المصري! 🇪🇬"
            ],
            'farewell': [
                "Goodbye! Have a wonderful trip to Egypt! 🌟",
                "وداعا! استمتع برحلتك في مصر! 🌟"
            ],
            'attraction_pyramids': [
                "The Pyramids of Giza are Egypt's most iconic attraction! Built over 4,500 years ago, they're a must-see wonder of the ancient world. 🏺✨",
                "أهرامات الجيزة هي أشهر معالم مصر! بُنيت منذ أكثر من 4500 سنة وهي من عجائب العالم القديم التي يجب زيارتها! 🏺✨"
            ],
            'attraction_sphinx': [
                "The Great Sphinx stands guard at Giza, carved from a single limestone block. This mysterious monument is over 4,000 years old! 🦁",
                "أبو الهول العظيم يحرس الجيزة، منحوت من كتلة حجر جيري واحدة. هذا النصب الغامض عمره أكثر من 4000 سنة! 🦁"
            ],
            'service_hotel': [
                "Egypt offers amazing accommodations from luxury resorts to budget-friendly hotels. Would you like recommendations for a specific city? 🏨",
                "مصر تقدم إقامة رائعة من المنتجعات الفاخرة للفنادق الاقتصادية. هل تريد توصيات لمدينة معينة؟ 🏨"
            ],
            'help_request': [
                "I'm here to help with your Egypt travel plans! Ask me about attractions, hotels, restaurants, weather, or practical information. 🗺️",
                "أنا هنا للمساعدة في خطط سفرك لمصر! اسألني عن المعالم والفنادق والمطاعم والطقس أو المعلومات العملية. 🗺️"
            ],
            'fallback': [
                "I understand you're asking about Egypt tourism. Let me help you discover the wonders of Egypt! What specifically interests you? 🌟",
                "أفهم أنك تسأل عن السياحة في مصر. دعني أساعدك في اكتشاف عجائب مصر! ما الذي يهمك تحديداً؟ 🌟"
            ]
        }
        
        logger.info("✅ Phase 3: FastNLUEngine ready for instant responses")
    
    def process(self, text: str, session_id: str, language: Optional[str] = None) -> Dict[str, Any]:
        """
        Process user message using fast pattern-based matching.
        
        Args:
            text: User message
            session_id: Session identifier  
            language: Language code (optional)
            
        Returns:
            Fast NLU result with intent and basic entities
        """
        start_time = time.time()
        
        # Detect language from text patterns if not provided
        if not language:
            language = self._detect_language_fast(text)
        
        # Fast intent classification using patterns
        intent = self._classify_intent_fast(text)
        
        # Fast entity extraction
        entities = self._extract_entities_fast(text)
        
        # Generate quick response
        response_text = self._generate_quick_response(intent, language)
        
        processing_time = time.time() - start_time
        
        logger.debug(f"🚀 FastNLU processed '{text[:30]}...' in {processing_time:.4f}s")
        
        return {
            "text": text,
            "processed_text": text.lower().strip(),
            "language": language,
            "language_confidence": 0.8,  # Default confidence for fast detection
            "intent": intent,
            "intent_confidence": 0.9,  # High confidence for pattern matches
            "entities": entities,
            "entity_confidence": {entity_type: [0.8] * len(entity_list) 
                                 for entity_type, entity_list in entities.items()},
            "session_id": session_id,
            "processing_time": processing_time,
            "fast_path": True,  # Mark as fast-path processing
            "response_text": response_text,
            "fallback_mode": True  # Indicate this is fallback processing
        }
    
    def _detect_language_fast(self, text: str) -> str:
        """Fast language detection using character patterns."""
        # Check for Arabic characters
        arabic_chars = re.findall(r'[\u0600-\u06FF]', text)
        if arabic_chars:
            return "ar"
        return "en"
    
    def _classify_intent_fast(self, text: str) -> str:
        """Fast intent classification using regex patterns."""
        text_lower = text.lower()
        
        # Check patterns in order of specificity
        for pattern, intent in self.simple_patterns.items():
            if re.search(pattern, text_lower, re.IGNORECASE):
                logger.debug(f"🎯 Fast intent match: '{intent}' for pattern: {pattern}")
                return intent
        
        # Default fallback intent
        return "general_query"
    
    def _extract_entities_fast(self, text: str) -> Dict[str, List[str]]:
        """Fast entity extraction using regex patterns."""
        entities = {}
        text_lower = text.lower()
        
        for entity_type, patterns in self.entity_patterns.items():
            matches = []
            for pattern in patterns:
                found = re.findall(pattern, text_lower, re.IGNORECASE)
                matches.extend([match.title() for match in found])
            
            if matches:
                # Remove duplicates while preserving order
                entities[entity_type] = list(dict.fromkeys(matches))
        
        return entities
    
    def _generate_quick_response(self, intent: str, language: str) -> str:
        """Generate a quick response based on intent and language."""
        if intent in self.quick_responses:
            responses = self.quick_responses[intent]
            # Choose response based on language (0=English, 1=Arabic if available)
            if language == "ar" and len(responses) > 1:
                return responses[1]
            else:
                return responses[0]
        else:
            # Fallback response
            fallback_responses = self.quick_responses['fallback']
            if language == "ar" and len(fallback_responses) > 1:
                return fallback_responses[1]
            else:
                return fallback_responses[0]
    
    async def process_async(self, text: str, session_id: str, language: Optional[str] = None) -> Dict[str, Any]:
        """Async version of process (just calls sync version for fast processing)."""
        return self.process(text, session_id, language)
    
    def is_models_loaded(self) -> bool:
        """FastNLU doesn't need models, so always ready."""
        return True
    
    def get_embedding_async(self, text: str, language: str = None):
        """Fast fallback embedding (random vector for compatibility)."""
        logger.debug(f"🚀 FastNLU providing fallback embedding for: {text[:30]}...")
        return np.random.rand(768)  # Standard 768D embedding for compatibility


class LazyNLUEngine:
    """
    Phase 3 Optimization: Lazy loading NLU engine with fast fallback.
    Provides immediate responses while full models load in background.
    """
    
    def __init__(self, models_config: str, knowledge_base):
        """Initialize lazy loading NLU engine."""
        self.models_config = models_config
        self.knowledge_base = knowledge_base
        
        # Start with fast engine for immediate responses
        self.fast_engine = FastNLUEngine()
        self.full_engine = None
        self._models_loading = False
        self._models_loaded = False
        
        logger.info("🚀 Phase 3: LazyNLUEngine initialized with FastNLU fallback")
    
    async def initialize_full_engine(self):
        """Initialize the full NLU engine asynchronously."""
        if self._models_loading or self._models_loaded:
            return
            
        self._models_loading = True
        logger.info("🔥 Phase 3: Starting async full NLU engine initialization...")
        
        try:
            # Import and create full engine
            from .engine import NLUEngine
            
            # Create full engine (will load all models)
            self.full_engine = NLUEngine(self.models_config, self.knowledge_base)
            
            # Load models asynchronously
            await self.full_engine._load_models_async()
            
            self._models_loaded = True
            self._models_loading = False
            
            logger.info("🎯 Phase 3: Full NLU engine ready - switching from fast fallback")
            
        except Exception as e:
            logger.error(f"❌ Phase 3: Failed to initialize full NLU engine: {e}")
            self._models_loading = False
            # Continue using fast engine as fallback
    
    def get_engine(self):
        """Get the appropriate engine (fast or full)."""
        if self._models_loaded and self.full_engine:
            return self.full_engine
        return self.fast_engine
    
    def process(self, text: str, session_id: str, language: Optional[str] = None, 
                context: Optional[Dict] = None) -> Dict[str, Any]:
        """Process using appropriate engine."""
        engine = self.get_engine()
        
        if engine == self.fast_engine:
            logger.debug("🚀 Using FastNLU for immediate response")
            return engine.process(text, session_id, language)
        else:
            logger.debug("🎯 Using full NLU engine")
            return engine.process(text, session_id, language, context)
    
    async def process_async(self, text: str, session_id: str, language: Optional[str] = None,
                          context: Optional[Dict] = None) -> Dict[str, Any]:
        """Async process using appropriate engine."""
        engine = self.get_engine()
        return await engine.process_async(text, session_id, language, context)
    
    @property
    def models_loaded(self) -> bool:
        """Check if full models are loaded."""
        return self._models_loaded
    
    @property
    def embedding_cache(self):
        """Access embedding cache from active engine."""
        engine = self.get_engine()
        return getattr(engine, 'embedding_cache', {})
    
    def _batch_embeddings(self, *args, **kwargs):
        """Delegate to active engine."""
        engine = self.get_engine()
        if hasattr(engine, '_batch_embeddings'):
            return engine._batch_embeddings(*args, **kwargs)
        return {}
    
    def get_learning_stats(self):
        """Get learning stats from active engine."""
        engine = self.get_engine()
        if hasattr(engine, 'get_learning_stats'):
            return engine.get_learning_stats()
        return {"fast_mode": True, "full_engine_loaded": self._models_loaded} 