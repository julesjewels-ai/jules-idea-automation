import pytest
from unittest.mock import MagicMock, patch, call
from src.cli.commands import watch_session

@patch('src.cli.commands.Spinner')
@patch('src.cli.commands.print_watch_complete')
@patch('src.cli.commands.print_watch_timeout')
@patch('src.services.jules.JulesClient')
def test_watch_session_complete_immediately(mock_jules_cls, mock_print_timeout, mock_print_complete, mock_spinner):
    # Setup
    mock_client = mock_jules_cls.return_value
    mock_client.is_session_complete.return_value = (True, "http://pr.url")

    # Execute
    result = watch_session("sess-123", timeout=10)

    # Verify
    assert result == (True, "http://pr.url")
    mock_print_complete.assert_called_once()
    mock_print_timeout.assert_not_called()

@patch('src.cli.commands.Spinner')
@patch('src.cli.commands.print_watch_complete')
@patch('src.cli.commands.print_watch_timeout')
@patch('src.utils.polling.time.sleep') # Mock sleep to speed up test
@patch('src.services.jules.JulesClient')
def test_watch_session_polling(mock_jules_cls, mock_sleep, mock_print_timeout, mock_print_complete, mock_spinner):
    # Setup
    mock_client = mock_jules_cls.return_value
    # First call False, second call True
    mock_client.is_session_complete.side_effect = [(False, None), (True, "http://pr.url")]

    mock_client.list_activities.return_value = {
        "activities": [{"progressUpdated": {"title": "Compiling..."}}]
    }

    # Execute
    result = watch_session("sess-123", timeout=100)

    # Verify
    assert result == (True, "http://pr.url")
    assert mock_client.is_session_complete.call_count == 2
    mock_print_complete.assert_called_once()

    # Check spinner updates
    spinner_instance = mock_spinner.return_value.__enter__.return_value
    # It should have updated with the activity title
    spinner_instance.update.assert_called()
    # Check that update was called with something containing "Compiling..."
    # We look at the last call or any call
    calls = spinner_instance.update.call_args_list
    found_msg = False
    for c in calls:
        if "Compiling..." in c[0][0]:
            found_msg = True
            break
    assert found_msg

@patch('src.cli.commands.Spinner')
@patch('src.cli.commands.print_watch_complete')
@patch('src.cli.commands.print_watch_timeout')
@patch('src.utils.polling.time.sleep')
@patch('src.services.jules.JulesClient')
def test_watch_session_timeout(mock_jules_cls, mock_sleep, mock_print_timeout, mock_print_complete, mock_spinner):
    # Setup
    mock_client = mock_jules_cls.return_value
    mock_client.is_session_complete.return_value = (False, None)
    mock_client.get_session.return_value = {"url": "http://session.url"}

    # Execute
    # Set timeout to something small, but since we mock sleep, we need to ensure loop terminates
    # The loop condition is elapsed < timeout. elapsed increments by 30.
    # So if timeout=40, it runs once (0), increments to 30. Next check 30 < 40 (True), runs again, increments to 60. 60 < 40 (False).
    result = watch_session("sess-123", timeout=40)

    # Verify
    assert result == (False, None)
    mock_print_complete.assert_not_called()
    mock_print_timeout.assert_called_once()
