import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from app import schemas
import app.models.device as mdevice
import app.models.permission as mpermission
from sqlalchemy import extract


class PermissionService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_permission(self,
                            user_id: int,
                            time: datetime = datetime.datetime.now()) -> mpermission.Permission:
        perm = self.db.query(mpermission.Permission).join(mdevice.Room, mpermission.Permission.room).filter(mpermission.Permission.user_id == user_id,
                                                    mpermission.Permission.start_reservation < time,
                                                    mpermission.Permission.end_reservation > time).order_by(mdevice.Room.number).all()
        if not perm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No reservations found"
            )
        return perm

    def get_filtered_permissions(self,
                        room_id: Optional[int] = None,
                        day: datetime = datetime.datetime.today()
                        ) -> List[mpermission.Permission]:
        """
        Helper function to retrieve permissions by user_id or room_id.
        """
        query = (
            self.db.query(
                mpermission.Permission
            ).filter(
                mpermission.Permission.room_id == room_id,
                extract('year', mpermission.Permission.start_reservation) == day.year,
                extract('month', mpermission.Permission.start_reservation) == day.month,
                extract('day', mpermission.Permission.start_reservation) == day.day
            )
        )
        perm = query.order_by(mpermission.Permission.start_reservation).all()

        if not perm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No reservations found"
            )
        return perm

    def check_if_permitted(self,
                           user_id: int,
                           room_id: int,
                           last_operation_type: Optional[str] = None,
                           force: bool = False) -> bool:
        """
        Checks if a user has permission to access a specific room.

        If the user doesn't have permission and the operation is not forced, it raises
        an HTTPException with a 403 status code. If the operation is forced, it returns False.

        Args:
            user_id (int): ID of the user whose permissions are being checked.
            room_id (int): ID of the room to check access for.
            force (bool, optional): Whether to force the operation despite lack of permissions.

        Returns:
            bool: True if the user has permission, False if permission is absent but the operation is forced.

        Raises:
            HTTPException: If the user doesn't have permission and the operation is not forced.
        """
        has_permission = self.db.query(mpermission.Permission).filter(
            mpermission.Permission.user_id == user_id,
            mpermission.Permission.room_id == room_id,
            mpermission.Permission.start_reservation < datetime.datetime.now(),
            mpermission.Permission.end_reservation > datetime.datetime.now()
        ).first()
        if not has_permission:
            if not force and (last_operation_type is None or last_operation_type == "zwrot"):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                    detail=f"User with id {user_id} does not have permission to access room with id {room_id}")
            return False
        else:
            return True

    def create_permission(self, permission: schemas.PermissionCreate, commit: bool = True) -> mpermission.Permission:
        """
        Creates a new permission in the database.
        """
        new_permission = mpermission.Permission(**permission.model_dump())
        self.db.add(new_permission)
        if commit:
            self.db.commit()
            self.db.refresh(new_permission)
        return new_permission
