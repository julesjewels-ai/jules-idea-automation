import pytest
import requests
from src.services.jules import JulesClient
from src.utils.errors import ConfigurationError

@pytest.fixture
def jules_client(monkeypatch):
    monkeypatch.setenv("JULES_API_KEY", "test_key")
    return JulesClient()

def test_init_raises_error_without_api_key(monkeypatch):
    monkeypatch.delenv("JULES_API_KEY", raising=False)
    with pytest.raises(ConfigurationError):
        JulesClient(api_key=None)

def test_init_with_explicit_api_key():
    client = JulesClient(api_key="explicit_key")
    assert client.api_key == "explicit_key"

def test_list_sources(jules_client, requests_mock):
    mock_response = {"sources": [{"name": "source1"}]}
    requests_mock.get("https://jules.googleapis.com/v1alpha/sources", json=mock_response)

    result = jules_client.list_sources()
    assert result == mock_response
    assert requests_mock.last_request.headers["x-goog-api-key"] == "test_key"

def test_create_session(jules_client, requests_mock):
    mock_response = {"name": "session1"}
    requests_mock.post("https://jules.googleapis.com/v1alpha/sessions", json=mock_response)

    result = jules_client.create_session("source1", "test prompt")
    assert result == mock_response

    payload = requests_mock.last_request.json()
    assert payload["prompt"] == "test prompt"
    assert payload["sourceContext"]["source"] == "source1"

def test_source_exists(jules_client, requests_mock):
    mock_response = {"sources": [{"name": "source1"}, {"name": "source2"}]}
    requests_mock.get("https://jules.googleapis.com/v1alpha/sources", json=mock_response)

    assert jules_client.source_exists("source1") is True
    assert jules_client.source_exists("source3") is False

def test_get_session(jules_client, requests_mock):
    mock_response = {"name": "session1"}
    requests_mock.get("https://jules.googleapis.com/v1alpha/sessions/123", json=mock_response)

    result = jules_client.get_session("123")
    assert result == mock_response

def test_list_sessions(jules_client, requests_mock):
    mock_response = {"sessions": []}
    requests_mock.get("https://jules.googleapis.com/v1alpha/sessions?pageSize=10", json=mock_response)

    result = jules_client.list_sessions()
    assert result == mock_response

def test_list_activities(jules_client, requests_mock):
    mock_response = {"activities": []}
    requests_mock.get("https://jules.googleapis.com/v1alpha/sessions/123/activities?pageSize=30", json=mock_response)

    result = jules_client.list_activities("123")
    assert result == mock_response

def test_send_message(jules_client, requests_mock):
    mock_response = {"name": "message1"}
    requests_mock.post("https://jules.googleapis.com/v1alpha/sessions/123:sendMessage", json=mock_response)

    result = jules_client.send_message("123", "follow up")
    assert result == mock_response
    assert requests_mock.last_request.json() == {"prompt": "follow up"}

def test_approve_plan(jules_client, requests_mock):
    mock_response = {"name": "plan1"}
    requests_mock.post("https://jules.googleapis.com/v1alpha/sessions/123:approvePlan", json=mock_response)

    result = jules_client.approve_plan("123")
    assert result == mock_response

def test_is_session_complete_with_pr(jules_client, requests_mock):
    session_response = {
        "outputs": [{"pullRequest": {"url": "http://pr.url"}}]
    }
    requests_mock.get("https://jules.googleapis.com/v1alpha/sessions/123", json=session_response)

    is_complete, pr_url = jules_client.is_session_complete("123")
    assert is_complete is True
    assert pr_url == "http://pr.url"

def test_is_session_complete_via_activity(jules_client, requests_mock):
    session_response = {"outputs": []}
    activity_response = {
        "activities": [{"sessionCompleted": {}}]
    }

    requests_mock.get("https://jules.googleapis.com/v1alpha/sessions/123", json=session_response)
    requests_mock.get("https://jules.googleapis.com/v1alpha/sessions/123/activities?pageSize=30", json=activity_response)

    is_complete, pr_url = jules_client.is_session_complete("123")
    assert is_complete is True
    assert pr_url is None

def test_is_session_incomplete(jules_client, requests_mock):
    session_response = {"outputs": []}
    activity_response = {"activities": []}

    requests_mock.get("https://jules.googleapis.com/v1alpha/sessions/123", json=session_response)
    requests_mock.get("https://jules.googleapis.com/v1alpha/sessions/123/activities?pageSize=30", json=activity_response)

    is_complete, pr_url = jules_client.is_session_complete("123")
    assert is_complete is False
    assert pr_url is None

def test_send_message_empty_response(jules_client, requests_mock):
    # Simulate empty text response which happens sometimes with actions
    requests_mock.post("https://jules.googleapis.com/v1alpha/sessions/123:sendMessage", text="")

    result = jules_client.send_message("123", "prompt")
    assert result == {}

def test_approve_plan_empty_response(jules_client, requests_mock):
    requests_mock.post("https://jules.googleapis.com/v1alpha/sessions/123:approvePlan", text="")

    result = jules_client.approve_plan("123")
    assert result == {}

def test_http_error(jules_client, requests_mock):
    requests_mock.get("https://jules.googleapis.com/v1alpha/sources", status_code=500)

    with pytest.raises(requests.exceptions.HTTPError):
        jules_client.list_sources()
