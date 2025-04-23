#!/usr/bin/env python3
"""
Optimize PostgreSQL Indexes for Egypt Tourism Chatbot

This script:
1. Analyzes existing database structure and indexes
2. Creates optimized indexes for common query patterns
3. Adds specialized indexes for text search, JSONB, and geospatial queries
4. Reports on index status and recommendations

Usage:
    python optimize_db_indexes.py

Environment variables:
    POSTGRES_URI: The PostgreSQL connection URI
    LOG_LEVEL: Logging level (default: INFO)
"""

import os
import logging
import time
import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
numeric_level = getattr(logging, log_level, logging.INFO)
logging.basicConfig(
    level=numeric_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
def load_config():
    """Load configuration from .env file"""
    import dotenv
    dotenv.load_dotenv()
    
    # Get PostgreSQL URI from environment or use default
    pg_uri = os.environ.get("POSTGRES_URI", "postgresql://omarmohamed@localhost:5432/postgres")
    logger.info(f"Using PostgreSQL URI: {pg_uri}")
    return pg_uri

def connect_to_db(uri):
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(uri)
        logger.info("Connected to PostgreSQL database")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to PostgreSQL database: {e}")
        return None

def get_existing_tables(conn):
    """Get list of existing tables in the database"""
    tables = []
    try:
        with conn.cursor() as cur:
            # Query schema information for relevant tables
            cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            AND table_name IN (
                'attractions', 'hotels', 'restaurants', 'cities', 'users', 'sessions', 'analytics'
            )
            """)
            tables = [row[0] for row in cur.fetchall()]
        logger.info(f"Found {len(tables)} relevant tables: {', '.join(tables)}")
        return tables
    except Exception as e:
        logger.error(f"Error getting existing tables: {e}")
        return []

def get_existing_indexes(conn, table):
    """Get existing indexes for a table"""
    indexes = []
    try:
        with conn.cursor() as cur:
            cur.execute("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = %s
            """, (table,))
            indexes = [(row[0], row[1]) for row in cur.fetchall()]
        logger.debug(f"Found {len(indexes)} existing indexes for table {table}")
        return indexes
    except Exception as e:
        logger.error(f"Error getting existing indexes for table {table}: {e}")
        return []

def get_extension_status(conn):
    """Check status of required PostgreSQL extensions"""
    extensions = {
        "postgis": False,
        "vector": False,
        "pg_trgm": False,
        "btree_gin": False
    }
    
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT extname FROM pg_extension")
            installed = [row[0] for row in cur.fetchall()]
            
            for ext in extensions:
                extensions[ext] = ext in installed
                
        logger.info(f"Extension status: {extensions}")
        return extensions
    except Exception as e:
        logger.error(f"Error checking extension status: {e}")
        return extensions

def create_extension(conn, extension):
    """Create a PostgreSQL extension if it doesn't exist"""
    try:
        with conn.cursor() as cur:
            cur.execute(f"CREATE EXTENSION IF NOT EXISTS {extension}")
            conn.commit()
            logger.info(f"Created extension: {extension}")
            return True
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating extension {extension}: {e}")
        return False

def create_index(conn, table, index_name, index_def):
    """Create an index if it doesn't exist"""
    try:
        with conn.cursor() as cur:
            # Check if index already exists
            cur.execute("""
            SELECT 1 FROM pg_indexes 
            WHERE tablename = %s AND indexname = %s
            """, (table, index_name))
            
            if cur.fetchone():
                logger.debug(f"Index {index_name} already exists on {table}")
                return False
            
            # Create the index
            logger.info(f"Creating index {index_name} on {table}")
            cur.execute(index_def)
            conn.commit()
            return True
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating index {index_name} on {table}: {e}")
        return False

def analyze_table(conn, table):
    """Run ANALYZE on a table to update statistics"""
    try:
        with conn.cursor() as cur:
            logger.info(f"Analyzing table {table}")
            cur.execute(f"ANALYZE {table}")
            conn.commit()
            return True
    except Exception as e:
        conn.rollback()
        logger.error(f"Error analyzing table {table}: {e}")
        return False

