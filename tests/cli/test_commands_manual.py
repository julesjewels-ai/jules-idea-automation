from argparse import Namespace
from unittest.mock import patch, ANY
import pytest
from src.cli.commands import handle_manual
from src.core.models import IdeaResponse

@patch('src.cli.commands._execute_and_watch')
@patch('src.utils.slugify.slugify')
def test_handle_manual_basic(mock_slugify, mock_execute):
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
    expected_data = IdeaResponse(
        title="My Title",
        description="My Description",
        slug="my-title",
        tech_stack=[],
        features=[]
    )
    mock_execute.assert_called_once_with(args, expected_data)

@patch('src.cli.commands._execute_and_watch')
@patch('src.utils.slugify.slugify')
def test_handle_manual_long_title(mock_slugify, mock_execute):
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

    mock_slugify.assert_called_once()

    # We can verify via the called args
    call_args = mock_execute.call_args
    idea_data = call_args[0][1]

    assert isinstance(idea_data, IdeaResponse)
    assert idea_data.description == long_title
    assert idea_data.slug == "this-is-a-very-long"
    assert idea_data.title == "This is a very long title that is actually a descr"

@patch('src.cli.commands._execute_and_watch')
def test_handle_manual_with_lists(mock_execute):
    """Test parsing of tech stack and features."""
    args = Namespace(
        title="App",
        description="Desc",
        slug="app",
        tech_stack="python, react,  typescript ",
        features="login,  dashboard"
    )

    handle_manual(args)

    expected_data = IdeaResponse(
        title="App",
        description="Desc",
        slug="app",
        tech_stack=["python", "react", "typescript"],
        features=["login", "dashboard"]
    )
    mock_execute.assert_called_once_with(args, expected_data)
