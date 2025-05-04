import unittest
from src.response.generator import ResponseGenerator
from unittest.mock import MagicMock

class TestResponseGenerator(unittest.TestCase):
    def setUp(self):
        self.knowledge_base_mock = MagicMock()
        self.generator = ResponseGenerator("/path/to/templates", self.knowledge_base_mock)

    def test_generate_response_greeting(self):
        dialog_action = {"action_type": "response", "response_type": "greeting", "language": "en"}
        # Mock _get_template to always return a test greeting
        self.generator._get_template = lambda template_name, language: "Hello! This is a test greeting."
        # Use generate_response_from_action
        response = self.generator.generate_response_from_action(dialog_action, {}, {})
        # Ensure response is a dict and 'text' and 'response_type' are present
        self.assertIsInstance(response, dict)
        self.assertIn("text", response)
        self.assertIn("response_type", response)
        self.assertEqual(response["response_type"], "greeting")
        self.assertIn("Hello! This is a test greeting.", response["text"])
