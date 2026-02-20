from unittest.mock import patch
from src.cli.commands import watch_session


@patch('src.services.jules.JulesClient')
@patch('src.utils.polling.time.sleep')  # Speed up tests
def test_watch_session_success(mock_sleep, MockJulesClient, capsys):
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

    is_complete, pr_url = watch_session("sess_123", timeout=1)

    assert is_complete is True
    assert pr_url == "http://pr-url"
    # Should have polled 3 times
    assert mock_client.is_session_complete.call_count == 3


@patch('src.services.jules.JulesClient')
@patch('src.utils.polling.time.sleep')
def test_watch_session_timeout(mock_sleep, MockJulesClient, capsys):
    mock_client = MockJulesClient.return_value
    # Always incomplete
    mock_client.is_session_complete.return_value = (False, None)
    mock_client.get_session.return_value = {"url": "http://session-url"}

    # Short timeout to force exit
    is_complete, pr_url = watch_session("sess_123", timeout=0.1)

    assert is_complete is False
    assert pr_url is None
