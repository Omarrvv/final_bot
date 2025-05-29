#!/usr/bin/env python3
"""
Fix script for Egypt Tourism Chatbot LLM response brevity.
This script will:
1. Update the LLM prompts to generate shorter, more concise responses
2. Reduce the max_tokens parameter to limit response length
"""
import os
import sys
import logging
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the necessary components
from src.chatbot import Chatbot

def fix_llm_brevity():
    """Fix the LLM prompts to generate shorter, more concise responses."""
    logger.info("\n=== Fixing LLM Response Brevity ===")
    
    # Monkey patch the process_message method in Chatbot
    try:
        # Get the Chatbot class
        chatbot_class = Chatbot
        
        # Store the original method for reference
        original_process_message = chatbot_class.process_message
        
        # Define the fixed method
        async def fixed_process_message(self, user_message: str, session_id: str = None, language: str = None):
            """
            Fixed version of process_message that uses more concise LLM prompts.
            """
            # Start timing
            import time
            start_time = time.time()
            
            # Create a new session if none provided
            if not session_id:
                import uuid
                session_id = str(uuid.uuid4())
                logger.info(f"Created new session: {session_id}")
            
            # Validate or generate session
            session = await self.get_or_create_session(session_id)
            
            # Detect language if not provided
            if not language:
                language = session.get("language", "en")
            
            try:
                # Set this to False to use database first, True to always use LLM
                USE_LLM_FIRST = False
                logger.info("Chatbot configured to use database first (USE_LLM_FIRST = False)")
                
                # Use the Anthropic LLM for all queries if USE_LLM_FIRST is True
                if USE_LLM_FIRST:
                    try:
                        # Get the Anthropic service from the container
                        from src.utils.container import container
                        anthropic_service = None
                        
                        if container.has("anthropic_service"):
                            anthropic_service = container.get("anthropic_service")
                            logger.info(f"Got Anthropic service from container")
                        else:
                            # Fallback to service hub
                            anthropic_service = self.service_hub.get_service("anthropic_service")
                            logger.info(f"Got Anthropic service from service hub")
                        
                        if anthropic_service:
                            logger.info(f"Using Anthropic LLM for direct response")
                            
                            # Create a prompt for the LLM - UPDATED FOR BREVITY
                            prompt = f"""
                            You are an expert guide on Egyptian tourism, history, and culture.
                            Answer the following question about Egypt tourism.
                            KEEP YOUR RESPONSE EXTREMELY BRIEF - under 80 words maximum.
                            Focus ONLY on the most essential facts.
                            Use simple language and short sentences.
                            Format your response in a conversational style.
                            DO NOT use Markdown formatting.
                            DO NOT use bullet points or numbered lists.
                            Just write in plain, conversational text with regular paragraphs.
                            Respond in {'Arabic' if language == 'ar' else 'English'}.
                            
                            USER QUESTION:
                            {user_message}
                            """
                            
                            # Call the LLM service directly using generate_response method
                            response_text = anthropic_service.generate_response(
                                prompt=prompt,
                                max_tokens=150  # REDUCED FROM 300
                            )
                            
                            if response_text:
                                # Process message through NLU just to get intent and entities
                                nlu_result = await self._process_nlu(user_message, session_id, language)
                                
                                # Log the response text for debugging
                                logger.info(f"Anthropic response text: {response_text[:100]}...")
                                
                                # Clean up the response text to remove any unwanted characters and Markdown formatting
                                response_text = self._clean_markdown_formatting(response_text)
                                
                                # Create a proper response object
                                response = {
                                    "text": response_text,
                                    "response_type": "direct_response",
                                    "suggestions": [],
                                    "intent": nlu_result.get("intent"),
                                    "entities": nlu_result.get("entities", {}),
                                    "source": "anthropic_llm",
                                    "fallback": False,
                                    "session_id": session_id,
                                    "language": language
                                }
                                
                                # Save session with updated state
                                await self._save_session(session_id, session)
                                
                                # Add message to session history
                                try:
                                    await self._add_message_to_session(
                                        session_id=session_id,
                                        role="user",
                                        content=user_message
                                    )
                                    
                                    await self._add_message_to_session(
                                        session_id=session_id,
                                        role="assistant",
                                        content=response.get("text", "")
                                    )
                                except Exception as e:
                                    logger.error(f"Error adding message to session: {str(e)}")
                                
                                # Track performance
                                processing_time = time.time() - start_time
                                logger.info(f"Message processed in {processing_time:.2f}s using LLM directly")
                                
                                return response
                    
                    except Exception as llm_err:
                        logger.error(f"Error using direct LLM in process_message: {str(llm_err)}")
                        # Continue with the regular flow if LLM fails
                
                # Continue with the original method for the rest of the processing
                return await original_process_message(self, user_message, session_id, language)
            
            except Exception as e:
                logger.error(f"Error in fixed_process_message: {str(e)}")
                # Return to the original method if there's an error
                return await original_process_message(self, user_message, session_id, language)
        
        # Replace the original method with the fixed one
        chatbot_class.process_message = fixed_process_message
        
        # Now patch the _use_llm_fallback method if it exists
        if hasattr(chatbot_class, '_use_llm_fallback'):
            original_use_llm_fallback = chatbot_class._use_llm_fallback
            
            async def fixed_use_llm_fallback(self, user_message, session, original_response):
                """
                Fixed version of _use_llm_fallback that generates shorter responses.
                """
                logger.info(f"Using LLM fallback for message: {user_message[:50]}...")
                
                try:
                    # Get the Anthropic service
                    from src.utils.container import container
                    anthropic_service = None
                    
                    if container.has("anthropic_service"):
                        anthropic_service = container.get("anthropic_service")
                        logger.info(f"Got Anthropic service from container")
                    else:
                        # Fallback to service hub
                        anthropic_service = self.service_hub.get_service("anthropic_service")
                        logger.info(f"Got Anthropic service from service hub")
                    
                    if not anthropic_service:
                        logger.error("Could not get Anthropic service")
                        return original_response
                    
                    # Get language from session
                    language = session.get("language", "en")
                    
                    # Create a prompt for the LLM - UPDATED FOR BREVITY
                    prompt = f"""
                    You are an expert guide on Egyptian tourism, history, and culture.
                    Answer the following question about Egypt tourism.
                    KEEP YOUR RESPONSE EXTREMELY BRIEF - under 80 words maximum.
                    Focus ONLY on the most essential facts.
                    Use simple language and short sentences.
                    Format your response in a conversational style.
                    DO NOT use Markdown formatting.
                    DO NOT use bullet points or numbered lists.
                    Just write in plain, conversational text with regular paragraphs.
                    Respond in {'Arabic' if language == 'ar' else 'English'}.
                    
                    USER QUESTION:
                    {user_message}
                    """
                    
                    # Call the LLM service
                    response_text = anthropic_service.generate_response(
                        prompt=prompt,
                        max_tokens=150  # REDUCED FROM 500
                    )
                    
                    if not response_text:
                        logger.error("Empty response from LLM")
                        return original_response
                    
                    # Log the response text for debugging
                    logger.info(f"Anthropic fallback response text: {response_text[:100]}...")
                    
                    # Clean up the response text
                    response_text = self._clean_markdown_formatting(response_text)
                    
                    # Create a new response
                    return {
                        "text": response_text,
                        "response_type": "fallback",
                        "suggestions": original_response.get("suggestions", []),
                        "intent": original_response.get("intent"),
                        "entities": original_response.get("entities", {}),
                        "source": "anthropic_llm",
                        "fallback": True,
                        "session_id": session.get("session_id"),
                        "language": language
                    }
                except Exception as e:
                    logger.error(f"Error in fixed_use_llm_fallback: {str(e)}")
                    return original_response
            
            # Replace the original method with the fixed one
            chatbot_class._use_llm_fallback = fixed_use_llm_fallback
            logger.info("Successfully patched _use_llm_fallback method to generate shorter responses")
        
        # Also patch the process_attraction_query method to use shorter LLM responses
        original_process_attraction_query = chatbot_class.process_attraction_query
        
        async def fixed_process_attraction_query(self, message: str, session_id: str, language: str = "en"):
            """
            Fixed version of process_attraction_query that generates shorter responses.
            """
            # Call the original method
            response = await original_process_attraction_query(self, message, session_id, language)
            
            # If the response is from the LLM, make sure it's not too long
            if response and response.get("source") == "anthropic_llm":
                text = response.get("text", "")
                if len(text) > 300:  # If the response is too long
                    # Truncate it to a reasonable length
                    response["text"] = text[:300] + "..."
                    logger.info("Truncated long LLM response for attraction query")
            
            return response
        
        # Replace the original method with the fixed one
        chatbot_class.process_attraction_query = fixed_process_attraction_query
        
        logger.info("Successfully patched process_message method to generate shorter LLM responses")
        return True
    except Exception as e:
        logger.error(f"Failed to patch process_message: {str(e)}")
        return False

def main():
    """Run all fixes."""
    logger.info("Starting LLM brevity fixes for Egypt Tourism Chatbot...")
    
    # Fix LLM brevity
    if fix_llm_brevity():
        logger.info("✅ LLM brevity fix applied")
    else:
        logger.error("❌ LLM brevity fix failed")
    
    logger.info("\nAll fixes applied. Please restart the chatbot for changes to take effect.")

if __name__ == "__main__":
    main()
