# src/nlu/smart_model_manager.py
"""
Smart Model Manager for Egypt Tourism Chatbot NLU Engine.

This module provides intelligent model lifecycle management with:
- On-demand model loading/unloading
- Memory pressure monitoring
- Usage-based model prioritization
- Automatic cleanup of unused models
- Graceful degradation under memory constraints

Phase 4: Memory & Caching Optimization
"""
import gc
import logging
import time
import threading
import psutil
from typing import Dict, Any, Optional, List, Tuple, Callable
from collections import defaultdict
from datetime import datetime, timedelta
try:
    import torch
except ImportError:
    torch = None
    
try:
    import spacy
except ImportError:
    spacy = None

logger = logging.getLogger(__name__)

class ModelMetrics:
    """Track model usage and performance metrics"""
    
    def __init__(self):
        self.load_count = 0
        self.access_count = 0
        self.last_accessed = time.time()
        self.last_loaded = time.time()
        self.memory_usage_mb = 0.0
        self.load_time_avg = 0.0
        self.total_load_time = 0.0

class SmartModelManager:
    """
    Intelligent model lifecycle management system.
    
    Features:
    - Memory pressure-aware loading
    - Automatic model unloading based on usage patterns
    - Model prioritization and caching strategies
    - Real-time memory monitoring
    - Graceful degradation under constraints
    """
    
    def __init__(self, 
                 memory_limit_gb: float = 2.0,
                 cleanup_interval_minutes: int = 30,
                 max_idle_hours: int = 1,
                 warning_threshold: float = 0.8):
        """
        Initialize Smart Model Manager.
        
        Args:
            memory_limit_gb: Maximum memory limit for models (GB)
            cleanup_interval_minutes: How often to run cleanup (minutes)
            max_idle_hours: Unload models idle for this many hours
            warning_threshold: Memory warning threshold (0.0-1.0)
        """
        self.memory_limit = memory_limit_gb * 1024**3  # Convert to bytes
        self.cleanup_interval = cleanup_interval_minutes * 60  # Convert to seconds
        self.max_idle_time = max_idle_hours * 3600  # Convert to seconds
        self.warning_threshold = warning_threshold
        
        # Model storage and tracking
        self._loaded_models: Dict[str, Any] = {}
        self._model_loaders: Dict[str, Callable] = {}
        self._model_metrics: Dict[str, ModelMetrics] = defaultdict(ModelMetrics)
        self._model_priorities: Dict[str, int] = defaultdict(int)  # Higher = more important
        
        # Threading and locks
        self._lock = threading.RLock()
        self._cleanup_thread = None
        self._shutdown_event = threading.Event()
        
        # Configuration
        self.essential_models = {'language_detector', 'intent_classifier'}  # Never unload
        
        # Start background cleanup
        self._start_cleanup_thread()
        
        logger.info(f"🧠 Smart Model Manager initialized:")
        logger.info(f"   Memory limit: {memory_limit_gb:.1f}GB")
        logger.info(f"   Cleanup interval: {cleanup_interval_minutes}min")
        logger.info(f"   Max idle time: {max_idle_hours}h")
    
    def register_model_loader(self, model_key: str, loader_func: Callable, priority: int = 1):
        """
        Register a model loader function.
        
        Args:
            model_key: Unique identifier for the model
            loader_func: Function that loads and returns the model
            priority: Model priority (higher = more important, never unload if >10)
        """
        with self._lock:
            self._model_loaders[model_key] = loader_func
            self._model_priorities[model_key] = priority
            
        logger.debug(f"📝 Registered model loader: {model_key} (priority: {priority})")
    
    def get_model(self, model_key: str, force_load: bool = False) -> Optional[Any]:
        """
        Get a model with intelligent loading/caching.
        
        Args:
            model_key: Model identifier
            force_load: Force reload even if already loaded
            
        Returns:
            Loaded model or None if unavailable
        """
        with self._lock:
            # Update access metrics
            metrics = self._model_metrics[model_key]
            metrics.access_count += 1
            metrics.last_accessed = time.time()
            
            # Return cached model if available and not forcing reload
            if model_key in self._loaded_models and not force_load:
                logger.debug(f"🎯 Model cache hit: {model_key}")
                return self._loaded_models[model_key]
            
            # Check if we have a loader for this model
            if model_key not in self._model_loaders:
                logger.error(f"❌ No loader registered for model: {model_key}")
                return None
            
            # Check memory pressure before loading
            if not self._can_load_model(model_key):
                logger.warning(f"⚠️ Memory pressure - attempting cleanup before loading {model_key}")
                self._cleanup_unused_models(aggressive=True)
                
                if not self._can_load_model(model_key):
                    logger.error(f"❌ Cannot load {model_key} - insufficient memory")
                    return None
            
            # Load the model
            return self._load_model_safe(model_key)
    
    def _load_model_safe(self, model_key: str) -> Optional[Any]:
        """Safely load a model with error handling and metrics tracking."""
        try:
            logger.info(f"⏳ Loading model: {model_key}")
            start_time = time.time()
            start_memory = self._get_process_memory_gb()
            
            # Load model using registered loader
            loader_func = self._model_loaders[model_key]
            model = loader_func()
            
            # Calculate metrics
            load_time = time.time() - start_time
            end_memory = self._get_process_memory_gb()
            memory_increase = (end_memory - start_memory) * 1024  # Convert to MB
            
            # Update metrics
            metrics = self._model_metrics[model_key]
            metrics.load_count += 1
            metrics.last_loaded = time.time()
            metrics.memory_usage_mb = max(metrics.memory_usage_mb, memory_increase)
            metrics.total_load_time += load_time
            metrics.load_time_avg = metrics.total_load_time / metrics.load_count
            
            # Store model
            self._loaded_models[model_key] = model
            
            logger.info(f"✅ Model loaded: {model_key}")
            logger.info(f"   Load time: {load_time:.2f}s")
            logger.info(f"   Memory impact: +{memory_increase:.1f}MB")
            logger.info(f"   Total models: {len(self._loaded_models)}")
            
            return model
            
        except Exception as e:
            logger.error(f"❌ Failed to load model {model_key}: {str(e)}")
            return None
    
    def unload_model(self, model_key: str, force: bool = False) -> bool:
        """
        Unload a specific model.
        
        Args:
            model_key: Model to unload
            force: Force unload even if it's essential
            
        Returns:
            True if unloaded, False otherwise
        """
        with self._lock:
            if model_key not in self._loaded_models:
                return False
            
            # Check if model is essential
            if not force and (model_key in self.essential_models or self._model_priorities[model_key] > 10):
                logger.debug(f"🔒 Skipping unload of essential model: {model_key}")
                return False
            
            # Unload model
            try:
                del self._loaded_models[model_key]
                
                # Clear GPU memory if using PyTorch
                if torch and torch.cuda.is_available():
                    torch.cuda.empty_cache()
                
                # Force garbage collection
                gc.collect()
                
                logger.info(f"🗑️ Unloaded model: {model_key}")
                return True
                
            except Exception as e:
                logger.error(f"❌ Error unloading model {model_key}: {str(e)}")
                return False
    
    def _can_load_model(self, model_key: str) -> bool:
        """Check if we have enough memory to load a model."""
        current_memory = self._get_process_memory()
        available_memory = psutil.virtual_memory().available
        
        # Estimate model memory requirement
        estimated_model_memory = self._estimate_model_memory(model_key)
        
        # Check against limits
        memory_after_load = current_memory + estimated_model_memory
        
        return (memory_after_load < self.memory_limit and 
                estimated_model_memory < available_memory * 0.8)
    
    def _estimate_model_memory(self, model_key: str) -> int:
        """Estimate memory requirements for a model."""
        # Use historical data if available
        if model_key in self._model_metrics:
            historical_usage = self._model_metrics[model_key].memory_usage_mb * 1024**2
            if historical_usage > 0:
                return int(historical_usage * 1.2)  # Add 20% buffer
        
        # Default estimates based on model type
        model_estimates = {
            'language_detector': 50 * 1024**2,      # 50MB
            'intent_classifier': 200 * 1024**2,     # 200MB
            'nlp_en': 500 * 1024**2,                # 500MB for spaCy English
            'nlp_ar': 300 * 1024**2,                # 300MB for spaCy Arabic
            'transformer_multilingual': 1000 * 1024**2,  # 1GB for large transformers
            'transformer_en': 800 * 1024**2,        # 800MB
            'transformer_ar': 600 * 1024**2,        # 600MB
        }
        
        return model_estimates.get(model_key, 400 * 1024**2)  # Default 400MB
    
    def _cleanup_unused_models(self, aggressive: bool = False):
        """Clean up unused models based on usage patterns."""
        current_time = time.time()
        cleanup_threshold = self.max_idle_time
        
        if aggressive:
            cleanup_threshold = self.max_idle_time // 2  # More aggressive cleanup
        
        models_to_unload = []
        
        with self._lock:
            for model_key, model in self._loaded_models.items():
                metrics = self._model_metrics[model_key]
                idle_time = current_time - metrics.last_accessed
                
                # Skip essential models unless very aggressive
                if model_key in self.essential_models and not aggressive:
                    continue
                
                # Skip high-priority models
                if self._model_priorities[model_key] > 10:
                    continue
                
                # Mark for unloading if idle too long
                if idle_time > cleanup_threshold:
                    models_to_unload.append(model_key)
        
        # Unload marked models
        unloaded_count = 0
        for model_key in models_to_unload:
            if self.unload_model(model_key):
                unloaded_count += 1
        
        if unloaded_count > 0:
            logger.info(f"🧹 Cleanup: Unloaded {unloaded_count} unused models")
            
        return unloaded_count
    
    def _start_cleanup_thread(self):
        """Start background cleanup thread."""
        def cleanup_worker():
            while not self._shutdown_event.wait(self.cleanup_interval):
                try:
                    # Regular cleanup
                    self._cleanup_unused_models()
                    
                    # Check memory pressure
                    memory_usage_ratio = self._get_process_memory() / self.memory_limit
                    if memory_usage_ratio > self.warning_threshold:
                        logger.warning(f"⚠️ High memory usage: {memory_usage_ratio:.1%}")
                        self._cleanup_unused_models(aggressive=True)
                        
                except Exception as e:
                    logger.error(f"❌ Cleanup thread error: {str(e)}")
        
        self._cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        self._cleanup_thread.start()
        logger.debug("🧹 Cleanup thread started")
    
    def get_memory_metrics(self) -> Dict[str, Any]:
        """Get comprehensive memory and model metrics."""
        process_memory_gb = self._get_process_memory_gb()
        system_memory = psutil.virtual_memory()
        
        with self._lock:
            model_stats = {}
            for model_key, metrics in self._model_metrics.items():
                model_stats[model_key] = {
                    'loaded': model_key in self._loaded_models,
                    'access_count': metrics.access_count,
                    'load_count': metrics.load_count,
                    'last_accessed': datetime.fromtimestamp(metrics.last_accessed).isoformat(),
                    'memory_mb': metrics.memory_usage_mb,
                    'avg_load_time': metrics.load_time_avg,
                    'priority': self._model_priorities[model_key]
                }
        
        return {
            'timestamp': datetime.now().isoformat(),
            'process_memory_gb': process_memory_gb,
            'memory_limit_gb': self.memory_limit / 1024**3,
            'memory_usage_ratio': process_memory_gb / (self.memory_limit / 1024**3),
            'system_memory_gb': system_memory.total / 1024**3,
            'system_available_gb': system_memory.available / 1024**3,
            'system_usage_percent': system_memory.percent,
            'loaded_models_count': len(self._loaded_models),
            'registered_models_count': len(self._model_loaders),
            'models': model_stats
        }
    
    def get_optimization_recommendations(self) -> List[str]:
        """Get AI-powered optimization recommendations."""
        recommendations = []
        metrics = self.get_memory_metrics()
        
        # Memory usage recommendations
        if metrics['memory_usage_ratio'] > 0.9:
            recommendations.append("🚨 Critical: Memory usage >90% - consider increasing memory limit")
        elif metrics['memory_usage_ratio'] > 0.8:
            recommendations.append("⚠️ Warning: Memory usage >80% - monitor closely")
        
        # Model loading recommendations
        loaded_count = metrics['loaded_models_count']
        if loaded_count > 5:
            recommendations.append(f"📦 Consider reducing simultaneously loaded models ({loaded_count} current)")
        
        # Usage pattern recommendations
        with self._lock:
            rarely_used_models = []
            for model_key, model_metrics in self._model_metrics.items():
                if model_key in self._loaded_models:
                    last_access_hours = (time.time() - model_metrics.last_accessed) / 3600
                    if last_access_hours > 2 and model_key not in self.essential_models:
                        rarely_used_models.append(f"{model_key} ({last_access_hours:.1f}h ago)")
            
            if rarely_used_models:
                recommendations.append(f"⏰ Consider unloading rarely used models: {', '.join(rarely_used_models)}")
        
        if not recommendations:
            recommendations.append("✅ Memory usage is optimal")
        
        return recommendations
    
    def _get_process_memory(self) -> int:
        """Get current process memory usage in bytes."""
        return psutil.Process().memory_info().rss
    
    def _get_process_memory_gb(self) -> float:
        """Get current process memory usage in GB."""
        return self._get_process_memory() / 1024**3
    
    def shutdown(self):
        """Gracefully shutdown the model manager."""
        logger.info("🛑 Shutting down Smart Model Manager...")
        
        # Stop cleanup thread
        self._shutdown_event.set()
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=5)
        
        # Unload all models
        with self._lock:
            models_to_unload = list(self._loaded_models.keys())
            for model_key in models_to_unload:
                self.unload_model(model_key, force=True)
        
        logger.info("✅ Smart Model Manager shutdown complete")
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        try:
            self.shutdown()
        except:
            pass  # Ignore errors during cleanup 