#!/usr/bin/env python3
"""
Check if the database contains tourist information data.
"""
import os
import sys
import psycopg2
from psycopg2 import sql
import urllib.parse as urlparse

def get_postgres_connection():
    """Get a PostgreSQL connection from environment variables."""
    # Get PostgreSQL connection info
    postgres_uri = os.environ.get("POSTGRES_URI")
    if not postgres_uri:
        print("⚠️ POSTGRES_URI environment variable not found")
        db_host = os.environ.get("DB_HOST", "db_postgres")
        db_port = os.environ.get("DB_PORT", "5432")
        db_name = os.environ.get("DB_NAME", "egypt_chatbot")
        db_user = os.environ.get("DB_USERNAME", "postgres")
        db_pass = os.environ.get("DB_PASSWORD", "password")
        postgres_uri = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
        print(f"Using constructed URI: postgresql://{db_user}:***@{db_host}:{db_port}/{db_name}")
    else:
        # For security, print the URI without password
        url = urlparse.urlparse(postgres_uri)
        safe_uri = f"{url.scheme}://{url.username}:***@{url.hostname}:{url.port}{url.path}"
        print(f"Using environment URI: {safe_uri}")
    
    try:
        print("Connecting to PostgreSQL...")
        conn = psycopg2.connect(postgres_uri)
        print("✅ Connected to PostgreSQL successfully")
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to PostgreSQL: {e}")
        return None

def check_tables(conn):
    """Check if tables exist and have data."""
    cursor = conn.cursor()
    
    # List of tables to check
    tables = ["attractions", "accommodations", "restaurants", "cities"]
    
    print("\nChecking tables and row counts:")
    for table in tables:
        try:
            # Check if table exists
            cursor.execute(sql.SQL("SELECT to_regclass(%s)").format(), (table,))
            exists = cursor.fetchone()[0]
            
            if exists:
                # Count rows
                cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(table)))
                count = cursor.fetchone()[0]
                print(f"✅ Table '{table}' exists with {count} rows")
                
                # Get a sample row if there are rows
                if count > 0:
                    cursor.execute(sql.SQL("SELECT * FROM {} LIMIT 1").format(sql.Identifier(table)))
                    sample = cursor.fetchone()
                    columns = [desc[0] for desc in cursor.description]
                    print(f"  Sample columns: {', '.join(columns)}")
            else:
                print(f"❌ Table '{table}' does not exist")
        except Exception as e:
            print(f"❌ Error checking table '{table}': {e}")
    
    cursor.close()

def main():
    """Main function to check database content."""
    # Make sure POSTGRES_URI is in the environment
    conn = get_postgres_connection()
    if conn:
        try:
            check_tables(conn)
            conn.close()
        except Exception as e:
            print(f"❌ Error: {e}")
            return 1
    else:
        print("❌ Could not connect to database - check your connection settings")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
