
import pytest
from unittest.mock import MagicMock, patch, call
import src.services.jules # Ensure module is loaded for patching
from src.cli.commands import watch_session

@patch('src.cli.commands.Spinner')
@patch('src.services.jules.JulesClient')
@patch('src.cli.commands.time.sleep')
@patch('src.cli.commands.print_watch_complete')
@patch('src.cli.commands.print_watch_timeout')
def test_watch_session_complete(mock_print_timeout, mock_print_complete, mock_sleep, mock_jules_class, mock_spinner_class):
    # Setup
    mock_jules = mock_jules_class.return_value
    mock_spinner = mock_spinner_class.return_value
    mock_spinner.__enter__.return_value = mock_spinner

    # Mock sequence: incomplete, incomplete, complete
    mock_jules.is_session_complete.side_effect = [
        (False, None),
        (False, None),
        (True, "http://pr.url")
    ]

    mock_jules.list_activities.return_value = {
        "activities": [{"progressUpdated": {"title": "Activity 1"}}]
    }

    # Execute
    is_complete, pr_url = watch_session("session-123", timeout=100)

    # Verify
    assert is_complete is True
    assert pr_url == "http://pr.url"

    # Verify calls
    assert mock_jules.is_session_complete.call_count == 3
    assert mock_sleep.call_count == 2 # Called twice (after first two checks)

    # Verify spinner updates
    # We expect update calls for activity
    assert mock_spinner.update.call_count >= 2

    # Verify print
    mock_print_complete.assert_called_once()
    mock_print_timeout.assert_not_called()

@patch('src.cli.commands.Spinner')
@patch('src.services.jules.JulesClient')
@patch('src.cli.commands.time.sleep')
@patch('src.cli.commands.print_watch_complete')
@patch('src.cli.commands.print_watch_timeout')
def test_watch_session_timeout(mock_print_timeout, mock_print_complete, mock_sleep, mock_jules_class, mock_spinner_class):
    # Setup
    mock_jules = mock_jules_class.return_value
    mock_spinner = mock_spinner_class.return_value
    mock_spinner.__enter__.return_value = mock_spinner

    # Always incomplete
    mock_jules.is_session_complete.return_value = (False, None)
    mock_jules.get_session.return_value = {'url': 'http://session.url'}

    # Execute
    # Timeout=40, poll_interval=30
    # 1. check, sleep(30), elapsed=30
    # 2. check, sleep(30), elapsed=60 -> loop terminates
    is_complete, pr_url = watch_session("session-123", timeout=40)

    # Verify
    assert is_complete is False
    assert pr_url is None

    # Verify calls
    assert mock_jules.is_session_complete.call_count == 2
    assert mock_sleep.call_count == 2

    # Verify print
    mock_print_complete.assert_not_called()
    mock_print_timeout.assert_called_once_with(40, 'http://session.url')
