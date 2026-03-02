
from typing import Any
from unittest.mock import patch, MagicMock
import pytest
from pytest import CaptureFixture
from src.cli.commands import handle_list_sources

# Ensure module is loaded for patching

@patch('src.cli.commands.Spinner')
@patch('src.services.jules.JulesClient')
@patch('src.cli.commands.print_sources_list')
def test_handle_list_sources(mock_print_sources: MagicMock, mock_jules_client_class: MagicMock, mock_spinner: MagicMock) -> None:
    # Setup
    mock_client_instance = mock_jules_client_class.return_value
    mock_sources: dict[str, Any] = {"sources": [{"name": "source1", "displayName": "Source 1"}]}
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
def test_handle_list_sources_empty(mock_print_sources: MagicMock, mock_jules_client_class: MagicMock, mock_spinner: MagicMock) -> None:
    # Setup
    mock_client_instance = mock_jules_client_class.return_value
    mock_sources: dict[str, Any] = {}
    mock_client_instance.list_sources.return_value = mock_sources

    # Execute
    handle_list_sources()

    # Verify
    mock_print_sources.assert_called_once_with(mock_sources)

from src.utils.reporter import print_sources_list

def test_print_sources_list(capsys: CaptureFixture[str]) -> None:
    sources: dict[str, Any] = {"sources": [{"name": "source1", "displayName": "Source 1"}]}
    print_sources_list(sources)
    captured = capsys.readouterr()
    assert "Found 1 source(s)" in captured.out
    assert "source1" in captured.out

def test_print_sources_list_empty(capsys: CaptureFixture[str]) -> None:
    sources: dict[str, Any] = {}
    print_sources_list(sources)
    captured = capsys.readouterr()
    assert "No sources found" in captured.out
    assert "Connect a GitHub repository" in captured.out
