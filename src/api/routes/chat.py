"""
Chat-related API endpoints for FastAPI.
MIGRATED TO PHASE 4 FACADE ARCHITECTURE
"""
import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Request, Depends, HTTPException, Body

import os

from ...models.api_models import ChatMessageRequest, ChatbotResponse, SuggestionsResponse
from ...utils.exceptions import ChatbotError

# Phase 4: Import the new ComponentFactory instead of legacy factory
from ...knowledge.factory import ComponentFactory
from ...chatbot import Chatbot
from ...utils.llm_config import toggle_llm_first, get_config

# Create router
router = APIRouter(tags=["Chatbot"])
logger = logging.getLogger(__name__)

# Define dependencies
def get_chatbot(request: Request):
    """
    Dependency to get the chatbot instance from app.state (PERFORMANCE OPTIMIZED).
    Uses singleton instance created during app startup instead of recreating components.
    """
    try:
        # Use singleton from app.state instead of recreating via factory
        if not hasattr(request.app.state, 'chatbot') or not request.app.state.chatbot:
            logger.error("Chatbot not found in app.state - check lifespan initialization")
            raise HTTPException(status_code=503, detail="Chatbot service unavailable")
        
        chatbot = request.app.state.chatbot
        logger.debug(f"✅ Chat using singleton: {type(chatbot).__name__}")
        return chatbot
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error accessing chatbot singleton: {str(e)}", exc_info=True)
        raise HTTPException(status_code=503, detail="Chatbot service unavailable")

# Conditional rate limiter based on environment


@router.post("/chat", response_model=ChatbotResponse, tags=["Chat"])
async def chat_endpoint(
    message_request: ChatMessageRequest,
    request: Request,
    chatbot: Chatbot = Depends(get_chatbot)
):
    """
    Process a chat message and return a response.
    PHASE 4: Now using facade architecture.

    Args:
        message_request: The chat message request containing the user message and session ID
        request: The FastAPI request object
        chatbot: The chatbot instance dependency

    Returns:
        ChatbotResponse: The chatbot response containing text and session information
    """
    try:
        # Log incoming message (excluding session token for privacy)
        log_data = {
            "message": message_request.message,
            "session_id": message_request.session_id[:10] + "..." if message_request.session_id else None,
            "language": message_request.language,
            "client_ip": request.client.host if request.client else None,
        }
        logger.info(f"Chat request: {log_data}")

        # Process message with chatbot
        response = await chatbot.process_message(
            user_message=message_request.message,
            session_id=message_request.session_id,
            language=message_request.language
        )

        logger.info(f"✅ Chat processed via Phase 4 facade architecture")
        # Return response
        return response

    except ChatbotError as e:
        # Handle known chatbot errors
        logger.error(f"Chatbot error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Error processing chat message: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred processing your message")

@router.get("/suggestions", response_model=SuggestionsResponse)
async def get_suggestions(
    request: Request,
    session_id: Optional[str] = None,
    language: str = "en",
    chatbot=Depends(get_chatbot)
):
    """
    Get suggested queries for the chatbot.
    PHASE 4: Now using facade architecture.
    """
    try:
        suggestions = chatbot.get_suggestions(session_id=session_id, language=language)
        logger.info(f"✅ Suggestions retrieved via Phase 4 facade architecture")
        return {"suggestions": suggestions}
    except Exception as e:
        logger.error(f"Error getting suggestions: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get suggestions")

@router.post("/toggle-llm-first", tags=["Config"])
async def toggle_llm_first_endpoint():
    """
    Toggle the LLM first setting.

    This endpoint toggles whether the LLM should respond first (True) or
    the database should be queried first (False).

    Returns:
        Dict containing the new setting value
    """
    try:
        # Toggle the setting
        new_value = toggle_llm_first()

        # Return the new value
        return {
            "use_llm_first": new_value,
            "message": f"LLM first setting toggled to: {new_value}"
        }
    except Exception as e:
        logger.error(f"Error toggling LLM first setting: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to toggle LLM first setting")

@router.get("/config", tags=["Config"])
async def get_llm_config():
    """
    Get the current LLM configuration.

    Returns:
        Dict containing the current configuration
    """
    try:
        # Get the current configuration
        config = get_config()

        # Return the configuration
        return {
            "config": config,
            "message": "Current LLM configuration"
        }
    except Exception as e:
        logger.error(f"Error getting LLM configuration: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get LLM configuration")

# Performance Optimized Health Check Endpoint
@router.get("/health")
async def chat_health_check(request: Request):
    """
    Health check endpoint using optimized singleton access.
    PERFORMANCE OPTIMIZED: Uses app.state instead of factory calls.
    """
    try:
        # Use singleton from app.state instead of expensive factory call
        if not hasattr(request.app.state, 'chatbot') or not request.app.state.chatbot:
            return {
                "status": "unhealthy",
                "error": "Chatbot singleton not available in app.state",
                "phase": "performance_optimized"
            }
        
        chatbot = request.app.state.chatbot
        
        return {
            "status": "healthy",
            "phase": "performance_optimized",
            "chat_components": {
                "chatbot": {
                    "type": type(chatbot).__name__,
                    "has_db_manager": hasattr(chatbot, 'db_manager'),
                    "has_knowledge_base": hasattr(chatbot, 'knowledge_base'),
                    "db_connected": chatbot.db_manager.is_connected() if hasattr(chatbot, 'db_manager') else False
                }
            },
            "optimization": "Using singleton from app.state (no factory calls)"
        }
    except Exception as e:
        logger.error(f"Chat health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")
