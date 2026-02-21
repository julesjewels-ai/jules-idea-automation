"""Tests for manual command."""

from unittest.mock import patch, ANY
from src.cli.commands import handle_manual


@patch('src.cli.commands._execute_and_watch')
def test_handle_manual_basic(mock_execute):
    """Test manual mode with basic title."""
    args = type('Args', (), {
        'title': "My Idea",
        'description': None,
        'slug': None,
        'tech_stack': None,
        'features': None
    })

    handle_manual(args)

    mock_execute.assert_called_once()
    idea_data = mock_execute.call_args[0][1]
    assert idea_data['title'] == "My Idea"
    assert idea_data['description'] == "My Idea"  # Default description
    assert idea_data['slug'] == "my-idea"


@patch('src.cli.commands._execute_and_watch')
def test_handle_manual_full(mock_execute):
    """Test manual mode with all options."""
    args = type('Args', (), {
        'title': "My Idea",
        'description': "Desc",
        'slug': "custom-slug",
        'tech_stack': "Python, Go",
        'features': "Auth, API"
    })

    handle_manual(args)

    idea_data = mock_execute.call_args[0][1]
    assert idea_data['tech_stack'] == ["Python", "Go"]
    assert idea_data['features'] == ["Auth", "API"]


@patch('src.cli.commands._execute_and_watch')
def test_handle_manual_long_title_split(mock_execute):
    """Test handling of description-as-title input."""
    # > 100 chars
    long_title = (
        "This is a very long title that is actually a description of the project. "
        "It goes on and on to exceed the limit. "
        "It definitely needs to be more than 100 characters to trigger the logic."
    )

    args = type('Args', (), {
        'title': long_title,
        'description': None,
        'slug': None,
        'tech_stack': None,
        'features': None
    })

    handle_manual(args)

    idea_data = mock_execute.call_args[0][1]
    # Check that title was truncated/extracted
    assert len(idea_data['title']) < len(long_title)
    # Full text goes to description
    assert idea_data['description'] == long_title


@patch('src.cli.commands._execute_and_watch')
def test_handle_manual_explicit_slug(mock_execute):
    """Test manual mode with explicit slug."""
    args = type('Args', (), {
        'title': "Some Title",
        'description': None,
        'slug': "my-custom-slug",
        'tech_stack': None,
        'features': None
    })

    handle_manual(args)

    mock_execute.assert_called_with(
        args,
        {
            "title": ANY,
            "description": ANY,
            "slug": "my-custom-slug",
            "tech_stack": [],
            "features": []
        }
    )


@patch('src.cli.commands._execute_and_watch')
def test_handle_manual_empty_lists(mock_execute):
    """Test manual mode with empty list arguments."""
    args = type('Args', (), {
        'title': "Title",
        'description': None,
        'slug': None,
        'tech_stack': "",
        'features': ""
    })

    handle_manual(args)

    idea_data = mock_execute.call_args[0][1]
    assert idea_data['tech_stack'] == []
    assert idea_data['features'] == []
