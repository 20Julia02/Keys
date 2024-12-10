from sqlalchemy import and_, or_, CheckConstraint, Integer, case, func, ForeignKey, String, Date, Time, text, Table, Connection, event
from sqlalchemy.orm import relationship, mapped_column, Mapped, Session
from typing import Optional, List, Any
import datetime
from app.models.base import Base, timestamp
from app.models.user import User
from app.models.device import Room
from fastapi import HTTPException, status
from app import schemas
from app.config import logger


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

    __table_args__ = (
        CheckConstraint("end_time > start_time",
                        name="check_end_time_gt_start_time"),
    )

    @classmethod
    def get_permissions(cls,
                        db: Session,
                        user_id: Optional[int] = None,
                        room_id: Optional[int] = None,
                        date: Optional[datetime.date] = None,
                        time: Optional[datetime.time] = None,
                        ) -> List["Permission"]:
        """
        Retrieves a list of permissions based on specified filters such as `user_id`, `room_id`, `date`, and `time`.

        Filters permissions that occur today or in the future. 
        For today's date, it includes permissions that are currently active or start later on the same day. 
        Results are sorted by date and start time.

        Args:
            db (Session): The database session.
            user_id (Optional[int]): The ID of the user whose permissions are being queried. Default is None.
            room_id (Optional[int]): The ID of the room for which permissions are being queried. Default is None.
            date (Optional[datetime.date]): The specific date for which permissions should be retrieved. Default is None.
            time (Optional[datetime.time]): The specific time for which permissions should be retrieved. Default is None.

        Returns:
            List[Permission]: A list of permissions matching the specified criteria.

        Raises:
            HTTPException: 
                - 404 Not Found: If no permissions are found that match the given criteria.
        """
        logger.info(f"Attempting to retrieve permissions")

        current_date = datetime.date.today()
        current_time = datetime.datetime.now().time()

        query = db.query(Permission).filter(
            or_(
                Permission.date > current_date,
                and_(
                    Permission.date == current_date,
                    Permission.end_time >= current_time
                )
            )
        )

        if user_id is not None:
            logger.debug(f"Filtering permissions by user with ID: {user_id}")
            query = query.filter(Permission.user_id == user_id)

        if room_id is not None:
            logger.debug(f"Filtering permissions by room with ID: {room_id}")
            query = query.filter(Permission.room_id == room_id)

        if date is not None:
            logger.debug(f"Filtering permissions by date: {date}")
            query = query.filter(Permission.date == date)

        if time is not None:
            logger.debug(f"Filtering permissions by time: {time}")
            query = query.filter(Permission.start_time <= time, Permission.end_time >= time)

        permissions = query.order_by(Permission.date, Permission.start_time).all()

        if not permissions:
            logger.warning("No permissions found that match given criteria")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No permissions found that match given criteria"
            )

        logger.debug(f"Retrieved {len(permissions)} permissions that match given criteria.")
        return permissions

    @classmethod
    def check_if_permitted(cls,
                           db: Session,
                           user_id: int,
                           room_id: int) -> bool:
        """
        Checks if a user has active permission to access a specific room at the current date and time.

        Args:
            db (Session): The database session.
            user_id (int): The ID of the user whose permission is being checked.
            room_id (int): The ID of the room being accessed.

        Returns:
            bool: True if the user has permission, False otherwise.
        """
        logger.info(
            f"Checking if user with ID: {user_id} has permission to access room with ID: {room_id}")
        current_date = datetime.date.today()
        current_time = datetime.datetime.now().time()
        has_permission = db.query(Permission).filter(
            Permission.user_id == user_id,
            Permission.room_id == room_id,
            Permission.date == current_date,
            Permission.start_time <= current_time,
            Permission.end_time >= current_time
        ).first()

        logger.debug(
            f"User has permission with ID {has_permission.id}"
            if has_permission else "User doesn't have permission")
        return bool(has_permission)

    @classmethod
    def create_permission(cls,
                          db: Session,
                          permission_data: schemas.PermissionCreate,
                          commit: Optional[bool] = True) -> "Permission":
        """
        Creates a new permission and saves it to the database.

        Commits the transaction unless specified otherwise.

        Args:
            db (Session): The database session.
            permission_data (schemas.PermissionCreate): Data required to create the permission.
            commit (bool, optional): Whether to commit the transaction immediately. Default is True.

        Returns:
            Permission: The newly created permission object.

        Raises:
            HTTPException: 
                - 500 Internal Server Error: If an error occurs during the commit process.
        """
        logger.info("Creating a new permission")

        new_permission = cls(**permission_data.model_dump())
        db.add(new_permission)
        if commit:
            try:
                db.commit()
                logger.info(
                    "Permission created and committed to the database.")
            except Exception as e:
                db.rollback()
                logger.error(
                    f"Error while creating permission: {e}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail="An internal error occurred while creating permission")
        return new_permission

    @classmethod
    def update_permission(cls,
                          db: Session,
                          permission_id: int,
                          permission_data: schemas.PermissionCreate,
                          commit: Optional[bool] = True) -> "Permission":
        """
        Updates an existing permission in the database.
        Commits the transaction unless specified otherwise.

        Args:
            db (Session): The database session.
            permission_id (int): The ID of the permission to update.
            permission_data (schemas.PermissionUpdate): Data for updating the permission.
            commit (bool, optional): Whether to commit the transaction immediately. Default is True.

        Returns:
            Permission: The updated Permission object.

        Raises:
            HTTPException: 
                - 404 Not Found: If the permission with the given ID does not exist.
                - 500 Internal Server Error: If an error occurs during the commit process.
        """
        logger.info(
            f"Attempting to update permission with ID: {permission_id}")
        logger.debug(
            f"New permission data: {permission_data}")
        
        permission = db.query(Permission).filter(
            Permission.id == permission_id).first()
        if not permission:
            logger.warning(f"Permission with ID {permission_id} not found")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Permission doesn't exist")

        permission.user_id = permission_data.user_id
        permission.room_id = permission_data.room_id
        permission.date = permission_data.date
        permission.start_time = permission_data.start_time
        permission.end_time = permission_data.end_time

        if commit:
            try:
                db.commit()
                logger.info(
                    f"Permission with ID {permission_id} updated successfully.")
            except Exception as e:
                logger.error(
                    f"Error while updating permission with ID {permission_id}: {e}")
                db.rollback()
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail="An internal error occurred while updating permission")
        return permission

    @classmethod
    def delete_permission(cls,
                          db: Session,
                          permission_id: int,
                          commit: Optional[bool] = True) -> bool:
        """
        Deletes a permission by its ID from the database. Commits the transaction unless specified otherwise.

        Args:
            db (Session): The database session.
            permission_id (int): The ID of the permission to delete.
            commit (bool, optional): Whether to commit the transaction immediately. Default is True.

        Returns:
            bool: True if the permission was successfully deleted.

        Raises:
            HTTPException: 
                - 404 Not Found: If the permission with the given ID does not exist.
                - 500 Internal Server Error: If an error occurs during the commit process.
        """
        logger.info(
            f"Attempting to delete permission with ID: {permission_id}")
        permission = db.query(Permission).filter(
            Permission.id == permission_id).first()
        if not permission:
            logger.warning(f"Permission with ID {permission_id} not found")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Permission doesn't exist")
        db.delete(permission)
        if commit:
            try:
                logger.info(
                    f"Permission with ID {permission_id} deleted successfully.")
                db.commit()
            except Exception as e:
                logger.error(
                    f"Error while deleting permission with ID {permission_id}: {e}")
                db.rollback()
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail="An internal error occurred while deleting permission")
        return True

    @classmethod
    def get_active_permissions(cls,
                               db: Session,
                               user_id: int,
                               date: Optional[datetime.date] = datetime.datetime.now().date(),
                               time: Optional[datetime.time] = datetime.datetime.now().time()) -> List["Permission"]:
        """
        Retrieves all active permissions for a user at a specific date and time.

        Filters permissions for the given user, date, and time, and sorts them by room number. If no date or time is provided, defaults to the current date and time.

        Args:
            db (Session): The database session.
            user_id (int): The ID of the user whose permissions are being checked.
            date (Optional[datetime.date]): The date to check for permissions. Defaults to the current date.
            time (Optional[datetime.time]): The time to check for permissions. Defaults to the current time.

        Returns:
            List[Permission]: A list of active permissions for the user at the specified date and time.
        
        Raises:
            HTTPException: 
                - 404 Not Found: If no permissions are found that match the given criteria.
        """
        logger.info(f"Checking active permissions for user with ID {user_id}")
        logger.debug(
            f"Filtering permissions for date: {date} and time: {time}")

        query = db.query(Permission).join(Room, Permission.room_id == Room.id).filter(
            Permission.user_id == user_id,
            Permission.date == date,
            Permission.start_time <= time,
            Permission.end_time >= time
        )

        numeric_part = func.regexp_replace(Room.number, r'\D+', '', 'g')
        text_part = func.regexp_replace(Room.number, r'\d+', '', 'g')

        query = query.order_by(
            case(
                (numeric_part != '', func.cast(numeric_part, Integer)),
                else_=None
            ).asc(),
            case(
                (numeric_part == '', text_part),
                else_=None
            ).asc(),
            text_part.asc()
        )

        permissions = query.all()
        if not permissions:
            logger.warning("No permissions found that match given criteria")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No permissions found that match given criteria"
            )
        
        logger.debug(
            f"Found {len(permissions)} permissions for user with ID {user_id} at the specified time")
        return permissions


