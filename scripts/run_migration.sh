#!/bin/bash
# Run the JSONB migration script and verify the results

# Set up error handling
set -e

echo "=== Running JSONB Migration Script ==="
echo "This script will:"
echo "1. Run the migration script to migrate data from text fields to JSONB columns"
echo "2. Fix reference integrity issues"
echo "3. Verify the results"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not found"
    exit 1
fi

# Check if the migration script exists
if [ ! -f "migrations/20240610_migrate_data_to_jsonb.sql" ]; then
    echo "Error: Migration script not found at migrations/20240610_migrate_data_to_jsonb.sql"
    exit 1
fi

# Check if the verification script exists
if [ ! -f "scripts/run_jsonb_migration.py" ]; then
    echo "Error: Verification script not found at scripts/run_jsonb_migration.py"
    exit 1
fi

# Make the verification script executable
chmod +x scripts/run_jsonb_migration.py

# Run the migration
echo "Running migration script..."
python3 scripts/run_jsonb_migration.py

# Check if the migration was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "=== Migration Completed Successfully ==="
    echo "The following changes have been made:"
    echo "1. Added missing JSONB columns to cities table"
    echo "2. Created GIN indexes for efficient JSONB querying"
    echo "3. Migrated data from text fields to JSONB columns for all tables"
    echo "4. Fixed reference integrity issues (attraction and accommodation types)"
    echo ""
    echo "Next steps in the migration plan:"
    echo "- Phase 4.2: Add Foreign Key Columns"
    echo "- Phase 4.3: Populate Foreign Key Columns"
    echo "- Phase 4.4: Add Foreign Key Constraints"
else
    echo ""
    echo "=== Migration Failed ==="
    echo "Please check the error messages above for details."
    exit 1
fi
