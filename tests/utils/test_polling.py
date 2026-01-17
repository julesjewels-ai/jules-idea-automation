
from unittest.mock import Mock, patch
from src.utils.polling import poll_with_result

@patch('src.utils.polling.time.sleep')
def test_poll_with_result_success(mock_sleep):
    # Setup
    mock_check = Mock(side_effect=[(False, None), (True, "result")])

    # Execute
    # New signature: (bool, Optional[T], int)
    success, result, elapsed = poll_with_result(mock_check, timeout=100, interval=10)

    # Verify
    assert success is True
    assert result == "result"
    assert elapsed == 10
    assert mock_check.call_count == 2
    mock_sleep.assert_called_once_with(10)

@patch('src.utils.polling.time.sleep')
def test_poll_with_result_timeout(mock_sleep):
    # Setup
    mock_check = Mock(return_value=(False, None))

    # Execute
    success, result, elapsed = poll_with_result(mock_check, timeout=20, interval=10)

    # Verify
    assert success is False
    assert result is None
    assert elapsed >= 20
    # Should run at elapsed=0, sleep 10, elapsed=10, sleep 10, elapsed=20 -> stop
    assert mock_check.call_count >= 2
