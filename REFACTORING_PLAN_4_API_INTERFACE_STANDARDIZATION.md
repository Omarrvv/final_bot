# 🌐 **REFACTORING PLAN 4: API & INTERFACE STANDARDIZATION**

## **📋 Overview**

**Duration:** 2-3 days  
**Priority:** HIGH - External integration readiness  
**Dependencies:** Plans 1, 2, 3 complete  
**Risk Level:** Medium (breaking changes to API)

### **Strategic Objectives**

1. **API Versioning** - Add `/api/v1/` to all endpoints for future-proof evolution
2. **Dependency Injection Standardization** - Consolidate 4 DI patterns to 1 unified approach
3. **Response Model Consistency** - Add Pydantic models to all endpoints
4. **RESTful API Design** - Fix non-RESTful patterns and URL structures

---

## **🎯 PHASE 4A: API Versioning Implementation**

**Duration:** 4-5 hours  
**Risk:** Medium (breaking changes)

### **Step 1.1: Create Versioned Router Structure** ⏱️ _2 hours_

```python
# src/api/v1/__init__.py (NEW)
from fastapi import APIRouter
from .routes import (
    conversations,
    knowledge,
    health,
    analytics,
    sessions
)

# V1 API Router
v1_router = APIRouter(prefix="/api/v1", tags=["v1"])

# Include all v1 routes
v1_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
v1_router.include_router(knowledge.router, prefix="/knowledge", tags=["knowledge"])
v1_router.include_router(health.router, prefix="/health", tags=["health"])
v1_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
v1_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
```

### **Step 1.2: Create RESTful Resource-Based Routes** ⏱️ _2-3 hours_

```python
# src/api/v1/routes/conversations.py (NEW)
from fastapi import APIRouter, Depends, HTTPException
from src.models.api_models import *
from src.services.chat_service import ChatService

router = APIRouter()

# RESTful conversation endpoints
@router.post("/", response_model=ConversationResponse)
async def create_conversation(
    request: CreateConversationRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """Create new conversation"""
    return await chat_service.create_conversation(request)

@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    chat_service: ChatService = Depends(get_chat_service)
):
    """Get conversation by ID"""
    return await chat_service.get_conversation(conversation_id)

@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    conversation_id: str,
    message_request: MessageRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """Send message to conversation"""
    return await chat_service.send_message(conversation_id, message_request)

@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: str,
    limit: int = 50,
    offset: int = 0,
    chat_service: ChatService = Depends(get_chat_service)
):
    """Get conversation messages"""
    return await chat_service.get_messages(conversation_id, limit, offset)
```

### **Step 1.3: Update Main Application** ⏱️ _30 minutes_

```python
# src/main.py (UPDATE)
from src.api.v1 import v1_router

# Replace individual router includes with versioned router
app.include_router(v1_router)

# Keep legacy routes temporarily for transition
# TODO: Remove after migration period
app.include_router(chat_router, prefix="/api", tags=["legacy"])
app.include_router(session_router, prefix="/api", tags=["legacy"])
```

---

## **🔧 PHASE 4B: Dependency Injection Standardization**

**Duration:** 4-5 hours  
**Risk:** Medium (affects all endpoints)

### **Step 2.1: Create Unified Dependency Provider** ⏱️ _2 hours_

```python
# src/dependencies/providers.py (NEW)
from fastapi import Depends, Request, HTTPException
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class ServiceProvider:
    """Unified dependency provider for all services"""

    @staticmethod
    def get_database_service():
        """Get database service instance"""
        from src.database.unified_db_service import UnifiedDatabaseService
        from src.config import settings
        return UnifiedDatabaseService(settings.database_url)

    @staticmethod
    def get_session_service():
        """Get session service instance"""
        from src.session.enhanced_session_manager import EnhancedSessionManager
        return EnhancedSessionManager()

    @staticmethod
    def get_chat_service():
        """Get chat service instance"""
        from src.services.chat_service import ChatService
        db_service = ServiceProvider.get_database_service()
        session_service = ServiceProvider.get_session_service()
        return ChatService(db_service, session_service)

    @staticmethod
    def get_knowledge_service():
        """Get knowledge service instance"""
        from src.services.knowledge_service import KnowledgeService
        db_service = ServiceProvider.get_database_service()
        return KnowledgeService(db_service)

# Standard dependency functions
def get_database_service():
    return ServiceProvider.get_database_service()

def get_session_service():
    return ServiceProvider.get_session_service()

def get_chat_service():
    return ServiceProvider.get_chat_service()

def get_knowledge_service():
    return ServiceProvider.get_knowledge_service()
```

### **Step 2.2: Replace All Dependency Patterns** ⏱️ _2-3 hours_

**Systematic replacement across all route files:**

