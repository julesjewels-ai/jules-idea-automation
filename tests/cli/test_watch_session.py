
from unittest.mock import patch
from src.cli.commands import watch_session

@patch('src.services.jules.JulesClient')
@patch('src.cli.commands.Spinner')
@patch('src.utils.polling.time.sleep')
@patch('src.cli.commands.time.sleep')
@patch('src.cli.commands.print_watch_complete')
@patch('src.cli.commands.print_watch_timeout')
def test_watch_session_complete(mock_print_timeout, mock_print_complete, mock_sleep_cmd, mock_sleep_poll, mock_spinner_cls, mock_jules_cls):
    # Setup
    mock_jules = mock_jules_cls.return_value
    mock_jules.is_session_complete.side_effect = [(False, None), (True, "http://pr.url")]
    mock_jules.list_activities.return_value = {"activities": []}

    # Execute
    result = watch_session("sess_123", timeout=100)

    # Verify
    assert result == (True, "http://pr.url")
    assert mock_jules.is_session_complete.call_count == 2
    mock_print_complete.assert_called_once()
    mock_print_timeout.assert_not_called()

@patch('src.services.jules.JulesClient')
@patch('src.cli.commands.Spinner')
@patch('src.utils.polling.time.sleep')
@patch('src.cli.commands.time.sleep')
@patch('src.cli.commands.print_watch_complete')
@patch('src.cli.commands.print_watch_timeout')
def test_watch_session_timeout(mock_print_timeout, mock_print_complete, mock_sleep_cmd, mock_sleep_poll, mock_spinner_cls, mock_jules_cls):
    # Setup
    mock_jules = mock_jules_cls.return_value
    mock_jules.is_session_complete.return_value = (False, None)
    mock_jules.get_session.return_value = {'url': 'http://session.url'}
    mock_jules.list_activities.return_value = {"activities": []}

    # Execute
    # Timeout 60, poll interval 30.
    # Iteration 1: elapsed=0. check. sleep. elapsed=30.
    # Iteration 2: elapsed=30. check. sleep. elapsed=60.
    # Iteration 3: elapsed=60. 60 < 60 False. Stop.
    result = watch_session("sess_123", timeout=60)

    # Verify
    assert result == (False, None)
    assert mock_jules.is_session_complete.call_count == 2
    mock_print_timeout.assert_called_once()
    mock_print_complete.assert_not_called()
