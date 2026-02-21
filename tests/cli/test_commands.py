"""Tests for CLI commands."""

from src.utils.reporter import print_sources_list
from unittest.mock import patch, ANY
from src.cli.commands import handle_list_sources, handle_agent


@patch('src.cli.commands.Spinner')
@patch('src.services.jules.JulesClient')
def test_handle_list_sources(mock_jules_cls, mock_spinner):
    """Test handle_list_sources command."""
    mock_client = mock_jules_cls.return_value
    mock_client.list_sources.return_value = {"sources": [{"name": "test"}]}

    with patch('src.cli.commands.print_sources_list') as mock_print:
        handle_list_sources()
        mock_print.assert_called_once()


@patch('src.cli.commands.Spinner')
@patch('src.services.gemini.GeminiClient')
@patch('src.cli.commands._execute_and_watch')
def test_handle_agent(mock_execute, mock_gemini_cls, mock_spinner):
    """Test handle_agent command."""
    mock_gemini = mock_gemini_cls.return_value
    mock_gemini.generate_idea.return_value = {"title": "Test Idea"}

    args = type('Args', (), {'category': None})
    handle_agent(args)

    mock_gemini.generate_idea.assert_called_once()
    mock_execute.assert_called_once()


@patch('src.cli.commands.Spinner')
@patch('src.services.gemini.GeminiClient')
@patch('src.cli.commands._execute_and_watch')
def test_handle_agent_with_category(mock_execute, mock_gemini_cls, mock_spinner):
    """Test handle_agent command with category."""
    mock_gemini = mock_gemini_cls.return_value
    mock_gemini.generate_idea.return_value = {"title": "Test Idea"}

    args = type('Args', (), {'category': 'web_app'})
    handle_agent(args)

    mock_gemini.generate_idea.assert_called_once_with(category='web_app')
    mock_execute.assert_called_once()


def test_print_sources_list(capsys):
    """Test output formatting for sources."""
    sources = {"sources": [{"name": "repo/1"}]}
    print_sources_list(sources)
    captured = capsys.readouterr()
    assert "repo/1" in captured.out


def test_print_sources_list_empty(capsys):
    """Test output formatting for empty sources."""
    print_sources_list({})
    captured = capsys.readouterr()
    assert "No sources found" in captured.out
