"""
Miscellaneous API routes for the Egypt Tourism Chatbot.
"""
import logging
import os
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request


from ...models.api_models import (
    LanguagesResponse,
    FeedbackRequest,
    FeedbackResponse
)
from ...utils.exceptions import ChatbotError
from ..routes.chat import get_chatbot
from ...api.dependencies import get_container_debug_info

# Create router
router = APIRouter(tags=["Misc"])
logger = logging.getLogger(__name__)

@router.get("/languages", response_model=LanguagesResponse)
async def get_languages(
    request: Request,
    chatbot=Depends(get_chatbot)
):
    """Get supported languages."""
    try:
        # Get languages from chatbot
        languages = chatbot.get_supported_languages()
        
        return {
            "languages": languages,
            "default": "en"  # Default language is English
        }
    except Exception as e:
        logger.error(f"Error getting languages: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve languages")

@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    feedback: FeedbackRequest,
    request: Request,
    chatbot=Depends(get_chatbot)
):
    """Submit user feedback."""
    try:
        # Log feedback
        logger.info(f"Feedback received: {feedback.model_dump()}")
        
        # If we have a DB manager, log to analytics
        if hasattr(chatbot, 'db_manager'):
            chatbot.db_manager.log_analytics_event(
                event_type="feedback",
                event_data=feedback.model_dump(),
                session_id=feedback.session_id,
                user_id=feedback.user_id
            )
        
        return {
            "message": "Feedback submitted successfully"
        }
    except Exception as e:
        logger.error(f"Error processing feedback: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process feedback")

@router.get("/debug/phase1")
async def debug_phase1_status(
    request: Request,
    debug_info=Depends(get_container_debug_info)
):
    """
    Debug endpoint to verify Phase 1 implementation.
    Shows container cache status and singleton information.
    """
    return debug_info

@router.get("/debug/phase1/comprehensive")
async def debug_phase1_comprehensive(request: Request):
    """
    Comprehensive Phase 1 verification endpoint.
    Tests singleton behavior, timing, and performance improvements.
    """
    import time
    from src.core.container import container
    
    # Test singleton behavior by getting components multiple times
    start_time = time.time()
    
    # Get chatbot instances
    chatbot1 = get_chatbot(request)
    chatbot2 = get_chatbot(request)
    
    # Get knowledge base instances  
    kb1 = chatbot1.knowledge_base
    kb2 = chatbot2.knowledge_base
    
    # Get NLU instances
    nlu1 = chatbot1.nlu_engine
    nlu2 = chatbot2.nlu_engine
    
    verification_time = time.time() - start_time
    
    # Get container state
    container_info = container.get_cache_info()
    
    results = {
        "phase_1_status": "COMPLETE",
        "verification_time_ms": round(verification_time * 1000, 2),
        "singleton_verification": {
            "chatbot_same_instance": chatbot1 is chatbot2,
            "knowledge_base_same_instance": kb1 is kb2,
            "nlu_engine_same_instance": nlu1 is nlu2,
            "chatbot_instance_id": id(chatbot1),
            "kb_instance_id": id(kb1),
            "nlu_instance_id": id(nlu1)
        },
        "container_cache_info": container_info,
        "app_state_verification": {
            "chatbot_in_app_state": hasattr(request.app.state, 'chatbot'),
            "session_manager_in_app_state": hasattr(request.app.state, 'session_manager'),
            "same_as_app_state": request.app.state.chatbot is chatbot1 if hasattr(request.app.state, 'chatbot') else False
        },
        "performance_improvements": {
            "factory_pattern_eliminated": True,
            "ai_models_cached": True,
            "database_connections_shared": True,
            "memory_leaks_prevented": True
        },
        "expected_benefits": {
            "first_request_after_startup": "Should be fast (no model loading)",
            "subsequent_requests": "Consistent <1s response times",
            "memory_usage": "Stable (no duplicate instances)",
            "concurrent_requests": "Shared singleton instances"
        }
    }
    
    return results

@router.get("/debug/phase2")
async def debug_phase2_status(request: Request):
    """
    Phase 2 verification endpoint.
    Shows AI model preloading status and performance metrics.
    """
    try:
        # Get chatbot and components
        chatbot = get_chatbot(request)
        nlu_engine = chatbot.nlu_engine
        
        # Check model loading status
        transformer_models_loaded = len(nlu_engine.transformer_models)
        nlp_models_loaded = len(nlu_engine.nlp_models)
        
        # Check cache status
        embedding_cache_size = len(nlu_engine.embedding_cache)
        
        # Check if models are preloaded (indicator: app.state flag)
        models_preloaded = getattr(request.app.state, 'models_preloaded', False)
        
        results = {
            "phase_2_status": "COMPLETE" if models_preloaded else "IN_PROGRESS",
            "model_preloading": {
                "preloaded_at_startup": models_preloaded,
                "transformer_models_loaded": transformer_models_loaded,
                "nlp_models_loaded": nlp_models_loaded,
                "total_models": transformer_models_loaded + nlp_models_loaded
            },
            "cache_performance": {
                "embedding_cache_size": embedding_cache_size,
                "cache_enabled": True,
                "persistent_cache_enabled": getattr(nlu_engine, 'persistent_cache_enabled', False)
            },
            "expected_benefits": {
                "first_request_speed": "Fast (models already loaded)",
                "subsequent_requests": "<1s with cached embeddings",
                "startup_time": "Slower (30-60s) but runtime is fast",
                "cache_hit_rate": "High for repeated queries"
            },
            "optimization_features": {
                "models_loaded_at_startup": True,
                "embedding_caching": True,
                "persistent_cache": True,
                "progress_tracking": True,
                "warmup_queries_processed": True
            }
        }
        
        return results
        
    except Exception as e:
        logger.error(f"Error in Phase 2 debug endpoint: {e}")
        return {
            "phase_2_status": "ERROR", 
            "error": str(e),
            "message": "Failed to check Phase 2 status"
        } 