def optimize_attraction_indexes(conn):
    """Optimize indexes for attractions table"""
    table = "attractions"
    index_definitions = [
        # B-tree indexes for common equality and range queries
        (f"{table}_type_idx", f"CREATE INDEX {table}_type_idx ON {table} (type)"),
        
        # Trigram indexes for name text search (for partial text search)
        (f"{table}_name_en_trgm_idx", f"CREATE INDEX {table}_name_en_trgm_idx ON {table} USING GIN (name_en gin_trgm_ops)"),
        (f"{table}_name_ar_trgm_idx", f"CREATE INDEX {table}_name_ar_trgm_idx ON {table} USING GIN (name_ar gin_trgm_ops)"),
        
        # JSONB path operators for structured data search
        (f"{table}_ticket_price_idx", f"CREATE INDEX {table}_ticket_price_idx ON {table} USING GIN ((data->'ticket_price') jsonb_path_ops)"),
        
        # Full GIN index for all JSONB data searching
        (f"{table}_data_full_idx", f"CREATE INDEX {table}_data_full_idx ON {table} USING GIN (data)"),
        
        # Geospatial index if latitude/longitude are present
        (f"{table}_location_idx", f"CREATE INDEX {table}_location_idx ON {table} USING GIST (ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography)"),
        
        # Specialized index for "best" attractions (highly rated or popular)
        (f"{table}_popular_idx", f"CREATE INDEX {table}_popular_idx ON {table} USING BTREE ((data->'popularity'))")
    ]
    
    created_count = 0
    for index_name, index_def in index_definitions:
        if create_index(conn, table, index_name, index_def):
            created_count += 1
    
    if created_count > 0:
        analyze_table(conn, table)
    
    logger.info(f"Created {created_count} new indexes for {table}")
    return created_count

def optimize_hotel_indexes(conn):
    """Optimize indexes for hotels table"""
    table = "hotels"
    index_definitions = [
        # B-tree indexes for common equality and range queries
        (f"{table}_stars_idx", f"CREATE INDEX {table}_stars_idx ON {table} (stars)"),
        
        # Trigram indexes for name text search
        (f"{table}_name_en_trgm_idx", f"CREATE INDEX {table}_name_en_trgm_idx ON {table} USING GIN (name_en gin_trgm_ops)"),
        (f"{table}_name_ar_trgm_idx", f"CREATE INDEX {table}_name_ar_trgm_idx ON {table} USING GIN (name_ar gin_trgm_ops)"),
        
        # JSONB path operators for structured data search
        (f"{table}_price_range_idx", f"CREATE INDEX {table}_price_range_idx ON {table} USING GIN ((data->'price_range') jsonb_path_ops)"),
        (f"{table}_facilities_idx", f"CREATE INDEX {table}_facilities_idx ON {table} USING GIN ((data->'facilities') jsonb_path_ops)"),
        
        # Geospatial index for location-based queries
        (f"{table}_location_idx", f"CREATE INDEX {table}_location_idx ON {table} USING GIST (ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography)")
    ]
    
    created_count = 0
    for index_name, index_def in index_definitions:
        if create_index(conn, table, index_name, index_def):
            created_count += 1
    
    if created_count > 0:
        analyze_table(conn, table)
    
    logger.info(f"Created {created_count} new indexes for {table}")
    return created_count

def optimize_restaurant_indexes(conn):
    """Optimize indexes for restaurants table"""
    table = "restaurants"
    index_definitions = [
        # B-tree indexes for common equality and range queries
        (f"{table}_cuisine_idx", f"CREATE INDEX {table}_cuisine_idx ON {table} (cuisine)"),
        
        # Trigram indexes for name text search
        (f"{table}_name_en_trgm_idx", f"CREATE INDEX {table}_name_en_trgm_idx ON {table} USING GIN (name_en gin_trgm_ops)"),
        (f"{table}_name_ar_trgm_idx", f"CREATE INDEX {table}_name_ar_trgm_idx ON {table} USING GIN (name_ar gin_trgm_ops)"),
        
        # JSONB path operators for structured data search
        (f"{table}_price_range_idx", f"CREATE INDEX {table}_price_range_idx ON {table} USING GIN ((data->'price_range') jsonb_path_ops)"),
        (f"{table}_menu_idx", f"CREATE INDEX {table}_menu_idx ON {table} USING GIN ((data->'menu_highlights') jsonb_path_ops)"),
        
        # Geospatial index for location-based queries
        (f"{table}_location_idx", f"CREATE INDEX {table}_location_idx ON {table} USING GIST (ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography)")
    ]
    
    created_count = 0
    for index_name, index_def in index_definitions:
        if create_index(conn, table, index_name, index_def):
            created_count += 1
    
    if created_count > 0:
        analyze_table(conn, table)
    
    logger.info(f"Created {created_count} new indexes for {table}")
    return created_count

