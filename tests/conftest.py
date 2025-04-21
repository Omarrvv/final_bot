"""
Pytest configuration file for Egypt Tourism Chatbot tests.
"""

import os
import json
import pytest
from pathlib import Path
from .setup_test_env import setup_test_environment, cleanup_test_environment
from fastapi.testclient import TestClient

# Global variable to store temporary directory
_TEMP_TEST_DIR = None

def pytest_sessionstart(session):
    """
    Called before test session starts.
    Set up the global test environment.
    """
    global _TEMP_TEST_DIR
    _TEMP_TEST_DIR = setup_test_environment()
    
    # Save the test directory path to a temp file for reference
    with open(".test_dir_path", "w") as f:
        f.write(_TEMP_TEST_DIR)
    
    print(f"\nTest environment set up in: {_TEMP_TEST_DIR}\n")

def pytest_sessionfinish(session, exitstatus):
    """
    Called after whole test run finished.
    Clean up the test environment.
    """
    global _TEMP_TEST_DIR
    if _TEMP_TEST_DIR:
        cleanup_test_environment(_TEMP_TEST_DIR)
        _TEMP_TEST_DIR = None
        
        # Remove the temp file
        if os.path.exists(".test_dir_path"):
            os.unlink(".test_dir_path")
    
    print("\nTest environment cleaned up.\n")

@pytest.fixture
def test_temp_dir():
    """
    Fixture to provide test directory path to tests.
    """
    global _TEMP_TEST_DIR
    return _TEMP_TEST_DIR

@pytest.fixture
def mock_env_vars():
    """
    Fixture to provide access to the test environment variables.
    """
    env_vars = {
        "CONTENT_PATH": os.environ.get("CONTENT_PATH"),
        "DATABASE_URI": os.environ.get("DATABASE_URI"),
        "SESSION_STORAGE_URI": os.environ.get("SESSION_STORAGE_URI"),
        "VECTOR_DB_URI": os.environ.get("VECTOR_DB_URI"),
        "JWT_SECRET": "***", # Hidden for security
        "API_HOST": os.environ.get("API_HOST"),
        "API_PORT": os.environ.get("API_PORT"),
        "FRONTEND_URL": os.environ.get("FRONTEND_URL"),
        "USE_NEW_KB": os.environ.get("USE_NEW_KB"),
        "USE_NEW_API": os.environ.get("USE_NEW_API"),
        "USE_POSTGRES": os.environ.get("USE_POSTGRES"),
        "USE_REDIS": os.environ.get("USE_REDIS"),
    }
    return env_vars

# --- Add FastAPI App and Async Client Fixtures --- 

@pytest.fixture
def app():
    """Fixture to provide the FastAPI app instance."""
    # Ensure dependencies are loaded *after* test environment setup if needed
    from src.main import app as fastapi_app # Use alias
    return fastapi_app

@pytest.fixture
def client(app): 
    """Provides a FastAPI TestClient instance that handles lifespan."""
    # TestClient handles startup/shutdown (lifespan) automatically
    with TestClient(app) as test_client:
        yield test_client

# --- Minimal App Fixtures for Debugging --- #
from fastapi import FastAPI as MinimalFastAPI # Use alias to avoid confusion

@pytest.fixture
def minimal_app():
    """A minimal FastAPI app for basic fixture testing."""
    app = MinimalFastAPI()
    @app.get("/ping")
    async def _minimal_ping():
        return {"ping": "pong"}
    return app

@pytest.fixture
async def minimal_client(minimal_app):
    """Async client for the minimal FastAPI app."""
    from httpx import AsyncClient
    async with AsyncClient(app=minimal_app, base_url="http://test") as client:
        yield client