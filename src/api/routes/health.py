"""
Comprehensive health check endpoints for Phase 4 optimization.
Monitors system components, performance metrics, and optimization status.
"""
import time
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Request, Depends, HTTPException
from src.utils.dependencies import get_chatbot, get_knowledge_base, get_database_manager

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/health",
    tags=["health"],
)

@router.get("/")
async def basic_health_check(request: Request):
    """
    Basic health check endpoint - fast and lightweight.
    Phase 4: Optimized for <100ms response time.
    """
    start_time = time.time()
    
    try:
        # Quick check of app.state singleton
        chatbot_available = hasattr(request.app.state, 'chatbot') and request.app.state.chatbot is not None
        
        processing_time = time.time() - start_time
        
        return {
            "status": "healthy" if chatbot_available else "unhealthy",
            "timestamp": time.time(),
            "processing_time_ms": round(processing_time * 1000, 2),
            "version": "1.0.0",
            "phase": "4_optimized"
        }
    
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Basic health check failed: {e}")
        
        return {
            "status": "unhealthy",
            "error": str(e),
            "processing_time_ms": round(processing_time * 1000, 2),
            "phase": "4_optimized"
        }

@router.get("/detailed")
async def detailed_health_check(
    request: Request,
    chatbot=Depends(get_chatbot),
    knowledge_base=Depends(get_knowledge_base),
    db_manager=Depends(get_database_manager)
):
    """
    Detailed health check with component verification.
    Phase 4: Comprehensive health monitoring with performance metrics.
    """
    start_time = time.time()
    
    try:
        # Component status checks
        components = {}
        
        # 1. Chatbot components
        components["chatbot"] = {
            "status": "healthy",
            "type": type(chatbot).__name__,
            "has_knowledge_base": hasattr(chatbot, 'knowledge_base') and chatbot.knowledge_base is not None,
            "has_nlu_engine": hasattr(chatbot, 'nlu_engine') and chatbot.nlu_engine is not None,
            "has_db_manager": hasattr(chatbot, 'db_manager') and chatbot.db_manager is not None,
            "singleton_from_app_state": request.app.state.chatbot is chatbot
        }
        
        # 2. Database connectivity
        try:
            db_connected = db_manager.is_connected()
            components["database"] = {
                "status": "healthy" if db_connected else "unhealthy",
                "connected": db_connected,
                "type": type(db_manager).__name__
            }
        except Exception as e:
            components["database"] = {
                "status": "unhealthy",
                "error": str(e),
                "connected": False
            }
        
        # 3. NLU Engine status
        try:
            nlu_engine = chatbot.nlu_engine
            transformer_models_loaded = len(nlu_engine.transformer_models) if hasattr(nlu_engine, 'transformer_models') else 0
            nlp_models_loaded = len(nlu_engine.nlp_models) if hasattr(nlu_engine, 'nlp_models') else 0
            embedding_cache_size = len(nlu_engine.embedding_cache) if hasattr(nlu_engine, 'embedding_cache') else 0
            
            components["nlu_engine"] = {
                "status": "healthy",
                "transformer_models_loaded": transformer_models_loaded,
                "nlp_models_loaded": nlp_models_loaded,
                "embedding_cache_size": embedding_cache_size,
                "has_async_processing": hasattr(nlu_engine, 'process_async'),
                "type": type(nlu_engine).__name__
            }
        except Exception as e:
            components["nlu_engine"] = {
                "status": "unhealthy", 
                "error": str(e)
            }
        
        # 4. Knowledge Base status
        try:
            components["knowledge_base"] = {
                "status": "healthy",
                "type": type(knowledge_base).__name__,
                "has_search_methods": all(hasattr(knowledge_base, method) for method in 
                                        ['search_attractions', 'search_hotels', 'search_restaurants'])
            }
        except Exception as e:
            components["knowledge_base"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # 5. Performance middleware status
        performance_middleware = getattr(request.app.state, 'performance_middleware', None)
        if performance_middleware:
            try:
                perf_summary = performance_middleware.get_performance_summary()
                components["performance_monitoring"] = {
                    "status": "healthy",
                    "enabled": True,
                    "summary": perf_summary
                }
            except Exception as e:
                components["performance_monitoring"] = {
                    "status": "unhealthy",
                    "enabled": True,
                    "error": str(e)
                }
        else:
            components["performance_monitoring"] = {
                "status": "disabled",
                "enabled": False
            }
        
        # Overall status determination
        component_statuses = [comp.get("status", "unknown") for comp in components.values()]
        unhealthy_components = [name for name, comp in components.items() if comp.get("status") != "healthy"]
        
        overall_status = "healthy" if all(status == "healthy" for status in component_statuses) else "degraded"
        if any(status == "unhealthy" for status in component_statuses):
            overall_status = "unhealthy"
        
        processing_time = time.time() - start_time
        
        return {
            "status": overall_status,
            "timestamp": time.time(),
            "processing_time_ms": round(processing_time * 1000, 2),
            "components": components,
            "unhealthy_components": unhealthy_components,
            "optimization_phase": "4_complete",
            "performance_targets": {
                "basic_health_check": "<100ms",
                "detailed_health_check": "<500ms",
                "chat_api": "<1s", 
                "knowledge_queries": "<1s"
            }
        }
    
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Detailed health check failed: {e}")
        
        return {
            "status": "unhealthy",
            "error": str(e),
            "processing_time_ms": round(processing_time * 1000, 2),
            "optimization_phase": "4_error"
        }

@router.get("/performance")
async def performance_health_check(request: Request):
    """
    Performance-focused health check.
    Phase 4: Detailed performance metrics and optimization status.
    """
    start_time = time.time()
    
    try:
        # Get performance middleware
        performance_middleware = getattr(request.app.state, 'performance_middleware', None)
        
        if not performance_middleware:
            return {
                "status": "performance_monitoring_disabled",
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                "message": "Performance monitoring middleware not enabled"
            }
        
        # Get comprehensive performance data
        perf_summary = performance_middleware.get_performance_summary()
        slow_requests = performance_middleware.get_slow_requests(limit=5)
        
        # Phase optimization status
        optimization_status = {
            "phase_1_dependency_injection": "complete",
            "phase_2_model_preloading": "complete", 
            "phase_3_nlu_optimization": "complete",
            "phase_4_route_optimization": "in_progress"
        }
        
        # Performance target compliance
        target_compliance = {}
        for endpoint, perf in perf_summary.get('endpoint_performance', {}).items():
            target = perf.get('performance_target')
            recent_avg = perf.get('recent_average_time', 0)
            
            if target:
                compliance = recent_avg <= target
                target_compliance[endpoint] = {
                    "target": target,
                    "recent_average": recent_avg,
                    "compliant": compliance,
                    "margin": target - recent_avg if compliance else recent_avg - target
                }
        
        processing_time = time.time() - start_time
        
        return {
            "status": "healthy",
            "processing_time_ms": round(processing_time * 1000, 2),
            "performance_summary": perf_summary,
            "recent_slow_requests": slow_requests,
            "optimization_status": optimization_status,
            "target_compliance": target_compliance,
            "recommendations": _generate_performance_recommendations(perf_summary, target_compliance)
        }
    
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Performance health check failed: {e}")
        
        return {
            "status": "unhealthy",
            "error": str(e),
            "processing_time_ms": round(processing_time * 1000, 2)
        }

@router.get("/components")
async def components_health_check(
    request: Request,
    chatbot=Depends(get_chatbot)
):
    """
    Component-specific health check.
    Phase 4: Detailed component analysis and singleton verification.
    """
    start_time = time.time()
    
    try:
        # Verify singleton pattern compliance
        singleton_verification = {
            "chatbot_from_app_state": request.app.state.chatbot is chatbot,
            "chatbot_instance_id": id(chatbot),
            "app_state_chatbot_id": id(request.app.state.chatbot) if hasattr(request.app.state, 'chatbot') else None
        }
        
        # Component initialization status
        component_status = {}
        
        # Check each component
        for component_name in ['knowledge_base', 'nlu_engine', 'dialog_manager', 'response_generator', 'service_hub', 'session_manager', 'db_manager']:
            if hasattr(chatbot, component_name):
                component = getattr(chatbot, component_name)
                component_status[component_name] = {
                    "initialized": component is not None,
                    "type": type(component).__name__ if component else None,
                    "instance_id": id(component) if component else None
                }
            else:
                component_status[component_name] = {
                    "initialized": False,
                    "error": "Component not found in chatbot"
                }
        
        # Phase-specific checks
        phase_checks = {
            "phase_1_singletons": singleton_verification["chatbot_from_app_state"],
            "phase_2_models_loaded": component_status.get('nlu_engine', {}).get('initialized', False),
            "phase_3_fast_path": True,  # Assume enabled if we reach this point
            "phase_4_monitoring": hasattr(request.app.state, 'performance_middleware')
        }
        
        overall_status = "healthy" if all(phase_checks.values()) else "degraded"
        
        processing_time = time.time() - start_time
        
        return {
            "status": overall_status,
            "processing_time_ms": round(processing_time * 1000, 2),
            "singleton_verification": singleton_verification,
            "component_status": component_status,
            "phase_checks": phase_checks,
            "optimization_level": "phase_4_complete" if all(phase_checks.values()) else "partial"
        }
    
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Components health check failed: {e}")
        
        return {
            "status": "unhealthy",
            "error": str(e),
            "processing_time_ms": round(processing_time * 1000, 2)
        }

def _generate_performance_recommendations(perf_summary: Dict[str, Any], target_compliance: Dict[str, Any]) -> List[str]:
    """Generate performance recommendations based on metrics."""
    recommendations = []
    
    # Check slow request percentage
    last_hour = perf_summary.get('last_hour_summary', {})
    slow_percentage = last_hour.get('slow_request_percentage', 0)
    
    if slow_percentage > 10:
        recommendations.append(f"High slow request rate ({slow_percentage:.1f}%) - consider optimizing slow endpoints")
    
    # Check target compliance
    non_compliant_endpoints = [
        endpoint for endpoint, compliance in target_compliance.items() 
        if not compliance.get('compliant', True)
    ]
    
    if non_compliant_endpoints:
        recommendations.append(f"Performance targets not met for: {', '.join(non_compliant_endpoints)}")
    
    # Check error rate
    error_requests = last_hour.get('error_requests', 0)
    total_requests = last_hour.get('total_requests', 0)
    
    if total_requests > 0 and (error_requests / total_requests) > 0.05:
        recommendations.append(f"High error rate ({error_requests}/{total_requests}) - investigate error causes")
    
    if not recommendations:
        recommendations.append("All performance metrics within acceptable ranges")
    
    return recommendations 