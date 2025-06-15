# 🏗️ **REFACTORING PLAN 5: SERVICE LAYER ARCHITECTURE**

## **📋 Overview**

**Duration:** 2-3 days  
**Priority:** MEDIUM - Clean architecture  
**Dependencies:** Plans 1, 2, 3, 4 complete  
**Risk Level:** Medium (major architectural changes)

### **Strategic Objectives**

1. **Extract Service Layer** - Move business logic from controllers to dedicated services
2. **Break Up God Objects** - Split 2,183-line chatbot.py into focused components
3. **Separation of Concerns** - Clear boundaries between presentation, business, and data layers
4. **Domain-Driven Design** - Create focused services for each business domain

---

## **🎯 PHASE 5A: Service Layer Creation**

**Duration:** 6-8 hours  
**Risk:** Medium

### **Step 1.1: Create Core Service Interfaces** ⏱️ _2 hours_

```python
# src/services/interfaces.py (NEW)
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from src.models.api_models import *

class IChatService(ABC):
    """Interface for chat service"""

    @abstractmethod
    async def create_conversation(self, request: CreateConversationRequest) -> ConversationResponse:
        pass

    @abstractmethod
    async def send_message(self, conversation_id: str, message: MessageRequest) -> MessageResponse:
        pass

    @abstractmethod
    async def get_conversation(self, conversation_id: str) -> ConversationResponse:
        pass

class IKnowledgeService(ABC):
    """Interface for knowledge service"""

    @abstractmethod
    async def search_attractions(self, query: str, filters: Dict[str, Any]) -> SearchResponse:
        pass

    @abstractmethod
    async def get_attraction(self, attraction_id: int) -> AttractionResponse:
        pass

class IAnalyticsService(ABC):
    """Interface for analytics service"""

    @abstractmethod
    async def track_user_interaction(self, event: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    async def get_analytics_overview(self) -> Dict[str, Any]:
        pass
```

### **Step 1.2: Implement Chat Service** ⏱️ _3 hours_

```python
# src/services/chat_service.py (NEW)
from typing import Dict, Any, Optional
import logging
from datetime import datetime, timedelta
import uuid

from src.services.interfaces import IChatService
from src.models.api_models import *
from src.database.unified_db_service import UnifiedDatabaseService
from src.session.enhanced_session_manager import EnhancedSessionManager
from src.nlu.nlu_orchestrator import NLUOrchestrator

logger = logging.getLogger(__name__)

class ChatService(IChatService):
    """Service for chat and conversation management"""

    def __init__(self, db_service: UnifiedDatabaseService, session_manager: EnhancedSessionManager):
        self.db_service = db_service
        self.session_manager = session_manager
        self.nlu_orchestrator = NLUOrchestrator("configs/models.json")

    async def create_conversation(self, request: CreateConversationRequest) -> ConversationResponse:
        """Create new conversation with proper business logic"""
        try:
            # Business logic: Generate conversation ID
            conversation_id = str(uuid.uuid4())

            # Business logic: Create session
            session_data = {
                "conversation_id": conversation_id,
                "user_id": request.user_id,
                "language": request.language,
                "created_at": datetime.utcnow(),
                "status": "active"
            }

            session_id = self.session_manager.create_session(
                user_id=request.user_id,
                metadata=session_data
            )

            # Business logic: Handle initial message if provided
            message_count = 0
            if request.initial_message:
                await self._process_initial_message(conversation_id, request.initial_message, request.language)
                message_count = 1

            return ConversationResponse(
                id=conversation_id,
                user_id=request.user_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                language=request.language,
                message_count=message_count,
                status="active"
            )

        except Exception as e:
            logger.error(f"Failed to create conversation: {str(e)}")
            raise ServiceError(f"Failed to create conversation: {str(e)}")

    async def send_message(self, conversation_id: str, message: MessageRequest) -> MessageResponse:
        """Send message with full business logic"""
        try:
            # Business logic: Validate conversation exists
            conversation = await self.get_conversation(conversation_id)
            if not conversation:
                raise ValidationError("Conversation not found")

            # Business logic: Process message through NLU
            nlu_result = await self.nlu_orchestrator.process(message.content)

            # Business logic: Generate response based on intent
            response_content = await self._generate_response(nlu_result, message.language)

            # Business logic: Store message and response
            user_message = MessageResponse(
                id=str(uuid.uuid4()),
                role=MessageRole.USER,
                content=message.content,
                timestamp=datetime.utcnow(),
                language=message.language,
                metadata={"nlu_result": nlu_result}
            )

            assistant_message = MessageResponse(
                id=str(uuid.uuid4()),
                role=MessageRole.ASSISTANT,
                content=response_content,
                timestamp=datetime.utcnow(),
                language=message.language,
                metadata={"intent": nlu_result.get("intent")}
            )

            # Business logic: Update conversation
            await self._update_conversation_messages(conversation_id, [user_message, assistant_message])

            return assistant_message

        except Exception as e:
            logger.error(f"Failed to send message: {str(e)}")
            raise ServiceError(f"Failed to send message: {str(e)}")

    async def _generate_response(self, nlu_result: Dict[str, Any], language: str) -> str:
        """Business logic for response generation"""
        intent = nlu_result.get("intent", {}).get("name", "general_query")
        entities = nlu_result.get("entities", {})

        # Business logic: Route to appropriate response handler
        if intent == "attraction_query":
            return await self._handle_attraction_query(entities, language)
        elif intent == "restaurant_query":
            return await self._handle_restaurant_query(entities, language)
        elif intent == "greeting":
            return await self._handle_greeting(language)
        else:
            return await self._handle_general_query(nlu_result, language)

    # Additional business logic methods...
```

