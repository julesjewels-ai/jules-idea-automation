import pytest
import requests
import requests_mock
from src.services.jules import JulesClient
from src.utils.errors import JulesApiError

@pytest.fixture
def client():
    return JulesClient(api_key="test-key")

def test_list_sources_success(client):
    """Test successful API call."""
    with requests_mock.Mocker() as m:
        m.get("https://jules.googleapis.com/v1alpha/sources", json={"sources": []})
        response = client.list_sources()
        assert response == {"sources": []}

def test_api_error_401(client):
    """Test 401 Unauthorized error."""
    with requests_mock.Mocker() as m:
        m.get("https://jules.googleapis.com/v1alpha/sources", status_code=401, json={"error": {"message": "Invalid key"}})
        with pytest.raises(JulesApiError) as excinfo:
            client.list_sources()
        assert "Invalid key" in str(excinfo.value)
        assert "JULES_API_KEY" in excinfo.value.tip

def test_api_error_403(client):
    """Test 403 Forbidden error."""
    with requests_mock.Mocker() as m:
        m.get("https://jules.googleapis.com/v1alpha/sources", status_code=403, json={"error": {"message": "Permission denied"}})
        with pytest.raises(JulesApiError) as excinfo:
            client.list_sources()
        assert "Permission denied" in str(excinfo.value)
        assert "permission" in excinfo.value.tip.lower()

def test_api_error_404(client):
    """Test 404 Not Found error."""
    with requests_mock.Mocker() as m:
        m.get("https://jules.googleapis.com/v1alpha/sources", status_code=404)
        with pytest.raises(JulesApiError) as excinfo:
            client.list_sources()
        assert "404" in str(excinfo.value)
        assert "not found" in excinfo.value.tip.lower()

def test_api_error_500(client):
    """Test 500 Server Error."""
    with requests_mock.Mocker() as m:
        m.get("https://jules.googleapis.com/v1alpha/sources", status_code=500)
        with pytest.raises(JulesApiError) as excinfo:
            client.list_sources()
        assert "500" in str(excinfo.value)
        assert "service error" in excinfo.value.tip.lower()

def test_connection_error(client):
    """Test connection error."""
    with requests_mock.Mocker() as m:
        m.get("https://jules.googleapis.com/v1alpha/sources", exc=requests.exceptions.ConnectionError("Connection refused"))
        with pytest.raises(JulesApiError) as excinfo:
            client.list_sources()
        assert "Connection refused" in str(excinfo.value)
        assert "connection" in excinfo.value.tip.lower()
