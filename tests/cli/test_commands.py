
import pytest
from unittest.mock import MagicMock, patch
from src.cli.commands import handle_list_sources, watch_session
from src.utils.reporter import Colors, print_sources_list

# Ensure module is loaded for patching
import src.services.jules
import src.utils.polling

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
@patch('src.cli.commands.print_watch_timeout')
@patch('src.utils.polling.time.sleep')
@patch('src.cli.commands.time.time')
def test_watch_session_success(mock_time, mock_sleep, mock_print_timeout, mock_print_complete, mock_jules_client_class, mock_spinner_class):
    # Setup
    mock_client_instance = mock_jules_client_class.return_value
    mock_spinner_instance = mock_spinner_class.return_value
    mock_spinner_class.return_value.__enter__.return_value = mock_spinner_instance

    # Mock time.time() to advance
    # Start: 0. Poll 1: 30. Complete: 30.
    mock_time.side_effect = [0, 30]

    # Mock sequence: Not complete, then complete
    mock_client_instance.is_session_complete.side_effect = [
        (False, None),
        (True, "http://pr.url")
    ]

    mock_client_instance.list_activities.return_value = {
        "activities": [{"progressUpdated": {"title": "Doing something"}}]
    }

    mock_client_instance.get_session.return_value = {"url": "http://session.url"}

    # Execute
    result = watch_session("session-123", timeout=100)

    # Verify
    assert result == (True, "http://pr.url")
    mock_print_complete.assert_called_once_with(30, "http://pr.url")
    mock_spinner_instance.update.assert_called()


@patch('src.cli.commands.Spinner')
@patch('src.services.jules.JulesClient')
@patch('src.cli.commands.print_watch_complete')
@patch('src.cli.commands.print_watch_timeout')
@patch('src.utils.polling.time.sleep')
@patch('src.cli.commands.time.time')
def test_watch_session_timeout(mock_time, mock_sleep, mock_print_timeout, mock_print_complete, mock_jules_client_class, mock_spinner_class):
    # Setup
    mock_client_instance = mock_jules_client_class.return_value
    mock_spinner_instance = mock_spinner_class.return_value
    mock_spinner_class.return_value.__enter__.return_value = mock_spinner_instance

    mock_time.return_value = 0

    # Always incomplete
    mock_client_instance.is_session_complete.return_value = (False, None)
    mock_client_instance.list_activities.return_value = {}
    mock_client_instance.get_session.return_value = {"url": "http://session.url"}

    # Execute
    result = watch_session("session-123", timeout=40)

    # Verify
    assert result == (False, None)
    mock_print_timeout.assert_called_once_with(40, "http://session.url")
    mock_print_complete.assert_not_called()
