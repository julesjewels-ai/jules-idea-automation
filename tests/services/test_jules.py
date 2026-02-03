"""Tests for JulesClient."""

import pytest
from src.services.jules import JulesClient
from src.utils.errors import JulesApiError

def test_jules_client_api_error_401(requests_mock):
    client = JulesClient(api_key="test-key")
    requests_mock.get("https://jules.googleapis.com/v1alpha/sources", status_code=401, text="Unauthorized")

    with pytest.raises(JulesApiError) as excinfo:
        client.list_sources()

    assert "Your Jules API key seems invalid" in excinfo.value.tip

def test_jules_client_api_error_403(requests_mock):
    client = JulesClient(api_key="test-key")
    requests_mock.get("https://jules.googleapis.com/v1alpha/sources", status_code=403, text="Forbidden")

    with pytest.raises(JulesApiError) as excinfo:
        client.list_sources()

    assert "You don't have permission" in excinfo.value.tip

def test_jules_client_api_error_404(requests_mock):
    client = JulesClient(api_key="test-key")
    requests_mock.get("https://jules.googleapis.com/v1alpha/sources", status_code=404, text="Not Found")

    with pytest.raises(JulesApiError) as excinfo:
        client.list_sources()

    assert "The requested resource was not found" in excinfo.value.tip

def test_jules_client_generic_error(requests_mock):
    client = JulesClient(api_key="test-key")
    requests_mock.get("https://jules.googleapis.com/v1alpha/sources", status_code=500, text="Internal Server Error")

    with pytest.raises(JulesApiError) as excinfo:
        client.list_sources()

    assert "API returned status 500" in excinfo.value.tip
