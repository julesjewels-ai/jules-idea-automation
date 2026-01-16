
import pytest
import requests
import requests_mock
from src.services.jules import JulesClient

@pytest.fixture
def jules_client(monkeypatch):
    monkeypatch.setenv("JULES_API_KEY", "fake_key")
    return JulesClient()

def test_jules_client_init_no_key(monkeypatch):
    monkeypatch.delenv("JULES_API_KEY", raising=False)
    with pytest.raises(ValueError, match="JULES_API_KEY environment variable is not set"):
        JulesClient()

def test_list_sources(jules_client):
    with requests_mock.Mocker() as m:
        m.get("https://jules.googleapis.com/v1alpha/sources", json={"sources": []})
        response = jules_client.list_sources()
        assert response == {"sources": []}
        assert m.called
        assert m.last_request.headers["x-goog-api-key"] == "fake_key"

def test_create_session(jules_client):
    with requests_mock.Mocker() as m:
        m.post("https://jules.googleapis.com/v1alpha/sessions", json={"id": "123"})
        response = jules_client.create_session("source_id", "prompt")
        assert response == {"id": "123"}
        assert m.called
        assert m.last_request.json()["prompt"] == "prompt"

def test_request_error(jules_client):
    with requests_mock.Mocker() as m:
        m.get("https://jules.googleapis.com/v1alpha/sources", status_code=500, text="Internal Server Error")
        with pytest.raises(requests.exceptions.HTTPError):
            jules_client.list_sources()

def test_list_sessions_pagination(jules_client):
    with requests_mock.Mocker() as m:
        m.get("https://jules.googleapis.com/v1alpha/sessions", json={"sessions": []})
        jules_client.list_sessions(page_size=20)
        assert m.called
        assert "pageSize=20" in m.last_request.url

def test_send_message(jules_client):
    with requests_mock.Mocker() as m:
        m.post("https://jules.googleapis.com/v1alpha/sessions/123:sendMessage", json={"response": "ok"})
        response = jules_client.send_message("123", "msg")
        assert response == {"response": "ok"}
        assert m.last_request.json() == {"prompt": "msg"}
