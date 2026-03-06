from typing import Any

import pytest
from pytest_mock import MockerFixture

from src.services.jules import JulesClient
from src.utils.errors import JulesApiError


@pytest.fixture
def jules_client() -> JulesClient:
    return JulesClient(api_key="test_key")


@pytest.fixture
def mock_session_with_pr() -> dict[str, Any]:
    return {"outputs": [{"pullRequest": {"url": "https://github.com/pr/1"}}]}


@pytest.fixture
def mock_session_complete_no_pr() -> dict[str, Any]:
    return {"outputs": [{"other": {}}]}


@pytest.fixture
def mock_session_incomplete() -> dict[str, Any]:
    return {"outputs": []}


@pytest.fixture
def mock_activities_complete() -> dict[str, Any]:
    return {"activities": [{"sessionStarted": {}}, {"sessionCompleted": {}}]}


@pytest.fixture
def mock_activities_incomplete() -> dict[str, Any]:
    return {"activities": [{"sessionStarted": {}}]}


@pytest.mark.parametrize(
    "session_fixture, activities_fixture, expected, expected_error",
    [
        ("mock_session_with_pr", None, (True, "https://github.com/pr/1"), None),  # Happy Path
        ("mock_session_complete_no_pr", "mock_activities_complete", (True, None), None),  # Happy Path 2
        ("mock_session_incomplete", "mock_activities_incomplete", (False, None), None),  # Edge Case
        ("mock_session_incomplete", None, None, JulesApiError),  # Error State
    ],
)
def test_is_session_complete_behavior(
    request: pytest.FixtureRequest,
    mocker: MockerFixture,
    jules_client: JulesClient,
    session_fixture: str,
    activities_fixture: str | None,
    expected: tuple[bool, str | None] | None,
    expected_error: type[Exception] | None,
) -> None:
    # 1. Setup Mocks
    mock_get_session = mocker.patch.object(jules_client, "get_session")
    mock_list_activities = mocker.patch.object(jules_client, "list_activities")

    session_val = request.getfixturevalue(session_fixture)
    mock_get_session.return_value = session_val

    if activities_fixture:
        activities_val = request.getfixturevalue(activities_fixture)
        mock_list_activities.return_value = activities_val

    session_id = "test_session_123"

    # 2. Execution & Validation
    if expected_error:
        mock_get_session.side_effect = expected_error("API Error")
        with pytest.raises(expected_error):
            jules_client.is_session_complete(session_id)
        mock_get_session.assert_called_once_with(session_id)
        mock_list_activities.assert_not_called()
    else:
        result = jules_client.is_session_complete(session_id)
        assert result == expected
        mock_get_session.assert_called_once_with(session_id)

        # Verify Side Effects
        if expected and expected[0] and expected[1] is not None:
            # PR found in get_session, list_activities skipped
            mock_list_activities.assert_not_called()
        else:
            mock_list_activities.assert_called_once_with(session_id)
