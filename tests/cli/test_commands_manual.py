from unittest.mock import patch
from argparse import Namespace
from src.cli.commands import handle_manual


@patch('src.cli.commands._execute_and_watch')
def test_handle_manual_basic(mock_execute):
    args = Namespace(
        title="My App",
        description=None,
        slug=None,
        tech_stack=None,
        features=None
    )

    handle_manual(args)

    mock_execute.assert_called_once()
    call_args = mock_execute.call_args
    idea_data = call_args[0][1]

    assert idea_data["title"] == "My App"
    assert idea_data["description"] == "My App"
    assert idea_data["slug"] == "my-app"


@patch('src.cli.commands._execute_and_watch')
def test_handle_manual_long_title(mock_execute):
    # Description-as-title pattern
    long_title = (
        "This is a very long title that is actually a description of the project. "
        "It goes on and on to exceed the limit. "
        "It definitely needs to be more than 100 characters to trigger the logic."
    )
    args = Namespace(
        title=long_title,
        description=None,
        slug=None,
        tech_stack=None,
        features=None
    )

    handle_manual(args)

    idea_data = mock_execute.call_args[0][1]
    # Check that description is the full text
    assert idea_data["description"] == long_title
    # Check that title is shortened (first sentence or prefix)
    assert len(idea_data["title"]) < len(long_title)


@patch('src.cli.commands._execute_and_watch')
def test_handle_manual_full_options(mock_execute):
    args = Namespace(
        title="App",
        description="Desc",
        slug="custom-slug",
        tech_stack="python, react",
        features="login, dashboard"
    )

    handle_manual(args)

    mock_execute.assert_called_with(
        args,
        {
            "title": "App",
            "description": "Desc",
            "slug": "custom-slug",
            "tech_stack": ["python", "react"],
            "features": ["login", "dashboard"]
        }
    )


@patch('src.cli.commands._execute_and_watch')
def test_handle_manual_slug_generation(mock_execute):
    args = Namespace(
        title="My Cool App!",
        description=None,
        slug=None,
        tech_stack=None,
        features=None
    )

    handle_manual(args)
    idea_data = mock_execute.call_args[0][1]
    assert idea_data["slug"] == "my-cool-app"
