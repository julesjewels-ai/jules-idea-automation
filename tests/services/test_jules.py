
import pytest
import os
from unittest.mock import MagicMock, patch
from src.services.jules import JulesClient

# Mock environment variable
@pytest.fixture
def mock_env():
    with patch.dict(os.environ, {"JULES_API_KEY": "test-key"}):
        yield

@pytest.fixture
def jules_client(mock_env):
    with patch("requests.Session") as mock_session:
        client = JulesClient()
        # Mock the session object
        client.session = MagicMock()
        client.session.headers = {}
        yield client

def test_jules_client_init_error():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="JULES_API_KEY environment variable is not set"):
            JulesClient()

def test_list_sources(jules_client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"sources": []}
    jules_client.session.get.return_value = mock_response

    sources = jules_client.list_sources()

    assert sources == {"sources": []}
    jules_client.session.get.assert_called_once()
    assert jules_client.session.get.call_args[0][0].endswith("/sources")

def test_create_session(jules_client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": "123"}
    jules_client.session.post.return_value = mock_response

    session = jules_client.create_session("source-1", "my prompt")

    assert session == {"id": "123"}
    jules_client.session.post.assert_called_once()
    assert jules_client.session.post.call_args[0][0].endswith("/sessions")
    assert jules_client.session.post.call_args[1]["json"]["prompt"] == "my prompt"

def test_get_session(jules_client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": "123"}
    jules_client.session.get.return_value = mock_response

    session = jules_client.get_session("123")

    assert session == {"id": "123"}
    jules_client.session.get.assert_called_once()
    assert jules_client.session.get.call_args[0][0].endswith("/sessions/123")

def test_list_activities(jules_client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"activities": []}
    jules_client.session.get.return_value = mock_response

    activities = jules_client.list_activities("123")

    assert activities == {"activities": []}
    jules_client.session.get.assert_called_once()
    assert "/sessions/123/activities" in jules_client.session.get.call_args[0][0]

def test_is_session_complete_with_pr(jules_client):
    # Mock get_session response with PR
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "id": "123",
        "outputs": [{"pullRequest": {"url": "http://pr.url"}}]
    }
    jules_client.session.get.return_value = mock_response

    is_complete, pr_url = jules_client.is_session_complete("123")

    assert is_complete is True
    assert pr_url == "http://pr.url"

def test_is_session_complete_with_activity(jules_client):
    # Mock get_session response without PR
    mock_session_resp = MagicMock()
    mock_session_resp.json.return_value = {"id": "123", "outputs": []}

    # Mock list_activities response with completion
    mock_activity_resp = MagicMock()
    mock_activity_resp.json.return_value = {
        "activities": [{"sessionCompleted": {}}]
    }

    jules_client.session.get.side_effect = [mock_session_resp, mock_activity_resp]

    is_complete, pr_url = jules_client.is_session_complete("123")

    assert is_complete is True
    assert pr_url is None
