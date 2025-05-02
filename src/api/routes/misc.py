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