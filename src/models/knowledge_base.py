"""
Pydantic models for the knowledge base entities including attractions, cities, hotels,
restaurants, and practical information.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class AttractionsType(str, Enum):
    """Types of attractions."""
    HISTORICAL = "historical"
    NATURAL = "natural"
    CULTURAL = "cultural"
    ACTIVITY = "activity"
    OTHER = "other"


class CuisineType(str, Enum):
    """Types of cuisine for restaurants."""
    EGYPTIAN = "egyptian"
    MEDITERRANEAN = "mediterranean"
    MIDDLE_EASTERN = "middle_eastern"
    INTERNATIONAL = "international"
    SEAFOOD = "seafood"
    VEGETARIAN = "vegetarian"
    OTHER = "other"


class PracticalInfoCategory(str, Enum):
    """Categories for practical information."""
    TRANSPORTATION = "transportation"
    CURRENCY = "currency"
    VISA = "visa"
    SAFETY = "safety"
    CUSTOMS = "customs"
    WEATHER = "weather"
    COMMUNICATION = "communication"
    HEALTH = "health"
    OTHER = "other"


class BaseKnowledgeItem(BaseModel):
    """Base model for all knowledge base items."""
    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Name of the item")
    description: str = Field(..., description="Detailed description")
    keywords: List[str] = Field(default_factory=list, description="Keywords for search")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    

class Attraction(BaseKnowledgeItem):
    """Model for attractions."""
    city_id: str = Field(..., description="ID of the city where the attraction is located")
    type: AttractionsType = Field(..., description="Type of attraction")
    location: Dict[str, float] = Field(..., description="Geographic coordinates (latitude, longitude)")
    images: List[str] = Field(default_factory=list, description="URLs to images")
    entrance_fee: Optional[float] = Field(None, description="Entrance fee if applicable")
    opening_hours: Optional[Dict[str, str]] = Field(None, description="Opening hours by day")
    accessibility: Optional[Dict[str, bool]] = Field(None, description="Accessibility features")
    tips: List[str] = Field(default_factory=list, description="Tips for visitors")


class City(BaseKnowledgeItem):
    """Model for cities."""
    region: str = Field(..., description="Region or governorate")
    population: Optional[int] = Field(None, description="Population estimate")
    location: Dict[str, float] = Field(..., description="Geographic coordinates (latitude, longitude)")
    images: List[str] = Field(default_factory=list, description="URLs to images")
    known_for: List[str] = Field(default_factory=list, description="What the city is known for")
    best_time_to_visit: Optional[str] = Field(None, description="Best season or months to visit")


class Hotel(BaseKnowledgeItem):
    """Model for hotels."""
    city_id: str = Field(..., description="ID of the city where the hotel is located")
    stars: int = Field(..., ge=1, le=5, description="Hotel rating (1-5 stars)")
    location: Dict[str, float] = Field(..., description="Geographic coordinates (latitude, longitude)")
    address: str = Field(..., description="Physical address")
    amenities: List[str] = Field(default_factory=list, description="Available amenities")
    price_range: Optional[str] = Field(None, description="Price range indicator")
    images: List[str] = Field(default_factory=list, description="URLs to images")
    contact: Optional[Dict[str, str]] = Field(None, description="Contact information")


class Restaurant(BaseKnowledgeItem):
    """Model for restaurants."""
    city_id: str = Field(..., description="ID of the city where the restaurant is located")
    cuisine: List[CuisineType] = Field(..., description="Types of cuisine offered")
    location: Dict[str, float] = Field(..., description="Geographic coordinates (latitude, longitude)")
    address: str = Field(..., description="Physical address")
    price_range: Optional[str] = Field(None, description="Price range indicator")
    menu_highlights: List[str] = Field(default_factory=list, description="Signature dishes")
    images: List[str] = Field(default_factory=list, description="URLs to images")
    opening_hours: Optional[Dict[str, str]] = Field(None, description="Opening hours by day")
    contact: Optional[Dict[str, str]] = Field(None, description="Contact information")


class PracticalInfo(BaseKnowledgeItem):
    """Model for practical information."""
    category: PracticalInfoCategory = Field(..., description="Category of information")
    applies_to: List[str] = Field(default_factory=list, description="Cities or regions this applies to")
    valid_from: Optional[datetime] = Field(None, description="Start of validity period")
    valid_to: Optional[datetime] = Field(None, description="End of validity period")
    links: List[Dict[str, str]] = Field(default_factory=list, description="Related external resources")


# Response models for API endpoints
class AttractionResponse(Attraction):
    """Response model for an attraction."""
    pass


class AttractionListResponse(BaseModel):
    """Response model for a list of attractions."""
    items: List[Attraction]
    total: int
    page: int
    page_size: int


class CityResponse(City):
    """Response model for a city."""
    pass


class CityListResponse(BaseModel):
    """Response model for a list of cities."""
    items: List[City]
    total: int
    page: int
    page_size: int


class HotelResponse(Hotel):
    """Response model for a hotel."""
    pass


class HotelListResponse(BaseModel):
    """Response model for a list of hotels."""
    items: List[Hotel]
    total: int
    page: int
    page_size: int


class RestaurantResponse(Restaurant):
    """Response model for a restaurant."""
    pass


class RestaurantListResponse(BaseModel):
    """Response model for a list of restaurants."""
    items: List[Restaurant]
    total: int
    page: int
    page_size: int


class PracticalInfoResponse(PracticalInfo):
    """Response model for practical information."""
    pass


class PracticalInfoListResponse(BaseModel):
    """Response model for a list of practical information."""
    items: List[PracticalInfo]
    total: int
    page: int
    page_size: int 