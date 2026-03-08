import pytest
from pytest_mock import MockerFixture

from src.services.jules import JulesClient
from src.utils.errors import JulesApiError

# Complex objects as constants to avoid inline dictionary bloat
PR_OUTPUT = {
    "outputs": [
        {"pullRequest": {"url": "https://github.com/repo/pull/1"}}
    ]
}

NO_PR_OUTPUT = {
    "outputs": [
        {"otherOutput": {}}
    ]
}

SESSION_COMPLETED_ACTIVITIES = {
    "activities": [
        {"sessionStarted": {}},
        {"sessionCompleted": {}}
    ]
}

SESSION_INCOMPLETE_ACTIVITIES = {
    "activities": [
        {"sessionStarted": {}},
        {"agentThinking": {}}
    ]
}

@pytest.fixture
def mock_client() -> JulesClient:
    return JulesClient(api_key="test_key")

@pytest.mark.parametrize("session_data, activities_data, expected_result, expected_error", [
    # Happy Path 1: Session complete with PR
    (PR_OUTPUT, None, (True, "https://github.com/repo/pull/1"), None),

    # Happy Path 2: Session complete without PR (found in activities)
    (NO_PR_OUTPUT, SESSION_COMPLETED_ACTIVITIES, (True, None), None),

    # Edge Case: Session incomplete (no PR, no sessionCompleted activity)
    (NO_PR_OUTPUT, SESSION_INCOMPLETE_ACTIVITIES, (False, None), None),

    # Error State: get_session raises an error
    (JulesApiError("Network error"), None, None, JulesApiError),
])
def test_is_session_complete_behavior(
    mocker: MockerFixture,
    mock_client: JulesClient,
    session_data: dict | Exception,
    activities_data: dict | None,
    expected_result: tuple[bool, str | None] | None,
    expected_error: type[Exception] | None
) -> None:
    session_id = "test_session_123"

    # 1. Setup Mocks (Namespace Verified)
    # Using mocker.patch.object on the instance to prevent mock drift and isolate the method under test
    mock_get_session = mocker.patch.object(mock_client, 'get_session', autospec=True)
    mock_list_activities = mocker.patch.object(mock_client, 'list_activities', autospec=True)

    if isinstance(session_data, Exception):
        mock_get_session.side_effect = session_data
    else:
        mock_get_session.return_value = session_data

    if activities_data is not None:
        mock_list_activities.return_value = activities_data

    # 2. Execution & Validation
    if expected_error:
        with pytest.raises(expected_error):
            mock_client.is_session_complete(session_id)
        mock_get_session.assert_called_once_with(session_id)
        mock_list_activities.assert_not_called()
    else:
        result = mock_client.is_session_complete(session_id)
        assert result == expected_result

        # Verify Side Effects
        mock_get_session.assert_called_once_with(session_id)

        # list_activities is only called if no PR is found in get_session
        if session_data == PR_OUTPUT:
            mock_list_activities.assert_not_called()
        else:
            mock_list_activities.assert_called_once_with(session_id)
