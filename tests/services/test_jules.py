import os
import pytest
import requests
import requests_mock
from src.services.jules import JulesClient
from src.utils.errors import AppError, ConfigurationError

# Mock API Key
@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("JULES_API_KEY", "test_key")

@pytest.fixture
def client(mock_env):
    return JulesClient()

def test_init_no_api_key(monkeypatch):
    monkeypatch.delenv("JULES_API_KEY", raising=False)
    with pytest.raises(ConfigurationError) as excinfo:
        JulesClient()
    assert "JULES_API_KEY environment variable is not set" in str(excinfo.value)

def test_list_sources_success(client):
    with requests_mock.Mocker() as m:
        m.get("https://jules.googleapis.com/v1alpha/sources", json={"sources": []})
        response = client.list_sources()
        assert response == {"sources": []}

def test_error_401_unauthorized(client):
    with requests_mock.Mocker() as m:
        m.get("https://jules.googleapis.com/v1alpha/sources", status_code=401)

        with pytest.raises(AppError) as excinfo:
            client.list_sources()

        assert "Jules API Authentication Failed" in str(excinfo.value)
        assert "Check your JULES_API_KEY" in excinfo.value.tip

def test_error_403_forbidden(client):
    with requests_mock.Mocker() as m:
        m.get("https://jules.googleapis.com/v1alpha/sources", status_code=403)

        with pytest.raises(AppError) as excinfo:
            client.list_sources()

        assert "Jules API Permission Denied" in str(excinfo.value)
        assert "API key doesn't have access" in excinfo.value.tip

def test_error_404_not_found(client):
    with requests_mock.Mocker() as m:
        m.get("https://jules.googleapis.com/v1alpha/sessions/999", status_code=404)

        with pytest.raises(AppError) as excinfo:
            client.get_session("999")

        assert "Resource Not Found" in str(excinfo.value)
        assert "session or source ID might be incorrect" in excinfo.value.tip

def test_error_500_server_error(client):
    with requests_mock.Mocker() as m:
        m.get("https://jules.googleapis.com/v1alpha/sources", status_code=500)

        with pytest.raises(AppError) as excinfo:
            client.list_sources()

        assert "Jules API Server Error (500)" in str(excinfo.value)
        assert "try again later" in excinfo.value.tip

def test_timeout(client):
    with requests_mock.Mocker() as m:
        m.get("https://jules.googleapis.com/v1alpha/sources", exc=requests.exceptions.Timeout)

        with pytest.raises(AppError) as excinfo:
            client.list_sources()

        assert "Jules API Request Timed Out" in str(excinfo.value)

def test_connection_error(client):
    with requests_mock.Mocker() as m:
        m.get("https://jules.googleapis.com/v1alpha/sources", exc=requests.exceptions.ConnectionError)

        with pytest.raises(AppError) as excinfo:
            client.list_sources()

        assert "Jules API Connection Failed" in str(excinfo.value)

def test_create_session(client):
    with requests_mock.Mocker() as m:
        m.post("https://jules.googleapis.com/v1alpha/sessions", json={"name": "sessions/123"})
        response = client.create_session("source-1", "do something")
        assert response == {"name": "sessions/123"}
        assert m.last_request.json()["prompt"] == "do something"

def test_source_exists_error_propagation(client):
    with requests_mock.Mocker() as m:
        m.get("https://jules.googleapis.com/v1alpha/sources", status_code=500)

        with pytest.raises(AppError) as excinfo:
            client.source_exists("some-source")

        assert "Jules API Server Error" in str(excinfo.value)

def test_is_session_complete_error_propagation(client):
    with requests_mock.Mocker() as m:
        m.get("https://jules.googleapis.com/v1alpha/sessions/123", status_code=403)

        with pytest.raises(AppError) as excinfo:
            client.is_session_complete("123")

        assert "Jules API Permission Denied" in str(excinfo.value)
