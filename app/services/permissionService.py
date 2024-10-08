from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from app import models, schemas

# todo tu sie dzieje zlo


class PermissionService:
    def __init__(self, db: Session):
        self.db = db

    def get_permissions(self,
                        room_id: Optional[int] = None,
                        user_id: Optional[int] = None) -> List[schemas.PermissionOut]:
        """
        Helper function to retrieve permissions by user_id or room_id.
        """
        query = self.db.query(models.Permission)
        if user_id:
            query = query.filter(models.Permission.user_id == user_id)
        if room_id:
            query = query.filter(models.Permission.room_id == room_id)

        perm = query.all()

        if not perm:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="No permissions found that meet the stated criteria")
        return perm

    def check_if_permitted(self, user_id: int, room_id: int, force: bool = False) -> bool:
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
            models.Permission.room_id == room_id
        ).first()

        if has_permission:
            return True
        elif force:
            return False
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User with id {user_id} does not have permission to access room with id {room_id}"
            )

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
