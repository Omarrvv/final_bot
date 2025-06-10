"""
Consolidated Analytics Service Module

This module provides unified analytics and monitoring functionality including:
- Performance monitoring and metrics collection
- Query performance analysis  
- System health monitoring
- Analytics reporting and dashboards
- Optimization recommendations

Consolidates functionality from:
- src/services/analytics/monitoring_service.py
- src/services/analyticsService.js (legacy)
"""

import logging
import hashlib
import time
import threading
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, deque
import psutil
import numpy as np

from src.services.base_service import BaseService

logger = logging.getLogger(__name__)

class PerformanceLevel(Enum):
    """Performance level enumeration."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"

@dataclass
class QueryMetrics:
    """Query performance metrics."""
    query_hash: str
    query_type: str
    table_name: Optional[str]
    avg_duration_ms: float
    min_duration_ms: float
    max_duration_ms: float
    p95_duration_ms: float
    execution_count: int
    error_count: int
    last_executed: float
    performance_level: PerformanceLevel

@dataclass
class SystemMetrics:
    """System-wide performance metrics."""
    total_queries: int
    avg_response_time_ms: float
    queries_per_second: float
    error_rate: float
    slow_query_count: int
    cache_hit_rate: float
    active_connections: int
    cpu_usage_percent: float
    memory_usage_mb: float

class MonitoringService(BaseService):
    """
    Service for monitoring database and system performance.
    
    Responsibilities:
    - Query performance tracking
    - Slow query analysis
    - System metrics collection
    - Performance optimization suggestions
    - Health monitoring
    """
    
    def __init__(self, db_manager=None, slow_query_threshold_ms: int = 500):
        super().__init__(db_manager)
        self.slow_query_threshold_ms = slow_query_threshold_ms
        
        # Performance tracking
        self._query_metrics: Dict[str, Dict[str, Any]] = {}
        self._metrics_lock = threading.RLock()
        
        # System metrics tracking
        self._system_metrics_history = deque(maxlen=100)
        self._last_system_check = 0
        
        logger.info(f"MonitoringService initialized with threshold {slow_query_threshold_ms}ms")

    def record_query_performance(self, query: str, params: Tuple, duration_ms: float, 
                               rows_affected: int, table_name: Optional[str] = None,
                               query_type: str = "unknown", error: Optional[str] = None) -> None:
        """Record performance metrics for a database query."""
        try:
            query_hash = self._hash_query(query)
            
            with self._metrics_lock:
                if query_hash not in self._query_metrics:
                    self._query_metrics[query_hash] = {
                        'query': query[:200],  # Store truncated query
                        'query_type': query_type,
                        'table_name': table_name,
                        'durations': [],
                        'execution_count': 0,
                        'error_count': 0,
                        'rows_affected_total': 0,
                        'first_seen': time.time(),
                        'last_executed': 0
                    }
                
                metrics = self._query_metrics[query_hash]
                metrics['durations'].append(duration_ms)
                metrics['execution_count'] += 1
                metrics['rows_affected_total'] += rows_affected
                metrics['last_executed'] = time.time()
                
                if error:
                    metrics['error_count'] += 1
                
                # Keep only last 100 durations to prevent memory bloat
                if len(metrics['durations']) > 100:
                    metrics['durations'] = metrics['durations'][-100:]
                
                # Check for performance alerts
                self._check_performance_alerts(query, duration_ms, error)
                
        except Exception as e:
            logger.error(f"Error recording query performance: {e}")

    def get_slow_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get list of slowest queries."""
        try:
            with self._metrics_lock:
                slow_queries = []
                
                for query_hash, metrics in self._query_metrics.items():
                    if not metrics['durations']:
                        continue
                    
                    avg_duration = np.mean(metrics['durations'])
                    if avg_duration >= self.slow_query_threshold_ms:
                        slow_queries.append({
                            'query_hash': query_hash,
                            'query': metrics['query'],
                            'avg_duration_ms': round(avg_duration, 2),
                            'max_duration_ms': round(max(metrics['durations']), 2),
                            'execution_count': metrics['execution_count'],
                            'error_count': metrics['error_count'],
                            'table_name': metrics.get('table_name'),
                            'performance_level': self._categorize_performance(avg_duration)
                        })
                
                # Sort by average duration descending
                slow_queries.sort(key=lambda x: x['avg_duration_ms'], reverse=True)
                return slow_queries[:limit]
                
        except Exception as e:
            logger.error(f"Error getting slow queries: {e}")
            return []

    def get_performance_metrics(self) -> SystemMetrics:
        """Get current system performance metrics."""
        try:
            with self._metrics_lock:
                # Calculate query metrics
                total_queries = sum(m['execution_count'] for m in self._query_metrics.values())
                total_errors = sum(m['error_count'] for m in self._query_metrics.values())
                
                all_durations = []
                for metrics in self._query_metrics.values():
                    all_durations.extend(metrics['durations'])
                
                avg_response_time = np.mean(all_durations) if all_durations else 0
                error_rate = (total_errors / total_queries * 100) if total_queries > 0 else 0
                
                slow_query_count = len([
                    m for m in self._query_metrics.values() 
                    if m['durations'] and np.mean(m['durations']) >= self.slow_query_threshold_ms
                ])
                
                # Get system metrics
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory_info = psutil.virtual_memory()
                memory_mb = memory_info.used / (1024 * 1024)
                
                # Calculate QPS over last minute
                current_time = time.time()
                recent_queries = sum(
                    1 for m in self._query_metrics.values() 
                    if current_time - m['last_executed'] <= 60
                )
                qps = recent_queries / 60.0
                
                return SystemMetrics(
                    total_queries=total_queries,
                    avg_response_time_ms=round(avg_response_time, 2),
                    queries_per_second=round(qps, 2),
                    error_rate=round(error_rate, 2),
                    slow_query_count=slow_query_count,
                    cache_hit_rate=self._get_cache_hit_rate(),
                    active_connections=self._get_active_connections(),
                    cpu_usage_percent=round(cpu_percent, 1),
                    memory_usage_mb=round(memory_mb, 1)
                )
                
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return SystemMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0)

    def suggest_optimizations(self) -> List[str]:
        """Analyze performance and suggest optimizations."""
        suggestions = []
        try:
            metrics = self.get_performance_metrics()
            
            # High error rate
            if metrics.error_rate > 5:
                suggestions.append(f"High error rate ({metrics.error_rate}%) - Check query syntax and database connections")
            
            # Slow average response time
            if metrics.avg_response_time_ms > 1000:
                suggestions.append(f"Slow average response time ({metrics.avg_response_time_ms}ms) - Consider adding indexes")
            
            # Many slow queries
            if metrics.slow_query_count > 5:
                suggestions.append(f"Multiple slow queries detected ({metrics.slow_query_count}) - Review query optimization")
            
            # High CPU usage
            if metrics.cpu_usage_percent > 80:
                suggestions.append(f"High CPU usage ({metrics.cpu_usage_percent}%) - Consider query optimization or scaling")
            
            # High memory usage
            if metrics.memory_usage_mb > 1000:
                suggestions.append(f"High memory usage ({metrics.memory_usage_mb}MB) - Monitor for memory leaks")
            
            # Low cache hit rate
            if metrics.cache_hit_rate < 70:
                suggestions.append(f"Low cache hit rate ({metrics.cache_hit_rate}%) - Consider cache warming or TTL adjustment")
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating optimization suggestions: {e}")
            return ["Unable to analyze performance metrics"]

    def _hash_query(self, query: str) -> str:
        """Generate hash for query normalization."""
        # Normalize query by removing extra whitespace and converting to lowercase
        normalized = ' '.join(query.lower().split())
        return hashlib.md5(normalized.encode()).hexdigest()

    def _categorize_performance(self, duration_ms: float) -> PerformanceLevel:
        """Categorize query performance level."""
        if duration_ms < 50:
            return PerformanceLevel.EXCELLENT
        elif duration_ms < 200:
            return PerformanceLevel.GOOD
        elif duration_ms < 500:
            return PerformanceLevel.FAIR
        elif duration_ms < 1000:
            return PerformanceLevel.POOR
        else:
            return PerformanceLevel.CRITICAL

    def _check_performance_alerts(self, query: str, duration_ms: float, error: Optional[str]) -> None:
        """Check if performance alerts should be triggered."""
        if duration_ms > self.slow_query_threshold_ms * 3:  # Very slow query
            logger.warning(f"Very slow query detected ({duration_ms}ms): {query[:100]}...")
        
        if error:
            logger.error(f"Query error: {error} for query: {query[:100]}...")

    def _get_cache_hit_rate(self) -> float:
        """Get cache hit rate (placeholder implementation)."""
        # In a real implementation, this would get actual cache metrics
        return 85.0

    def _get_active_connections(self) -> int:
        """Get number of active database connections."""
        try:
            if self.db_manager and hasattr(self.db_manager, 'get_pool_status'):
                pool_status = self.db_manager.get_pool_status()
                return pool_status.get('active_connections', 0)
        except Exception:
            pass
        return 0

