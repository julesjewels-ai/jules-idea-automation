import pytest
import requests
from unittest.mock import patch, MagicMock
from src.services.jules import JulesClient
from src.utils.errors import AppError

class TestJulesClientErrors:

    def setup_method(self):
        # Pass explicit key to bypass environment check
        self.client = JulesClient(api_key="fake-key")

    def test_list_sources_401_error(self):
        """Test that a 401 error raises AppError with correct tip."""
        with patch('requests.request') as mock_req:
            mock_resp = MagicMock()
            # The exception needs a response object attached to it for the code to read status_code
            http_error = requests.exceptions.HTTPError("401 Client Error")
            http_error.response = MagicMock(status_code=401)

            mock_resp.raise_for_status.side_effect = http_error
            mock_resp.status_code = 401
            mock_req.return_value = mock_resp

            with pytest.raises(AppError) as excinfo:
                self.client.list_sources()

            assert "Authentication failed" in str(excinfo.value)
            assert excinfo.value.tip == "Check your JULES_API_KEY in .env file."

    def test_get_session_404_error(self):
        """Test that a 404 error raises AppError with correct tip."""
        with patch('requests.request') as mock_req:
            mock_resp = MagicMock()
            http_error = requests.exceptions.HTTPError("404 Client Error")
            http_error.response = MagicMock(status_code=404)

            mock_resp.raise_for_status.side_effect = http_error
            mock_resp.status_code = 404
            mock_req.return_value = mock_resp

            with pytest.raises(AppError) as excinfo:
                self.client.get_session("123")

            assert "Resource not found" in str(excinfo.value)
            assert "endpoint 'sessions/123' does not exist" in excinfo.value.tip

    def test_connection_error(self):
        """Test that connection error raises AppError."""
        with patch('requests.request') as mock_req:
            mock_req.side_effect = requests.exceptions.ConnectionError("Connection refused")

            with pytest.raises(AppError) as excinfo:
                self.client.list_sources()

            assert "Connection failed" in str(excinfo.value)
            assert excinfo.value.tip == "Check your internet connection and try again."

    def test_success(self):
        """Test successful request."""
        with patch('requests.request') as mock_req:
            mock_resp = MagicMock()
            mock_resp.content = b'{"sources": []}'
            mock_resp.json.return_value = {"sources": []}
            mock_resp.raise_for_status.return_value = None
            mock_req.return_value = mock_resp

            sources = self.client.list_sources()
            assert sources == {"sources": []}
