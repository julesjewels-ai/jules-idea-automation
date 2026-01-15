
import pytest
from unittest.mock import MagicMock, patch, call
from src.cli.commands import watch_session
import src.services.jules

# Patch the sleep function in the utility module where it is actually called
@patch('src.utils.polling.time.sleep')
@patch('src.cli.commands.Spinner')
@patch('src.services.jules.JulesClient')
@patch('src.cli.commands.print_watch_complete')
@patch('src.cli.commands.print_watch_timeout')
def test_watch_session_success(mock_timeout, mock_complete, mock_jules_cls, mock_spinner, mock_sleep):
    # Setup
    mock_client = mock_jules_cls.return_value
    mock_client.is_session_complete.side_effect = [
        (False, None), # First check
        (True, "http://pr.url")  # Second check
    ]

    # Mock activities
    mock_client.list_activities.return_value = {
        "activities": [{"progressUpdated": {"title": "Building..."}}]
    }

    # Execute
    result = watch_session("123", timeout=100)

    # Verify
    assert result == (True, "http://pr.url")
    mock_complete.assert_called_once()
    assert mock_sleep.call_count == 1

@patch('src.utils.polling.time.sleep')
@patch('src.cli.commands.Spinner')
@patch('src.services.jules.JulesClient')
@patch('src.cli.commands.print_watch_complete')
@patch('src.cli.commands.print_watch_timeout')
def test_watch_session_timeout(mock_print_timeout, mock_print_complete, mock_jules_cls, mock_spinner, mock_sleep):
    # Setup
    mock_client = mock_jules_cls.return_value
    mock_client.is_session_complete.return_value = (False, None)
    mock_client.get_session.return_value = {"url": "http://session.url"}
    mock_client.list_activities.return_value = {}

    # Execute with short timeout to force loop exit
    # We rely on mocked time.sleep not actually sleeping, but we need to advance the 'elapsed' variable
    # src.utils.polling.poll_with_result increments elapsed by interval (30)

    result = watch_session("123", timeout=60)

    # Verify
    assert result == (False, None)
    mock_print_timeout.assert_called_once()
    assert mock_sleep.call_count >= 2
