from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union

# ============================================================================
# SEARCH REQUEST SCHEMAS
# ============================================================================

class SearchRequest(BaseModel):
    """Base search request schema"""
    query: Optional[str] = Field(None, max_length=500, description="Search query text")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Number of results to skip")
    language: str = Field("en", pattern=r'^(en|ar)$', description="Language code")

    @validator('query')
    def validate_query(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip() if v else v

class AttractionSearchRequest(SearchRequest):
    """Attraction search request schema"""
    name: Optional[str] = Field(None, max_length=200, description="Attraction name")
    city_id: Optional[str] = Field(None, pattern=r'^[a-zA-Z0-9_-]+$', description="City ID")
    type: Optional[str] = Field(None, max_length=50, description="Attraction type")

class HotelSearchRequest(SearchRequest):
    """Hotel search request schema"""
    name: Optional[str] = Field(None, max_length=200, description="Hotel name")
    city_id: Optional[str] = Field(None, pattern=r'^[a-zA-Z0-9_-]+$', description="City ID")
    stars: Optional[int] = Field(None, ge=1, le=5, description="Hotel star rating")

class RestaurantSearchRequest(SearchRequest):
    """Restaurant search request schema"""
    name: Optional[str] = Field(None, max_length=200, description="Restaurant name")
    city_id: Optional[str] = Field(None, pattern=r'^[a-zA-Z0-9_-]+$', description="City ID")
    cuisine: Optional[str] = Field(None, max_length=100, description="Cuisine type")

class PracticalInfoSearchRequest(SearchRequest):
    """Practical info search request schema"""
    category: Optional[str] = Field(None, max_length=100, description="Info category")
    keyword: Optional[str] = Field(None, max_length=100, description="Search keyword")

class FAQSearchRequest(SearchRequest):
    """FAQ search request schema"""
    category: Optional[str] = Field(None, max_length=100, description="FAQ category")
    keyword: Optional[str] = Field(None, max_length=100, description="Search keyword")

# ============================================================================
# ID-BASED REQUEST SCHEMAS
# ============================================================================

class AttractionByIdRequest(BaseModel):
    """Request schema for getting attraction by ID"""
    attraction_id: str = Field(..., pattern=r'^[a-zA-Z0-9_-]+$', description="Valid attraction ID")

class HotelByIdRequest(BaseModel):
    """Request schema for getting hotel by ID"""
    hotel_id: str = Field(..., pattern=r'^[a-zA-Z0-9_-]+$', description="Valid hotel ID")

class RestaurantByIdRequest(BaseModel):
    """Request schema for getting restaurant by ID"""
    restaurant_id: str = Field(..., pattern=r'^[a-zA-Z0-9_-]+$', description="Valid restaurant ID")

class CityByIdRequest(BaseModel):
    """Request schema for getting city by ID"""
    city_id: str = Field(..., pattern=r'^[a-zA-Z0-9_-]+$', description="Valid city ID")

# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class KnowledgeBaseResponse(BaseModel):
    """Base response schema for knowledge base endpoints"""
    success: bool = Field(..., description="Request success status")
    data: Union[Dict[str, Any], List[Dict[str, Any]]] = Field(..., description="Response data")
    message: Optional[str] = Field(None, description="Response message")
    total_count: Optional[int] = Field(None, description="Total available results")

class AttractionResponse(BaseModel):
    """Attraction response schema"""
    id: Union[str, int]
    name: Dict[str, str]
    description: Optional[Dict[str, str]] = None
    type: Optional[str] = None
    city_id: Optional[Union[str, int]] = None
    location: Optional[Dict[str, Any]] = None

class HotelResponse(BaseModel):
    """Hotel response schema"""
    id: Union[str, int]
    name: Dict[str, str]
    description: Optional[Dict[str, str]] = None
    stars: Optional[int] = None
    city_id: Optional[Union[str, int]] = None
    location: Optional[Dict[str, Any]] = None

class RestaurantResponse(BaseModel):
    """Restaurant response schema"""
    id: Union[str, int]
    name: Dict[str, str]
    description: Optional[Dict[str, str]] = None
    cuisine: Optional[str] = None
    city_id: Optional[Union[str, int]] = None
    location: Optional[Dict[str, Any]] = None

class PracticalInfoResponse(BaseModel):
    """Practical info response schema"""
    id: Union[str, int]
    title: Dict[str, str]
    content: Dict[str, str]
    category: Optional[str] = None

class FAQResponse(BaseModel):
    """FAQ response schema"""
    id: Union[str, int]
    question: Dict[str, str]
    answer: Dict[str, str]
    category: Optional[str] = None 