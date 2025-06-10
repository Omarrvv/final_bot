"""
Pydantic models for API request and response validation.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any, Union

class ChatMessageRequest(BaseModel):
    """Model for the request body of the /api/chat endpoint."""
    message: str = Field(..., description="The user's message text.")
    session_id: Optional[str] = Field(None, description="Optional existing session ID.")
    language: Optional[str] = Field('en', description="Language code for the request (e.g., 'en', 'ar').")
    # Add other fields if the frontend might send them, e.g., user_id
    user_id: Optional[int] = Field(None, description="Optional user ID (integer).")

class Suggestion(BaseModel):
    """Model for a suggested action."""
    text: Union[str, Dict[str, Any]] = Field(..., description="Suggestion text")  # Can be string or structured response
    action: Optional[str] = Field(None, description="Optional action type")  # Make action optional
    
    @classmethod
    def from_string(cls, text: str):
        """Create a Suggestion from a simple string."""
        return cls(text=text, action="suggestion")

class ChatbotResponse(BaseModel):
    """Model for the response body of the /api/chat endpoint."""
    session_id: str = Field(..., description="The session ID for the conversation.")
    text: Union[str, Dict[str, Any]] = Field(..., description="The chatbot's response text.")  # Can be string or structured response
    response_type: str = Field(..., description="Type of response (e.g., 'greeting', 'attraction_info', 'fallback').")
    language: str = Field(..., description="Language code of the response.")
    suggestions: Optional[List[Union[Suggestion, str]]] = Field(None, description="Optional list of suggested follow-up actions.")
    # Include other potential fields based on Chatbot.process_message output
    debug_info: Optional[Dict[str, Any]] = Field(None, description="Optional debugging information.")
    
    @field_validator('suggestions', mode='before')
    @classmethod
    def convert_suggestion_strings(cls, v):
        """Convert string suggestions to Suggestion objects."""
        if v is None:
            return v
        result = []
        for item in v:
            if isinstance(item, str):
                result.append(Suggestion.from_string(item))
            elif isinstance(item, dict):
                result.append(Suggestion(**item))
            else:
                result.append(item)
        return result
    # Example: Add fields if the chatbot returns structured data like lists of items
    # items: Optional[List[Dict[str, Any]]] = None

# Add other models as needed for different endpoints later
# (e.g., SuggestionsResponse, ResetResponse, FeedbackRequest, etc.)

# --- Models for other endpoints ---

class SuggestionsResponse(BaseModel):
    suggestions: List[Dict[str, Any]]

class ResetResponse(BaseModel):
    message: str
    session_id: str

class ResetRequest(BaseModel):
    session_id: Optional[str] = None
    create_new: Optional[bool] = False
    create_new_with_id: Optional[bool] = False

class Language(BaseModel):
    code: str
    name: str
    flag: Optional[str] = None
    direction: Optional[str] = "ltr"

class LanguagesResponse(BaseModel):
    languages: List[Dict[str, str]]
    default: str = "en"

class FeedbackRequest(BaseModel):
    message_id: str
    rating: int # Or float, or specific values
    comment: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[int] = None

class FeedbackResponse(BaseModel):
    """Response model for the feedback endpoint."""
    message: str

class CSRFTokenResponse(BaseModel):
    """Response model for the CSRF token endpoint."""
    csrf_token: str
