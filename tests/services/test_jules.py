
import pytest
import requests_mock
from src.services.jules import JulesClient
from src.utils.errors import ConfigurationError

@pytest.fixture
def jules_client(monkeypatch):
    monkeypatch.setenv("JULES_API_KEY", "test-key")
    return JulesClient()

def test_init_no_api_key(monkeypatch):
    monkeypatch.delenv("JULES_API_KEY", raising=False)
    with pytest.raises(ConfigurationError):
        JulesClient()

def test_list_sources(jules_client):
    with requests_mock.Mocker() as m:
        m.get("https://jules.googleapis.com/v1alpha/sources", json={"sources": []})
        result = jules_client.list_sources()
        assert result == {"sources": []}
        assert m.last_request.headers["x-goog-api-key"] == "test-key"

def test_create_session(jules_client):
    with requests_mock.Mocker() as m:
        m.post("https://jules.googleapis.com/v1alpha/sessions", json={"name": "sessions/123"})
        result = jules_client.create_session("source-id", "test prompt")
        assert result == {"name": "sessions/123"}
        assert m.last_request.json()["prompt"] == "test prompt"

def test_source_exists_true(jules_client):
    with requests_mock.Mocker() as m:
        m.get("https://jules.googleapis.com/v1alpha/sources", json={"sources": [{"name": "source-id"}]})
        assert jules_client.source_exists("source-id") is True

def test_source_exists_false(jules_client):
    with requests_mock.Mocker() as m:
        m.get("https://jules.googleapis.com/v1alpha/sources", json={"sources": [{"name": "other-id"}]})
        assert jules_client.source_exists("source-id") is False

def test_get_session(jules_client):
    with requests_mock.Mocker() as m:
        m.get("https://jules.googleapis.com/v1alpha/sessions/123", json={"name": "sessions/123"})
        result = jules_client.get_session("123")
        assert result == {"name": "sessions/123"}

def test_list_sessions(jules_client):
    with requests_mock.Mocker() as m:
        # Check query param handling
        m.get("https://jules.googleapis.com/v1alpha/sessions?pageSize=10", json={"sessions": []})
        result = jules_client.list_sessions(page_size=10)
        assert result == {"sessions": []}

def test_list_activities(jules_client):
    with requests_mock.Mocker() as m:
        m.get("https://jules.googleapis.com/v1alpha/sessions/123/activities?pageSize=30", json={"activities": []})
        result = jules_client.list_activities("123")
        assert result == {"activities": []}

def test_send_message(jules_client):
    with requests_mock.Mocker() as m:
        m.post("https://jules.googleapis.com/v1alpha/sessions/123:sendMessage", json={"response": "ok"})
        result = jules_client.send_message("123", "follow up")
        assert result == {"response": "ok"}
        assert m.last_request.json()["prompt"] == "follow up"

def test_approve_plan(jules_client):
    with requests_mock.Mocker() as m:
        m.post("https://jules.googleapis.com/v1alpha/sessions/123:approvePlan", json={"response": "approved"})
        result = jules_client.approve_plan("123")
        assert result == {"response": "approved"}

def test_is_session_complete_with_pr(jules_client):
    with requests_mock.Mocker() as m:
        m.get("https://jules.googleapis.com/v1alpha/sessions/123", json={
            "outputs": [{"pullRequest": {"url": "http://pr.url"}}]
        })
        is_complete, pr_url = jules_client.is_session_complete("123")
        assert is_complete is True
        assert pr_url == "http://pr.url"

def test_is_session_complete_via_activity(jules_client):
    with requests_mock.Mocker() as m:
        m.get("https://jules.googleapis.com/v1alpha/sessions/123", json={"outputs": []})
        m.get("https://jules.googleapis.com/v1alpha/sessions/123/activities?pageSize=30", json={
            "activities": [{"sessionCompleted": {}}]
        })
        is_complete, pr_url = jules_client.is_session_complete("123")
        assert is_complete is True
        assert pr_url is None

def test_is_session_incomplete(jules_client):
    with requests_mock.Mocker() as m:
        m.get("https://jules.googleapis.com/v1alpha/sessions/123", json={"outputs": []})
        m.get("https://jules.googleapis.com/v1alpha/sessions/123/activities?pageSize=30", json={
            "activities": [{"someOtherActivity": {}}]
        })
        is_complete, pr_url = jules_client.is_session_complete("123")
        assert is_complete is False
        assert pr_url is None
