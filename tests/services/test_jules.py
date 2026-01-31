import pytest
import requests_mock
from src.services.jules import JulesClient
from src.utils.errors import ConfigurationError, JulesApiError

API_KEY = "test-api-key"
BASE_URL = "https://jules.googleapis.com/v1alpha"

@pytest.fixture
def client():
    return JulesClient(api_key=API_KEY)

def test_init_no_api_key(monkeypatch):
    monkeypatch.delenv("JULES_API_KEY", raising=False)
    with pytest.raises(ConfigurationError):
        JulesClient()

def test_list_sources(client):
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/sources", json={"sources": [{"name": "source1"}]})
        response = client.list_sources()
        assert response == {"sources": [{"name": "source1"}]}
        assert m.last_request.headers["x-goog-api-key"] == API_KEY

def test_create_session(client):
    with requests_mock.Mocker() as m:
        m.post(f"{BASE_URL}/sessions", json={"name": "session1"})
        response = client.create_session("source1", "test prompt")
        assert response == {"name": "session1"}
        assert m.last_request.json()["prompt"] == "test prompt"
        assert m.last_request.json()["sourceContext"]["source"] == "source1"

def test_source_exists_true(client):
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/sources", json={"sources": [{"name": "source1"}]})
        assert client.source_exists("source1") is True

def test_source_exists_false(client):
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/sources", json={"sources": []})
        assert client.source_exists("source1") is False

def test_get_session(client):
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/sessions/123", json={"name": "session123"})
        response = client.get_session("123")
        assert response == {"name": "session123"}

def test_list_sessions(client):
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/sessions?pageSize=10", json={"sessions": []})
        response = client.list_sessions()
        assert response == {"sessions": []}

def test_list_activities(client):
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/sessions/123/activities?pageSize=30", json={"activities": []})
        response = client.list_activities("123")
        assert response == {"activities": []}

def test_send_message(client):
    with requests_mock.Mocker() as m:
        m.post(f"{BASE_URL}/sessions/123:sendMessage", json={"response": "ok"})
        response = client.send_message("123", "hello")
        assert response == {"response": "ok"}
        assert m.last_request.json()["prompt"] == "hello"

def test_approve_plan(client):
    with requests_mock.Mocker() as m:
        m.post(f"{BASE_URL}/sessions/123:approvePlan", json={"response": "ok"})
        response = client.approve_plan("123")
        assert response == {"response": "ok"}

def test_is_session_complete_with_pr(client):
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/sessions/123", json={
            "outputs": [{"pullRequest": {"url": "http://pr.url"}}]
        })
        is_complete, pr_url = client.is_session_complete("123")
        assert is_complete is True
        assert pr_url == "http://pr.url"

def test_is_session_complete_via_activity(client):
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/sessions/123", json={"outputs": []})
        m.get(f"{BASE_URL}/sessions/123/activities?pageSize=30", json={
            "activities": [{"sessionCompleted": {}}]
        })
        is_complete, pr_url = client.is_session_complete("123")
        assert is_complete is True
        assert pr_url is None

def test_is_session_incomplete(client):
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/sessions/123", json={"outputs": []})
        m.get(f"{BASE_URL}/sessions/123/activities?pageSize=30", json={"activities": []})
        is_complete, pr_url = client.is_session_complete("123")
        assert is_complete is False
        assert pr_url is None

def test_api_error_handling(client):
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/sources", status_code=403)
        with pytest.raises(JulesApiError) as excinfo:
            client.list_sources()
        assert "permission" in excinfo.value.tip
