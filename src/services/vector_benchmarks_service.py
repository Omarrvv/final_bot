"""
Vector Search Benchmarking Utilities

This module provides tools to benchmark vector search performance in the database.
"""

import time
import logging
import statistics
import random
from typing import Dict, List, Any, Callable, Optional
import numpy as np

from src.utils.logger import get_logger
from src.services.postgres_database_service import PostgresqlDatabaseManager

logger = get_logger(__name__)

class VectorSearchBenchmark:
    """Benchmark utility for vector search operations."""
    
    def __init__(self, db_manager: PostgresqlDatabaseManager):
        """
        Initialize the benchmark utility.
        
        Args:
            db_manager: PostgreSQL database manager instance
        """
        self.db_manager = db_manager
        
    def generate_random_embedding(self, dimensions: int = 1536) -> List[float]:
        """
        Generate a random embedding vector for testing.
        
        Args:
            dimensions: Dimensionality of the embedding vector
            
        Returns:
            Random embedding vector
        """
        return list(np.random.rand(dimensions).astype(float))
    
    def run_benchmark(self, 
                     search_function: Callable, 
                     iterations: int = 10, 
                     table_name: str = None,
                     embedding_dimensions: int = 1536,
                     filters: Dict[str, Any] = None,
                     limit: int = 10) -> Dict[str, Any]:
        """
        Run a benchmark on a vector search function.
        
        Args:
            search_function: Function to benchmark
            iterations: Number of iterations to run
            table_name: Name of the table to search
            embedding_dimensions: Dimensionality of embedding vectors
            filters: Search filters to apply
            limit: Search result limit
            
        Returns:
            Dictionary with benchmark results
        """
        if filters is None:
            filters = {}
            
        timings = []
        result_counts = []
        
        for i in range(iterations):
            # Generate a random test embedding
            test_embedding = self.generate_random_embedding(embedding_dimensions)
            
            # Time the search operation
            start_time = time.time()
            
            # Call the search function with appropriate arguments based on its signature
            if table_name:
                results = search_function(table=table_name, 
                                         embedding=test_embedding,
                                         filters=filters,
                                         limit=limit)
            else:
                results = search_function(embedding=test_embedding,
                                         filters=filters,
                                         limit=limit)
            
            elapsed_time = time.time() - start_time
            
            # Record stats
            timings.append(elapsed_time)
            result_counts.append(len(results))
            
            logger.debug(f"Iteration {i+1}/{iterations}: {elapsed_time:.4f}s, {len(results)} results")
        
        # Calculate statistics
        avg_time = statistics.mean(timings)
        median_time = statistics.median(timings)
        min_time = min(timings)
        max_time = max(timings)
        std_dev = statistics.stdev(timings) if iterations > 1 else 0
        
        avg_results = statistics.mean(result_counts)
        
        results = {
            "avg_time": avg_time,
            "median_time": median_time,
            "min_time": min_time,
            "max_time": max_time,
            "std_dev": std_dev,
            "iterations": iterations,
            "avg_results": avg_results
        }
        
        logger.info(f"Benchmark results: {results}")
        return results
        
    def benchmark_all_vector_search(self, iterations: int = 5) -> Dict[str, Dict[str, Any]]:
        """
        Benchmark all vector search methods.
        
        Args:
            iterations: Number of iterations for each benchmark
            
        Returns:
            Dictionary with benchmark results for each method
        """
        results = {}
        
        # Benchmark attractions vector search
        results["attractions"] = self.run_benchmark(
            self.db_manager.vector_search_attractions,
            iterations=iterations
        )
        
        # Benchmark hotels vector search
        results["hotels"] = self.run_benchmark(
            self.db_manager.vector_search_hotels,
            iterations=iterations
        )
        
        # Benchmark restaurants vector search
        results["restaurants"] = self.run_benchmark(
            self.db_manager.vector_search_restaurants,
            iterations=iterations
        )
        
        # Benchmark cities vector search
        results["cities"] = self.run_benchmark(
            self.db_manager.vector_search_cities,
            iterations=iterations
        )
        
        # Benchmark hybrid search for each table
        for table in ["attractions", "hotels", "restaurants", "cities"]:
            results[f"hybrid_{table}"] = self.run_benchmark(
                self.db_manager.hybrid_search,
                iterations=iterations,
                table_name=table,
            )
        
        return results
    
    def generate_benchmark_report(self, results: Dict[str, Dict[str, Any]]) -> str:
        """
        Generate a readable benchmark report.
        
        Args:
            results: Benchmark results from benchmark_all_vector_search
            
        Returns:
            Formatted report string
        """
        report_lines = ["# Vector Search Performance Benchmark Report", ""]
        
        # Add a summary table
        report_lines.append("## Summary")
        report_lines.append("")
        report_lines.append("| Method | Avg Time (s) | Median Time (s) | Min Time (s) | Max Time (s) | Avg Results |")
        report_lines.append("|--------|-------------|----------------|-------------|-------------|------------|")
        
        for method_name, stats in results.items():
            report_lines.append(
                f"| {method_name} | {stats['avg_time']:.4f} | {stats['median_time']:.4f} | "
                f"{stats['min_time']:.4f} | {stats['max_time']:.4f} | {stats['avg_results']:.1f} |"
            )
        
        report_lines.append("")
        report_lines.append("## Detailed Results")
        
        for method_name, stats in results.items():
            report_lines.append(f"### {method_name}")
            report_lines.append(f"- Average Time: {stats['avg_time']:.4f} seconds")
            report_lines.append(f"- Median Time: {stats['median_time']:.4f} seconds")
            report_lines.append(f"- Min Time: {stats['min_time']:.4f} seconds")
            report_lines.append(f"- Max Time: {stats['max_time']:.4f} seconds")
            report_lines.append(f"- Standard Deviation: {stats['std_dev']:.4f} seconds")
            report_lines.append(f"- Iterations: {stats['iterations']}")
            report_lines.append(f"- Average Results: {stats['avg_results']:.1f}")
            report_lines.append("")
        
        return "\n".join(report_lines)

def main():
    """Run benchmarks as a standalone script."""
    # Connect to database
    db_uri = input("Enter PostgreSQL database URI (or press Enter for default): ")
    db_uri = db_uri.strip() if db_uri.strip() else None
    
    db_manager = PostgresqlDatabaseManager(database_uri=db_uri)
    benchmark = VectorSearchBenchmark(db_manager)
    
    # Number of iterations
    iterations = int(input("Number of benchmark iterations per method (default 5): ") or "5")
    
    print(f"Running vector search benchmarks with {iterations} iterations each...")
    results = benchmark.benchmark_all_vector_search(iterations=iterations)
    
    # Generate and save report
    report = benchmark.generate_benchmark_report(results)
    with open("vector_benchmark_report.md", "w") as f:
        f.write(report)
    
    print(f"Benchmark completed. Results saved to vector_benchmark_report.md")
    
    # Close database connection
    db_manager.disconnect()

if __name__ == "__main__":
    main()