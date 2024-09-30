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

    def check_if_permitted(self, user_id: int, room_id: int):
        """
        Checks if a user has permission to access a room.
        """
        self.get_user_or_404(user_id)
        self.get_room_or_404(room_id)

        perm = self.db.query(models.Permission).filter(
            models.Permission.user_id == user_id,
            models.Permission.room_id == room_id
        ).first()
        return perm is not None

    def create_permission(self, permission: schemas.PermissionCreate):
        """
        Creates a new permission in the database.
        """
        new_permission = models.Permission(**permission.model_dump())
        self.db.add(new_permission)
        self.db.commit()
        self.db.refresh(new_permission)
        return new_permission
