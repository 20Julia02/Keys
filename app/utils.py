import datetime
from passlib.context import CryptContext
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from .models import TokenBlacklist, Activities

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def start_activity(db: Session, user_id: int, concierge_id: int) -> int:
    start_time = datetime.datetime.now(datetime.timezone.utc)
    new_activity = Activities(user_id=user_id, concierge_id = concierge_id, start_time=start_time, status="in_progress")
    db.add(new_activity)
    db.commit()
    db.refresh(new_activity)
    return new_activity.id