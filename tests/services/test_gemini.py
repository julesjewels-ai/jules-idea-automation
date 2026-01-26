import unittest
from unittest.mock import MagicMock, patch
import json
import os
from src.services.gemini import GeminiClient
from src.utils.errors import GenerationError

class TestGeminiClient(unittest.TestCase):
    def setUp(self):
        # Ensure API key is set to avoid ConfigurationError
        self.env_patcher = patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"})
        self.env_patcher.start()
        self.client = GeminiClient()

    def tearDown(self):
        self.env_patcher.stop()

    def test_generate_idea_validation_error(self):
        # Valid JSON but missing 'title' and 'description' which are required in IdeaResponse
        invalid_data = {
            "slug": "test-idea",
            "tech_stack": ["python"],
            "features": ["feature1"]
        }

        mock_response = MagicMock()
        mock_response.text = json.dumps(invalid_data)

        # Mock the client.models.generate_content method
        self.client.client.models.generate_content = MagicMock(return_value=mock_response)

        # Execute and Assert
        with self.assertRaises(GenerationError) as cm:
            self.client.generate_idea()

        # Check that the tip contains validation errors
        error_tip = cm.exception.tip
        self.assertIn("Validation errors:", error_tip)
        # Note: formatting might vary slightly depending on pydantic version, but "title" and "required" should be there
        self.assertIn("title", error_tip)
        self.assertIn("Field required", error_tip)
        self.assertIn("description", error_tip)

    def test_generate_idea_success(self):
        valid_data = {
            "title": "Test Idea",
            "description": "A test idea",
            "slug": "test-idea",
            "tech_stack": ["python"],
            "features": ["feature1"]
        }

        mock_response = MagicMock()
        mock_response.text = json.dumps(valid_data)

        # Mock the client.models.generate_content method
        self.client.client.models.generate_content = MagicMock(return_value=mock_response)

        # Execute
        result = self.client.generate_idea()

        # Assert
        self.assertEqual(result["title"], "Test Idea")
