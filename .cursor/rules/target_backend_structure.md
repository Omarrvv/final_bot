# Target Backend Architecture

This document describes the intended, consolidated backend architecture for the Egypt Tourism Chatbot, primarily utilizing the components within the `src/` directory.

## 1. Overview

The target architecture is a modular Flask application managed via Dependency Injection. A thin Flask wrapper (`app.py`) handles HTTP requests and delegates processing to a core `Chatbot` orchestrator, which leverages specialized components for NLU, Dialog Management, Knowledge Base access (via a DB Manager), RAG, and external Service integrations.

## 2. Architecture Diagram

```mermaid
flowchart TD
    A[React Frontend] --> B[Flask App\napp.py]
    B --> C[DI Container]
    C --> D[Chatbot Orchestrator]
    D --> E[NLU Engine]
    D --> F[Dialog Manager]
    D --> G[Knowledge Base]
    G --> H[Database Manager]
    H --> I[SQLite KB]
    D --> J[RAG Pipeline]
    J --> K[Vector DB]
    D --> L[Service Hub]
    L --> M[Anthropic LLM]
    L --> N[Weather Service]
    L --> O[Translation]
    D --> P[Session Manager]
    P --> Q[Redis]

## 3. Core Components (src/ directory)

Entry Point (app.py root, refactored): Initializes Flask, Factory/DI, serves API endpoints, delegates to Chatbot.
DI/Factory (src/utils/): Manages component creation and injection.
Chatbot (src/chatbot.py): Central request handler, orchestrates NLU->Dialog->KB/RAG/Service->Response flow.
NLU Engine (src/nlu/): Processes text for language, intent, entities. Uses SpaCy, Transformers, Regex, Fuzzy Matching, KB for resolution.
Dialog Manager (src/dialog/): Controls conversation state using configs/dialog_flows.json.
KnowledgeBase (src/knowledge/knowledge_base.py): FIXED - Acts as an interface to KB data, calling DatabaseManager for actual data operations.
DatabaseManager (src/knowledge/database.py): Handles all SQLite interactions for KB data, users, sessions (if migrated), and analytics (assuming migration).
RAG Pipeline (src/knowledge/rag_pipeline.py): Uses KB, VectorDB, and LLM (via ServiceHub) to enhance responses.
VectorDB (src/knowledge/vector_db.py): Manages vector embeddings (local file storage initially).
ResponseGenerator (src/response/): Builds responses from templates and retrieved data.
ServiceHub / Plugins (src/integration/): Manages connections and calls to external APIs (Anthropic, Weather, Translation).
Session Management (src/utils/session.py): Interfaces with Redis for session storage.
4. Database Strategy

Primary: SQLite (data/egypt_chatbot.db) for structured KB data (attractions, hotels, restaurants), users, and refactored analytics.
Sessions: Redis (configured via .env and docker-compose.yml).
Vector Embeddings: Local file storage initially (data/vector_db/), recommend external for scaling.