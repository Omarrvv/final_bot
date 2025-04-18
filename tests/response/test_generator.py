import unittest
from src.response.generator import ResponseGenerator
from unittest.mock import MagicMock

class TestResponseGenerator(unittest.TestCase):
    def setUp(self):
        self.knowledge_base_mock = MagicMock()
        self.generator = ResponseGenerator("/path/to/templates", self.knowledge_base_mock)
    
    def test_generate_response_greeting(self):
        dialog_action = {"action_type": "response", "response_type": "greeting", "language": "en"}
        response = self.generator.generate_response(dialog_action, {}, {})
        self.assertIn("text", response)
        self.assertEqual(response["response_type"], "greeting")
