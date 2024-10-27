from sqlalchemy import ForeignKey, String, extract
from sqlalchemy.orm import relationship, mapped_column, Mapped, Session
from typing import Optional, List
import datetime
from app.models.base import Base, intpk, timestamp
from app.models.user import User
from app.models.device import Room
from fastapi import HTTPException, status
from app import schemas


class TokenBlacklist(Base):
    __tablename__ = 'token_blacklist'

    id: Mapped[intpk]
    token: Mapped[str] = mapped_column(String(255), unique=True)
    added_at: Mapped[Optional[timestamp]]


class Permission(Base):
    __tablename__ = "permission"
    id: Mapped[intpk]
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    room_id: Mapped[int] = mapped_column(ForeignKey("room.id"))
    start_reservation: Mapped[datetime.datetime]
    end_reservation: Mapped[datetime.datetime]

    user: Mapped["User"] = relationship(back_populates="permissions")
    room: Mapped["Room"] = relationship(back_populates="permissions")

    @classmethod
    def get_permissions(cls,
                        db: Session,
                        user_id: Optional[int] = None,
                        room_id: Optional[int] = None,
                        start_time: Optional[datetime.datetime] = None,
                        ) -> List["Permission"]:
        query = db.query(Permission)
        
        if user_id is not None:
            query = query.filter(Permission.user_id == user_id)

        if room_id is not None:
            query = query.filter(Permission.room_id == room_id)

        if start_time is not None:
            query = query.filter(Permission.start_reservation >= start_time)

        permissions = query.order_by(Permission.start_reservation).all()

        if not permissions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No reservations found"
            )
        return permissions

    @classmethod
    def check_if_permitted(cls,
                           db: Session,
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
        has_permission = db.query(Permission).filter(
            Permission.user_id == user_id,
            Permission.room_id == room_id,
            Permission.start_reservation < datetime.datetime.now(),
            Permission.end_reservation > datetime.datetime.now()
        ).first()
        if not has_permission:
            if not force and (last_operation_type is None or last_operation_type == "zwrot"):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                    detail=f"User with id {user_id} does not have permission to access room with id {room_id}")
            return False
        else:
            return True

    @classmethod
    def create_permission(cls,
                           db: Session, 
                           permission: schemas.PermissionCreate, 
                           commit: bool = True) -> "Permission":
        """
        Creates a new permission in the database.
        """
        new_permission = Permission(**permission.model_dump())
        db.add(new_permission)
        if commit:
            db.commit()
            db.refresh(new_permission)
        return new_permission
