"""
Vector Search Optimization Utilities

This module provides tools to optimize vector search performance in PostgreSQL
using pgvector indexes like IVFFlat and HNSW.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Union
import math

from src.utils.logger import get_logger
from src.utils.postgres_database import PostgresqlDatabaseManager
from src.utils.vector_benchmarks import VectorSearchBenchmark

logger = get_logger(__name__)

class VectorOptimizer:
    """Utility for optimizing vector search performance."""
    
    def __init__(self, db_manager: PostgresqlDatabaseManager):
        """
        Initialize the vector optimizer.
        
        Args:
            db_manager: PostgreSQL database manager instance
        """
        self.db_manager = db_manager
        self.benchmark = VectorSearchBenchmark(db_manager)
        
    def check_pgvector_extension(self) -> bool:
        """
        Check if pgvector extension is installed and available.
        
        Returns:
            True if pgvector is available, False otherwise
        """
        try:
            query = "SELECT 1 FROM pg_extension WHERE extname = 'vector'"
            result = self.db_manager.execute_query(query)
            return len(result) > 0
        except Exception as e:
            logger.error(f"Error checking pgvector extension: {e}")
            return False
    
    def get_vector_dimensions(self, table: str) -> Optional[int]:
        """
        Get the dimensions of vectors in a table.
        
        Args:
            table: Name of the table with vector data
            
        Returns:
            Number of dimensions or None if it cannot be determined
        """
        try:
            # First check if table has any data with embeddings
            check_query = f"SELECT embedding FROM {table} WHERE embedding IS NOT NULL LIMIT 1"
            result = self.db_manager.execute_query(check_query)
            
            if not result:
                logger.warning(f"No vectors found in table {table}")
                return None
                
            # Get vector dimensions from the table
            dim_query = """
                SELECT a.atttypmod
                FROM pg_attribute a
                JOIN pg_class c ON a.attrelid = c.oid
                WHERE c.relname = %s AND a.attname = 'embedding'
            """
            result = self.db_manager.execute_query(dim_query, (table,))
            
            if result and result[0]['atttypmod'] > 0:
                # atttypmod is dimensions+4 for vector type
                return result[0]['atttypmod'] - 4
                
            # Alternative approach - check the first non-null vector
            sample_query = f"SELECT embedding FROM {table} WHERE embedding IS NOT NULL LIMIT 1"
            sample = self.db_manager.execute_query(sample_query)
            if sample and 'embedding' in sample[0]:
                return len(sample[0]['embedding'])
                
            return None
        except Exception as e:
            logger.error(f"Error getting vector dimensions for table {table}: {e}")
            return None
    
    def get_table_count(self, table: str) -> int:
        """
        Get the number of rows in a table.
        
        Args:
            table: Name of the table
            
        Returns:
            Number of rows in the table
        """
        try:
            query = f"SELECT COUNT(*) as count FROM {table} WHERE embedding IS NOT NULL"
            result = self.db_manager.execute_query(query)
            return result[0]['count'] if result else 0
        except Exception as e:
            logger.error(f"Error getting row count for table {table}: {e}")
            return 0
    
    def estimate_optimal_ivfflat_lists(self, row_count: int) -> int:
        """
        Estimate the optimal number of lists for an IVFFlat index.
        
        Args:
            row_count: Number of vectors in the table
            
        Returns:
            Recommended number of lists
        """
        # Heuristic: sqrt(n) is a common starting point
        # For smaller datasets, we want fewer lists
        if row_count < 1000:
            return max(4, int(math.sqrt(row_count / 2)))
        elif row_count < 10000:
            return max(10, int(math.sqrt(row_count)))
        else:
            # For larger datasets, slightly more lists than sqrt
            return int(math.sqrt(row_count) * 1.5)
    
    def create_vector_index(
        self, 
        table: str, 
        column: str = 'embedding', 
        index_type: str = 'ivfflat',
        parameters: Dict[str, Any] = None
    ) -> bool:
        """
        Create a vector search index for a table.
        
        Args:
            table: Name of the table
            column: Name of the vector column
            index_type: Type of index ('ivfflat' or 'hnsw')
            parameters: Index-specific parameters
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current vector dimensions and row count
            dimensions = self.get_vector_dimensions(table)
            row_count = self.get_table_count(table)
            
            if not dimensions:
                logger.error(f"Could not determine vector dimensions for table {table}")
                return False
                
            logger.info(f"Creating {index_type} index for {table}.{column} with {dimensions} dimensions, {row_count} vectors")
            
            # Drop existing index if it exists
            drop_query = f"DROP INDEX IF EXISTS idx_{table}_{column}"
            self.db_manager.execute_update(drop_query)
            
            # Create the appropriate index type
            if index_type.lower() == 'ivfflat':
                # Determine optimal number of lists if not provided
                lists = parameters.get('lists') if parameters else None
                if not lists:
                    lists = self.estimate_optimal_ivfflat_lists(row_count)
                    logger.info(f"Estimated optimal IVFFlat lists for {table}: {lists}")
                
                # Create IVFFlat index
                create_query = f"""
                    CREATE INDEX idx_{table}_{column} ON {table} 
                    USING ivfflat ({column} vector_l2_ops)
                    WITH (lists = {lists})
                """
                self.db_manager.execute_update(create_query)
                logger.info(f"Created IVFFlat index for {table}.{column} with {lists} lists")
                
            elif index_type.lower() == 'hnsw':
                # HNSW parameters
                m = parameters.get('m', 16) if parameters else 16  # Max number of connections per node
                ef_construction = parameters.get('ef_construction', 64) if parameters else 64  # Size of dynamic list for candidates
                
                # Create HNSW index
                create_query = f"""
                    CREATE INDEX idx_{table}_{column} ON {table} 
                    USING hnsw ({column} vector_l2_ops)
                    WITH (m = {m}, ef_construction = {ef_construction})
                """
                self.db_manager.execute_update(create_query)
                logger.info(f"Created HNSW index for {table}.{column} with m={m}, ef_construction={ef_construction}")
                
            else:
                logger.error(f"Unknown index type: {index_type}")
                return False
                
            return True
        except Exception as e:
            logger.error(f"Error creating vector index: {e}")
            return False
    
    def optimize_all_vector_tables(self, index_type: str = 'ivfflat') -> Dict[str, bool]:
        """
        Optimize vector indexes for all relevant tables.
        
        Args:
            index_type: Type of index to create ('ivfflat' or 'hnsw')
            
        Returns:
            Dictionary of tables and optimization status
        """
        # Check pgvector extension
        if not self.check_pgvector_extension():
            logger.error("pgvector extension is not available, cannot optimize vector search")
            return {}
            
        tables = ['attractions', 'hotels', 'restaurants', 'cities']
        results = {}
        
        # Optimize each table
        for table in tables:
            # Benchmark before optimization
            logger.info(f"Benchmarking {table} before optimization...")
            if table == 'attractions':
                before_results = self.benchmark.run_benchmark(
                    self.db_manager.vector_search_attractions, iterations=3)
            elif table == 'hotels':
                before_results = self.benchmark.run_benchmark(
                    self.db_manager.vector_search_hotels, iterations=3)
            elif table == 'restaurants':
                before_results = self.benchmark.run_benchmark(
                    self.db_manager.vector_search_restaurants, iterations=3)
            elif table == 'cities':
                before_results = self.benchmark.run_benchmark(
                    self.db_manager.vector_search_cities, iterations=3)
            
            # Create optimized index
            success = self.create_vector_index(table, index_type=index_type)
            results[table] = success
            
            if success:
                # Benchmark after optimization
                logger.info(f"Benchmarking {table} after optimization...")
                if table == 'attractions':
                    after_results = self.benchmark.run_benchmark(
                        self.db_manager.vector_search_attractions, iterations=3)
                elif table == 'hotels':
                    after_results = self.benchmark.run_benchmark(
                        self.db_manager.vector_search_hotels, iterations=3)
                elif table == 'restaurants':
                    after_results = self.benchmark.run_benchmark(
                        self.db_manager.vector_search_restaurants, iterations=3)
                elif table == 'cities':
                    after_results = self.benchmark.run_benchmark(
                        self.db_manager.vector_search_cities, iterations=3)
                
                # Calculate improvement
                if 'avg_time' in before_results and 'avg_time' in after_results:
                    improvement = (before_results['avg_time'] - after_results['avg_time']) / before_results['avg_time'] * 100
                    logger.info(f"{table} optimization: {improvement:.2f}% improvement in query time")
            
        return results
    
    def analyze_vector_health(self) -> Dict[str, Dict[str, Any]]:
        """
        Analyze the health of vector indices and tables.
        
        Returns:
            Dictionary with health analysis results
        """
        tables = ['attractions', 'hotels', 'restaurants', 'cities']
        results = {}
        
        for table in tables:
            table_stats = {
                'total_rows': 0,
                'rows_with_embeddings': 0,
                'embedding_coverage': 0,
                'has_index': False,
                'index_type': None,
                'dimensions': None,
                'recommendations': []
            }
            
            try:
                # Get total rows
                total_query = f"SELECT COUNT(*) as count FROM {table}"
                total_result = self.db_manager.execute_query(total_query)
                table_stats['total_rows'] = total_result[0]['count'] if total_result else 0
                
                # Get rows with embeddings
                embedding_query = f"SELECT COUNT(*) as count FROM {table} WHERE embedding IS NOT NULL"
                embedding_result = self.db_manager.execute_query(embedding_query)
                table_stats['rows_with_embeddings'] = embedding_result[0]['count'] if embedding_result else 0
                
                # Calculate coverage
                if table_stats['total_rows'] > 0:
                    table_stats['embedding_coverage'] = (table_stats['rows_with_embeddings'] / table_stats['total_rows']) * 100
                
                # Check for vector index
                index_query = f"""
                    SELECT indexname, indexdef 
                    FROM pg_indexes 
                    WHERE tablename = '{table}' AND indexdef LIKE '%vector%'
                """
                index_result = self.db_manager.execute_query(index_query)
                
                if index_result:
                    table_stats['has_index'] = True
                    index_def = index_result[0]['indexdef']
                    
                    if 'ivfflat' in index_def.lower():
                        table_stats['index_type'] = 'IVFFlat'
                    elif 'hnsw' in index_def.lower():
                        table_stats['index_type'] = 'HNSW'
                    else:
                        table_stats['index_type'] = 'Unknown'
                
                # Get vector dimensions
                table_stats['dimensions'] = self.get_vector_dimensions(table)
                
                # Generate recommendations
                if table_stats['embedding_coverage'] < 90:
                    table_stats['recommendations'].append(
                        f"Only {table_stats['embedding_coverage']:.1f}% of rows have embeddings. Consider generating embeddings for missing rows."
                    )
                
                if not table_stats['has_index'] and table_stats['rows_with_embeddings'] > 0:
                    table_stats['recommendations'].append(
                        "No vector index found. Create an index to improve search performance."
                    )
                
                if table_stats['has_index'] and table_stats['index_type'] == 'IVFFlat' and table_stats['rows_with_embeddings'] > 100000:
                    table_stats['recommendations'].append(
                        "Large dataset detected with IVFFlat index. Consider using HNSW for better search performance."
                    )
                
                results[table] = table_stats
                
            except Exception as e:
                logger.error(f"Error analyzing vector health for table {table}: {e}")
                results[table] = {'error': str(e)}
        
        return results

