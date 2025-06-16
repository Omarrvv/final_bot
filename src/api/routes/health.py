"""
Phase 5: Environment Hardening - Health Monitoring Endpoints
Production-ready health check and monitoring system
"""
import time
import json
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import logging

# Import our core services
import sys
import os
sys.path.append('src')

from src.services.database_manager_service import DatabaseManagerService
from src.services.knowledge_base_service import KnowledgeBaseService
from src.nlu.engine import NLUEngine

# Validation schemas for input validation  
from ..schemas.health_schemas import (
    HealthCheckResponse, DetailedHealthResponse, PerformanceMetricsResponse,
    ReadinessCheckResponse, LivenessCheckResponse, RequestMetricsRequest,
    HealthAlertsResponse
)

logger = logging.getLogger(__name__)

# Create router for health endpoints
router = APIRouter(prefix="/api/health", tags=["health"])

# Global health metrics storage
health_metrics = {
    "system_start_time": datetime.utcnow(),
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0,
    "database_queries": 0,
    "api_calls": 0,
    "average_response_time": 0.0,
    "last_health_check": None,
    "alerts": []
}

# Performance thresholds
PERFORMANCE_THRESHOLDS = {
    "response_time_warning": 500,  # ms
    "response_time_critical": 2000,  # ms
    "memory_warning": 800,  # MB
    "memory_critical": 1500,  # MB
    "database_query_warning": 100,  # ms
    "error_rate_warning": 0.05,  # 5%
    "error_rate_critical": 0.15  # 15%
}

