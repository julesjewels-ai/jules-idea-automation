import pytest
from unittest.mock import Mock, patch
from src.services.jules import JulesClient
from src.utils.errors import JulesApiError, ConfigurationError
import requests

class TestJulesClient:

    @pytest.fixture
    def client(self):
        return JulesClient(api_key="test-key")

    def test_init_raises_config_error_without_api_key(self, monkeypatch):
        monkeypatch.delenv("JULES_API_KEY", raising=False)
        with pytest.raises(ConfigurationError):
            JulesClient(api_key=None)

    @patch('src.services.jules.requests.request')
    def test_list_sources_success(self, mock_request, client):
        mock_response = Mock()
        mock_response.json.return_value = {"sources": []}
        mock_response.text = '{"sources": []}'
        mock_response.raise_for_status.return_value = None

        mock_request.return_value = mock_response

        sources = client.list_sources()
        assert sources == {"sources": []}

    @patch('src.services.jules.requests.request')
    def test_error_401_unauthorized(self, mock_request, client):
        error_response = Mock()
        error_response.status_code = 401
        error_response.json.return_value = {"error": {"message": "Unauthorized"}}

        error = requests.exceptions.HTTPError("401 Client Error")
        error.response = error_response

        mock_response = Mock()
        mock_response.raise_for_status.side_effect = error
        mock_request.return_value = mock_response

        with pytest.raises(JulesApiError) as excinfo:
            client.list_sources()

        assert excinfo.value.tip is not None
        assert "Check your JULES_API_KEY" in excinfo.value.tip

    @patch('src.services.jules.requests.request')
    def test_error_403_forbidden(self, mock_request, client):
        error_response = Mock()
        error_response.status_code = 403
        error_response.json.return_value = {"error": {"message": "Forbidden"}}

        error = requests.exceptions.HTTPError("403 Client Error")
        error.response = error_response

        mock_response = Mock()
        mock_response.raise_for_status.side_effect = error
        mock_request.return_value = mock_response

        with pytest.raises(JulesApiError) as excinfo:
            client.list_sources()

        assert excinfo.value.tip is not None
        assert "Check your JULES_API_KEY" in excinfo.value.tip

    @patch('src.services.jules.requests.request')
    def test_error_404_not_found(self, mock_request, client):
        error_response = Mock()
        error_response.status_code = 404
        error_response.json.return_value = {"error": {"message": "Not Found"}}

        error = requests.exceptions.HTTPError("404 Client Error")
        error.response = error_response

        mock_response = Mock()
        mock_response.raise_for_status.side_effect = error
        mock_request.return_value = mock_response

        with pytest.raises(JulesApiError) as excinfo:
            client.get_session("123")

        assert excinfo.value.tip is not None
        assert "verify the ID" in excinfo.value.tip or "not found" in excinfo.value.tip

    @patch('src.services.jules.requests.request')
    def test_error_generic(self, mock_request, client):
        error_response = Mock()
        error_response.status_code = 500
        error_response.json.return_value = {"error": {"message": "Server Error"}}

        error = requests.exceptions.HTTPError("500 Server Error")
        error.response = error_response

        mock_response = Mock()
        mock_response.raise_for_status.side_effect = error
        mock_request.return_value = mock_response

        with pytest.raises(JulesApiError) as excinfo:
            client.list_sources()

        assert excinfo.value.tip is not None
        assert "try again later" in excinfo.value.tip.lower()
