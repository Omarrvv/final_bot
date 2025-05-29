# Tourism Data Fix and Verification

This directory contains scripts to fix and verify tourism data issues in the Egypt Tourism Chatbot database.

## Issues Addressed

1. **Duplicate FAQs**: Removes duplicate entries in the tourism_faqs table
2. **Missing Embeddings**: Generates embeddings for FAQs that are missing them
3. **Data Quality**: Replaces generated/test city names with realistic Egyptian city names

## Scripts

### Fix Scripts

- `fix_tourism_data.sh`: Main shell script to run the fix process
- `run_fix_tourism_data.py`: Python script that executes the SQL migration and generates embeddings
- `migrations/20250626_fix_tourism_data_issues.sql`: SQL migration to fix data issues

### Verification Scripts

- `verify_tourism_data.sh`: Shell script to run the verification process
- `verify_tourism_data.py`: Python script that checks if all issues have been fixed

## Usage

### Prerequisites

Make sure you have the following installed:
- Python 3.8+
- PostgreSQL client
- Required Python packages: `psycopg2`, `numpy`, `python-dotenv`, `tabulate`

### Environment Variables

Create a `.env` file with the following variables:

```
POSTGRES_DB=egypt_chatbot
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

### Running the Fix

1. Make the scripts executable:
   ```
   chmod +x scripts/fix_tourism_data.sh scripts/run_fix_tourism_data.py
   ```

2. Run the fix script:
   ```
   ./scripts/fix_tourism_data.sh
   ```

### Verifying the Fix

1. Make the verification scripts executable:
   ```
   chmod +x scripts/verify_tourism_data.sh scripts/verify_tourism_data.py
   ```

2. Run the verification script:
   ```
   ./scripts/verify_tourism_data.sh
   ```

## Validation Checks

The verification script performs the following checks:

1. **No duplicate FAQs**: Ensures there are no duplicate questions in the tourism_faqs table
2. **All FAQs have embeddings**: Verifies that all FAQs have valid embeddings for vector search
3. **All destination names are realistic**: Checks that there are no generated/test names in the destinations table
4. **All test queries return results**: Runs test queries to verify the functionality of the new tables

## Rollback

If the fix causes issues, you can restore the database from the latest backup:

```
pg_restore -U postgres -d egypt_chatbot egypt_chatbot_pre_migration_YYYYMMDD.dump
```

## Logs

Both the fix and verification scripts generate log files with timestamps:
- `tourism_data_fix_YYYYMMDD_HHMMSS.log`
- `tourism_data_verification_YYYYMMDD_HHMMSS.log`

Check these logs for detailed information about the process and any issues encountered.
