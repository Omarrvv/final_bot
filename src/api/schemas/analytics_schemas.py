from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

# ============================================================================
# ANALYTICS REQUEST SCHEMAS
# ============================================================================

class AnalyticsRequest(BaseModel):
    """Base analytics request schema"""
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    
    @validator('start_date', 'end_date')
    def validate_date_format(cls, v):
        if v is not None:
            try:
                datetime.strptime(v, '%Y-%m-%d')
            except ValueError:
                raise ValueError('Date must be in YYYY-MM-DD format')
        return v

class DailyStatsRequest(BaseModel):
    """Daily statistics request schema"""
    days: int = Field(7, ge=1, le=90, description="Number of days to retrieve")

class SessionStatsRequest(BaseModel):
    """Session statistics request schema"""
    session_id: str = Field(..., pattern=r'^[a-zA-Z0-9_-]+$', description="Valid session ID")

class MessageStatsRequest(BaseModel):
    """Message statistics request schema"""
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of messages")
    offset: int = Field(0, ge=0, description="Number of messages to skip")

# ============================================================================
# ANALYTICS RESPONSE SCHEMAS
# ============================================================================

class OverviewStatsResponse(BaseModel):
    """Overview statistics response"""
    total_conversations: int = Field(..., description="Total number of conversations")
    total_messages: int = Field(..., description="Total number of messages")
    unique_users: int = Field(..., description="Number of unique users")
    avg_session_length: float = Field(..., description="Average session length in minutes")
    top_intents: List[Dict[str, Any]] = Field(..., description="Most common intents")
    response_time_avg: float = Field(..., description="Average response time in seconds")

class DailyStatsResponse(BaseModel):
    """Daily statistics response"""
    period: Dict[str, str] = Field(..., description="Time period")
    daily_stats: List[Dict[str, Any]] = Field(..., description="Daily statistics data")
    summary: Dict[str, Any] = Field(..., description="Period summary")

class SessionStatsResponse(BaseModel):
    """Session statistics response"""
    session_id: str = Field(..., description="Session ID")
    user_id: Optional[str] = Field(None, description="User ID")
    start_time: str = Field(..., description="Session start time")
    end_time: Optional[str] = Field(None, description="Session end time")
    message_count: int = Field(..., description="Number of messages in session")
    duration_minutes: Optional[float] = Field(None, description="Session duration in minutes")
    intents_used: List[str] = Field(..., description="Intents used in session")
    entities_extracted: Dict[str, List[str]] = Field(..., description="Entities extracted")

class IntentDistributionResponse(BaseModel):
    """Intent distribution response"""
    total_intents: int = Field(..., description="Total number of intent classifications")
    intent_distribution: Dict[str, int] = Field(..., description="Intent frequency distribution")
    top_intents: List[Dict[str, Any]] = Field(..., description="Most common intents with details")

class EntityDistributionResponse(BaseModel):
    """Entity distribution response"""
    total_entities: int = Field(..., description="Total number of entities extracted")
    entity_types: Dict[str, int] = Field(..., description="Entity type distribution")
    top_entities: List[Dict[str, Any]] = Field(..., description="Most common entities")

class FeedbackStatsResponse(BaseModel):
    """Feedback statistics response"""
    total_feedback: int = Field(..., description="Total feedback count")
    average_rating: float = Field(..., description="Average feedback rating")
    rating_distribution: Dict[str, int] = Field(..., description="Rating distribution")
    recent_feedback: List[Dict[str, Any]] = Field(..., description="Recent feedback entries")

class MessageStatsResponse(BaseModel):
    """Message statistics response"""
    total_messages: int = Field(..., description="Total number of messages")
    messages: List[Dict[str, Any]] = Field(..., description="Message data")
    pagination: Dict[str, int] = Field(..., description="Pagination information") 