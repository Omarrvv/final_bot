"""
Direct database access routes for debugging and testing.
These routes are not part of the public API and are only for development and testing.

MIGRATED TO PHASE 4 FACADE ARCHITECTURE
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import List, Dict, Any, Optional
import logging

# Phase 4: Using ComponentFactory instead of direct imports
from src.knowledge.factory import ComponentFactory
from src.middleware.auth import User
from src.utils.auth import get_current_active_user as get_current_user

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/db",
    tags=["database"],
)

def get_db_manager(request: Request):
    """Get DatabaseManager from app.state singleton (PERFORMANCE OPTIMIZED)."""
    try:
        # Use singleton from app.state instead of expensive factory call
        if not hasattr(request.app.state, 'chatbot') or not request.app.state.chatbot:
            logger.error("Chatbot singleton not found in app.state")
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        chatbot = request.app.state.chatbot
        if not hasattr(chatbot, 'db_manager'):
            logger.error("Database manager not found in chatbot singleton")
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        db_manager = chatbot.db_manager
        
        # Test database connection
        if not db_manager.is_connected():
            logger.error("Database connection failed")
            raise HTTPException(status_code=503, detail="Database connection failed")
        
        logger.debug(f"✅ DB Route using singleton: {type(db_manager).__name__}")
        return db_manager
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error accessing database manager singleton: {e}")
        raise HTTPException(status_code=503, detail="Database service unavailable")

def get_knowledge_base(request: Request):
    """Get KnowledgeBase from app.state singleton (PERFORMANCE OPTIMIZED)."""
    try:
        # Use singleton from app.state instead of expensive factory call
        if not hasattr(request.app.state, 'chatbot') or not request.app.state.chatbot:
            logger.error("Chatbot singleton not found in app.state")
            raise HTTPException(status_code=503, detail="Knowledge base service unavailable")
        
        chatbot = request.app.state.chatbot
        if not hasattr(chatbot, 'knowledge_base'):
            logger.error("Knowledge base not found in chatbot singleton")
            raise HTTPException(status_code=503, detail="Knowledge base service unavailable")
        
        knowledge_base = chatbot.knowledge_base
        logger.debug(f"✅ KB Route using singleton: {type(knowledge_base).__name__}")
        return knowledge_base
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error accessing knowledge base singleton: {e}")
        raise HTTPException(status_code=503, detail="Knowledge base service unavailable")

@router.get("/restaurants", response_model=List[Dict[str, Any]])
async def get_restaurants(
    limit: int = Query(10, description="Maximum number of restaurants to return"),
    db_manager = Depends(get_db_manager),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Get restaurants from the database.
    For development and testing purposes only.
    PHASE 4: Now using facade architecture.
    """
    try:
        # Get the first {limit} restaurants
        restaurants = db_manager.get_all_restaurants(limit=limit)
        logger.info(f"✅ Retrieved {len(restaurants)} restaurants via {type(db_manager).__name__}")
        return restaurants
    except Exception as e:
        logger.error(f"Error getting restaurants: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting restaurants: {str(e)}")

@router.get("/restaurants/{restaurant_id}", response_model=Dict[str, Any])
async def get_restaurant_by_id(
    restaurant_id: str,
    db_manager = Depends(get_db_manager),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Get restaurant by ID from the database.
    For development and testing purposes only.
    PHASE 4: Now using facade architecture.
    """
    try:
        restaurant = db_manager.get_restaurant(restaurant_id)
        if not restaurant:
            raise HTTPException(status_code=404, detail=f"Restaurant with ID {restaurant_id} not found")
        logger.info(f"✅ Retrieved restaurant {restaurant_id} via {type(db_manager).__name__}")
        return restaurant
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error getting restaurant by ID {restaurant_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting restaurant: {str(e)}")

@router.get("/search/restaurants", response_model=List[Dict[str, Any]])
async def search_restaurants(
    query: str = Query("", description="Search query"),
    limit: int = Query(10, description="Maximum number of results"),
    db_manager = Depends(get_db_manager),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Search restaurants in the database.
    For development and testing purposes only.
    PHASE 4: Now using facade architecture.
    """
    try:
        search_query = {"name": query} if query else {}
        restaurants = db_manager.search_restaurants(search_query, limit=limit)
        logger.info(f"✅ Searched restaurants '{query}' via {type(db_manager).__name__}, found {len(restaurants)}")
        return restaurants
    except Exception as e:
        logger.error(f"Error searching restaurants: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching restaurants: {str(e)}")

@router.get("/hotels", response_model=List[Dict[str, Any]])
async def get_hotels(
    limit: int = Query(10, description="Maximum number of hotels to return"),
    db_manager = Depends(get_db_manager),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Get hotels from the database.
    For development and testing purposes only.
    PHASE 4: Now using facade architecture.
    """
    try:
        # Get the first {limit} hotels
        hotels = db_manager.get_all_accommodations(limit=limit)
        logger.info(f"✅ Retrieved {len(hotels)} hotels via {type(db_manager).__name__}")
        return hotels
    except Exception as e:
        logger.error(f"Error getting hotels: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting hotels: {str(e)}")

@router.get("/attractions", response_model=List[Dict[str, Any]])
async def get_attractions(
    limit: int = Query(10, description="Maximum number of attractions to return"),
    db_manager = Depends(get_db_manager),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Get attractions from the database.
    For development and testing purposes only.
    PHASE 4: Now using facade architecture.
    """
    try:
        # Get the first {limit} attractions
        attractions = db_manager.get_all_attractions(limit=limit)
        logger.info(f"✅ Retrieved {len(attractions)} attractions via {type(db_manager).__name__}")
        return attractions
    except Exception as e:
        logger.error(f"Error getting attractions: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting attractions: {str(e)}")

# Performance Optimized Health Check Endpoint
@router.get("/health")
async def db_health_check(request: Request):
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
            "database_manager": {
                "type": type(chatbot.db_manager).__name__ if hasattr(chatbot, 'db_manager') else "None",
                "connected": chatbot.db_manager.is_connected() if hasattr(chatbot, 'db_manager') else False
            },
            "knowledge_base": {
                "type": type(chatbot.knowledge_base).__name__ if hasattr(chatbot, 'knowledge_base') else "None"
            },
            "optimization": "Using singleton from app.state (no factory calls)"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")