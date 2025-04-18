
**File: implementation_plan.md**
```markdown
# Implementation Plan: Egypt Tourism Chatbot Refactoring

This plan outlines the steps to consolidate the architecture, fix critical issues, and activate the advanced features of the chatbot.

**Target Architecture:** Consolidate onto the modular `src/` structure, activate the SQLite Knowledge Base, use Redis for sessions, resolve DB inconsistencies, fix tests, and harden security.

---

## Phase 0: Preparation & Setup (Effort: Low)

*   **Goal:** Prepare environment, backup state, confirm target path.
*   **Actions:**
    1.  `git checkout -b refactor/consolidate-src`
    2.  Backup `data/`, `configs/`, `.env`.
    3.  Document target architecture decision (Use `src/`).
    4.  Define acceptance criteria.
    5.  Ensure Conda env is up-to-date. Install `sqlite3` CLI if needed.

---

## Phase 1: Critical Fixes & Environment Setup (Effort: Medium)

*   **Goal:** Fix testing environment, baseline security issues, and frontend serving errors.
*   **Actions:**
    1.  **Fix Python Test Environment:**
        *   Diagnose and fix `PYTHONPATH` issues (e.g., set `PYTHONPATH=.` or configure `pytest.ini`).
        *   Install missing test dependencies in `egypt-tourism` env: `pip install python-dotenv flask pytest-mock fasttext-wheel pytest-cov` (or Conda equivalent).
        *   *Verify:* `pytest -v` runs without `ModuleNotFoundError`.
    2.  **Fix Frontend Serving (root `app.py`):**
        *   Adjust Flask `static_folder`/`template_folder` or `send_from_directory` logic in the `/` route to correctly serve `react-frontend/build/index.html`.
        *   *Files:* `app.py`.
        *   *Verify:* Accessing `/` in browser loads React app without errors.
    3.  **Fix Security Issues (root `app.py`):**
        *   Restrict CORS `origins` from `"*"` to specific frontend URLs.
        *   Set `app.config['CSRF_ENABLED'] = True`. Verify frontend sends `X-CSRF-Token` fetched from `/api/csrf-token`.
        *   *Files:* `app.py`, `react-frontend/src/services/ChatbotService.js`.
        *   *Verify:* App functions, CORS restricts, CSRF works.

---

## Phase 2: Architectural Consolidation (Effort: Medium-High)

*   **Goal:** Switch execution to the `src/` module structure via a refactored entry point.
*   **Actions:**
    1.  **Refactor Entry Point (root `app.py`):**
        *   Remove hardcoded `EGYPT_TOURISM_KB`, `generate_response`, direct Anthropic init.
        *   Import `component_factory` from `src/utils/factory.py` and `Chatbot` from `src/chatbot.py`.
        *   Call `component_factory.initialize()` early.
        *   Instantiate `chatbot = Chatbot(initialize_components=False)`.
        *   Adapt API routes (`/api/chat`, etc.) to call `chatbot` methods (`chatbot.process_message`, etc.).
        *   Ensure Flask app config (CORS, Limiter etc.) remains.
        *   *Files:* `app.py`, `src/utils/factory.py`.
        *   *Verify:* App runs via `start_chatbot.sh`. API requests hit `src/chatbot.py` (check logs). Responses will be mock/fallback initially.
    2.  **(Optional) Cleanup:** Delete `src/main.py` if `app.py` is the sole entry point.
        *   *Files:* `src/main.py`.
        *   *Verify:* App still runs.

---

## Phase 3: Feature Completion (KB & Services) (Effort: High)

*   **Goal:** Activate the Knowledge Base connection, populate the DB, and implement real external services.
*   **Actions:**
    1.  **Implement KB Population Script:**
        *   Create `scripts/populate_kb.py` to parse `data/**/*.json` (focus on `attractions` first) and INSERT/REPLACE data into SQLite tables (`attractions`, `accommodations`, `restaurants`) matching `init_db.py` schema. Use logic similar to provided example in `knowledge_base_plan.md`.
        *   *Files:* `scripts/populate_kb.py`.
        *   *Verify:* Run script, use `sqlite3` to confirm data exists in tables.
    2.  **Fix `src/knowledge/knowledge_base.py`:**
        *   Modify `__init__` to accept injected `db_manager` instance from the `database_manager` factory (`src/utils/factory.py`).
        *   Remove placeholder methods/data.
        *   Implement KB methods (`get_attraction_by_id`, `search_attractions`, etc.) by **calling the corresponding methods on the injected `db_manager`**.
        *   *Files:* `src/knowledge/knowledge_base.py`, `src/utils/factory.py`.
        *   *Verify:* Restart app. Test `/api/chat` with KB queries. Responses should reflect data from SQLite DB.
    3.  **Implement `TranslationService`:**
        *   Choose API provider, add key to `.env`.
        *   Replace mock logic in `src/integration/plugins/translation_service.py` with real API calls.
        *   *Files:* `src/integration/plugins/translation_service.py`, `.env`.
        *   *Verify:* Test flows involving translation.
    4.  **Verify `WeatherService`:** Ensure `WEATHER_API_KEY` is set in `.env` if needed.

---

## Phase 4: Tuning, Cleanup & Debt Reduction (Effort: Ongoing High)**

*   **Goal:** Optimize performance, resolve remaining inconsistencies, improve code quality, and add tests.
*   **Actions:**
    1.  **Resolve Analytics DB:**
        *   Decide SQLite/Mongo. Recommend **SQLite**.
        *   Refactor analytics `DatabaseManager` and `/api/stats/*` endpoints to use the main SQLite DB Manager (`src/knowledge/database.py`).
        *   *Files:* `src/database/database_manager.py` (if separate file persists for task), `src/api/analytics_api.py`, `src/knowledge/database.py`.
        *   *Verify:* Analytics logged and retrieved correctly from SQLite.
    2.  **Consolidate LLM:** Remove unused OpenAI code (`src/integration/plugins/*openai*`, `llm_service.py`), update `ServiceHub`/`configs/services.json` if needed.
        *   *Files:* Affected plugin files, `service_hub.py`, `services.json`.
        *   *Verify:* Clean codebase, only Anthropic configured unless OpenAI explicitly added.
    3.  **Optimize Performance:**
        *   **Sessions:** Migrate sessions to **Redis**. Update `SESSION_STORAGE_URI` in `.env`, update `src/utils/session.py` and `src/knowledge/database.py` (if it handles Redis connection). *Verification:* Sessions persist across restarts via Redis.
        *   **LLM (Async):** (Advanced) Investigate using `asyncio` with Flask (or switching to Quart/FastAPI) or Celery for background LLM calls to prevent blocking.
        *   **VectorDB:** Document recommendation for external vector DB for scaling.
        *   **Database:** Add necessary indexes to SQLite (`init_db.py`) based on query patterns.
    4.  **Increase Test Coverage:**
        *   Write `pytest` unit/integration tests for all critical components (KB access, NLU logic, Dialog transitions, Service interactions).
        *   Fix `npm test` warnings and add React component tests.
        *   Use `pytest-cov` and `npm test -- --coverage` to measure progress.
        *   *Files:* `tests/`, `react-frontend/src/`.
        *   *Verify:* Tests pass, coverage improves.
    5.  **Streamline Configuration:** Minimize direct `os.getenv`, use central config object/factory values via DI.
    6.  **Dependency Audit:** Run `pip-audit`, `npm audit`. Update/remove packages.
    7.  **Documentation:** Update `README.md`, `ARCHITECTURE.md` (target), API Docs (Swagger).

---

This roadmap prioritizes unblocking the core `src/` functionality and fixing critical issues first, followed by completion, optimization, and cleanup.