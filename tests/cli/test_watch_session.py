import pytest
from unittest.mock import MagicMock, patch, call
# Lazy import handling: we need to import the module to patch objects used in it
# But watch_session does imports inside the function.
# Patching src.services.jules.JulesClient affects the import inside watch_session
from src.cli.commands import watch_session

@patch('src.cli.commands.time.time')
@patch('src.cli.commands.print_watch_complete')
@patch('src.utils.polling.time.sleep')
@patch('src.cli.commands.Spinner')
@patch('src.services.jules.JulesClient')
def test_watch_session_success(mock_jules_cls, mock_spinner_cls, mock_sleep, mock_print_complete, mock_time):
    # Setup
    mock_time.side_effect = [0, 30] # start_time, end_time
    mock_jules = mock_jules_cls.return_value
    # is_session_complete returns (False, None) first, then (True, "http://pr")
    mock_jules.is_session_complete.side_effect = [
        (False, None),
        (True, "http://pr")
    ]

    # Mock list_activities for the status update
    mock_jules.list_activities.return_value = {
        "activities": [{"progressUpdated": {"title": "Generating code..."}}]
    }

    mock_spinner_instance = mock_spinner_cls.return_value
    # Spinner is used as a context manager: with Spinner(...) as spinner:
    # So we need to ensure __enter__ returns the instance (or a mock we check)
    mock_spinner_instance.__enter__.return_value = mock_spinner_instance

    # Execute
    is_complete, pr_url = watch_session("sess-123", timeout=100)

    # Verify results
    assert is_complete is True
    assert pr_url == "http://pr"

    # Verify interactions
    assert mock_jules.is_session_complete.call_count == 2
    # Sleep should be called once between polls
    mock_sleep.assert_called_once_with(30)

    # Spinner update should have been called with the activity title
    # We check if update was called at least once
    mock_spinner_instance.update.assert_called()

    # Verify completion print
    # elapsed should be 30 because we slept once
    mock_print_complete.assert_called_once_with(30, "http://pr")

@patch('src.cli.commands.time.time')
@patch('src.cli.commands.print_watch_timeout')
@patch('src.utils.polling.time.sleep')
@patch('src.cli.commands.Spinner')
@patch('src.services.jules.JulesClient')
def test_watch_session_timeout(mock_jules_cls, mock_spinner_cls, mock_sleep, mock_print_timeout, mock_time):
    # Setup
    mock_time.side_effect = [0, 40]
    mock_jules = mock_jules_cls.return_value
    mock_jules.is_session_complete.return_value = (False, None)
    mock_jules.get_session.return_value = {"url": "http://session"}

    # Execute with timeout=40. Interval=30.
    # 0s: Poll -> False. Sleep 30s. Elapsed=30.
    # 30s: Poll -> False. Sleep 30s. Elapsed=60.
    # 60s: Loop terminates (60 < 40 is False).
    is_complete, pr_url = watch_session("sess-123", timeout=40)

    # Verify results
    assert is_complete is False
    assert pr_url is None

    # Verify interactions
    assert mock_sleep.call_count == 2
    mock_print_timeout.assert_called_once_with(40, "http://session")