def optimize_sessions_indexes(conn):
    """Optimize indexes for sessions table"""
    table = "sessions"
    index_definitions = [
        # B-tree indexes for common equality queries
        (f"{table}_user_id_idx", f"CREATE INDEX {table}_user_id_idx ON {table} (user_id)"),
        
        # Index for timestamp for expiration queries
        (f"{table}_expires_at_idx", f"CREATE INDEX {table}_expires_at_idx ON {table} (expires_at)")
    ]
    
    created_count = 0
    for index_name, index_def in index_definitions:
        if create_index(conn, table, index_name, index_def):
            created_count += 1
    
    if created_count > 0:
        analyze_table(conn, table)
    
    logger.info(f"Created {created_count} new indexes for {table}")
    return created_count

def optimize_analytics_indexes(conn):
    """Optimize indexes for analytics table"""
    table = "analytics"
    index_definitions = [
        # B-tree indexes for common equality and range queries
        (f"{table}_event_type_idx", f"CREATE INDEX {table}_event_type_idx ON {table} (event_type)"),
        (f"{table}_session_id_idx", f"CREATE INDEX {table}_session_id_idx ON {table} (session_id)"),
        (f"{table}_timestamp_idx", f"CREATE INDEX {table}_timestamp_idx ON {table} (timestamp)")
    ]
    
    created_count = 0
    for index_name, index_def in index_definitions:
        if create_index(conn, table, index_name, index_def):
            created_count += 1
    
    if created_count > 0:
        analyze_table(conn, table)
    
    logger.info(f"Created {created_count} new indexes for {table}")
    return created_count

