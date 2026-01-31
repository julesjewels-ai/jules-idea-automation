import pytest
from unittest.mock import Mock, call, patch
from src.utils.polling import poll_until, poll_with_result

@patch('src.utils.polling.time.sleep')
def test_poll_until_success(mock_sleep):
    # Setup
    condition = Mock(side_effect=[False, False, True])

    # Execute
    result = poll_until(condition, interval=10, timeout=100)

    # Verify
    assert result is True
    assert condition.call_count == 3
    assert mock_sleep.call_count == 2
    mock_sleep.assert_has_calls([call(10), call(10)])

@patch('src.utils.polling.time.sleep')
def test_poll_until_timeout(mock_sleep):
    # Setup
    condition = Mock(return_value=False)

    # Execute
    result = poll_until(condition, interval=10, timeout=30)

    # Verify
    assert result is False
    # elapsed: 0 -> sleep -> 10 -> sleep -> 20 -> sleep -> 30 (loop ends)
    assert mock_sleep.call_count == 3

@patch('src.utils.polling.time.sleep')
def test_poll_with_result_success(mock_sleep):
    # Setup
    check = Mock(side_effect=[(False, None), (True, "Success")])

    # Execute
    result = poll_with_result(check, interval=10, timeout=100)

    # Verify
    # New behavior returns (bool, result, elapsed)
    assert result == (True, "Success", 10)
    assert check.call_count == 2
    mock_sleep.assert_called_once_with(10)

@patch('src.utils.polling.time.sleep')
def test_poll_with_result_timeout(mock_sleep):
    # Setup
    check = Mock(return_value=(False, None))

    # Execute
    result = poll_with_result(check, interval=10, timeout=30)

    # Verify
    assert result == (False, None, 30)
    assert mock_sleep.call_count == 3
