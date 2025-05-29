"""
Hybrid Search Utilities

This module provides enhanced hybrid search capabilities that combine vector similarity
with text-based searching for improved retrieval quality in the RAG pipeline.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Union
import numpy as np
from sklearn.preprocessing import MinMaxScaler

from src.utils.logger import get_logger
from src.utils.postgres_database import PostgresqlDatabaseManager

logger = get_logger(__name__)

class HybridSearchEngine:
    """
    Enhanced hybrid search engine that combines vector similarity with text search.
    Uses a weighted combination of vector similarity scores and text match scores.
    """

    def __init__(self, db_manager: PostgresqlDatabaseManager):
        """
        Initialize the hybrid search engine.

        Args:
            db_manager: PostgreSQL database manager instance
        """
        self.db_manager = db_manager
        self.default_text_weight = 0.3  # Default weight for text search component
        self.default_vector_weight = 0.7  # Default weight for vector search component

    def hybrid_search(
        self,
        query: str,
        table: str,
        embedding: List[float],
        text_fields: List[str] = None,
        filters: Dict[str, Any] = None,
        text_weight: float = None,
        vector_weight: float = None,
        limit: int = 10,
        min_text_score: float = 0.1
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining vector similarity with text search.

        Args:
            query: Text query string for text search component
            table: Table name to search
            embedding: Query vector embedding for vector similarity component
            text_fields: List of text fields to search in
            filters: Additional filters to apply
            text_weight: Weight for text search component (0.0 to 1.0)
            vector_weight: Weight for vector search component (0.0 to 1.0)
            limit: Maximum number of results to return
            min_text_score: Minimum text score for considering text matches

        Returns:
            List of results with combined scores
        """
        text_weight = text_weight if text_weight is not None else self.default_text_weight
        vector_weight = vector_weight if vector_weight is not None else self.default_vector_weight

        # Normalize weights to sum to 1.0
        total_weight = text_weight + vector_weight
        text_weight = text_weight / total_weight
        vector_weight = vector_weight / total_weight

        if filters is None:
            filters = {}

        # Default text fields if not provided
        if not text_fields:
            if table in ["attractions", "hotels", "restaurants"]:
                text_fields = ["name", "description"]
            elif table == "cities":
                text_fields = ["name", "description", "history"]
            else:
                # Generic fallback
                text_fields = ["name", "description"]

        logger.debug(f"Hybrid search on table '{table}' with weights: text={text_weight}, vector={vector_weight}")

        # Construct text search condition using tsvector
        text_conditions = []
        for field in text_fields:
            text_conditions.append(f"to_tsvector('english', {field}) @@ plainto_tsquery('english', %s)")

        text_search_condition = " OR ".join(text_conditions)

        # Calculate text search rank
        rank_expressions = []
        for field in text_fields:
            rank_expressions.append(f"ts_rank(to_tsvector('english', {field}), plainto_tsquery('english', %s))")

        text_rank = " + ".join(rank_expressions)

        # Construct filter conditions
        filter_conditions = []
        filter_params = []

        for key, value in filters.items():
            filter_conditions.append(f"{key} = %s")
            filter_params.append(value)

        # Combine all conditions
        where_clause = ""
        if text_search_condition and query:
            where_clause = f"({text_search_condition})"
            filter_params = [query] * len(text_fields) + filter_params

        if filter_conditions:
            if where_clause:
                where_clause += " AND "
            where_clause += " AND ".join(filter_conditions)

        if where_clause:
            where_clause = f"WHERE {where_clause}"

        # Vector distance calculation using HNSW index
        # Note: The HNSW index is automatically used when the <-> operator is used in ORDER BY
        vector_distance = f"embedding <-> %s as vector_distance"

        # Text rank calculation (only if query is provided)
        text_rank_calc = ""
        if query:
            text_rank_calc = f", ({text_rank}) as text_score"
            filter_params += [query] * len(text_fields)

        # Combined scoring function
        combined_score = f"(1.0 - (embedding <-> %s)) as vector_score"
        filter_params.append(embedding)

        # Set ef_search parameter for HNSW index (higher values = more accurate but slower)
        # This is set at query time and doesn't affect the index itself
        set_ef_search = "SET hnsw.ef_search = 100;"

        # Build the main query
        main_query = f"""
            SELECT *,
                {vector_distance},
                {combined_score}
                {text_rank_calc}
            FROM {table}
            {where_clause}
            ORDER BY
                CASE
                    WHEN {text_rank_calc != ""}
                    THEN ({vector_weight} * (1.0 - (embedding <-> %s))) +
                         ({text_weight} * GREATEST(({text_rank}), {min_text_score}))
                    ELSE (1.0 - (embedding <-> %s))
                END DESC
            LIMIT {limit}
        """

        # Combine the SET command with the main query
        query = f"{set_ef_search} {main_query}"

        # Add final vector parameters for the ORDER BY clause
        if text_rank_calc != "":
            filter_params.append(embedding)
            filter_params += [query] * len(text_fields)
            filter_params.append(embedding)
        else:
            filter_params.append(embedding)

        try:
            results = self.db_manager.execute_query(query, filter_params)

            # Post-process results to normalize scores
            if results and len(results) > 0:
                # Extract scores
                if "text_score" in results[0]:
                    text_scores = [result.get("text_score", 0) for result in results]
                    # Normalize text scores to 0-1 range if we have multiple scores
                    if len(text_scores) > 1 and max(text_scores) > min(text_scores):
                        scaler = MinMaxScaler()
                        normalized_text_scores = scaler.fit_transform(np.array(text_scores).reshape(-1, 1)).flatten()
                        for i, result in enumerate(results):
                            result["text_score_normalized"] = float(normalized_text_scores[i])
                    else:
                        # If all scores are the same, normalize to 0.5
                        for result in results:
                            result["text_score_normalized"] = 0.5 if result.get("text_score", 0) > 0 else 0

                # Calculate final combined scores
                for result in results:
                    vector_score = result.get("vector_score", 0)
                    text_score_norm = result.get("text_score_normalized", 0)

                    # Calculate combined score
                    result["combined_score"] = (vector_weight * vector_score +
                                              text_weight * text_score_norm)

            return results

        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            return []

    def multi_table_hybrid_search(
        self,
        query: str,
        embedding: List[float],
        tables: List[str] = None,
        limit_per_table: int = 5,
        text_weight: float = None,
        vector_weight: float = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search across multiple tables using hybrid search.

        Args:
            query: Text query string
            embedding: Query vector embedding
            tables: List of tables to search
            limit_per_table: Maximum results per table
            text_weight: Weight for text search component
            vector_weight: Weight for vector search component

        Returns:
            Dictionary of table names to search results
        """
        if tables is None:
            tables = ["attractions", "hotels", "restaurants", "cities"]

        results = {}

        for table in tables:
            table_results = self.hybrid_search(
                query=query,
                table=table,
                embedding=embedding,
                text_weight=text_weight,
                vector_weight=vector_weight,
                limit=limit_per_table
            )
            results[table] = table_results

        return results

    def optimize_hybrid_weights(
        self,
        table: str,
        sample_queries: List[str],
        embeddings: List[List[float]],
        relevant_ids: List[List[int]],
        vector_weights: List[float] = None
    ) -> Dict[str, Any]:
        """
        Find optimal weights for hybrid search using a set of sample queries.

        Args:
            table: Table to optimize for
            sample_queries: List of sample queries
            embeddings: List of query embeddings (one per query)
            relevant_ids: List of lists of relevant item IDs for each query
            vector_weights: List of vector weights to try

        Returns:
            Dictionary with optimization results
        """
        if vector_weights is None:
            vector_weights = [0.0, 0.2, 0.4, 0.5, 0.6, 0.8, 1.0]

        results = {}
        best_score = 0.0
        best_vector_weight = 0.5

        # Try different weight combinations
        for vector_weight in vector_weights:
            text_weight = 1.0 - vector_weight

            precision_at_k = []
            recall_at_k = []

            # Test each query
            for i, query in enumerate(sample_queries):
                hybrid_results = self.hybrid_search(
                    query=query,
                    table=table,
                    embedding=embeddings[i],
                    text_weight=text_weight,
                    vector_weight=vector_weight,
                    limit=10
                )

                # Calculate precision and recall
                result_ids = [r.get("id") for r in hybrid_results]
                relevant_for_query = set(relevant_ids[i])

                relevant_retrieved = len([rid for rid in result_ids if rid in relevant_for_query])
                precision = relevant_retrieved / len(result_ids) if result_ids else 0
                recall = relevant_retrieved / len(relevant_for_query) if relevant_for_query else 0

                precision_at_k.append(precision)
                recall_at_k.append(recall)

            # Calculate average metrics
            avg_precision = sum(precision_at_k) / len(precision_at_k) if precision_at_k else 0
            avg_recall = sum(recall_at_k) / len(recall_at_k) if recall_at_k else 0

            # Calculate F1 score
            f1_score = 2 * (avg_precision * avg_recall) / (avg_precision + avg_recall) if (avg_precision + avg_recall) > 0 else 0

            results[f"vector_{vector_weight}_text_{text_weight}"] = {
                "precision": avg_precision,
                "recall": avg_recall,
                "f1": f1_score
            }

            # Track best weights
            if f1_score > best_score:
                best_score = f1_score
                best_vector_weight = vector_weight

        # Set class defaults to the best weights
        self.default_vector_weight = best_vector_weight
        self.default_text_weight = 1.0 - best_vector_weight

        return {
            "best_vector_weight": best_vector_weight,
            "best_text_weight": 1.0 - best_vector_weight,
            "best_f1_score": best_score,
            "all_results": results
        }

def main():
    """Run hybrid search tests as a standalone script."""
    import argparse
    import json
    import time

    parser = argparse.ArgumentParser(description="Test hybrid search functionality")
    parser.add_argument("--uri", help="PostgreSQL database URI", default=None)
    parser.add_argument("--query", help="Test query to search for", required=True)
    parser.add_argument("--table", help="Table to search", default="attractions")
    parser.add_argument("--limit", type=int, help="Number of results to return", default=10)
    parser.add_argument("--text-weight", type=float, help="Text search weight (0-1)", default=0.3)
    args = parser.parse_args()

    try:
        from src.utils.embedding import get_embedding
        # Generate embedding for the query
        embedding = get_embedding(args.query)

        # Connect to database and run search
        db_manager = PostgresqlDatabaseManager(database_uri=args.uri)
        search_engine = HybridSearchEngine(db_manager)

        start_time = time.time()
        results = search_engine.hybrid_search(
            query=args.query,
            table=args.table,
            embedding=embedding,
            text_weight=args.text_weight,
            vector_weight=1.0 - args.text_weight,
            limit=args.limit
        )
        elapsed_time = time.time() - start_time

        # Print results
        print(f"Query: '{args.query}'")
        print(f"Found {len(results)} results in {elapsed_time:.4f} seconds")
        print("\nResults:")

        for i, result in enumerate(results):
            print(f"\n{i+1}. {result.get('name', 'Unnamed')}")

            # Print scores
            vector_score = result.get("vector_score", 0)
            text_score = result.get("text_score", 0)
            combined_score = result.get("combined_score", 0)

            print(f"   Vector Score: {vector_score:.4f}")
            print(f"   Text Score: {text_score:.4f}")
            print(f"   Combined Score: {combined_score:.4f}")

            # Print snippet of description
            description = result.get("description", "")
            if description:
                snippet = description[:150] + "..." if len(description) > 150 else description
                print(f"   Description: {snippet}")

        # Close database connection
        db_manager.disconnect()

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()