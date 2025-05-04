# Database Schema Migration Documentation

## Overview

This document describes the migration of the Egypt Tourism Chatbot database schema to use JSONB fields for multilingual content. The migration addresses the schema mismatch issue identified in the repair plan.

## Changes Made

### 1. Added JSONB Columns

Added JSONB columns for name and description to the following tables:

- attractions
- restaurants
- accommodations

The SQL migration script (`migrations/20240530_add_jsonb_columns.sql`) adds these columns and creates indexes for efficient querying.

### 2. Migrated Data

Migrated data from the separate text fields (name_en, name_ar, description_en, description_ar) to the JSONB fields (name, description) using the following approach:

- Used PostgreSQL's `jsonb_build_object` function to create JSONB objects
- Preserved the original data in the separate text fields for backward compatibility
- Created indexes on the JSONB fields for efficient querying

### 3. Updated Code

Updated the formatters in `src/knowledge/knowledge_base.py` to prioritize the JSONB fields:

- Modified `_format_attraction_data`, `_format_restaurant_data`, and `_format_accommodation_data` methods
- Implemented a fallback mechanism to use the separate text fields if the JSONB fields are not available
- Ensured backward compatibility with existing code and tests

## Implementation Details

### Migration Script

The migration script (`migrations/20240530_add_jsonb_columns.sql`) performs the following operations:

1. Adds JSONB columns for name and description to the tables
2. Migrates data from separate text fields to JSONB fields
3. Creates indexes for efficient querying

### Code Changes

The code changes in `src/knowledge/knowledge_base.py` prioritize the JSONB fields:

1. Check if the JSONB field exists
2. If it exists, use it (parsing it if it's a string)
3. If it doesn't exist, fall back to the separate text fields
4. Ensure backward compatibility with existing code and tests

### Parameter Fixes

We also fixed parameter mismatches in the KnowledgeBase methods:

1. Updated `search_restaurants` to use `filters` parameter instead of `query`
2. Updated `search_hotels` to use `filters` parameter instead of `query`
3. Added fallback mechanisms for when the database methods are not available
4. Ensured that the code works with both the old and new schema

## Testing

The migration was tested by:

1. Running the migration script
2. Verifying that the JSONB columns were created
3. Verifying that data was migrated correctly
4. Testing the code changes to ensure they work with both the JSONB fields and the separate text fields

## Future Considerations

In the future, consider:

1. Removing the separate text fields once all code has been updated to use only the JSONB fields
2. Adding more validation to ensure data consistency
3. Updating the database schema creation code to create only the JSONB fields for new installations
