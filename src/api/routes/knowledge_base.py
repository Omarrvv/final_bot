"""
Knowledge Base API Routes

This module provides API routes for accessing the tourism knowledge base.
MIGRATED TO PHASE 4 FACADE ARCHITECTURE
"""
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request

# Phase 4: Using ComponentFactory instead of adapter
# REMOVED: from src.knowledge.factory import ComponentFactory  # Archived - using unified service provider
from src.core.container import container
from src.api.dependencies import get_optional_user
# FIXED: get_optional_user returns Dict, not User object
from src.utils.logger import get_logger

# Validation schemas for input validation
from ..schemas.knowledge_schemas import (
    AttractionSearchRequest, HotelSearchRequest, RestaurantSearchRequest,
    PracticalInfoSearchRequest, FAQSearchRequest, AttractionByIdRequest,
    HotelByIdRequest, RestaurantByIdRequest, CityByIdRequest
)
from ..schemas.common_schemas import PaginationRequest, SuccessResponse

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/knowledge",
    tags=["knowledge-base"],
)

def get_knowledge_base(request: Request):
    """Dependency to get the KnowledgeBase from app.state singleton (PERFORMANCE OPTIMIZED)."""
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
        logger.debug(f"✅ Knowledge Route using singleton: {type(knowledge_base).__name__}")
        return knowledge_base
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error accessing knowledge base singleton: {e}")
        raise HTTPException(status_code=503, detail="Knowledge base service unavailable")

def get_session_id(request: Request) -> str:
    """Extract session ID from cookies or generate a new one."""
    return request.cookies.get("session_id", "anonymous")

