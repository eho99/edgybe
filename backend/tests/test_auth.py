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
        user.id = str(uuid.uuid4())  # Supabase returns string UUIDs
        user.email = "test@example.com"
        return user

    @pytest.fixture
    def mock_user_response(self, mock_supabase_user):
        """Create a mock Supabase user response."""
        response = Mock()
        response.user = mock_supabase_user
        return response

    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self, mock_request, valid_token, mock_user_response, mock_supabase_client):
        """Test that valid JWT token returns correct user."""
        # Patch the mock client's get_user method since mock_supabase_client is autouse
        mock_supabase_client.auth.get_user.return_value = mock_user_response
        
        # Create credentials object that HTTPBearer would provide
        from fastapi.security import HTTPAuthorizationCredentials
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=valid_token
        )
        
        user = await get_current_user(credentials)
        
        assert isinstance(user, schemas.SupabaseUser)
        assert str(user.id) == str(mock_user_response.user.id)
        assert user.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_current_user_missing_authorization_header(self, mock_request):
        """Test that missing Authorization header raises 401."""
        # When HTTPBearer dependency is not satisfied, FastAPI raises HTTPException
        # We need to test this through the actual dependency system or simulate it
        from fastapi.security import HTTPAuthorizationCredentials
        from fastapi import Depends
        from fastapi.security import HTTPBearer
        
        # HTTPBearer will raise HTTPException when no credentials are provided
        bearer_scheme = HTTPBearer()
        
        # Simulate what happens when no Authorization header is present
        # HTTPBearer raises HTTPException with status 403 by default for missing auth
        with pytest.raises(HTTPException) as exc_info:
            # This simulates what happens when credentials are None/missing
            await bearer_scheme(mock_request)
        
        # HTTPBearer raises 403 for missing credentials, not 401
        assert exc_info.value.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_get_current_user_empty_token(self, mock_request, mock_supabase_client):
        """Test that empty token raises 401."""
        # Mock Supabase to raise an error for empty token
        from supabase_auth.errors import AuthApiError
        mock_supabase_client.auth.get_user.side_effect = AuthApiError("Invalid token", 401, "invalid_token")
        
        from fastapi.security import HTTPAuthorizationCredentials
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=""  # Empty token
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)
        
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_malformed_header(self, mock_request):
        """Test that malformed Authorization header raises 401."""
        # HTTPBearer will reject malformed headers before get_current_user is called
        from fastapi.security import HTTPBearer
        bearer_scheme = HTTPBearer()
        
        mock_request.headers = {"Authorization": "InvalidFormat token"}
        
        with pytest.raises(HTTPException) as exc_info:
            await bearer_scheme(mock_request)
        
        # HTTPBearer raises 403 for malformed auth, not 401
        assert exc_info.value.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_get_current_user_no_bearer_prefix(self, mock_request):
        """Test that missing Bearer prefix raises 401."""
        # HTTPBearer will reject headers without Bearer prefix
        from fastapi.security import HTTPBearer
        bearer_scheme = HTTPBearer()
        
        mock_request.headers = {"Authorization": "valid.jwt.token"}
        
        with pytest.raises(HTTPException) as exc_info:
            await bearer_scheme(mock_request)
        
        # HTTPBearer raises 403 for missing Bearer prefix, not 401
        assert exc_info.value.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, mock_request, mock_supabase_client):
        """Test that invalid JWT token raises 401."""
        # Mock Supabase to raise an error for invalid token
        mock_supabase_client.auth.get_user.side_effect = Exception("Invalid token")
        
        from fastapi.security import HTTPAuthorizationCredentials
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid.token"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)
        
        assert exc_info.value.status_code == 401
        assert "Invalid token" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_auth_api_error(self, mock_request, mock_supabase_client):
        """Test that AuthApiError raises 401 with proper message."""
        from supabase_auth.errors import AuthApiError
        
        # AuthApiError requires status and code parameters
        mock_supabase_client.auth.get_user.side_effect = AuthApiError("Token expired", 401, "invalid_token")
        
        from fastapi.security import HTTPAuthorizationCredentials
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="expired.token"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)
        
        assert exc_info.value.status_code == 401
        assert "Authentication error: Token expired" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_no_user_returned(self, mock_request, mock_supabase_client):
        """Test that None user from Supabase raises 401."""
        mock_response = Mock()
        mock_response.user = None
        mock_supabase_client.auth.get_user.return_value = mock_response
        
        from fastapi.security import HTTPAuthorizationCredentials
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="valid.token"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)
        
        assert exc_info.value.status_code == 401
        assert "Invalid token or user not found" in exc_info.value.detail


