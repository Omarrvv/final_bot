# Create a test script to verify the Anthropic service works
# Save as test_anthropic.py

import os
from dotenv import load_dotenv
from src.services.anthropic_service import AnthropicService

# Load environment variables
load_dotenv()

# Create a simple config object (mimicking what your factory would provide)
config = {
    "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY")
}

# Initialize the service
service = AnthropicService(config)

# Test with a simple prompt
test_prompt = "Tell me about the pyramids of Giza in 3 sentences."
response = service.generate_response(test_prompt)

print(f"Prompt: {test_prompt}")
print(f"Response: {response}")