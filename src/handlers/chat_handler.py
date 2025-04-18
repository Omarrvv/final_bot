from typing import Optional
import traceback
import uuid

class ChatHandler:
    def handle_message(self, message: str, session_id: str, user_id: Optional[str] = None):
        """
        Handle a user message.
        
        Args:
            message (str): User message
            session_id (str): Session ID
            user_id (str, optional): User ID
            
        Returns:
            dict: Response with generated answer and metadata
        """
        try:
            # Track the user message
            self.app.analytics.track_message(
                message=message,
                is_user=True,
                session_id=session_id,
                user_id=user_id
            )
            
            # Get or create session
            session = self.context_manager.get_session(session_id, create_if_missing=True)
            
            # Create new session if this is the first message
            if not session.has_messages():
                # Track session start
                self.app.analytics.track_session_start(
                    session_id=session_id,
                    user_id=user_id
                )
            
            # Process the message with NLU
            nlu_result = self.nlu_processor.process(message)
            
            # Track intent
            if nlu_result.intent:
                self.app.analytics.track_intent(
                    intent=nlu_result.intent,
                    confidence=nlu_result.confidence,
                    session_id=session_id,
                    user_id=user_id
                )
            
            # Track entities
            if nlu_result.entities:
                for entity_type, values in nlu_result.entities.items():
                    for value in values:
                        self.app.analytics.track_entity(
                            entity_type=entity_type,
                            entity_value=value,
                            confidence=1.0,  # Default confidence
                            session_id=session_id,
                            user_id=user_id
                        )
            
            # Add user message to context
            session.add_user_message(message)
            
            # Generate response using dialogue manager
            response = self.dialogue_manager.generate_response(message, session, nlu_result)
            
            # Track the bot message
            self.app.analytics.track_message(
                message=response.message,
                is_user=False,
                session_id=session_id,
                user_id=user_id
            )
            
            # Add bot message to context
            session.add_bot_message(response.message)
            
            # Update session in context manager
            self.context_manager.update_session(session)
            
            # Prepare response
            chat_response = {
                "message": response.message,
                "intent": nlu_result.intent,
                "confidence": nlu_result.confidence,
                "entities": nlu_result.entities,
                "session_id": session_id,
                "message_id": str(uuid.uuid4())
            }
            
            return chat_response
            
        except Exception as e:
            self.logger.error(f"Error handling message: {str(e)}")
            
            # Track error
            self.app.analytics.track_error(
                error_type="CHAT_ERROR",
                error_message=str(e),
                stack_trace=traceback.format_exc(),
                session_id=session_id,
                user_id=user_id
            )
            
            return {
                "message": "I apologize, but I encountered an error while processing your message. Please try again.",
                "error": str(e),
                "session_id": session_id
            }

    def handle_feedback(self, message_id: str, rating: int, comment: Optional[str] = None, 
                       session_id: Optional[str] = None, user_id: Optional[str] = None):
        """
        Handle user feedback.
        
        Args:
            message_id (str): Message ID
            rating (int): Rating (positive/negative)
            comment (str, optional): User comment
            session_id (str, optional): Session ID
            user_id (str, optional): User ID
            
        Returns:
            dict: Response with success status
        """
        try:
            # Track feedback
            self.app.analytics.track_feedback(
                rating=rating,
                message_id=message_id,
                comment=comment,
                session_id=session_id,
                user_id=user_id
            )
            
            # Store feedback in database if available
            if self.app.db_manager:
                self.app.db_manager.store_feedback(
                    message_id=message_id,
                    rating=rating,
                    comment=comment,
                    session_id=session_id,
                    user_id=user_id
                )
            
            return {
                "success": True,
                "message": "Thank you for your feedback!"
            }
            
        except Exception as e:
            self.logger.error(f"Error handling feedback: {str(e)}")
            
            # Track error
            self.app.analytics.track_error(
                error_type="FEEDBACK_ERROR",
                error_message=str(e),
                stack_trace=traceback.format_exc(),
                session_id=session_id,
                user_id=user_id
            )
            
            return {
                "success": False,
                "error": str(e)
            }

    def end_session(self, session_id: str, user_id: Optional[str] = None):
        """
        End a chat session.
        
        Args:
            session_id (str): Session ID
            user_id (str, optional): User ID
            
        Returns:
            dict: Response with success status
        """
        try:
            # Get session
            session = self.context_manager.get_session(session_id)
            
            if session:
                # Track session end
                self.app.analytics.track_session_end(
                    session_id=session_id,
                    user_id=user_id,
                    duration=session.get_duration(),
                    message_count=session.get_message_count()
                )
                
                # Clear session
                self.context_manager.clear_session(session_id)
                
                return {
                    "success": True,
                    "message": "Session ended successfully."
                }
            else:
                return {
                    "success": False,
                    "error": "Session not found."
                }
                
        except Exception as e:
            self.logger.error(f"Error ending session: {str(e)}")
            
            # Track error
            self.app.analytics.track_error(
                error_type="SESSION_END_ERROR",
                error_message=str(e),
                stack_trace=traceback.format_exc(),
                session_id=session_id,
                user_id=user_id
            )
            
            return {
                "success": False,
                "error": str(e)
            } 