### **Step 1.3: Implement Knowledge Service** ⏱️ _2 hours_

```python
# src/services/knowledge_service.py (NEW)
from typing import Dict, Any, List, Optional
import logging

from src.services.interfaces import IKnowledgeService
from src.models.api_models import *
from src.database.unified_db_service import UnifiedDatabaseService

logger = logging.getLogger(__name__)

class KnowledgeService(IKnowledgeService):
    """Service for tourism knowledge base operations"""

    def __init__(self, db_service: UnifiedDatabaseService):
        self.db_service = db_service

    async def search_attractions(self, query: str, filters: Dict[str, Any]) -> SearchResponse:
        """Search attractions with business logic"""
        try:
            # Business logic: Build search query
            search_params = self._build_search_params(query, filters)

            # Business logic: Execute search
            with self.db_service.get_connection() as conn:
                cursor = conn.cursor()

                # Count total results
                count_query = "SELECT COUNT(*) FROM attractions WHERE ..."
                cursor.execute(count_query, search_params)
                total_count = cursor.fetchone()[0]

                # Get paginated results
                search_query = """
                    SELECT id, name, description, city_id, category, rating,
                           ST_X(geom) as lng, ST_Y(geom) as lat
                    FROM attractions
                    WHERE ...
                    ORDER BY rating DESC NULLS LAST
                    LIMIT %s OFFSET %s
                """
                cursor.execute(search_query, search_params + [filters.get('limit', 20), filters.get('offset', 0)])
                results = cursor.fetchall()

            # Business logic: Transform to response model
            attractions = []
            for row in results:
                attraction = AttractionResponse(
                    id=row['id'],
                    name=row['name'],  # Already JSONB format
                    description=row['description'],
                    city_id=row['city_id'],
                    category=row['category'],
                    rating=row['rating'],
                    location={"lat": row['lat'], "lng": row['lng']} if row['lat'] else None
                )
                attractions.append(attraction)

            return SearchResponse(
                results=attractions,
                total_count=total_count,
                page=filters.get('offset', 0) // filters.get('limit', 20) + 1,
                page_size=filters.get('limit', 20),
                has_more=(filters.get('offset', 0) + len(attractions)) < total_count
            )

        except Exception as e:
            logger.error(f"Failed to search attractions: {str(e)}")
            raise ServiceError(f"Search failed: {str(e)}")

    def _build_search_params(self, query: str, filters: Dict[str, Any]) -> List[Any]:
        """Business logic for building search parameters"""
        params = []

        # Text search
        if query:
            params.extend([f"%{query}%", f"%{query}%"])  # For name->>'en' and description->>'en'

        # Category filter
        if filters.get('category'):
            params.append(filters['category'])

        # City filter
        if filters.get('city_id'):
            params.append(filters['city_id'])

        return params
```

