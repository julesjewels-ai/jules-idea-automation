
import pytest
from unittest.mock import patch
from src.cli.commands import watch_session

@pytest.fixture
def mock_jules_client():
    # Patch where the class is defined because it is imported locally
    with patch('src.services.jules.JulesClient') as MockClient:
        yield MockClient.return_value

@pytest.fixture
def mock_spinner():
    with patch('src.cli.commands.Spinner') as MockSpinner:
        yield MockSpinner

@pytest.fixture
def mock_print_complete():
    with patch('src.cli.commands.print_watch_complete') as mock:
        yield mock

@pytest.fixture
def mock_print_timeout():
    with patch('src.cli.commands.print_watch_timeout') as mock:
        yield mock

@patch('src.utils.polling.time.sleep')
def test_watch_session_immediate_success(mock_sleep, mock_jules_client, mock_spinner, mock_print_complete):
    # Setup
    mock_jules_client.is_session_complete.return_value = (True, "http://pr.url")

    # Execute
    result = watch_session("session_123", timeout=60)

    # Verify
    assert result == (True, "http://pr.url")
    mock_jules_client.is_session_complete.assert_called_with("session_123")
    mock_print_complete.assert_called_once()
    # Spinner should have been initialized
    mock_spinner.assert_called_once()

@patch('src.utils.polling.time.sleep')
def test_watch_session_polling_success(mock_sleep, mock_jules_client, mock_spinner, mock_print_complete):
    # Setup - first call False, second call True
    mock_jules_client.is_session_complete.side_effect = [
        (False, None),
        (True, "http://pr.url")
    ]

    # Mock activity response
    mock_jules_client.list_activities.return_value = {
        "activities": [{"progressUpdated": {"title": "Generating Code"}}]
    }

    # Execute
    result = watch_session("session_123", timeout=60)

    # Verify
    assert result == (True, "http://pr.url")
    assert mock_jules_client.is_session_complete.call_count == 2
    mock_jules_client.list_activities.assert_called()
    mock_print_complete.assert_called_once()

@patch('src.utils.polling.time.sleep')
def test_watch_session_timeout(mock_sleep, mock_jules_client, mock_spinner, mock_print_timeout):
    # Setup - always return False
    mock_jules_client.is_session_complete.return_value = (False, None)
    mock_jules_client.get_session.return_value = {'url': 'http://session.url'}

    # We need to simulate time passing or loop iterations.
    # Since watch_session uses `elapsed += poll_interval`, checking elapsed < timeout.
    # If we set timeout to 60 and interval is 30, it should loop twice.
    # However, mocking time.sleep just skips the delay.
    # We can control the loop by side_effect on is_session_complete if we want to limit iterations,
    # but the loop condition is `elapsed < timeout`.
    # `elapsed` is incremented by `poll_interval` (30) inside the loop.
    # So if timeout=60, elapsed=0 -> sleep -> elapsed=30 -> loop -> elapsed=30 -> sleep -> elapsed=60 -> loop terminates.

    # Execute
    result = watch_session("session_123", timeout=40)

    # Verify
    assert result == (False, None)
    mock_print_timeout.assert_called_once()
