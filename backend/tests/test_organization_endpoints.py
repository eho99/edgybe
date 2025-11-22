import uuid
from typing import Dict

import pytest

from app.models.organization import Organization
from app.models.district import District
from app.models.organization_member import OrganizationMember, OrgRole
from app.models.profile import Profile


def _seed_profile(db_session, user_id):
    profile = Profile(id=user_id, full_name="Test User")
    db_session.add(profile)
    db_session.commit()
    return profile


def _seed_org_with_membership(db_session, user_id, role=OrgRole.admin, **org_kwargs):
    org_data = {"name": "Seed Org"}
    org_data.update(org_kwargs)
    organization = Organization(**org_data)
    db_session.add(organization)
    db_session.commit()
    db_session.refresh(organization)

    membership = OrganizationMember(
        organization_id=organization.id,
        user_id=user_id,
        role=role,
    )
    db_session.add(membership)
    db_session.commit()
    return organization, membership


def _default_payload() -> Dict:
    return {
        "name": "New Org",
        "street_number": "123",
        "street_name": "Main St",
        "city": "Springfield",
        "state": "CA",
        "zip_code": "90210",
        "phone_number": "+14155550123",
        "office_extension": "101",
        "lower_grade": 1,
        "upper_grade": 6,
        "slug": "new-org",
        "preset_config": {"theme": "blue"},
        "form_config": {"steps": []},
        "disclaimers": {"note": "Test"},
    }


def test_admin_can_create_organization(client, db_session, mock_user):
    _seed_profile(db_session, mock_user.id)
    _seed_org_with_membership(db_session, mock_user.id, role=OrgRole.admin)

    payload = _default_payload()
    response = client.post("/api/v1/organizations/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["slug"] == payload["slug"]
    assert "district_name" in data
    assert data["district_name"] is None  # New orgs don't have districts by default


def test_non_admin_cannot_create_organization(client, db_session, mock_user):
    _seed_profile(db_session, mock_user.id)
    _seed_org_with_membership(db_session, mock_user.id, role=OrgRole.staff)

    payload = _default_payload()
    response = client.post("/api/v1/organizations/", json=payload)

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin membership required to manage organizations."


def test_admin_can_update_organization(client, db_session, mock_user):
    _seed_profile(db_session, mock_user.id)
    organization, _ = _seed_org_with_membership(
        db_session,
        mock_user.id,
        role=OrgRole.admin,
        name="Editable Org",
        slug="editable-org",
    )

    patch_payload = {
        "name": "Updated Org",
        "phone_number": "+14155550124",
        "office_extension": "204",
    }

    response = client.patch(
        f"/api/v1/organizations/{organization.id}",
        json=patch_payload,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Org"
    assert data["phone_number"] == "tel:+1-415-555-0124"
    assert data["office_extension"] == "204"
    assert "district_name" in data


def test_create_rejects_district_id(client, db_session, mock_user):
    _seed_profile(db_session, mock_user.id)
    _seed_org_with_membership(db_session, mock_user.id, role=OrgRole.admin)

    payload = _default_payload()
    payload["district_id"] = str(uuid.uuid4())

    response = client.post("/api/v1/organizations/", json=payload)
    assert response.status_code == 422
    assert "district_id" in response.json()["detail"]


def test_update_rejects_district_id(client, db_session, mock_user):
    _seed_profile(db_session, mock_user.id)
    organization, _ = _seed_org_with_membership(
        db_session,
        mock_user.id,
        role=OrgRole.admin,
        name="District Locked",
        slug="district-locked",
    )

    payload = {"district_id": str(uuid.uuid4())}
    response = client.patch(
        f"/api/v1/organizations/{organization.id}",
        json=payload,
    )

    assert response.status_code == 422
    assert "district_id" in response.json()["detail"]


def test_staff_view_hides_sensitive_fields(client, db_session, mock_user):
    _seed_profile(db_session, mock_user.id)
    organization, membership = _seed_org_with_membership(
        db_session,
        mock_user.id,
        role=OrgRole.staff,
        name="Staff Org",
        slug="staff-org",
    )

    district = District(name="Hidden District")
    db_session.add(district)
    db_session.commit()

    organization.aeries_school_code = "AER123"
    organization.sis_source_id = "SRC456"
    organization.sis_client_id = "CLIENT789"
    organization.sis_client_secret = "SECRET"
    organization.district_id = district.id
    db_session.add(organization)
    db_session.commit()

    response = client.get(f"/api/v1/organizations/{organization.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Staff Org"
    assert data["aeries_school_code"] is None
    assert data["sis_source_id"] is None
    assert data["sis_client_id"] is None
    assert data["sis_client_secret"] is None
    assert data["district_name"] == "Hidden District"


def test_list_sanitizes_secretary_results(client, db_session, mock_user):
    _seed_profile(db_session, mock_user.id)
    admin_org, _ = _seed_org_with_membership(
        db_session,
        mock_user.id,
        role=OrgRole.admin,
        name="Admin Org",
        slug="admin-org",
    )
    admin_org.sis_source_id = "VISIBLE"

    district = District(name="Secretary District")
    db_session.add(district)
    db_session.commit()

    secretary_org, _ = _seed_org_with_membership(
        db_session,
        mock_user.id,
        role=OrgRole.secretary,
        name="Secretary Org",
        slug="secretary-org",
    )
    secretary_org.sis_source_id = "HIDDEN"
    secretary_org.district_id = district.id

    db_session.add_all([admin_org, secretary_org])
    db_session.commit()

    response = client.get("/api/v1/organizations/")
    assert response.status_code == 200
    data = response.json()

    admin_entry = next(item for item in data if item["id"] == str(admin_org.id))
    secretary_entry = next(item for item in data if item["id"] == str(secretary_org.id))

    assert admin_entry["sis_source_id"] == "VISIBLE"
    assert secretary_entry["sis_source_id"] is None
    assert secretary_entry["district_name"] == "Secretary District"


def test_list_organizations_includes_district_name(client, db_session, mock_user):
    """Test that list_organizations endpoint returns district_name instead of district_id."""
    _seed_profile(db_session, mock_user.id)
    
    # Create a district
    district = District(name="Test District")
    db_session.add(district)
    db_session.commit()
    
    # Create an organization with a district
    organization, _ = _seed_org_with_membership(
        db_session,
        mock_user.id,
        role=OrgRole.admin,
        name="Org With District",
        slug="org-with-district",
        district_id=district.id,
    )
    
    # Create an organization without a district
    org_no_district, _ = _seed_org_with_membership(
        db_session,
        mock_user.id,
        role=OrgRole.admin,
        name="Org Without District",
        slug="org-without-district",
    )
    
    response = client.get("/api/v1/organizations/")
    assert response.status_code == 200
    data = response.json()
    
    # Find both organizations in the response
    org_with_district = next(item for item in data if item["id"] == str(organization.id))
    org_without_district = next(item for item in data if item["id"] == str(org_no_district.id))
    
    # Verify district_name is present and correct
    assert "district_name" in org_with_district
    assert org_with_district["district_name"] == "Test District"
    assert "district_id" not in org_with_district
    
    # Verify organization without district has None for district_name
    assert "district_name" in org_without_district
    assert org_without_district["district_name"] is None
    assert "district_id" not in org_without_district



