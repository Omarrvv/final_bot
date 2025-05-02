"""
Direct database access routes for debugging and testing.
These routes are not part of the public API and are only for development and testing.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import List, Dict, Any, Optional
import logging

from ..knowledge.database import DatabaseManager
from ..knowledge.knowledge_base import KnowledgeBase
from ..middleware.auth import User
from ..utils.auth import get_current_active_user as get_current_user

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/db",
    tags=["database"],
)

def get_db_manager():
    """Get DatabaseManager instance."""
    try:
        db_manager = DatabaseManager()
        # Test database connection
        db_manager.test_connection()
        return db_manager
    except Exception as e:
        logger.error(f"Error initializing DatabaseManager: {e}")
        raise HTTPException(status_code=500, detail="Database initialization error")

def get_knowledge_base(db_manager: DatabaseManager = Depends(get_db_manager)):
    """Get KnowledgeBase instance."""
    try:
        return KnowledgeBase(db_manager=db_manager)
    except Exception as e:
        logger.error(f"Error initializing KnowledgeBase: {e}")
        raise HTTPException(status_code=500, detail="Knowledge base initialization error")

@router.get("/restaurants", response_model=List[Dict[str, Any]])
async def get_restaurants(
    limit: int = Query(10, description="Maximum number of restaurants to return"),
    db_manager: DatabaseManager = Depends(get_db_manager),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Get restaurants from the database.
    For development and testing purposes only.
    """
    try:
        # Get the first {limit} restaurants
        restaurants = db_manager.get_all_restaurants(limit=limit)
        return restaurants
    except Exception as e:
        logger.error(f"Error getting restaurants: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting restaurants: {str(e)}")

@router.get("/restaurants/{restaurant_id}", response_model=Dict[str, Any])
async def get_restaurant_by_id(
    restaurant_id: str,
    db_manager: DatabaseManager = Depends(get_db_manager),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Get restaurant by ID from the database.
    For development and testing purposes only.
    """
    try:
        restaurant = db_manager.get_restaurant(restaurant_id)
        if not restaurant:
            raise HTTPException(status_code=404, detail=f"Restaurant with ID {restaurant_id} not found")
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
    db_manager: DatabaseManager = Depends(get_db_manager),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Search restaurants in the database.
    For development and testing purposes only.
    """
    try:
        search_query = {"name": query} if query else {}
        restaurants = db_manager.search_restaurants(search_query, limit=limit)
        return restaurants
    except Exception as e:
        logger.error(f"Error searching restaurants: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching restaurants: {str(e)}")

@router.get("/hotels", response_model=List[Dict[str, Any]])
async def get_hotels(
    limit: int = Query(10, description="Maximum number of hotels to return"),
    db_manager: DatabaseManager = Depends(get_db_manager),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Get hotels from the database.
    For development and testing purposes only.
    """
    try:
        # Get the first {limit} hotels
        hotels = db_manager.get_all_accommodations(limit=limit)
        return hotels
    except Exception as e:
        logger.error(f"Error getting hotels: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting hotels: {str(e)}")

@router.get("/attractions", response_model=List[Dict[str, Any]])
async def get_attractions(
    limit: int = Query(10, description="Maximum number of attractions to return"),
    db_manager: DatabaseManager = Depends(get_db_manager),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Get attractions from the database.
    For development and testing purposes only.
    """
    try:
        # Get the first {limit} attractions
        attractions = db_manager.get_all_attractions(limit=limit)
        return attractions
    except Exception as e:
        logger.error(f"Error getting attractions: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting attractions: {str(e)}")