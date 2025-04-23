"""
Chat-related API endpoints for FastAPI.
"""
import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Request, Depends, HTTPException, Body
from fastapi_limiter.depends import RateLimiter
import os

from ...models.api_models import ChatMessageRequest, ChatbotResponse, SuggestionsResponse
from ...utils.exceptions import ChatbotError

# Import dependencies
from ...utils.factory import component_factory
from ...chatbot import Chatbot

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
def get_rate_limiter():
    """
    Get rate limiter dependency or skip based on environment.
    """
    # Skip rate limiting in test environment
    if os.getenv("TESTING") == "true" or os.getenv("USE_REDIS", "").lower() == "false":
        return []
    return [Depends(RateLimiter(times=10, seconds=60))]

@router.post("/chat", response_model=ChatbotResponse, 
             dependencies=get_rate_limiter(),
             tags=["Chat"])
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
