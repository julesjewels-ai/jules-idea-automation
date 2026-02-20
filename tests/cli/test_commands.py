from unittest.mock import patch
from src.cli.commands import handle_list_sources
from src.utils.reporter import print_sources_list


@patch('src.cli.commands.Spinner')
@patch('src.services.jules.JulesClient')
def test_handle_list_sources(MockJulesClient, MockSpinner, capsys):
    # Setup mock
    mock_client = MockJulesClient.return_value
    mock_client.list_sources.return_value = [
        {"id": "source1", "metadata": {"web": {"url": "http://example.com"}}},
        {"id": "source2", "metadata": {}}
    ]

    # Run command
    handle_list_sources()

    # Verify calls
    mock_client.list_sources.assert_called_once()
    MockSpinner.assert_called()

    # Capture output (print_sources_list prints to stdout)
    captured = capsys.readouterr()
    assert "source1" in captured.out
    assert "http://example.com" in captured.out


@patch('src.cli.commands.Spinner')
@patch('src.services.jules.JulesClient')
def test_handle_list_sources_empty(MockJulesClient, MockSpinner, capsys):
    mock_client = MockJulesClient.return_value
    mock_client.list_sources.return_value = []

    handle_list_sources()

    captured = capsys.readouterr()
    assert "No sources found" in captured.out


def test_print_sources_list(capsys):
    sources = [
        {"id": "s1", "metadata": {"web": {"url": "u1", "title": "t1"}}},
        {"id": "s2", "metadata": {"github": {"owner": "o", "repo": "r"}}}
    ]
    print_sources_list(sources)
    captured = capsys.readouterr()
    assert "t1" in captured.out
    assert "o/r" in captured.out


def test_print_sources_list_empty(capsys):
    print_sources_list([])
    captured = capsys.readouterr()
    assert "No sources found" in captured.out
