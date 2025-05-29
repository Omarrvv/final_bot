"""
Tests for query optimization tools.

This module contains tests for the QueryAnalyzer and QueryBatch classes.
"""
import json
import pytest
from unittest.mock import MagicMock, patch

from src.utils.query_analyzer import QueryAnalyzer
from src.utils.query_batch import QueryBatch

class TestQueryAnalyzer:
    """Test suite for the QueryAnalyzer class."""

    @pytest.fixture
    def query_analyzer(self):
        """Create a QueryAnalyzer instance."""
        return QueryAnalyzer(
            slow_query_threshold_ms=500,
            max_queries_to_track=100
        )

    @pytest.fixture
    def mock_db_manager(self):
        """Create a mock database manager."""
        db_manager = MagicMock()
        db_manager.execute_postgres_query.return_value = {
            'QUERY PLAN': [
                {
                    'Plan': {
                        'Node Type': 'Seq Scan',
                        'Relation Name': 'attractions',
                        'Plan Rows': 1500,
                        'Total Cost': 100.0
                    },
                    'Planning Time': 0.5,
                    'Execution Time': 10.0
                }
            ]
        }
        return db_manager

    def test_init(self, query_analyzer):
        """Test initialization."""
        assert query_analyzer.slow_query_threshold_ms == 500
        assert query_analyzer.max_queries_to_track == 100
        assert isinstance(query_analyzer.query_stats, dict)
        assert isinstance(query_analyzer.slow_queries, list)
        assert isinstance(query_analyzer.query_plans, dict)

    def test_record_query(self, query_analyzer):
        """Test recording a query."""
        query_analyzer.record_query(
            query="SELECT * FROM attractions WHERE id = %s",
            params=("test_id",),
            duration_ms=100.0,
            rows_affected=1
        )

        # Check that the query was recorded
        normalized_query = "SELECT * FROM attractions WHERE id = %s"
        assert normalized_query in query_analyzer.query_stats
        assert len(query_analyzer.query_stats[normalized_query]) == 1
        assert query_analyzer.query_stats[normalized_query][0]["duration_ms"] == 100.0
        assert query_analyzer.query_stats[normalized_query][0]["rows_affected"] == 1

        # Check that it wasn't recorded as a slow query
        assert len(query_analyzer.slow_queries) == 0

        # Record a slow query
        query_analyzer.record_query(
            query="SELECT * FROM attractions",
            params=(),
            duration_ms=600.0,
            rows_affected=100
        )

        # Check that it was recorded as a slow query
        assert len(query_analyzer.slow_queries) == 1
        assert query_analyzer.slow_queries[0]["query"] == "SELECT * FROM attractions"
        assert query_analyzer.slow_queries[0]["duration_ms"] == 600.0

    def test_get_slow_queries(self, query_analyzer):
        """Test getting slow queries."""
        # Record some queries
        query_analyzer.record_query(
            query="SELECT * FROM attractions WHERE id = %s",
            params=("test_id",),
            duration_ms=600.0,
            rows_affected=1
        )

        query_analyzer.record_query(
            query="SELECT * FROM restaurants",
            params=(),
            duration_ms=700.0,
            rows_affected=100
        )

        # Get slow queries
        slow_queries = query_analyzer.get_slow_queries()

        # Check that they are sorted by duration
        assert len(slow_queries) == 2
        assert slow_queries[0]["query"] == "SELECT * FROM restaurants"
        assert slow_queries[0]["duration_ms"] == 700.0
        assert slow_queries[1]["query"] == "SELECT * FROM attractions WHERE id = %s"
        assert slow_queries[1]["duration_ms"] == 600.0

    def test_get_query_stats(self, query_analyzer):
        """Test getting query statistics."""
        # Record some queries
        for i in range(5):
            query_analyzer.record_query(
                query="SELECT * FROM attractions WHERE id = %s",
                params=("test_id",),
                duration_ms=100.0 + i * 10,
                rows_affected=1
            )

        # Get stats for a specific query
        stats = query_analyzer.get_query_stats("SELECT * FROM attractions WHERE id = %s")

        # Check the stats
        assert stats["count"] == 5
        assert stats["avg_duration_ms"] == 120.0
        assert stats["min_duration_ms"] == 100.0
        assert stats["max_duration_ms"] == 140.0

        # Get stats for all queries
        all_stats = query_analyzer.get_query_stats()

        # Check that the query is in the stats
        assert "SELECT * FROM attractions WHERE id = %s" in all_stats

    def test_analyze_query_plan(self, query_analyzer, mock_db_manager):
        """Test analyzing a query plan."""
        # Analyze a query plan
        plan_info = query_analyzer.analyze_query_plan(
            mock_db_manager,
            "SELECT * FROM attractions WHERE id = %s",
            ("test_id",)
        )

        # Check the plan info
        assert "plan" in plan_info
        assert "analysis" in plan_info
        assert plan_info["plan"] == mock_db_manager.execute_postgres_query.return_value["QUERY PLAN"]

        # Check that the plan was cached
        assert "SELECT * FROM attractions WHERE id = %s" in query_analyzer.query_plans

    def test_suggest_indexes(self, query_analyzer, mock_db_manager):
        """Test suggesting indexes."""
        # Record a slow query
        query_analyzer.record_query(
            query="SELECT * FROM attractions WHERE type_id = %s",
            params=("museum",),
            duration_ms=600.0,
            rows_affected=100
        )

        # Mock the analyze_query_plan method
        query_analyzer.analyze_query_plan = MagicMock(return_value={
            "plan": [
                {
                    "Plan": {
                        "Node Type": "Seq Scan",
                        "Relation Name": "attractions",
                        "Filter": "type_id = 'museum'",
                        "Plan Rows": 1500,
                        "Total Cost": 100.0
                    }
                }
            ],
            "analysis": {
                "issues": ["Sequential scan on potentially large table: attractions"],
                "recommendations": ["Consider adding an index on attractions for the columns used in the WHERE clause"]
            }
        })

        # Get index suggestions
        suggestions = query_analyzer.suggest_indexes(mock_db_manager)

        # Check the suggestions
        assert "attractions" in suggestions
        assert any("CREATE INDEX" in suggestion and "type_id" in suggestion for suggestion in suggestions["attractions"])


