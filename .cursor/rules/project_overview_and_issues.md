# Project Overview and Issues: Egypt Tourism Chatbot

## 1. Project Purpose

This project aims to be a conversational AI assistant focused on providing information and assistance related to tourism in Egypt. It intends to handle user queries in natural language (English/Arabic), understand intent and entities, access a knowledge base, potentially integrate with external services (LLM, Weather, Translation), and provide informative responses via a web interface.

## 2. Current High-Level Status

The project currently exists in a state with **two parallel backend implementations**:

1.  **A simpler, functional implementation (root `app.py`)**: This is the *active* implementation run by default (`Dockerfile`, `start_chatbot.sh`). It uses a hardcoded Python dictionary as its Knowledge Base and relies heavily on direct calls to the Anthropic (Claude) LLM for generating responses.
2.  **A sophisticated, modular implementation (`src/` directory)**: This contains a well-structured architecture with dedicated components for NLU, Dialog Management, RAG, Database interaction, etc., using Dependency Injection. However, this path is currently **inactive** and critically hampered by a **placeholder `KnowledgeBase` implementation** that doesn't connect to the defined (but empty) SQLite database.

The primary goal of the planned work is to **consolidate the architecture** onto the more robust `src/` path, **activate its connection to a populated Knowledge Base**, resolve database inconsistencies, fix broken tests, and address security flaws.

## 3. Critical Issues Requiring Urgent Attention

Based on terminal analysis:

1.  **Dual Architecture Execution:** The sophisticated `src/` module is bypassed; the limited root `app.py` runs instead (`Dockerfile`, logs).
2.  **Placeholder `src/KnowledgeBase`:** The `src/` KB component returns mock data, not DB data (`cat src/knowledge/knowledge_base.py`).
3.  **Empty KB Database:** SQLite KB tables (`attractions`, etc.) are empty (`sqlite3 "SELECT COUNT(*)..."`).
4.  **Missing KB Population Script:** No script exists to load data from `data/*.json` into the SQLite DB (`find` command).
5.  **Broken Python Test Suite:** Tests fail completely due to import errors and missing dependencies (`pytest -v` output).
6.  **Missing `fasttext` Dependency:** Required by `src/nlu/language.py` but not installed (`pytest` output).
7.  **CORS Misconfiguration:** Allows all origins (`*`) (`cat app.py`).
8.  **CSRF Disabled:** Protection explicitly turned off (`cat app.py`).
9.  **Frontend Template Not Found:** Root `app.py` fails to render `index.html` (`tail logs/*.log`).

## 4. Goal of AI Intervention

The AI agent should follow the `implementation_plan.md` to refactor the codebase, consolidate the architecture onto the `src/` path, implement the knowledge base connection and population, fix tests, address security issues, and prepare the project for reliable operation and future development.