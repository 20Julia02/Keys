from sqlalchemy import ForeignKey, String, Date, Time, text
from sqlalchemy.orm import relationship, mapped_column, Mapped, Session
from typing import Optional, List
import datetime
from app.models.base import Base, intpk, timestamp
from app.models.user import User
from app.models.device import Room
from fastapi import HTTPException, status
from app import schemas
from sqlalchemy import event


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
    date: Mapped[datetime.date] = mapped_column(Date)
    start_time: Mapped[datetime.time] = mapped_column(Time)
    end_time: Mapped[datetime.time] = mapped_column(Time)

    user: Mapped["User"] = relationship(back_populates="permissions")
    room: Mapped["Room"] = relationship(back_populates="permissions")

    @classmethod
    def get_permissions(cls,
                        db: Session,
                        user_id: Optional[int] = None,
                        room_id: Optional[int] = None,
                        date: Optional[datetime.date] = None,
                        start_time: Optional[datetime.time] = None,
                        ) -> List["Permission"]:
        query = db.query(Permission).filter(Permission.date >= datetime.date.today())

        if user_id is not None:
            query = query.filter(Permission.user_id == user_id)

        if room_id is not None:
            query = query.filter(Permission.room_id == room_id)

        if date is not None:
            query = query.filter(Permission.date == date)

        if start_time is not None:
            query = query.filter(Permission.start_time == start_time)

        permissions = query.order_by(Permission.date, Permission.start_time).all()

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
        """
        current_date = datetime.date.today()
        current_time = datetime.datetime.now().time()
        
        has_permission = db.query(Permission).filter(
            Permission.user_id == user_id,
            Permission.room_id == room_id,
            Permission.date == current_date,
            Permission.start_time <= current_time,
            Permission.end_time >= current_time
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


@event.listens_for(Permission.__table__, 'after_create')
def delete_old_reservations(target, connection, **kwargs):
    one_week_ago = datetime.date.today() - datetime.timedelta(weeks=1)
    delete_query = text(f"DELETE FROM {target.name} WHERE date < :one_week_ago")
    connection.execute(delete_query, {"one_week_ago": one_week_ago})
