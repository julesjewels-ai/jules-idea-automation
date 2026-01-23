import pytest
import requests
import requests_mock
from src.services.jules import JulesClient
from src.utils.errors import AppError, ConfigurationError

@pytest.fixture
def jules_client():
    return JulesClient(api_key="test_key")

def test_init_raises_config_error_without_key(monkeypatch):
    monkeypatch.delenv("JULES_API_KEY", raising=False)
    with pytest.raises(ConfigurationError):
        JulesClient(api_key=None)

def test_list_sources_success(jules_client):
    with requests_mock.Mocker() as m:
        m.get("https://jules.googleapis.com/v1alpha/sources", json={"sources": []})
        response = jules_client.list_sources()
        assert response == {"sources": []}

def test_list_sources_forbidden_error(jules_client):
    """Test that 403 Forbidden raises ConfigurationError."""
    with requests_mock.Mocker() as m:
        m.get("https://jules.googleapis.com/v1alpha/sources", status_code=403, text="Forbidden")

        with pytest.raises(ConfigurationError) as excinfo:
            jules_client.list_sources()
        assert "Access denied" in str(excinfo.value)
        assert "Ensure your API key has the necessary scopes" in excinfo.value.tip

def test_list_sources_unauthorized_error(jules_client):
    """Test that 401 Unauthorized raises ConfigurationError."""
    with requests_mock.Mocker() as m:
        m.get("https://jules.googleapis.com/v1alpha/sources", status_code=401, text="Unauthorized")

        with pytest.raises(ConfigurationError) as excinfo:
            jules_client.list_sources()
        assert "Authentication failed" in str(excinfo.value)
        assert "Check your JULES_API_KEY" in excinfo.value.tip

def test_get_session_not_found(jules_client):
    """Test that 404 Not Found raises AppError."""
    with requests_mock.Mocker() as m:
        m.get("https://jules.googleapis.com/v1alpha/sessions/123", status_code=404, text="Not Found")

        with pytest.raises(AppError) as excinfo:
            jules_client.get_session("123")
        assert "Resource not found" in str(excinfo.value)
        assert "ID might be incorrect" in excinfo.value.tip

def test_server_error(jules_client):
    """Test that 500 Server Error raises AppError."""
    with requests_mock.Mocker() as m:
        m.get("https://jules.googleapis.com/v1alpha/sources", status_code=500, text="Internal Error")

        with pytest.raises(AppError) as excinfo:
            jules_client.list_sources()
        assert "Jules API encountered a server error" in str(excinfo.value)
        assert "try again later" in excinfo.value.tip

def test_create_session_connection_error(jules_client):
    """Test that ConnectionError raises AppError."""
    with requests_mock.Mocker() as m:
        m.post("https://jules.googleapis.com/v1alpha/sessions", exc=requests.exceptions.ConnectionError)

        with pytest.raises(AppError) as excinfo:
            jules_client.create_session("source_id", "prompt")
        assert "Unable to connect" in str(excinfo.value)
        assert "Check your internet connection" in excinfo.value.tip

def test_generic_request_exception(jules_client):
    """Test that other RequestExceptions raise AppError."""
    with requests_mock.Mocker() as m:
        m.get("https://jules.googleapis.com/v1alpha/sources", exc=requests.exceptions.Timeout)

        with pytest.raises(AppError) as excinfo:
            jules_client.list_sources()
        assert "An unexpected network error" in str(excinfo.value)
        assert "Check your network configuration" in excinfo.value.tip

def test_is_session_complete_indirect_error(jules_client):
    """Test that errors bubble up from helper methods."""
    with requests_mock.Mocker() as m:
        m.get("https://jules.googleapis.com/v1alpha/sessions/123", status_code=403)

        with pytest.raises(ConfigurationError):
            jules_client.is_session_complete("123")
