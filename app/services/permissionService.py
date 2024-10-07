from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List
from app import models, schemas


class PermissionService:
    def __init__(self, db: Session):
        self.db = db

    def get_room_or_404(self, room_id: int):
        """
        Helper function to retrieve room by id or raise a 404 error.
        """
        room = self.db.query(models.Room).filter(models.Room.id == room_id).first()
        if not room:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Room with id: {room_id} doesn't exist")
        return room

    def get_user_or_404(self, user_id: int):
        """
        Helper function to retrieve user by id or raise a 404 error.
        """
        user = self.db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"User with id: {user_id} doesn't exist")
        return user

    def get_all_permissions(self) -> List[schemas.PermissionOut]:
        """
        Helper function to retrieve permissions by user_id or room_id.
        """
        perm = self.db.query(models.Permission).all()
        if not perm:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="No permissions found")
        return perm

    def get_permissions_by_field(self, field_name: str, field_value: int) -> List[schemas.PermissionOut]:
        """
        Helper function to retrieve permissions by user_id or room_id.
        """
        perm = self.db.query(models.Permission).filter(getattr(models.Permission, field_name) == field_value).all()
        if not perm:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"No permissions found for {field_name} with value: {field_value}")
        return perm

    def get_room_permission(self, room_id: int) -> List[schemas.PermissionOut]:
        """
        Retrieves all permissions for a given room.
        """
        self.get_room_or_404(room_id)
        return self.get_permissions_by_field('room_id', room_id)

    def get_user_permission(self, user_id: int) -> List[schemas.PermissionOut]:
        """
        Retrieves all permissions for a given user.
        """
        self.get_user_or_404(user_id)
        return self.get_permissions_by_field('user_id', user_id)

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
        self.get_user_or_404(user_id)
        self.get_room_or_404(room_id)

        perm = self.db.query(models.Permission).filter(
            models.Permission.user_id == user_id,
            models.Permission.room_id == room_id
        ).first()

        if perm:
            return True

        if not perm and force:
            return False

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User with id {user_id} does not have permission to access room with id {room_id}")

    def create_permission(self, permission: schemas.PermissionCreate, commit: bool = True):
        """
        Creates a new permission in the database.
        """
        new_permission = models.Permission(**permission.model_dump())
        self.db.add(new_permission)
        if commit:
            self.db.commit()
        return new_permission
