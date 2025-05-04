# Egypt Tourism Chatbot - Critical Repair Plan

## Overview

This document outlines a focused plan to fix the critical issues in the Egypt Tourism Chatbot, addressing only what's needed to make it functional for answering tourism queries about Egypt. This plan is designed for an AI agent to follow, with clear steps to resolve the identified problems in order of priority.

## Phase 1: Fix Critical Database Issues 

### 1.1 Correct Database Schema Mismatch

The PostgreSQL schema doesn't match what the code expects, causing widespread failures.

- Review the actual database schema using `psql \d+` commands
- Compare with the expected schema in the code (particularly in formatters expecting JSONB)
- Develop a migration plan - either:
  - Update the database schema to match code expectations (JSONB fields, correct FKs), or
  - Update the code to work with the existing schema (adapt formatters and query methods)
- Document the chosen approach for future reference

### 1.2 Fix Database Initialization

The `_create_postgres_tables` method in `DatabaseManager` has critical errors with foreign keys.

- Fix table creation order to ensure referenced tables exist before foreign keys
- Correct the user_id column/foreign key issue causing initialization failures
- Implement proper error handling for when columns already exist
- Test that the database can be initialized from scratch correctly

### 1.3 Update Database Access Methods

Several DB methods are missing or incomplete, breaking core functionality.

- Implement the missing `search_restaurants` method
- Fix parameter issues in `search_accommodations`
- Ensure all entity types have consistent search methods
- Verify that basic CRUD operations work for all entity types

## Phase 2: Fix Code-Level Errors 

### 2.1 Correct Indentation Error in Attraction Query Processing

There's a critical indentation error in `chatbot.py` that causes early return from attraction queries.

- Fix the indentation in the attraction query handler
- Ensure the function follows the intended flow through NLU processing
- Verify that attraction queries now receive proper responses

### 2.2 Resolve Duplicate Method Definition

The `generate_response` method in `response/generator.py` is defined twice with different signatures.

- Rename one of the methods (e.g., to `generate_response_from_action`)
- Update all call sites to use the appropriate method
- Ensure response generation works with both patterns

### 2.3 Fix Authentication Implementation

Type errors in bcrypt usage are causing authentication issues.

- Correct type handling (bytes vs. strings) in bcrypt functions
- Ensure password hashing and verification work correctly
- Verify login/register functionality with test cases

## Phase 3: Fix Test Framework 

### 3.1 Repair Test Database Setup

Test fixtures are failing due to database issues.

- Update database initialization in test fixtures
- Correct mock data to match expected schema
- Fix async fixture issues to properly yield/return values

### 3.2 Update Test Assertions

Many tests are failing with KeyErrors due to schema mismatch.

- Update assertions to match actual data structure
- Fix tests that rely on specific database schemas
- Ensure test cases reflect current functionality

### 3.3 Address Remaining Test Failures

- Fix other test failures one by one, focusing on core functionality first
- Update integration tests to match current API patterns
- Verify that critical paths have working tests

## Phase 4: Consolidate Architecture 

### 4.1 Establish Single Entry Point

Remove architectural inconsistencies to establish a clear entry point.

- Ensure `src/main.py` is the sole entry point
- Remove or refactor `src/chatbot.py` if it's causing confusion
- Verify that all routes are properly configured in FastAPI

### 4.2 Unify Session Management

- Choose one session management approach (likely FastAPI-based)
- Remove or deprecate alternative session management code
- Ensure session handling works consistently

### 4.3 Remove Legacy Code

- Identify and remove Flask/SQLite remnants
- Delete unused frontend files (if `src/frontend` is obsolete)
- Remove dead code and unused imports

## Phase 5: Implement Core Tourism Knowledge

### 5.1 Create Basic Tourism Data

- Create JSON files with core Egyptian tourism data:
  - Major attractions (pyramids, temples, museums)
  - Cities and regions
  - Hotels and accommodations
  - Restaurants and dining options
  - Practical travel information

### 5.2 Implement Data Loading

- Create a script to load data into the database
- Include English and Arabic content for all entries
- Verify data is correctly stored in the database

### 5.3 Test Query Capabilities

- Verify that basic queries about attractions work
- Test queries about hotels and restaurants
- Ensure language support (English/Arabic) functions correctly

## Phase 6: Verify Core Functionality 

### 6.1 Test End-to-End Flow

- Create a test script to verify the full message flow
- Test key query types:
  - "Tell me about the Pyramids of Giza"
  - "What are the best hotels in Cairo?"
  - "Recommend restaurants in Luxor"
  - "How do I get from Cairo to Alexandria?"

### 6.2 Implement Basic Fallbacks

- Ensure the system has graceful fallbacks for unknown queries
- Add basic error handling for all critical paths
- Test with edge case inputs

### 6.3 Verify Multi-language Support

- Test both English and Arabic queries
- Ensure responses are generated in the correct language
- Verify that language detection works

## Implementation Checklist

Use this checklist to track progress:

- [ ] Fixed database schema mismatch
- [ ] Corrected database initialization
- [ ] Implemented missing database methods
- [ ] Fixed indentation error in attraction query processing
- [ ] Resolved duplicate method definition
- [ ] Fixed authentication implementation
- [ ] Repaired test database setup
- [ ] Updated test assertions
- [ ] Fixed remaining test failures
- [ ] Established single entry point
- [ ] Unified session management
- [ ] Removed legacy code
- [ ] Created basic tourism data
- [ ] Implemented data loading
- [ ] Verified query capabilities
- [ ] Tested end-to-end flow
- [ ] Implemented basic fallbacks
- [ ] Verified multi-language support

## Next Steps (Post-Repair)

Once the chatbot is working for basic tourism queries, consider these improvements:

- Enhance the knowledge base with more detailed information
- Optimize database queries for performance
- Implement more sophisticated natural language understanding
- Add analytics to track user interactions
- Integrate with external services for weather, etc.

But focus on making the core functionality work first!