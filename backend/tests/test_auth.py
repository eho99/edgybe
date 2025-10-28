import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.main import app
from app.auth import get_current_user, supabase
from app import schemas
import uuid


class TestAuthDependencies:
    """Test authentication dependencies and JWT validation."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock FastAPI request."""
        request = Mock()
        request.headers = {}
        return request

    @pytest.fixture
    def valid_token(self):
        """Return a valid JWT token for testing."""
        return "valid.jwt.token"

    @pytest.fixture
    def mock_supabase_user(self):
        """Create a mock Supabase user response."""
        user = Mock()
        user.id = str(uuid.uuid4())  # Use valid UUID format
        user.email = "test@example.com"
        return user

    @pytest.fixture
    def mock_user_response(self, mock_supabase_user):
        """Create a mock Supabase user response."""
        response = Mock()
        response.user = mock_supabase_user
        return response

    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self, mock_request, valid_token, mock_user_response):
        """Test that valid JWT token returns correct user."""
        mock_request.headers = {"Authorization": f"Bearer {valid_token}"}
        
        with patch.object(supabase.auth, 'get_user', return_value=mock_user_response):
            user = await get_current_user(mock_request)
            
            assert isinstance(user, schemas.SupabaseUser)
            assert str(user.id) == str(mock_user_response.user.id)
            assert user.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_current_user_missing_authorization_header(self, mock_request):
        """Test that missing Authorization header raises 401."""
        mock_request.headers = {}
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request)
        
        assert exc_info.value.status_code == 401
        assert "Missing Authorization header" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_empty_token(self, mock_request):
        """Test that empty token raises 401."""
        mock_request.headers = {"Authorization": "Bearer "}
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request)
        
        assert exc_info.value.status_code == 401
        assert "Invalid token format" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_malformed_header(self, mock_request):
        """Test that malformed Authorization header raises 401."""
        mock_request.headers = {"Authorization": "InvalidFormat token"}
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request)
        
        assert exc_info.value.status_code == 401
        # The actual error message from Supabase may vary, so we just check for 401

    @pytest.mark.asyncio
    async def test_get_current_user_no_bearer_prefix(self, mock_request):
        """Test that missing Bearer prefix raises 401."""
        mock_request.headers = {"Authorization": "valid.jwt.token"}
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request)
        
        assert exc_info.value.status_code == 401
        # The actual error message from Supabase may vary, so we just check for 401

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, mock_request):
        """Test that invalid JWT token raises 401."""
        mock_request.headers = {"Authorization": "Bearer invalid.token"}
        
        with patch.object(supabase.auth, 'get_user', side_effect=Exception("Invalid token")):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_request)
            
            assert exc_info.value.status_code == 401
            assert "Invalid token" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_auth_api_error(self, mock_request):
        """Test that AuthApiError raises 401 with proper message."""
        from supabase_auth.errors import AuthApiError
        
        mock_request.headers = {"Authorization": "Bearer expired.token"}
        
        # AuthApiError requires status and code parameters
        with patch.object(supabase.auth, 'get_user', side_effect=AuthApiError("Token expired", 401, "invalid_token")):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_request)
            
            assert exc_info.value.status_code == 401
            assert "Authentication error: Token expired" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_no_user_returned(self, mock_request):
        """Test that None user from Supabase raises 401."""
        mock_request.headers = {"Authorization": "Bearer valid.token"}
        
        mock_response = Mock()
        mock_response.user = None
        
        with patch.object(supabase.auth, 'get_user', return_value=mock_response):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_request)
            
            assert exc_info.value.status_code == 401
            assert "Invalid token or user not found" in exc_info.value.detail


class TestAuthEndpoints:
    """Test authentication-protected endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_valid_user_response(self):
        """Create mock valid user response."""
        user = Mock()
        user.id = str(uuid.uuid4())  # Use valid UUID format
        user.email = "test@example.com"
        
        response = Mock()
        response.user = user
        return response

    def test_health_endpoint_no_auth_required(self, client):
        """Test that health endpoint doesn't require authentication."""
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_protected_endpoint_without_token(self, client):
        """Test that protected endpoints return 401 without token."""
        # Using organizations endpoint as example
        response = client.get("/api/v1/organizations/my-memberships")
        assert response.status_code == 401

    def test_protected_endpoint_with_invalid_token(self, client):
        """Test that protected endpoints return 401 with invalid token."""
        headers = {"Authorization": "Bearer invalid.token"}
        response = client.get("/api/v1/organizations/my-memberships", headers=headers)
        assert response.status_code == 401

    @patch('app.auth.supabase.auth.get_user')
    def test_protected_endpoint_with_valid_token(self, mock_get_user, client, mock_valid_user_response):
        """Test that protected endpoints work with valid token."""
        mock_get_user.return_value = mock_valid_user_response
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        response = client.get("/api/v1/organizations/my-memberships", headers=headers)
        
        # This will likely return 404 or other error since we're not mocking the full flow,
        # but it should not be 401 (authentication error)
        assert response.status_code != 401

    def test_missing_authorization_header(self, client):
        """Test that missing Authorization header returns 401."""
        response = client.get("/api/v1/organizations/my-memberships")
        assert response.status_code == 401
        assert "Missing Authorization header" in response.json()["detail"]

    def test_malformed_authorization_header(self, client):
        """Test that malformed Authorization header returns 401."""
        headers = {"Authorization": "InvalidFormat token"}
        response = client.get("/api/v1/organizations/my-memberships", headers=headers)
        assert response.status_code == 401
        # The actual error message may vary, so we just check for 401

    def test_empty_bearer_token(self, client):
        """Test that empty Bearer token returns 401."""
        headers = {"Authorization": "Bearer "}
        response = client.get("/api/v1/organizations/my-memberships", headers=headers)
        assert response.status_code == 401
        assert "Invalid token format" in response.json()["detail"]


class TestAuthIntegration:
    """Integration tests for authentication flow."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_auth_flow_with_mock_supabase(self, client):
        """Test complete authentication flow with mocked Supabase."""
        # Mock a successful user response
        mock_user = Mock()
        mock_user.id = str(uuid.uuid4())  # Use valid UUID format
        mock_user.email = "integration@test.com"
        
        mock_response = Mock()
        mock_response.user = mock_user
        
        with patch('app.auth.supabase.auth.get_user', return_value=mock_response):
            headers = {"Authorization": "Bearer integration.test.token"}
            response = client.get("/api/v1/organizations/my-memberships", headers=headers)
            
            # Should not be authentication error (401)
            assert response.status_code != 401

    def test_multiple_auth_requests(self, client):
        """Test that multiple auth requests work correctly."""
        mock_user = Mock()
        mock_user.id = str(uuid.uuid4())  # Use valid UUID format
        mock_user.email = "multi@test.com"
        
        mock_response = Mock()
        mock_response.user = mock_user
        
        with patch('app.auth.supabase.auth.get_user', return_value=mock_response):
            headers = {"Authorization": "Bearer multi.test.token"}
            
            # Make multiple requests
            for _ in range(3):
                response = client.get("/api/v1/organizations/my-memberships", headers=headers)
                assert response.status_code != 401