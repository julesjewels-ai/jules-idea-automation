
import pytest
from unittest.mock import MagicMock, patch, call
import src.services.jules  # Ensure module is loaded for patching
from src.cli.commands import watch_session

# Helper patch decorator for common mocks
def patch_common(func):
    @patch('src.cli.commands.Spinner')
    @patch('src.services.jules.JulesClient')
    @patch('src.cli.commands.print_watch_complete')
    @patch('src.cli.commands.print_watch_timeout')
    @patch('src.utils.polling.time.sleep')
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

@patch_common
def test_watch_session_success(mock_sleep, mock_print_timeout, mock_print_complete, mock_jules_class, mock_spinner_class):
    # Setup
    mock_jules = mock_jules_class.return_value
    mock_spinner = mock_spinner_class.return_value
    mock_spinner.__enter__.return_value = mock_spinner

    # Sequence: Not complete, then Complete
    # Note: loop checks is_session_complete
    mock_jules.is_session_complete.side_effect = [
        (False, None),
        (True, "http://pr.url")
    ]

    mock_jules.list_activities.return_value = {
        "activities": [{"progressUpdated": {"title": "Building..."}}]
    }

    # Execute
    result = watch_session("session-123", timeout=100)

    # Verify
    assert result == (True, "http://pr.url")
    assert mock_jules.is_session_complete.call_count == 2
    mock_print_complete.assert_called_once()
    mock_print_timeout.assert_not_called()

    # Verify spinner updates
    # The code calls spinner.update with formatted duration
    assert mock_spinner.update.called

@patch_common
def test_watch_session_timeout(mock_sleep, mock_print_timeout, mock_print_complete, mock_jules_class, mock_spinner_class):
    # Setup
    mock_jules = mock_jules_class.return_value
    mock_spinner = mock_spinner_class.return_value
    mock_spinner.__enter__.return_value = mock_spinner

    # Always incomplete
    mock_jules.is_session_complete.return_value = (False, None)
    mock_jules.get_session.return_value = {'url': 'http://session.url'}

    # Execute
    # Timeout 40, interval 30.
    # 1. elapsed=0. check. incomplete. sleep(30). elapsed=30.
    # 2. elapsed=30. check. incomplete. sleep(30). elapsed=60.
    # 3. elapsed=60. loop terminates.
    result = watch_session("session-123", timeout=40)

    # Verify
    assert result == (False, None)
    mock_print_complete.assert_not_called()
    mock_print_timeout.assert_called_once()

@patch_common
def test_watch_session_status_update(mock_sleep, mock_print_timeout, mock_print_complete, mock_jules_class, mock_spinner_class):
    # Setup
    mock_jules = mock_jules_class.return_value
    mock_spinner = mock_spinner_class.return_value
    mock_spinner.__enter__.return_value = mock_spinner

    mock_jules.is_session_complete.side_effect = [(False, None), (True, "url")]
    mock_jules.list_activities.return_value = {
        "activities": [{"progressUpdated": {"title": "Test Activity"}}]
    }

    # Execute
    watch_session("session-123", timeout=100)

    # Verify that spinner was updated with the activity title
    # We check if any call to update contained the title
    found_activity = False
    for call_args in mock_spinner.update.call_args_list:
        if "Test Activity" in call_args[0][0]:
            found_activity = True
            break
    assert found_activity
