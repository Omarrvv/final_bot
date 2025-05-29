#!/bin/bash
# Script to switch between production and test databases

# Default to production if no argument is provided
DB_ENV=${1:-prod}

if [ "$DB_ENV" = "test" ]; then
    echo "Switching to TEST database environment"
    export DB_HOST=localhost
    export DB_PORT=5432
    export DB_USER=postgres
    export DB_PASSWORD=postgres
    export DB_NAME=egypt_chatbot_migration_test
    echo "Now using database: $DB_NAME"
elif [ "$DB_ENV" = "prod" ]; then
    echo "Switching to PRODUCTION database environment"
    export DB_HOST=localhost
    export DB_PORT=5432
    export DB_USER=postgres
    export DB_PASSWORD=postgres
    export DB_NAME=egypt_chatbot
    echo "Now using database: $DB_NAME"
else
    echo "Invalid environment. Use 'test' or 'prod'"
    exit 1
fi

# Create a temporary .env file with the current database configuration
cat > .env.current << EOF
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_NAME=$DB_NAME
EOF

echo "Database environment variables set"
echo "To use in your shell session, run:"
echo "source .env.current"
