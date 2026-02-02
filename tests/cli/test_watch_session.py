import pytest
from unittest.mock import MagicMock, patch, call
from src.cli.commands import watch_session
import src.services.jules

@patch('src.services.jules.JulesClient')
@patch('src.cli.commands.Spinner')
@patch('src.utils.polling.time.sleep')
@patch('src.cli.commands.print_watch_complete')
@patch('src.cli.commands.print_watch_timeout')
def test_watch_session_success(mock_print_timeout, mock_print_complete, mock_sleep, mock_spinner, mock_jules_client_class):
    # Setup
    mock_jules = mock_jules_client_class.return_value
    mock_spinner_instance = mock_spinner.return_value
    mock_spinner_instance.__enter__.return_value = mock_spinner_instance

    # Sequence of is_session_complete responses: False, False, True
    mock_jules.is_session_complete.side_effect = [
        (False, None),
        (False, None),
        (True, "http://pr.url")
    ]

    # Sequence of list_activities
    mock_jules.list_activities.side_effect = [
        {"activities": [{"progressUpdated": {"title": "Step 1"}}]},
        {"activities": [{"progressUpdated": {"title": "Step 2"}}]},
    ]

    # Execute
    result = watch_session("session-123", timeout=100)

    # Verify
    assert result == (True, "http://pr.url")
    assert mock_jules.is_session_complete.call_count == 3
    assert mock_print_complete.called
    assert not mock_print_timeout.called

    # Check spinner updates
    # We expect updates for the first two iterations
    assert mock_spinner_instance.update.call_count >= 2

@patch('src.services.jules.JulesClient')
@patch('src.cli.commands.Spinner')
@patch('src.utils.polling.time.sleep')
@patch('src.cli.commands.print_watch_complete')
@patch('src.cli.commands.print_watch_timeout')
def test_watch_session_timeout(mock_print_timeout, mock_print_complete, mock_sleep, mock_spinner, mock_jules_client_class):
    # Setup
    mock_jules = mock_jules_client_class.return_value
    mock_spinner_instance = mock_spinner.return_value
    mock_spinner_instance.__enter__.return_value = mock_spinner_instance

    # Always incomplete
    mock_jules.is_session_complete.return_value = (False, None)
    mock_jules.list_activities.return_value = {}
    mock_jules.get_session.return_value = {'url': 'http://session.url'}

    # Execute
    result = watch_session("session-123", timeout=70)

    # Verify
    assert result == (False, None)
    assert mock_print_timeout.called
    assert not mock_print_complete.called

@patch('src.services.jules.JulesClient')
@patch('src.cli.commands.Spinner')
@patch('src.utils.polling.time.sleep')
@patch('src.cli.commands.print_watch_timeout')
def test_watch_session_api_error(mock_print_timeout, mock_sleep, mock_spinner, mock_jules_client_class):
    # Setup
    mock_jules = mock_jules_client_class.return_value
    mock_spinner_instance = mock_spinner.return_value
    mock_spinner_instance.__enter__.return_value = mock_spinner_instance

    mock_jules.is_session_complete.return_value = (False, None)
    # Simulate API error
    mock_jules.list_activities.side_effect = Exception("API Error")
    mock_jules.get_session.return_value = {'url': 'http://session.url'}

    # We need to stop the loop eventually, let's use a short timeout
    watch_session("session-123", timeout=40)

    # Verify spinner update with "Polling..." when exception occurs
    calls = mock_spinner_instance.update.call_args_list
    # Check if any call contains "Polling..."
    found_polling = any("Polling..." in str(c) for c in calls)
    assert found_polling
