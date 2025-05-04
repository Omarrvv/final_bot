#!/usr/bin/env python3
"""
Test script for verifying the chatbot works with session-based approach without authentication.
This script directly uses the chatbot components without going through the FastAPI app.
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

# Import the chatbot components
from src.utils.factory import ComponentFactory
from src.chatbot import Chatbot

async def test_chatbot_without_auth():
    """Test the chatbot without authentication."""
    logger.info("Testing chatbot without authentication...")

    # Create the component factory and initialize it
    factory = ComponentFactory()
    factory.initialize()

    # Create the chatbot components
    knowledge_base = factory.create_knowledge_base()
    nlu_engine = factory.create_nlu_engine()
    dialog_manager = factory.create_dialog_manager()
    response_generator = factory.create_response_generator()
    service_hub = factory.create_service_hub()
    session_manager = factory.create_session_manager()
    db_manager = factory.create_database_manager()

    # Create the chatbot instance
    chatbot = Chatbot(
        knowledge_base=knowledge_base,
        nlu_engine=nlu_engine,
        dialog_manager=dialog_manager,
        response_generator=response_generator,
        service_hub=service_hub,
        session_manager=session_manager,
        db_manager=db_manager
    )

    # Step 1: Create a new session
    session_id = str(uuid.uuid4())
    logger.info(f"Created new session: {session_id}")

    # Step 2: Send a message to the chatbot
    response = await chatbot.process_message("Tell me about the pyramids", session_id, "en")

    logger.info(f"Chatbot response: {response.get('text')}")

    # Verify the response contains information about pyramids
    assert "pyramid" in response.get("text", "").lower(), "Response doesn't contain information about pyramids"

    # Step 3: Get suggestions
    suggestions = chatbot.get_suggestions(session_id, "en")
    logger.info(f"Suggestions: {suggestions}")

    # Step 4: Reset the session
    reset_response = chatbot.reset_session(session_id)
    logger.info(f"Reset session: {reset_response}")

    logger.info("Chatbot without authentication test passed!")
    return True

if __name__ == "__main__":
    # Run the test
    success = asyncio.run(test_chatbot_without_auth())

    # Exit with appropriate status code
    sys.exit(0 if success else 1)
