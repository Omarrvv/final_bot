#!/usr/bin/env python3
"""
Database Maintenance Utilities

Handles routine database maintenance tasks like:
- Vacuum/analyze
- Index maintenance
- Invalid data cleanup
- Session expiration
"""

import logging
import psycopg2
from datetime import datetime, timedelta
from typing import List, Optional
from pathlib import Path
import sys

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger import get_logger
from scripts.database.utils.db_utils import check_postgis_extension, check_pgvector_extension

logger = get_logger(__name__)

class DatabaseMaintenance:
    """Handles database maintenance tasks."""
    
    def __init__(self, pg_uri: str):
        self.pg_uri = pg_uri
        
    def connect(self) -> psycopg2.extensions.connection:
        """Connect to PostgreSQL database."""
        return psycopg2.connect(self.pg_uri)
        
    def vacuum_analyze(self, tables: Optional[List[str]] = None) -> None:
        """Run VACUUM ANALYZE on specified tables or all tables."""
        try:
            # Need to use separate connection for VACUUM
            with psycopg2.connect(self.pg_uri, autocommit=True) as conn:
                with conn.cursor() as cur:
                    if tables:
                        for table in tables:
                            logger.info(f"Running VACUUM ANALYZE on {table}")
                            cur.execute(f"VACUUM ANALYZE {table}")
                    else:
                        logger.info("Running VACUUM ANALYZE on all tables")
                        cur.execute("VACUUM ANALYZE")
            logger.info("VACUUM ANALYZE completed successfully")
        except Exception as e:
            logger.error(f"Error during VACUUM ANALYZE: {e}")
            raise

    def reindex_tables(self, tables: Optional[List[str]] = None) -> None:
        """Rebuild indexes for specified tables or all tables."""
        try:
            with self.connect() as conn:
                with conn.cursor() as cur:
                    if tables:
                        for table in tables:
                            logger.info(f"Reindexing table {table}")
                            cur.execute(f"REINDEX TABLE {table}")
                    else:
                        logger.info("Reindexing all tables")
                        cur.execute("REINDEX DATABASE CONCURRENTLY")
                conn.commit()
            logger.info("Reindexing completed successfully")
        except Exception as e:
            logger.error(f"Error during reindexing: {e}")
            raise

    def check_spatial_data(self) -> None:
        """Check for invalid spatial data."""
        spatial_tables = ["attractions", "accommodations", "restaurants"]
        invalid_geoms = []
        
        try:
            with self.connect() as conn:
                with conn.cursor() as cur:
                    if not check_postgis_extension(cur):
                        logger.warning("PostGIS extension not available")
                        return
                        
                    for table in spatial_tables:
                        cur.execute(f"""
                            SELECT id, ST_IsValid(geom) as valid, ST_IsValidReason(geom) as reason
                            FROM {table}
                            WHERE geom IS NOT NULL AND NOT ST_IsValid(geom)
                        """)
                        for id, valid, reason in cur.fetchall():
                            invalid_geoms.append({
                                "table": table,
                                "id": id,
                                "reason": reason
                            })
                            
            if invalid_geoms:
                logger.warning(f"Found {len(invalid_geoms)} invalid geometries")
                for geom in invalid_geoms:
                    logger.warning(f"Invalid geometry in {geom['table']} (id: {geom['id']}): {geom['reason']}")
            else:
                logger.info("All spatial data is valid")
                
        except Exception as e:
            logger.error(f"Error checking spatial data: {e}")
            raise

    def check_vector_data(self) -> None:
        """Check for missing or invalid vector embeddings."""
        vector_tables = ["attractions", "accommodations", "restaurants"]
        missing_vectors = []
        
        try:
            with self.connect() as conn:
                with conn.cursor() as cur:
                    if not check_pgvector_extension(cur):
                        logger.warning("pgvector extension not available")
                        return
                        
                    for table in vector_tables:
                        cur.execute(f"""
                            SELECT id 
                            FROM {table}
                            WHERE embedding IS NULL
                        """)
                        for (id,) in cur.fetchall():
                            missing_vectors.append({
                                "table": table,
                                "id": id
                            })
                            
            if missing_vectors:
                logger.warning(f"Found {len(missing_vectors)} missing vector embeddings")
                for vec in missing_vectors:
                    logger.warning(f"Missing embedding in {vec['table']} (id: {vec['id']})")
            else:
                logger.info("All vector embeddings are present")
                
        except Exception as e:
            logger.error(f"Error checking vector data: {e}")
            raise

    def cleanup_sessions(self, max_age_days: int = 30) -> None:
        """Clean up expired sessions."""
        try:
            with self.connect() as conn:
                with conn.cursor() as cur:
                    cutoff = datetime.now() - timedelta(days=max_age_days)
                    
                    # Delete expired sessions
                    cur.execute("""
                        DELETE FROM sessions 
                        WHERE expires_at < %s 
                        OR (updated_at < %s AND expires_at IS NULL)
                        RETURNING id
                    """, (cutoff, cutoff))
                    
                    deleted = cur.fetchall()
                    conn.commit()
                    
                    if deleted:
                        logger.info(f"Cleaned up {len(deleted)} expired sessions")
                    else:
                        logger.info("No expired sessions found")
                        
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {e}")
            raise

    def analyze_index_usage(self) -> None:
        """Analyze and report on index usage."""
        try:
            with self.connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT 
                            schemaname || '.' || relname as table,
                            indexrelname as index,
                            idx_scan as scans,
                            idx_tup_read as tuples_read,
                            idx_tup_fetch as tuples_fetched
                        FROM pg_stat_user_indexes
                        ORDER BY idx_scan DESC
                    """)
                    
                    logger.info("\nIndex Usage Statistics:")
                    for table, index, scans, reads, fetches in cur.fetchall():
                        logger.info(
                            f"Table: {table}\n"
                            f"  Index: {index}\n"
                            f"  Scans: {scans}\n"
                            f"  Tuples read: {reads}\n"
                            f"  Tuples fetched: {fetches}\n"
                        )
                        
        except Exception as e:
            logger.error(f"Error analyzing index usage: {e}")
            raise

    def run_maintenance(self, 
                       vacuum: bool = True,
                       reindex: bool = True,
                       check_spatial: bool = True,
                       check_vectors: bool = True,
                       cleanup_old_sessions: bool = True,
                       analyze_indexes: bool = True,
                       max_session_age_days: int = 30) -> None:
        """Run all maintenance tasks."""
        try:
            if vacuum:
                self.vacuum_analyze()
                
            if reindex:
                self.reindex_tables()
                
            if check_spatial:
                self.check_spatial_data()
                
            if check_vectors:
                self.check_vector_data()
                
            if cleanup_old_sessions:
                self.cleanup_sessions(max_session_age_days)
                
            if analyze_indexes:
                self.analyze_index_usage()
                
            logger.info("All maintenance tasks completed successfully")
            
        except Exception as e:
            logger.error(f"Error during maintenance: {e}")
            raise

def main():
    """Main entry point for maintenance script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Database Maintenance Tool")
    parser.add_argument("--pg-uri", 
                      default="postgresql://localhost:5432/egypt_chatbot",
                      help="PostgreSQL connection URI")
    parser.add_argument("--no-vacuum", action="store_true",
                      help="Skip VACUUM ANALYZE")
    parser.add_argument("--no-reindex", action="store_true",
                      help="Skip reindexing")
    parser.add_argument("--no-spatial", action="store_true",
                      help="Skip spatial data check")
    parser.add_argument("--no-vectors", action="store_true",
                      help="Skip vector data check")
    parser.add_argument("--no-sessions", action="store_true",
                      help="Skip session cleanup")
    parser.add_argument("--no-indexes", action="store_true",
                      help="Skip index analysis")
    parser.add_argument("--session-age", type=int, default=30,
                      help="Maximum session age in days")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Run maintenance
    maintenance = DatabaseMaintenance(args.pg_uri)
    maintenance.run_maintenance(
        vacuum=not args.no_vacuum,
        reindex=not args.no_reindex,
        check_spatial=not args.no_spatial,
        check_vectors=not args.no_vectors,
        cleanup_old_sessions=not args.no_sessions,
        analyze_indexes=not args.no_indexes,
        max_session_age_days=args.session_age
    )

if __name__ == "__main__":
    main()