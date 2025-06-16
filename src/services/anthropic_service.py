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

    def generate_response(self, prompt, max_tokens=150, model="claude-3-7-sonnet-20250219"):
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
            # Return a helpful Egypt tourism response instead of generic error
            return "I'm your Egypt tourism expert! I can help you with information about pyramids, temples, hotels, restaurants, and attractions throughout Egypt. What would you like to know?"

    def execute_service(self, method="generate", params=None):
        """
        Execute a service method with the given parameters.
        This method is used by the RAG pipeline to generate responses.

        Args:
            method: The method to execute (e.g., "generate")
            params: Parameters for the method

        Returns:
            Dict containing the response
        """
        if params is None:
            params = {}

        logger.info(f"Executing Anthropic service method: {method}")

        if method == "generate":
            prompt = params.get("prompt", "")
            max_tokens = params.get("max_tokens", 150)
            temperature = params.get("temperature", 0.7)
            model = params.get("model", "claude-3-7-sonnet-20250219")

            try:
                response = self.client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )

                return {
                    "text": response.content[0].text,
                    "model": model,
                    "usage": {
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens
                    }
                }
            except Exception as e:
                logger.error(f"Anthropic API error in execute_service: {str(e)}")
                return {
                    "text": "I'm your Egypt tourism expert! I can help you with information about pyramids, temples, hotels, restaurants, and attractions throughout Egypt. What would you like to know?",
                    "error": str(e)
                }
        else:
            logger.error(f"Unknown method: {method}")
            return {
                "text": "I'm your Egypt tourism expert! I can help you with information about pyramids, temples, hotels, restaurants, and attractions throughout Egypt. What would you like to know?",
                "error": f"Unknown method: {method}"
            }

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
        # Enhanced Egypt Tourism Expert System Prompt
        system_prompt = """You are the ultimate Egypt tourism expert with comprehensive knowledge of:

🏛️ ATTRACTIONS: Pyramids of Giza, Sphinx, Karnak Temple, Luxor Temple, Valley of the Kings, Abu Simbel, Egyptian Museum, Islamic Cairo, Alexandria Library, Philae Temple, Edfu Temple, Kom Ombo Temple, Dendera Temple, Saqqara, Memphis, Dahshur Pyramids

🏨 ACCOMMODATIONS: Luxury hotels (Four Seasons, Sofitel, Marriott), boutique hotels, Nile cruise ships, desert camps, Red Sea resorts, budget hostels, traditional riads

🍽️ CUISINE: Koshari, ful medames, molokhia, mahshi, kebab, kofta, fattah, baklava, kunafa, Egyptian tea, fresh juices, street food culture

🌍 DESTINATIONS: Cairo, Luxor, Aswan, Alexandria, Hurghada, Sharm El Sheikh, Dahab, Siwa Oasis, White Desert, Marsa Alam, El Gouna

🚗 TRANSPORTATION: Domestic flights, trains, buses, taxis, Uber, Nile cruises, feluccas, metro in Cairo

💡 PRACTICAL INFO: Visa requirements, currency (EGP), tipping culture, weather patterns, safety tips, cultural etiquette, language basics

Provide detailed, helpful, and accurate information. Be conversational and enthusiastic about Egypt's wonders."""

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

    def generate_fallback_response(self, query, language="en", session_data=None):
        """
        Generate a fallback response when database searches fail.

        Args:
            query: The user's original query
            language: The language code (en, ar)
            session_data: Optional session data containing conversation history

        Returns:
            Dict containing the response
        """
        logger.info(f"Generating fallback response using Anthropic for query: {query}")

        try:
            # Create context from session data if available
            context = {}
            if session_data:
                context["conversation_history"] = session_data.get("conversation_history", [])

            # Create specialized prompt for Egypt tourism
            prompt = self.create_egypt_tourism_prompt(
                user_message=query,
                language=language,
                context=context
            )

            # Default model from config or use fallback
            model = self.config.get("claude_model", "claude-3-7-sonnet-20250219")

            # Generate response
            response = self.client.messages.create(
                model=model,
                max_tokens=150,
                temperature=0.7,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            response_text = response.content[0].text

            return {
                "text": response_text,
                "source": "anthropic_llm",
                "model": model,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                }
            }
        except Exception as e:
            logger.error(f"Error generating fallback response: {str(e)}")

            # Return a helpful Egypt tourism message in the appropriate language
            if language == "ar":
                fallback_text = "مرحباً! أنا خبير السياحة المصرية. يمكنني مساعدتك في معلومات عن الأهرامات، المعابد، الفنادق، المطاعم، والأماكن السياحية في مصر. ما الذي تود معرفته عن مصر؟"
            else:
                fallback_text = "Hello! I'm your Egypt tourism expert. I can help you with information about the Pyramids of Giza, ancient temples, hotels, restaurants, Red Sea resorts, and all the amazing attractions Egypt has to offer. What would you like to know about Egypt?"

            return {
                "text": fallback_text,
                "error": str(e)
            }