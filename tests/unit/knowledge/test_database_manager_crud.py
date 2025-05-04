import pytest
from unittest.mock import MagicMock, patch, ANY
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import json
from src.knowledge.database import DatabaseManager
from src.utils.exceptions import DatabaseError

# Helper function to check if a string contains specific substrings
def mock_contains(*args):
    class StringContains:
        def __init__(self, *substrings):
            self.substrings = substrings

        def __eq__(self, other):
            if not isinstance(other, str):
                return False
            return all(substring in other for substring in self.substrings)

        def __repr__(self):
            return f"<String containing {self.substrings}>"

    return StringContains(*args)

# Sample data matching the PostgreSQL schema
# Columns: id, name_en, name_ar, description_en, description_ar, type, city, region, latitude, longitude, data
SAMPLE_ATTRACTION_ROW = {
    'id': 'attraction_123',
    'name_en': 'Pyramids',
    'name_ar': 'الأهرامات',
    'description_en': 'Ancient wonders',
    'description_ar': 'عجائب قديمة',
    'city': 'giza',
    'region': 'giza_region',
    'type': 'monument',
    'latitude': 29.9792,
    'longitude': 31.1342,
    'data': json.dumps({"rating": 4.5})
}


@pytest.fixture
def mock_db_connection():
    """Mock database connection and cursor."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None
    mock_cursor.fetchall.return_value = []
    # Mock description - PostgreSQL schema
    mock_cursor.description = [
        ('id',), ('name_en',), ('name_ar',), ('description_en',), ('description_ar',),
        ('type',), ('city',), ('region',), ('latitude',), ('longitude',), ('data',)
    ]
    return mock_conn, mock_cursor


@pytest.fixture
def db_manager(mock_db_connection):
    """Fixture for DatabaseManager instance with mocked connection."""
    mock_conn, mock_cursor = mock_db_connection

    # Mock table_exists to return True for required tables
    def mock_table_exists(_):
        return True

    # PostgreSQL: Use psycopg2 mocks or patch as needed
    with (
        patch.object(DatabaseManager, '_table_exists', side_effect=mock_table_exists) as _,
        patch('os.makedirs', return_value=None) as _
    ):
        # Create the DB manager with mocked connections
        db_manager = DatabaseManager(database_uri="postgresql://test:test@localhost:5432/test_db")

        # Replace the connection pool with our mock
        db_manager.pg_pool = MagicMock()
        db_manager.pg_pool.getconn.return_value = mock_conn

        # Mock execute_postgres_query to return our mock data
        def mock_execute_postgres_query(query, params=None, fetchall=True, cursor_factory=None):
            if "id = " in query and params and params[0] == "attraction_123":
                # Create a copy of the sample data with data as a JSON string for get_attraction
                result = SAMPLE_ATTRACTION_ROW.copy()
                if 'data' in result and isinstance(result['data'], str):
                    # Keep it as a string for the test
                    pass
                elif 'data' in result:
                    # Already parsed to dict by the get_attraction method
                    result['data'] = json.loads(result['data']) if isinstance(result['data'], str) else result['data']
                return result if not fetchall else [result]
            elif "id = " in query:
                return None if not fetchall else []
            elif "attractions" in query and "city" in query:
                return [SAMPLE_ATTRACTION_ROW]
            else:
                return []

        db_manager.execute_postgres_query = MagicMock(side_effect=mock_execute_postgres_query)

        yield db_manager

# --- Tests for Existing DatabaseManager Methods ---

def test_get_attraction_found(db_manager):
    """Test retrieving an attraction by ID when it exists."""
    attraction_id = "attraction_123"

    record = db_manager.get_attraction(attraction_id)

    assert record is not None
    assert isinstance(record, dict)
    assert record['id'] == attraction_id
    assert record['name_en'] == 'Pyramids'
    assert record['city'] == 'giza'
    # Data could be parsed as JSON or kept as string depending on the implementation
    if isinstance(record['data'], dict):
        assert record['data'] == {"rating": 4.5}
    else:
        assert record['data'] == '{"rating": 4.5}'

    # Verify execute_postgres_query was called
    db_manager.execute_postgres_query.assert_called()

    # Get the last call arguments
    call_args = db_manager.execute_postgres_query.call_args[0]
    query_str = call_args[0]
    params = call_args[1]

    # Check that the query contains the expected parts
    assert "SELECT" in query_str
    assert "FROM attractions" in query_str
    assert "WHERE id = %s" in query_str
    assert params == (attraction_id,)


def test_get_attraction_not_found(db_manager):
    """Test retrieving an attraction by ID when it does not exist."""
    attraction_id = "non_existent_id"

    record = db_manager.get_attraction(attraction_id)

    assert record is None

    # Verify execute_postgres_query was called
    db_manager.execute_postgres_query.assert_called()

    # Get the last call arguments
    call_args = db_manager.execute_postgres_query.call_args[0]
    query_str = call_args[0]
    params = call_args[1]

    # Check that the query contains the expected parts
    assert "SELECT" in query_str
    assert "FROM attractions" in query_str
    assert "WHERE id = %s" in query_str
    assert params == (attraction_id,)


def test_search_attractions_success(db_manager):
    """Test searching attractions successfully."""
    query = {"city": "Giza"}
    limit = 5
    offset = 0

    # Mock _build_postgres_where_clause to return a valid SQL query and parameters
    with patch.object(db_manager, '_build_postgres_where_clause', return_value=(
        "city = %s",
        ["Giza"]
    )):
        results = db_manager.search_attractions(query=query, limit=limit, offset=offset)

    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0]['id'] == SAMPLE_ATTRACTION_ROW['id']
    assert results[0]['city'] == 'giza'

    # Verify execute_postgres_query was called with the correct parameters
    db_manager.execute_postgres_query.assert_called()

    # Get the last call arguments
    call_args = db_manager.execute_postgres_query.call_args[0]
    query_str = call_args[0]

    # Check SQL execution
    assert 'SELECT' in query_str.upper()
    assert 'attractions' in query_str.lower()
    assert 'WHERE' in query_str.upper()
    assert 'LIMIT' in query_str.upper()
    assert 'OFFSET' in query_str.upper()


def test_search_attractions_no_results(db_manager):
    """Test searching attractions when no results are found."""
    query = {"city": "Nowhere"}
    limit = 5
    offset = 0

    # Override the mock to return empty results for this specific query
    def mock_execute_postgres_query_empty(query, params=None, fetchall=True, cursor_factory=None):
        if "attractions" in query and params and "Nowhere" in str(params):
            return []
        return db_manager.execute_postgres_query.side_effect(query, params, fetchall, cursor_factory)

    db_manager.execute_postgres_query.side_effect = mock_execute_postgres_query_empty

    # Mock _build_postgres_where_clause to return a valid SQL query and parameters
    with patch.object(db_manager, '_build_postgres_where_clause', return_value=(
        "city = %s",
        ["Nowhere"]
    )):
        results = db_manager.search_attractions(query=query, limit=limit, offset=offset)

    assert isinstance(results, list)
    assert len(results) == 0

    # Verify execute_postgres_query was called with the correct parameters
    db_manager.execute_postgres_query.assert_called()

    # Get the last call arguments
    call_args = db_manager.execute_postgres_query.call_args[0]
    params = call_args[1]

    # Check that the parameters include our search term
    assert any("Nowhere" in str(param) for param in params)

# Add more tests here for:
# get_restaurant, search_restaurants, get_accommodation, search_accommodations,
# search_practical_info, enhanced_search, log_analytics_event etc.
# Remember to adjust SAMPLE_DATA and mock_cursor.description for each table/query.