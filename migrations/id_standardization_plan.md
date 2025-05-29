# ID Standardization Migration Plan

## Overview

This plan outlines the steps to standardize all table IDs to integer type in the Egypt Chatbot database. The migration will be executed in stages to minimize risk and ensure proper testing at each step.

## Prerequisites

- Create a backup of the production database
- Create a test database for migration testing
- Verify application code compatibility with integer IDs
- Prepare rollback scripts for each stage

## Migration Stages

### Stage 1: Independent Tables

These tables have minimal foreign key relationships and can be migrated first:

1. `users`
2. `chat_logs`
3. `analytics_events`
4. `media`
5. `reviews`
6. `favorites`
7. `sessions`

### Stage 2: Reference Tables

These tables are referenced by other tables but don't have many foreign key dependencies themselves:

1. `regions`
2. `cities` (depends on regions)
3. `attraction_subcategories`
4. `event_categories`
5. `faq_categories`
6. `practical_info_categories`
7. `tour_package_categories`
8. `itinerary_types`

### Stage 3: Core Domain Tables

These tables are central to the application and have multiple foreign key relationships:

1. `attractions`
2. `accommodations`
3. `restaurants`
4. `hotels`
5. `destinations`

### Stage 4: Test Tables

These tables are used for testing and can be migrated last:

1. `test_attractions`
2. `test_restaurants`
3. `perf_attractions`

## Migration Process for Each Table

For each table, follow these steps:

1. Create an ID mapping table to preserve relationships
2. Populate the mapping table with existing IDs
3. Add a new integer ID column to the table
4. Update foreign key columns in related tables
5. Modify column types for foreign keys
6. Drop old primary key constraint
7. Rename ID columns
8. Add new primary key constraint
9. Add foreign key constraints
10. Clean up mapping tables

## Testing Strategy

After each stage:

1. Verify data integrity with count queries
2. Test application functionality related to the migrated tables
3. Verify foreign key relationships
4. Run performance tests to ensure no degradation

## Rollback Plan

For each stage, prepare a rollback script that:

1. Restores the original ID columns
2. Restores foreign key relationships
3. Drops the integer ID columns

## Application Code Changes

The following application code changes will be needed:

1. Update database models to use integer IDs
2. Update queries to handle integer IDs
3. Update API endpoints to accept and return integer IDs
4. Update frontend code to handle integer IDs

## Timeline

- Stage 1: 1 day
- Stage 2: 1-2 days
- Stage 3: 2-3 days
- Stage 4: 1 day
- Testing: Throughout each stage

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Data loss | Create backups before each stage |
| Application errors | Test thoroughly after each stage |
| Performance issues | Monitor query performance |
| Downtime | Schedule migration during low-traffic periods |

## Success Criteria

- All tables use integer IDs
- All foreign key relationships are preserved
- Application functions correctly with integer IDs
- No performance degradation