class AnalyticsService:
    """
    Unified analytics service combining monitoring and reporting.
    
    Responsibilities:
    - Performance monitoring
    - Analytics reporting
    - System health checks
    - Optimization recommendations
    """
    
    def __init__(self, db_manager=None, slow_query_threshold_ms: int = 500):
        self.monitoring = MonitoringService(db_manager, slow_query_threshold_ms)
        self.db_manager = db_manager
        
        logger.info("AnalyticsService initialized")

    def record_query_performance(self, query: str, params: Tuple, duration_ms: float, 
                               rows_affected: int, **kwargs) -> None:
        """Record query performance metrics."""
        return self.monitoring.record_query_performance(
            query, params, duration_ms, rows_affected, **kwargs
        )

    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""
        try:
            metrics = self.monitoring.get_performance_metrics()
            slow_queries = self.monitoring.get_slow_queries(limit=5)
            suggestions = self.monitoring.suggest_optimizations()
            
            return {
                'system_metrics': {
                    'total_queries': metrics.total_queries,
                    'avg_response_time_ms': metrics.avg_response_time_ms,
                    'queries_per_second': metrics.queries_per_second,
                    'error_rate': metrics.error_rate,
                    'slow_query_count': metrics.slow_query_count,
                    'cache_hit_rate': metrics.cache_hit_rate,
                    'active_connections': metrics.active_connections,
                    'cpu_usage_percent': metrics.cpu_usage_percent,
                    'memory_usage_mb': metrics.memory_usage_mb
                },
                'slow_queries': slow_queries,
                'optimization_suggestions': suggestions,
                'health_status': 'healthy' if metrics.error_rate < 5 else 'warning',
                'generated_at': time.time()
            }
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return {'error': str(e), 'generated_at': time.time()}

    def get_slow_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get slow queries report."""
        return self.monitoring.get_slow_queries(limit)

    def get_system_health(self) -> Dict[str, Any]:
        """Get system health status."""
        try:
            metrics = self.monitoring.get_performance_metrics()
            
            health_score = 100
            issues = []
            
            # Deduct points for various issues
            if metrics.error_rate > 5:
                health_score -= 20
                issues.append(f"High error rate: {metrics.error_rate}%")
            
            if metrics.avg_response_time_ms > 1000:
                health_score -= 15
                issues.append(f"Slow response time: {metrics.avg_response_time_ms}ms")
            
            if metrics.slow_query_count > 5:
                health_score -= 10
                issues.append(f"Multiple slow queries: {metrics.slow_query_count}")
            
            if metrics.cpu_usage_percent > 80:
                health_score -= 15
                issues.append(f"High CPU usage: {metrics.cpu_usage_percent}%")
            
            status = "healthy"
            if health_score < 70:
                status = "warning"
            if health_score < 50:
                status = "critical"
            
            return {
                'status': status,
                'health_score': max(0, health_score),
                'issues': issues,
                'metrics': metrics,
                'checked_at': time.time()
            }
            
        except Exception as e:
            logger.error(f"Error checking system health: {e}")
            return {
                'status': 'error',
                'health_score': 0,
                'issues': [f"Health check failed: {str(e)}"],
                'checked_at': time.time()
            } 