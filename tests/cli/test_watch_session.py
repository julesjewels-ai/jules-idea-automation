
from unittest.mock import patch
from src.cli.commands import watch_session

@patch('src.cli.commands.print_watch_timeout')
@patch('src.cli.commands.print_watch_complete')
@patch('src.utils.polling.time.sleep')
@patch('src.cli.commands.Spinner')
@patch('src.services.jules.JulesClient')
def test_watch_session_success(mock_jules_cls, mock_spinner_cls, mock_sleep, mock_print_complete, mock_print_timeout):
    # Setup
    mock_jules = mock_jules_cls.return_value
    # First call not complete, second call complete
    mock_jules.is_session_complete.side_effect = [(False, None), (True, "http://pr.url")]

    # Mock activities
    mock_jules.list_activities.return_value = {
        "activities": [{"progressUpdated": {"title": "Doing things"}}]
    }

    mock_spinner = mock_spinner_cls.return_value
    mock_spinner.__enter__.return_value = mock_spinner

    # Execute
    result = watch_session("sess-123", timeout=100)

    # Verify
    assert result == (True, "http://pr.url")
    assert mock_jules.is_session_complete.call_count == 2
    mock_sleep.assert_called_once() # Should sleep once between calls
    mock_print_complete.assert_called_once()
    mock_print_timeout.assert_not_called()
    mock_spinner.update.assert_called()

@patch('src.cli.commands.print_watch_timeout')
@patch('src.cli.commands.print_watch_complete')
@patch('src.utils.polling.time.sleep')
@patch('src.cli.commands.Spinner')
@patch('src.services.jules.JulesClient')
def test_watch_session_timeout(mock_jules_cls, mock_spinner_cls, mock_sleep, mock_print_complete, mock_print_timeout):
    # Setup
    mock_jules = mock_jules_cls.return_value
    mock_jules.is_session_complete.return_value = (False, None)
    mock_jules.get_session.return_value = {'url': 'http://session.url'}

    mock_spinner = mock_spinner_cls.return_value
    mock_spinner.__enter__.return_value = mock_spinner

    # Execute
    # Set timeout to something small, but we rely on loop condition.
    # Since we mock time.sleep, we need to ensure the loop terminates.
    # The loop condition is `elapsed < timeout`.
    # `elapsed` is incremented by `poll_interval` (30) each iteration.
    # So if timeout=60, it runs twice (0, 30), then stops at 60.
    result = watch_session("sess-123", timeout=60)

    # Verify
    assert result == (False, None)
    assert mock_jules.is_session_complete.call_count == 2 # 0 and 30
    assert mock_sleep.call_count == 2
    mock_print_complete.assert_not_called()
    mock_print_timeout.assert_called_once()
