
from unittest.mock import patch
from src.cli.commands import handle_list_sources, watch_session
from src.utils.reporter import print_sources_list

# Ensure module is loaded for patching

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
@patch('src.utils.polling.time.sleep')
def test_watch_session_success(mock_sleep, mock_print_complete, mock_jules_client_class, mock_spinner):
    # Setup
    mock_client_instance = mock_jules_client_class.return_value
    # First call: incomplete, Second call: complete
    mock_client_instance.is_session_complete.side_effect = [(False, None), (True, "http://pr.url")]
    mock_client_instance.list_activities.return_value = {"activities": [{"progressUpdated": {"title": "Activity 1"}}]}

    # Execute
    result = watch_session("session-123", timeout=100)

    # Verify
    assert result == (True, "http://pr.url")
    assert mock_client_instance.is_session_complete.call_count == 2
    mock_print_complete.assert_called_once()

@patch('src.cli.commands.Spinner')
@patch('src.services.jules.JulesClient')
@patch('src.cli.commands.print_watch_timeout')
@patch('src.utils.polling.time.sleep')
def test_watch_session_timeout(mock_sleep, mock_print_timeout, mock_jules_client_class, mock_spinner):
    # Setup
    mock_client_instance = mock_jules_client_class.return_value
    mock_client_instance.is_session_complete.return_value = (False, None)
    mock_client_instance.get_session.return_value = {'url': 'http://session.url'}

    # Execute
    # Set timeout to allow 2 iterations (0, 30). Next is 60 which is >= 60.
    result = watch_session("session-123", timeout=60)

    # Verify
    assert result == (False, None)
    assert mock_client_instance.is_session_complete.call_count >= 1
    mock_print_timeout.assert_called_once()
