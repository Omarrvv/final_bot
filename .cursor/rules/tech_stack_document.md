# Technology Stack: Egypt Tourism Chatbot

This document lists the key technologies, frameworks, libraries, and tools identified in the project.

## Backend

*   **Language:** Python 3.12.9 (via Conda)
*   **Web Framework:** Flask (including Flask-CORS, Flask-Limiter, Flask-Swagger-UI)
*   **WSGI Server:** Gunicorn
*   **NLP/ML Libraries (`src/`):**
    *   SpaCy (`spacy`): For basic NER, tokenization. Models: `en_core_web_md`, `xx_ent_wiki_sm`.
    *   Hugging Face Transformers (`transformers`, `torch`, `tokenizers`): For sentence embeddings via specified models (e.g., `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`, `asafaya/bert-base-arabic`).
    *   PyTorch (`torch`, `torchaudio`, `torchvision`): Underlying library for Transformers.
    *   Scikit-learn (`scikit-learn`): Used for utilities like `cosine_similarity`.
    *   *Missing:* `fasttext`: Required for `src/nlu/language.py` but not found in dependencies.
*   **Databases:**
    *   SQLite (`sqlite3` module): Primary configured database for KB, users, sessions (potential), analytics (potential). File: `data/egypt_chatbot.db`.
    *   Redis (`redis` client, via `docker-compose.yml`): Intended/available for session management and caching.
    *   MongoDB (`pymongo` client referenced): Syntax used for analytics logging suggests potential/intended use, but not configured in `.env`.
    *   Local File Vector DB (`src/knowledge/vector_db.py`): Default vector storage.
*   **LLM Integration:**
    *   Anthropic SDK (`anthropic`): Used by root `app.py` and `src/services/anthropic_service.py`. Configured in `.env`.
    *   (OpenAI SDK likely needed for unused `openai_service.py`, `llm_service.py` if activated).
*   **Authentication/Security:**
    *   `PyJWT`: For handling JSON Web Tokens.
    *   `bcrypt`: For password hashing.
*   **Configuration:** `python-dotenv`, `PyYAML` (used by `src/config.py`, though potentially inactive path).
*   **Utilities:** `requests`, `numpy`, `python-dateutil`.

## Frontend

*   **Language:** JavaScript
*   **Framework/Library:** React
*   **HTTP Client:** Axios
*   **Styling:** Tailwind CSS, PostCSS
*   **State Management:** (Not explicitly identified - likely component state or possibly Context API/Redux/Zustand).
*   **Potential:** `react-speech-recognition` dependency suggests voice input capability.

## DevOps & Tooling

*   **Environment Management:** Conda (`environment.yml`)
*   **Package Management:** Pip (`requirements.txt`), Conda, NPM (`package.json`, `package-lock.json`)
*   **Containerization:** Docker (`Dockerfile`), Docker Compose (`docker-compose.yml`)
*   **Orchestration:** Kubernetes (`k8s/` manifests, Kustomize)
*   **CI/CD:** GitHub Actions (`.github/workflows/`)
*   **Testing:**
    *   Python: Pytest (Setup broken)
    *   JavaScript: Jest (Config issues)
*   **Linting:**
    *   Python: `flake8` (`.flake8` file exists)
    *   JavaScript: ESLint (`package.json`, `.eslintrc.json`)
*   **API Documentation:** Swagger UI (`flask-swagger-ui`)

## Development Environment

*   **OS:** macOS ARM64 (based on `uname -a`)
*   **Python:** 3.12.9
*   **Conda:** 25.1.1