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

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey(
        "base_user.id", onupdate="RESTRICT", ondelete="SET NULL"))
    concierge_id: Mapped[int] = mapped_column(ForeignKey(
        "user.id", onupdate="RESTRICT", ondelete="SET NULL"))
    start_time: Mapped[datetime.datetime] = mapped_column(index=True)
    end_time: Mapped[Optional[datetime.datetime]]
    status: Mapped[SessionStatus] = mapped_column(index=True)

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

        Args:
            db (Session): The database session.
            user_id (int): The ID of the user associated with the session.
            concierge_id (int): The ID of the concierge managing the session.
            commit (bool, optional): Whether to commit the transaction after adding the device.

        Returns:
            UserSession: The UserSession object with the specified ID.
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
                                    detail=f"An internal error occurred while creating session")
        return new_session

    @classmethod
    def end_session(cls,
                    db: Session,
                    session_id: int,
                    reject: Optional[bool] = False,
                    commit: Optional[bool] = True) -> "UserSession":
        """
        Changes the status of the session to rejected or completed
        depending on the given value of the reject argument. The default
        (reject = False) changes the status to completed.

        Args:
            db (Session): The database session.
            session_id (int): the ID of the session
            reject (bool, optional): if False the status changes to completed, else to rejected
            commit (bool, optional): Whether to commit the transaction after adding the device.

        Returns:
            _type_: schemas.Session. The session with completed status

        Raises:
            HTTPException: If the session with given ID doesn't exist
        """

        logger.info("Attempting to end session.")
        logger.debug(
            f"Input parameters - session_id: {session_id}, reject: {reject}")

        session = db.query(UserSession).filter_by(id=session_id).first()
        if not session:
            logger.warning(
                f"Session with id {session_id} not found for update")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Session with id {session_id}not found")
        if session.status == "w trakcie" and session.end_time is None:
            session.status = "odrzucona" if reject else "potwierdzona"
            session.end_time = datetime.datetime.now(ZoneInfo("Europe/Warsaw"))
        else:
            logger.error(
                f"Session with id {session_id} has been allready ended with status {session.status}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail=f"Session has been allready ended.")
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
                                    detail=f"An internal error occurred while updating session status")
        return session

    @classmethod
    def get_session_id(cls,
                       db: Session,
                       session_id: int) -> "UserSession":
        """
        Retrieves a session by its ID.

        Args:
            db (Session): The database session.
            session_id (int): ID of the session.

        Returns:
            UserSession: The UserSession object with the specified ID.

        Raises:
            HTTPException: If no session with the given ID exists.
        """
        logger.info(f"Attempting to retrieve session with ID: {session_id}")
        session = db.query(UserSession).filter(
            UserSession.id == session_id
        ).first()

        if not session:
            logger.warning(f"Session with ID {session_id} not found.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Session doesn't exist")

        logger.debug(f"Retrieved session: {session}")
        return session


OperationType = Literal["pobranie", "zwrot"]


