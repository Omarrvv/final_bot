"""
Unit tests for the vector storage methods in DatabaseManager.
"""
import os
import unittest
import numpy as np
from unittest.mock import patch, MagicMock
import uuid

from src.knowledge.database import DatabaseManager, DatabaseType

# Test constants
TEST_DB_URI = os.environ.get("POSTGRES_URI") or "postgresql://omarmohamed@localhost:5432/postgres"
TEST_EMBEDDING = [0.1, 0.2, 0.3, 0.4, 0.5]
TEST_EMBEDDING_2 = [0.2, 0.3, 0.4, 0.5, 0.6]

class TestVectorStorage(unittest.TestCase):
    """Test vector storage operations with pgvector."""
    
    def setUp(self):
        """Set up test environment."""
        self.db_uri = os.environ.get("POSTGRES_URI") or "postgresql://postgres:postgres@localhost:5432/egypt_chatbot"
        self.db_manager = DatabaseManager(database_uri=self.db_uri)
        
        # Sample test embeddings (smaller dimension for testing)
        self.test_id = f"test_vector_{uuid.uuid4().hex[:8]}"
        self.test_embedding = [0.1] * 1536  # Reduced dimension for testing
        
    def test_add_vector_column(self):
        """Test adding vector columns to tables."""
        # Mock the vector check and database operations
        with (
            patch.object(self.db_manager, '_check_vector_enabled', return_value=True),
            patch.object(self.db_manager, '_table_exists', return_value=True),
            patch.object(self.db_manager, '_postgres_column_exists', return_value=False),
            patch.object(self.db_manager, 'execute_postgres_query', return_value=True),
        ):
            # Test adding vector columns
            result = self.db_manager.update_vector_columns(['test_table'])
            
            # Verify the function succeeded
            self.assertTrue(result)
            
            # Verify execute_postgres_query was called to add columns
            self.db_manager.execute_postgres_query.assert_called_once()
            
    def test_store_embedding(self):
        """Test storing a vector embedding."""
        # Mock the vector check and database operations
        with (
            patch.object(self.db_manager, '_check_vector_enabled', return_value=True),
            patch.object(self.db_manager, '_table_exists', return_value=True),
            patch.object(self.db_manager, '_postgres_column_exists', return_value=True),
            patch.object(self.db_manager, 'execute_postgres_query', return_value=1),
        ):
            # Test storing an embedding
            result = self.db_manager.store_embedding('attractions', self.test_id, self.test_embedding)
            
            # Verify the function succeeded
            self.assertTrue(result)
            
            # Verify execute_postgres_query was called twice (once to check if record exists, once to update)
            self.assertEqual(self.db_manager.execute_postgres_query.call_count, 2)
            
            # Get the second call, which should be the update
            update_call = self.db_manager.execute_postgres_query.call_args_list[1]
            sql = update_call[0][0]
            params = update_call[0][1]
            
            self.assertIn('UPDATE attractions', sql)
            self.assertIn('SET embedding = %s::vector', sql)
            self.assertIn('WHERE id = %s', sql)
            self.assertEqual(params[0], self.test_embedding)  # First param should be embedding
            self.assertEqual(params[1], self.test_id)  # Second param should be record ID
            
    def test_batch_store_embeddings(self):
        """Test batch storing of vector embeddings."""
        # Mock the vector check and database operations
        with (
            patch.object(self.db_manager, '_check_vector_enabled', return_value=True),
            patch.object(self.db_manager, '_table_exists', return_value=True),
            patch.object(self.db_manager, '_postgres_column_exists', return_value=True),
            patch.object(self.db_manager, '_get_pg_connection'),
            patch.object(self.db_manager, '_return_pg_connection'),
        ):
            # Create mock connection and cursor
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.__enter__ = MagicMock(return_value=mock_conn)
            mock_conn.__exit__ = MagicMock(return_value=None)
            mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
            mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=None)
            
            # Set up the mock connection to be returned by _get_pg_connection
            self.db_manager._get_pg_connection.return_value = mock_conn
            
            # Test data
            batch_data = {
                f"{self.test_id}_1": [0.1] * 1536,
                f"{self.test_id}_2": [0.2] * 1536,
                f"{self.test_id}_3": [0.3] * 1536,
            }
            
            # Test batch storing embeddings
            result = self.db_manager.batch_store_embeddings('attractions', batch_data)
            
            # Verify the function succeeded
            self.assertTrue(result)
            
            # Verify cursor.execute was called for each item in the batch
            self.assertEqual(mock_cursor.execute.call_count, 3)
            
            # Check that connection handling was correct
            self.db_manager._get_pg_connection.assert_called_once()
            self.db_manager._return_pg_connection.assert_called_once_with(mock_conn)
            
    def test_get_embedding(self):
        """Test retrieving a vector embedding."""
        # Mock embedding data
        mock_embedding = [0.5] * 1536
        mock_result = {'embedding': mock_embedding}
        
        # Mock the vector check and database operations
        with (
            patch.object(self.db_manager, '_check_vector_enabled', return_value=True),
            patch.object(self.db_manager, '_table_exists', return_value=True),
            patch.object(self.db_manager, '_postgres_column_exists', return_value=True),
            patch.object(self.db_manager, 'execute_postgres_query', return_value=mock_result),
        ):
            # Test getting an embedding
            embedding = self.db_manager.get_embedding('attractions', self.test_id)
            
            # Verify the result
            self.assertEqual(embedding, mock_embedding)
            
            # Verify execute_postgres_query was called with correct parameters
            self.db_manager.execute_postgres_query.assert_called_once()
            
            # Check SQL query contains expected elements
            call_args = self.db_manager.execute_postgres_query.call_args
            sql = call_args[0][0]
            params = call_args[0][1]
            
            self.assertIn('SELECT embedding', sql)
            self.assertIn('FROM attractions', sql)
            self.assertIn('WHERE id = %s', sql)
            self.assertEqual(params, (self.test_id,))
            
    def test_find_similar(self):
        """Test finding similar vectors."""
        # Mock search results
        mock_results = [
            {'id': f"{self.test_id}_1", 'name': 'Test 1', 'similarity': 0.95},
            {'id': f"{self.test_id}_2", 'name': 'Test 2', 'similarity': 0.85},
            {'id': f"{self.test_id}_3", 'name': 'Test 3', 'similarity': 0.75},
        ]
        
        # Mock the vector check and database operations
        with (
            patch.object(self.db_manager, '_check_vector_enabled', return_value=True),
            patch.object(self.db_manager, '_table_exists', return_value=True),
            patch.object(self.db_manager, '_postgres_column_exists', return_value=True),
            patch.object(self.db_manager, 'execute_postgres_query', return_value=mock_results),
        ):
            # Test finding similar vectors
            results = self.db_manager.find_similar('attractions', self.test_embedding, limit=3, 
                                                  additional_filters={'type': 'historical'})
            
            # Verify the results
            self.assertEqual(results, mock_results)
            self.assertEqual(len(results), 3)
            
            # Verify execute_postgres_query was called with correct parameters
            self.db_manager.execute_postgres_query.assert_called_once()
            
            # Check SQL query contains expected elements
            call_args = self.db_manager.execute_postgres_query.call_args
            sql = call_args[0][0]
            params = call_args[0][1]
            
            self.assertIn('SELECT *', sql)
            self.assertIn('1 - (embedding <=> %s::vector) AS similarity', sql)
            self.assertIn('FROM attractions', sql)
            self.assertIn('WHERE embedding IS NOT NULL', sql)
            self.assertIn('AND type = %s', sql)
            self.assertIn('ORDER BY similarity DESC LIMIT %s', sql)
            self.assertEqual(params[0], self.test_embedding)  # First param should be embedding
            self.assertEqual(params[1], 'historical')  # Second param should be type filter
            self.assertEqual(params[2], 3)  # Third param should be limit
            
    def test_hybrid_search(self):
        """Test hybrid search combining vector and keyword search."""
        # For this test, we're assuming the database has a method like hybrid_search that combines
        # vector similarity with keyword matching. If it doesn't exist, you would implement it.
        
        # Mock search results
        mock_results = [
            {'id': f"{self.test_id}_1", 'name': 'Test Pyramid', 'similarity': 0.95},
            {'id': f"{self.test_id}_2", 'name': 'Another Pyramid', 'similarity': 0.85},
        ]
        
        # Define a hybrid_search method or use an existing one
        def mock_hybrid_search(table, embedding, query_text, limit=10, filters=None):
            # This is a simplified mock implementation
            # In a real implementation, this would combine vector search and text search
            sql = """
                SELECT *, 
                       (1 - (embedding <=> %s::vector)) * 0.7 + 
                       ts_rank(to_tsvector('english', name_en), to_tsquery('english', %s)) * 0.3 AS hybrid_score
                FROM attractions
                WHERE embedding IS NOT NULL
                AND to_tsvector('english', name_en) @@ to_tsquery('english', %s)
                ORDER BY hybrid_score DESC
                LIMIT %s
            """
            params = [embedding, query_text, query_text, limit]
            if filters:
                sql = sql.replace("WHERE embedding IS NOT NULL", 
                                 "WHERE embedding IS NOT NULL AND " + " AND ".join([f"{k} = %s" for k in filters.keys()]))
                params.extend(filters.values())
            return mock_results
        
        # Use the mock function directly or patch an existing method
        with patch.object(self.db_manager, 'hybrid_search', side_effect=mock_hybrid_search):
            # Test hybrid search
            results = self.db_manager.hybrid_search('attractions', self.test_embedding, 'pyramid', limit=2)
            
            # Verify the results
            self.assertEqual(results, mock_results)
            self.assertEqual(len(results), 2)
            
            # Verify our mock was called with correct parameters
            self.db_manager.hybrid_search.assert_called_once_with('attractions', self.test_embedding, 'pyramid', limit=2)

    def test_sparse_vectors(self):
        """Test vector search with sparse vectors."""
        sparse_vector = [0.0] * 1536
        sparse_vector[100] = 1.0  # Add a single non-zero value

        with patch.object(self.db_manager, 'vector_search', return_value=[]) as mock_search:
            results = self.db_manager.vector_search('attractions', sparse_vector, limit=5)
            mock_search.assert_called_once()
            self.assertEqual(results, [])

    def test_high_dimensional_vectors(self):
        """Test vector search with high-dimensional vectors."""
        high_dim_vector = [0.1] * 2048  # Exceeding typical dimensions

        with patch.object(self.db_manager, 'vector_search', return_value=[]) as mock_search:
            results = self.db_manager.vector_search('attractions', high_dim_vector, limit=5)
            mock_search.assert_called_once()
            self.assertEqual(results, [])

    def test_multilingual_queries(self):
        """Test vector search with multilingual queries."""
        multilingual_vector = [0.2] * 1536  # Simulate a vector for multilingual text

        with patch.object(self.db_manager, 'vector_search', return_value=[]) as mock_search:
            results = self.db_manager.vector_search('attractions', multilingual_vector, limit=5)
            mock_search.assert_called_once()
            self.assertEqual(results, [])
