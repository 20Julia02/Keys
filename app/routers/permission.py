from fastapi import Depends, APIRouter
from app.schemas import PermissionOut, PermissionCreate
from app import database, oauth2
from app.services import securityService, permissionService
from sqlalchemy.orm import Session
from typing import List

router = APIRouter(
    prefix="/permissions",
    tags=['Permissions']
)

# todo dane o pozwoleniach brac z systemu pw
# todo sprawdzac date i godzine


@router.get("/", response_model=List[PermissionOut])
def get_permissions(user_id: int = None,
                    room_id: int = None,
                    current_concierge=Depends(oauth2.get_current_concierge),
                    db: Session = Depends(database.get_db)) -> List[PermissionOut]:
    permission_service = permissionService.PermissionService(db)
    return permission_service.get_permissions(room_id, user_id)


@router.post("/", response_model=PermissionOut)
def create_permission(permission: PermissionCreate,
                      current_concierge=Depends(oauth2.get_current_concierge),
                      db: Session = Depends(database.get_db)):
    """
    Creates a new permission entry in the database.

    Args:
        permission: The permission data to be created.
        current_concierge: The currently authenticated user.
        db: Database session.

    Returns:
        The newly created permission record.

    Raises:
        HTTPException: If the user is not entitled.
    """

    auth_service = securityService.AuthorizationService(db)
    auth_service.check_if_entitled("admin", current_concierge)
    permission_service = permissionService.PermissionService(db)
    new_permission = permission_service.create_permission(permission)
    return new_permission
