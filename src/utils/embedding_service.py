"""
Standardized Embedding Service

This module provides a unified interface for generating embeddings across the entire codebase.
All embedding generation should go through this service to ensure consistency.
"""

import numpy as np
import torch
import time
import logging
from typing import Union, List, Optional, Dict, Any
from transformers import AutoModel, AutoTokenizer

logger = logging.getLogger(__name__)

class StandardizedEmbeddingService:
    """
    Unified embedding service for the entire application.
    Handles model selection, fallback logic, caching, and standardization.
    """
    
    def __init__(self, models: Dict[str, Any] = None, tokenizers: Dict[str, Any] = None, cache=None):
        """
        Initialize the standardized embedding service.
        
        Args:
            models: Dictionary of loaded transformer models {key: model} (optional)
            tokenizers: Dictionary of loaded tokenizers {key: tokenizer} (optional)
            cache: Optional cache for embeddings
        """
        self.models = models or {}
        self.tokenizers = tokenizers or {}
        self.cache = cache
        self.standard_dimension = 768  # Standard embedding dimension
        
        # Model priority order for fallback
        self.model_priority = ['multilingual', 'en', 'ar']
        
        logger.info(f"✅ Initialized StandardizedEmbeddingService with {len(self.models)} models")
        
    def is_ready(self) -> bool:
        """Check if the service is ready to generate embeddings."""
        return len(self.models) > 0 and len(self.tokenizers) > 0
    
    def get_available_models(self) -> List[str]:
        """Get list of available model keys."""
        return list(self.models.keys())
    
    def select_best_model(self, language: Optional[str] = None) -> Optional[str]:
        """
        Select the best available model for the given language.
        
        Args:
            language: Target language code (e.g., 'en', 'ar')
            
        Returns:
            Model key or None if no models available
        """
        if not self.models:
            return None
            
        # First priority: exact language match
        if language and language in self.models:
            return language
            
        # Second priority: model priority order
        for model_key in self.model_priority:
            if model_key in self.models:
                return model_key
                
        # Last resort: any available model
        return next(iter(self.models.keys()))
    
    def generate_embedding(self, text: str, language: Optional[str] = None) -> np.ndarray:
        """
        Generate a standardized embedding for the given text.
        
        Args:
            text: Text to embed
            language: Target language (optional)
            
        Returns:
            Numpy array with standardized dimensions
        """
        if not text:
            logger.warning("Empty text provided for embedding generation")
            return self._get_fallback_embedding()
            
        # Check cache first
        if self.cache:
            cache_key = f"{text}_{language}"
            if hasattr(self.cache, '__contains__') and cache_key in self.cache:
                cached = self.cache[cache_key] if hasattr(self.cache, '__getitem__') else self.cache.get(cache_key)
                if cached is not None:
                    return self._standardize_embedding(cached)
        
        # Select appropriate model
        model_key = self.select_best_model(language)
        if not model_key:
            logger.error("No embedding models available!")
            return self._get_fallback_embedding()
            
        model = self.models[model_key]
        tokenizer = self.tokenizers[model_key]
        
        try:
            logger.debug(f"🧠 Generating embedding using {model_key} for: {text[:50]}...")
            start_time = time.time()
            
            # Tokenize
            inputs = tokenizer(
                text, 
                return_tensors="pt", 
                padding=True, 
                truncation=True, 
                max_length=512
            )
            
            # Generate embedding
            with torch.no_grad():
                outputs = model(**inputs)
            
            # Extract embedding based on model type
            if hasattr(outputs, "pooler_output") and outputs.pooler_output is not None:
                embedding = outputs.pooler_output.cpu().numpy()
            else:
                # Mean pooling fallback
                attention_mask = inputs["attention_mask"]
                token_embeddings = outputs.last_hidden_state
                input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
                sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
                sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
                embedding = (sum_embeddings / sum_mask).cpu().numpy()
            
            # Standardize the embedding - handle potential tuple returns
            standardized = self._standardize_embedding(embedding)
            
            # Validate the standardized embedding
            if not self.validate_embedding(standardized):
                logger.warning(f"Generated invalid embedding, using fallback")
                standardized = self._get_fallback_embedding()
            
            # Cache the result
            if self.cache:
                cache_key = f"{text}_{language}"
                if hasattr(self.cache, '__setitem__'):
                    self.cache[cache_key] = standardized
                elif hasattr(self.cache, 'set'):
                    self.cache.set(cache_key, standardized)
            
            duration = time.time() - start_time
            logger.debug(f"✅ Generated embedding in {duration:.3f}s, shape: {standardized.shape}")
            
            return standardized
            
        except Exception as e:
            logger.error(f"❌ Embedding generation failed with {model_key}: {str(e)}")
            return self._get_fallback_embedding()
    
    def generate_batch_embeddings(self, texts: List[str], language: Optional[str] = None) -> Dict[str, np.ndarray]:
        """
        Generate embeddings for multiple texts efficiently.
        
        Args:
            texts: List of texts to embed
            language: Target language (optional)
            
        Returns:
            Dictionary mapping texts to embeddings
        """
        if not texts:
            return {}
            
        results = {}
        uncached_texts = []
        
        # Check cache for all texts
        for text in texts:
            if self.cache:
                cache_key = f"{text}_{language}"
                if hasattr(self.cache, '__contains__') and cache_key in self.cache:
                    cached = self.cache[cache_key] if hasattr(self.cache, '__getitem__') else self.cache.get(cache_key)
                    if cached is not None:
                        results[text] = self._standardize_embedding(cached)
                        continue
            uncached_texts.append(text)
        
        if not uncached_texts:
            return results
            
        # Select appropriate model
        model_key = self.select_best_model(language)
        if not model_key:
            logger.error("No embedding models available for batch generation!")
            for text in uncached_texts:
                results[text] = self._get_fallback_embedding()
            return results
            
        model = self.models[model_key]
        tokenizer = self.tokenizers[model_key]
        
        try:
            logger.info(f"🔥 Batch generating {len(uncached_texts)} embeddings using {model_key}")
            start_time = time.time()
            
            # Batch tokenization
            inputs = tokenizer(
                uncached_texts,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            )
            
            # Generate batch embeddings
            with torch.no_grad():
                outputs = model(**inputs)
            
            # Extract embeddings
            if hasattr(outputs, "pooler_output") and outputs.pooler_output is not None:
                batch_embeddings = outputs.pooler_output.cpu().numpy()
            else:
                # Mean pooling for batch
                attention_mask = inputs["attention_mask"]
                token_embeddings = outputs.last_hidden_state
                input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
                sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
                sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
                batch_embeddings = (sum_embeddings / sum_mask).cpu().numpy()
            
            # Process each embedding
            for i, text in enumerate(uncached_texts):
                embedding = batch_embeddings[i]
                standardized = self._standardize_embedding(embedding)
                results[text] = standardized
                
                # Cache the result
                if self.cache:
                    cache_key = f"{text}_{language}"
                    if hasattr(self.cache, '__setitem__'):
                        self.cache[cache_key] = standardized
                    elif hasattr(self.cache, 'set'):
                        self.cache.set(cache_key, standardized)
            
            duration = time.time() - start_time
            logger.info(f"✅ Batch generated {len(uncached_texts)} embeddings in {duration:.3f}s")
            
        except Exception as e:
            logger.error(f"❌ Batch embedding generation failed with {model_key}: {str(e)}")
            # Fallback to individual generation
            for text in uncached_texts:
                results[text] = self.generate_embedding(text, language)
        
        return results
    
    def _standardize_embedding(self, embedding: Union[np.ndarray, List[float]]) -> np.ndarray:
        """
        Standardize an embedding to consistent format and dimensions.
        
        Args:
            embedding: Raw embedding in various formats
            
        Returns:
            Standardized numpy array
        """
        # Convert to numpy array
        if isinstance(embedding, list):
            embedding = np.array(embedding)
        elif not isinstance(embedding, np.ndarray):
            logger.warning(f"Unexpected embedding type: {type(embedding)}")
            return self._get_fallback_embedding()
        
        # Handle different dimensionalities
        if embedding.ndim == 0:
            # Scalar - expand to standard dimension
            logger.warning("Converting scalar embedding to standard dimension")
            result = np.zeros(self.standard_dimension)
            result.fill(float(embedding))
            return result
        elif embedding.ndim == 1:
            # 1D array - this is the expected format
            return embedding
        elif embedding.ndim == 2:
            # 2D array - take the first row
            if embedding.shape[0] > 0:
                return embedding[0]
            else:
                logger.warning("Empty 2D embedding array")
                return self._get_fallback_embedding()
        else:
            # Higher dimensions - flatten
            return embedding.flatten()
    
    def _get_fallback_embedding(self) -> np.ndarray:
        """Generate a fallback embedding when normal generation fails."""
        logger.warning("Using fallback random embedding")
        return np.random.rand(self.standard_dimension).astype(np.float32)
    
    def validate_embedding(self, embedding: np.ndarray) -> bool:
        """
        Validate that an embedding meets the expected standards.
        
        Args:
            embedding: Embedding to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(embedding, np.ndarray):
            return False
            
        if embedding.ndim != 1:
            return False
            
        if embedding.size == 0:
            return False
            
        if not np.isfinite(embedding).all():
            return False
            
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        return {
            'available_models': self.get_available_models(),
            'standard_dimension': self.standard_dimension,
            'is_ready': self.is_ready(),
            'cache_available': self.cache is not None
        } 