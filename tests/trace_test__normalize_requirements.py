import pytest
from src.core.workflow import _normalize_requirements
from typing import Any

@pytest.fixture
def mock_list_str() -> list[str]:
    return ["pytest", "requests"]

@pytest.fixture
def mock_dict() -> dict[str, str]:
    return {"pytest": ">=7", "requests": "*", "black": "latest", "isort": ""}

@pytest.fixture
def mock_list_dict() -> list[dict[str, str]]:
    return [
        {"package": "pytest", "version": ">=7"},
        {"name": "requests", "constraint": "<3"},
        {"package": "black"} # Missing version
    ]

@pytest.fixture
def mock_mixed_list() -> list[Any]:
    return [
        "pytest",
        {"package": "requests", "version": ">=2"},
        123
    ]

@pytest.mark.parametrize("input_fixture_name, expected", [
    ("mock_list_str", ["pytest", "requests"]),                               # Happy Path
    ("mock_dict", ["pytest>=7", "requests", "black", "isort"]),              # Edge Case: dict format with * and latest
    ("mock_list_dict", ["pytest>=7", "requests<3", "black"]),                # Edge Case: list of dicts format
    ("mock_mixed_list", ["pytest", "requests>=2", "123"]),                   # Edge Case: mixed list format
])
def test_normalize_requirements_behavior(
    request: pytest.FixtureRequest,
    input_fixture_name: str,
    expected: list[str]
) -> None:
    # Get the actual data from the fixture dynamically
    input_val = request.getfixturevalue(input_fixture_name)

    # Execution & Validation
    result = _normalize_requirements(input_val)
    assert result == expected

@pytest.mark.parametrize("scalar_input, expected", [
    ("pytest", ["pytest"]),                                                  # Edge Case: scalar string
    (123, ["123"]),                                                          # Error State / Edge Case: scalar non-string
    (None, ["None"]),                                                        # Error State: None
    ([], []),                                                                # Edge Case: empty list
    ({}, []),                                                                # Edge Case: empty dict
])
def test_normalize_requirements_scalars_and_empty(
    scalar_input: Any,
    expected: list[str]
) -> None:
    # Execution & Validation
    result = _normalize_requirements(scalar_input)
    assert result == expected
