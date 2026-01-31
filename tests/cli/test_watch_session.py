import pytest
from unittest.mock import MagicMock, patch, call
from src.cli.commands import watch_session

# Ensure module is loaded
import src.services.jules
import src.utils.polling

@patch('src.cli.commands.Spinner')
@patch('src.services.jules.JulesClient')
@patch('src.cli.commands.print_watch_complete')
@patch('src.utils.polling.poll_with_result')
def test_watch_session_success(mock_poll, mock_print_complete, mock_jules_class, mock_spinner_class):
    # Setup
    mock_jules = mock_jules_class.return_value
    mock_poll.return_value = (True, "http://pr.url", 120)

    mock_spinner_instance = mock_spinner_class.return_value
    mock_spinner = mock_spinner_instance.__enter__.return_value

    # Execute
    result = watch_session("session-123", timeout=100)

    # Verify
    assert result == (True, "http://pr.url")

    # Verify poll_with_result args
    args, kwargs = mock_poll.call_args
    assert kwargs['timeout'] == 100
    assert kwargs['interval'] == 30

    # Verify callbacks
    status_extractor = kwargs['status_extractor']
    on_poll = kwargs['on_poll']

    # Test status_extractor
    mock_jules.list_activities.return_value = {
        "activities": [{"progressUpdated": {"title": "Doing things"}}]
    }
    assert status_extractor() == "Doing things"

    # Test on_poll
    # Note: format_duration(60) -> "1m 0s" or "60s" depending on implementation.
    # Let's check what format_duration does.
    # For now assuming "1m 0s" or checking substring.
    # But wait, format_duration is imported in src.cli.commands.
    # I should verify what it outputs or mock it too.
    # I'll rely on string containment or loose check if unsure, or read format_duration.

    on_poll(60, "Doing things")
    # Check if update called with string containing status
    mock_spinner.update.assert_called()
    call_arg = mock_spinner.update.call_args[0][0]
    assert "Doing things" in call_arg

    mock_print_complete.assert_called_once_with(120, "http://pr.url")

@patch('src.cli.commands.Spinner')
@patch('src.services.jules.JulesClient')
@patch('src.cli.commands.print_watch_timeout')
@patch('src.utils.polling.poll_with_result')
def test_watch_session_timeout(mock_poll, mock_print_timeout, mock_jules_class, mock_spinner_class):
    # Setup
    mock_poll.return_value = (False, None, 40)
    mock_jules = mock_jules_class.return_value
    mock_jules.get_session.return_value = {'url': 'http://session.url'}

    # Execute
    result = watch_session("session-123", timeout=40)

    # Verify
    assert result == (False, None)
    mock_print_timeout.assert_called_once()

@patch('src.cli.commands.Spinner')
@patch('src.services.jules.JulesClient')
@patch('src.utils.polling.poll_with_result')
def test_watch_session_api_error(mock_poll, mock_jules_class, mock_spinner_class):
    # Setup
    mock_poll.return_value = (False, None, 0)
    mock_jules = mock_jules_class.return_value
    mock_jules.get_session.return_value = {'url': 'http://session.url'}

    mock_spinner_instance = mock_spinner_class.return_value
    mock_spinner = mock_spinner_instance.__enter__.return_value

    # Execute
    watch_session("session-123", timeout=40)

    # Get the callback
    args, kwargs = mock_poll.call_args
    status_extractor = kwargs['status_extractor']

    # Simulate API error
    mock_jules.list_activities.side_effect = Exception("API Error")

    # Verify it returns "Polling..." instead of raising
    assert status_extractor() == "Polling..."
