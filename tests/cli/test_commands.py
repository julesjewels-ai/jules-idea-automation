from unittest.mock import patch
from src.cli.commands import handle_list_sources, watch_session
from src.utils.reporter import print_sources_list

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

@patch('src.utils.polling.time.sleep')
@patch('src.services.jules.JulesClient')
@patch('src.cli.commands.Spinner')
@patch('src.cli.commands.print_watch_complete')
def test_watch_session_success(mock_print_complete, mock_spinner, mock_jules_cls, mock_sleep):
    """Test watch_session successfully completes."""
    # Setup
    mock_jules = mock_jules_cls.return_value

    mock_jules.is_session_complete.side_effect = [(False, None), (True, "http://pr")] + [(False, None)] * 10
    mock_jules.list_activities.return_value = {"activities": []}

    # Execute
    result = watch_session("sess-123", timeout=100)

    # Verify
    assert result == (True, "http://pr")
    mock_print_complete.assert_called_once()

@patch('src.utils.polling.time.sleep')
@patch('src.services.jules.JulesClient')
@patch('src.cli.commands.Spinner')
@patch('src.cli.commands.print_watch_timeout')
def test_watch_session_timeout(mock_print_timeout, mock_spinner, mock_jules_cls, mock_sleep):
    """Test watch_session times out."""
    # Setup
    mock_jules = mock_jules_cls.return_value
    mock_jules.is_session_complete.return_value = (False, None)
    mock_jules.list_activities.return_value = {"activities": []}
    mock_jules.get_session.return_value = {'url': 'http://session'}

    # Execute
    result = watch_session("sess-123", timeout=40)

    # Verify
    assert result == (False, None)
    assert mock_sleep.call_count >= 2
    mock_print_timeout.assert_called_once()
