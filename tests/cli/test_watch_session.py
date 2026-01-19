import pytest
from unittest.mock import MagicMock, patch, call
from src.cli.commands import watch_session

# Ensure module is loaded for patching
import src.services.jules

@patch('src.cli.commands.Spinner')
@patch('src.cli.commands.print_watch_complete')
@patch('src.cli.commands.print_watch_timeout')
@patch('src.services.jules.JulesClient')
def test_watch_session_complete(mock_jules_client_class, mock_print_timeout, mock_print_complete, mock_spinner):
    # Setup
    mock_client = mock_jules_client_class.return_value
    mock_client.is_session_complete.return_value = (True, "http://pr.url")

    # Execute
    is_complete, pr_url = watch_session("sess-123", timeout=10)

    # Verify
    assert is_complete is True
    assert pr_url == "http://pr.url"
    mock_client.is_session_complete.assert_called_with("sess-123")
    mock_print_complete.assert_called_once()
    mock_print_timeout.assert_not_called()

@patch('src.cli.commands.poll_with_result')
@patch('src.cli.commands.Spinner')
@patch('src.cli.commands.print_watch_complete')
@patch('src.services.jules.JulesClient')
def test_watch_session_delegates_to_poll(mock_jules, mock_print, mock_spinner, mock_poll):
    # Setup
    mock_poll.return_value = (True, "http://pr")

    # Execute
    watch_session("sess-123", timeout=60)

    # Verify
    mock_poll.assert_called_once()
    args, kwargs = mock_poll.call_args
    assert kwargs['timeout'] == 60
    assert kwargs['interval'] == 30
    assert callable(kwargs['check'])
    assert callable(kwargs['on_poll'])
    assert callable(kwargs['status_extractor'])

@patch('src.cli.commands.Spinner')
@patch('src.cli.commands.print_watch_timeout')
@patch('src.services.jules.JulesClient')
def test_watch_session_timeout(mock_jules_client_class, mock_print_timeout, mock_spinner):
    # Setup
    mock_client = mock_jules_client_class.return_value
    mock_client.is_session_complete.return_value = (False, None)

    # Mock time.sleep to run immediately to avoid delay
    with patch('src.utils.polling.time.sleep') as mock_sleep:
        # We need to simulate timeout. poll_with_result will loop.
        # But wait, if I use the real poll_with_result, I need to make sure 'check' returns False
        # and timeout is small enough.

        # But better to mock poll_with_result to return (False, None) to test the outer logic
        with patch('src.cli.commands.poll_with_result', return_value=(False, None)):
             mock_client.get_session.return_value = {'url': 'http://session'}

             is_complete, pr_url = watch_session("sess-123", timeout=1)

             assert is_complete is False
             assert pr_url is None
             mock_print_timeout.assert_called_once()