def main():
    """Run vector optimization as a standalone script."""
    import argparse
    from pprint import pprint
    
    parser = argparse.ArgumentParser(description="Optimize pgvector indexes")
    parser.add_argument("--uri", help="PostgreSQL database URI", default=None)
    parser.add_argument("--index-type", choices=["ivfflat", "hnsw"], default="ivfflat",
                      help="Type of index to create (default: ivfflat)")
    parser.add_argument("--table", help="Specific table to optimize (default: all)", default=None)
    parser.add_argument("--analyze", action="store_true", help="Only analyze vector health without making changes")
    args = parser.parse_args()
    
    # Connect to database
    db_manager = PostgresqlDatabaseManager(database_uri=args.uri)
    optimizer = VectorOptimizer(db_manager)
    
    # Check if pgvector extension is available
    if not optimizer.check_pgvector_extension():
        print("Error: pgvector extension is not installed in the database")
        return 1
    
    if args.analyze:
        # Analyze vector health
        print("Analyzing vector health...")
        health_results = optimizer.analyze_vector_health()
        
        for table, stats in health_results.items():
            print(f"\n=== {table.upper()} ===")
            if 'error' in stats:
                print(f"Error: {stats['error']}")
                continue
                
            print(f"Total rows: {stats['total_rows']}")
            print(f"Rows with embeddings: {stats['rows_with_embeddings']} ({stats['embedding_coverage']:.1f}%)")
            print(f"Has vector index: {'Yes - ' + stats['index_type'] if stats['has_index'] else 'No'}")
            print(f"Vector dimensions: {stats['dimensions']}")
            
            if stats['recommendations']:
                print("\nRecommendations:")
                for i, rec in enumerate(stats['recommendations'], 1):
                    print(f"{i}. {rec}")
    else:
        # Optimize vector indexes
        if args.table:
            # Optimize specific table
            print(f"Optimizing vector index for table {args.table}...")
            success = optimizer.create_vector_index(args.table, index_type=args.index_type)
            print(f"Optimization {'successful' if success else 'failed'}")
        else:
            # Optimize all tables
            print(f"Optimizing vector indexes for all tables using {args.index_type}...")
            results = optimizer.optimize_all_vector_tables(index_type=args.index_type)
            
            for table, success in results.items():
                print(f"{table}: {'Successful' if success else 'Failed'}")
    
    # Close database connection
    db_manager.disconnect()
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())