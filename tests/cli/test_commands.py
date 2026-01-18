
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

# We need to patch time.sleep in the module where it is USED.
# After refactor, it is used in src.utils.polling
@patch('src.utils.polling.time.sleep')
@patch('src.cli.commands.Spinner')
@patch('src.services.jules.JulesClient')
def test_watch_session_success(mock_jules_class, mock_spinner_class, mock_sleep):
    # Setup
    mock_client = mock_jules_class.return_value
    # First call: not complete
    # Second call: complete, with PR URL
    mock_client.is_session_complete.side_effect = [
        (False, None),
        (True, "http://github.com/pr/1")
    ]

    mock_client.list_activities.return_value = {
        "activities": [
            {"progressUpdated": {"title": "Coding..."}}
        ]
    }

    # Execute
    is_complete, pr_url = watch_session("sess-123", timeout=100)

    # Verify
    assert is_complete is True
    assert pr_url == "http://github.com/pr/1"
    assert mock_client.is_session_complete.call_count == 2

    # Verify spinner updates
    mock_spinner_instance = mock_spinner_class.return_value.__enter__.return_value
    mock_spinner_instance.update.assert_called()


@patch('src.utils.polling.time.sleep')
@patch('src.cli.commands.Spinner')
@patch('src.services.jules.JulesClient')
def test_watch_session_timeout(mock_jules_class, mock_spinner_class, mock_sleep):
    # Setup
    mock_client = mock_jules_class.return_value
    mock_client.is_session_complete.return_value = (False, None)
    mock_client.get_session.return_value = {"url": "http://jules.ai/sess-123"}

    # Execute with short timeout
    # poll_with_result loop condition is `elapsed < timeout`
    # It increments elapsed by interval (30)

    is_complete, pr_url = watch_session("sess-123", timeout=50)

    # Verify
    assert is_complete is False
    assert pr_url is None
    # Should run twice (0, 30)
    # 0 < 50 -> check -> sleep -> elapsed=30
    # 30 < 50 -> check -> sleep -> elapsed=60
    # 60 < 50 -> False
    assert mock_client.is_session_complete.call_count == 2
