"""Tests for watch_session utility."""

from unittest.mock import patch
from src.cli.commands import watch_session


@patch('src.services.jules.JulesClient')
@patch('src.utils.polling.time.sleep')  # Speed up tests
def test_watch_session_completes(mock_sleep, mock_jules_cls):
    """Test watch_session when session completes successfully."""
    mock_client = mock_jules_cls.return_value
    # First incomplete, then complete
    mock_client.is_session_complete.side_effect = [
        (False, None),
        (True, "http://pr.url")
    ]
    mock_client.list_activities.return_value = {"activities": []}

    # Use a large timeout, but poll_with_result should exit early due to True return
    # The default interval in watch_session is 30, so we need mock_sleep to absorb that
    is_complete, pr_url = watch_session("123", timeout=100)

    assert is_complete is True
    assert pr_url == "http://pr.url"
    assert mock_client.is_session_complete.call_count == 2


@patch('src.services.jules.JulesClient')
@patch('src.utils.polling.time.sleep')
def test_watch_session_timeout(mock_sleep, mock_jules_cls):
    """Test watch_session timeout."""
    mock_client = mock_jules_cls.return_value
    mock_client.is_session_complete.return_value = (False, None)
    mock_client.list_activities.return_value = {}
    mock_client.get_session.return_value = {"url": "http://session"}

    # Short timeout to force exit
    is_complete, pr_url = watch_session("123", timeout=1)

    assert is_complete is False
    assert pr_url is None