@router.get("/attractions/{attraction_id}")
async def get_attraction(
    attraction_id: str,
    request: Request,
    kb = Depends(get_knowledge_base),
    user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """
    Get an attraction by its ID.
    PHASE 4: Now using facade architecture.
    """
    try:
        attraction = kb.get_attraction_by_id(int(attraction_id))
        
        if not attraction:
            raise HTTPException(status_code=404, detail="Attraction not found")
        
        # Log the view for analytics
        session_id = get_session_id(request)
        kb.log_view(
            "attraction", 
            attraction_id, 
            attraction.get("name"), 
            session_id, 
            user.get("user_id") if user else None
        )
        
        logger.info(f"✅ Retrieved attraction {attraction_id} via {type(kb).__name__}")
        return attraction
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting attraction {attraction_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving attraction: {str(e)}")

@router.get("/attractions")
async def search_attractions(
    request: Request,
    name: Optional[str] = None,
    city_id: Optional[str] = None,
    type: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    kb = Depends(get_knowledge_base),
    user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """
    Search for attractions based on filters.
    PHASE 4: Now using facade architecture.
    """
    try:
        # Build filters for the new architecture
        filters = {}
        if city_id:
            filters['city_id'] = int(city_id) if city_id.isdigit() else city_id
        if type:
            filters['type'] = type
            
        attractions = kb.search_attractions(query=name or "", filters=filters, language="en", limit=limit)
        
        # Log the search for analytics
        session_id = get_session_id(request)
        search_filters = {k: v for k, v in {"name": name, "city_id": city_id, "type": type}.items() if v is not None}
        kb.log_search(
            name or "all attractions", 
            len(attractions), 
            search_filters, 
            session_id, 
            user.get("user_id") if user else None
        )
        
        logger.info(f"✅ Searched attractions '{name}' via {type(kb).__name__}, found {len(attractions)}")
        return {"data": attractions, "total": len(attractions), "offset": offset, "limit": limit}
    except Exception as e:
        logger.error(f"Error searching attractions: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching attractions: {str(e)}")

@router.get("/cities/{city_id}")
async def get_city(
    city_id: str,
    request: Request,
    kb = Depends(get_knowledge_base),
    user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """
    Get a city by its ID.
    PHASE 4: Now using facade architecture.
    """
    try:
        city = kb.lookup_location(city_id, "en")
        
        if not city:
            raise HTTPException(status_code=404, detail="City not found")
        
        # Log the view for analytics
        session_id = get_session_id(request)
        kb.log_view(
            "city", 
            city_id, 
            city.get("name"), 
            session_id, 
            user.get("user_id") if user else None
        )
        
        logger.info(f"✅ Retrieved city {city_id} via {type(kb).__name__}")
        return city
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting city {city_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving city: {str(e)}")

@router.get("/cities")
async def search_cities(
    request: Request,
    name: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    kb = Depends(get_knowledge_base),
    user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """
    Search for cities based on filters.
    PHASE 4: Now using facade architecture.
    """
    try:
        # Use singleton database manager from app.state instead of factory
        if not hasattr(request.app.state, 'chatbot') or not request.app.state.chatbot:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        db_manager = request.app.state.chatbot.db_manager
        cities = db_manager.search_cities({"name": name} if name else {}, limit, offset)
        
        # Log the search for analytics
        session_id = get_session_id(request)
        search_filters = {k: v for k, v in {"name": name}.items() if v is not None}
        kb.log_search(
            name or "all cities", 
            len(cities), 
            search_filters, 
            session_id, 
            user.get("user_id") if user else None
        )
        
        logger.info(f"✅ Searched cities '{name}' via {type(kb).__name__}, found {len(cities)}")
        return {"data": cities, "total": len(cities), "offset": offset, "limit": limit}
    except Exception as e:
        logger.error(f"Error searching cities: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching cities: {str(e)}")

@router.get("/hotels/{hotel_id}")
async def get_hotel(
    hotel_id: str,
    request: Request,
    kb = Depends(get_knowledge_base),
    user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """
    Get a hotel by its ID.
    PHASE 4: Now using facade architecture.
    """
    try:
        hotel = kb.get_hotel_by_id(hotel_id)
        
        if not hotel:
            raise HTTPException(status_code=404, detail="Hotel not found")
        
        # Log the view for analytics
        session_id = get_session_id(request)
        kb.log_view(
            "hotel", 
            hotel_id, 
            hotel.get("name"), 
            session_id, 
            user.get("user_id") if user else None
        )
        
        logger.info(f"✅ Retrieved hotel {hotel_id} via {type(kb).__name__}")
        return hotel
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting hotel {hotel_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving hotel: {str(e)}")

@router.get("/hotels")
async def search_hotels(
    request: Request,
    name: Optional[str] = None,
    city_id: Optional[str] = None,
    stars: Optional[int] = Query(None, ge=1, le=5),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    kb = Depends(get_knowledge_base),
    user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """
    Search for hotels based on filters.
    PHASE 4: Now using facade architecture.
    """
    try:
        # Build filters for the new architecture
        filters = {}
        if city_id:
            filters['city_id'] = city_id
        if stars:
            filters['stars'] = stars
            
        hotels = kb.search_hotels({"name": name} if name else filters, limit, "en")
        
        # Log the search for analytics
        session_id = get_session_id(request)
        search_filters = {k: v for k, v in {"name": name, "city_id": city_id, "stars": stars}.items() if v is not None}
        kb.log_search(
            name or "all hotels", 
            len(hotels), 
            search_filters, 
            session_id, 
            user.get("user_id") if user else None
        )
        
        logger.info(f"✅ Searched hotels '{name}' via {type(kb).__name__}, found {len(hotels)}")
        return {"data": hotels, "total": len(hotels), "offset": offset, "limit": limit}
    except Exception as e:
        logger.error(f"Error searching hotels: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching hotels: {str(e)}")

@router.get("/restaurants/{restaurant_id}")
async def get_restaurant(
    restaurant_id: str,
    request: Request,
    kb = Depends(get_knowledge_base),
    user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """
    Get a restaurant by its ID.
    PHASE 4: Now using facade architecture.
    """
    try:
        restaurant = kb.get_restaurant_by_id(restaurant_id)
        
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        
        # Log the view for analytics
        session_id = get_session_id(request)
        kb.log_view(
            "restaurant", 
            restaurant_id, 
            restaurant.get("name"), 
            session_id, 
            user.get("user_id") if user else None
        )
        
        logger.info(f"✅ Retrieved restaurant {restaurant_id} via {type(kb).__name__}")
        return restaurant
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting restaurant {restaurant_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving restaurant: {str(e)}")

@router.get("/restaurants")
async def search_restaurants(
    request: Request,
    name: Optional[str] = None,
    city_id: Optional[str] = None,
    cuisine: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    kb = Depends(get_knowledge_base),
    user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """
    Search for restaurants based on filters.
    PHASE 4: Now using facade architecture.
    """
    try:
        # Build filters for the new architecture
        filters = {}
        if city_id:
            filters['city_id'] = city_id
        if cuisine:
            filters['cuisine'] = cuisine
            
        restaurants = kb.search_restaurants({"name": name} if name else filters, limit, "en")
        
        # Log the search for analytics
        session_id = get_session_id(request)
        search_filters = {k: v for k, v in {"name": name, "city_id": city_id, "cuisine": cuisine}.items() if v is not None}
        kb.log_search(
            name or "all restaurants", 
            len(restaurants), 
            search_filters, 
            session_id, 
            user.get("user_id") if user else None
        )
        
        logger.info(f"✅ Searched restaurants '{name}' via {type(kb).__name__}, found {len(restaurants)}")
        return {"data": restaurants, "total": len(restaurants), "offset": offset, "limit": limit}
    except Exception as e:
        logger.error(f"Error searching restaurants: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching restaurants: {str(e)}")

@router.get("/practical-info")
async def search_practical_info(
    request: Request,
    category: Optional[str] = None,
    query: Optional[str] = None,
    keyword: Optional[str] = None,  # Keep for backward compatibility
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    kb = Depends(get_knowledge_base),
    user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """
    Search practical information based on filters.
    PHASE 4: Now using facade architecture.
    """
    try:
        # Use query parameter, fallback to keyword for backward compatibility
        search_term = query or keyword
        
        # Build filters
        filters = {}
        if category:
            filters['category'] = category
            
        # Build query for KnowledgeBase (different signature than DatabaseManagerService)
        query_dict = {}
        if search_term:
            query_dict["text"] = search_term
        if category:
            query_dict["category"] = category
        if not query_dict:
            query_dict = filters
            
        practical_info = kb.search_practical_info(query=query_dict, limit=limit, language="en")
        
        # Log the search for analytics
        session_id = get_session_id(request)
        search_filters = {k: v for k, v in {"category": category, "query": search_term}.items() if v is not None}
        kb.log_search(
            search_term or f"practical info - {category}", 
            len(practical_info), 
            search_filters, 
            session_id, 
            user.get("user_id") if user else None
        )
        
        logger.info(f"✅ Searched practical info '{search_term}' via {type(kb).__name__}, found {len(practical_info)}")
        return {"data": practical_info, "total": len(practical_info), "offset": offset, "limit": limit}
    except Exception as e:
        logger.error(f"Error searching practical info: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching practical info: {str(e)}")

@router.get("/faqs")
async def search_faqs(
    request: Request,
    category: Optional[str] = None,
    keyword: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    kb = Depends(get_knowledge_base),
    user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """
    Search FAQs based on filters.
    PHASE 4: Now using facade architecture.
    """
    try:
        # Build filters
        filters = {}
        if category:
            filters['category'] = category
            
        faqs = kb.search_faqs({"keyword": keyword} if keyword else filters, limit, "en")
        
        # Log the search for analytics
        session_id = get_session_id(request)
        search_filters = {k: v for k, v in {"category": category, "keyword": keyword}.items() if v is not None}
        kb.log_search(
            keyword or f"faqs - {category}", 
            len(faqs), 
            search_filters, 
            session_id, 
            user.get("user_id") if user else None
        )
        
        logger.info(f"✅ Searched FAQs '{keyword}' via {type(kb).__name__}, found {len(faqs)}")
        return {"data": faqs, "total": len(faqs), "offset": offset, "limit": limit}
    except Exception as e:
        logger.error(f"Error searching FAQs: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching FAQs: {str(e)}")

@router.get("/health")
async def knowledge_health_check(request: Request):
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
                "implementation": "Performance Optimized"
            }
        
        chatbot = request.app.state.chatbot
        kb = chatbot.knowledge_base if hasattr(chatbot, 'knowledge_base') else None
        db_manager = chatbot.db_manager if hasattr(chatbot, 'db_manager') else None
        
        # Test basic database connectivity
        is_connected = db_manager.is_connected() if db_manager else False
        
        logger.debug(f"✅ Knowledge health check using singleton: {type(kb).__name__}")
        
        return {
            "status": "healthy" if is_connected else "unhealthy",
            "knowledge_base_type": type(kb).__name__ if kb else "None",
            "database_connected": is_connected,
            "implementation": "Performance Optimized (Using app.state singleton)",
            "optimization": "No factory calls - using singleton from app.state"
        }
    except Exception as e:
        logger.error(f"Knowledge health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "implementation": "Performance Optimized"
        } 