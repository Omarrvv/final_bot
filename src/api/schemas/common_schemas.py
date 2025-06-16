from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union

# ============================================================================
# COMMON VALIDATION SCHEMAS
# ============================================================================

class PaginationRequest(BaseModel):
    """Common pagination request schema"""
    limit: int = Field(10, ge=1, le=100, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Number of results to skip")

class LanguageRequest(BaseModel):
    """Common language request schema"""
    language: str = Field("en", pattern=r'^(en|ar)$', description="Language code (en/ar)")

class IDRequest(BaseModel):
    """Common ID validation schema"""
    id: str = Field(..., pattern=r'^[a-zA-Z0-9_-]+$', description="Valid alphanumeric ID")

class QueryRequest(BaseModel):
    """Common query request schema"""
    query: Optional[str] = Field(None, max_length=500, description="Search query")
    
    @validator('query')
    def validate_query(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip() if v else v

# ============================================================================
# STANDARD RESPONSE SCHEMAS
# ============================================================================

class SuccessResponse(BaseModel):
    """Standard success response"""
    success: bool = Field(True, description="Operation success status")
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")

class ErrorResponse(BaseModel):
    """Standard error response"""
    success: bool = Field(False, description="Operation success status")
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")

class PaginatedResponse(BaseModel):
    """Standard paginated response"""
    success: bool = Field(True, description="Operation success status")
    data: List[Dict[str, Any]] = Field(..., description="Response data")
    pagination: Dict[str, int] = Field(..., description="Pagination info")
    total_count: int = Field(..., description="Total available results")

# ============================================================================
# DATABASE ROUTE SCHEMAS
# ============================================================================

class RestaurantSearchRequest(PaginationRequest):
    """Restaurant search request"""
    query: Optional[str] = Field("", description="Search query")

class HotelSearchRequest(PaginationRequest):
    """Hotel search request"""
    query: Optional[str] = Field("", description="Search query")

class AttractionSearchRequest(PaginationRequest):
    """Attraction search request"""
    query: Optional[str] = Field("", description="Search query")

class DatabaseHealthResponse(BaseModel):
    """Database health response"""
    status: str = Field(..., description="Database status")
    connected: bool = Field(..., description="Connection status")
    response_time_ms: float = Field(..., description="Response time in milliseconds")

# ============================================================================
# MISCELLANEOUS SCHEMAS
# ============================================================================

class LanguagesResponse(BaseModel):
    """Languages endpoint response"""
    languages: List[Dict[str, str]] = Field(..., description="Available languages")
    default: str = Field("en", description="Default language")

class ConfigResponse(BaseModel):
    """Configuration response"""
    llm_first: bool = Field(..., description="LLM first preference")
    other_settings: Optional[Dict[str, Any]] = Field(None, description="Additional settings")

class DebugResponse(BaseModel):
    """Debug information response"""
    debug_info: Dict[str, Any] = Field(..., description="Debug information")
    timestamp: str = Field(..., description="Debug timestamp")
    system_status: str = Field(..., description="System status") 