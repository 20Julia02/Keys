from sqlalchemy import ForeignKey, String, Date, Time, text, Table, Connection, event
from sqlalchemy.orm import relationship, mapped_column, Mapped, Session
from typing import Optional, List, Any
import datetime
from app.models.base import Base, timestamp
from app.models.user import User
from app.models.device import Room
from fastapi import HTTPException, status
from app import schemas


class TokenBlacklist(Base):
    __tablename__ = 'token_blacklist'

    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(String(255), unique=True)
    added_at: Mapped[Optional[timestamp]]


class Permission(Base):
    __tablename__ = "permission"
    id: Mapped[int] = mapped_column(primary_key=True)
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
        """
        Retrieves a list of permissions based on specified filters like `user_id`, `room_id`, `date`, and `start_time`.
        The results are sorted by date and start time.

        Args:
            db (Session): Database session used to execute the query.
            user_id (Optional[int], optional): ID of the user whose permissions are being queried. Default is `None`.
            room_id (Optional[int], optional): ID of the room for which permissions are being queried. Default is `None`.
            date (Optional[datetime.date], optional): Date of permissions to retrieve. Default is `None`.
            start_time (Optional[datetime.time], optional): Start time of permissions to retrieve. Default is `None`.

        Returns:
            List[Permission]: A list of permissions that match the specified criteria.

        Raises:
            HTTPException: Raises a 404 error if no permissions are found, with the message "No reservations found".
        """
        query = db.query(Permission).filter(
            Permission.date >= datetime.date.today())

        if user_id is not None:
            query = query.filter(Permission.user_id == user_id)

        if room_id is not None:
            query = query.filter(Permission.room_id == room_id)

        if date is not None:
            query = query.filter(Permission.date == date)

        if start_time is not None:
            query = query.filter(Permission.start_time == start_time)

        permissions = query.order_by(
            Permission.date, Permission.start_time).all()

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
                           room_id: int) -> bool:
        """
        Checks if the user has permission to access a specific room. Permissions are checked for the moment.
        Returns `True` or `False` depending on whether the user has active permissions.

        Args:
            db (Session): Database session used to execute the query.
            user_id (int): ID of the user whose permissions are being checked.
            room_id (int): ID of the room being accessed.

        Returns:
            bool: `True` if the user has permission, `False` otherwise.
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

        return bool(has_permission)

    @classmethod
    def create_permission(cls,
                          db: Session,
                          permission: schemas.PermissionCreate,
                          commit: bool = True) -> "Permission":
        """
        Creates a new permission based on the data provided in `permission` and saves it to the database.
        Commits and refreshes the object depending on the value of `commit`.

        Args:
            db (Session): Database session used to execute the operation.
            permission (schemas.PermissionCreate): Schema containing data for creating a new permission.
            commit (bool, optional): Indicates whether to commit changes to the database after adding the new permission. Default is `True`.

        Returns:
            Permission: The newly created permission.

        Raises:
            Exception: If there are issues adding or committing the permission.
        """
        new_permission = Permission(**permission.model_dump())
        db.add(new_permission)
        if commit:
            db.commit()
            db.refresh(new_permission)
        return new_permission


@event.listens_for(Permission.__table__, 'after_create')
def delete_old_reservations(target: Table,
                            connection: Connection,
                            **kwargs: Any) -> None:
    """
    Deletes permissions older than one week after the `Permission` table is created to keep the database current.
    Automatically invoked after the `Permission` table is created.

    Args:
        target (Table): The table affected by the operation, in this case `Permission`.
        connection (Connection): Database connection object used to execute the delete query.
        **kwargs (Any): Additional arguments passed to the event.

    Returns:
        None
    """
    one_week_ago = datetime.date.today() - datetime.timedelta(weeks=1)
    delete_query = text(
        f"DELETE FROM {target.name} WHERE date < :one_week_ago")
    connection.execute(delete_query, {"one_week_ago": one_week_ago})