def create_vector_indexes(conn):
    """Create vector indexes for semantic search if vector extension is available"""
    if not get_extension_status(conn)["vector"]:
        logger.warning("Vector extension not available, skipping vector indexes")
        return 0
    
    tables_with_vectors = ["attractions", "hotels", "restaurants"]
    created_count = 0
    
    for table in tables_with_vectors:
        # Check if table exists and has the embedding column
        with conn.cursor() as cur:
            cur.execute(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = '{table}' AND column_name = 'embedding'
            """)
            
            if not cur.fetchone():
                logger.warning(f"Table {table} does not have embedding column, skipping vector index")
                continue
            
            # Create vector index for semantic similarity search
            index_name = f"{table}_embedding_idx"
            index_def = f"CREATE INDEX {index_name} ON {table} USING ivfflat (embedding vector_cosine_ops)"
            
            if create_index(conn, table, index_name, index_def):
                created_count += 1
                logger.info(f"Created vector index for {table}")
    
    return created_count

def optimize_database(conn):
    """Optimize database indexes"""
    total_created = 0
    
    # Ensure required extensions are installed
    extensions = get_extension_status(conn)
    
    for ext in ["postgis", "pg_trgm", "btree_gin"]:
        if not extensions[ext]:
            create_extension(conn, ext)
    
    # Get list of available tables
    tables = get_existing_tables(conn)
    
    # Optimize indexes for each table
    if "attractions" in tables:
        total_created += optimize_attraction_indexes(conn)
    
    if "hotels" in tables:
        total_created += optimize_hotel_indexes(conn)
    
    if "restaurants" in tables:
        total_created += optimize_restaurant_indexes(conn)
    
    if "sessions" in tables:
        total_created += optimize_sessions_indexes(conn)
    
    if "analytics" in tables:
        total_created += optimize_analytics_indexes(conn)
    
    # Create vector indexes if appropriate
    total_created += create_vector_indexes(conn)
    
    logger.info(f"Created {total_created} new indexes across all tables")
    return total_created

def analyze_query_performance(conn):
    """Analyze query performance and make recommendations"""
    recommendations = []
    
    # Check for common query performance issues
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Check for tables without indexes
            cur.execute("""
            SELECT
                tablename,
                count(indexname) as index_count
            FROM
                pg_tables
                LEFT JOIN pg_indexes ON pg_tables.tablename = pg_indexes.tablename
            WHERE
                pg_tables.schemaname = 'public'
            GROUP BY
                pg_tables.tablename
            HAVING
                count(indexname) < 1
            """)
            
            tables_no_indexes = cur.fetchall()
            if tables_no_indexes:
                table_names = ", ".join([t["tablename"] for t in tables_no_indexes])
                recommendations.append(f"Tables without indexes found: {table_names}")
            
            # Check for large tables
            cur.execute("""
            SELECT
                relname as table_name,
                pg_size_pretty(pg_relation_size(C.oid)) as table_size
            FROM
                pg_class C
                LEFT JOIN pg_namespace N ON (N.oid = C.relnamespace)
            WHERE
                nspname = 'public'
                AND C.relkind = 'r'
            ORDER BY
                pg_relation_size(C.oid) DESC
            LIMIT 5
            """)
            
            large_tables = cur.fetchall()
            if large_tables:
                recommendations.append("Large tables detected (consider partitioning if they grow):")
                for table in large_tables:
                    recommendations.append(f"  - {table['table_name']}: {table['table_size']}")
            
            # Check for invalid indexes
            cur.execute("""
            SELECT
                relname as index_name,
                pg_size_pretty(pg_relation_size(C.oid)) as index_size,
                idx_scan as index_scans
            FROM
                pg_catalog.pg_class C,
                pg_catalog.pg_stat_user_indexes PSUI
            WHERE
                C.relname = PSUI.indexrelname
                AND PSUI.idx_scan = 0
                AND 0 <> (SELECT indisvalid FROM pg_catalog.pg_index WHERE indexrelid = c.oid)
                AND NOT EXISTS (
                    SELECT 1 FROM pg_catalog.pg_constraint WHERE conindid = c.oid
                )
            ORDER BY
                pg_relation_size(C.oid) DESC
            LIMIT 5
            """)
            
            unused_indexes = cur.fetchall()
            if unused_indexes:
                recommendations.append("Unused indexes detected (consider removing if they remain unused):")
                for idx in unused_indexes:
                    recommendations.append(f"  - {idx['index_name']}: Size {idx['index_size']}, Scans: {idx['index_scans']}")
    
    except Exception as e:
        logger.error(f"Error during performance analysis: {e}")
    
    # Add general recommendations
    recommendations.append("General recommendations:")
    recommendations.append("  - Run ANALYZE periodically to update statistics")
    recommendations.append("  - Consider adding full-text search (using tsvector) for better text search capabilities")
    recommendations.append("  - Monitor index usage and consider dropping unused indexes")
    recommendations.append("  - Use EXPLAIN ANALYZE to check query performance")
    
    return recommendations

def main():
    """Main execution function"""
    start_time = time.time()
    logger.info("Starting database index optimization")
    
    # Load configuration
    pg_uri = load_config()
    
    # Connect to database
    conn = connect_to_db(pg_uri)
    if not conn:
        logger.error("Failed to connect to database, exiting")
        return False
    
    try:
        # Optimize database indexes
        created_count = optimize_database(conn)
        
        # Analyze query performance
        recommendations = analyze_query_performance(conn)
        
        logger.info(f"Index optimization completed in {time.time() - start_time:.2f} seconds")
        logger.info(f"Created {created_count} new indexes")
        
        logger.info("Performance recommendations:")
        for rec in recommendations:
            logger.info(f"  {rec}")
        
        return True
    except Exception as e:
        logger.error(f"Error during index optimization: {e}")
        return False
    finally:
        conn.close()
        logger.info("Database connection closed")

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 