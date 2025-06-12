"""
Performance monitoring middleware for Phase 4 optimization.
Tracks request timing and identifies performance bottlenecks.
"""
import time
import logging
from typing import Dict, Any, List, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
import asyncio
from collections import defaultdict, deque
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """
    Phase 4: Performance monitoring middleware to track request timing.
    Identifies slow requests and provides performance analytics.
    """
    
    def __init__(self, app, slow_request_threshold: float = 1.0, max_history: int = 1000):
        """
        Initialize performance monitoring middleware.
        
        Args:
            app: FastAPI application
            slow_request_threshold: Time in seconds to consider a request slow
            max_history: Maximum number of requests to keep in history
        """
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold
        self.max_history = max_history
        
        # Performance metrics storage
        self.request_history = deque(maxlen=max_history)
        self.endpoint_stats = defaultdict(lambda: {
            'total_requests': 0,
            'total_time': 0.0,
            'slow_requests': 0,
            'fastest_time': float('inf'),
            'slowest_time': 0.0,
            'recent_times': deque(maxlen=100)
        })
        
        # Phase targets from optimization plan
        self.performance_targets = {
            '/api/chat': 1.0,      # Chat API: <1s
            '/api/health': 0.1,    # Health checks: <100ms
            '/api/knowledge': 1.0, # Knowledge queries: <1s
            '/api/session': 0.5,   # Session operations: <500ms
        }
        
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Process request with performance monitoring."""
        start_time = time.time()
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        # Extract endpoint pattern for monitoring
        endpoint = self._get_endpoint_pattern(request.url.path)
        
        # Initialize request metadata
        request_metadata = {
            'method': request.method,
            'endpoint': endpoint,
            'start_time': start_time,
            'request_id': request_id,
            'user_agent': request.headers.get('user-agent', 'unknown')
        }
        
        try:
            # Call the next middleware/endpoint
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Add performance headers
            response.headers["X-Process-Time"] = f"{process_time:.3f}"
            response.headers["X-Request-ID"] = request_id
            
            # Record performance metrics
            self._record_request_metrics(
                endpoint=endpoint,
                method=request.method,
                status_code=response.status_code,
                process_time=process_time,
                request_id=request_id
            )
            
            # Log slow requests
            if process_time > self.slow_request_threshold:
                logger.warning(
                    f"⚠️  SLOW REQUEST: {request.method} {endpoint} took {process_time:.3f}s "
                    f"(threshold: {self.slow_request_threshold}s) - Request ID: {request_id}"
                )
                
                # Check against Phase 4 targets
                target = self._get_performance_target(endpoint)
                if target and process_time > target:
                    logger.error(
                        f"❌ PERFORMANCE TARGET MISSED: {endpoint} took {process_time:.3f}s "
                        f"(target: {target}s) - Request ID: {request_id}"
                    )
            
            return response
            
        except Exception as e:
            # Record error metrics
            process_time = time.time() - start_time
            
            self._record_request_metrics(
                endpoint=endpoint,
                method=request.method,
                status_code=500,
                process_time=process_time,
                request_id=request_id,
                error=str(e)
            )
            
            logger.error(
                f"❌ REQUEST ERROR: {request.method} {endpoint} failed after {process_time:.3f}s "
                f"- Error: {str(e)} - Request ID: {request_id}"
            )
            
            raise
    
    def _get_endpoint_pattern(self, path: str) -> str:
        """Extract endpoint pattern from path for grouping metrics."""
        # Normalize paths to group similar endpoints
        if path.startswith('/api/chat'):
            return '/api/chat'
        elif path.startswith('/api/knowledge'):
            return '/api/knowledge'
        elif path.startswith('/api/session'):
            return '/api/session'
        elif path.startswith('/api/health') or path.endswith('/health'):
            return '/api/health'
        elif path.startswith('/api/debug'):
            return '/api/debug'
        else:
            return path
    
    def _get_performance_target(self, endpoint: str) -> Optional[float]:
        """Get performance target for endpoint."""
        for pattern, target in self.performance_targets.items():
            if endpoint.startswith(pattern):
                return target
        return None
    
    def _record_request_metrics(self, endpoint: str, method: str, status_code: int, 
                               process_time: float, request_id: str, error: str = None):
        """Record request metrics for analysis."""
        
        # Update endpoint statistics
        stats = self.endpoint_stats[endpoint]
        stats['total_requests'] += 1
        stats['total_time'] += process_time
        stats['recent_times'].append(process_time)
        
        if process_time > self.slow_request_threshold:
            stats['slow_requests'] += 1
            
        if process_time < stats['fastest_time']:
            stats['fastest_time'] = process_time
            
        if process_time > stats['slowest_time']:
            stats['slowest_time'] = process_time
        
        # Add to request history
        request_record = {
            'timestamp': datetime.now(),
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code,
            'process_time': process_time,
            'request_id': request_id,
            'is_slow': process_time > self.slow_request_threshold,
            'error': error
        }
        
        self.request_history.append(request_record)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for health checks."""
        now = datetime.now()
        last_hour = now - timedelta(hours=1)
        
        # Filter recent requests
        recent_requests = [
            req for req in self.request_history 
            if req['timestamp'] > last_hour
        ]
        
        # Calculate summary statistics
        total_requests = len(recent_requests)
        slow_requests = len([req for req in recent_requests if req['is_slow']])
        error_requests = len([req for req in recent_requests if req['error']])
        
        # Calculate average response time
        avg_response_time = (
            sum(req['process_time'] for req in recent_requests) / total_requests
            if total_requests > 0 else 0
        )
        
        # Endpoint breakdown
        endpoint_summary = {}
        for endpoint, stats in self.endpoint_stats.items():
            if stats['total_requests'] > 0:
                avg_time = stats['total_time'] / stats['total_requests']
                recent_avg = (
                    sum(stats['recent_times']) / len(stats['recent_times'])
                    if stats['recent_times'] else 0
                )
                
                target = self._get_performance_target(endpoint)
                target_met = recent_avg <= target if target else True
                
                endpoint_summary[endpoint] = {
                    'total_requests': stats['total_requests'],
                    'average_time': avg_time,
                    'recent_average_time': recent_avg,
                    'slow_requests': stats['slow_requests'],
                    'fastest_time': stats['fastest_time'] if stats['fastest_time'] != float('inf') else 0,
                    'slowest_time': stats['slowest_time'],
                    'performance_target': target,
                    'target_met': target_met
                }
        
        return {
            'last_hour_summary': {
                'total_requests': total_requests,
                'slow_requests': slow_requests,
                'error_requests': error_requests,
                'average_response_time': avg_response_time,
                'slow_request_percentage': (slow_requests / total_requests * 100) if total_requests > 0 else 0
            },
            'endpoint_performance': endpoint_summary,
            'performance_targets': self.performance_targets,
            'monitoring_config': {
                'slow_request_threshold': self.slow_request_threshold,
                'max_history': self.max_history,
                'history_size': len(self.request_history)
            }
        }
    
    def get_slow_requests(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent slow requests for debugging."""
        slow_requests = [
            {
                'timestamp': req['timestamp'].isoformat(),
                'endpoint': req['endpoint'],
                'method': req['method'],
                'process_time': req['process_time'],
                'status_code': req['status_code'],
                'request_id': req['request_id'],
                'error': req['error']
            }
            for req in self.request_history 
            if req['is_slow']
        ]
        
        # Sort by process time (slowest first) and limit
        slow_requests.sort(key=lambda x: x['process_time'], reverse=True)
        return slow_requests[:limit]


def add_performance_middleware(app, slow_request_threshold: float = 1.0):
    """
    Add performance monitoring middleware to FastAPI app.
    
    Args:
        app: FastAPI application
        slow_request_threshold: Time in seconds to consider a request slow
    """
    middleware = PerformanceMonitoringMiddleware(app, slow_request_threshold)
    app.add_middleware(PerformanceMonitoringMiddleware, slow_request_threshold=slow_request_threshold)
    
    # Store middleware instance for access from routes
    app.state.performance_middleware = middleware
    
    logger.info(f"✅ Performance monitoring middleware added (threshold: {slow_request_threshold}s)")
    return middleware 