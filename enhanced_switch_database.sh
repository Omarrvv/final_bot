#!/bin/bash
# Enhanced script to switch between production and test databases
# Features:
# - Verifies database connectivity after switching
# - Creates a .env file for the current environment
# - Provides detailed information about the selected database

set -e  # Exit immediately if a command exits with a non-zero status

# Default to production if no argument is provided
DB_ENV=${1:-prod}

# Function to verify database connectivity
verify_connection() {
    local host=$1
    local port=$2
    local user=$3
    local password=$4
    local dbname=$5
    
    echo "Verifying connection to $dbname..."
    
    # Use PGPASSWORD environment variable to avoid password prompt
    PGPASSWORD=$password psql -h $host -p $port -U $user -d $dbname -c "SELECT 1 as connection_test;" > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        echo "✅ Connection successful"
        return 0
    else
        echo "❌ Connection failed"
        return 1
    fi
}

# Function to get database statistics
get_db_stats() {
    local host=$1
    local port=$2
    local user=$3
    local password=$4
    local dbname=$5
    
    echo "Fetching database statistics..."
    
    # Get table counts
    PGPASSWORD=$password psql -h $host -p $port -U $user -d $dbname -t -c "
    SELECT 'Total tables: ' || COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';
    SELECT 'Cities: ' || COUNT(*) FROM cities;
    SELECT 'Attractions: ' || COUNT(*) FROM attractions;
    SELECT 'Accommodations: ' || COUNT(*) FROM accommodations;
    SELECT 'Regions: ' || COUNT(*) FROM regions;
    SELECT 'Users: ' || COUNT(*) FROM users;
    " | sed 's/^ *//'
    
    # Get database size
    PGPASSWORD=$password psql -h $host -p $port -U $user -d $dbname -t -c "
    SELECT 'Database size: ' || pg_size_pretty(pg_database_size('$dbname'));
    " | sed 's/^ *//'
}

# Set environment variables based on selected environment
if [ "$DB_ENV" = "test" ]; then
    echo "🧪 Switching to TEST database environment"
    export DB_HOST=localhost
    export DB_PORT=5432
    export DB_USER=postgres
    export DB_PASSWORD=postgres
    export DB_NAME=egypt_chatbot_migration_test
    export POSTGRES_URI="postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
    
    # Verify connection
    verify_connection $DB_HOST $DB_PORT $DB_USER $DB_PASSWORD $DB_NAME
    if [ $? -ne 0 ]; then
        echo "Failed to connect to test database. Please check your configuration."
        exit 1
    fi
    
    # Get database statistics
    get_db_stats $DB_HOST $DB_PORT $DB_USER $DB_PASSWORD $DB_NAME
    
elif [ "$DB_ENV" = "prod" ]; then
    echo "🏭 Switching to PRODUCTION database environment"
    export DB_HOST=localhost
    export DB_PORT=5432
    export DB_USER=postgres
    export DB_PASSWORD=postgres
    export DB_NAME=egypt_chatbot
    export POSTGRES_URI="postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
    
    # Verify connection
    verify_connection $DB_HOST $DB_PORT $DB_USER $DB_PASSWORD $DB_NAME
    if [ $? -ne 0 ]; then
        echo "Failed to connect to production database. Please check your configuration."
        exit 1
    fi
    
    # Get database statistics
    get_db_stats $DB_HOST $DB_PORT $DB_USER $DB_PASSWORD $DB_NAME
    
else
    echo "❌ Invalid environment. Use 'test' or 'prod'"
    exit 1
fi

# Create a .env file with the current database configuration
cat > .env.current << EOF
# Database configuration for $DB_ENV environment
# Generated on $(date)
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_NAME=$DB_NAME
POSTGRES_URI=$POSTGRES_URI
EOF

echo ""
echo "✅ Database environment variables set"
echo "📝 Configuration saved to .env.current"
echo ""
echo "To use in your shell session, run:"
echo "source .env.current"
echo ""
echo "Current database: $DB_NAME"
