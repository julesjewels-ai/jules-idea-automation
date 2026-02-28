from unittest.mock import patch
from src.cli.commands import watch_session

@patch('src.services.jules.JulesClient')
@patch('src.cli.commands.Spinner')
@patch('src.utils.polling.time.sleep') # Speed up tests
@patch('src.cli.commands.print_watch_complete')
@patch('src.cli.commands.print_watch_timeout')
def test_watch_session_success(mock_timeout_print, mock_complete_print, mock_sleep, mock_spinner_cls, mock_jules_cls):
    # Setup
    mock_jules = mock_jules_cls.return_value
    # is_session_complete returns (is_complete, pr_url)
    # First call False, Second call True
    mock_jules.is_session_complete.side_effect = [(False, None), (True, "http://pr.url")]

    # Mock list_activities
    mock_jules.list_activities.return_value = {
        "activities": [{"progressUpdated": {"title": "Doing something"}}]
    }

    # Execute
    result, pr_url = watch_session("sess-123", timeout=100)

    # Verify
    assert result is True
    assert pr_url == "http://pr.url"
    mock_complete_print.assert_called_once()
    mock_timeout_print.assert_not_called()
    assert mock_jules.is_session_complete.call_count == 2

@patch('src.services.jules.JulesClient')
@patch('src.cli.commands.Spinner')
@patch('src.utils.polling.time.sleep')
@patch('src.cli.commands.print_watch_complete')
@patch('src.cli.commands.print_watch_timeout')
def test_watch_session_timeout(mock_timeout_print, mock_complete_print, mock_sleep, mock_spinner_cls, mock_jules_cls):
    # Setup
    mock_jules = mock_jules_cls.return_value
    mock_jules.is_session_complete.return_value = (False, None)
    mock_jules.get_session.return_value = {"url": "http://session.url"}

    # Execute
    # poll_interval is 30. timeout 50.
    # 0 < 50 -> check -> sleep 30 -> elapsed 30
    # 30 < 50 -> check -> sleep 30 -> elapsed 60
    # 60 < 50 -> Break
    result, pr_url = watch_session("sess-123", timeout=50)

    # Verify
    assert result is False
    assert pr_url is None
    mock_complete_print.assert_not_called()
    mock_timeout_print.assert_called_once()
    assert mock_jules.is_session_complete.call_count >= 2
