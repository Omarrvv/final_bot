#!/usr/bin/env python3
"""
Test script for verifying the chatbot works with session-based approach without authentication.
"""
import os
import sys
import json
import asyncio
import uuid
import logging
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the FastAPI app
from src.main import app
from fastapi.testclient import TestClient

# Create a test client
client = TestClient(app)

def test_session_based_approach():
    """Test the session-based approach without authentication."""
    logger.info("Testing session-based approach without authentication...")
    
    # Step 1: Get a new session
    reset_response = client.post("/api/reset", json={"create_new": True})
    assert reset_response.status_code == 200, f"Failed to create session: {reset_response.text}"
    
    session_data = reset_response.json()
    session_id = session_data.get("session_id")
    
    logger.info(f"Created new session: {session_id}")
    assert session_id is not None, "Session ID is missing in response"
    
    # Step 2: Send a message to the chatbot
    message_response = client.post(
        "/api/chat",
        json={
            "message": "Tell me about the pyramids",
            "session_id": session_id,
            "language": "en"
        }
    )
    
    assert message_response.status_code == 200, f"Failed to send message: {message_response.text}"
    
    response_data = message_response.json()
    logger.info(f"Chatbot response: {response_data.get('text')}")
    
    # Verify the response contains information about pyramids
    assert "pyramid" in response_data.get("text", "").lower(), "Response doesn't contain information about pyramids"
    
    # Step 3: Get suggestions
    suggestions_response = client.get(f"/api/suggestions?session_id={session_id}")
    assert suggestions_response.status_code == 200, f"Failed to get suggestions: {suggestions_response.text}"
    
    suggestions_data = suggestions_response.json()
    logger.info(f"Suggestions: {suggestions_data}")
    
    # Step 4: Reset the session
    reset_response = client.post("/api/reset", json={"session_id": session_id})
    assert reset_response.status_code == 200, f"Failed to reset session: {reset_response.text}"
    
    logger.info("Session-based approach test passed!")
    return True

if __name__ == "__main__":
    # Run the test
    success = test_session_based_approach()
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1)
