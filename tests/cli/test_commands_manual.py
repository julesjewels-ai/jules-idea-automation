from argparse import Namespace
from typing import Any
from unittest.mock import patch, ANY
from src.cli.commands import handle_manual

@patch('src.cli.commands._execute_and_watch')
@patch('src.utils.slugify.slugify')
def test_handle_manual_basic(mock_slugify: Any, mock_execute: Any) -> None:
    """Test basic manual command with explicit title and description."""
    mock_slugify.return_value = "my-title"
    args = Namespace(
        title="My Title",
        description="My Description",
        slug=None,
        tech_stack=None,
        features=None
    )

    handle_manual(args)

    mock_slugify.assert_called_once_with("My Title")
    expected_data = {
        "title": "My Title",
        "description": "My Description",
        "slug": "my-title",
        "tech_stack": [],
        "features": []
    }
    mock_execute.assert_called_once_with(args, expected_data)

@patch('src.cli.commands._execute_and_watch')
@patch('src.utils.slugify.slugify')
def test_handle_manual_long_title(mock_slugify: Any, mock_execute: Any) -> None:
    """Test handling of long titles (description-as-title pattern)."""
    long_title = "This is a very long title that is actually a description of the project. It goes on and on to exceed the limit. It definitely needs to be more than 100 characters to trigger the logic."
    mock_slugify.return_value = "this-is-a-very-long"
    args = Namespace(
        title=long_title,
        description=None,
        slug=None,
        tech_stack=None,
        features=None
    )

    handle_manual(args)

    # Should extract first sentence/prefix
    # Wait, the logic is: raw_title[:50].split('.')[0].strip()
    # "This is a very long title that is actually a descri" -> split('.') -> same string

    # Let's verify the logic in commands.py:
    # title = raw_title[:50].split('.')[0].strip() or "Manual Idea"

    # "This is a very long title that is actually a descri" (50 chars)
    # It doesn't contain a dot. So it takes the whole 50 chars.

    mock_slugify.assert_called_once()

    expected_data = {
        "title": ANY, # We'll verify exact logic via the called args
        "description": long_title,
        "slug": "this-is-a-very-long",
        "tech_stack": [],
        "features": []
    }
    mock_execute.assert_called_once_with(args, expected_data)

    # Verify title specifically
    call_args = mock_execute.call_args
    idea_data = call_args[0][1]
    assert idea_data["title"] == "This is a very long title that is actually a descr"

@patch('src.cli.commands._execute_and_watch')
def test_handle_manual_with_lists(mock_execute: Any) -> None:
    """Test parsing of tech stack and features."""
    args = Namespace(
        title="App",
        description="Desc",
        slug="app",
        tech_stack="python, react,  typescript ",
        features="login,  dashboard"
    )

    handle_manual(args)

    expected_data = {
        "title": "App",
        "description": "Desc",
        "slug": "app",
        "tech_stack": ["python", "react", "typescript"],
        "features": ["login", "dashboard"]
    }
    mock_execute.assert_called_once_with(args, expected_data)