```python
# Before (Pattern 1 - Custom functions):
def get_chatbot(request: Request):
    return request.app.state.chatbot

# Before (Pattern 2 - Direct access):
chatbot = request.app.state.chatbot

# Before (Pattern 3 - Container):
from src.utils.container import container
db_manager = container.get("database_manager")

# After (Standardized):
from src.dependencies.providers import get_chat_service
chat_service: ChatService = Depends(get_chat_service)
```

**Files to update:**

- All files in `src/api/v1/routes/`
- Legacy route files (for transition period)

---

## **📋 PHASE 4C: Response Model Standardization**

**Duration:** 3-4 hours  
**Risk:** Low (additive changes)

### **Step 3.1: Create Comprehensive Response Models** ⏱️ _2 hours_

```python
# src/models/api_models.py (EXPAND)
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

# Conversation Models
class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class MessageRequest(BaseModel):
    content: str = Field(..., description="Message content")
    language: Optional[str] = Field("en", description="Message language")

class MessageResponse(BaseModel):
    id: str
    role: MessageRole
    content: str
    timestamp: datetime
    language: str
    metadata: Optional[Dict[str, Any]] = None

class CreateConversationRequest(BaseModel):
    user_id: Optional[str] = None
    language: str = "en"
    initial_message: Optional[str] = None

class ConversationResponse(BaseModel):
    id: str
    user_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    language: str
    message_count: int
    status: str

# Knowledge Models
class AttractionResponse(BaseModel):
    id: int
    name: Dict[str, str]  # {"en": "Great Pyramid", "ar": "الهرم الأكبر"}
    description: Dict[str, str]
    city_id: int
    category: str
    rating: Optional[float] = None
    location: Optional[Dict[str, float]] = None  # {"lat": 29.9792, "lng": 31.1342}

class SearchResponse(BaseModel):
    results: List[Union[AttractionResponse]]
    total_count: int
    page: int
    page_size: int
    has_more: bool

# Health Models
class ComponentHealth(BaseModel):
    status: str  # "healthy", "degraded", "unhealthy"
    response_time_ms: float
    last_check: datetime
    details: Optional[Dict[str, Any]] = None

class HealthResponse(BaseModel):
    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: datetime
    uptime_seconds: float
    version: str
    components: Dict[str, ComponentHealth]
```

### **Step 3.2: Add Response Models to All Endpoints** ⏱️ _1-2 hours_

**Update route definitions:**

```python
# Before (no response model):
@router.get("/health")
async def health_check():
    return {"status": "ok"}

# After (with response model):
@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        uptime_seconds=get_uptime(),
        version="1.0.0",
        components=get_component_health()
    )
```

---

## **🛡️ PHASE 4D: Request Validation & Error Handling**

**Duration:** 2-3 hours  
**Risk:** Low

### **Step 4.1: Enhanced Request Validation** ⏱️ _1.5 hours_

```python
# src/models/validators.py (NEW)
from pydantic import validator, Field
from typing import Optional

class ValidatedMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000, description="Message content")
    language: Optional[str] = Field("en", regex="^(en|ar|fr|de|es)$", description="Supported language")

    @validator('content')
    def content_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Message content cannot be empty')
        return v.strip()

    @validator('language')
    def supported_language(cls, v):
        supported = ['en', 'ar', 'fr', 'de', 'es']
        if v not in supported:
            raise ValueError(f'Language must be one of: {supported}')
        return v

class ValidatedSearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=100)
    category: Optional[str] = Field(None, regex="^(attractions|restaurants|hotels)$")
    limit: int = Field(10, ge=1, le=100)
    offset: int = Field(0, ge=0)
```

### **Step 4.2: API Error Response Consistency** ⏱️ _1 hour_

```python
# src/api/v1/error_handlers.py (NEW)
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from src.models.error_models import StandardErrorResponse

async def validation_exception_handler(request, exc: ValidationError):
    """Handle Pydantic validation errors consistently"""
    error_details = []
    for error in exc.errors():
        error_details.append({
            "field": ".".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "code": error["type"]
        })

    return JSONResponse(
        status_code=422,
        content=StandardErrorResponse(
            error="validation_failed",
            message="Request validation failed",
            details=error_details,
            request_id=getattr(request.state, 'request_id', 'unknown'),
            timestamp=datetime.utcnow()
        ).dict()
    )
```

---

## **🧪 PHASE 4E: API Testing & Documentation**

**Duration:** 2-3 hours  
**Risk:** Low

### **Step 5.1: Comprehensive API Tests** ⏱️ _1.5 hours_

