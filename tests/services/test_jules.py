import pytest
import requests
from src.services.jules import JulesClient
from src.utils.errors import AppError, ConfigurationError

# Mock environment variable
@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("JULES_API_KEY", "test_key")

def test_jules_client_init_no_key(monkeypatch):
    monkeypatch.delenv("JULES_API_KEY", raising=False)
    with pytest.raises(ConfigurationError, match="JULES_API_KEY environment variable is not set"):
        JulesClient(api_key=None)

def test_jules_client_init_with_key(mock_env):
    client = JulesClient()
    assert client.api_key == "test_key"
    assert client.headers["x-goog-api-key"] == "test_key"

def test_list_sources_success(mock_env, requests_mock):
    client = JulesClient()
    mock_response = {"sources": [{"name": "source1"}]}
    requests_mock.get(f"{client.base_url}/sources", json=mock_response)

    response = client.list_sources()
    assert response == mock_response

def test_list_sources_http_error_401(mock_env, requests_mock):
    client = JulesClient()
    requests_mock.get(f"{client.base_url}/sources", status_code=401, text="Unauthorized")

    with pytest.raises(AppError) as excinfo:
        client.list_sources()

    assert "Jules API Error" in str(excinfo.value)
    assert "Your JULES_API_KEY appears to be invalid" in excinfo.value.tip

def test_list_sources_http_error_403(mock_env, requests_mock):
    client = JulesClient()
    requests_mock.get(f"{client.base_url}/sources", status_code=403, text="Forbidden")

    with pytest.raises(AppError) as excinfo:
        client.list_sources()

    assert "permission" in excinfo.value.tip

def test_create_session_success(mock_env, requests_mock):
    client = JulesClient()
    mock_response = {"name": "sessions/123", "state": "ACTIVE"}
    requests_mock.post(f"{client.base_url}/sessions", json=mock_response)

    response = client.create_session("source1", "test prompt")
    assert response == mock_response

    # Verify payload
    assert requests_mock.last_request.json()["sourceContext"]["source"] == "source1"
    assert requests_mock.last_request.json()["prompt"] == "test prompt"

def test_is_session_complete_with_pr(mock_env, requests_mock):
    client = JulesClient()
    session_id = "123"

    mock_session = {
        "name": f"sessions/{session_id}",
        "outputs": [
            {
                "pullRequest": {
                    "url": "https://github.com/user/repo/pull/1"
                }
            }
        ]
    }

    requests_mock.get(f"{client.base_url}/sessions/{session_id}", json=mock_session)

    is_complete, pr_url = client.is_session_complete(session_id)
    assert is_complete is True
    assert pr_url == "https://github.com/user/repo/pull/1"

def test_is_session_complete_via_activity(mock_env, requests_mock):
    client = JulesClient()
    session_id = "123"

    mock_session = {"name": f"sessions/{session_id}", "outputs": []}
    mock_activities = {
        "activities": [
            {"sessionCompleted": {}}
        ]
    }

    requests_mock.get(f"{client.base_url}/sessions/{session_id}", json=mock_session)
    requests_mock.get(f"{client.base_url}/sessions/{session_id}/activities?pageSize=30", json=mock_activities)

    is_complete, pr_url = client.is_session_complete(session_id)
    assert is_complete is True
    assert pr_url is None

def test_connection_error(mock_env, requests_mock):
    client = JulesClient()
    requests_mock.get(f"{client.base_url}/sources", exc=requests.exceptions.ConnectionError)

    with pytest.raises(AppError) as excinfo:
        client.list_sources()

    assert "Connection failed" in str(excinfo.value)
    assert "internet connection" in excinfo.value.tip
