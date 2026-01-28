import pytest
from unittest.mock import MagicMock, patch, call
from src.cli.commands import watch_session

@pytest.fixture
def mock_dependencies():
    # Patch time in src.utils.polling because watch_session delegates to it
    with patch('src.services.jules.JulesClient') as mock_jules_cls, \
         patch('src.cli.commands.Spinner') as mock_spinner_cls, \
         patch('src.utils.polling.time') as mock_polling_time, \
         patch('src.cli.commands.print_watch_complete') as mock_print_complete, \
         patch('src.cli.commands.print_watch_timeout') as mock_print_timeout:

        mock_jules = mock_jules_cls.return_value
        mock_spinner = mock_spinner_cls.return_value
        # Spinner context manager
        mock_spinner_cls.return_value.__enter__.return_value = mock_spinner

        yield {
            'jules_cls': mock_jules_cls,
            'jules': mock_jules,
            'spinner_cls': mock_spinner_cls,
            'spinner': mock_spinner,
            'time': mock_polling_time,
            'print_complete': mock_print_complete,
            'print_timeout': mock_print_timeout
        }

def test_watch_session_success(mock_dependencies):
    deps = mock_dependencies

    # Setup
    session_id = "sess_123"
    pr_url = "http://github.com/pr/1"

    # Mock behavior:
    # 1. Not complete, some activity
    # 2. Complete
    deps['jules'].is_session_complete.side_effect = [
        (False, None),
        (True, pr_url)
    ]

    deps['jules'].list_activities.return_value = {
        "activities": [{
            "progressUpdated": {"title": "Generating code"}
        }]
    }

    # Execute
    result = watch_session(session_id, timeout=60)

    # Verify
    assert result == (True, pr_url)
    assert deps['jules'].is_session_complete.call_count == 2
    deps['spinner'].update.assert_called()
    deps['print_complete'].assert_called()
    deps['print_timeout'].assert_not_called()

def test_watch_session_timeout(mock_dependencies):
    deps = mock_dependencies
    session_id = "sess_timeout"

    # Always not complete
    deps['jules'].is_session_complete.return_value = (False, None)

    # Set timeout to equal poll_interval so it runs once and exits
    # poll_interval is hardcoded to 30 in watch_session

    # Execute
    result = watch_session(session_id, timeout=30)

    # Verify
    assert result == (False, None)
    deps['print_timeout'].assert_called()
    deps['print_complete'].assert_not_called()
