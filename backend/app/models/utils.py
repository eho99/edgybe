from datetime import datetime, timedelta, timezone

def get_expiration_time():
    return datetime.now(timezone.utc) + timedelta(days=7)