from unittest.mock import patch
from src.cli.commands import watch_session
# removed unused import


@patch('src.services.jules.JulesClient')
def test_watch_session_success(MockJulesClient, capsys):
    mock_client = MockJulesClient.return_value
    # Sequence: Not complete, Not complete, Complete

    mock_client.is_session_complete.side_effect = [
        (False, None),
        (False, None),
        (True, "http://pr-url")
    ]
    mock_client.list_activities.return_value = {
        "activities": [{"progressUpdated": {"title": "Working..."}}]
    }

    # Patch time.sleep to avoid waiting real time
    with patch('src.utils.polling.time.sleep'):
        is_complete, pr_url = watch_session("sess_123", timeout=100)

    assert is_complete is True
    assert pr_url == "http://pr-url"
    assert mock_client.is_session_complete.call_count == 3


@patch('src.services.jules.JulesClient')
def test_watch_session_timeout(MockJulesClient, capsys):
    mock_client = MockJulesClient.return_value
    # Always incomplete
    mock_client.is_session_complete.return_value = (False, None)
    mock_client.get_session.return_value = {"url": "http://session-url"}

    # Timeout smaller than interval (30) ensures only 1 call
    with patch('src.utils.polling.time.sleep'):
        is_complete, pr_url = watch_session("sess_123", timeout=10)

    assert is_complete is False
    assert pr_url is None
