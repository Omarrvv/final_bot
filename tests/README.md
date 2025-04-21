# Egypt Tourism Chatbot - Testing

This directory contains tests for the Egypt Tourism Chatbot application.

## Test Structure

- `tests/unit/`: Unit tests for individual components
- `tests/integration/`: Integration tests for component interactions
- `tests/test_framework.py`: Test utilities and base classes
- `tests/setup_test_env.py`: Environment setup for tests
- `tests/conftest.py`: Pytest configuration and fixtures

## Running Tests

### Prerequisites

Ensure all dependencies are installed:

```bash
pip install -r requirements.txt
pip install pytest pytest-cov pytest-asyncio
```

### Running All Tests

To run the entire test suite:

```bash
pytest tests/
```

### Running With Coverage

To run tests with coverage reporting:

```bash
pytest --cov=src tests/
```

For a detailed HTML coverage report:

```bash
pytest --cov=src --cov-report=html tests/
```

The HTML report will be available in the `htmlcov/` directory.

### Running Specific Tests

To run a specific test file:

```bash
pytest tests/test_settings.py
```

To run a specific test:

```bash
pytest tests/test_settings.py::TestSettings::test_settings_load
```

## Test Environment

Tests run in an isolated environment with:

- Temporary directories for data
- Test-specific environment variables
- SQLite test database
- File-based session storage
- Mock external services

The environment is automatically set up by `conftest.py` and cleaned up after tests complete.

## Adding New Tests

1. Create a new test file in the appropriate directory
2. Import necessary components and base classes
3. Use `pytest` fixtures defined in `conftest.py` if needed
4. Follow existing test patterns for consistency

## Troubleshooting

If you encounter import errors:

- Ensure `PYTHONPATH` includes the project root
- Check that `tests/__init__.py` correctly adds the project root to `sys.path`
- Verify environment variables are set correctly

For database-related errors:

- Check if test database is properly initialized
- Ensure `DatabaseManager` handles test URIs correctly
- Verify test data is created in `setup_test_env.py`

## Continuous Integration

Tests run automatically on GitHub Actions on:

- Pull requests to main/develop branches
- Pushes to main/develop branches

See `.github/workflows/ci.yml` for the CI configuration.
