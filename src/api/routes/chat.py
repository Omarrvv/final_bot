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
def get_chatbot():
    """
    Dependency to get the chatbot instance.
    PHASE 4: Now using ComponentFactory for facade architecture.
    """
    try:
        # Phase 4: Use new ComponentFactory to create chatbot with facades
        stack = ComponentFactory.create_knowledge_base_stack()
        db_manager = stack['db_manager']
        knowledge_base = stack['knowledge_base']
        
        # Create the chatbot using the new factory pattern
        from ...utils.factory import component_factory
        
        # Initialize the factory if not already done
        if not hasattr(component_factory, '_initialized'):
            component_factory.initialize()
            component_factory._initialized = True
        
        # Override the factory components with facade implementations
        component_factory.register_component("database_manager", db_manager)
        component_factory.register_component("knowledge_base", knowledge_base)
        
        # Create chatbot
        chatbot = component_factory.create_chatbot()

        if not chatbot:
            raise HTTPException(status_code=500, detail="Chatbot service not available")

        logger.info(f"✅ Chat using: DB={type(db_manager).__name__}, KB={type(knowledge_base).__name__}")
        return chatbot
    except Exception as e:
        logger.error(f"Error getting chatbot: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Chatbot service not available")

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

# Phase 4 Health Check Endpoint
@router.get("/health")
async def chat_health_check():
    """
    Health check endpoint to verify chat facade architecture is working.
    PHASE 4: New endpoint for monitoring facade health.
    """
    try:
        stack = ComponentFactory.create_knowledge_base_stack()
        db_manager = stack['db_manager']
        knowledge_base = stack['knowledge_base']
        
        return {
            "status": "healthy",
            "phase": "4_incremental_migration",
            "chat_components": {
                "database_manager": {
                    "type": type(db_manager).__name__,
                    "connected": db_manager.is_connected(),
                    "facade_enabled": hasattr(db_manager, 'get_facade_metrics')
                },
                "knowledge_base": {
                    "type": type(knowledge_base).__name__,
                    "facade_enabled": hasattr(knowledge_base, 'get_facade_metrics')
                }
            },
            "implementation_info": stack['implementation_info']
        }
    except Exception as e:
        logger.error(f"Chat health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")
