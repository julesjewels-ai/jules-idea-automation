
import pytest
from unittest.mock import MagicMock, patch
from argparse import Namespace
from src.cli.commands import handle_agent, watch_session

@patch('src.services.gemini.GeminiClient')
@patch('src.core.workflow.IdeaWorkflow')
@patch('src.cli.commands.watch_session')
@patch('src.cli.commands.Spinner')
@patch('src.cli.commands.print_idea_summary')
def test_handle_agent_with_watch(mock_print_summary, mock_spinner, mock_watch, mock_workflow_class, mock_gemini_class):
    # Setup
    args = Namespace(category="web_app", private=False, timeout=10, watch=True)

    mock_gemini = mock_gemini_class.return_value
    mock_gemini.generate_idea.return_value = {"title": "Test Idea", "description": "Desc"}

    mock_workflow = mock_workflow_class.return_value
    result = MagicMock()
    result.session_id = "session-123"
    mock_workflow.execute.return_value = result

    # Execute
    handle_agent(args)

    # Verify
    mock_gemini.generate_idea.assert_called_with(category="web_app")
    mock_workflow.execute.assert_called_with(
        {"title": "Test Idea", "description": "Desc"},
        private=False,
        timeout=10
    )
    mock_watch.assert_called_once_with("session-123", timeout=10)


@patch('src.services.jules.JulesClient')
@patch('src.cli.commands.Spinner')
@patch('src.cli.commands.print_watch_complete')
@patch('src.utils.polling.poll_with_result')
def test_watch_session_success(mock_poll, mock_print_complete, mock_spinner, mock_jules_class):
    # Setup
    mock_poll.return_value = (True, "http://pr.url")

    # Execute
    result = watch_session("session-123", timeout=10)

    # Verify
    assert result == (True, "http://pr.url")
    mock_poll.assert_called_once()
    mock_print_complete.assert_called_once()