@event.listens_for(Permission.__table__, 'after_create')
def delete_old_reservations(target: Table,
                            connection: Connection,
                            **kwargs: Any) -> None:
    """
    Deletes permissions older than one week after the `Permission` table is created.

    This function is automatically invoked when the `Permission` table is created.

    Args:
        target (Table): The table affected by the operation (`Permission` in this case).
        connection (Connection): Database connection object used to execute the query.
        **kwargs (Any): Additional arguments.

    Returns:
        None
    """

    one_week_ago = datetime.date.today() - datetime.timedelta(weeks=1)
    delete_query = text(
        f"DELETE FROM {target.name} WHERE date < :one_week_ago")
    connection.execute(delete_query, {"one_week_ago": one_week_ago})


@event.listens_for(Permission.__table__, 'after_create')
def create_permission_conflict_trigger(target: Table,
                                       connection: Any,
                                       **kw: Any) -> None:
    """
    Creates a database trigger to prevent time conflicts in room permissions.

    The trigger ensures that no overlapping permissions exist for the same room on the same date.

    Args:
        target (Table): The table to which the trigger applies (`Permission`).
        connection (Any): The database connection used to execute the trigger creation.
        **kw (Any): Additional arguments.

    Returns:
        None
    """
    connection.execute(text("""
    CREATE OR REPLACE FUNCTION check_room_permission_conflict() 
    RETURNS TRIGGER AS $$
    BEGIN
        IF EXISTS (
            SELECT 1 
            FROM permission
            WHERE room_id = NEW.room_id 
            AND date = NEW.date
            AND start_time < NEW.end_time
            AND end_time > NEW.start_time
        ) THEN
            RAISE EXCEPTION 'A permission already exists for the specified room and time.';
        END IF;
        
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """))

    connection.execute(text("""
    CREATE TRIGGER room_permission_conflict_trigger
    BEFORE INSERT OR UPDATE ON permission
    FOR EACH ROW EXECUTE FUNCTION check_room_permission_conflict();
    """))
