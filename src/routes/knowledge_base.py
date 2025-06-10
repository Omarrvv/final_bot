"""
Knowledge Base API Routes

This module provides API routes for accessing the tourism knowledge base.
MIGRATED TO PHASE 4 FACADE ARCHITECTURE
"""
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request

# Phase 4: Using ComponentFactory instead of adapter
from src.knowledge.factory import ComponentFactory
from src.utils.dependencies import get_optional_user
from src.models.user import User
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/knowledge",
    tags=["knowledge-base"],
)

def get_knowledge_base():
    """Dependency to get the KnowledgeBase service instance via ComponentFactory."""
    try:
        # Phase 4: Use ComponentFactory to get the appropriate implementation
        stack = ComponentFactory.create_knowledge_base_stack()
        knowledge_base = stack['knowledge_base']
        
        logger.info(f"✅ Knowledge Route using: {type(knowledge_base).__name__}")
        return knowledge_base
    except Exception as e:
        logger.error(f"Error initializing KnowledgeBase: {e}")
        raise HTTPException(status_code=500, detail="Knowledge base initialization error")

def get_session_id(request: Request) -> str:
    """Extract session ID from cookies or generate a new one."""
    return request.cookies.get("session_id", "anonymous")

@router.get("/attractions/{attraction_id}")
async def get_attraction(
    attraction_id: str,
    request: Request,
    kb = Depends(get_knowledge_base),
    user: Optional[User] = Depends(get_optional_user)
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
            user.id if user else None
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
    user: Optional[User] = Depends(get_optional_user)
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
            
        attractions = kb.search_attractions(name or "", filters, "en", limit)
        
        # Log the search for analytics
        session_id = get_session_id(request)
        search_filters = {k: v for k, v in {"name": name, "city_id": city_id, "type": type}.items() if v is not None}
        kb.log_search(
            name or "all attractions", 
            len(attractions), 
            search_filters, 
            session_id, 
            user.id if user else None
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
    user: Optional[User] = Depends(get_optional_user)
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
            user.id if user else None
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
    user: Optional[User] = Depends(get_optional_user)
):
    """
    Search for cities based on filters.
    PHASE 4: Now using facade architecture.
    """
    try:
        # Use the legacy database access for cities (since KB doesn't have direct city search)
        db_manager = ComponentFactory.create_knowledge_base_stack()['db_manager']
        cities = db_manager.search_cities({"name": name} if name else {}, limit, offset)
        
        # Log the search for analytics
        session_id = get_session_id(request)
        search_filters = {k: v for k, v in {"name": name}.items() if v is not None}
        kb.log_search(
            name or "all cities", 
            len(cities), 
            search_filters, 
            session_id, 
            user.id if user else None
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
    user: Optional[User] = Depends(get_optional_user)
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
            user.id if user else None
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
    user: Optional[User] = Depends(get_optional_user)
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
            user.id if user else None
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
    user: Optional[User] = Depends(get_optional_user)
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
            user.id if user else None
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
    user: Optional[User] = Depends(get_optional_user)
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
            user.id if user else None
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
    keyword: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    kb = Depends(get_knowledge_base),
    user: Optional[User] = Depends(get_optional_user)
):
    """
    Search practical information based on filters.
    PHASE 4: Now using facade architecture.
    """
    try:
        # Build filters
        filters = {}
        if category:
            filters['category'] = category
            
        practical_info = kb.search_practical_info({"keyword": keyword} if keyword else filters, limit, "en")
        
        # Log the search for analytics
        session_id = get_session_id(request)
        search_filters = {k: v for k, v in {"category": category, "keyword": keyword}.items() if v is not None}
        kb.log_search(
            keyword or f"practical info - {category}", 
            len(practical_info), 
            search_filters, 
            session_id, 
            user.id if user else None
        )
        
        logger.info(f"✅ Searched practical info '{keyword}' via {type(kb).__name__}, found {len(practical_info)}")
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
    user: Optional[User] = Depends(get_optional_user)
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
            user.id if user else None
        )
        
        logger.info(f"✅ Searched FAQs '{keyword}' via {type(kb).__name__}, found {len(faqs)}")
        return {"data": faqs, "total": len(faqs), "offset": offset, "limit": limit}
    except Exception as e:
        logger.error(f"Error searching FAQs: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching FAQs: {str(e)}")

@router.get("/health")
async def knowledge_health_check():
    """
    Health check endpoint for the knowledge base service.
    PHASE 4: Now using facade architecture.
    """
    try:
        # Test if we can create a knowledge base instance
        stack = ComponentFactory.create_knowledge_base_stack()
        kb = stack['knowledge_base']
        db_manager = stack['db_manager']
        
        # Test basic database connectivity
        is_connected = db_manager.is_connected()
        
        # Get facade metrics if available
        metrics = {}
        if hasattr(kb, 'get_facade_metrics'):
            try:
                metrics = kb.get_facade_metrics()
            except:
                metrics = {"error": "Unable to get facade metrics"}
        
        logger.info(f"✅ Knowledge health check via {type(kb).__name__}")
        
        return {
            "status": "healthy" if is_connected else "unhealthy",
            "knowledge_base_type": type(kb).__name__,
            "database_connected": is_connected,
            "implementation": "Phase 4 (Production Ready - New Model Default)",
            "metrics": metrics
        }
    except Exception as e:
        logger.error(f"Knowledge health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "implementation": "Phase 4 (Production Ready - New Model Default)"
        } 