### **Step 1.4: Extract Business Logic from Controllers** ⏱️ _1-2 hours_

**Update API controllers to use services:**

```python
# src/api/v1/routes/conversations.py (UPDATE)
from src.services.chat_service import ChatService
from src.dependencies.providers import get_chat_service

# Before (business logic in controller):
@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(conversation_id: str, message_request: MessageRequest, chatbot = Depends(get_chatbot)):
    # Complex business logic mixed in controller
    nlu_result = await chatbot.process_nlu(message_request.content)
    response = await chatbot.generate_response(nlu_result)
    # ... more business logic

# After (clean controller with service):
@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    conversation_id: str,
    message_request: MessageRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """Send message to conversation"""
    return await chat_service.send_message(conversation_id, message_request)
```

---

## **⚡ PHASE 5B: Chatbot God Object Decomposition**

**Duration:** 6-8 hours  
**Risk:** High (major refactoring)

### **Step 2.1: Extract Core Components from Chatbot** ⏱️ _3 hours_

**Break up 2,183-line chatbot.py:**

```python
# src/core/message_processor.py (NEW)
class MessageProcessor:
    """Focused message processing logic"""

    def __init__(self, nlu_orchestrator, response_generator):
        self.nlu_orchestrator = nlu_orchestrator
        self.response_generator = response_generator

    async def process_message(self, text: str, language: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process message through pipeline"""
        # Step 1: NLU processing
        nlu_result = await self.nlu_orchestrator.process(text)

        # Step 2: Generate response
        response = await self.response_generator.generate(nlu_result, language, context)

        return {
            "nlu_result": nlu_result,
            "response": response
        }

# src/core/conversation_manager.py (NEW)
class ConversationManager:
    """Focused conversation management"""

    def __init__(self, session_manager, db_service):
        self.session_manager = session_manager
        self.db_service = db_service

    async def get_or_create_conversation(self, conversation_id: Optional[str], user_id: Optional[str]) -> Dict[str, Any]:
        """Get existing or create new conversation"""
        if conversation_id:
            conversation = await self._get_conversation(conversation_id)
            if conversation:
                return conversation

        # Create new conversation
        return await self._create_conversation(user_id)

# src/core/response_orchestrator.py (NEW)
class ResponseOrchestrator:
    """Focused response coordination"""

    def __init__(self, knowledge_service, analytics_service):
        self.knowledge_service = knowledge_service
        self.analytics_service = analytics_service

    async def orchestrate_response(self, intent: str, entities: Dict[str, Any], language: str) -> str:
        """Orchestrate response based on intent"""
        # Route to appropriate handler
        if intent == "attraction_query":
            return await self._handle_attraction_intent(entities, language)
        elif intent == "restaurant_query":
            return await self._handle_restaurant_intent(entities, language)
        # ... more handlers
```

### **Step 2.2: Create Simplified Chatbot Facade** ⏱️ _2 hours_

