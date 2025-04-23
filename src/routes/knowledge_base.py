"""
Knowledge Base API Routes

This module provides API routes for accessing the tourism knowledge base.
"""
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from src.services.knowledge_base import KnowledgeBase
from src.utils.dependencies import get_optional_user
from src.models.user import User
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/knowledge",
    tags=["knowledge-base"],
)

def get_knowledge_base():
    """Dependency to get the KnowledgeBase service instance."""
    return KnowledgeBase()

def get_session_id(request: Request) -> str:
    """Extract session ID from cookies or generate a new one."""
    return request.cookies.get("session_id", "anonymous")

@router.get("/attractions/{attraction_id}")
async def get_attraction(
    attraction_id: str,
    request: Request,
    kb: KnowledgeBase = Depends(get_knowledge_base),
    user: Optional[User] = Depends(get_optional_user)
):
    """
    Get an attraction by its ID.
    """
    attraction = kb.get_attraction(attraction_id)
    
    if not attraction:
        raise HTTPException(status_code=404, detail="Attraction not found")
    
    # Log the view for analytics
    session_id = get_session_id(request)
    kb.log_view(
        "attraction", 
        attraction_id, 
        attraction.get("name"), 
        session_id, 
        user.id if user else None
    )
    
    return attraction

@router.get("/attractions")
async def search_attractions(
    request: Request,
    name: Optional[str] = None,
    city_id: Optional[str] = None,
    type: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    kb: KnowledgeBase = Depends(get_knowledge_base),
    user: Optional[User] = Depends(get_optional_user)
):
    """
    Search for attractions based on filters.
    """
    attractions = kb.search_attractions(name, city_id, type, limit, offset)
    
    # Log the search for analytics
    session_id = get_session_id(request)
    filters = {k: v for k, v in {"name": name, "city_id": city_id, "type": type}.items() if v is not None}
    kb.log_search(
        name or "all attractions", 
        len(attractions), 
        filters, 
        session_id, 
        user.id if user else None
    )
    
    return {"data": attractions, "total": len(attractions), "offset": offset, "limit": limit}

@router.get("/cities/{city_id}")
async def get_city(
    city_id: str,
    request: Request,
    kb: KnowledgeBase = Depends(get_knowledge_base),
    user: Optional[User] = Depends(get_optional_user)
):
    """
    Get a city by its ID.
    """
    city = kb.get_city(city_id)
    
    if not city:
        raise HTTPException(status_code=404, detail="City not found")
    
    # Log the view for analytics
    session_id = get_session_id(request)
    kb.log_view(
        "city", 
        city_id, 
        city.get("name"), 
        session_id, 
        user.id if user else None
    )
    
    return city

@router.get("/cities")
async def search_cities(
    request: Request,
    name: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    kb: KnowledgeBase = Depends(get_knowledge_base),
    user: Optional[User] = Depends(get_optional_user)
):
    """
    Search for cities based on filters.
    """
    cities = kb.search_cities(name, limit, offset)
    
    # Log the search for analytics
    session_id = get_session_id(request)
    filters = {k: v for k, v in {"name": name}.items() if v is not None}
    kb.log_search(
        name or "all cities", 
        len(cities), 
        filters, 
        session_id, 
        user.id if user else None
    )
    
    return {"data": cities, "total": len(cities), "offset": offset, "limit": limit}

@router.get("/hotels/{hotel_id}")
async def get_hotel(
    hotel_id: str,
    request: Request,
    kb: KnowledgeBase = Depends(get_knowledge_base),
    user: Optional[User] = Depends(get_optional_user)
):
    """
    Get a hotel by its ID.
    """
    hotel = kb.get_hotel(hotel_id)
    
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    
    # Log the view for analytics
    session_id = get_session_id(request)
    kb.log_view(
        "hotel", 
        hotel_id, 
        hotel.get("name"), 
        session_id, 
        user.id if user else None
    )
    
    return hotel

@router.get("/hotels")
async def search_hotels(
    request: Request,
    name: Optional[str] = None,
    city_id: Optional[str] = None,
    stars: Optional[int] = Query(None, ge=1, le=5),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    kb: KnowledgeBase = Depends(get_knowledge_base),
    user: Optional[User] = Depends(get_optional_user)
):
    """
    Search for hotels based on filters.
    """
    hotels = kb.search_hotels(name, city_id, stars, limit, offset)
    
    # Log the search for analytics
    session_id = get_session_id(request)
    filters = {k: v for k, v in {"name": name, "city_id": city_id, "stars": stars}.items() if v is not None}
    kb.log_search(
        name or "all hotels", 
        len(hotels), 
        filters, 
        session_id, 
        user.id if user else None
    )
    
    return {"data": hotels, "total": len(hotels), "offset": offset, "limit": limit}

@router.get("/restaurants/{restaurant_id}")
async def get_restaurant(
    restaurant_id: str,
    request: Request,
    kb: KnowledgeBase = Depends(get_knowledge_base),
    user: Optional[User] = Depends(get_optional_user)
):
    """
    Get a restaurant by its ID.
    """
    restaurant = kb.get_restaurant(restaurant_id)
    
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    # Log the view for analytics
    session_id = get_session_id(request)
    kb.log_view(
        "restaurant", 
        restaurant_id, 
        restaurant.get("name"), 
        session_id, 
        user.id if user else None
    )
    
    return restaurant

@router.get("/restaurants")
async def search_restaurants(
    request: Request,
    name: Optional[str] = None,
    city_id: Optional[str] = None,
    cuisine: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    kb: KnowledgeBase = Depends(get_knowledge_base),
    user: Optional[User] = Depends(get_optional_user)
):
    """
    Search for restaurants based on filters.
    """
    restaurants = kb.search_restaurants(name, city_id, cuisine, limit, offset)
    
    # Log the search for analytics
    session_id = get_session_id(request)
    filters = {k: v for k, v in {"name": name, "city_id": city_id, "cuisine": cuisine}.items() if v is not None}
    kb.log_search(
        name or "all restaurants", 
        len(restaurants), 
        filters, 
        session_id, 
        user.id if user else None
    )
    
    return {"data": restaurants, "total": len(restaurants), "offset": offset, "limit": limit}

@router.get("/practical-info/{info_id}")
async def get_practical_info(
    info_id: str,
    request: Request,
    kb: KnowledgeBase = Depends(get_knowledge_base),
    user: Optional[User] = Depends(get_optional_user)
):
    """
    Get practical information by its ID.
    """
    info = kb.get_practical_info(info_id)
    
    if not info:
        raise HTTPException(status_code=404, detail="Practical information not found")
    
    # Log the view for analytics
    session_id = get_session_id(request)
    kb.log_view(
        "practical_info", 
        info_id, 
        info.get("title"), 
        session_id, 
        user.id if user else None
    )
    
    return info

@router.get("/practical-info")
async def search_practical_info(
    request: Request,
    keyword: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    kb: KnowledgeBase = Depends(get_knowledge_base),
    user: Optional[User] = Depends(get_optional_user)
):
    """
    Search for practical information based on filters.
    """
    info_items = kb.search_practical_info(keyword, category, limit, offset)
    
    # Log the search for analytics
    session_id = get_session_id(request)
    filters = {k: v for k, v in {"keyword": keyword, "category": category}.items() if v is not None}
    kb.log_search(
        keyword or "all practical info", 
        len(info_items), 
        filters, 
        session_id, 
        user.id if user else None
    )
    
    return {"data": info_items, "total": len(info_items), "offset": offset, "limit": limit} 