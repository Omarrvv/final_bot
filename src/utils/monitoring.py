"""
Monitoring utilities for the Egypt Tourism Chatbot.
Provides logging, metrics, and tracing capabilities.
"""
import os
import time
import json
import logging
import traceback
import threading
import functools
from flask import request
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class Metrics:
    """Metrics collection and reporting."""
    
    def __init__(self, app_name: str = "egypt_tourism_chatbot"):
        """
        Initialize metrics collector.
        
        Args:
            app_name (str): Application name
        """
        self.app_name = app_name
        self.metrics = {}
        self.timers = {}
        self.lock = threading.Lock()
        self.backend = os.getenv("METRICS_BACKEND", "").lower()
        self.enabled = os.getenv("METRICS_ENABLED", "true").lower() == "true"
        
        # Initialize metrics backend if available
        if self.enabled:
            self._initialize_backend()
    
    def _initialize_backend(self):
        """Initialize metrics backend based on environment configuration."""
        if self.backend == "prometheus":
            self._initialize_prometheus()
        elif self.backend == "statsd":
            self._initialize_statsd()
        else:
            logger.info("Using in-memory metrics backend")
    
    def _initialize_prometheus(self):
        """Initialize Prometheus metrics backend."""
        try:
            from prometheus_client import Counter, Gauge, Histogram, Summary, start_http_server
            
            # Start Prometheus metrics server
            port = int(os.getenv("PROMETHEUS_PORT", "9090"))
            start_http_server(port)
            
            # Initialize metrics
            self.prom_request_count = Counter(
                'chatbot_requests_total', 
                'Total request count',
                ['method', 'endpoint', 'status']
            )
            
            self.prom_request_latency = Histogram(
                'chatbot_request_latency_seconds',
                'Request latency in seconds',
                ['method', 'endpoint']
            )
            
            self.prom_active_sessions = Gauge(
                'chatbot_active_sessions',
                'Number of active sessions'
            )
            
            self.prom_intent_count = Counter(
                'chatbot_intent_count',
                'Intent classification count',
                ['intent', 'confidence_bucket']
            )
            
            self.prom_api_latency = Histogram(
                'chatbot_api_latency_seconds',
                'External API latency in seconds',
                ['service', 'method']
            )
            
            self.prom_error_count = Counter(
                'chatbot_errors_total',
                'Total error count',
                ['component', 'error_type']
            )
            
            logger.info(f"Prometheus metrics server started on port {port}")
            
        except ImportError:
            logger.warning("Prometheus client not installed. Falling back to in-memory metrics.")
            self.backend = ""
    
    def _initialize_statsd(self):
        """Initialize StatsD metrics backend."""
        try:
            import statsd
            
            # Initialize StatsD client
            host = os.getenv("STATSD_HOST", "localhost")
            port = int(os.getenv("STATSD_PORT", "8125"))
            prefix = os.getenv("STATSD_PREFIX", f"{self.app_name}.")
            
            self.statsd_client = statsd.StatsClient(host, port, prefix=prefix)
            
            logger.info(f"StatsD client initialized ({host}:{port}, prefix: {prefix})")
            
        except ImportError:
            logger.warning("StatsD client not installed. Falling back to in-memory metrics.")
            self.backend = ""
    
    def increment(self, metric_name: str, value: int = 1, tags: Dict = None):
        """
        Increment a counter metric.
        
        Args:
            metric_name (str): Metric name
            value (int): Increment value
            tags (dict, optional): Metric tags
        """
        if not self.enabled:
            return
        
        tags = tags or {}
        
        # Update in-memory metrics
        with self.lock:
            if metric_name not in self.metrics:
                self.metrics[metric_name] = {"value": 0, "type": "counter"}
            
            self.metrics[metric_name]["value"] += value
            
            if "tags" not in self.metrics[metric_name]:
                self.metrics[metric_name]["tags"] = {}
            
            for tag_key, tag_value in tags.items():
                tag_key_str = str(tag_key)
                tag_value_str = str(tag_value)
                
                if tag_key_str not in self.metrics[metric_name]["tags"]:
                    self.metrics[metric_name]["tags"][tag_key_str] = {}
                
                if tag_value_str not in self.metrics[metric_name]["tags"][tag_key_str]:
                    self.metrics[metric_name]["tags"][tag_key_str][tag_value_str] = 0
                
                self.metrics[metric_name]["tags"][tag_key_str][tag_value_str] += value
        
        # Send to backend if available
        if self.backend == "prometheus":
            if metric_name == "request_count":
                self.prom_request_count.labels(
                    tags.get("method", ""),
                    tags.get("endpoint", ""),
                    tags.get("status", "")
                ).inc(value)
            elif metric_name == "intent_count":
                self.prom_intent_count.labels(
                    tags.get("intent", ""),
                    tags.get("confidence_bucket", "")
                ).inc(value)
            elif metric_name == "error_count":
                self.prom_error_count.labels(
                    tags.get("component", ""),
                    tags.get("error_type", "")
                ).inc(value)
            
        elif self.backend == "statsd":
            # Format tag string if tags are provided
            tag_str = ""
            if tags:
                tag_str = "," + ",".join(f"{k}:{v}" for k, v in tags.items())
            
            self.statsd_client.incr(f"{metric_name}{tag_str}", value)
    
    def gauge(self, metric_name: str, value: float, tags: Dict = None):
        """
        Set a gauge metric value.
        
        Args:
            metric_name (str): Metric name
            value (float): Gauge value
            tags (dict, optional): Metric tags
        """
        if not self.enabled:
            return
        
        tags = tags or {}
        
        # Update in-memory metrics
        with self.lock:
            if metric_name not in self.metrics:
                self.metrics[metric_name] = {"value": 0, "type": "gauge"}
            
            self.metrics[metric_name]["value"] = value
            
            if "tags" not in self.metrics[metric_name]:
                self.metrics[metric_name]["tags"] = {}
            
            for tag_key, tag_value in tags.items():
                tag_key_str = str(tag_key)
                tag_value_str = str(tag_value)
                
                if tag_key_str not in self.metrics[metric_name]["tags"]:
                    self.metrics[metric_name]["tags"][tag_key_str] = {}
                
                self.metrics[metric_name]["tags"][tag_key_str][tag_value_str] = value
        
        # Send to backend if available
        if self.backend == "prometheus":
            if metric_name == "active_sessions":
                self.prom_active_sessions.set(value)
            
        elif self.backend == "statsd":
            # Format tag string if tags are provided
            tag_str = ""
            if tags:
                tag_str = "," + ",".join(f"{k}:{v}" for k, v in tags.items())
            
            self.statsd_client.gauge(f"{metric_name}{tag_str}", value)
    
    def timing(self, metric_name: str, value: float, tags: Dict = None):
        """
        Record timing metric.
        
        Args:
            metric_name (str): Metric name
            value (float): Timing value in milliseconds
            tags (dict, optional): Metric tags
        """
        if not self.enabled:
            return
        
        tags = tags or {}
        
        # Update in-memory metrics
        with self.lock:
            if metric_name not in self.metrics:
                self.metrics[metric_name] = {"value": [], "type": "timing"}
            
            if not isinstance(self.metrics[metric_name]["value"], list):
                self.metrics[metric_name]["value"] = []
            
            self.metrics[metric_name]["value"].append(value)
            
            # Keep only the last 100 values to avoid memory growth
            if len(self.metrics[metric_name]["value"]) > 100:
                self.metrics[metric_name]["value"] = self.metrics[metric_name]["value"][-100:]
            
            if "tags" not in self.metrics[metric_name]:
                self.metrics[metric_name]["tags"] = {}
            
            for tag_key, tag_value in tags.items():
                tag_key_str = str(tag_key)
                tag_value_str = str(tag_value)
                
                if tag_key_str not in self.metrics[metric_name]["tags"]:
                    self.metrics[metric_name]["tags"][tag_key_str] = {}
                
                if tag_value_str not in self.metrics[metric_name]["tags"][tag_key_str]:
                    self.metrics[metric_name]["tags"][tag_key_str][tag_value_str] = []
                
                self.metrics[metric_name]["tags"][tag_key_str][tag_value_str].append(value)
                
                # Keep only the last 100 values to avoid memory growth
                if len(self.metrics[metric_name]["tags"][tag_key_str][tag_value_str]) > 100:
                    self.metrics[metric_name]["tags"][tag_key_str][tag_value_str] = self.metrics[metric_name]["tags"][tag_key_str][tag_value_str][-100:]
        
        # Send to backend if available
        if self.backend == "prometheus":
            if metric_name == "request_latency":
                self.prom_request_latency.labels(
                    tags.get("method", ""),
                    tags.get("endpoint", "")
                ).observe(value / 1000.0)  # Convert to seconds
            elif metric_name == "api_latency":
                self.prom_api_latency.labels(
                    tags.get("service", ""),
                    tags.get("method", "")
                ).observe(value / 1000.0)  # Convert to seconds
            
        elif self.backend == "statsd":
            # Format tag string if tags are provided
            tag_str = ""
            if tags:
                tag_str = "," + ",".join(f"{k}:{v}" for k, v in tags.items())
            
            self.statsd_client.timing(f"{metric_name}{tag_str}", value)
    
    def start_timer(self, metric_name: str, tags: Dict = None) -> str:
        """
        Start a timer for measuring execution time.
        
        Args:
            metric_name (str): Metric name
            tags (dict, optional): Metric tags
            
        Returns:
            str: Timer ID
        """
        if not self.enabled:
            return ""
        
        timer_id = str(uuid.uuid4())
        
        with self.lock:
            self.timers[timer_id] = {
                "metric_name": metric_name,
                "start_time": time.time(),
                "tags": tags or {}
            }
        
        return timer_id
    
    def stop_timer(self, timer_id: str) -> float:
        """
        Stop a timer and record the timing.
        
        Args:
            timer_id (str): Timer ID from start_timer
            
        Returns:
            float: Elapsed time in milliseconds
        """
        if not self.enabled or not timer_id or timer_id not in self.timers:
            return 0.0
        
        with self.lock:
            timer = self.timers.pop(timer_id)
            elapsed_time = (time.time() - timer["start_time"]) * 1000.0  # Convert to milliseconds
            
            # Record timing
            self.timing(timer["metric_name"], elapsed_time, timer["tags"])
            
            return elapsed_time
    
    def timed(self, metric_name: str, tags: Dict = None):
        """
        Decorator for timing function execution.
        
        Args:
            metric_name (str): Metric name
            tags (dict, optional): Metric tags
            
        Returns:
            callable: Decorated function
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                timer_id = self.start_timer(metric_name, tags)
                try:
                    return func(*args, **kwargs)
                finally:
                    self.stop_timer(timer_id)
            return wrapper
        return decorator
    
    def get_metrics(self) -> Dict:
        """
        Get current metrics.
        
        Returns:
            dict: Current metrics
        """
        with self.lock:
            # Create a deep copy of metrics to avoid modification during iteration
            return json.loads(json.dumps(self.metrics))

class ErrorTracker:
    """Error tracking and reporting."""
    
    def __init__(self, app_name: str = "egypt_tourism_chatbot"):
        """
        Initialize error tracker.
        
        Args:
            app_name (str): Application name
        """
        self.app_name = app_name
        self.backend = os.getenv("ERROR_TRACKING_BACKEND", "").lower()
        self.enabled = os.getenv("ERROR_TRACKING_ENABLED", "true").lower() == "true"
        self.metrics = Metrics(app_name)
        
        # Initialize error tracking backend if available
        if self.enabled:
            self._initialize_backend()
    
    def _initialize_backend(self):
        """Initialize error tracking backend based on environment configuration."""
        if self.backend == "sentry":
            self._initialize_sentry()
        else:
            logger.info("Using default error tracking (logging only)")
    
    def _initialize_sentry(self):
        """Initialize Sentry error tracking."""
        try:
            import sentry_sdk
            from sentry_sdk.integrations.flask import FlaskIntegration
            
            sentry_dsn = os.getenv("SENTRY_DSN")
            if not sentry_dsn:
                logger.warning("Sentry DSN not configured. Falling back to default error tracking.")
                self.backend = ""
                return
            
            environment = os.getenv("ENVIRONMENT", "production")
            
            sentry_sdk.init(
                dsn=sentry_dsn,
                environment=environment,
                integrations=[FlaskIntegration()],
                traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))
            )
            
            logger.info(f"Sentry error tracking initialized (environment: {environment})")
            
        except ImportError:
            logger.warning("Sentry SDK not installed. Falling back to default error tracking.")
            self.backend = ""
    
    def capture_exception(self, exc: Exception, context: Dict = None):
        """
        Capture an exception.
        
        Args:
            exc (Exception): Exception to capture
            context (dict, optional): Additional context
        """
        context = context or {}
        
        # Log the exception
        logger.exception(f"Error captured: {str(exc)}")
        
        # Track error count
        error_type = type(exc).__name__
        component = context.get("component", "unknown")
        self.metrics.increment("error_count", tags={
            "error_type": error_type,
            "component": component
        })
        
        # Send to backend if available
        if self.backend == "sentry":
            import sentry_sdk
            
            with sentry_sdk.push_scope() as scope:
                # Add context
                for key, value in context.items():
                    scope.set_tag(key, value)
                
                sentry_sdk.capture_exception(exc)
    
    def capture_message(self, message: str, level: str = "error", context: Dict = None):
        """
        Capture a message.
        
        Args:
            message (str): Message to capture
            level (str): Message level (debug, info, warning, error, critical)
            context (dict, optional): Additional context
        """
        context = context or {}
        
        # Log the message
        log_method = getattr(logger, level.lower(), logger.error)
        log_method(f"Message captured: {message}")
        
        # Track message count
        component = context.get("component", "unknown")
        self.metrics.increment("message_count", tags={
            "level": level,
            "component": component
        })
        
        # Send to backend if available
        if self.backend == "sentry":
            import sentry_sdk
            
            with sentry_sdk.push_scope() as scope:
                # Add context
                for key, value in context.items():
                    scope.set_tag(key, value)
                
                # Set level
                scope.level = level
                
                # Capture message
                sentry_sdk.capture_message(message)
    
    def wrap_flask_app(self, app):
        """
        Add error tracking middleware to a Flask app.
        
        Args:
            app: Flask application
        """
        if not self.enabled:
            return
        
        @app.errorhandler(Exception)
        def handle_exception(exc):
            """Handle exceptions in Flask routes."""
            self.capture_exception(exc, {
                "component": "flask",
                "url": getattr(request, "url", "unknown"),
                "method": getattr(request, "method", "unknown"),
                "endpoint": getattr(request, "endpoint", "unknown")
            })
            
            # Re-raise the exception for Flask to handle
            raise exc
        
        logger.info("Error tracking middleware added to Flask app")


class HealthCheck:
    """Health check monitoring and reporting."""
    
    def __init__(self, app_name: str = "egypt_tourism_chatbot"):
        """
        Initialize health check monitor.
        
        Args:
            app_name (str): Application name
        """
        self.app_name = app_name
        self.checks = {}
        self.enabled = os.getenv("HEALTH_CHECK_ENABLED", "true").lower() == "true"
        self.metrics = Metrics(app_name)
        
        # Add default health checks
        if self.enabled:
            self.add_check("memory", self._check_memory)
            self.add_check("disk", self._check_disk)
    
    def add_check(self, name: str, check_func: Callable[[], Dict]):
        """
        Add a health check.
        
        Args:
            name (str): Check name
            check_func (callable): Check function that returns a dict with 'status' and 'details' keys
        """
        if not self.enabled:
            return
        
        self.checks[name] = check_func
        logger.info(f"Health check added: {name}")
    
    def run_checks(self) -> Dict:
        """
        Run all health checks.
        
        Returns:
            dict: Health check results
        """
        if not self.enabled:
            return {"status": "disabled", "checks": {}}
        
        results = {}
        overall_status = "healthy"
        
        for name, check_func in self.checks.items():
            try:
                start_time = time.time()
                check_result = check_func()
                elapsed_time = (time.time() - start_time) * 1000.0  # Convert to milliseconds
                
                # Track check latency
                self.metrics.timing("health_check_latency", elapsed_time, {
                    "check": name
                })
                
                # Add latency to result
                check_result["latency_ms"] = round(elapsed_time, 2)
                
                # Update overall status
                if check_result.get("status") in ["warning", "unhealthy"] and overall_status == "healthy":
                    overall_status = check_result["status"]
                elif check_result.get("status") == "unhealthy" and overall_status == "warning":
                    overall_status = "unhealthy"
                
                results[name] = check_result
                
            except Exception as e:
                results[name] = {
                    "status": "error",
                    "error": str(e),
                    "details": traceback.format_exc()
                }
                
                overall_status = "unhealthy"
                
                # Track check errors
                self.metrics.increment("health_check_error", tags={
                    "check": name
                })
        
        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "checks": results
        }
    
    def _check_memory(self) -> Dict:
        """
        Check memory usage.
        
        Returns:
            dict: Memory check result
        """
        try:
            import psutil
            
            process = psutil.Process()
            memory_info = process.memory_info()
            
            # Get memory usage in MB
            rss_mb = memory_info.rss / (1024 * 1024)
            vms_mb = memory_info.vms / (1024 * 1024)
            
            # Get system memory
            system_memory = psutil.virtual_memory()
            total_mb = system_memory.total / (1024 * 1024)
            available_mb = system_memory.available / (1024 * 1024)
            used_percent = system_memory.percent
            
            # Determine status based on memory usage
            status = "healthy"
            if used_percent > 90:
                status = "unhealthy"
            elif used_percent > 75:
                status = "warning"
            
            return {
                "status": status,
                "details": {
                    "process_rss_mb": round(rss_mb, 2),
                    "process_vms_mb": round(vms_mb, 2),
                    "system_total_mb": round(total_mb, 2),
                    "system_available_mb": round(available_mb, 2),
                    "system_used_percent": round(used_percent, 2)
                }
            }
            
        except ImportError:
            return {
                "status": "unknown",
                "details": {
                    "error": "psutil module not available"
                }
            }
    
    def _check_disk(self) -> Dict:
        """
        Check disk usage.
        
        Returns:
            dict: Disk check result
        """
        try:
            import psutil
            
            # Get disk usage for the current directory
            disk_usage = psutil.disk_usage(".")
            
            # Convert to GB
            total_gb = disk_usage.total / (1024 * 1024 * 1024)
            used_gb = disk_usage.used / (1024 * 1024 * 1024)
            free_gb = disk_usage.free / (1024 * 1024 * 1024)
            used_percent = disk_usage.percent
            
            # Determine status based on disk usage
            status = "healthy"
            if used_percent > 90:
                status = "unhealthy"
            elif used_percent > 75:
                status = "warning"
            
            return {
                "status": status,
                "details": {
                    "total_gb": round(total_gb, 2),
                    "used_gb": round(used_gb, 2),
                    "free_gb": round(free_gb, 2),
                    "used_percent": round(used_percent, 2)
                }
            }
            
        except ImportError:
            return {
                "status": "unknown",
                "details": {
                    "error": "psutil module not available"
                }
            }
    
    def add_flask_route(self, app):
        """
        Add health check route to a Flask app.
        
        Args:
            app: Flask application
        """
        if not self.enabled:
            return
        
        @app.route('/health')
        def health_check():
            """Health check endpoint."""
            results = self.run_checks()
            
            # Set appropriate status code based on overall status
            status_code = 200
            if results["status"] == "warning":
                status_code = 200  # Still OK but with warning
            elif results["status"] == "unhealthy":
                status_code = 503  # Service Unavailable
            
            return results, status_code
        
        logger.info("Health check route added to Flask app")


def configure_logging(app_name: str = "egypt_tourism_chatbot", log_level: str = None):
    """
    Configure logging for the application.
    
    Args:
        app_name (str): Application name
        log_level (str, optional): Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Determine log level
    level_name = log_level or os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Set up log handler based on environment
    log_handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        '%Y-%m-%d %H:%M:%S'
    ))
    log_handlers.append(console_handler)
    
    # File handler if LOG_FILE is specified
    log_file = os.getenv("LOG_FILE")
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                '%Y-%m-%d %H:%M:%S'
            ))
            log_handlers.append(file_handler)
        except Exception as e:
            logging.warning(f"Failed to create file handler: {str(e)}")
    
    # Configure logger for our app
    app_logger = logging.getLogger(app_name)
    app_logger.setLevel(level)
    
    # Remove existing handlers
    for handler in app_logger.handlers[:]:
        app_logger.removeHandler(handler)
    
    # Add new handlers
    for handler in log_handlers:
        app_logger.addHandler(handler)
    
    # Configure third-party loggers
    third_party_level = getattr(logging, os.getenv("THIRD_PARTY_LOG_LEVEL", "WARNING").upper(), logging.WARNING)
    
    for logger_name in ["requests", "urllib3", "werkzeug", "flask", "pika", "boto3", "botocore"]:
        third_party_logger = logging.getLogger(logger_name)
        third_party_logger.setLevel(third_party_level)
    
    logging.info(f"Logging configured: level={level_name}, app={app_name}")
