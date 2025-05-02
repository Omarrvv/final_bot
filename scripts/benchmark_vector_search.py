import time
import random
import numpy as np
from src.knowledge.database import DatabaseManager

def benchmark_vector_search():
    """
    Benchmark vector search performance for different configurations.
    """
    db_manager = DatabaseManager()

    # Test configurations
    table_name = "attractions"
    dimensions = [128, 256, 512, 768, 1024, 1536]
    dataset_sizes = [100, 1000, 10000]
    num_queries = 10

    results = []

    for dim in dimensions:
        for size in dataset_sizes:
            # Generate random embeddings for testing
            embeddings = [np.random.rand(dim).tolist() for _ in range(size)]

            # Insert embeddings into the database (mocked for benchmarking)
            print(f"Benchmarking {dim}-dimensional vectors with dataset size {size}...")

            # Perform vector search
            query_times = []
            for _ in range(num_queries):
                query_embedding = random.choice(embeddings)
                start_time = time.time()
                db_manager.vector_search(table_name, query_embedding, limit=10)
                query_times.append(time.time() - start_time)

            avg_time = sum(query_times) / len(query_times)
            results.append({
                "dimension": dim,
                "dataset_size": size,
                "average_query_time": avg_time
            })

            print(f"Average query time for {dim}-dimensional vectors with dataset size {size}: {avg_time:.4f} seconds")

    # Print summary
    print("\nBenchmark Results:")
    for result in results:
        print(result)

if __name__ == "__main__":
    benchmark_vector_search()