class HealthMonitor:
    """Production health monitoring system."""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.db_manager = None
        self.nlu_engine = None
        self.kb_service = None
        
    def initialize_services(self):
        """Initialize core services for health checking."""
        try:
            self.db_manager = DatabaseManagerService()
            self.kb_service = KnowledgeBaseService(self.db_manager)
            self.nlu_engine = NLUEngine('configs/models.json', self.kb_service)
            return True
        except Exception as e:
            logger.error(f"Failed to initialize services for health monitoring: {e}")
            return False
    
    def check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and performance."""
        try:
            if not self.db_manager:
                self.db_manager = DatabaseManagerService()
            
            start_time = time.time()
            connection_ok = self.db_manager.test_connection()
            connection_time = (time.time() - start_time) * 1000
            
            if not connection_ok:
                return {
                    "status": "CRITICAL",
                    "message": "Database connection failed",
                    "response_time_ms": connection_time
                }
            
            # Test a simple query
            start_time = time.time()
            result = self.db_manager.generic_search("attractions", limit=1)
            query_time = (time.time() - start_time) * 1000
            
            status = "HEALTHY"
            if query_time > PERFORMANCE_THRESHOLDS["database_query_warning"]:
                status = "WARNING"
            
            return {
                "status": status,
                "message": "Database operational",
                "connection_time_ms": round(connection_time, 2),
                "query_time_ms": round(query_time, 2),
                "sample_results": len(result) if result else 0
            }
            
        except Exception as e:
            return {
                "status": "CRITICAL",
                "message": f"Database health check failed: {str(e)}",
                "error": str(e)
            }
    
    def check_nlu_health(self) -> Dict[str, Any]:
        """Check NLU engine and embedding service health."""
        try:
            if not self.nlu_engine:
                self.kb_service = KnowledgeBaseService(DatabaseManagerService())
                self.nlu_engine = NLUEngine('configs/models.json', self.kb_service)
            
            # Test embedding service
            embedding_status = "CRITICAL"
            embedding_message = "Embedding service not ready"
            
            if self.nlu_engine.embedding_service and self.nlu_engine.embedding_service.is_ready():
                embedding_status = "HEALTHY"
                embedding_message = "Embedding service operational"
                
                # Test embedding generation
                start_time = time.time()
                test_embedding = self.nlu_engine.embedding_service.generate_embedding("test health check")
                embedding_time = (time.time() - start_time) * 1000
                
                if embedding_time > 200:  # 200ms threshold for embeddings
                    embedding_status = "WARNING"
                    embedding_message = f"Embedding generation slow: {embedding_time:.1f}ms"
            
            # Test intent classification
            start_time = time.time()
            result = self.nlu_engine.process("What are the best attractions in Cairo?", "health_check")
            classification_time = (time.time() - start_time) * 1000
            
            classification_status = "HEALTHY"
            if classification_time > PERFORMANCE_THRESHOLDS["response_time_warning"]:
                classification_status = "WARNING"
            
            intent = result.get('intent', 'unknown') if result else 'failed'
            
            return {
                "status": "HEALTHY" if embedding_status == "HEALTHY" and classification_status == "HEALTHY" else "WARNING",
                "embedding_service": {
                    "status": embedding_status,
                    "message": embedding_message
                },
                "intent_classification": {
                    "status": classification_status,
                    "response_time_ms": round(classification_time, 2),
                    "test_result": intent
                },
                "models_loaded": len(self.nlu_engine.transformer_models),
                "intents_configured": len(self.nlu_engine.models_config.get('intents', {}))
            }
            
        except Exception as e:
            return {
                "status": "CRITICAL",
                "message": f"NLU health check failed: {str(e)}",
                "error": str(e)
            }
        
    def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage."""
        try:
            process = psutil.Process()
            
            # Memory usage
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            memory_status = "HEALTHY"
            
            if memory_mb > PERFORMANCE_THRESHOLDS["memory_critical"]:
                memory_status = "CRITICAL"
            elif memory_mb > PERFORMANCE_THRESHOLDS["memory_warning"]:
                memory_status = "WARNING"
            
            # CPU usage
            cpu_percent = process.cpu_percent(interval=0.1)
            cpu_status = "HEALTHY"
            if cpu_percent > 80:
                cpu_status = "WARNING"
            elif cpu_percent > 95:
                cpu_status = "CRITICAL"
            
            # System uptime
            uptime = datetime.utcnow() - self.start_time
            
            return {
                "status": memory_status if memory_status != "HEALTHY" else cpu_status,
                "memory": {
                    "usage_mb": round(memory_mb, 1),
                    "status": memory_status,
                    "threshold_warning": PERFORMANCE_THRESHOLDS["memory_warning"],
                    "threshold_critical": PERFORMANCE_THRESHOLDS["memory_critical"]
                },
                "cpu": {
                    "usage_percent": round(cpu_percent, 1),
                    "status": cpu_status
                },
                "uptime": {
                    "seconds": int(uptime.total_seconds()),
                    "human_readable": str(uptime).split('.')[0]
                }
            }
            
        except Exception as e:
            return {
                "status": "CRITICAL",
                "message": f"System resource check failed: {str(e)}",
                "error": str(e)
            }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics and statistics."""
        total_requests = health_metrics["total_requests"]
        
        if total_requests == 0:
            return {
                "status": "HEALTHY",
                "message": "No requests processed yet",
                "metrics": health_metrics
            }
        
        success_rate = health_metrics["successful_requests"] / total_requests
        error_rate = health_metrics["failed_requests"] / total_requests
        
        status = "HEALTHY"
        if error_rate > PERFORMANCE_THRESHOLDS["error_rate_critical"]:
            status = "CRITICAL"
        elif error_rate > PERFORMANCE_THRESHOLDS["error_rate_warning"]:
            status = "WARNING"
        
        return {
            "status": status,
            "metrics": {
                "total_requests": total_requests,
                "success_rate": round(success_rate * 100, 2),
                "error_rate": round(error_rate * 100, 2),
                "average_response_time_ms": round(health_metrics["average_response_time"], 2),
                "database_queries": health_metrics["database_queries"],
                "api_calls": health_metrics["api_calls"]
            },
            "thresholds": {
                "error_rate_warning": PERFORMANCE_THRESHOLDS["error_rate_warning"] * 100,
                "error_rate_critical": PERFORMANCE_THRESHOLDS["error_rate_critical"] * 100,
                "response_time_warning": PERFORMANCE_THRESHOLDS["response_time_warning"],
                "response_time_critical": PERFORMANCE_THRESHOLDS["response_time_critical"]
            }
        }

# Global health monitor instance
health_monitor = HealthMonitor()

@router.get("/")
async def basic_health_check():
    """Basic health check endpoint - lightweight."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Egypt Tourism Chatbot",
        "version": "1.0.0",
        "uptime_seconds": int((datetime.utcnow() - health_metrics["system_start_time"]).total_seconds())
    }

