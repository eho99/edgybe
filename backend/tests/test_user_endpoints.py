import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import uuid

from app.main import app
from app.db import get_db
from app.models import Profile
from app.auth import get_current_user
from app.schemas import SupabaseUser

mock_user_uuid = uuid.UUID("190fa60a-1ff1-4fa0-abc3-ffac2ed211b1")
mock_profile_uuid = uuid.UUID("290fa60a-1ff1-4fa0-abc3-ffac2ed211b1")

mock_user = SupabaseUser(
    id=mock_user_uuid, 
    email="test@example.com"
)
mock_profile = Profile(
    id=mock_profile_uuid, 
    full_name="Initial Name", 
    has_completed_profile=False
)

async def override_get_current_user():
    return mock_user

app.dependency_overrides[get_current_user] = override_get_current_user

@pytest.fixture(autouse=True)
def setup_db(db_session):
    """Add mock profile before each test and clear after."""
    db_session.add(mock_profile)
    db_session.commit()
    yield
    # To avoid InvalidRequestError after deletion, expunge the object from the session.
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
    assert data["id"] == str(mock_profile_uuid)
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
    db_profile = db_session.query(Profile).get(mock_profile_uuid)
    assert db_profile is not None
    assert db_profile.full_name == "Updated Full Name"
    assert db_profile.has_completed_profile is True
