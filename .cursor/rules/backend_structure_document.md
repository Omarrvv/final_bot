# Backend Structure Documentation (Current State)

This document outlines the **current state** of the project's backend architecture(s), based on analysis of file structure and the running application logs.

## 1. Overview: Dual Architectures

The project currently contains two distinct backend implementations:

**1.1. Path A: Root `app.py` (Active Implementation)**

*   **Location:** `app.py` file at the project root.
*   **Framework:** Flask.
*   **Entry Point:** Directly executed by `start_chatbot.sh` (`python app.py`) and `Dockerfile` (`gunicorn app:app`).
*   **Key Characteristics:**
    *   Self-contained Flask application logic.
    *   Defines API endpoints directly (`/api/chat`, `/api/health`, `/api/suggestions`, `/api/reset`, `/api/languages`, `/api/feedback`, `/api/csrf-token`, `/`).
    *   **Knowledge Base:** Uses a large, hardcoded Python dictionary named `EGYPT_TOURISM_KB` defined within the file.
    *   **Response Logic:** Implemented in `generate_response()` function, using simple keyword matching (`detect_topic()`) against the hardcoded KB, falling back to direct Anthropic calls for complex queries.
    *   **LLM Integration:** Directly initializes `anthropic.Anthropic` client using API key from `.env`. Uses a custom `create_egypt_tourism_prompt()` function.
    *   **NLU/Dialog:** Very basic keyword spotting only (`detect_topic`). No complex NLU or state management from the `src/` module is used.
    *   **Database:** Does not significantly interact with SQLite for KB. Session storage likely uses file system based on `.env`. Analytics logging (MongoDB syntax) likely inactive.
    *   **Configuration:** Reads `.env`, some hardcoded values (KB), uses `os.getenv`.
    *   **Security:** CORS allows all origins, CSRF is disabled.

**1.2. Path B: `src/` Module (Inactive Implementation)**

*   **Location:** Code organized within the `src/` directory.
*   **Framework:** Modular Flask application intended to be driven by Dependency Injection.
*   **Entry Point:** Not the default execution path. Potentially intended to be run via a refactored `app.py` or `src/main.py`.
*   **Key Characteristics:**
    *   **Modular Structure:** Components separated into directories (`nlu`, `dialog`, `knowledge`, `integration`, `database`, `api`, `utils`, etc.).
    *   **Dependency Injection:** Uses `src/utils/container.py` and `src/utils/factory.py` to manage component instantiation and dependencies. `ComponentFactory` loads config from `.env` and `configs/*.json`.
    *   **Core Orchestration:** `src/chatbot.py::Chatbot` class intended to coordinate components.
    *   **NLU Engine:** Advanced implementation in `src/nlu/` using Spacy, Transformers, similarity, regex, fuzzy matching, potentially continuous learning. Requires `fasttext` dependency.
    *   **Dialog Manager:** State machine logic in `src/dialog/manager.py` based on `configs/dialog_flows.json`.
    *   **Knowledge Base:**
        *   Abstraction class `src/knowledge/knowledge_base.py` **exists but is a placeholder returning mock data.** Critical disconnect.
        *   Database access class `src/knowledge/database.py` exists and **can handle SQLite** (and MongoDB/Redis), intended to be used by `KnowledgeBase`.
        *   Vector DB class `src/knowledge/vector_db.py` manages embeddings (local file storage).
        *   RAG pipeline class `src/knowledge/rag_pipeline.py` exists.
    *   **LLM Integration:** `AnthropicService` is registered in the factory. `OpenAIService` code exists but is unconfigured/likely unused.
    *   **Service Hub:** `src/integration/service_hub.py` manages external services (Weather, Translation(mock), LLMs).
    *   **Database:** Configured for SQLite KB/Users (`.env`), Redis Sessions (via `docker-compose`, capable in DB manager), separate Analytics logic uses MongoDB syntax.

## 2. Identified Problem

The primary issue is that the **active execution path (Root `app.py`) does not utilize the sophisticated but inactive `src/` module.** The advanced features are present in code but bypassed in practice. The `src/` module itself is incomplete due to the **placeholder Knowledge Base** component.