import pytest
from unittest.mock import MagicMock, patch, call
from src.cli.commands import watch_session

# Ensure module is loaded for patching
import src.services.jules

@patch('src.cli.commands.Spinner')
@patch('src.services.jules.JulesClient')
@patch('src.cli.commands.print_watch_complete')
@patch('src.cli.commands.print_watch_timeout')
@patch('src.cli.commands.time.sleep')
def test_watch_session_success(mock_sleep, mock_print_timeout, mock_print_complete, mock_jules_client_class, mock_spinner_class):
    # Setup
    mock_client = mock_jules_client_class.return_value
    mock_spinner = mock_spinner_class.return_value
    mock_spinner.__enter__.return_value = mock_spinner

    # Mock sequence: incomplete, incomplete, complete
    mock_client.is_session_complete.side_effect = [
        (False, None),
        (False, None),
        (True, "http://github.com/pr/123")
    ]

    # Mock activity updates
    mock_client.list_activities.side_effect = [
        {"activities": [{"progressUpdated": {"title": "Activity 1"}}]},
        {"activities": [{"progressUpdated": {"title": "Activity 2"}}]},
        {"activities": []}
    ]

    # Execute
    is_complete, pr_url = watch_session("session-123", timeout=100)

    # Verify
    assert is_complete is True
    assert pr_url == "http://github.com/pr/123"

    # Verify polling
    assert mock_client.is_session_complete.call_count == 3
    assert mock_sleep.call_count == 2

    # Verify spinner updates
    mock_spinner.update.assert_has_calls([
        call("[0s] Activity 1"),
        call("[30s] Activity 2")
    ])

    mock_print_complete.assert_called_once()
    mock_print_timeout.assert_not_called()

@patch('src.cli.commands.Spinner')
@patch('src.services.jules.JulesClient')
@patch('src.cli.commands.print_watch_complete')
@patch('src.cli.commands.print_watch_timeout')
@patch('src.cli.commands.time.sleep')
def test_watch_session_timeout(mock_sleep, mock_print_timeout, mock_print_complete, mock_jules_client_class, mock_spinner_class):
    # Setup
    mock_client = mock_jules_client_class.return_value
    mock_spinner = mock_spinner_class.return_value
    mock_spinner.__enter__.return_value = mock_spinner

    # Always incomplete
    mock_client.is_session_complete.return_value = (False, None)
    mock_client.get_session.return_value = {'url': 'http://jules.app/session'}
    mock_client.list_activities.return_value = {}

    # Execute with short timeout to limit loops
    # watch_session loops while elapsed < timeout.
    # Logic:
    # Loop 1: elapsed=0. sleep(30). elapsed=30.
    # Loop 2: elapsed=30. sleep(30). elapsed=60.
    # Loop 3: elapsed=60. STOP (if timeout=60).

    is_complete, pr_url = watch_session("session-123", timeout=60)

    # Verify
    assert is_complete is False
    assert pr_url is None

    mock_print_complete.assert_not_called()
    mock_print_timeout.assert_called_once_with(60, 'http://jules.app/session')

@patch('src.cli.commands.Spinner')
@patch('src.services.jules.JulesClient')
@patch('src.cli.commands.time.sleep')
def test_watch_session_api_error(mock_sleep, mock_jules_client_class, mock_spinner_class):
    # Setup
    mock_client = mock_jules_client_class.return_value
    mock_spinner = mock_spinner_class.return_value
    mock_spinner.__enter__.return_value = mock_spinner

    mock_client.is_session_complete.side_effect = [(False, None), (True, "url")]

    # API error during activity check
    mock_client.list_activities.side_effect = Exception("API Error")

    # Execute
    watch_session("session-123", timeout=100)

    # Verify graceful handling
    mock_spinner.update.assert_called_with("[0s] Polling...")