```python
# src/chatbot_facade.py (NEW - replaces 2,183-line chatbot.py)
from typing import Dict, Any, Optional
import logging

from src.core.message_processor import MessageProcessor
from src.core.conversation_manager import ConversationManager
from src.core.response_orchestrator import ResponseOrchestrator
from src.services.chat_service import ChatService

logger = logging.getLogger(__name__)

class ChatbotFacade:
    """Simplified chatbot facade - coordinates components"""

    def __init__(self, chat_service: ChatService):
        self.chat_service = chat_service
        # Components are created by chat_service internally

    async def process_message(self, user_message: str, session_id: Optional[str] = None, language: str = "en") -> Dict[str, Any]:
        """Main entry point - delegates to chat service"""
        try:
            # Simple delegation to service layer
            message_request = MessageRequest(content=user_message, language=language)

            if not session_id:
                # Create new conversation
                conversation_request = CreateConversationRequest(language=language, initial_message=user_message)
                conversation = await self.chat_service.create_conversation(conversation_request)
                return {
                    "session_id": conversation.id,
                    "text": "Conversation created",
                    "response_type": "conversation_created",
                    "language": language
                }
            else:
                # Send message to existing conversation
                response = await self.chat_service.send_message(session_id, message_request)
                return {
                    "session_id": session_id,
                    "text": response.content,
                    "response_type": "message_response",
                    "language": language
                }

        except Exception as e:
            logger.error(f"Chatbot processing failed: {str(e)}")
            return {
                "session_id": session_id,
                "text": "I apologize, but I'm having trouble processing your request right now.",
                "response_type": "error",
                "language": language
            }

# Legacy compatibility layer
class Chatbot(ChatbotFacade):
    """Legacy compatibility - same interface as old god object"""
    pass
```

### **Step 2.3: Update All References** ⏱️ _1-2 hours_

**Update imports throughout codebase:**

```python
# Before:
from src.chatbot import Chatbot  # 2,183-line god object

# After:
from src.chatbot_facade import Chatbot  # Simplified facade
```

### **Step 2.4: Archive Original Chatbot** ⏱️ _30 minutes_

```bash
# Archive the god object
mkdir -p archives/deprecated_chatbot/
mv src/chatbot.py archives/deprecated_chatbot/chatbot_god_object.py
```

---

## **🏛️ PHASE 5C: Domain Service Implementation**

**Duration:** 4-5 hours  
**Risk:** Low

### **Step 3.1: Create Domain-Specific Services** ⏱️ _3 hours_

```python
# src/services/tourism_service.py (NEW)
class TourismService:
    """Domain service for tourism-specific business logic"""

    def __init__(self, knowledge_service: IKnowledgeService):
        self.knowledge_service = knowledge_service

    async def get_recommendations(self, user_preferences: Dict[str, Any], location: str) -> List[AttractionResponse]:
        """Business logic for personalized recommendations"""
        # Domain logic: Weight preferences
        filters = self._build_recommendation_filters(user_preferences, location)

        # Use knowledge service
        search_result = await self.knowledge_service.search_attractions("", filters)

        # Domain logic: Rank results by user preferences
        ranked_results = self._rank_by_preferences(search_result.results, user_preferences)

        return ranked_results[:10]  # Top 10 recommendations

# src/services/language_service.py (NEW)
class LanguageService:
    """Domain service for multilingual support"""

    def __init__(self):
        self.supported_languages = ["en", "ar", "fr", "de", "es"]

    def get_localized_content(self, content: Dict[str, str], language: str) -> str:
        """Business logic for content localization"""
        if language in content:
            return content[language]
        elif "en" in content:
            return content["en"]  # Fallback to English
        else:
            return list(content.values())[0]  # Any available language

# src/services/analytics_service.py (NEW)
class AnalyticsService(IAnalyticsService):
    """Domain service for analytics and tracking"""

    def __init__(self, db_service: UnifiedDatabaseService):
        self.db_service = db_service

    async def track_user_interaction(self, event: Dict[str, Any]) -> bool:
        """Business logic for event tracking"""
        try:
            # Domain logic: Enrich event data
            enriched_event = self._enrich_event_data(event)

            # Store in database
            with self.db_service.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO analytics_events (event_type, event_data, timestamp) VALUES (%s, %s, %s)",
                    (enriched_event['type'], enriched_event['data'], enriched_event['timestamp'])
                )

            return True
        except Exception as e:
            logger.error(f"Failed to track event: {str(e)}")
            return False
```

