import pytest
from unittest.mock import MagicMock
from pytest_mock import MockerFixture
from src.services.scraper import _extract_text

@pytest.fixture
def mock_soup_instance(mocker: MockerFixture) -> MagicMock:
    # Mock the BeautifulSoup class and return the instance it produces
    mock_class = mocker.patch("src.services.scraper.BeautifulSoup")
    mock_instance = mock_class.return_value
    return mock_instance

@pytest.mark.parametrize("content, elements_to_decompose, text_content, expected", [
    (b"<html>valid</html>", 2, " Clean content ", "Clean content"),  # Happy Path
    (b"", 0, "", ""),                                              # Edge Case (Empty)
    (b"<html>error</html>", 0, Exception, Exception),              # Error State
])
def test_extract_text_behavior(
    mocker: MockerFixture,
    mock_soup_instance: MagicMock,
    content: bytes,
    elements_to_decompose: int,
    text_content: str | type[Exception],
    expected: str | type[Exception]
) -> None:
    # 1. Setup Mocks
    # Setup elements to decompose
    mock_elements = [MagicMock() for _ in range(elements_to_decompose)]
    # Mock soup([...]) call behavior
    mock_soup_instance.side_effect = None # Reset side effect if any
    mock_soup_instance.return_value = mock_elements

    # Setup text extraction or error
    if isinstance(text_content, type) and issubclass(text_content, Exception):
        mock_soup_instance.get_text.side_effect = text_content("Parsing Error")
    else:
        mock_soup_instance.get_text.return_value = text_content

    # Handle constructor exception case
    if isinstance(expected, type) and issubclass(expected, Exception) and text_content is expected:
         # Check if we expect the constructor to fail (Error State scenario)
         mocker.patch("src.services.scraper.BeautifulSoup", side_effect=expected("Init Error"))
         # Note: This overrides the fixture's patch for this specific test iteration

    # 2. Execution & Validation
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            _extract_text(content)
    else:
        result = _extract_text(content)
        assert result == expected

        # Verify interactions
        # Verify BeautifulSoup instantiation
        # Note: We can't easily assert called_once on the class mock here because the fixture
        # created it, and if we re-patched it (in Error State), we lost the reference.
        # But for non-error cases, we can verify the instance usage.

        # Verify soup([...]) called
        mock_soup_instance.assert_called_once()

        # Verify decompose called on all elements
        for el in mock_elements:
            el.decompose.assert_called_once()

        # Verify get_text called
        mock_soup_instance.get_text.assert_called_once()
