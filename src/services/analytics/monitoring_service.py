"""
Analytics and Monitoring Service for the Egypt Tourism Chatbot.

This service handles query performance analytics, monitoring, and optimization
recommendations. Extracted from QueryAnalyzer and DatabaseManager performance 
tracking as part of Phase 2.5 refactoring.
"""
import logging
import os
import time
import statistics
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from enum import Enum

# Import existing analyzer
from src.utils.query_analyzer import QueryAnalyzer

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

class AnalyticsMonitoringService:
    """
    Service for analytics and performance monitoring.
    
    This service provides comprehensive monitoring of database performance,
    query analytics, and system health metrics.
    
    Responsibilities:
    - Query performance tracking and analysis
    - Slow query detection and alerting
    - System metrics collection and reporting
    - Performance optimization recommendations
    - Real-time monitoring and alerting
    - Historical trend analysis
    """
    
    def __init__(self, db_manager=None, slow_query_threshold_ms: int = 500):
        """
        Initialize the analytics monitoring service.
        
        Args:
            db_manager: Database manager instance
            slow_query_threshold_ms: Threshold for slow query detection
        """
        self.db_manager = db_manager
        self.slow_query_threshold_ms = slow_query_threshold_ms
        
        # Feature flags from environment
        self.enabled = os.getenv('USE_NEW_ANALYTICS_SERVICE', 'false').lower() == 'true'
        
        # Initialize analytics components
        self.query_analyzer = QueryAnalyzer(
            slow_query_threshold_ms=slow_query_threshold_ms,
            max_queries_to_track=1000
        )
        
        # Metrics storage
        self._query_metrics = defaultdict(list)
        self._system_metrics = deque(maxlen=1000)  # Keep last 1000 metrics
        self._performance_alerts = deque(maxlen=100)  # Keep last 100 alerts
        
        # Timing and counters
        self._total_queries = 0
        self._total_errors = 0
        self._start_time = time.time()
        self._last_metrics_calculation = 0
        self._metrics_cache_ttl = 60  # 1 minute
        
        logger.info("Analytics monitoring service initialized")
    
    def record_query_performance(self, query: str, params: Tuple, duration_ms: float, 
                               rows_affected: int, table_name: Optional[str] = None,
                               query_type: str = "unknown", error: Optional[str] = None) -> None:
        """
        Record query performance metrics.
        
        Args:
            query: SQL query string
            params: Query parameters
            duration_ms: Execution time in milliseconds
            rows_affected: Number of rows affected/returned
            table_name: Optional table name
            query_type: Type of query (SELECT, INSERT, UPDATE, etc.)
            error: Optional error message if query failed
        """
        try:
            # Use legacy analyzer if new service is disabled
            if not self.enabled and self.query_analyzer:
                self.query_analyzer.record_query(query, params, duration_ms, rows_affected)
                return
            
            # Record in query analyzer
            self.query_analyzer.record_query(query, params, duration_ms, rows_affected)
            
            # Update counters
            self._total_queries += 1
            if error:
                self._total_errors += 1
            
            # Store detailed metrics
            query_hash = self._hash_query(query)
            self._query_metrics[query_hash].append({
                'timestamp': time.time(),
                'duration_ms': duration_ms,
                'rows_affected': rows_affected,
                'table_name': table_name,
                'query_type': query_type,
                'error': error,
                'params_count': len(params) if params else 0
            })
            
            # Check for performance alerts
            self._check_performance_alerts(query, duration_ms, error)
            
            # Record system metrics periodically
            if time.time() - self._last_metrics_calculation > 30:  # Every 30 seconds
                self._record_system_metrics()
                self._last_metrics_calculation = time.time()
            
        except Exception as e:
            logger.error(f"Error recording query performance: {str(e)}")
    
    def get_slow_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get list of slow queries with detailed analysis.
        
        Args:
            limit: Maximum number of queries to return
            
        Returns:
            List[Dict[str, Any]]: List of slow queries with metrics
        """
        try:
            if not self.enabled and self.query_analyzer:
                return self.query_analyzer.get_slow_queries()[:limit]
            
            slow_queries = self.query_analyzer.get_slow_queries()
            
            # Enhance with additional metrics
            enhanced_queries = []
            for query_info in slow_queries[:limit]:
                query = query_info['query']
                enhanced_info = query_info.copy()
                
                # Add performance level
                duration = query_info['duration_ms']
                enhanced_info['performance_level'] = self._categorize_performance(duration)
                
                # Add optimization suggestions
                enhanced_info['optimization_suggestions'] = self._get_optimization_suggestions(query, duration)
                
                enhanced_queries.append(enhanced_info)
            
            return enhanced_queries
            
        except Exception as e:
            logger.error(f"Error getting slow queries: {str(e)}")
            return []
    
    def get_query_stats(self, query: Optional[str] = None) -> Dict[str, Any]:
        """
        Get comprehensive query statistics.
        
        Args:
            query: Optional specific query to analyze
            
        Returns:
            Dict[str, Any]: Query statistics
        """
        try:
            if not self.enabled and self.query_analyzer:
                return self.query_analyzer.get_query_stats(query)
            
            if query:
                return self._get_specific_query_stats(query)
            else:
                return self._get_all_query_stats()
                
        except Exception as e:
            logger.error(f"Error getting query stats: {str(e)}")
            return {}
    
    def _get_specific_query_stats(self, query: str) -> Dict[str, Any]:
        """Get statistics for a specific query."""
        query_hash = self._hash_query(query)
        metrics = self._query_metrics.get(query_hash, [])
        
        if not metrics:
            return {}
        
        durations = [m['duration_ms'] for m in metrics]
        rows = [m['rows_affected'] for m in metrics]
        errors = [m for m in metrics if m['error']]
        
        return {
            'query_hash': query_hash,
            'execution_count': len(metrics),
            'avg_duration_ms': statistics.mean(durations),
            'min_duration_ms': min(durations),
            'max_duration_ms': max(durations),
            'median_duration_ms': statistics.median(durations),
            'p95_duration_ms': statistics.quantiles(durations, n=20)[19] if len(durations) >= 20 else max(durations),
            'avg_rows': statistics.mean(rows) if rows else 0,
            'total_rows': sum(rows),
            'error_count': len(errors),
            'error_rate': len(errors) / len(metrics),
            'last_executed': max(m['timestamp'] for m in metrics),
            'performance_level': self._categorize_performance(statistics.mean(durations)).value,
            'table_names': list(set(m['table_name'] for m in metrics if m['table_name']))
        }
    
    def _get_all_query_stats(self) -> Dict[str, Any]:
        """Get statistics for all queries."""
        all_stats = {}
        
        for query_hash, metrics in self._query_metrics.items():
            if not metrics:
                continue
            
            durations = [m['duration_ms'] for m in metrics]
            rows = [m['rows_affected'] for m in metrics]
            errors = [m for m in metrics if m['error']]
            
            all_stats[query_hash] = {
                'execution_count': len(metrics),
                'avg_duration_ms': statistics.mean(durations),
                'min_duration_ms': min(durations),
                'max_duration_ms': max(durations),
                'median_duration_ms': statistics.median(durations),
                'p95_duration_ms': statistics.quantiles(durations, n=20)[19] if len(durations) >= 20 else max(durations),
                'avg_rows': statistics.mean(rows) if rows else 0,
                'total_rows': sum(rows),
                'error_count': len(errors),
                'error_rate': len(errors) / len(metrics) if metrics else 0,
                'last_executed': max(m['timestamp'] for m in metrics),
                'performance_level': self._categorize_performance(statistics.mean(durations)).value,
                'query_types': list(set(m['query_type'] for m in metrics if m['query_type']))
            }
        
        return all_stats
    
    def analyze_query_patterns(self) -> Dict[str, Any]:
        """
        Analyze query patterns and trends.
        
        Returns:
            Dict[str, Any]: Pattern analysis results
        """
        try:
            patterns = {
                'timestamp': time.time(),
                'total_unique_queries': len(self._query_metrics),
                'query_type_distribution': defaultdict(int),
                'table_access_patterns': defaultdict(int),
                'performance_distribution': defaultdict(int),
                'time_based_patterns': {},
                'optimization_opportunities': []
            }
            
            # Analyze all metrics
            for query_hash, metrics in self._query_metrics.items():
                for metric in metrics:
                    # Query type distribution
                    patterns['query_type_distribution'][metric['query_type']] += 1
                    
                    # Table access patterns
                    if metric['table_name']:
                        patterns['table_access_patterns'][metric['table_name']] += 1
                    
                    # Performance distribution
                    perf_level = self._categorize_performance(metric['duration_ms'])
                    patterns['performance_distribution'][perf_level.value] += 1
            
            # Find optimization opportunities
            patterns['optimization_opportunities'] = self._find_optimization_opportunities()
            
            # Analyze time-based patterns
            patterns['time_based_patterns'] = self._analyze_time_patterns()
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing query patterns: {str(e)}")
            return {}
    
    def get_performance_metrics(self) -> SystemMetrics:
        """
        Get current system performance metrics.
        
        Returns:
            SystemMetrics: Current system performance metrics
        """
        try:
            current_time = time.time()
            uptime_seconds = current_time - self._start_time
            
            # Calculate queries per second
            qps = self._total_queries / uptime_seconds if uptime_seconds > 0 else 0
            
            # Calculate average response time
            all_durations = []
            for metrics in self._query_metrics.values():
                all_durations.extend([m['duration_ms'] for m in metrics])
            
            avg_response_time = statistics.mean(all_durations) if all_durations else 0
            
            # Calculate error rate
            error_rate = (self._total_errors / self._total_queries) if self._total_queries > 0 else 0
            
            # Count slow queries
            slow_query_count = len([d for d in all_durations if d > self.slow_query_threshold_ms])
            
            # Get cache hit rate (if available)
            cache_hit_rate = self._get_cache_hit_rate()
            
            # Get connection info
            active_connections = self._get_active_connections()
            
            # System resource usage (placeholder - would need system monitoring)
            cpu_usage = 0.0  # Would integrate with system monitoring
            memory_usage = 0.0  # Would integrate with system monitoring
            
            return SystemMetrics(
                total_queries=self._total_queries,
                avg_response_time_ms=avg_response_time,
                queries_per_second=qps,
                error_rate=error_rate,
                slow_query_count=slow_query_count,
                cache_hit_rate=cache_hit_rate,
                active_connections=active_connections,
                cpu_usage_percent=cpu_usage,
                memory_usage_mb=memory_usage
            )
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {str(e)}")
            return SystemMetrics(
                total_queries=0, avg_response_time_ms=0, queries_per_second=0,
                error_rate=0, slow_query_count=0, cache_hit_rate=0,
                active_connections=0, cpu_usage_percent=0, memory_usage_mb=0
            )
    
    def suggest_optimizations(self) -> List[str]:
        """
        Generate optimization suggestions based on performance analysis.
        
        Returns:
            List[str]: List of optimization recommendations
        """
        try:
            suggestions = []
            
            # Analyze slow queries
            slow_queries = self.get_slow_queries(5)
            if slow_queries:
                suggestions.append(f"Found {len(slow_queries)} slow queries - consider optimization")
                
                for query in slow_queries:
                    if query['duration_ms'] > 1000:  # > 1 second
                        suggestions.append(f"Critical: Query taking {query['duration_ms']:.0f}ms needs immediate attention")
            
            # Check error rates
            metrics = self.get_performance_metrics()
            if metrics.error_rate > 0.05:  # > 5% error rate
                suggestions.append(f"High error rate detected: {metrics.error_rate:.1%} - investigate failed queries")
            
            # Check cache performance
            if metrics.cache_hit_rate < 0.5:  # < 50% hit rate
                suggestions.append(f"Low cache hit rate: {metrics.cache_hit_rate:.1%} - consider cache optimization")
            
            # Check query frequency patterns
            patterns = self.analyze_query_patterns()
            for table, count in patterns['table_access_patterns'].items():
                if count > self._total_queries * 0.3:  # > 30% of all queries
                    suggestions.append(f"Table '{table}' is heavily accessed ({count} queries) - consider indexing optimization")
            
            # Check for missing indexes based on query analyzer
            if hasattr(self.query_analyzer, 'suggest_indexes') and self.db_manager:
                try:
                    index_suggestions = self.query_analyzer.suggest_indexes(self.db_manager)
                    for table, indexes in index_suggestions.items():
                        if indexes:
                            suggestions.append(f"Consider adding indexes to {table}: {', '.join(indexes)}")
                except Exception as e:
                    logger.warning(f"Error getting index suggestions: {str(e)}")
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating optimization suggestions: {str(e)}")
            return ["Error generating suggestions - check monitoring service logs"]
    
    def get_monitoring_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive monitoring report.
        
        Returns:
            Dict[str, Any]: Comprehensive monitoring report
        """
        try:
            metrics = self.get_performance_metrics()
            patterns = self.analyze_query_patterns()
            slow_queries = self.get_slow_queries(10)
            suggestions = self.suggest_optimizations()
            
            # Get recent alerts
            recent_alerts = list(self._performance_alerts)[-10:]  # Last 10 alerts
            
            report = {
                'timestamp': time.time(),
                'service_status': 'active' if self.enabled else 'legacy_mode',
                'uptime_seconds': time.time() - self._start_time,
                'system_metrics': asdict(metrics),
                'query_patterns': patterns,
                'slow_queries': slow_queries,
                'optimization_suggestions': suggestions,
                'recent_alerts': recent_alerts,
                'configuration': {
                    'slow_query_threshold_ms': self.slow_query_threshold_ms,
                    'max_queries_tracked': 1000,
                    'metrics_cache_ttl': self._metrics_cache_ttl
                }
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating monitoring report: {str(e)}")
            return {
                'timestamp': time.time(),
                'service_status': 'error',
                'error': str(e)
            }
    
    def _hash_query(self, query: str) -> str:
        """Generate a hash for query normalization."""
        import hashlib
        normalized_query = ' '.join(query.strip().split())
        return hashlib.md5(normalized_query.encode()).hexdigest()[:16]
    
    def _categorize_performance(self, duration_ms: float) -> PerformanceLevel:
        """Categorize query performance level."""
        if duration_ms < 10:
            return PerformanceLevel.EXCELLENT
        elif duration_ms < 50:
            return PerformanceLevel.GOOD
        elif duration_ms < 200:
            return PerformanceLevel.FAIR
        elif duration_ms < 1000:
            return PerformanceLevel.POOR
        else:
            return PerformanceLevel.CRITICAL
    
    def _get_optimization_suggestions(self, query: str, duration_ms: float) -> List[str]:
        """Get optimization suggestions for a specific query."""
        suggestions = []
        
        query_lower = query.lower()
        
        # Basic suggestions based on query patterns
        if 'select *' in query_lower:
            suggestions.append("Avoid SELECT * - specify only needed columns")
        
        if 'order by' in query_lower and 'limit' not in query_lower:
            suggestions.append("Consider adding LIMIT to ORDER BY queries")
        
        if duration_ms > 1000:
            suggestions.append("Query is very slow - consider adding indexes or query rewrite")
        
        if 'like' in query_lower and query_lower.count('%') > 0:
            suggestions.append("LIKE patterns with wildcards can be slow - consider full-text search")
        
        return suggestions
    
    def _check_performance_alerts(self, query: str, duration_ms: float, error: Optional[str]) -> None:
        """Check for performance alerts and log them."""
        try:
            alert_created = False
            
            # Critical performance alert
            if duration_ms > 2000:  # > 2 seconds
                alert = {
                    'timestamp': time.time(),
                    'type': 'critical_performance',
                    'message': f"Critical: Query took {duration_ms:.0f}ms",
                    'query_preview': query[:100] + '...' if len(query) > 100 else query,
                    'duration_ms': duration_ms
                }
                self._performance_alerts.append(alert)
                alert_created = True
                logger.warning(f"Critical performance alert: {alert['message']}")
            
            # Error alert
            if error:
                alert = {
                    'timestamp': time.time(),
                    'type': 'query_error',
                    'message': f"Query error: {error[:200]}",
                    'query_preview': query[:100] + '...' if len(query) > 100 else query,
                    'error': error
                }
                self._performance_alerts.append(alert)
                alert_created = True
                logger.error(f"Query error alert: {alert['message']}")
            
        except Exception as e:
            logger.error(f"Error checking performance alerts: {str(e)}")
    
    def _record_system_metrics(self) -> None:
        """Record current system metrics."""
        try:
            metrics = self.get_performance_metrics()
            self._system_metrics.append({
                'timestamp': time.time(),
                'metrics': asdict(metrics)
            })
        except Exception as e:
            logger.error(f"Error recording system metrics: {str(e)}")
    
    def _find_optimization_opportunities(self) -> List[str]:
        """Find optimization opportunities from query patterns."""
        opportunities = []
        
        try:
            # Analyze frequent slow queries
            slow_query_patterns = defaultdict(int)
            for query_hash, metrics in self._query_metrics.items():
                slow_count = sum(1 for m in metrics if m['duration_ms'] > self.slow_query_threshold_ms)
                if slow_count > 5:  # More than 5 slow executions
                    slow_query_patterns[query_hash] = slow_count
            
            if slow_query_patterns:
                opportunities.append(f"Found {len(slow_query_patterns)} frequently slow query patterns")
            
            # Analyze table access frequency
            table_frequency = defaultdict(int)
            for metrics in self._query_metrics.values():
                for metric in metrics:
                    if metric['table_name']:
                        table_frequency[metric['table_name']] += 1
            
            # Suggest indexing for heavily accessed tables
            total_queries = sum(table_frequency.values())
            for table, count in table_frequency.items():
                if count > total_queries * 0.2:  # > 20% of queries
                    opportunities.append(f"Table '{table}' needs index optimization (heavy access pattern)")
            
        except Exception as e:
            logger.error(f"Error finding optimization opportunities: {str(e)}")
        
        return opportunities
    
    def _analyze_time_patterns(self) -> Dict[str, Any]:
        """Analyze time-based query patterns."""
        try:
            current_time = time.time()
            last_hour = current_time - 3600
            last_day = current_time - 86400
            
            patterns = {
                'last_hour_queries': 0,
                'last_day_queries': 0,
                'peak_hour_qps': 0,
                'off_peak_hour_qps': 0
            }
            
            # Count queries in different time periods
            for metrics in self._query_metrics.values():
                for metric in metrics:
                    if metric['timestamp'] > last_hour:
                        patterns['last_hour_queries'] += 1
                    if metric['timestamp'] > last_day:
                        patterns['last_day_queries'] += 1
            
            # Calculate QPS for last hour
            patterns['last_hour_qps'] = patterns['last_hour_queries'] / 3600
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing time patterns: {str(e)}")
            return {}
    
    def _get_cache_hit_rate(self) -> float:
        """Get cache hit rate if available."""
        try:
            if hasattr(self.db_manager, 'vector_cache'):
                # Would get actual cache statistics
                return 0.75  # Placeholder
            return 0.0
        except:
            return 0.0
    
    def _get_active_connections(self) -> int:
        """Get number of active database connections."""
        try:
            if hasattr(self.db_manager, 'pg_pool'):
                pool = self.db_manager.pg_pool
                if hasattr(pool, 'taken'):
                    return pool.taken.qsize() if hasattr(pool.taken, 'qsize') else 0
            return 0
        except:
            return 0 