class TestQueryBatch:
    """Test suite for the QueryBatch class."""

    @pytest.fixture
    def mock_db_manager(self):
        """Create a mock database manager."""
        db_manager = MagicMock()
        db_manager._get_pg_connection.return_value = MagicMock()
        return db_manager

    @pytest.fixture
    def query_batch(self, mock_db_manager):
        """Create a QueryBatch instance."""
        return QueryBatch(
            db_manager=mock_db_manager,
            batch_size=100,
            auto_execute=False
        )

    def test_init(self, query_batch, mock_db_manager):
        """Test initialization."""
        assert query_batch.db_manager == mock_db_manager
        assert query_batch.batch_size == 100
        assert query_batch.auto_execute is False
        assert isinstance(query_batch.inserts, dict)
        assert isinstance(query_batch.updates, dict)
        assert isinstance(query_batch.deletes, dict)
        assert isinstance(query_batch.custom_batches, dict)

    def test_add_insert(self, query_batch):
        """Test adding an insert operation."""
        # Add an insert operation
        query_batch.add_insert(
            table="attractions",
            data={"id": "test_id", "name": "Test Attraction"}
        )

        # Check that the operation was added
        assert "attractions" in query_batch.inserts
        assert len(query_batch.inserts["attractions"]) == 1
        assert query_batch.inserts["attractions"][0]["id"] == "test_id"
        assert query_batch.inserts["attractions"][0]["name"] == "Test Attraction"

    def test_add_update(self, query_batch):
        """Test adding an update operation."""
        # Add an update operation
        query_batch.add_update(
            table="attractions",
            record_id="test_id",
            data={"name": "Updated Attraction"}
        )

        # Check that the operation was added
        assert "attractions" in query_batch.updates
        assert len(query_batch.updates["attractions"]) == 1
        assert query_batch.updates["attractions"][0][0] == "test_id"
        assert query_batch.updates["attractions"][0][1]["name"] == "Updated Attraction"

    def test_add_delete(self, query_batch):
        """Test adding a delete operation."""
        # Add a delete operation
        query_batch.add_delete(
            table="attractions",
            record_id="test_id"
        )

        # Check that the operation was added
        assert "attractions" in query_batch.deletes
        assert len(query_batch.deletes["attractions"]) == 1
        assert query_batch.deletes["attractions"][0] == "test_id"

    def test_add_custom(self, query_batch):
        """Test adding a custom operation."""
        # Add a custom operation
        query_batch.add_custom(
            batch_name="test_batch",
            item={"id": "test_id", "name": "Test Item"}
        )

        # Check that the operation was added
        assert "test_batch" in query_batch.custom_batches
        assert len(query_batch.custom_batches["test_batch"]) == 1
        assert query_batch.custom_batches["test_batch"][0]["id"] == "test_id"
        assert query_batch.custom_batches["test_batch"][0]["name"] == "Test Item"

    def test_execute_inserts(self, query_batch, mock_db_manager):
        """Test executing insert operations."""
        # Add some insert operations
        query_batch.add_insert(
            table="attractions",
            data={"id": "test_id1", "name": "Test Attraction 1"}
        )

        query_batch.add_insert(
            table="attractions",
            data={"id": "test_id2", "name": "Test Attraction 2"}
        )

        # Mock the execute_values function
        with patch('src.utils.query_batch.execute_values') as mock_execute_values:
            # Execute the inserts
            result = query_batch.execute_inserts("attractions")

            # Check the result
            assert result is True

            # Check that execute_values was called
            assert mock_execute_values.called

        # Check that the batch was cleared
        assert len(query_batch.inserts["attractions"]) == 0

    def test_execute_updates(self, query_batch, mock_db_manager):
        """Test executing update operations."""
        # Add some update operations
        query_batch.add_update(
            table="attractions",
            record_id="test_id1",
            data={"name": "Updated Attraction 1"}
        )

        query_batch.add_update(
            table="attractions",
            record_id="test_id2",
            data={"name": "Updated Attraction 2"}
        )

        # Execute the updates
        result = query_batch.execute_updates("attractions")

        # Check the result
        assert result is True

        # Check that the batch was cleared
        assert len(query_batch.updates["attractions"]) == 0

    def test_execute_deletes(self, query_batch, mock_db_manager):
        """Test executing delete operations."""
        # Add some delete operations
        query_batch.add_delete(
            table="attractions",
            record_id="test_id1"
        )

        query_batch.add_delete(
            table="attractions",
            record_id="test_id2"
        )

        # Execute the deletes
        result = query_batch.execute_deletes("attractions")

        # Check the result
        assert result is True

        # Check that the batch was cleared
        assert len(query_batch.deletes["attractions"]) == 0

    def test_execute_custom(self, query_batch):
        """Test executing custom operations."""
        # Add some custom operations
        query_batch.add_custom(
            batch_name="test_batch",
            item={"id": "test_id1", "name": "Test Item 1"}
        )

        query_batch.add_custom(
            batch_name="test_batch",
            item={"id": "test_id2", "name": "Test Item 2"}
        )

        # Create a processor function
        processor = MagicMock(return_value=True)

        # Execute the custom batch
        result = query_batch.execute_custom("test_batch", processor)

        # Check the result
        assert result is True

        # Check that the processor was called with the batch items
        processor.assert_called_once()
        assert len(processor.call_args[0][0]) == 2

        # Check that the batch was cleared
        assert len(query_batch.custom_batches["test_batch"]) == 0

    def test_execute_all(self, query_batch):
        """Test executing all operations."""
        # Add some operations
        query_batch.add_insert(
            table="attractions",
            data={"id": "test_id1", "name": "Test Attraction 1"}
        )

        query_batch.add_update(
            table="restaurants",
            record_id="test_id1",
            data={"name": "Updated Restaurant 1"}
        )

        query_batch.add_delete(
            table="cities",
            record_id="test_id1"
        )

        # Mock the execute methods
        query_batch.execute_inserts = MagicMock(return_value=True)
        query_batch.execute_updates = MagicMock(return_value=True)
        query_batch.execute_deletes = MagicMock(return_value=True)

        # Execute all operations
        result = query_batch.execute_all()

        # Check the result
        assert result is True

        # Check that the execute methods were called
        query_batch.execute_inserts.assert_called_once_with("attractions")
        query_batch.execute_updates.assert_called_once_with("restaurants")
        query_batch.execute_deletes.assert_called_once_with("cities")

    def test_clear(self, query_batch):
        """Test clearing all operations."""
        # Add some operations
        query_batch.add_insert(
            table="attractions",
            data={"id": "test_id1", "name": "Test Attraction 1"}
        )

        query_batch.add_update(
            table="restaurants",
            record_id="test_id1",
            data={"name": "Updated Restaurant 1"}
        )

        query_batch.add_delete(
            table="cities",
            record_id="test_id1"
        )

        # Clear all operations
        query_batch.clear()

        # Check that all batches were cleared
        assert len(query_batch.inserts) == 0
        assert len(query_batch.updates) == 0
        assert len(query_batch.deletes) == 0
        assert len(query_batch.custom_batches) == 0

    def test_context_manager(self, query_batch):
        """Test using the query batch as a context manager."""
        # Mock the execute_all method
        query_batch.execute_all = MagicMock(return_value=True)

        # Use the query batch as a context manager
        with query_batch:
            query_batch.add_insert(
                table="attractions",
                data={"id": "test_id1", "name": "Test Attraction 1"}
            )

        # Check that execute_all was called
        query_batch.execute_all.assert_called_once()
