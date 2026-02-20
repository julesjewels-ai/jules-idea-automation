from unittest.mock import patch
from src.cli.commands import handle_list_sources
from src.utils.reporter import print_sources_list
# removed unused import


@patch('src.cli.commands.Spinner')
def test_handle_list_sources(MockSpinner, capsys):
    # Setup mock
    with patch('src.services.jules.JulesClient') as MockJulesClient:
        mock_client = MockJulesClient.return_value
        mock_client.list_sources.return_value = {
            "sources": [
                {"id": "source1", "name": "Source 1", "metadata": {"web": {"url": "http://example.com"}}},
                {"id": "source2", "metadata": {}}
            ]
        }

        # Run command
        handle_list_sources()

        # Verify calls
        mock_client.list_sources.assert_called_once()
        MockSpinner.assert_called()

        # Capture output (print_sources_list prints to stdout)
        captured = capsys.readouterr()
        # The output contains ansi codes, check for substrings
        assert "Source 1" in captured.out
        # The reporter now only prints name, so "http://example.com" might not be printed if it's only in metadata
        # We checked src/utils/reporter.py: print_sources_list only prints `name`.
        # So we should not assert for "http://example.com"
        assert "Unknown" in captured.out


@patch('src.cli.commands.Spinner')
def test_handle_list_sources_empty(MockSpinner, capsys):
    with patch('src.services.jules.JulesClient') as MockJulesClient:
        mock_client = MockJulesClient.return_value
        mock_client.list_sources.return_value = {"sources": []}

        handle_list_sources()

        captured = capsys.readouterr()
        assert "No sources found" in captured.out


def test_print_sources_list(capsys):
    response = {
        "sources": [
            {"id": "s1", "name": "Test Source", "metadata": {"web": {"url": "u1", "title": "t1"}}},
            {"id": "s2", "metadata": {"github": {"owner": "o", "repo": "r"}}}
        ]
    }
    print_sources_list(response)
    captured = capsys.readouterr()
    assert "Test Source" in captured.out
    assert "Unknown" in captured.out


def test_print_sources_list_empty(capsys):
    print_sources_list({})
    captured = capsys.readouterr()
    assert "No sources found" in captured.out
