from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Session
from sqlalchemy.orm import relationship, mapped_column, Mapped
from zoneinfo import ZoneInfo
from fastapi import HTTPException, status
from app.models.base import Base
from app import schemas
import datetime
from typing import TYPE_CHECKING, List, Literal, Optional, Sequence
from app.config import logger

if TYPE_CHECKING:
    from app.models.user import BaseUser, User
    from app.models.device import Device


SessionStatus = Literal["w trakcie", "potwierdzona", "odrzucona"]


class UserSession(Base):
    __tablename__ = "session"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey(
        "base_user.id", onupdate="RESTRICT", ondelete="SET NULL"), index=True)
    concierge_id: Mapped[int] = mapped_column(ForeignKey(
        "user.id", onupdate="RESTRICT", ondelete="SET NULL"), index=True)
    start_time: Mapped[datetime.datetime]
    end_time: Mapped[Optional[datetime.datetime]]
    status: Mapped[SessionStatus]

    device_operations: Mapped[List["DeviceOperation"]
                              ] = relationship(back_populates="session")
    unapproved_operations: Mapped[List["UnapprovedOperation"]] = relationship(
        back_populates="session")
    user: Mapped["BaseUser"] = relationship(
        foreign_keys=[user_id], back_populates="sessions")
    concierge: Mapped["User"] = relationship(
        foreign_keys=[concierge_id], back_populates="sessions")

    @classmethod
    def create_session(cls,
                       db: Session,
                       user_id: int,
                       concierge_id: int,
                       commit: Optional[bool] = True) -> "UserSession":
        """
        Creates a new session in the database for a given user and concierge.

        The session is initialized with the current timestamp as the start time and a status of "w trakcie". 
        By default, commits the transaction unless specified otherwise.

        Args:
            db (Session): The database session.
            user_id (int): The ID of the user associated with the session.
            concierge_id (int): The ID of the concierge managing the session.
            commit (bool, optional): Whether to commit the transaction immediately. Default is True.

        Returns:
            UserSession: The newly created UserSession object.

        Raises:
            HTTPException: 
                - 500 Internal Server Error: If an error occurs while committing the transaction.
        """
        logger.info("Starting session creation process.")
        logger.debug(
            f"Input parameters - user_id: {user_id}, concierge_id: {concierge_id}")

        start_time = datetime.datetime.now(ZoneInfo("Europe/Warsaw"))
        new_session = UserSession(
            user_id=user_id,
            concierge_id=concierge_id,
            start_time=start_time,
            status="w trakcie"
        )
        db.add(new_session)
        if commit:
            try:
                db.commit()
                db.refresh(new_session)
                logger.info("Session created successfully.")
            except Exception as e:
                logger.error(f"Error while creating session: {str(e)}")
                db.rollback()
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail="An internal error occurred while creating session")
        return new_session

    @classmethod
    def end_session(cls,
                    db: Session,
                    session_id: int,
                    reject: Optional[bool] = False,
                    commit: Optional[bool] = True) -> "UserSession":
        """
        Ends a session by updating its status to either "odrzucona" or "potwierdzona" based on the `reject` argument.

        If `reject` is `False` (default), the status is updated to "potwierdzona". The end time is set to the current timestamp. 
        Raises an exception if the session has already ended.
        By default, commits the transaction unless specified otherwise.

        Args:
            db (Session): The database session.
            session_id (int): The ID of the session to end.
            reject (bool, optional): If True, the session status is set to "odrzucona". Default is False.
            commit (bool, optional): Whether to commit the transaction immediately. Default is True.

        Returns:
            UserSession: The updated UserSession object.

        Raises:
            HTTPException: 
                - 404 Not Found: If the session with the given ID does not exist.
                - 403 Forbidden: If the session has already been ended.
                - 500 Internal Server Error: If an error occurs while committing the transaction.
        """

        logger.info("Attempting to end session.")
        logger.debug(
            f"Input parameters - session_id: {session_id}, reject: {reject}")

        session = db.query(UserSession).filter_by(id=session_id).first()
        if not session:
            logger.warning(
                f"Session with id {session_id} not found for update")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        if session.status == "w trakcie" and session.end_time is None:
            session.status = "odrzucona" if reject else "potwierdzona"
            session.end_time = datetime.datetime.now(ZoneInfo("Europe/Warsaw"))
        else:
            logger.error(
                f"Session with id {session_id} has been already ended with status {session.status}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Session has been already ended")
        if commit:
            try:
                db.commit()
                logger.info(
                    f"Session with ID {session_id} ended successfully.")
            except Exception as e:
                logger.error(
                    f"Error while updating session status with ID {session_id}: {e}")
                db.rollback()
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail="An internal error occurred while updating session status")
        return session

    @classmethod
    def get_session_id(cls,
                       db: Session,
                       session_id: int) -> "UserSession":
        """
        Retrieves a session by its unique ID.

        Args:
            db (Session): The database session.
            session_id (int): The unique ID of the session to retrieve.

        Returns:
            Optional[UserSession]: The UserSession object with the specified ID if found.
        """
        logger.info(f"Attempting to retrieve session with ID: {session_id}")
        session = db.query(UserSession).filter(
            UserSession.id == session_id
        ).first()
        return session


