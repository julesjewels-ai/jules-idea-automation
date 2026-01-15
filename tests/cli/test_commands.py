
import pytest
from unittest.mock import MagicMock, patch
from src.cli.commands import handle_list_sources, watch_session
from src.utils.reporter import Colors

# Ensure module is loaded for patching
import src.services.jules

@patch('src.cli.commands.Spinner')
@patch('src.services.jules.JulesClient')
@patch('src.cli.commands.print_sources_list')
def test_handle_list_sources(mock_print_sources, mock_jules_client_class, mock_spinner):
    # Setup
    mock_client_instance = mock_jules_client_class.return_value
    mock_sources = {"sources": [{"name": "source1", "displayName": "Source 1"}]}
    mock_client_instance.list_sources.return_value = mock_sources

    # Execute
    handle_list_sources()

    # Verify
    mock_jules_client_class.assert_called_once()
    mock_client_instance.list_sources.assert_called_once()
    mock_print_sources.assert_called_once_with(mock_sources)
    mock_spinner.assert_called_once_with("Fetching sources...", success_message="Sources fetched")

@patch('src.cli.commands.Spinner')
@patch('src.services.jules.JulesClient')
@patch('src.cli.commands.print_sources_list')
def test_handle_list_sources_empty(mock_print_sources, mock_jules_client_class, mock_spinner):
    # Setup
    mock_client_instance = mock_jules_client_class.return_value
    mock_sources = {}
    mock_client_instance.list_sources.return_value = mock_sources

    # Execute
    handle_list_sources()

    # Verify
    mock_print_sources.assert_called_once_with(mock_sources)

from src.utils.reporter import print_sources_list

def test_print_sources_list(capsys):
    sources = {"sources": [{"name": "source1", "displayName": "Source 1"}]}
    print_sources_list(sources)
    captured = capsys.readouterr()
    assert "Found 1 source(s)" in captured.out
    assert "source1" in captured.out

def test_print_sources_list_empty(capsys):
    sources = {}
    print_sources_list(sources)
    captured = capsys.readouterr()
    assert "No sources found" in captured.out
    assert "Connect a GitHub repository" in captured.out

@patch('src.cli.commands.Spinner')
@patch('src.services.jules.JulesClient')
@patch('src.cli.commands.print_watch_complete')
@patch('src.utils.polling.time.sleep')
def test_watch_session_success(mock_sleep, mock_print_complete, mock_jules_client_class, mock_spinner):
    # Setup
    mock_client_instance = mock_jules_client_class.return_value

    # We use a large side_effect list to avoid StopIteration if called more times than expected.
    # The last items are True to ensure it eventually returns.
    mock_client_instance.is_session_complete.side_effect = [
        (False, None),
        (False, None),
        (True, "http://pr.url"),
        (True, "http://pr.url"), # Padding
        (True, "http://pr.url")  # Padding
    ]

    # Mock activities
    mock_client_instance.list_activities.return_value = {
        "activities": [{"progressUpdated": {"title": "Doing things"}}]
    }

    # Execute
    is_complete, pr_url = watch_session("sess-123", timeout=100)

    # Verify
    assert is_complete is True
    assert pr_url == "http://pr.url"
    assert mock_client_instance.is_session_complete.call_count >= 3
    mock_print_complete.assert_called_once()

@patch('src.cli.commands.Spinner')
@patch('src.services.jules.JulesClient')
@patch('src.cli.commands.print_watch_timeout')
@patch('src.utils.polling.time.sleep')
def test_watch_session_timeout(mock_sleep, mock_print_timeout, mock_jules_client_class, mock_spinner):
    # Setup
    mock_client_instance = mock_jules_client_class.return_value

    # Always returns not complete
    mock_client_instance.is_session_complete.return_value = (False, None)
    mock_client_instance.get_session.return_value = {'url': 'http://session.url'}

    # Mock activities
    mock_client_instance.list_activities.return_value = {}

    # Execute with short timeout.
    is_complete, pr_url = watch_session("sess-123", timeout=31)

    # Verify
    assert is_complete is False
    assert pr_url is None
    mock_print_timeout.assert_called_once()
