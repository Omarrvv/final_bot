# Egypt Tourism Chatbot: Test Environment

This document describes the test environment set up for the database migration project.

## Test Database

A test database has been created to safely test all migration steps before applying them to the production database.

### Database Details

- **Name**: egypt_chatbot_migration_test
- **Host**: localhost
- **Port**: 5432
- **User**: postgres
- **Password**: postgres

### Contents

The test database is a clone of the production database, containing:

- All tables with the same structure
- All data from the production database
- All extensions (postgis, vector)
- All indexes and constraints

### Usage

To switch between production and test databases, use the `switch_database.sh` script:

```bash
# Switch to test database
./switch_database.sh test

# Switch to production database
./switch_database.sh prod
```

After running the script, source the environment variables:

```bash
source .env.current
```

### Validation

The test database has been validated to ensure it matches the production database:

- Table count: 23 tables
- Data counts:
  - 4 attractions
  - 4 cities
  - 2 accommodations
- Extensions:
  - postgis (version 3.5.2)
  - vector (version 0.8.0)

### Migration Testing Process

1. All migration steps should be tested in this environment first
2. After successful testing, the steps can be applied to the production database
3. Each step should be validated according to the criteria in the migration plan

## Test Scripts

Test scripts have been created to validate the migration steps:

- `test_redis_session.py`: Tests Redis session management
- `backup_database.py` and `restore_database.py`: Test backup and restore procedures

Additional test scripts will be created for each migration phase.

## Rollback Procedure

If issues are encountered during testing:

1. Drop the test database:
   ```bash
   dropdb -h localhost -p 5432 -U postgres egypt_chatbot_migration_test
   ```

2. Recreate the test database:
   ```bash
   createdb -h localhost -p 5432 -U postgres egypt_chatbot_migration_test
   ```

3. Restore from backup:
   ```bash
   pg_restore -h localhost -p 5432 -U postgres -d egypt_chatbot_migration_test backups/egypt_chatbot_20250504_062903.sql
   ```

This allows for quick recovery to a clean state for retesting.
