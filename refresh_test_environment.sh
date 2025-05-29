#!/bin/bash
# Script to refresh the test environment with production data
# Features:
# - Creates a backup of the production database
# - Drops and recreates the test database
# - Restores the production data to the test database
# - Optionally anonymizes sensitive data
# - Verifies the test database

set -e  # Exit immediately if a command exits with a non-zero status

# Configuration
PROD_DB_NAME="egypt_chatbot"
TEST_DB_NAME="egypt_chatbot_migration_test"
DB_USER="postgres"
DB_PASSWORD="postgres"
DB_HOST="localhost"
DB_PORT="5432"
BACKUP_DIR="backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/refresh_${PROD_DB_NAME}_${TIMESTAMP}.sql"
ANONYMIZE=${1:-false}  # Default to not anonymizing data

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if required commands exist
if ! command_exists psql || ! command_exists pg_dump; then
    echo "❌ PostgreSQL client tools (psql, pg_dump) are required but not installed."
    exit 1
fi

# Function to execute SQL commands
execute_sql() {
    local db=$1
    local sql=$2
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $db -c "$sql"
}

# Function to check if a database exists
database_exists() {
    local db=$1
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -lqt | cut -d \| -f 1 | grep -qw $db
    return $?
}

echo "🔄 Starting test environment refresh process"
echo "📊 Source: $PROD_DB_NAME"
echo "🧪 Target: $TEST_DB_NAME"

# Step 1: Create a backup of the production database
echo "📦 Creating backup of production database..."
PGPASSWORD=$DB_PASSWORD pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -F p -f $BACKUP_FILE $PROD_DB_NAME
echo "✅ Backup created: $BACKUP_FILE"

# Step 2: Drop the test database if it exists
if database_exists $TEST_DB_NAME; then
    echo "🗑️ Dropping existing test database..."
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -c "DROP DATABASE $TEST_DB_NAME;"
    echo "✅ Test database dropped"
fi

# Step 3: Create a new test database
echo "🏗️ Creating new test database..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -c "CREATE DATABASE $TEST_DB_NAME;"
echo "✅ Test database created"

# Step 4: Restore the production data to the test database
echo "📥 Restoring data to test database..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $TEST_DB_NAME -f $BACKUP_FILE
echo "✅ Data restored to test database"

# Step 5: Anonymize sensitive data if requested
if [ "$ANONYMIZE" = "true" ]; then
    echo "🔒 Anonymizing sensitive data..."
    
    # Anonymize user data
    execute_sql $TEST_DB_NAME "
    UPDATE users 
    SET 
        email = 'user_' || id || '@example.com',
        password_hash = 'anonymized',
        salt = 'anonymized'
    WHERE id != 'system';
    "
    
    # Anonymize any other sensitive data here
    
    echo "✅ Sensitive data anonymized"
fi

# Step 6: Verify the test database
echo "🔍 Verifying test database..."

# Check if essential tables exist
tables=("cities" "attractions" "accommodations" "regions" "users")
for table in "${tables[@]}"; do
    count=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -t -c "SELECT COUNT(*) FROM $table;" $TEST_DB_NAME | tr -d ' ')
    echo "  - $table: $count records"
done

# Compare record counts with production
echo "📊 Comparing with production database..."
for table in "${tables[@]}"; do
    prod_count=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -t -c "SELECT COUNT(*) FROM $table;" $PROD_DB_NAME | tr -d ' ')
    test_count=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -t -c "SELECT COUNT(*) FROM $table;" $TEST_DB_NAME | tr -d ' ')
    
    if [ "$prod_count" = "$test_count" ]; then
        echo "  - $table: ✅ Counts match ($prod_count records)"
    else
        echo "  - $table: ❌ Counts differ (Prod: $prod_count, Test: $test_count)"
    fi
done

echo ""
echo "✅ Test environment refresh completed successfully"
echo "🧪 You can now switch to the test environment using:"
echo "./enhanced_switch_database.sh test"
