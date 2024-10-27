import datetime
from fastapi import Depends, APIRouter
from app.schemas import PermissionOut
from app import database, oauth2
from sqlalchemy.orm import Session
from typing import List
import app.models.permission as mpermission

router = APIRouter(
    prefix="/permissions",
    tags=['Permissions']
)

# todo dane o pozwoleniach brac z systemu pw
# todo sprawdzac date i godzine


@router.get("/", response_model=List[PermissionOut])
def get_filtered_permissions(room_id: int = None,
                    day: datetime.datetime = datetime.datetime.today(),
                    current_concierge=Depends(oauth2.get_current_concierge),
                    db: Session = Depends(database.get_db)) -> List[PermissionOut]:
    return mpermission.Permission.get_filtered_permissions(db, room_id, day)


@router.get("/users/{user_id}", response_model=List[PermissionOut])
def get_user_permissions(user_id: int,
                         time: datetime.datetime = datetime.datetime.now(),
                         current_concierge=Depends(oauth2.get_current_concierge),
                         db: Session = Depends(database.get_db)) -> List[PermissionOut]:
    return mpermission.Permission.get_user_permission(db, user_id, time)