OperationType = Literal["pobranie", "zwrot"]


class UnapprovedOperation(Base):
    __tablename__ = "operation_unapproved"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(ForeignKey(
        "device.id", onupdate="CASCADE", ondelete="CASCADE"), index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey(
        "session.id", onupdate="CASCADE", ondelete="CASCADE"), index=True)
    operation_type: Mapped[OperationType]
    entitled: Mapped[bool]
    timestamp: Mapped[datetime.datetime]

    session: Mapped["UserSession"] = relationship(
        back_populates="unapproved_operations")
    device: Mapped["Device"] = relationship(
        back_populates="unapproved_operations")
    

    @classmethod
    def check_if_rescanned(cls, db: Session, device_id: int, session_id: int) -> Optional["UnapprovedOperation"]:
        """
        Checks if a device has been rescanned during a session.

        Args:
            db (Session): The database session.
            device_id (int): The ID of the device.
            session_id (int): The ID of the session.

        Returns:
            Optional[UnapprovedOperation]: The unapproved operation if found, None otherwise.
        """
        logger.info(
            f"Checking if device with ID: {device_id} has been rescanned during session with ID: {session_id}.")
        operation_unapproved = db.query(UnapprovedOperation).filter(
            UnapprovedOperation.device_id == device_id,
            UnapprovedOperation.session_id == session_id).first()
        if operation_unapproved:
            logger.info(
                f"Device with ID: {device_id} has been rescanned during session with ID: {session_id}.")
        else:
            logger.info(
                f"No rescanned operation found for device ID: {device_id} in session ID: {session_id}.")
        return operation_unapproved

    @classmethod
    def delete_if_rescanned(cls, db: Session, device_id: int, session_id: int) -> bool:
        """
        Deletes an unapproved operation if it has been rescanned during a session.

        This method first checks if the device was rescanned using `check_if_rescanned`.
        If found, it deletes the operation and commits the transaction.

        Args:
            db (Session): The database session.
            device_id (int): The ID of the device.
            session_id (int): The ID of the session.

        Returns:
            bool: True if the unapproved operation was deleted, False otherwise.

        Raises:
            HTTPException: 
            - 500 Internal Server Error: If an error occurs while deleting the unapproved operation.
        """
        operation_unapproved = cls.check_if_rescanned(db, device_id, session_id)
        if not operation_unapproved:
            return False

        logger.info(
            f"Deleting unapproved operation with ID: {operation_unapproved.id}.")
        db.delete(operation_unapproved)
        try:
            db.commit()
            logger.info(
                f"Unapproved operation with ID {operation_unapproved.id} deleted successfully.")
            return True
        except Exception as e:
            db.rollback()
            logger.error(
                f"Error while deleting operation with ID {operation_unapproved.id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="An internal error occurred while deleting operation")


    @classmethod
    def create_unapproved_operation(cls,
                                    db: Session,
                                    operation_data: schemas.DevOperation,
                                    commit: Optional[bool] = True) -> "DeviceOperation":
        """
        Creates an unapproved operation in the database.

        The operation is initialized with the current timestamp. 
        By default, commits the transaction unless specified otherwise.

        Args:
            db (Session): The database session.
            operation_data (schemas.DevOperation): Data required to create the unapproved operation.
            commit (bool, optional): Whether to commit the transaction immediately. Default is True.

        Returns:
            UnapprovedOperation: The newly created unapproved operation object.

        Raises:
            HTTPException: 
                - 500 Internal Server Error: If an error occurs while committing the transaction.
        """
        logger.info("Creating a new unnapproved operation.")
        logger.debug(f"Uapproved peration data provided: {operation_data}")

        new_operation = cls(**operation_data.model_dump())
        new_operation.timestamp = datetime.datetime.now()

        db.add(new_operation)
        if commit:
            try:
                db.commit()
                logger.info(
                    "Unapproved operation created and committed to the database.")
            except Exception as e:
                logger.error(
                    f"Error while creating unapproved operation': {e}")
                db.rollback()
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail="An internal error occurred while creating unapproved operation")
        return new_operation

    @classmethod
    def get_unapproved_filtered(cls,
                                db: Session,
                                session_id: Optional[int] = None,
                                operation_type: Literal["pobranie", "zwrot", None] = None) -> List["UnapprovedOperation"]:
        """
        Retrieves unapproved operations filtered by session ID and/or operation type.

        If no filters are provided, all unapproved operations are retrieved. 
        Raises an exception if no operations match the criteria.

        Args:
            db (Session): The database session.
            session_id (Optional[int]): The ID of the session to filter by (optional).
            operation_type (Optional[Literal["pobranie", "zwrot"]]): The type of operation to filter by (optional).

        Returns:
            List[UnapprovedOperation]: A list of unapproved operations matching the criteria.

        Raises:
            HTTPException: 
                - 204 No Content: If no unapproved operations match the given criteria.
        """
        logger.info(f"Attempting to retrieve unapproved operations")

        unapproved_query = db.query(UnapprovedOperation)
        if session_id:
            logger.debug(
                f"Filtering unapproved operations by session with ID: {session_id}")
            unapproved_query = unapproved_query.filter(
                UnapprovedOperation.session_id == session_id)
        if operation_type:
            logger.debug(
                f"Filtering unapproved operations by operation type: {operation_type}")
            unapproved_query = unapproved_query.filter()
        unapproved = unapproved_query.all()

        logger.debug(
            f"Retrieved {len(unapproved)} unapproved operations that match given criteria.")
        return unapproved

    @classmethod
    def create_operation_from_unapproved(cls,
                                         db: Session,
                                         session_id: int,
                                         commit: Optional[bool] = True) -> List[schemas.DevOperationOut]:
        """
        Transfers unapproved operations to the approved operations table and removes them from the unapproved table.
        By default, commits the transaction unless specified otherwise.

        The function retrieves all unapproved operations for the given session ID, creates corresponding approved operations, and deletes the unapproved ones.

        Args:
            db (Session): The database session.
            session_id (int): The ID of the session.
            commit (bool, optional): Whether to commit the transaction immediately. Default is True.

        Returns:
            List[schemas.DevOperationOut]: A list of approved operation objects created from the unapproved operations.

        Raises:
            HTTPException: 
                - 404 Not Found: If no unapproved operations match the given criteria.
                - 500 Internal Server Error: If an error occurs during the commit.
        """
        logger.info(
            "Transfering unapproved operations to the approved ones.")
        logger.debug(f"Session ID provided:{session_id}")

        unapproved_operations = cls.get_unapproved_filtered(
            db, session_id=session_id)
        if not unapproved_operations:
            logger.warning(
                f"No unapproved operations found that match given criteria")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="No unapproved operations found")

        operation_list: List[schemas.DevOperationOut] = []
        for unapproved_operation in unapproved_operations:
            operation_schema = schemas.DevOperation.model_validate(
                unapproved_operation)
            new_operation = DeviceOperation.create_operation(
                db, operation_schema, False)
            db.flush()
            db.delete(unapproved_operation)
            validated_operation = schemas.DevOperationOut.model_validate(
                new_operation)
            operation_list.append(validated_operation)
        if commit:
            try:
                db.commit()
                logger.info(
                    "Operations removed from unapproved and new upproved operations created")
            except Exception as e:
                db.rollback()
                logger.error(
                    f"Error while removing operations from unapproved and creating new upproved ones': {e}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail="An internal error occurred during operation transfer")
        return operation_list

    @classmethod
    def delete_all_for_session(cls,
                               db: Session,
                               session_id: int,
                               commit: Optional[bool] = True) -> None:
        """
        Deletes all unapproved operations for a given session.

        If no unapproved operations are found for the specified session ID, returns None. 
        By default, commits the transaction unless specified otherwise.

        Args:
            db (Session): The database session.
            session_id (int): The ID of the session whose unapproved operations should be deleted.
            commit (bool, optional): Whether to commit the transaction immediately. Default is True.

        Raises:
            HTTPException: 
                - 500 Internal Server Error: If an error occurs during the commit.
        """
        logger.info(
            f"Deleting all unapproved operations for session ID: {session_id}")

        operations_to_delete = db.query(cls).filter(
            cls.session_id == session_id).all()

        if not operations_to_delete:
            logger.info(
                f"No unapproved operations found for session ID: {session_id}")
            return

        logger.debug(
            f"Found {len(operations_to_delete)} unapproved operations to delete.")

        db.query(cls).filter(cls.session_id == session_id).delete(
            synchronize_session=False)

        if commit:
            try:
                db.commit()
                logger.info(
                    f"All unapproved operations for session ID: {session_id} have been successfully deleted")
            except Exception as e:
                db.rollback()
                logger.error(
                    f"Error while deleting unapproved operations for session ID: {session_id}: {e}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail="An internal error occurred while deleting unapproved operations")


class DeviceOperation(Base):
    __tablename__ = "device_operation"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(ForeignKey(
        "device.id", onupdate="CASCADE", ondelete="CASCADE"), index=True)
    session_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("session.id", onupdate="CASCADE", ondelete="SET NULL"), index=True)
    operation_type: Mapped[OperationType] = mapped_column(index=True)
    entitled: Mapped[bool]
    timestamp: Mapped[datetime.datetime]

    device: Mapped["Device"] = relationship(back_populates="device_operations")
    session: Mapped[Optional["UserSession"]] = relationship(
        back_populates="device_operations")

    @classmethod
    def last_operation_subquery(cls,
                                db: Session):
        """
        Generates a subquery to retrieve the latest operation timestamp for each device.

        The subquery groups operations by `device_id` and retrieves the maximum timestamp for each group.

        Args:
            db (Session): The database session.

        Returns:
            sqlalchemy.sql.selectable.Subquery: A subquery for the latest device operations.
        """

        logger.debug(
            f"Generating a subquery to retrieve latest operation timestamp")
        return (
            db.query(
                cls.device_id,
                func.max(cls.timestamp).label('last_operation_timestamp')
            )
            .group_by(cls.device_id)
            .subquery()
        )

    @classmethod
    def get_last_operation_user_id(cls,
                                   db: Session,
                                   user_id: int,
                                   operation_type: Optional[Literal["pobranie", "zwrot"]] = "pobranie") -> Sequence["DeviceOperation"]:
        """
        Retrieves the last operations of a specific type for a given user.

        Filters operations by user ID and operation type (default: "pobranie"). 
        Retrieves only the latest operation for each device.

        Args:
            db (Session): The database session.
            user_id (int): The ID of the user.
            operation_type (Optional[Literal["pobranie", "zwrot"]]): The type of operation to filter by (default: "pobranie").

        Returns:
            Sequence[DeviceOperation]: A sequence of the user's last device operations.

        Raises:
            HTTPException: 
                - 204 No Content: If no operations are found for the specified user and type.
        """
        logger.info("Attempting to retrieve last user operation.")
        logger.debug(
            f"Filtering operations by user ID: {user_id} and operation type: {operation_type}")

        last_operation_subquery = cls.last_operation_subquery(db)

        query = (
            db.query(cls)
            .join(last_operation_subquery,
                  (cls.device_id == last_operation_subquery.c.device_id) &
                  (cls.timestamp == last_operation_subquery.c.last_operation_timestamp)
                  )
            .join(UserSession, cls.session)
            .filter(UserSession.user_id == user_id)
            .filter(cls.operation_type == operation_type)
            .order_by(cls.timestamp.asc())
        )

        operations = query.all()

        if not operations:
            logger.warning(
                f"Operations for user with ID {user_id} and type: {operation_type} not found.")
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT
            )
        logger.debug(
            f"Retrieved {len(operations)} operations that match given criteria.")
        return operations

    @classmethod
    def create_operation(cls,
                         db: Session,
                         operation_data: schemas.DevOperation,
                         commit: Optional[bool] = True) -> "DeviceOperation":
        """
        Creates a new operation for a device.

        The operation is initialized with the current timestamp. 
        By default, commits the transaction unless specified otherwise.

        Args:
            db (Session): The database session.
            operation_data (schemas.DevOperation): Data required to create the operation.
            commit (bool, optional): Whether to commit the transaction immediately. Default is True.

        Returns:
            DeviceOperation: The newly created DeviceOperation object.

        Raises:
            HTTPException: 
                - 500 Internal Server Error: If an error occurs during the commit process.
        """
        logger.info("Creating a new operation.")
        logger.debug(f"Operation data provided: {operation_data}")

        new_operation = DeviceOperation(**operation_data.model_dump())
        new_operation.timestamp = datetime.datetime.now()

        db.add(new_operation)
        if commit:
            try:
                db.commit()
                logger.info(
                    "Operation created and committed to the database.")
            except Exception as e:
                db.rollback()
                logger.error(
                    f"Error while creating operation': {e}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail="An internal error occurred while creating operation")
        return new_operation

    @classmethod
    def get_all_operations(cls,
                           db: Session,
                           session_id: Optional[int] = None
                           ) -> List["DeviceOperation"]:
        """
        Retrieves all device operations from the database, optionally filtering by session ID.

        If no session ID is provided, retrieves all operations. Raises an exception if no operations are found.

        Args:
            db (Session): The database session.
            session_id (Optional[int]): The session ID to filter by (optional).

        Returns:
            List[DeviceOperation]: A list of DeviceOperation objects matching the criteria.

        Raises:
            HTTPException: 
                - 204 No Content: If no operations are found.
        """
        logger.info("Attempting to retrieve operations.")

        operations_query = db.query(DeviceOperation)
        if session_id:
            logger.debug(f"Filtering operations by session ID: {session_id}")
            operations_query = operations_query.filter(DeviceOperation.session_id == session_id)
        operations = operations_query.all()
        if not operations:
            logger.warning(f"No operations found")
            raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)
        logger.debug(
            f"Retrieved {len(operations)} operations that match given criteria.")
        return operations

    @classmethod
    def get_operation_id(cls,
                         db: Session,
                         operation_id: int) -> "DeviceOperation":
        """
        Retrieves a specific operation by its ID. Raises an exception if operation doesn't exist.

        Args:
            db (Session): The database session.
            operation_id (int): The ID of the operation to retrieve.

        Returns:
            DeviceOperation: The DeviceOperation object with the specified ID.

        Raises:
            HTTPException: 
                - 204 No Content: If no operation with the given ID exists.
        """
        logger.info(
            f"Attempting to retrieve operation with ID: {operation_id}")
        operation = db.query(DeviceOperation).filter(
            DeviceOperation.id == operation_id).first()
        if not operation:
            logger.warning(f"Operationwith ID {operation_id} not found")
            raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)
        logger.debug(f"Retrieved operation")
        return operation

    @classmethod
    def get_last_dev_operation_or_none(cls,
                                       db: Session,
                                       device_id: int) -> "DeviceOperation|None":
        """
        Retrieves the last operation for a specific device or returns None if no operations exist.

        Args:
            db (Session): The database session.
            device_id (int): The ID of the device.

        Returns:
            Optional[DeviceOperation]: The last DeviceOperation object for the specified device, or None if no operations exist.
        """
        from app.models.device import Device
        logger.info(
            f"Attempting to retrieve last operation for device with ID: {device_id}")
        device = Device.get_dev_by_id(db, device_id)
        if not device:
            logger.warning(f"Device with ID {device_id} not found")
            raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)
        subquery = (
            db.query(func.max(DeviceOperation.timestamp))
            .filter(DeviceOperation.device_id == device_id)
            .scalar_subquery()
        )
        operation = (
            db.query(DeviceOperation)
            .filter(
                DeviceOperation.device_id == device_id,
                DeviceOperation.timestamp == subquery
            )
            .first()
        )
        if not operation:
            logger.info(f"Operation for device with ID: {device_id} not found")
        logger.debug(f"Retrieved operation: {operation}")
        return operation
