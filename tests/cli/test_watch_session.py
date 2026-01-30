
import pytest
from unittest.mock import MagicMock, patch, call
import src.services.jules # Ensure module is loaded
from src.cli.commands import watch_session

@patch('src.utils.polling.time.sleep')
@patch('src.cli.commands.Spinner')
@patch('src.services.jules.JulesClient')
@patch('src.cli.commands.print_watch_complete')
def test_watch_session_success(mock_print_complete, mock_jules_client_class, mock_spinner_class, mock_sleep):
    # Setup
    mock_client = mock_jules_client_class.return_value
    # First call: not complete, return pr_url=None
    # Second call: complete, return pr_url="http://pr"
    mock_client.is_session_complete.side_effect = [(False, None), (True, "http://pr")]

    mock_client.list_activities.return_value = {
        "activities": [{"progressUpdated": {"title": "Step 1"}}]
    }

    # Execute
    is_complete, pr_url = watch_session("session-123", timeout=100)

    # Verify
    assert is_complete is True
    assert pr_url == "http://pr"
    assert mock_client.is_session_complete.call_count == 2
    mock_sleep.assert_called_once() # Should sleep once between calls
    mock_print_complete.assert_called_once()

@patch('src.utils.polling.time.sleep')
@patch('src.cli.commands.Spinner')
@patch('src.services.jules.JulesClient')
@patch('src.cli.commands.print_watch_timeout')
def test_watch_session_timeout(mock_print_timeout, mock_jules_client_class, mock_spinner_class, mock_sleep):
    # Setup
    mock_client = mock_jules_client_class.return_value
    mock_client.is_session_complete.return_value = (False, None)
    mock_client.get_session.return_value = {"url": "http://session"}

    # Execute with short timeout to force loop exit
    # watch_session uses `elapsed += poll_interval` (30) inside the loop.
    # If timeout=40:
    # 1. elapsed=0. check -> false. sleep. elapsed=30.
    # 2. elapsed=30 < 40. check -> false. sleep. elapsed=60.
    # 3. elapsed=60 < 40 -> false. Loop ends.

    is_complete, pr_url = watch_session("session-123", timeout=40)

    # Verify
    assert is_complete is False
    assert pr_url is None
    assert mock_client.is_session_complete.call_count == 2
    mock_print_timeout.assert_called_once()

@patch('src.utils.polling.time.sleep')
@patch('src.cli.commands.Spinner')
@patch('src.services.jules.JulesClient')
@patch('src.cli.commands.print_watch_complete')
def test_watch_session_updates_spinner(mock_print_complete, mock_jules_client_class, mock_spinner_class, mock_sleep):
    # Setup
    mock_client = mock_jules_client_class.return_value
    mock_client.is_session_complete.side_effect = [(False, None), (False, None), (True, "http://pr")]
    mock_client.list_activities.side_effect = [
        {"activities": [{"progressUpdated": {"title": "Step 1"}}]},
        {"activities": [{"progressUpdated": {"title": "Step 2"}}]}
    ]

    mock_spinner_instance = mock_spinner_class.return_value.__enter__.return_value

    # Execute
    watch_session("session-123", timeout=100)

    # Verify spinner updates
    assert mock_spinner_instance.update.call_count >= 2
    args_list = mock_spinner_instance.update.call_args_list
    # Note: args_list[0][0][0] accesses the first argument of the first call
    assert "Step 1" in args_list[0][0][0]
    assert "Step 2" in args_list[1][0][0]
