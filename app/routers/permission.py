import datetime
from fastapi import Depends, APIRouter
from app.schemas import PermissionOut
from app import database, oauth2
from sqlalchemy.orm import Session
from typing import Sequence, Optional
import app.models.permission as mpermission
from app.models.user import User

router = APIRouter(
    prefix="/permissions",
    tags=['Permissions']
)

# todo dane o pozwoleniach brac z systemu pw
# todo sprawdzac date i godzine


@router.get("/", response_model=Sequence[PermissionOut])
def get_permissions(
    user_id: Optional[int] = None,
    room_id: Optional[int] = None,
    date: Optional[datetime.date] = None,
    start_time: Optional[datetime.time] = None,
    current_concierge: User = Depends(oauth2.get_current_concierge),
    db: Session = Depends(database.get_db)
) -> Sequence[PermissionOut]:
    return mpermission.Permission.get_permissions(db, user_id, room_id, date, start_time)
