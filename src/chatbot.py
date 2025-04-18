"""
Main chatbot module for the Egypt Tourism Chatbot.
Provides the core chatbot functionality with dependency injection.
"""
import logging
import json
from typing import Dict, List, Any, Optional
import os
import importlib

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
    
    def process_message(self, user_message: str, session_id: Optional[str] = None, 
                     language: Optional[str] = None, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a user message and generate a response.
        
        Args:
            user_message (str): User's message text
            session_id (str, optional): Session ID for context
            language (str, optional): Language code (e.g., 'en', 'ar')
            user_id (str, optional): User ID from request model
            
        Returns:
            Dict: Response containing text, session ID, and other data
        """
        context = {} # Initialize context
        try:
            # Ensure initialization (this check might be redundant now)
            # if not self._initialized:
            #    raise RuntimeError("Chatbot components not initialized.")
                
            logger.info(f"Processing message: {user_message[:50]}...")
            
            # Create a new session if none provided
            if not session_id:
                session_id = self.session_manager.create_session()
                logger.info(f"Created new session: {session_id}")
            
            # Get context from session
            context = self.session_manager.get_context(session_id)
            logger.debug(f"Retrieved context for session {session_id}: {context}")
            
            # Set language in context if provided
            if language:
                context["language"] = language
            elif "language" not in context:
                context["language"] = "en"  # Default to English
            
            logger.debug(f"Using language: {context['language']}")
            
            # Process the message with NLU
            logger.debug("Sending to NLU engine")
            nlu_result = self.nlu_engine.process(
                text=user_message,
                session_id=session_id,
                language=context.get("language"),
                context=context
            )
            logger.debug(f"NLU result: {nlu_result}")
            
            # Update context with NLU results
            context = self.session_manager.update_context(session_id, nlu_result)
            
            # Determine next dialog action
            logger.debug("Getting next dialog action")
            dialog_action = self.dialog_manager.next_action(nlu_result, context)
            logger.debug(f"Dialog action: {dialog_action}")
            
            # Execute any required service calls
            service_results = self._handle_service_calls(
                dialog_action.get("service_calls", []),
                context
            )
            
            # Add service results to context
            if service_results:
                context["service_results"] = service_results
                self.session_manager.set_context(session_id, context)
            
            # Generate response
            response = self.response_generator.generate_response(
                dialog_action=dialog_action,
                nlu_result=nlu_result,
                context=context
            )
            
            # Add session ID and language to response
            response["session_id"] = session_id
            response["language"] = context.get("language", "en")
            
            # Get suggestions if available
            suggestions = self.dialog_manager.get_suggestions(
                state=dialog_action.get("next_state", "greeting"),
                language=context.get("language", "en")
            )
            
            if suggestions:
                response["suggestions"] = suggestions
                
            # Log the interaction
            self._log_interaction(user_message, response, nlu_result, session_id)
                
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            
            # Generate fallback response
            fallback_response = {
                "text": "I'm sorry, I'm having trouble understanding. Could you try again?",
                "session_id": session_id,
                "language": context.get("language", "en")
            }
            
            if isinstance(e, ChatbotError):
                # Use the error message for better feedback
                fallback_response["text"] = f"Sorry, {e.message.lower()}"
                
            return fallback_response
    
    def _handle_service_calls(self, service_calls: List[Dict], context: Dict) -> Dict[str, Any]:
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
                result = self.service_hub.execute_service(
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
                        method=method,
                        error=str(e)
                    )
                    
                # Store error for non-required services
                results[f"{service}.{method}.error"] = str(e)
        
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