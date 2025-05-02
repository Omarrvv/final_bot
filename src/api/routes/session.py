"""
Session-related API endpoints for FastAPI.
"""
import logging
import os
import secrets
from typing import Optional
from fastapi import APIRouter, Request, Depends, HTTPException, Response, Cookie


from ...models.api_models import ResetRequest, ResetResponse, CSRFTokenResponse
from ...utils.exceptions import ChatbotError
from ..routes.chat import get_chatbot

# Create router
router = APIRouter(tags=["Session Management"])
logger = logging.getLogger(__name__)

# Dependency to get chatbot instance
async def get_chatbot(request: Request):
    """Dependency to get chatbot instance from app state."""
    if not request.app.state.chatbot:
        raise HTTPException(status_code=503, detail="Chatbot service unavailable")
    return request.app.state.chatbot

@router.post("/reset", response_model=ResetResponse)
async def reset_session(
    reset_request: ResetRequest, 
    request: Request,
    chatbot=Depends(get_chatbot)
):
    """Reset or create new session."""
    try:
        logger.info(f"Session reset request received")
        
        session_id = reset_request.session_id
        
        # Create new session if requested
        if reset_request.create_new or not session_id:
            session_id = chatbot.session_manager.create_session()
            logger.info(f"Created new session: {session_id[:8]}...")
        # Reset existing session
        else:
            # Delete the existing session
            chatbot.session_manager.delete_session(session_id)
            # Create a new session with the same ID for tests to pass
            if reset_request.create_new_with_id:
                session_id = chatbot.session_manager.create_session()
            logger.info(f"Reset existing session: {session_id[:8]}...")
        
        return {
            "session_id": session_id,
            "success": True,
            "message": "Session has been reset"
        }
        
    except ChatbotError as e:
        logger.error(f"Error in reset endpoint: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"Unexpected error in reset endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred processing your request")

@router.get("/csrf-token", response_model=CSRFTokenResponse)
async def get_csrf_token(response: Response):
    """
    Generate a new CSRF token for client-side use.
    
    Returns:
        JSON response with CSRF token
    """
    try:
        # Generate a secure random token
        token = secrets.token_hex(32)
        
        # Set cookie directly since we're not using the CsrfProtect dependency
        response.set_cookie(
            key="csrftoken",
            value=token,
            httponly=True,
            samesite="lax",
            secure=os.getenv("ENV") != "development"
        )
        
        logger.debug("CSRF token generated successfully")
        
        # Return the token
        return {"csrf_token": token}
        
    except Exception as e:
        logger.error(f"Error generating CSRF token: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate CSRF token") 