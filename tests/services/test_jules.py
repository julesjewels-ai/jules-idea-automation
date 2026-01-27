import pytest
from src.services.jules import JulesClient
from src.utils.errors import JulesApiError, ConfigurationError

@pytest.fixture
def jules_client(monkeypatch):
    monkeypatch.setenv("JULES_API_KEY", "test-key")
    return JulesClient(api_key="test-key")

def test_jules_client_init_error(monkeypatch):
    """Test that client raises ConfigurationError if no API key is provided."""
    monkeypatch.delenv("JULES_API_KEY", raising=False)

    with pytest.raises(ConfigurationError):
        JulesClient()

def test_list_sources_success(jules_client, requests_mock):
    """Test successful sources listing."""
    requests_mock.get(
        "https://jules.googleapis.com/v1alpha/sources",
        json={"sources": [{"name": "source-1"}]}
    )

    sources = jules_client.list_sources()
    assert sources["sources"][0]["name"] == "source-1"

def test_request_helper_401(jules_client, requests_mock):
    """Test 401 Unauthorized error handling."""
    requests_mock.get(
        "https://jules.googleapis.com/v1alpha/sources",
        status_code=401,
        json={"error": {"message": "Unauthorized"}}
    )

    with pytest.raises(JulesApiError) as excinfo:
        jules_client.list_sources()

    assert "Unauthorized" in str(excinfo.value)
    assert "Check your JULES_API_KEY" in excinfo.value.tip

def test_request_helper_404(jules_client, requests_mock):
    """Test 404 Not Found error handling."""
    requests_mock.get(
        "https://jules.googleapis.com/v1alpha/sessions/123",
        status_code=404,
        json={"error": {"message": "Session not found"}}
    )

    with pytest.raises(JulesApiError) as excinfo:
        jules_client.get_session("123")

    assert "Session not found" in str(excinfo.value)
    assert "requested resource (session or source) was not found" in excinfo.value.tip

def test_request_helper_500(jules_client, requests_mock):
    """Test 500 Internal Server Error handling."""
    requests_mock.get(
        "https://jules.googleapis.com/v1alpha/sources",
        status_code=500,
        text="Internal Server Error"
    )

    with pytest.raises(JulesApiError) as excinfo:
        jules_client.list_sources()

    # The message might vary depending on how requests handles text response without json
    # In my implementation: error_msg = str(e) which is usually "500 Server Error: ..."
    # So I shouldn't assert exact "Internal Server Error" string in exception message unless I'm sure
    assert "500" in str(excinfo.value)
    assert "Jules API is experiencing internal issues" in excinfo.value.tip

def test_list_sessions_params(jules_client, requests_mock):
    """Test that list_sessions passes query parameters correctly."""
    requests_mock.get(
        "https://jules.googleapis.com/v1alpha/sessions?pageSize=5",
        json={"sessions": []}
    )

    jules_client.list_sessions(page_size=5)
    assert requests_mock.called
    assert "pageSize=5" in requests_mock.last_request.url