@router.get("/detailed")
async def detailed_health_check():
    """Comprehensive health check with all systems."""
    health_results = {
        "timestamp": datetime.utcnow().isoformat(),
        "overall_status": "HEALTHY",
        "components": {}
    }
    
    # Initialize services if needed
    if not health_monitor.db_manager:
        init_success = health_monitor.initialize_services()
        if not init_success:
            health_results["overall_status"] = "CRITICAL"
            health_results["initialization_error"] = "Failed to initialize core services"
    
    # Check all components
    components = {
        "database": health_monitor.check_database_health,
        "nlu_system": health_monitor.check_nlu_health,
        "system_resources": health_monitor.check_system_resources
    }
    
    critical_issues = []
    warnings = []
    
    for component_name, check_func in components.items():
        try:
            result = check_func()
            health_results["components"][component_name] = result
            
            if result["status"] == "CRITICAL":
                critical_issues.append(f"{component_name}: {result.get('message', 'Critical issue')}")
            elif result["status"] == "WARNING":
                warnings.append(f"{component_name}: {result.get('message', 'Warning')}")
                
        except Exception as e:
            health_results["components"][component_name] = {
                "status": "CRITICAL",
                "error": str(e)
            }
            critical_issues.append(f"{component_name}: Health check failed")
    
    # Determine overall status
    if critical_issues:
        health_results["overall_status"] = "CRITICAL"
        health_results["critical_issues"] = critical_issues
    elif warnings:
        health_results["overall_status"] = "WARNING"
        health_results["warnings"] = warnings
    
    # Update health metrics
    health_metrics["last_health_check"] = datetime.utcnow().isoformat()
    
    return health_results

@router.get("/performance")
async def performance_metrics():
    """Get performance metrics and statistics."""
    return health_monitor.get_performance_metrics()

@router.get("/readiness")
async def readiness_check():
    """Kubernetes-style readiness probe."""
    try:
        # Quick checks for essential services
        db_check = health_monitor.check_database_health()
        
        if db_check["status"] == "CRITICAL":
            raise HTTPException(status_code=503, detail="Database not ready")
        
        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "database": db_check["status"]
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service not ready: {str(e)}")
        
@router.get("/liveness")
async def liveness_check():
    """Kubernetes-style liveness probe."""
    # Very lightweight check - just verify the service is responding
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "pid": os.getpid()
    }

@router.post("/metrics/request")
async def record_request_metrics(
    response_time_ms: float,
    success: bool = True,
    database_used: bool = False,
    api_used: bool = False
):
    """Record request metrics for monitoring."""
    try:
        health_metrics["total_requests"] += 1
        
        if success:
            health_metrics["successful_requests"] += 1
        else:
            health_metrics["failed_requests"] += 1
        
        if database_used:
            health_metrics["database_queries"] += 1
        
        if api_used:
            health_metrics["api_calls"] += 1
        
        # Update average response time
        current_avg = health_metrics["average_response_time"]
        total_requests = health_metrics["total_requests"]
        health_metrics["average_response_time"] = (
            (current_avg * (total_requests - 1) + response_time_ms) / total_requests
        )
        
        return {"status": "recorded"}
    
    except Exception as e:
        logger.error(f"Failed to record metrics: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/alerts")
async def get_health_alerts():
    """Get current system alerts and warnings."""
    current_alerts = []
    
    # Check for performance issues
    if health_metrics["average_response_time"] > PERFORMANCE_THRESHOLDS["response_time_warning"]:
        current_alerts.append({
            "type": "performance",
            "severity": "warning",
            "message": f"Average response time high: {health_metrics['average_response_time']:.1f}ms",
            "threshold": PERFORMANCE_THRESHOLDS["response_time_warning"]
        })
    
    # Check error rate
    if health_metrics["total_requests"] > 0:
        error_rate = health_metrics["failed_requests"] / health_metrics["total_requests"]
        if error_rate > PERFORMANCE_THRESHOLDS["error_rate_warning"]:
            severity = "critical" if error_rate > PERFORMANCE_THRESHOLDS["error_rate_critical"] else "warning"
            current_alerts.append({
                "type": "error_rate",
                "severity": severity,
                "message": f"Error rate high: {error_rate * 100:.1f}%",
                "threshold": PERFORMANCE_THRESHOLDS["error_rate_warning"] * 100
            })
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "alerts": current_alerts,
        "alert_count": len(current_alerts)
    } 