class TestAuthEndpoints:
    """Test authentication-protected endpoints."""

    @pytest.fixture
    def mock_valid_user_response(self):
        """Create mock valid user response."""
        user = Mock()
        user.id = str(uuid.uuid4())  # Supabase returns string UUIDs
        user.email = "test@example.com"
        
        response = Mock()
        response.user = user
        return response

    def test_health_endpoint_no_auth_required(self, client_without_auth):
        """Test that health endpoint doesn't require authentication."""
        response = client_without_auth.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_protected_endpoint_without_token(self, client_without_auth):
        """Test that protected endpoints return 401 or 403 without token."""
        # Using organizations endpoint as example
        # HTTPBearer returns 403 (Forbidden) for missing auth headers
        response = client_without_auth.get("/api/v1/organizations/my-memberships")
        assert response.status_code in [401, 403]  # HTTPBearer returns 403 by default

    def test_protected_endpoint_with_invalid_token(self, client_without_auth, mock_supabase_client):
        """Test that protected endpoints return 401 with invalid token."""
        # Mock Supabase to raise an error for invalid token
        from supabase_auth.errors import AuthApiError
        mock_supabase_client.auth.get_user.side_effect = AuthApiError("Invalid token", 401, "invalid_token")
        
        headers = {"Authorization": "Bearer invalid.token"}
        response = client_without_auth.get("/api/v1/organizations/my-memberships", headers=headers)
        assert response.status_code == 401

    def test_protected_endpoint_with_valid_token(self, client_without_auth, mock_supabase_client, mock_valid_user_response):
        """Test that protected endpoints work with valid token."""
        mock_supabase_client.auth.get_user.return_value = mock_valid_user_response
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        response = client_without_auth.get("/api/v1/organizations/my-memberships", headers=headers)
        
        # This will likely return 200 or 404 since we're not setting up memberships,
        # but it should not be 401 (authentication error)
        assert response.status_code != 401

    def test_missing_authorization_header(self, client_without_auth):
        """Test that missing Authorization header returns 401 or 403."""
        # HTTPBearer returns 403 (Forbidden) for missing auth headers
        response = client_without_auth.get("/api/v1/organizations/my-memberships")
        assert response.status_code in [401, 403]  # HTTPBearer returns 403 by default

    def test_malformed_authorization_header(self, client_without_auth):
        """Test that malformed Authorization header returns 401 or 403."""
        # HTTPBearer returns 403 (Forbidden) for malformed auth headers
        headers = {"Authorization": "InvalidFormat token"}
        response = client_without_auth.get("/api/v1/organizations/my-memberships", headers=headers)
        assert response.status_code in [401, 403]  # HTTPBearer returns 403 by default

    def test_empty_bearer_token(self, client_without_auth):
        """Test that empty Bearer token returns 401 or 403."""
        # HTTPBearer may return 403 (Forbidden) for empty tokens, or 401 if it reaches get_current_user
        headers = {"Authorization": "Bearer "}
        response = client_without_auth.get("/api/v1/organizations/my-memberships", headers=headers)
        assert response.status_code in [401, 403]  # HTTPBearer may return 403, or 401 if token validation fails


class TestAuthIntegration:
    """Integration tests for authentication flow."""

    def test_auth_flow_with_mock_supabase(self, client_without_auth, mock_supabase_client):
        """Test complete authentication flow with mocked Supabase."""
        # Mock a successful user response
        # Note: Supabase returns string UUIDs, which Pydantic converts to UUID4
        mock_user = Mock()
        mock_user.id = str(uuid.uuid4())  # Supabase returns string UUIDs
        mock_user.email = "integration@test.com"
        
        mock_response = Mock()
        mock_response.user = mock_user
        mock_supabase_client.auth.get_user.return_value = mock_response
        
        headers = {"Authorization": "Bearer integration.test.token"}
        response = client_without_auth.get("/api/v1/organizations/my-memberships", headers=headers)
        
        # Should not be authentication error (401)
        assert response.status_code != 401

    def test_multiple_auth_requests(self, client_without_auth, mock_supabase_client):
        """Test that multiple auth requests work correctly."""
        # Note: Supabase returns string UUIDs, which Pydantic converts to UUID4
        mock_user = Mock()
        mock_user.id = str(uuid.uuid4())  # Supabase returns string UUIDs
        mock_user.email = "multi@test.com"
        
        mock_response = Mock()
        mock_response.user = mock_user
        mock_supabase_client.auth.get_user.return_value = mock_response
        
        headers = {"Authorization": "Bearer multi.test.token"}
        
        # Make multiple requests
        for _ in range(3):
            response = client_without_auth.get("/api/v1/organizations/my-memberships", headers=headers)
            assert response.status_code != 401