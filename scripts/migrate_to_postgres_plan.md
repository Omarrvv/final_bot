# PostgreSQL Migration Plan

## Overview

This document outlines the systematic approach to migrating the Egypt Tourism Chatbot database from SQLite to PostgreSQL.

## Prerequisites

1. **PostgreSQL Installation**

   - Install PostgreSQL server (version 14 or higher recommended)
   - Install required extensions:
     - `pgvector` (for vector embeddings)
     - `postgis` (for geospatial functionality)

2. **Database Configuration**
   - Create a dedicated database: `egypt_chatbot`
   - Create a user with appropriate permissions
   - Update connection string in `.env` file

## Migration Process

### Step 1: Verify Environment Setup

- [ ] Check PostgreSQL installation and connectivity
- [ ] Verify required extensions are installed
- [ ] Ensure appropriate permissions for database operations

### Step 2: Prepare Migration Configuration

- [ ] Set `POSTGRES_URI` in `.env` file
- [ ] Keep `USE_POSTGRES=false` during migration setup

### Step 3: Initialize PostgreSQL Schema

- [ ] Create database schema (tables, indexes, constraints)
- [ ] Set up vector embedding columns
- [ ] Configure geospatial features

### Step 4: Migrate Data

- [ ] Run migration script to transfer data from SQLite to PostgreSQL
- [ ] Validate data integrity after migration
- [ ] Generate and store embeddings for vector search

### Step 5: Update Application Configuration

- [ ] Set `USE_POSTGRES=true` in `.env` file
- [ ] Ensure `USE_NEW_KB=true` to use the database-backed Knowledge Base
- [ ] Verify other feature flags that depend on PostgreSQL

### Step 6: Test and Verify

- [ ] Test database connectivity through DatabaseManager
- [ ] Verify Knowledge Base queries work correctly
- [ ] Test vector search functionality
- [ ] Test geospatial query capabilities

## Implementation Commands

```bash
# Step 1: Install PostgreSQL and extensions
# (Instructions depend on operating system)

# Step 2: Set up database and user
psql -c "CREATE DATABASE egypt_chatbot;"
psql -c "CREATE USER egypt_user WITH ENCRYPTED PASSWORD 'your_secure_password';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE egypt_chatbot TO egypt_user;"

# Step 3: Enable required extensions
psql -d egypt_chatbot -c "CREATE EXTENSION IF NOT EXISTS postgis;"
psql -d egypt_chatbot -c "CREATE EXTENSION IF NOT EXISTS pgvector;"

# Step 4: Update .env file
echo "POSTGRES_URI=postgresql://egypt_user:your_secure_password@localhost:5432/egypt_chatbot" >> .env

# Step 5: Run migration script
python scripts/migrate_to_postgres.py

# Step 6: Enable PostgreSQL in configuration
python scripts/set_feature_flags.py --use_postgres=true --use_new_kb=true --set-env
```

## Testing Steps

```bash
# Test database connection
python scripts/test_postgres_connection.py

# Test Knowledge Base with PostgreSQL
python scripts/test_kb_connection.py

# Test specific queries (e.g., for the Pyramids of Giza)
python scripts/test_pyramids_query.py
```

## Rollback Plan

If issues occur during migration:

1. Set `USE_POSTGRES=false` in `.env` to revert to SQLite
2. Diagnose PostgreSQL connectivity or schema issues
3. Correct issues and attempt migration again

## Advanced Features Enabled by PostgreSQL

- **Vector Search**: Semantic similarity search using pgvector
- **Geospatial Queries**: Find attractions/restaurants near a location
- **JSON Query**: Complex queries on structured JSON data using JSONB
- **Full-text Search**: Advanced text search capabilities

## Ongoing Maintenance

- Regular database backups
- Index optimization
- Query performance monitoring