### **Step 3.2: Implement Service Composition** ⏱️ _1-2 hours_

```python
# src/services/composite_service.py (NEW)
class CompositeService:
    """Composes multiple domain services for complex operations"""

    def __init__(self, tourism_service: TourismService, language_service: LanguageService, analytics_service: AnalyticsService):
        self.tourism_service = tourism_service
        self.language_service = language_service
        self.analytics_service = analytics_service

    async def get_personalized_recommendations(self, user_id: str, preferences: Dict[str, Any], language: str) -> List[Dict[str, Any]]:
        """Complex business operation using multiple services"""

        # Step 1: Get recommendations from tourism service
        recommendations = await self.tourism_service.get_recommendations(preferences, preferences.get('location'))

        # Step 2: Localize content using language service
        localized_recommendations = []
        for rec in recommendations:
            localized_rec = {
                "id": rec.id,
                "name": self.language_service.get_localized_content(rec.name, language),
                "description": self.language_service.get_localized_content(rec.description, language),
                "category": rec.category,
                "rating": rec.rating,
                "location": rec.location
            }
            localized_recommendations.append(localized_rec)

        # Step 3: Track analytics event
        await self.analytics_service.track_user_interaction({
            "type": "recommendation_request",
            "user_id": user_id,
            "preferences": preferences,
            "language": language,
            "result_count": len(localized_recommendations)
        })

        return localized_recommendations
```

---

## **🧪 PHASE 5D: Service Integration Testing**

**Duration:** 2-3 hours  
**Risk:** Low

### **Step 4.1: Service Layer Tests** ⏱️ _1.5 hours_

```python
# tests/test_service_layer.py (NEW)
import pytest
from unittest.mock import Mock, AsyncMock
from src.services.chat_service import ChatService
from src.services.knowledge_service import KnowledgeService
from src.models.api_models import *

class TestServiceLayer:

    @pytest.fixture
    def mock_db_service(self):
        return Mock()

    @pytest.fixture
    def mock_session_manager(self):
        return Mock()

    @pytest.fixture
    def chat_service(self, mock_db_service, mock_session_manager):
        return ChatService(mock_db_service, mock_session_manager)

    async def test_create_conversation(self, chat_service):
        """Test conversation creation business logic"""
        request = CreateConversationRequest(
            user_id="test_user",
            language="en",
            initial_message="Hello"
        )

        result = await chat_service.create_conversation(request)

        assert isinstance(result, ConversationResponse)
        assert result.user_id == "test_user"
        assert result.language == "en"
        assert result.status == "active"

    async def test_send_message_business_logic(self, chat_service):
        """Test message sending includes proper business logic"""
        # Mock conversation exists
        chat_service.get_conversation = AsyncMock(return_value=Mock())
        chat_service._generate_response = AsyncMock(return_value="Test response")
        chat_service._update_conversation_messages = AsyncMock()

        message = MessageRequest(content="What attractions are in Cairo?", language="en")
        result = await chat_service.send_message("conv_123", message)

        assert isinstance(result, MessageResponse)
        assert result.role == MessageRole.ASSISTANT
        assert result.content == "Test response"
        assert result.language == "en"

class TestKnowledgeService:

    async def test_search_attractions_business_logic(self):
        """Test attraction search includes proper business logic"""
        mock_db = Mock()
        knowledge_service = KnowledgeService(mock_db)

        # Mock database response
        mock_db.get_connection.return_value.__enter__.return_value.cursor.return_value.fetchall.return_value = [
            {
                'id': 1,
                'name': {'en': 'Great Pyramid', 'ar': 'الهرم الأكبر'},
                'description': {'en': 'Ancient pyramid', 'ar': 'هرم قديم'},
                'city_id': 1,
                'category': 'historical',
                'rating': 4.8,
                'lat': 29.9792,
                'lng': 31.1342
            }
        ]

        result = await knowledge_service.search_attractions("pyramid", {"limit": 10, "offset": 0})

        assert isinstance(result, SearchResponse)
        assert len(result.results) > 0
        assert result.results[0].name == {'en': 'Great Pyramid', 'ar': 'الهرم الأكبر'}
```

