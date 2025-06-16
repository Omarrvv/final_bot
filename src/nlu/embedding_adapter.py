"""
Simple embedding adapter for NLU layer.
Provides embedding functionality without violating architectural layers.
"""
import numpy as np
import torch
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class InfrastructureEmbeddingService:
    """
    Simple embedding service for infrastructure layer.
    Avoids importing from services layer to maintain clean architecture.
    
    CRITICAL FIX: Auto-loads essential models to ensure real AI functionality
    """
    
    def __init__(self, models: Dict[str, Any] = None, tokenizers: Dict[str, Any] = None, cache=None):
        self.models = models or {}
        self.tokenizers = tokenizers or {}
        self.cache = cache
        self._stats = {"embeddings_generated": 0, "cache_hits": 0}
        
        # CRITICAL FIX: Auto-load essential models if none provided
        if not self.models and not self.tokenizers:
            logger.info("🚀 CRITICAL FIX: Auto-loading essential transformer models...")
            self._auto_load_essential_models()
    
    def _auto_load_essential_models(self):
        """
        CRITICAL FIX: Auto-load essential transformer models
        Ensures the service is ready with real AI capabilities
        """
        try:
            from transformers import AutoTokenizer, AutoModel
            
            # Load essential lightweight model for embeddings
            essential_model_name = "sentence-transformers/all-MiniLM-L6-v2"
            
            logger.info(f"📦 Loading essential model: {essential_model_name}")
            
            # Load model and tokenizer
            tokenizer = AutoTokenizer.from_pretrained(essential_model_name)
            model = AutoModel.from_pretrained(essential_model_name)

            # CRITICAL FIX: Force model to CPU to avoid meta device issues
            model = model.to('cpu')

            # Store in dictionaries
            self.tokenizers["essential"] = tokenizer
            self.models["essential"] = model
            
            logger.info("✅ CRITICAL FIX: Essential transformer models loaded successfully!")
            logger.info(f"   - Models loaded: {list(self.models.keys())}")
            logger.info(f"   - Service ready: {self.is_ready()}")
            
        except Exception as e:
            logger.error(f"❌ CRITICAL ERROR: Failed to auto-load essential models: {e}")
            logger.error("   Service will fall back to zero embeddings")
    
    def is_ready(self) -> bool:
        """Check if service is ready to generate embeddings."""
        ready = len(self.models) > 0
        if ready:
            logger.debug(f"✅ Embedding service ready with {len(self.models)} models")
        else:
            logger.warning("❌ Embedding service NOT ready - no models loaded")
        return ready
    
    def generate_embedding(self, text: str, language: Optional[str] = None) -> np.ndarray:
        """Generate embedding for text."""
        # Use cache if available (CRITICAL FIX: Handle different cache types)
        if self.cache:
            cache_key = f"emb_{hash(text)}_{language}"
            try:
                # Try dict-like cache first
                if hasattr(self.cache, 'get'):
                    cached = self.cache.get(cache_key)
                    if cached is not None:
                        self._stats["cache_hits"] += 1
                        return np.array(cached)
                # Try LRUCache-like cache
                elif hasattr(self.cache, '__getitem__'):
                    try:
                        cached = self.cache[cache_key]
                        if cached is not None:
                            self._stats["cache_hits"] += 1
                            return np.array(cached)
                    except KeyError:
                        pass  # Cache miss
            except Exception as cache_error:
                logger.debug(f"Cache access error: {cache_error}")
        
        # Select best model for language
        model_key = self.select_best_model(language)
        if not model_key or model_key not in self.models:
            logger.warning(f"❌ No suitable model found for language: {language}")
            # Return zero embedding as fallback
            return np.zeros(768, dtype=np.float32)
        
        try:
            model = self.models[model_key]
            tokenizer = self.tokenizers.get(model_key)
            
            if tokenizer and model:
                # Tokenize and generate embedding
                inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
                with torch.no_grad():
                    outputs = model(**inputs)
                    # Use mean pooling of last hidden states
                    embedding = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
                
                # Ensure correct dimensionality
                if embedding.shape == ():
                    embedding = embedding.reshape(1)
                
                # Cache the result (CRITICAL FIX: Handle different cache types)
                if self.cache:
                    try:
                        # Try dict-like cache first
                        if hasattr(self.cache, 'set'):
                            self.cache.set(cache_key, embedding.tolist())
                        elif hasattr(self.cache, '__setitem__'):
                            self.cache[cache_key] = embedding.tolist()
                        else:
                            logger.debug("Cache doesn't support setting values")
                    except Exception as cache_error:
                        logger.debug(f"Cache set error: {cache_error}")
                
                self._stats["embeddings_generated"] += 1
                logger.debug(f"✅ Generated embedding of shape {embedding.shape} for text: {text[:50]}...")
                return embedding
            
        except Exception as e:
            logger.error(f"❌ Error generating embedding: {e}")
            # Return zero embedding on error
        
        logger.warning("⚠️  Falling back to zero embedding")
        return np.zeros(768, dtype=np.float32)
    
    def generate_batch_embeddings(self, texts: List[str], language: Optional[str] = None) -> List[np.ndarray]:
        """
        CRITICAL FIX: Generate embeddings for multiple texts in batch.
        Expected by intent classifier for processing intent examples.
        """
        logger.debug(f"🔧 Generating batch embeddings for {len(texts)} texts")
        
        embeddings = []
        for text in texts:
            try:
                embedding = self.generate_embedding(text, language)
                embeddings.append(embedding)
            except Exception as e:
                logger.warning(f"❌ Failed to generate embedding for text: {text[:50]}... - {e}")
                # Use zero embedding as fallback for failed items
                embeddings.append(np.zeros(768, dtype=np.float32))
        
        logger.debug(f"✅ Generated {len(embeddings)} batch embeddings")
        return embeddings
    
    def select_best_model(self, language: Optional[str] = None) -> Optional[str]:
        """Select best model for language."""
        if not self.models:
            return None
        
        # Simple model selection logic
        if language == "ar":
            # Prefer multilingual models for Arabic
            for key in self.models.keys():
                if "multilingual" in key.lower() or "bert" in key.lower():
                    return key
        
        # Return first available model (essential model for auto-loaded case)
        return list(self.models.keys())[0]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        stats = self._stats.copy()
        stats.update({
            "models_loaded": len(self.models),
            "model_names": list(self.models.keys()),
            "is_ready": self.is_ready()
        })
        return stats 