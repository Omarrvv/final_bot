# src/nlu/hierarchical_cache.py
"""
Hierarchical Cache System for Egypt Tourism Chatbot NLU Engine.

This module provides a 3-tier caching system:
- L1 Cache (Memory): Hot data, <100ms access
- L2 Cache (Redis): Warm data, <500ms access  
- L3 Cache (Disk): Cold data, <2s access

Features:
- Automatic cache promotion/demotion
- Memory-efficient data management
- Fault-tolerant with graceful degradation
- Performance monitoring and optimization

Phase 4: Memory & Caching Optimization
"""
import asyncio
import hashlib
import json
import logging
import os
import pickle
import time
import threading
from typing import Dict, Any, Optional, List, Union, Callable
from datetime import datetime, timedelta
from pathlib import Path

# Try to import Redis, fall back gracefully
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    from src.utils.cache import LRUCache
except ImportError:
    from utils.cache import LRUCache

logger = logging.getLogger(__name__)

class CacheMetrics:
    """Track cache performance metrics"""
    
    def __init__(self):
        self.l1_hits = 0
        self.l2_hits = 0  
        self.l3_hits = 0
        self.misses = 0
        self.promotions = 0
        self.evictions = 0
        self.total_requests = 0
        self.avg_access_time = 0.0
        self.last_reset = time.time()
    
    def record_hit(self, level: int, access_time: float):
        """Record a cache hit at specified level"""
        self.total_requests += 1
        
        if level == 1:
            self.l1_hits += 1
        elif level == 2:
            self.l2_hits += 1
        elif level == 3:
            self.l3_hits += 1
            
        # Update rolling average
        alpha = 0.1  # Smoothing factor
        self.avg_access_time = (1 - alpha) * self.avg_access_time + alpha * access_time
    
    def record_miss(self):
        """Record a cache miss"""
        self.total_requests += 1
        self.misses += 1
    
    def record_promotion(self):
        """Record a cache promotion"""
        self.promotions += 1
    
    def record_eviction(self):
        """Record a cache eviction"""
        self.evictions += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        total_hits = self.l1_hits + self.l2_hits + self.l3_hits
        hit_rate = total_hits / max(self.total_requests, 1)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_requests': self.total_requests,
            'total_hits': total_hits,
            'hit_rate': hit_rate,
            'miss_rate': self.misses / max(self.total_requests, 1),
            'l1_hit_rate': self.l1_hits / max(self.total_requests, 1),
            'l2_hit_rate': self.l2_hits / max(self.total_requests, 1),
            'l3_hit_rate': self.l3_hits / max(self.total_requests, 1),
            'promotions': self.promotions,
            'evictions': self.evictions,
            'avg_access_time_ms': self.avg_access_time * 1000,
            'uptime_hours': (time.time() - self.last_reset) / 3600
        }
    
    def reset(self):
        """Reset all metrics"""
        self.__init__()

