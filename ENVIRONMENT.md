# Egypt Tourism Chatbot - Environment Configuration Guide

This document explains how to configure the Egypt Tourism Chatbot application using environment variables.

## Overview

The application uses environment variables to configure its behavior. These can be set in:

1. A `.env` file (recommended for development)
2. System environment variables (recommended for production)

The configuration system uses Pydantic's settings management to validate and load environment variables with proper typing.

## Setting Up Your Environment

### Option 1: Using the .env file

1. Copy the `.env.example` file to `.env`:

   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file to customize settings:
   ```bash
   nano .env
   ```

### Option 2: Setting environment variables directly

For production or CI/CD environments, set the variables directly:

```bash
export DATABASE_URI=sqlite:///./data/egypt_chatbot.db
export USE_REDIS=false
# ... other variables
```

## Important Configuration Categories

### Database Configuration

```
DATABASE_URI=sqlite:///./data/egypt_chatbot.db
VECTOR_DB_URI=./data/vector_db
CONTENT_PATH=./data
```

- `DATABASE_URI`: Connection string for the primary database
- `VECTOR_DB_URI`: Path or connection string for vector database (for RAG)
- `CONTENT_PATH`: Path to content data files

### Session Storage

```
SESSION_STORAGE_URI=file:///./data/sessions
REDIS_URL=redis://localhost:6379/0
```

- `SESSION_STORAGE_URI`: URI for session storage (file or Redis)
- `REDIS_URL`: Redis connection string (used when Redis is enabled)

### API Keys

```
ANTHROPIC_API_KEY=your_anthropic_api_key_here
WEATHER_API_KEY=your_weather_api_key_here
TRANSLATION_API_KEY=your_translation_api_key_here
```

### Feature Flags

Feature flags allow for gradual activation of new features:

```
# Core architecture flags
USE_NEW_KB=false      # Use the new Knowledge Base implementation
USE_NEW_API=false     # Use FastAPI instead of Flask
USE_POSTGRES=false    # Use PostgreSQL instead of SQLite

# Advanced features flags
USE_NEW_NLU=false     # Use the advanced NLU engine
USE_NEW_DIALOG=false  # Use the stateful Dialog Manager
USE_RAG=false         # Use the RAG pipeline
USE_REDIS=false       # Use Redis for session storage
USE_SERVICE_HUB=false # Use the Service Hub for external APIs
```

### Security

```
JWT_SECRET=generate_a_strong_secret_key_here
```

### Server Configuration

```
FLASK_ENV=development
FLASK_DEBUG=1
ENV=development
```

## Validating Your Configuration

Run the settings check script to verify your configuration:

```bash
python scripts/check_settings.py
```

## Important Notes

1. **Environment Variable Format**: All values must be valid for their expected type. For boolean values, use `true` or `false` without any additional comments on the same line.

2. **Feature Flags**: Feature flags allow toggling specific functionality. When a feature flag is set to `true`, the related functionality is enabled.

3. **Automatic Redis Detection**: If your `SESSION_STORAGE_URI` starts with `redis://`, the system will automatically set `USE_REDIS=true` regardless of your .env file setting.

4. **Security**: Avoid storing sensitive values like API keys in version control. The `.env` file is included in `.gitignore` by default.

## Troubleshooting

### Common Issues

1. **Invalid Boolean Format**: Ensure boolean values are `true` or `false` without comments on the same line.

   Wrong: `USE_REDIS=true # Use Redis for caching`  
   Correct: `USE_REDIS=true`

2. **Missing Required Variables**: If the application fails to start, check the error message for missing variables.

3. **Invalid URIs**: Database and storage URIs must be valid URI strings.

### Debug Script

For detailed debugging, use the included debug script:

```bash
python debug_settings.py
```

This script will show all environment variables and how they're loaded by the settings system.
