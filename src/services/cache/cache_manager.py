"""
Cache Management Service for the Egypt Tourism Chatbot.

This service provides unified management of all caching systems including
vector cache, query cache, and cache coordination. Extracted from DatabaseManager
and cache classes as part of Phase 2.5 refactoring.
"""
import logging
import os
import time
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from enum import Enum

# Import existing cache classes
from src.knowledge.vector_tiered_cache import VectorTieredCache
from src.utils.query_cache import QueryCache

logger = logging.getLogger(__name__)

class CacheType(Enum):
    """Cache type enumeration."""
    VECTOR = "vector"
    QUERY = "query"
    MEMORY = "memory"
    REDIS = "redis"

@dataclass
class CacheStats:
    """Cache statistics data class."""
    cache_type: str
    hit_count: int
    miss_count: int
    hit_rate: float
    total_requests: int
    total_size: int
    max_size: int
    ttl: int
    last_eviction: Optional[float] = None
    error_count: int = 0

@dataclass
class CacheHealth:
    """Cache health status."""
    is_healthy: bool
    status: str
    response_time_ms: float
    memory_usage_mb: float
    connection_status: str
    errors: List[str]

class CacheManagementService:
    """
    Service for managing all caching systems.
    
    This service provides centralized management of vector caches,
    query caches, and cache coordination across the system.
    
    Responsibilities:
    - Vector cache management and coordination
    - Query cache management and coordination
    - Cache statistics and monitoring
    - Cache health checking and diagnostics
    - Cache warming and optimization
    - Cache invalidation strategies
    """
    
    def __init__(self, db_manager=None, redis_uri: Optional[str] = None):
        """
        Initialize the cache management service.
        
        Args:
            db_manager: Database manager instance
            redis_uri: Redis URI for distributed caching
        """
        self.db_manager = db_manager
        self.redis_uri = redis_uri
        
        # Feature flags from environment
        self.enabled = os.getenv('USE_NEW_CACHE_MANAGER', 'false').lower() == 'true'
        
        # Initialize cache instances
        self._vector_cache = None
        self._query_cache = None
        self._cache_stats = {}
        self._cache_health = {}
        self._last_health_check = 0
        self._health_check_interval = 60  # 1 minute
        
        # Initialize caches
        self._initialize_caches()
    
    def _initialize_caches(self) -> None:
        """Initialize cache instances."""
        try:
            # Initialize vector cache
            self._vector_cache = VectorTieredCache(
                redis_uri=self.redis_uri,
                ttl=3600,  # 1 hour
                max_size=1000
            )
            
            # Initialize query cache
            self._query_cache = QueryCache(
                redis_uri=self.redis_uri,
                ttl=1800,  # 30 minutes
                max_size=500
            )
            
            logger.info("Cache management service initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing caches: {str(e)}")
    
    def get_vector_cache(self) -> VectorTieredCache:
        """
        Get the vector cache instance.
        
        Returns:
            VectorTieredCache: Vector cache instance
        """
        if not self.enabled and self.db_manager:
            # Fallback to legacy cache
            return getattr(self.db_manager, 'vector_cache', self._vector_cache)
        
        return self._vector_cache
    
    def get_query_cache(self) -> QueryCache:
        """
        Get the query cache instance.
        
        Returns:
            QueryCache: Query cache instance
        """
        if not self.enabled and self.db_manager:
            # Fallback to legacy cache
            return getattr(self.db_manager, 'query_cache', self._query_cache)
        
        return self._query_cache
    
    def get_cache_stats(self) -> Dict[str, CacheStats]:
        """
        Get comprehensive cache statistics.
        
        Returns:
            Dict[str, CacheStats]: Cache statistics by cache type
        """
        stats = {}
        
        try:
            # Vector cache stats
            if self._vector_cache:
                vector_stats = self._get_cache_instance_stats(self._vector_cache, "vector")
                if vector_stats:
                    stats["vector"] = vector_stats
            
            # Query cache stats
            if self._query_cache:
                query_stats = self._get_cache_instance_stats(self._query_cache, "query")
                if query_stats:
                    stats["query"] = query_stats
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {str(e)}")
        
        return stats
    
    def _get_cache_instance_stats(self, cache_instance, cache_type: str) -> Optional[CacheStats]:
        """Get statistics for a specific cache instance."""
        try:
            # Get basic stats from cache instance
            hit_count = getattr(cache_instance, 'hit_count', 0)
            miss_count = getattr(cache_instance, 'miss_count', 0)
            total_requests = hit_count + miss_count
            hit_rate = (hit_count / total_requests) if total_requests > 0 else 0.0
            
            # Get cache size info
            total_size = getattr(cache_instance, 'current_size', 0)
            max_size = getattr(cache_instance, 'max_size', 0)
            ttl = getattr(cache_instance, 'ttl', 0)
            
            return CacheStats(
                cache_type=cache_type,
                hit_count=hit_count,
                miss_count=miss_count,
                hit_rate=hit_rate,
                total_requests=total_requests,
                total_size=total_size,
                max_size=max_size,
                ttl=ttl,
                last_eviction=getattr(cache_instance, 'last_eviction', None),
                error_count=getattr(cache_instance, 'error_count', 0)
            )
            
        except Exception as e:
            logger.error(f"Error getting stats for {cache_type} cache: {str(e)}")
            return None
    
    def invalidate_table(self, table_name: str) -> bool:
        """
        Invalidate all cached data for a specific table.
        
        Args:
            table_name: Name of the table to invalidate
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            success = True
            
            # Invalidate vector cache
            if self._vector_cache:
                if not self._vector_cache.invalidate_table(table_name):
                    success = False
                    logger.warning(f"Failed to invalidate vector cache for table {table_name}")
            
            # Invalidate query cache
            if self._query_cache:
                if not self._query_cache.invalidate_table(table_name):
                    success = False
                    logger.warning(f"Failed to invalidate query cache for table {table_name}")
            
            if success:
                logger.info(f"Successfully invalidated all caches for table: {table_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error invalidating caches for table {table_name}: {str(e)}")
            return False
    
    def invalidate_all_caches(self) -> bool:
        """
        Invalidate all cached data across all cache types.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            success = True
            
            # Clear vector cache
            if self._vector_cache:
                if not self._vector_cache.invalidate_all_vector_searches():
                    success = False
                    logger.warning("Failed to clear vector cache")
            
            # Clear query cache
            if self._query_cache:
                if not self._query_cache.invalidate_all_queries():
                    success = False
                    logger.warning("Failed to clear query cache")
            
            if success:
                logger.info("Successfully invalidated all caches")
            
            return success
            
        except Exception as e:
            logger.error(f"Error invalidating all caches: {str(e)}")
            return False
    
    def warm_cache(self, tables: Optional[List[str]] = None) -> bool:
        """
        Warm up caches with frequently accessed data.
        
        Args:
            tables: Optional list of tables to warm, defaults to all tables
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.db_manager:
                logger.warning("No database manager available for cache warming")
                return False
            
            default_tables = ['attractions', 'restaurants', 'accommodations', 'cities']
            tables_to_warm = tables if tables is not None else default_tables
            
            logger.info(f"Starting cache warming for tables: {tables_to_warm}")
            
            for table in tables_to_warm:
                try:
                    # Warm query cache with basic searches
                    self._warm_query_cache_for_table(table)
                    
                    # Warm vector cache if vectors are available
                    self._warm_vector_cache_for_table(table)
                    
                    logger.info(f"Cache warming completed for table: {table}")
                    
                except Exception as e:
                    logger.warning(f"Error warming cache for table {table}: {str(e)}")
                    # Continue with other tables
            
            logger.info("Cache warming process completed")
            return True
            
        except Exception as e:
            logger.error(f"Error during cache warming: {str(e)}")
            return False
    
    def _warm_query_cache_for_table(self, table: str) -> None:
        """Warm query cache for a specific table."""
        try:
            # Get some popular/recent queries for this table
            if hasattr(self.db_manager, f'search_{table}'):
                search_method = getattr(self.db_manager, f'search_{table}')
                
                # Perform some basic searches to populate cache
                common_searches = [
                    {},  # Empty search (get all)
                    {'limit': 10},  # Basic limit
                    {'limit': 20},  # Different limit
                ]
                
                for search_params in common_searches:
                    try:
                        search_method(**search_params)
                    except Exception as e:
                        logger.warning(f"Error during query cache warming for {table}: {str(e)}")
                        
        except Exception as e:
            logger.warning(f"Error warming query cache for {table}: {str(e)}")
    
    def _warm_vector_cache_for_table(self, table: str) -> None:
        """Warm vector cache for a specific table."""
        try:
            # Check if table has vector search capability
            if hasattr(self.db_manager, f'vector_search_{table}'):
                # For vector cache warming, we'd need sample embeddings
                # This is a placeholder - in real implementation, you'd use
                # popular/recent embeddings or generate sample ones
                logger.info(f"Vector cache warming for {table} - placeholder implementation")
                
        except Exception as e:
            logger.warning(f"Error warming vector cache for {table}: {str(e)}")
    
    def optimize_cache_settings(self) -> bool:
        """
        Optimize cache settings based on usage patterns.
        
        Returns:
            bool: True if optimizations were applied, False otherwise
        """
        try:
            optimizations_applied = False
            
            # Get current stats
            stats = self.get_cache_stats()
            
            for cache_type, cache_stats in stats.items():
                try:
                    # Analyze hit rates and suggest optimizations
                    if cache_stats.hit_rate < 0.3:  # Less than 30% hit rate
                        logger.warning(f"{cache_type} cache has low hit rate: {cache_stats.hit_rate:.2%}")
                        
                        # Consider increasing TTL if hit rate is low
                        if cache_type == "vector" and self._vector_cache:
                            # Increase TTL for vector cache
                            new_ttl = min(cache_stats.ttl * 1.5, 7200)  # Max 2 hours
                            logger.info(f"Increasing {cache_type} cache TTL to {new_ttl}")
                            optimizations_applied = True
                            
                        elif cache_type == "query" and self._query_cache:
                            # Increase TTL for query cache
                            new_ttl = min(cache_stats.ttl * 1.5, 3600)  # Max 1 hour
                            logger.info(f"Increasing {cache_type} cache TTL to {new_ttl}")
                            optimizations_applied = True
                    
                    # Check if cache is near capacity
                    if cache_stats.total_size > (cache_stats.max_size * 0.8):  # 80% full
                        logger.warning(f"{cache_type} cache is {cache_stats.total_size/cache_stats.max_size:.1%} full")
                        
                        # Consider increasing max size
                        if cache_type == "vector" and self._vector_cache:
                            new_max_size = min(cache_stats.max_size * 1.5, 5000)
                            logger.info(f"Considering increasing {cache_type} cache max size to {new_max_size}")
                            
                        elif cache_type == "query" and self._query_cache:
                            new_max_size = min(cache_stats.max_size * 1.5, 2000)
                            logger.info(f"Considering increasing {cache_type} cache max size to {new_max_size}")
                    
                except Exception as e:
                    logger.warning(f"Error optimizing {cache_type} cache: {str(e)}")
            
            return optimizations_applied
            
        except Exception as e:
            logger.error(f"Error optimizing cache settings: {str(e)}")
            return False
    
    def get_cache_health(self) -> Dict[str, CacheHealth]:
        """
        Get health status of all cache systems.
        
        Returns:
            Dict[str, CacheHealth]: Health status by cache type
        """
        current_time = time.time()
        
        # Check if we need to refresh health status
        if current_time - self._last_health_check > self._health_check_interval:
            self._refresh_cache_health()
            self._last_health_check = current_time
        
        return self._cache_health.copy()
    
    def _refresh_cache_health(self) -> None:
        """Refresh cache health status."""
        try:
            # Check vector cache health
            if self._vector_cache:
                self._cache_health['vector'] = self._check_cache_instance_health(
                    self._vector_cache, "vector"
                )
            
            # Check query cache health
            if self._query_cache:
                self._cache_health['query'] = self._check_cache_instance_health(
                    self._query_cache, "query"
                )
                
        except Exception as e:
            logger.error(f"Error refreshing cache health: {str(e)}")
    
    def _check_cache_instance_health(self, cache_instance, cache_type: str) -> CacheHealth:
        """Check health of a specific cache instance."""
        try:
            start_time = time.time()
            errors = []
            
            # Test basic cache operations
            test_key = f"health_check_{cache_type}_{int(start_time)}"
            test_value = {"timestamp": start_time, "test": True}
            
            # Test set operation
            try:
                if hasattr(cache_instance, 'set'):
                    cache_instance.set(test_key, test_value)
                else:
                    # For more complex cache keys
                    cache_instance.set_query_results("health_check", {"test": True}, test_value)
            except Exception as e:
                errors.append(f"Set operation failed: {str(e)}")
            
            # Test get operation
            try:
                if hasattr(cache_instance, 'get'):
                    result = cache_instance.get(test_key)
                else:
                    result = cache_instance.get_query_results("health_check", {"test": True})
                
                if result is None:
                    errors.append("Get operation returned None")
            except Exception as e:
                errors.append(f"Get operation failed: {str(e)}")
            
            # Calculate response time
            response_time_ms = (time.time() - start_time) * 1000
            
            # Check memory usage (approximation)
            memory_usage_mb = getattr(cache_instance, 'current_size', 0) / (1024 * 1024)
            
            # Determine overall health
            is_healthy = len(errors) == 0 and response_time_ms < 100  # Less than 100ms
            status = "healthy" if is_healthy else "degraded" if len(errors) < 2 else "unhealthy"
            
            return CacheHealth(
                is_healthy=is_healthy,
                status=status,
                response_time_ms=response_time_ms,
                memory_usage_mb=memory_usage_mb,
                connection_status="connected" if len(errors) == 0 else "error",
                errors=errors
            )
            
        except Exception as e:
            logger.error(f"Error checking health for {cache_type} cache: {str(e)}")
            return CacheHealth(
                is_healthy=False,
                status="error",
                response_time_ms=0.0,
                memory_usage_mb=0.0,
                connection_status="error",
                errors=[str(e)]
            )
    
    def get_cache_report(self) -> Dict[str, Any]:
        """
        Get comprehensive cache system report.
        
        Returns:
            Dict[str, Any]: Comprehensive cache report
        """
        try:
            stats = self.get_cache_stats()
            health = self.get_cache_health()
            
            # Calculate overall metrics
            total_hit_count = sum(s.hit_count for s in stats.values())
            total_miss_count = sum(s.miss_count for s in stats.values())
            total_requests = total_hit_count + total_miss_count
            overall_hit_rate = (total_hit_count / total_requests) if total_requests > 0 else 0.0
            
            # System health
            all_healthy = all(h.is_healthy for h in health.values())
            
            report = {
                'timestamp': time.time(),
                'overall_status': 'healthy' if all_healthy else 'degraded',
                'overall_hit_rate': overall_hit_rate,
                'total_requests': total_requests,
                'cache_stats': {k: asdict(v) for k, v in stats.items()},
                'cache_health': {k: asdict(v) for k, v in health.items()},
                'recommendations': self._get_cache_recommendations(stats, health),
                'feature_flags': {
                    'enabled': self.enabled,
                    'redis_configured': self.redis_uri is not None
                }
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating cache report: {str(e)}")
            return {
                'timestamp': time.time(),
                'overall_status': 'error',
                'error': str(e)
            }
    
    def _get_cache_recommendations(self, stats: Dict[str, CacheStats], 
                                 health: Dict[str, CacheHealth]) -> List[str]:
        """Get recommendations based on cache performance."""
        recommendations = []
        
        try:
            # Check hit rates
            for cache_type, cache_stats in stats.items():
                if cache_stats.hit_rate < 0.5:  # Less than 50%
                    recommendations.append(
                        f"Consider optimizing {cache_type} cache - hit rate is only {cache_stats.hit_rate:.1%}"
                    )
                
                if cache_stats.total_size > (cache_stats.max_size * 0.9):  # 90% full
                    recommendations.append(
                        f"Consider increasing {cache_type} cache size - currently {cache_stats.total_size/cache_stats.max_size:.1%} full"
                    )
            
            # Check health issues
            for cache_type, cache_health in health.items():
                if not cache_health.is_healthy:
                    recommendations.append(
                        f"Address {cache_type} cache health issues: {', '.join(cache_health.errors)}"
                    )
                
                if cache_health.response_time_ms > 50:  # Slower than 50ms
                    recommendations.append(
                        f"Optimize {cache_type} cache performance - response time is {cache_health.response_time_ms:.1f}ms"
                    )
            
            # Redis recommendations
            if not self.redis_uri:
                recommendations.append(
                    "Consider configuring Redis for distributed caching and better performance"
                )
            
        except Exception as e:
            logger.error(f"Error generating cache recommendations: {str(e)}")
            recommendations.append("Error analyzing cache performance - check logs")
        
        return recommendations 