class UnapprovedOperation(Base):
    __tablename__ = "operation_unapproved"
    id: Mapped[int] = mapped_column(primary_key=True)
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
    def delete_if_rescanned(cls,
                            db: Session,
                            device_id: int,
                            session_id: int) -> bool:
        """
        Checks if a device has been rescanned during a session. If it has, 
        deletes the unapproved operation and returns True. Otherwise, returns False.

        Args:
            db (Session): The database session.
            device_id (int): ID of the device.
            session_id (int): ID of the session.

        Returns:
            bool: True if device has been rescanned during one session 
            and unapproved operation was deleted, False otherwise.
        """
        logger.info(
            f"Attempting to check if device with ID: {device_id} has been rescanned during session with id: {session_id}")
        operation_unapproved = db.query(UnapprovedOperation).filter(
            UnapprovedOperation.device_id == device_id,
            UnapprovedOperation.session_id == session_id).first()
        if operation_unapproved:
            logger.info(
                f"Device with ID: {device_id} has been rescanned during session with ID: {session_id}.")
            db.delete(operation_unapproved)
            try:
                db.commit()
                logger.info(
                    f"Unapproved operation with ID {operation_unapproved.id} deleted successfully.")
            except Exception as e:
                db.rollback()
                logger.error(
                    f"Error while deleting operation with ID {operation_unapproved.id}: {e}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail=f"An internal error occurred while deleting operation")

            return True
        return False

    @classmethod
    def create_unapproved_operation(cls,
                                    db: Session,
                                    operation_data: schemas.DevOperation,
                                    commit: Optional[bool] = True) -> "DeviceOperation":
        """
        Creates an unapproved operation in the database.

        Args:
            db (Session): The database session.
            operation_data (schemas.DevOperation): Data for the unapproved operation.
            commit (bool, optional): Whether to commit the operation to the database.

        Returns:
            DeviceOperation: The created unapproved operation object.
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
                                    detail=f"An internal error occurred while creating unapproved operation")
        return new_operation

    @classmethod
    def get_unapproved_filtered(cls,
                                db: Session,
                                session_id: Optional[int] = None,
                                operation_type: Literal["pobranie", "zwrot", None] = None) -> List["UnapprovedOperation"]:
        """
        Retrieves unapproved operations. It filters results by a given session ID and operation type.

        Args:
            db (Session): The database session.
            session_id (int): ID of the session to filter by.
            operation_type(Optional[Literal["pobranie", "zwrot"]]): the type of operation to filter by.

        Returns:
            List[UnapprovedOperation]: A list of unapproved operations for the session.

        Raises:
            HTTPException: If no unapproved operations are found.
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
        if not unapproved:
            logger.warning(
                f"No unapproved operations found that match given criteria")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="No unapproved operations found for this session")

        logger.debug(
            f"Retrieved {len(unapproved)} unapproved operations that match given criteria.")
        return unapproved

    @classmethod
    def create_operation_from_unapproved(cls,
                                         db: Session,
                                         session_id: int,
                                         commit: Optional[bool] = True) -> List[schemas.DevOperationOut]:
        """
        Transfers unapproved operations to the approved operations table and
        removes them from the unapproved table.

        Args:
            db (Session): The database session.
            session_id (int): ID of the session.
            commit (bool, optional): Whether to commit the operations to the database.

        Returns:
            List[schemas.DevOperationOut]: A list of approved operation objects.

        Raises:
            HTTPException: If an error occurs during operation transfer.
        """
        logger.info(
            "Transfering unapproved operations to the approved ones.")
        logger.debug(f"Session ID provided:{session_id}")

        unapproved_operations = cls.get_unapproved_filtered(
            db, session_id=session_id)
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
                                    detail=f"An internal error occurred during operation transfer")
        return operation_list

    @classmethod
    def delete_all_for_session(cls,
                               db: Session,
                               session_id: int,
                               commit: Optional[bool] = True) -> None:
        """
        Deletes all unapproved operations for the given session ID.

        Args:
            db (Session): The database session.
            session_id (int): ID of the session whose unapproved operations should be deleted.
            commit (bool, optional): Whether to commit the transaction after deletion.

        Raises:
            HTTPException: If an error occurs during the deletion process.
        """
        logger.info(
            f"Deleting all unapproved operations for session ID: {session_id}")

        try:
            operations_to_delete = db.query(cls).filter(
                cls.session_id == session_id).all()

            if not operations_to_delete:
                logger.info(
                    f"No unapproved operations found for session ID: {session_id}")
                return

            logger.debug(
                f"Found {len(operations_to_delete)} unapproved operations to delete.")

            for operation in operations_to_delete:
                db.delete(operation)

            if commit:
                db.commit()
                logger.info(
                    f"All unapproved operations for session ID: {session_id} have been successfully deleted")
        except Exception as e:
            db.rollback()
            logger.error(
                f"Error while deleting unapproved operations for session ID: {session_id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"An internal error occurred while deleting unapproved operations")


class DeviceOperation(Base):
    __tablename__ = "device_operation"

    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey(
        "device.id", onupdate="CASCADE", ondelete="CASCADE"), index=True)
    session_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("session.id", onupdate="CASCADE", ondelete="SET NULL"))
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

        Args:
            db (Session): The database session.

        Returns:
            sqlalchemy.sql.selectable.Subquery: Subquery for the latest device operations.
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
        Retrieves the last operations of a specific type (default "pobranie") for a user.

        Args:
            db (Session): The database session.
            user_id (int): ID of the user.
            operation_type (Literal["pobranie", "zwrot"], optional): Type of operation to filter by (default is 'pobranie').

        Returns:
            Sequence[DeviceOperation]: A sequence of the user's last device operations.

        Raises:
            HTTPException: If no operations are found for the user.
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
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No operations that match given criteria found"
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

        Args:
            db (Session): The database session.
            operation_data (schemas.DevOperation): Data for the new operation.
            commit (bool, optional): Whether to commit the operation to the database.

        Returns:
            DeviceOperation: The created DeviceOperation object.
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
                                    detail=f"An internal error occurred while creating operation")
        return new_operation

    @classmethod
    def get_all_operations(cls,
                           db: Session,
                           session_id: Optional[int] = None
                           ) -> List["DeviceOperation"]:
        """
        Retrieves all device operations from the database and
        it filters results by session Id if given.

        Args:
            db (Session): The database session.
            session_id (Optional[int]): The session Id to filter by
        Returns:
            List[DeviceOperation]: A list of all DeviceOperation objects.

        Raises:
            HTTPException: If no operations are found.
        """
        logger.info("Attempting to retrieve operations.")

        operations_query = db.query(DeviceOperation)
        if session_id:
            logger.debug(f"Filtering operations by session ID: {session_id}")
            operations_query.filter(DeviceOperation.session_id == session_id)
        operations = operations_query.all()
        if not operations:
            logger.warning(f"No operations found")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="There is no operation")
        logger.debug(
            f"Retrieved {len(operations)} operations that match given criteria.")
        return operations

    @classmethod
    def get_operation_id(cls,
                         db: Session,
                         operation_id: int) -> "DeviceOperation":
        """
        Retrieves a specific operation by its ID.

        Args:
            db (Session): The database session.
            operation_id (int): ID of the operation.

        Returns:
            DeviceOperation: The DeviceOperation object with the specified ID.

        Raises:
            HTTPException: If the operation does not exist.
        """
        logger.info(
            f"Attempting to retrieve operation with ID: {operation_id}")
        operation = db.query(DeviceOperation).filter(
            DeviceOperation.id == operation_id).first()
        if not operation:
            logger.warning(f"Operationwith ID {operation_id} not found")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Operation with id: {operation_id} doesn't exist")
        logger.debug(f"Retrieved operation: {operation}")
        return operation

    @classmethod
    def get_last_dev_operation_or_none(cls,
                                       db: Session,
                                       device_id: int) -> "DeviceOperation|None":
        """
        Retrieves the last operation for a device or returns None if no operation exists.

        Args:
            db (Session): The database session.
            device_id (int): ID of the device.

        Returns:
            DeviceOperation|None: The last DeviceOperation for the device, or None if no operations exist.
        """
        logger.info(
            f"Attempting to retrieve last operation for device with ID: {device_id}")
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
