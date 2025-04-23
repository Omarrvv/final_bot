# Knowledge Base Connection Fix Guide

## The Problem

The Egypt Tourism Chatbot currently has a critical issue where the Knowledge Base component is disconnected from both the SQLite database and the JSON files. This prevents the chatbot from accessing rich structured tourism data, limiting its capabilities to a rudimentary hardcoded dictionary.

### Root Causes

1. **DatabaseManager/KnowledgeBase Connection**: The KnowledgeBase class doesn't properly initialize the connection to the DatabaseManager.
2. **Method Naming Inconsistencies**: Inconsistent method naming between DatabaseManager and KnowledgeBase (e.g., `search_hotels` vs `search_accommodations`).
3. **Environment Variables**: Incorrect or missing environment variable settings (`USE_NEW_KB`, `USE_POSTGRES`, etc.).
4. **Database Initialization**: The database may not be properly initialized or populated with data.
5. **Component Factory Issues**: The Component Factory creates the Knowledge Base but doesn't properly initialize the database connection.

## The Fix

We've created two scripts to address these issues:

1. `fix_knowledge_base.sh` - A shell script that handles environment setup and database initialization
2. `fix_db_connector.py` - A Python script that patches the DatabaseManager and KnowledgeBase classes

### How to Use the Fix Scripts

#### Step 1: Run the Knowledge Base Fix Script

```bash
chmod +x fix_knowledge_base.sh
./fix_knowledge_base.sh
```

This script will:

- Create/update the `.env` file with proper settings
- Ask if you want to use PostgreSQL or SQLite
- Initialize the selected database
- Test the Knowledge Base connection
- Verify end-to-end functionality with a test query

#### Step 2: Fix Any Remaining Database Connector Issues

```bash
python fix_db_connector.py
```

This script will:

- Patch the DatabaseManager class with any missing methods
- Patch the KnowledgeBase class to ensure proper database connection
- Verify database access works correctly

#### Step 3: Restart the Application

```bash
python src/main.py
```

## Detailed Explanation of the Issue

### Architecture Dichotomy

The chatbot exists in a dual-state architecture:

1. **Active (Legacy) Architecture**: Root-level `app.py` using Flask with a hardcoded knowledge base
2. **Target (Modular) Architecture**: `src/` directory structure using FastAPI with a proper database connection

The fix enables the Target Architecture by connecting the Knowledge Base component to the database.

### Knowledge Base Component

The Knowledge Base is designed to serve as an interface layer to access structured tourism data:

```python
class KnowledgeBase:
    """Knowledge base for Egyptian tourism information.
       Acts as an interface layer over the DatabaseManager."""

    def __init__(self, db_manager: Any, vector_db_uri: Optional[str] = None, content_path: Optional[str] = None):
        # ...
        self._db_available = self._check_db_connection()
        # ...
```

However, the `_db_available` flag may not be set correctly, or the `db_manager` connection might fail.

### Database Manager

The DatabaseManager is responsible for database access:

```python
class DatabaseManager:
    """
    Database manager providing database operations for the chatbot.
    Supports multiple database backends, including SQLite, PostgreSQL, and Redis.
    """

    def __init__(self, database_uri: str = None):
        # ...
        self.database_uri = database_uri or os.environ.get(
            "DATABASE_URI", "sqlite:///./data/egypt_chatbot.db"
        )
        # ...
```

Method naming inconsistencies can cause issues when the Knowledge Base tries to call methods that don't exist or have different names.

### Environment Variables

Key environment variables that affect the Knowledge Base connection:

- `USE_NEW_KB=true` - Use the new Knowledge Base implementation
- `USE_NEW_API=true` - Use the FastAPI application (src/main.py)
- `USE_POSTGRES=true|false` - Use PostgreSQL or SQLite
- `DATABASE_URI` - URI for the database connection

## Troubleshooting

If you still encounter issues after running the fix scripts:

### Database Connection Issues

1. Verify database existence:

   ```bash
   # For SQLite
   ls -la ./data/egypt_chatbot.db

   # For PostgreSQL
   psql -U postgres -c "SELECT datname FROM pg_database WHERE datname='egypt_chatbot'"
   ```

2. Check database tables:

   ```bash
   # For SQLite
   sqlite3 ./data/egypt_chatbot.db ".tables"

   # For PostgreSQL
   psql -U postgres -d egypt_chatbot -c "\dt"
   ```

### Knowledge Base Issues

1. Check for errors in logs:

   ```bash
   tail -n 100 logs/egypt_chatbot_*.log
   ```

2. Verify Knowledge Base connection explicitly:
   ```bash
   python verify_kb_connection.py
   ```

### Component Factory Issues

1. Check if the correct component is being created:
   ```bash
   python -c "
   from src.utils.factory import component_factory
   component_factory.initialize()
   kb = component_factory.create_knowledge_base()
   print(f'Knowledge Base type: {type(kb)}')
   print(f'Database available: {kb._db_available}')
   "
   ```

## Database Schema Information

The database contains the following key tables:

- `attractions` - Tourist attractions
- `cities` - City information
- `accommodations` - Hotels and resorts
- `restaurants` - Dining options
- `transportation` - Transport details
- `practical_info` - Practical information

Each table typically includes multilingual fields (English/Arabic) and structured JSON data.

## Migration to PostgreSQL

If you want to migrate from SQLite to PostgreSQL:

1. Install PostgreSQL and required extensions:

   ```bash
   # For macOS
   brew install postgresql postgis
   brew services start postgresql

   # For Ubuntu/Debian
   sudo apt-get install postgresql postgresql-contrib postgis
   sudo systemctl start postgresql
   ```

2. Create the database:

   ```bash
   createdb egypt_chatbot
   ```

3. Enable extensions:

   ```bash
   psql -d egypt_chatbot -c "CREATE EXTENSION IF NOT EXISTS postgis; CREATE EXTENSION IF NOT EXISTS vector;"
   ```

4. Run the fix script with PostgreSQL option:
   ```bash
   ./fix_knowledge_base.sh
   # Select 'y' when asked about PostgreSQL
   ```

## Conclusion

After following these steps, the Knowledge Base component should be properly connected to the database, enabling the chatbot to access rich structured tourism data. This fixes one of the most critical architectural issues in the system and unlocks more advanced features like sophisticated NLU and dialog management.
