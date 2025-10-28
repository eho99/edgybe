import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
from app.db import get_db
from app.models import Profile
from app.auth import get_current_user
from app.schemas import SupabaseUser

# Mock data
mock_user = SupabaseUser(
    id="uuid-test-user-profile", 
    email="profile.user@example.com"
)
mock_profile = Profile(
    id="uuid-test-user-profile", 
    full_name="Initial Name", 
    has_completed_profile=False
)

# Override get_current_user dependency
async def override_get_current_user():
    return mock_user

app.dependency_overrides[get_current_user] = override_get_current_user

@pytest.fixture(autouse=True)
def setup_db(db_session):
    """Add mock profile before each test and clear after."""
    db_session.add(mock_profile)
    db_session.commit()
    yield
    db_session.delete(mock_profile)
    db_session.commit()

def test_get_my_profile(client: TestClient):
    response = client.get("/api/v1/users/me/profile")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "uuid-test-user-profile"
    assert data["full_name"] == "Initial Name"
    assert data["has_completed_profile"] is False

def test_update_my_profile(client: TestClient, db_session):
    update_data = {"full_name": "Updated Full Name"}
    
    response = client.put("/api/v1/users/me/profile", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Full Name"
    assert data["has_completed_profile"] is True
    
    # Verify in DB
    db_profile = db_session.query(Profile).get("uuid-test-user-profile")
    assert db_profile.full_name == "Updated Full Name"
    assert db_profile.has_completed_profile is True
