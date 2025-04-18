"""
Anthropic Claude API service for the Egypt Tourism Chatbot.
Provides natural language generation capabilities.
"""
import logging
from anthropic import Anthropic

logger = logging.getLogger(__name__)

class AnthropicService:
    def __init__(self, config):
        """
        Initialize the Anthropic service.
        
        Args:
            config: Configuration object containing environment variables
        """
        self.config = config
        api_key = config.get("anthropic_api_key", "")
        if not api_key:
            logger.warning("No Anthropic API key provided")
        self.client = Anthropic(api_key=api_key)
    
    def generate_response(self, prompt, max_tokens=1000, model="claude-3-7-sonnet-20250219"):
        """
        Generate a response using the Anthropic Claude API.
        
        Args:
            prompt: The user's message or a crafted prompt
            max_tokens: Maximum tokens in the response
            model: Claude model to use
            
        Returns:
            Generated text response
        """
        try:
            logger.info(f"Sending request to Anthropic API with prompt length: {len(prompt)}")
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API error: {str(e)}")
            return "Sorry, I encountered an error processing your request."
    
    def create_egypt_tourism_prompt(self, user_message, language="en", context=None):
        """
        Create a specialized prompt for Egypt tourism questions.
        
        Args:
            user_message: The user's original message
            language: The language code (en, ar)
            context: Optional context from conversation history
            
        Returns:
            Formatted prompt for Claude
        """
        # Base system prompt
        system_prompt = """You are an expert guide on Egyptian tourism, history, and culture.
Answer questions about Egypt's attractions, history, customs, and travel tips.
Be informative yet concise, helpful, and engaging.
Include specific details when relevant, like opening hours, best times to visit, or historical facts.
If you don't know something specific, be honest about it."""
        
        # Language-specific instructions
        if language == "ar":
            system_prompt += "\nProvide your response in Arabic."
        
        # Add context from previous conversation if available
        context_str = ""
        if context and context.get("conversation_history"):
            last_exchanges = context["conversation_history"][-3:]  # Last 3 exchanges
            context_str = "Previous conversation:\n" + "\n".join([
                f"User: {ex.get('user', '')}\nAssistant: {ex.get('assistant', '')}" 
                for ex in last_exchanges
            ])
        
        # Combine everything into the final prompt
        prompt = f"{system_prompt}\n\n{context_str}\n\nUser question: {user_message}"
        
        return prompt