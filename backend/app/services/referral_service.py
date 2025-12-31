from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Iterable, List, Optional
import uuid

from sqlalchemy import or_, and_
from sqlalchemy.orm import Session, joinedload

from .. import models

DEFAULT_STATS_WINDOW_DAYS = 30


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _normalize_label(value: Optional[str]) -> str:
    return value if value else "Unspecified"


def _build_breakdown(values: Iterable[str]) -> List[Dict[str, Any]]:
    counter = Counter(values)
    return [
        {"label": label, "count": count}
        for label, count in counter.most_common()
    ]


def get_referral_stats(
    db: Session,
    org_id: uuid.UUID,
    *,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    location: Optional[str] = None,
    time_of_day: Optional[str] = None,
    behaviors: Optional[List[str]] = None,
    recent_limit: int = 5,
) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    normalized_end = _ensure_utc(end_date) if end_date else now
    normalized_start = (
        _ensure_utc(start_date)
        if start_date
        else normalized_end - timedelta(days=DEFAULT_STATS_WINDOW_DAYS)
    )

    if normalized_start > normalized_end:
        raise ValueError("start_date cannot be after end_date")

    query = db.query(models.Referral).filter(
        models.Referral.organization_id == org_id,
        models.Referral.archived.is_(False),
        models.Referral.created_at >= normalized_start,
        models.Referral.created_at <= normalized_end,
    )

    if location:
        query = query.filter(models.Referral.location == location)

    if time_of_day:
        query = query.filter(models.Referral.time_of_day == time_of_day)

    if behaviors:
        behavior_filters = [
            models.Referral.behaviors.contains([behavior])
            for behavior in behaviors
            if behavior
        ]
        if behavior_filters:
            query = query.filter(or_(*behavior_filters))

    total_referrals = query.count()

    referrals = (
        query.options(joinedload(models.Referral.student))
        .order_by(models.Referral.created_at.desc())
        .all()
    )

    location_labels = [_normalize_label(referral.location) for referral in referrals]
    time_labels = [
        _normalize_label(referral.time_of_day)
        for referral in referrals
    ]
    behavior_labels: List[str] = []
    for referral in referrals:
        if referral.behaviors:
            behavior_labels.extend([behavior for behavior in referral.behaviors if behavior])

    def build_recent(referral_list: List[models.Referral]) -> List[Dict[str, Any]]:
        recent = []
        for referral in referral_list[:recent_limit]:
            recent.append(
                {
                    "id": referral.id,
                    "student_name": referral.student.full_name if referral.student else None,
                    "student_student_id": referral.student.student_id if referral.student else None,
                    "type": referral.type,
                    "status": referral.status,
                    "location": referral.location,
                    "time_of_day": referral.time_of_day,
                    "behaviors": list(referral.behaviors) if referral.behaviors else None,
                    "created_at": referral.created_at,
                }
            )
        return recent

    return {
        "total_referrals": total_referrals,
        "breakdown_by_location": _build_breakdown(location_labels),
        "breakdown_by_time_of_day": _build_breakdown(time_labels),
        "breakdown_by_behavior": _build_breakdown(behavior_labels),
        "recent_referrals": build_recent(referrals),
        "start_date": normalized_start,
        "end_date": normalized_end,
    }


def assign_admin_to_referral(
    db: Session,
    organization: models.Organization,
    student: models.Profile,
) -> Optional[uuid.UUID]:
    """
    Assign an admin to a referral based on organization's assignment_config rules.
    
    Rules supported:
    - "grade": Assign based on student's grade level
    - "alphabetical": Assign based on student's name (first or last name)
    
    Returns:
        UUID of assigned admin profile, or None if no assignment rule matches
    """
    if not organization.assignment_config:
        return None
    
    config = organization.assignment_config
    if not isinstance(config, dict):
        return None
    
    rule_type = config.get("type")
    if not rule_type:
        return None
    
    # Get all active admin members for this organization
    admin_members = db.query(models.OrganizationMember).join(
        models.Profile,
        models.OrganizationMember.user_id == models.Profile.id
    ).filter(
        and_(
            models.OrganizationMember.organization_id == organization.id,
            models.OrganizationMember.role == models.OrgRole.admin,
            models.OrganizationMember.status == models.MemberStatus.active,
            models.Profile.is_active == True
        )
    ).all()
    
    if not admin_members:
        return None
    
    admin_ids = [member.user_id for member in admin_members if member.user_id]
    if not admin_ids:
        return None
    
    # Assignment by grade
    if rule_type == "grade":
        grade_mappings = config.get("grade_mappings", {})
        if not grade_mappings:
            return None
        
        student_grade = student.grade_level
        if not student_grade:
            return None
        
        # Try to match grade (handle both string and numeric grades)
        # Normalize grade to string for comparison
        grade_str = str(student_grade).strip()
        
        # Check for exact match first
        if grade_str in grade_mappings:
            admin_id_str = grade_mappings[grade_str]
            try:
                admin_id = uuid.UUID(admin_id_str) if isinstance(admin_id_str, str) else admin_id_str
                if admin_id in admin_ids:
                    return admin_id
            except (ValueError, TypeError):
                pass
        
        # If no exact match, try numeric comparison if grade is numeric
        try:
            grade_num = int(grade_str)
            # Check if any key matches as a number
            for key, admin_id_str in grade_mappings.items():
                try:
                    key_num = int(key)
                    if key_num == grade_num:
                        admin_id = uuid.UUID(admin_id_str) if isinstance(admin_id_str, str) else admin_id_str
                        if admin_id in admin_ids:
                            return admin_id
                except (ValueError, TypeError):
                    continue
        except ValueError:
            pass
        
        return None
    
    # Assignment by alphabetical order
    elif rule_type == "alphabetical":
        name_field = config.get("name_field", "last_name")  # default to last_name
        letter_ranges = config.get("letter_ranges", {})
        
        if not letter_ranges:
            return None
        
        # Get the name to use for sorting
        if not student.full_name:
            return None
        
        name_parts = student.full_name.strip().split()
        if not name_parts:
            return None
        
        # Determine which name part to use
        if name_field == "first_name":
            name_to_check = name_parts[0]
        else:  # last_name (default)
            name_to_check = name_parts[-1]
        
        if not name_to_check:
            return None
        
        # Get first letter (case-insensitive)
        first_letter = name_to_check[0].upper()
        
        # Find matching letter range
        for range_key, admin_id_str in letter_ranges.items():
            # Range can be a single letter "A" or a range "A-M"
            if "-" in range_key:
                # Handle range like "A-M"
                start, end = range_key.split("-", 1)
                start = start.strip().upper()
                end = end.strip().upper()
                if start <= first_letter <= end:
                    try:
                        admin_id = uuid.UUID(admin_id_str) if isinstance(admin_id_str, str) else admin_id_str
                        if admin_id in admin_ids:
                            return admin_id
                    except (ValueError, TypeError):
                        continue
            else:
                # Single letter match
                if range_key.strip().upper() == first_letter:
                    try:
                        admin_id = uuid.UUID(admin_id_str) if isinstance(admin_id_str, str) else admin_id_str
                        if admin_id in admin_ids:
                            return admin_id
                    except (ValueError, TypeError):
                        continue
        
        return None
    
    # Unknown rule type
    return None



