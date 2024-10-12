import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from app import models, schemas
from sqlalchemy import and_, extract


class PermissionService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_permission(self,
                            user_id: int,
                            time: datetime = datetime.datetime.now()) -> schemas.PermissionOut:
        perm = self.db.query(models.Permission).join(models.Room, models.Permission.room_id == models.Room.id).filter(models.Permission.user_id == user_id,
                                                    models.Permission.start_reservation < time,
                                                    models.Permission.end_reservation > time).order_by(models.Room.number).all()
        if not perm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No reservations found"
            )
        return perm

    def get_filtered_permissions(self,
                        room_id: Optional[int] = None,
                        day: datetime = datetime.datetime.today()
                        ) -> List[schemas.PermissionOut]:
        """
        Helper function to retrieve permissions by user_id or room_id.
        """
        query = (
            self.db.query(
                models.Permission
            ).filter(
                models.Permission.room_id == room_id,
                extract('year', models.Permission.start_reservation) == day.year,
                extract('month', models.Permission.start_reservation) == day.month,
                extract('day', models.Permission.start_reservation) == day.day
            )
        )
        perm = query.order_by(models.Permission.start_reservation).all()

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
        has_permission = self.db.query(models.Permission).filter(
            models.Permission.user_id == user_id,
            models.Permission.room_id == room_id,
            models.Permission.start_reservation < datetime.datetime.now(),
            models.Permission.end_reservation > datetime.datetime.now()
        ).first()
        if not has_permission: 
            if not force and (last_operation_type is None or last_operation_type == "return_dev"):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                    detail=f"User with id {user_id} does not have permission to access room with id {room_id}")
            return False
        else:
            return True

    def create_permission(self, permission: schemas.PermissionCreate, commit: bool = True):
        """
        Creates a new permission in the database.
        """
        new_permission = models.Permission(**permission.model_dump())
        self.db.add(new_permission)
        if commit:
            self.db.commit()
            self.db.refresh(new_permission)
        return new_permission
