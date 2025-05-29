"""
Chat-related API endpoints for FastAPI.
"""
import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Request, Depends, HTTPException, Body

import os

from ...models.api_models import ChatMessageRequest, ChatbotResponse, SuggestionsResponse
from ...utils.exceptions import ChatbotError

# Import dependencies
from ...utils.factory import component_factory
from ...chatbot import Chatbot
from ...utils.llm_config import toggle_llm_first, get_config

# Create router
router = APIRouter(tags=["Chatbot"])
logger = logging.getLogger(__name__)

# Define dependencies
def get_chatbot():
    """
    Dependency to get the chatbot instance.
    """
    try:
        # Get chatbot from app state if available
        from starlette.concurrency import run_in_threadpool

        # Create a new chatbot if needed
        chatbot = component_factory.create_chatbot()

        if not chatbot:
            raise HTTPException(status_code=500, detail="Chatbot service not available")

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
    """Get suggested queries for the chatbot."""
    try:
        suggestions = chatbot.get_suggestions(session_id=session_id, language=language)
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
