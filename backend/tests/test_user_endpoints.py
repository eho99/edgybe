import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import uuid

from app.models import Profile

# Use the mock_user fixture from conftest
mock_user_uuid = uuid.UUID("190fa60a-1ff1-4fa0-abc3-ffac2ed211b1")
mock_profile_uuid = uuid.UUID("290fa60a-1ff1-4fa0-abc3-ffac2ed211b1")

@pytest.fixture(autouse=True)
def setup_db(db_session, mock_user):
    """Add mock profile before each test and clear after."""
    # Create profile with the same ID as mock_user
    mock_profile = Profile(
        id=mock_user.id,  # Use mock_user.id from fixture
        full_name="Initial Name", 
        has_completed_profile=False,
        phone="+14155552671",
        city="Springfield",
        state="IL",
        is_active=True
    )
    db_session.add(mock_profile)
    db_session.commit()
    yield
    # Clean up
    db_session.delete(mock_profile)
    db_session.commit()
    db_session.expunge_all()

def test_get_my_profile(client: TestClient):
    response = client.get("/api/v1/users/me/profile")
    
    # For debugging: print response status and json on error
    if response.status_code != 200:
        print("Response data:", response.json())
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(mock_user_uuid)  # Profile ID matches user ID
    assert data["full_name"] == "Initial Name"
    assert data["has_completed_profile"] is False

def test_update_my_profile(client: TestClient, db_session):
    update_data = {"full_name": "Updated Full Name"}
    
    response = client.put("/api/v1/users/me/profile", json=update_data)
    
    if response.status_code != 200:
        print("Response data:", response.json())
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Full Name"
    assert data["has_completed_profile"] is True
    
    # Re-load the profile instance from the db after update and deletion setup
    db_profile = db_session.query(Profile).get(mock_user_uuid)
    assert db_profile is not None
    assert db_profile.full_name == "Updated Full Name"
    assert db_profile.has_completed_profile is True

def test_public_request_password_reset_success(client_without_auth: TestClient, mock_supabase_client):
    """Test that public password reset endpoint works without authentication."""
    # Use client_without_auth since this is a public endpoint
    # mock_supabase_client is automatically applied from conftest
    request_data = {"email": "test@example.com"}
    response = client_without_auth.post("/api/v1/users/request-password-reset", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "password reset link has been sent" in data["message"].lower()
    
    # Verify Supabase was called correctly
    mock_supabase_client.auth.reset_password_for_email.assert_called_once_with(
        "test@example.com",
        {
            "redirect_to": "http://localhost:3000/reset-password"
        }
    )

def test_public_request_password_reset_invalid_email(client_without_auth: TestClient):
    """Test that public password reset endpoint validates email format."""
    request_data = {"email": "invalid-email"}
    response = client_without_auth.post("/api/v1/users/request-password-reset", json=request_data)
    
    assert response.status_code == 422  # Validation error
    data = response.json()
    assert "detail" in data

def test_public_request_password_reset_missing_email(client_without_auth: TestClient):
    """Test that public password reset endpoint requires email."""
    request_data = {}
    response = client_without_auth.post("/api/v1/users/request-password-reset", json=request_data)
    
    assert response.status_code == 422  # Validation error
    data = response.json()
    assert "detail" in data

def test_public_request_password_reset_handles_supabase_error(client_without_auth: TestClient, mock_supabase_client):
    """Test that public password reset endpoint handles Supabase errors gracefully."""
    # Override the mock to raise an exception
    mock_supabase_client.auth.reset_password_for_email.side_effect = Exception("Supabase error")
    
    request_data = {"email": "test@example.com"}
    response = client_without_auth.post("/api/v1/users/request-password-reset", json=request_data)
    
    # Should still return 200 with generic message (security: don't reveal if email exists)
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "password reset link has been sent" in data["message"].lower()