### **Step 4.2: Integration Tests** ⏱️ _1 hour_

```python
# tests/test_service_integration.py (NEW)
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

class TestServiceIntegration:

    def test_end_to_end_conversation_flow(self):
        """Test complete conversation flow through service layer"""

        # Step 1: Create conversation
        response = client.post("/api/v1/conversations", json={
            "user_id": "test_user",
            "language": "en",
            "initial_message": "Hello"
        })
        assert response.status_code == 201
        conversation = response.json()

        # Step 2: Send message
        response = client.post(f"/api/v1/conversations/{conversation['id']}/messages", json={
            "content": "What attractions are in Cairo?",
            "language": "en"
        })
        assert response.status_code == 200
        message = response.json()

        # Step 3: Verify business logic was applied
        assert message["role"] == "assistant"
        assert "content" in message
        assert message["language"] == "en"

    def test_knowledge_service_integration(self):
        """Test knowledge service integration"""
        response = client.get("/api/v1/knowledge/attractions", params={
            "query": "pyramid",
            "limit": 5
        })

        if response.status_code == 200:
            data = response.json()
            assert "results" in data
            assert "total_count" in data
            assert isinstance(data["results"], list)
```

---

## **📊 SUCCESS CRITERIA & VALIDATION**

### **✅ Phase Completion Checklist**

**Service Layer:**

- [ ] IChatService, IKnowledgeService interfaces created
- [ ] ChatService, KnowledgeService implemented with business logic
- [ ] All business logic moved from controllers to services
- [ ] Controllers are thin and focused on HTTP concerns only

**God Object Elimination:**

- [ ] 2,183-line chatbot.py replaced with focused components
- [ ] MessageProcessor, ConversationManager, ResponseOrchestrator created
- [ ] ChatbotFacade provides simple coordination
- [ ] All functionality preserved with cleaner architecture

**Domain Services:**

- [ ] TourismService, LanguageService, AnalyticsService created
- [ ] CompositeService handles complex cross-domain operations
- [ ] Domain-specific business logic properly encapsulated

**Architecture Quality:**

- [ ] Clear separation between presentation, business, and data layers
- [ ] Service interfaces enable testing and future flexibility
- [ ] No circular dependencies between layers
- [ ] All services unit testable in isolation

### **🎯 Key Performance Indicators**

| Metric                        | Before Plan 5 | After Plan 5      | Target       |
| ----------------------------- | ------------- | ----------------- | ------------ |
| God Object Size               | 2,183 lines   | <200 lines facade | <200 lines   |
| Business Logic in Controllers | High          | None              | 0%           |
| Service Layer Coverage        | 0%            | 100%              | 100%         |
| Testable Components           | Low           | High              | >90%         |
| Separation of Concerns        | Poor          | Excellent         | Clear layers |

### **🚨 Rollback Procedures**

**If Architecture Issues:**

1. **Service Layer Rollback:**

```bash
# Restore business logic to controllers if needed
# Keep service interfaces for future use
```

2. **Chatbot Rollback:**

```bash
# Restore original god object if critical issues
cp archives/deprecated_chatbot/chatbot_god_object.py src/chatbot.py
```

---

## **➡️ TRANSITION TO PLAN 6**

### **Prerequisites for Plan 6:**

- [ ] Service layer operational
- [ ] God objects eliminated
- [ ] Clean architecture implemented
- [ ] All Plan 5 tests passing

### **Plan 6 Enablements:**

- **Clean Architecture** - Ready for final integration and deployment
- **Testable Services** - Can validate integration thoroughly
- **Maintainable Code** - Safe to integrate with external systems

**Plan 5 provides the clean, maintainable architecture needed for final integration and deployment in Plan 6.**

---

**🎯 Expected Outcome:** Clean service layer architecture with proper separation of concerns, eliminated god objects, and maintainable business logic ready for production deployment.
