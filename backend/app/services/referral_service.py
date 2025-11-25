from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Iterable, List, Optional
import uuid

from sqlalchemy import or_
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

