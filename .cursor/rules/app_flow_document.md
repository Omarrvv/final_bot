# Application Flow Documentation

This document describes the data flow for user interactions in *both* the current active system and the intended target system.

## 1. Current Data Flow (Active: Root `app.py`)

This flow relies on the hardcoded KB and direct Anthropic calls.

```mermaid
sequenceDiagram
    participant User
    participant ReactFrontend as React FE (Browser)
    participant RootApp as root/app.py (Flask)
    participant FileSession as data/sessions/*.json
    participant HardcodedKB as EGYPT_TOURISM_KB (in app.py)
    participant AnthropicAPI as Anthropic Claude API

    User->>ReactFrontend: Enters message, clicks Send
    ReactFrontend->>RootApp: POST /api/chat (message, session_id?, lang)
    RootApp->>FileSession: Get/Create/Update Session Data (if session_id exists/new)
    RootApp->>RootApp: Calls generate_response(message)
    RootApp->>RootApp: Calls detect_topic(message)
    RootApp->>HardcodedKB: Check for keyword matches
    alt Simple Query / KB Match Found
        RootApp->>HardcodedKB: Retrieve predefined response
        RootApp-->>ReactFrontend: Returns KB response JSON
    else Complex Query / No Match
        RootApp->>RootApp: Calls create_egypt_tourism_prompt()
        RootApp->>AnthropicAPI: Calls messages.create(prompt)
        AnthropicAPI-->>RootApp: Returns generated text
        RootApp-->>ReactFrontend: Returns Anthropic response JSON
    end
    ReactFrontend->>User: Displays response text

Key points of Current Flow:
- All backend logic resides in app.py
- Knowledge primarily comes from EGYPT_TOURISM_KB dict or Anthropic
- SQLite DB is NOT queried for knowledge
- No complex NLU/Dialog state used
- Sessions stored as files

## 2. Target Data Flow (Intended: src/ Module via Consolidated app.py)

This describes the flow after the proposed refactoring and fixes are implemented.

```mermaid
sequenceDiagram
    participant User
    participant ReactFrontend as React FE (Browser)
    participant FlaskApp as Consolidated app.py (Flask Wrapper)
    participant DIContainer as src/ DI Container
    participant Chatbot as src/Chatbot
    participant SessionMgr as src/utils/SessionManager
    participant Redis as Redis (Sessions)
    participant NLUEngine as src/nlu/NLUEngine
    participant DialogMgr as src/dialog/DialogManager
    participant KnowledgeBase as src/knowledge/KnowledgeBase
    participant DBMgr as src/knowledge/DatabaseManager
    participant SQLiteDB as data/egypt_chatbot.db (KB/Analytics)
    participant RAGPipeline as src/knowledge/RAGPipeline
    participant VectorDB as src/knowledge/VectorDB (Local/Ext.)
    participant ServiceHub as src/integration/ServiceHub
    participant ExtService as External API (Weather/Translate/LLM)

    User->>ReactFrontend: Enters message, clicks Send
    ReactFrontend->>FlaskApp: POST /api/chat (message, session_id?, lang)
    FlaskApp->>DIContainer: Get Chatbot instance
    FlaskApp->>Chatbot: Calls process_message(message, session_id, lang)

    Chatbot->>SessionMgr: get_context(session_id)
    SessionMgr->>Redis: GET session:<session_id>
    Redis-->>SessionMgr: Returns context (or None)
    SessionMgr-->>Chatbot: Returns context (creates if new)

    Chatbot->>NLUEngine: process(text, context)
    NLUEngine->>KnowledgeBase: (Calls for entity resolution/lists)
    KnowledgeBase->>DBMgr: (Calls search_attractions etc.)
    DBMgr->>SQLiteDB: Executes SELECT query
    SQLiteDB-->>DBMgr: Returns data
    DBMgr-->>KnowledgeBase: Returns data
    KnowledgeBase-->>NLUEngine: Returns resolved entities/data
    NLUEngine-->>Chatbot: Returns NLU Result (Intent, Entities)

    Chatbot->>SessionMgr: update_context(session_id, nlu_result)
    SessionMgr->>Redis: SETEX session:<session_id> (updated context)

    Chatbot->>DialogMgr: next_action(nlu_result, context)
    DialogMgr-->>Chatbot: Returns Dialog Action (respond/prompt/service call)

    opt Dialog requires Service Call
        Chatbot->>ServiceHub: execute_service(service_name, method, params)
        ServiceHub->>ExtService: API Call (e.g., Weather API)
        ExtService-->>ServiceHub: API Response
        ServiceHub-->>Chatbot: Returns Service Result
        Chatbot->>SessionMgr: update_context(session_id, service_result)
        SessionMgr->>Redis: SETEX session:<session_id>
    end

    opt Dialog requires KB/RAG
        Chatbot->>KnowledgeBase: (Calls specific lookup/search)
        KnowledgeBase->>DBMgr: (Calls specific get/search)
        DBMgr->>SQLiteDB: Executes SELECT
        SQLiteDB-->>DBMgr: Data
        DBMgr-->>KnowledgeBase: Data
        KnowledgeBase-->>Chatbot: KB Data

        opt RAG needed
            Chatbot->>RAGPipeline: process(query, context)
            RAGPipeline->>VectorDB: search(query_embedding)
            VectorDB-->>RAGPipeline: Relevant Doc IDs
            RAGPipeline->>KnowledgeBase: Get content for IDs
            KnowledgeBase-->>RAGPipeline: Context Docs
            RAGPipeline->>ServiceHub: (Call LLM to synthesize)
            ServiceHub->>ExtService: (LLM API call)
            ExtService-->>ServiceHub: Synthesized Answer
            ServiceHub-->>RAGPipeline: Synthesized Answer
            RAGPipeline-->>Chatbot: RAG Result
        end
    end

    Chatbot->>ResponseGenerator: generate_response(dialog_action, nlu, context, kb/rag/service_data)
    ResponseGenerator-->>Chatbot: Final response text/suggestions

    Chatbot->>DBMgr: log_analytics_event(...)
    DBMgr->>SQLiteDB: INSERT into analytics table

    Chatbot-->>FlaskApp: Returns final JSON response
    FlaskApp-->>ReactFrontend: Sends response
    ReactFrontend->>User: Displays response

Key points of Target Flow:
- Consolidated app.py acts as a gateway
- Core logic is orchestrated by src/Chatbot using DI
- NLU/Dialog components are actively used
- KnowledgeBase accesses real data via DatabaseManager and SQLite
- RAG and Service calls are integrated into the flow
- Sessions are managed via Redis
- Analytics logged to SQLite (assuming refactor)