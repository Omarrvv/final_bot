"""
Main chatbot module for the Egypt Tourism Chatbot.
Provides the core chatbot functionality with dependency injection.
"""
import logging
import json
from typing import Dict, List, Any, Optional
import os
import importlib
import time

from src.utils.container import container
from src.utils.exceptions import ChatbotError, ResourceNotFoundError, ServiceError, ConfigurationError
from src.utils.factory import component_factory
from src.knowledge.database import DatabaseManager # Import DatabaseManager - NEW

logger = logging.getLogger(__name__)

class Chatbot:
    """
    Egypt Tourism Chatbot with dependency injection.
    Processes user messages and generates appropriate responses.
    """
    
    def __init__(self, 
                 knowledge_base: Any, 
                 nlu_engine: Any, 
                 dialog_manager: Any, 
                 response_generator: Any, 
                 service_hub: Any, 
                 session_manager: Any, 
                 db_manager: Any):
        """
        Initialize the chatbot with injected components.
        """
        logger.info("Initializing Egypt Tourism Chatbot via injected components")
        self.knowledge_base = knowledge_base
        self.nlu_engine = nlu_engine
        self.dialog_manager = dialog_manager
        self.response_generator = response_generator
        self.service_hub = service_hub
        self.session_manager = session_manager
        self.db_manager = db_manager # Keep for logging
        
        # Basic check to ensure core components are present
        if not all([self.knowledge_base, self.nlu_engine, self.dialog_manager, 
                    self.response_generator, self.service_hub, self.session_manager, self.db_manager]):
            raise ConfigurationError("One or more core chatbot components failed to initialize.")
            
        self._initialized = True # Consider if this flag is still needed
        logger.info("Egypt Tourism Chatbot initialized successfully")
    
    async def process_message(self, message: str, session_id: Optional[str] = None, language: str = "en") -> Dict:
        """Process an incoming chat message and return a response."""
        logging.info(f"--- Chatbot processing message: '{message}' (lang={language}, session={session_id}) ---")
        logging.info(f"Processing message: {message}...")
        
        try:
            # Create or get session
            if not session_id:
                session_id = self.session_manager.create_session()  # Remove await since it's sync
                logging.info(f"Created new session: {session_id}")
            
            # Get or initialize session data
            session_data = self.session_manager.get_session(session_id) or {}
            
            # Update session with current language
            session_data["language"] = language
            self.session_manager.save_session(session_id, session_data)
            
            # Process message through NLU pipeline
            nlu_result = self.nlu_engine.process(message, language=language, context=session_data)
            logging.debug(f"NLU Result: {nlu_result}")
            
            # Update dialog state and get next action
            dialog_action = self.dialog_manager.process(nlu_result, session_data)
            logging.debug(f"Dialog Action: {dialog_action}")
            
            # Generate response based on dialog action
            response = self.response_generator.generate_response(dialog_action, nlu_result, session_data)
            logging.debug(f"Generated Response: {response}")
            
            # Add session ID to response
            response["session_id"] = session_id
            
            # Log analytics if enabled
            if self.db_manager:
                self.db_manager.log_analytics_event(
                    event_type="chat_message",
                    event_data={
                        "message": message,
                        "language": language,
                        "intent": nlu_result.get("intent"),
                        "entities": nlu_result.get("entities"),
                        "response": response
                    },
                    session_id=session_id
                )
            
            return response
            
        except Exception as e:
            logging.error(f"Error processing message: {str(e)}", exc_info=True)
            return {
                "text": "I apologize, but I encountered an error processing your message. Please try again.",
                "error": str(e),
                "session_id": session_id
            }
    
    async def _handle_service_calls(self, service_calls: List[Dict], context: Dict) -> Dict[str, Any]:
        """
        Execute service integration calls based on dialog requirements.
        
        Args:
            service_calls (List[Dict]): Service calls to execute
            context (Dict): Current conversation context
            
        Returns:
            Dict: Results from service calls
        """
        results = {}
        
        for call in service_calls:
            service = call.get("service")
            method = call.get("method")
            params = call.get("params", {})
            
            # Add context data to params if specified
            if call.get("include_context"):
                for key in call["include_context"]:
                    if key in context:
                        params[key] = context[key]
            
            # Execute service call
            try:
                result = await self.service_hub.execute_service(
                    service=service,
                    method=method,
                    params=params
                )
                
                # Store result
                results[f"{service}.{method}"] = result
                
                # Store in specific result location if specified
                if call.get("store_as"):
                    results[call["store_as"]] = result
                    
            except Exception as e:
                logger.error(f"Service call failed: {service}.{method} - {str(e)}")
                
                if call.get("required", False):
                    # Raise exception for required services
                    raise ServiceError(
                        service_name=service,
                        message=f"Required service {service}.{method} failed: {str(e)}"
                    )
                    
        return results
    
    def _log_interaction(self, user_message: str, response: Dict, nlu_result: Dict, session_id: str):
        """
        Log interaction details for analytics and debugging.
        
        Args:
            user_message (str): User's message
            response (Dict): Generated response
            nlu_result (Dict): NLU processing result
            session_id (str): Session ID
        """
        try:
            # Log to standard logger
            logger.info(f"Interaction - Session: {session_id}, Intent: {nlu_result.get('intent')}")
            
            # Log interaction event to database
            event_data = {
                "user_message": user_message,
                "bot_response": response.get("text"), # Log only the text part
                "intent": nlu_result.get("intent"),
                "intent_confidence": nlu_result.get("intent_confidence"),
                "entities": nlu_result.get("entities"),
                "language": response.get("language"),
                "suggestions_provided": response.get("suggestions")
            }
            self.db_manager.log_analytics_event(
                event_type="user_interaction", 
                event_data=event_data,
                session_id=session_id
                # user_id could be added here if user authentication is implemented
            )
            
        except Exception as e:
            logger.error(f"Failed to log interaction: {str(e)}", exc_info=True)
    
    def get_suggestions(self, session_id: Optional[str] = None, 
                     language: str = "en") -> List[Dict]:
        """
        Get suggested messages for the current conversation state.
        
        Args:
            session_id (str, optional): Session ID
            language (str): Language code
            
        Returns:
            List[Dict]: Suggested messages
        """
        # If no session ID provided, return default suggestions
        if not session_id:
            return self.dialog_manager.get_suggestions("greeting", language)
        
        # Get context for existing session
        try:
            context = self.session_manager.get_context(session_id)
            state = context.get("dialog_state", "greeting")
            return self.dialog_manager.get_suggestions(state, language)
        except Exception as e:
            logger.error(f"Error getting suggestions: {str(e)}")
            return []
    
    def reset_session(self, session_id: Optional[str] = None) -> Dict:
        """
        Reset or create a session.
        
        Args:
            session_id (str, optional): Session ID to reset
            
        Returns:
            Dict: New session information
        """
        # Delete existing session if provided
        if session_id:
            try:
                self.session_manager.delete_session(session_id)
            except Exception as e:
                logger.warning(f"Error deleting session {session_id}: {str(e)}")
        
        # Create new session
        new_session_id = self.session_manager.create_session()
        
        return {
            "session_id": new_session_id,
            "message": "Session reset successfully"
        } 