```python
# tests/test_api_v1.py (NEW)
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

class TestAPIv1:
    def test_api_versioning(self):
        """Test all endpoints have v1 prefix"""
        # Test new v1 endpoints work
        response = client.get("/api/v1/health")
        assert response.status_code in [200, 503]

        # Test legacy endpoints still work (during transition)
        response = client.get("/api/health")
        assert response.status_code in [200, 503]

    def test_conversation_endpoints(self):
        """Test RESTful conversation endpoints"""
        # Create conversation
        response = client.post("/api/v1/conversations", json={
            "language": "en",
            "initial_message": "Hello"
        })
        assert response.status_code == 201

        conversation = response.json()
        assert "id" in conversation

        # Send message
        response = client.post(f"/api/v1/conversations/{conversation['id']}/messages", json={
            "content": "What attractions are in Cairo?",
            "language": "en"
        })
        assert response.status_code == 200

    def test_response_model_consistency(self):
        """Test all endpoints return consistent response formats"""
        endpoints_to_test = [
            "/api/v1/health",
            "/api/v1/knowledge/attractions",
        ]

        for endpoint in endpoints_to_test:
            response = client.get(endpoint)
            if response.status_code == 200:
                data = response.json()
                # Test response has expected structure
                assert isinstance(data, dict)

    def test_validation_errors(self):
        """Test validation errors are properly formatted"""
        # Send invalid message request
        response = client.post("/api/v1/conversations/123/messages", json={
            "content": "",  # Invalid: empty content
            "language": "invalid"  # Invalid: unsupported language
        })

        assert response.status_code == 422
        error_data = response.json()
        assert "error" in error_data
        assert "details" in error_data
        assert error_data["error"] == "validation_failed"
```

### **Step 5.2: API Documentation Enhancement** ⏱️ _1 hour_

```python
# src/main.py (UPDATE OpenAPI configuration)
app = FastAPI(
    title="Egypt Tourism Chatbot API",
    description="Intelligent tourism assistant for Egypt with multilingual support",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    # Enhanced API documentation
    openapi_tags=[
        {
            "name": "conversations",
            "description": "Conversation management and messaging"
        },
        {
            "name": "knowledge",
            "description": "Tourism knowledge base access"
        },
        {
            "name": "health",
            "description": "System health and monitoring"
        }
    ]
)

# Add API versioning info to OpenAPI
@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": "Egypt Tourism Chatbot API",
        "version": "1.0.0",
        "docs": "/docs",
        "api_v1": "/api/v1"
    }
```

---

## **📊 SUCCESS CRITERIA & VALIDATION**

### **✅ Phase Completion Checklist**

**API Versioning:**

- [ ] All endpoints accessible via `/api/v1/` prefix
- [ ] RESTful resource-based URL structure implemented
- [ ] Legacy endpoints maintained for transition period
- [ ] OpenAPI documentation reflects v1 structure

**Dependency Injection:**

- [ ] Single ServiceProvider handles all dependencies
- [ ] All 4 old DI patterns replaced with standardized approach
- [ ] Clean dependency injection throughout API layer
- [ ] Service instances properly managed

**Response Models:**

- [ ] Pydantic response models for all v1 endpoints
- [ ] Consistent response structure across API
- [ ] Proper validation for all request models
- [ ] Standardized error response format

**Documentation:**

- [ ] OpenAPI schema complete and accurate
- [ ] Interactive docs (/docs) functional
- [ ] API examples and descriptions comprehensive

### **🎯 Key Performance Indicators**

| Metric              | Before Plan 4 | After Plan 4  | Target   |
| ------------------- | ------------- | ------------- | -------- |
| Versioned Endpoints | 0%            | 100%          | 100%     |
| DI Patterns         | 4 different   | 1 standard    | 1        |
| Response Models     | ~58% coverage | 100% coverage | 100%     |
| RESTful Compliance  | ~85%          | 100%          | 100%     |
| API Documentation   | Basic         | Comprehensive | Complete |

### **🚨 Rollback Procedures**

**If API Issues:**

1. **Versioning Rollback:**

```bash
# Route traffic back to legacy endpoints
# Keep v1 endpoints disabled until fixed
```

2. **Dependency Injection Rollback:**

```bash
# Restore original dependency patterns if needed
# Fall back to working DI approach
```

---

## **➡️ TRANSITION TO PLAN 5**

### **Prerequisites for Plan 5:**

- [ ] API v1 fully functional
- [ ] All endpoints have response models
- [ ] Dependency injection standardized
- [ ] API documentation complete

### **Plan 5 Enablements:**

- **Clean API Interface** - Service layer can focus on business logic
- **Standardized Dependencies** - Safe to extract service layer
- **Versioned API** - Breaking changes to internal architecture won't affect external API

**Plan 4 provides the stable, well-documented API foundation needed for service layer extraction in Plan 5.**

---

**🎯 Expected Outcome:** Professional, versioned API with consistent interfaces, comprehensive documentation, and standardized dependency injection ready for integration.
