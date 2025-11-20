import uuid
from typing import Dict

import pytest

from app.models.organization import Organization
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


def test_staff_view_hides_sensitive_fields(client, db_session, mock_user):
    _seed_profile(db_session, mock_user.id)
    organization, membership = _seed_org_with_membership(
        db_session,
        mock_user.id,
        role=OrgRole.staff,
        name="Staff Org",
        slug="staff-org",
    )

    organization.aeries_school_code = "AER123"
    organization.sis_source_id = "SRC456"
    organization.sis_client_id = "CLIENT789"
    organization.sis_client_secret = "SECRET"
    organization.district_id = uuid.uuid4()
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
    assert data["district_id"] is None


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

    secretary_org, _ = _seed_org_with_membership(
        db_session,
        mock_user.id,
        role=OrgRole.secretary,
        name="Secretary Org",
        slug="secretary-org",
    )
    secretary_org.sis_source_id = "HIDDEN"
    secretary_org.district_id = uuid.uuid4()

    db_session.add_all([admin_org, secretary_org])
    db_session.commit()

    response = client.get("/api/v1/organizations/")
    assert response.status_code == 200
    data = response.json()

    admin_entry = next(item for item in data if item["id"] == str(admin_org.id))
    secretary_entry = next(item for item in data if item["id"] == str(secretary_org.id))

    assert admin_entry["sis_source_id"] == "VISIBLE"
    assert secretary_entry["sis_source_id"] is None
    assert secretary_entry["district_id"] is None



