"""Integration tests for Resilience module and GeminiClient."""

import pytest
from unittest.mock import MagicMock
from src.utils.resilience import RetryStrategy, MaxRetriesExceededError
from src.services.gemini import GeminiClient


def test_retry_strategy_success():
    """Test that RetryStrategy returns result on success."""
    strategy = RetryStrategy(max_retries=3, base_delay=0.01)
    mock_op = MagicMock(return_value="success")

    result = strategy.execute(mock_op, "arg")

    assert result == "success"
    mock_op.assert_called_once_with("arg")


def test_retry_strategy_retries_on_failure():
    """Test that RetryStrategy retries on failure."""
    strategy = RetryStrategy(
        max_retries=2,
        base_delay=0.01,
        retryable_exceptions=(
            ValueError,
        ))
    mock_op = MagicMock(
        side_effect=[
            ValueError("fail1"),
            ValueError("fail2"),
            "success"])

    result = strategy.execute(mock_op)

    assert result == "success"
    assert mock_op.call_count == 3


def test_retry_strategy_max_retries_exceeded():
    """Test that RetryStrategy raises MaxRetriesExceededError."""
    strategy = RetryStrategy(
        max_retries=2,
        base_delay=0.01,
        retryable_exceptions=(
            ValueError,
        ))
    mock_op = MagicMock(side_effect=ValueError("fail"))

    with pytest.raises(MaxRetriesExceededError) as excinfo:
        strategy.execute(mock_op)

    assert "Max retries (2) exceeded" in str(excinfo.value)
    assert isinstance(excinfo.value.__cause__, ValueError)


def test_retry_strategy_ignores_other_exceptions():
    """Test that RetryStrategy does not retry non-retryable exceptions."""
    strategy = RetryStrategy(
        max_retries=2,
        base_delay=0.01,
        retryable_exceptions=(
            ValueError,
        ))
    mock_op = MagicMock(side_effect=TypeError("fail"))

    with pytest.raises(TypeError):
        strategy.execute(mock_op)

    assert mock_op.call_count == 1


def test_gemini_client_uses_resilience(mocker):
    """Test that GeminiClient uses the injected resilience policy."""
    mock_policy = MagicMock()
    # Mock return value should be a dict compatible with ProjectScaffold.model_dump() if used,
    # but here execute returns the result of _generate_content which is a dict.
    mock_policy.execute.return_value = {
        "files": [],
        "requirements": [],
        "run_command": "echo 'hello'"
    }

    # Mock genai.Client to avoid real API calls in __init__
    mocker.patch("src.services.gemini.genai.Client")

    # We need to set api_key to bypass env check
    client = GeminiClient(api_key="fake_key", resilience_policy=mock_policy)

    idea_data = {
        "title": "Test App",
        "description": "Desc",
        "slug": "test-app",
        "tech_stack": [],
        "features": []
    }

    client.generate_project_scaffold(idea_data)

    mock_policy.execute.assert_called_once()
    # Check that the first argument to execute was _generate_content
    assert mock_policy.execute.call_args[0][0] == client._generate_content


def test_gemini_client_fallback_on_failure(mocker):
    """Test that GeminiClient falls back to scaffold if resilience fails."""
    # Mock RetryStrategy to raise MaxRetriesExceededError immediately
    mock_policy = MagicMock()
    mock_policy.execute.side_effect = MaxRetriesExceededError("Failed")

    mocker.patch("src.services.gemini.genai.Client")

    client = GeminiClient(api_key="fake_key", resilience_policy=mock_policy)

    idea_data = {
        "title": "Test App",
        "description": "Desc",
        "slug": "test-app",
        "tech_stack": [],
        "features": []
    }

    result = client.generate_project_scaffold(idea_data)

    # Should return fallback scaffold dict
    # Checking for keys present in fallback scaffold
    assert "main.py" in str(result)
    assert result.get('run_command') == "python main.py"
