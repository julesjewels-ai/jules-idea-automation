import pytest
from pytest_mock import MockerFixture
from typing import Any, List, Tuple, Union, Optional
from src.utils.polling import poll_with_result

# Function: poll_with_result
# Mental Model:
# Input: check (callable), timeout (int), interval (int), on_poll (callable), status_extractor (callable)
# External Side Effects: time.sleep (mocked), callbacks invoked
# Output: Tuple(bool, Optional[T], int)

@pytest.fixture
def mock_context() -> dict[str, Any]:
    """Provides context for the polling operation."""
    return {"timeout": 30, "interval": 10}

@pytest.mark.parametrize("check_side_effect, expected_outcome", [
    # Happy Path: Immediate Success
    ([(True, "success")],
     {"success": True, "result": "success", "elapsed": 0}),

    # Happy Path: Success after retry
    ([(False, None), (True, "retry_success")],
     {"success": True, "result": "retry_success", "elapsed": 10}),

    # Edge Case: Timeout (never succeeds)
    # timeout=30, interval=10. Iterations at 0, 10, 20. Stops at 30.
    ([(False, None)] * 10,
     {"success": False, "result": None, "elapsed": 30}),

    # Error State: Exception propagation
    (ValueError("Critical Failure"), ValueError),
])
def test_poll_with_result_behavior(
    mocker: MockerFixture,
    mock_context: dict[str, Any],
    check_side_effect: Union[List[Tuple[bool, Any]], Exception],
    expected_outcome: Union[dict[str, Any], type[Exception]]
) -> None:
    # 1. Setup Mocks (Namespace Verified: src.utils.polling.time)
    # We mock time.sleep to avoid actual delays but keep the loop logic intact.
    mock_sleep = mocker.patch("src.utils.polling.time.sleep", autospec=True)

    mock_check = mocker.Mock()
    mock_check.side_effect = check_side_effect

    mock_on_poll = mocker.Mock()
    mock_status_extractor = mocker.Mock(return_value="Processing...")

    timeout = mock_context["timeout"]
    interval = mock_context["interval"]

    # 2. Execution & Validation
    if isinstance(expected_outcome, type) and issubclass(expected_outcome, Exception):
        with pytest.raises(expected_outcome):
            poll_with_result(
                check=mock_check,
                timeout=timeout,
                interval=interval
            )
    else:
        success, result, elapsed = poll_with_result(
            check=mock_check,
            timeout=timeout,
            interval=interval,
            on_poll=mock_on_poll,
            status_extractor=mock_status_extractor
        )

        # Verify Return Values
        assert success == expected_outcome["success"]
        assert result == expected_outcome["result"]
        assert elapsed == expected_outcome["elapsed"]

        # Verify Side Effects
        if success:
            # If successful, check calls usually match the number of iterations needed
            # Immediate: 1 call. Retry (1 fail, 1 success): 2 calls.
            expected_calls = len(check_side_effect)
            assert mock_check.call_count == expected_calls
        else:
            # If timeout, it should have run until elapsed >= timeout
            # 0, 10, 20 -> 3 calls. At 30 it stops.
            expected_calls = timeout // interval
            assert mock_check.call_count == expected_calls
            assert elapsed >= timeout

        # Verify on_poll calls
        if elapsed > 0:
            assert mock_on_poll.called
            assert mock_status_extractor.called
            # Ensure sleep was called correctly
            mock_sleep.assert_called_with(interval)