class L1MemoryCache:
    """Level 1: High-speed memory cache for hot data"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.cache = LRUCache(max_size=max_size, ttl=ttl)
        self.max_size = max_size
        self.ttl = ttl
        
    async def get(self, key: str) -> Optional[Any]:
        """Get item from L1 cache"""
        return self.cache.get(key)
    
    async def set(self, key: str, value: Any) -> bool:
        """Set item in L1 cache"""
        try:
            self.cache[key] = value
            return True
        except Exception as e:
            logger.error(f"L1 cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete item from L1 cache"""
        return self.cache.remove(key)
    
    async def clear(self) -> bool:
        """Clear L1 cache"""
        self.cache.clear()
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get L1 cache statistics"""
        return {
            'type': 'L1_Memory',
            'size': len(self.cache),
            'max_size': self.max_size,
            'usage_ratio': len(self.cache) / self.max_size,
            'ttl_seconds': self.ttl
        }

class L2RedisCache:
    """Level 2: Redis cache for warm data"""
    
    def __init__(self, redis_url: str = None, max_size: int = 5000, ttl: int = 7200):
        self.redis_url = redis_url or "redis://localhost:6379/1"
        self.max_size = max_size
        self.ttl = ttl
        self.client = None
        self.connected = False
        self.key_prefix = "nlu_cache:"
        
    async def _ensure_connection(self) -> bool:
        """Ensure Redis connection is established"""
        if self.connected and self.client:
            return True
            
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available - L2 cache disabled")
            return False
            
        try:
            self.client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_timeout=2.0,
                socket_connect_timeout=2.0
            )
            await self.client.ping()
            self.connected = True
            logger.debug(f"L2 Redis cache connected: {self.redis_url}")
            return True
        except Exception as e:
            logger.warning(f"L2 Redis cache connection failed: {e}")
            self.connected = False
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """Get item from L2 cache"""
        if not await self._ensure_connection():
            return None
            
        try:
            redis_key = f"{self.key_prefix}{key}"
            data = await self.client.get(redis_key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.debug(f"L2 cache get error: {e}")
            return None
    
    async def set(self, key: str, value: Any) -> bool:
        """Set item in L2 cache"""
        if not await self._ensure_connection():
            return False
            
        try:
            redis_key = f"{self.key_prefix}{key}"
            data = json.dumps(value, default=str)
            await self.client.setex(redis_key, self.ttl, data)
            return True
        except Exception as e:
            logger.debug(f"L2 cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete item from L2 cache"""
        if not await self._ensure_connection():
            return False
            
        try:
            redis_key = f"{self.key_prefix}{key}"
            result = await self.client.delete(redis_key)
            return result > 0
        except Exception as e:
            logger.debug(f"L2 cache delete error: {e}")
            return False
    
    async def clear(self) -> bool:
        """Clear L2 cache"""
        if not await self._ensure_connection():
            return False
            
        try:
            pattern = f"{self.key_prefix}*"
            keys = await self.client.keys(pattern)
            if keys:
                await self.client.delete(*keys)
            return True
        except Exception as e:
            logger.debug(f"L2 cache clear error: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get L2 cache statistics"""
        stats = {
            'type': 'L2_Redis',
            'connected': self.connected,
            'max_size': self.max_size,
            'ttl_seconds': self.ttl,
            'size': 0,
            'memory_usage_bytes': 0
        }
        
        if await self._ensure_connection():
            try:
                pattern = f"{self.key_prefix}*"
                keys = await self.client.keys(pattern)
                stats['size'] = len(keys)
                
                # Get memory usage (approximate)
                info = await self.client.info('memory')
                stats['memory_usage_bytes'] = info.get('used_memory', 0)
            except Exception as e:
                logger.debug(f"L2 stats error: {e}")
        
        return stats

class L3DiskCache:
    """Level 3: Disk cache for cold data"""
    
    def __init__(self, cache_dir: str = "data/cache/l3", max_size_mb: int = 1000, ttl: int = 86400):
        self.cache_dir = Path(cache_dir)
        self.max_size_mb = max_size_mb
        self.ttl = ttl
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        
    def _get_cache_path(self, key: str) -> Path:
        """Get file path for cache key"""
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"
    
    def _is_expired(self, file_path: Path) -> bool:
        """Check if cache file is expired"""
        try:
            file_age = time.time() - file_path.stat().st_mtime
            return file_age > self.ttl
        except (OSError, FileNotFoundError):
            return True
    
    async def get(self, key: str) -> Optional[Any]:
        """Get item from L3 cache"""
        file_path = self._get_cache_path(key)
        
        if not file_path.exists() or self._is_expired(file_path):
            return None
            
        try:
            with self._lock:
                with open(file_path, 'rb') as f:
                    data = pickle.load(f)
                return data
        except Exception as e:
            logger.debug(f"L3 cache get error: {e}")
            # Clean up corrupted file
            try:
                file_path.unlink()
            except:
                pass
            return None
    
    async def set(self, key: str, value: Any) -> bool:
        """Set item in L3 cache"""
        file_path = self._get_cache_path(key)
        
        try:
            with self._lock:
                # Check disk space before writing
                if not self._has_space_for_write():
                    await self._cleanup_old_files()
                
                with open(file_path, 'wb') as f:
                    pickle.dump(value, f)
                return True
        except Exception as e:
            logger.debug(f"L3 cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete item from L3 cache"""
        file_path = self._get_cache_path(key)
        try:
            with self._lock:
                if file_path.exists():
                    file_path.unlink()
                    return True
                return False
        except Exception as e:
            logger.debug(f"L3 cache delete error: {e}")
            return False
    
    async def clear(self) -> bool:
        """Clear L3 cache"""
        try:
            with self._lock:
                for file_path in self.cache_dir.glob("*.cache"):
                    file_path.unlink()
                return True
        except Exception as e:
            logger.debug(f"L3 cache clear error: {e}")
            return False
    
    def _has_space_for_write(self) -> bool:
        """Check if we have space for writing"""
        try:
            total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.cache"))
            return total_size < self.max_size_mb * 1024 * 1024
        except Exception:
            return True  # Assume we have space if we can't check
    
    async def _cleanup_old_files(self):
        """Clean up old cache files"""
        try:
            with self._lock:
                files = list(self.cache_dir.glob("*.cache"))
                # Sort by modification time (oldest first)
                files.sort(key=lambda f: f.stat().st_mtime)
                
                # Remove oldest 25% of files
                files_to_remove = files[:len(files) // 4]
                for file_path in files_to_remove:
                    file_path.unlink()
                    
                logger.debug(f"L3 cleanup: Removed {len(files_to_remove)} old cache files")
        except Exception as e:
            logger.debug(f"L3 cleanup error: {e}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get L3 cache statistics"""
        try:
            files = list(self.cache_dir.glob("*.cache"))
            total_size = sum(f.stat().st_size for f in files)
            
            return {
                'type': 'L3_Disk',
                'size': len(files),
                'total_size_mb': total_size / (1024 * 1024),
                'max_size_mb': self.max_size_mb,
                'usage_ratio': (total_size / (1024 * 1024)) / self.max_size_mb,
                'ttl_seconds': self.ttl,
                'cache_dir': str(self.cache_dir)
            }
        except Exception as e:
            logger.debug(f"L3 stats error: {e}")
            return {
                'type': 'L3_Disk',
                'error': str(e)
            }

class HierarchicalCache:
    """
    Multi-level hierarchical cache system.
    
    Architecture:
    L1 (Memory) → L2 (Redis) → L3 (Disk)
    
    Features:
    - Automatic promotion of frequently accessed data
    - Graceful degradation when layers fail
    - Performance monitoring and optimization
    - Memory-efficient data management
    """
    
    def __init__(self,
                 l1_max_size: int = 1000,
                 l1_ttl: int = 3600,
                 l2_redis_url: str = None,
                 l2_max_size: int = 5000,
                 l2_ttl: int = 7200,
                 l3_cache_dir: str = "data/cache/l3",
                 l3_max_size_mb: int = 1000,
                 l3_ttl: int = 86400):
        """
        Initialize hierarchical cache system.
        
        Args:
            l1_max_size: L1 cache max items
            l1_ttl: L1 cache TTL in seconds
            l2_redis_url: Redis URL for L2 cache
            l2_max_size: L2 cache max items
            l2_ttl: L2 cache TTL in seconds
            l3_cache_dir: L3 disk cache directory
            l3_max_size_mb: L3 cache max size in MB
            l3_ttl: L3 cache TTL in seconds
        """
        # Initialize cache layers
        self.l1_cache = L1MemoryCache(max_size=l1_max_size, ttl=l1_ttl)
        self.l2_cache = L2RedisCache(redis_url=l2_redis_url, max_size=l2_max_size, ttl=l2_ttl)
        self.l3_cache = L3DiskCache(cache_dir=l3_cache_dir, max_size_mb=l3_max_size_mb, ttl=l3_ttl)
        
        # Performance tracking
        self.metrics = CacheMetrics()
        
        logger.info("🏗️ Hierarchical Cache System initialized:")
        logger.info(f"   L1 (Memory): {l1_max_size} items, {l1_ttl}s TTL")
        logger.info(f"   L2 (Redis): {l2_max_size} items, {l2_ttl}s TTL")
        logger.info(f"   L3 (Disk): {l3_max_size_mb}MB, {l3_ttl}s TTL")
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get item from cache with automatic promotion.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        start_time = time.time()
        
        # Try L1 cache (Memory - fastest)
        value = await self.l1_cache.get(key)
        if value is not None:
            access_time = time.time() - start_time
            self.metrics.record_hit(1, access_time)
            logger.debug(f"🎯 L1 cache hit: {key}")
            return value
        
        # Try L2 cache (Redis - fast)
        value = await self.l2_cache.get(key)
        if value is not None:
            access_time = time.time() - start_time
            self.metrics.record_hit(2, access_time)
            
            # Promote to L1
            await self.l1_cache.set(key, value)
            self.metrics.record_promotion()
            
            logger.debug(f"🔥 L2 cache hit + L1 promotion: {key}")
            return value
        
        # Try L3 cache (Disk - slow but comprehensive)
        value = await self.l3_cache.get(key)
        if value is not None:
            access_time = time.time() - start_time
            self.metrics.record_hit(3, access_time)
            
            # Promote to L2 and L1
            await self.l2_cache.set(key, value)
            await self.l1_cache.set(key, value)
            self.metrics.record_promotion()
            
            logger.debug(f"💾 L3 cache hit + L2/L1 promotion: {key}")
            return value
        
        # Cache miss
        self.metrics.record_miss()
        logger.debug(f"❌ Cache miss: {key}")
        return None
    
    async def set(self, key: str, value: Any, levels: List[int] = None) -> bool:
        """
        Set item in cache across specified levels.
        
        Args:
            key: Cache key
            value: Value to cache
            levels: Which cache levels to update (default: all)
            
        Returns:
            True if set in at least one level
        """
        if levels is None:
            levels = [1, 2, 3]  # All levels by default
        
        success = False
        
        # Set in all specified levels
        if 1 in levels:
            if await self.l1_cache.set(key, value):
                success = True
        
        if 2 in levels:
            if await self.l2_cache.set(key, value):
                success = True
        
        if 3 in levels:
            if await self.l3_cache.set(key, value):
                success = True
        
        if success:
            logger.debug(f"💾 Cached in levels {levels}: {key}")
        
        return success
    
    async def delete(self, key: str) -> bool:
        """Delete item from all cache levels."""
        deleted = False
        
        # Delete from all levels
        if await self.l1_cache.delete(key):
            deleted = True
        if await self.l2_cache.delete(key):
            deleted = True
        if await self.l3_cache.delete(key):
            deleted = True
        
        if deleted:
            logger.debug(f"🗑️ Deleted from cache: {key}")
        
        return deleted
    
    async def clear(self, levels: List[int] = None) -> bool:
        """Clear specified cache levels."""
        if levels is None:
            levels = [1, 2, 3]  # All levels by default
        
        success = True
        
        if 1 in levels:
            success &= await self.l1_cache.clear()
        if 2 in levels:
            success &= await self.l2_cache.clear()
        if 3 in levels:
            success &= await self.l3_cache.clear()
        
        if success:
            logger.info(f"🧹 Cleared cache levels: {levels}")
        
        return success
    
    async def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics for all cache levels."""
        l1_stats = self.l1_cache.get_stats()
        l2_stats = await self.l2_cache.get_stats()
        l3_stats = await self.l3_cache.get_stats()
        cache_metrics = self.metrics.get_stats()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'cache_metrics': cache_metrics,
            'l1_memory': l1_stats,
            'l2_redis': l2_stats,
            'l3_disk': l3_stats,
            'total_items': l1_stats['size'] + l2_stats.get('size', 0) + l3_stats.get('size', 0),
            'health_score': self._calculate_health_score(l1_stats, l2_stats, l3_stats, cache_metrics)
        }
    
    def _calculate_health_score(self, l1_stats: Dict, l2_stats: Dict, l3_stats: Dict, metrics: Dict) -> float:
        """Calculate overall cache health score (0-100)."""
        score = 100.0
        
        # Penalize low hit rates
        hit_rate = metrics.get('hit_rate', 0)
        if hit_rate < 0.5:
            score -= (0.5 - hit_rate) * 100
        
        # Penalize high L1 usage
        l1_usage = l1_stats.get('usage_ratio', 0)
        if l1_usage > 0.9:
            score -= (l1_usage - 0.9) * 200
        
        # Penalize Redis disconnection
        if not l2_stats.get('connected', False):
            score -= 20
        
        # Penalize high L3 usage
        l3_usage = l3_stats.get('usage_ratio', 0)
        if l3_usage > 0.8:
            score -= (l3_usage - 0.8) * 50
        
        return max(0, min(100, score))
    
    async def optimize(self) -> Dict[str, Any]:
        """Run optimization and return recommendations."""
        stats = await self.get_comprehensive_stats()
        recommendations = []
        actions_taken = []
        
        # Optimize based on metrics
        hit_rate = stats['cache_metrics']['hit_rate']
        if hit_rate < 0.6:
            recommendations.append("Consider increasing L1 cache size for better hit rates")
        
        l1_usage = stats['l1_memory']['usage_ratio']
        if l1_usage > 0.95:
            recommendations.append("L1 cache is nearly full - consider increasing size")
        
        # Check Redis connectivity
        if not stats['l2_redis']['connected']:
            recommendations.append("L2 Redis cache is disconnected - check connection")
        
        # L3 disk usage
        l3_usage = stats['l3_disk'].get('usage_ratio', 0)
        if l3_usage > 0.9:
            recommendations.append("L3 disk cache is nearly full - cleanup recommended")
            # Trigger cleanup
            await self.l3_cache._cleanup_old_files()
            actions_taken.append("Cleaned up old L3 cache files")
        
        return {
            'timestamp': datetime.now().isoformat(),
            'health_score': stats['health_score'],
            'recommendations': recommendations,
            'actions_taken': actions_taken,
            'stats_snapshot': stats
        } 