from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import relationship, mapped_column, Mapped, Session
from typing import Optional, Literal, List, TYPE_CHECKING
import datetime
from fastapi import HTTPException, status
from app.models.base import Base, intpk, timestamp
from app import schemas

if TYPE_CHECKING:
    from app.models.user import BaseUser, User
    from app.models.device import Device
    

SessionStatus = Literal["w trakcie", "potwierdzona", "odrzucona"]


class IssueReturnSession(Base):
    __tablename__ = "session"

    id: Mapped[intpk]
    user_id: Mapped[int] = mapped_column(ForeignKey("base_user.id"))
    concierge_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    start_time: Mapped[datetime.datetime]
    end_time: Mapped[Optional[datetime.datetime]]
    status: Mapped[SessionStatus]

    device_operations: Mapped[List["DeviceOperation"]] = relationship(back_populates="session")
    unapproved_operations: Mapped[List["UnapprovedOperation"]] = relationship(back_populates="session")
    user: Mapped["BaseUser"] = relationship(foreign_keys=[user_id], back_populates="sessions")
    concierge: Mapped["User"] = relationship(foreign_keys=[concierge_id], back_populates="sessions")


OperationType = Literal["pobranie", "zwrot"]


class UnapprovedOperation(Base):
    __tablename__ = "operation_unapproved"
    id: Mapped[intpk]
    device_id: Mapped[int] = mapped_column(ForeignKey("device.id"))
    session_id: Mapped[int] = mapped_column(ForeignKey("session.id"))
    operation_type: Mapped[OperationType]
    entitled: Mapped[bool]
    timestamp: Mapped[Optional[timestamp]]

    session: Mapped["IssueReturnSession"] = relationship(back_populates="unapproved_operations")
    device: Mapped["Device"] = relationship(back_populates="unapproved_operations")

    @classmethod
    def delete_if_rescanned(cls, db: Session, device_id: int, session_id: int) -> bool:
        operation_unapproved = db.query(UnapprovedOperation).filter(UnapprovedOperation.device_id == device_id,
                                                                    UnapprovedOperation.session_id == session_id).first()
        if operation_unapproved:
            db.delete(operation_unapproved)
            db.commit()
            return True
        return False
    
    @classmethod
    def create_unapproved_operation(cls,
                                    db: Session,
                                    operation_data: schemas.DeviceOperation,
                                    commit: bool = True) -> "DeviceOperation":
        """
        Creates a new operation in the database.

        Args:
            operation (DeviceOperation): The data required to create a new operation.

        Returns:
            DeviceOperation: The newly created operation.
        """
        new_operation = UnapprovedOperation(**operation_data)
        new_operation.timestamp = datetime.datetime.now()

        db.add(new_operation)
        if commit:
            db.commit()
            db.refresh(new_operation)
        return new_operation
    
    @classmethod
    def get_unapproved_session(cls, db: Session, session_id: int) -> List["UnapprovedOperation"]:
        unapproved = db.query(UnapprovedOperation).filter(UnapprovedOperation.session_id == session_id).all()
        if not unapproved:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No unapproved operations found for this session")
        return unapproved
    
    @classmethod
    def create_operation_from_unappproved(cls, db: Session, session_id: int, commit: bool = True)-> "DeviceOperation":
        unapproved_operations = cls.get_unapproved_session(db, session_id)
        operation_list = []
        for unapproved_operation in unapproved_operations:
            operation_data = {
                "device_id": unapproved_operation.device_id,
                "session_id": unapproved_operation.session_id,
                "operation_type": unapproved_operation.operation_type,
                "timestamp": unapproved_operation.timestamp,
                "entitled": unapproved_operation.entitled
            }
            new_operation = DeviceOperation(**operation_data)
            db.add(new_operation)
            db.flush()
            db.delete(unapproved_operation)

            validated_operation = schemas.DeviceOperationOut.model_validate(new_operation)
            operation_list.append(validated_operation)
        
        if commit:
            try:
                db.commit()
            except Exception as e:
                db.rollback()
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail=f"Error during operation transfer: {str(e)}")
        return operation_list

class DeviceOperation(Base):
    __tablename__ = "device_operation"

    id: Mapped[intpk]
    device_id: Mapped[int] = mapped_column(ForeignKey("device.id"))
    session_id: Mapped[Optional[int]] = mapped_column(ForeignKey("session.id"))
    operation_type: Mapped[OperationType]
    entitled: Mapped[bool]
    timestamp: Mapped[Optional[timestamp]]

    device: Mapped["Device"] = relationship(back_populates="device_operations")
    session: Mapped[Optional["IssueReturnSession"]] = relationship(back_populates="device_operations")

    @classmethod
    def last_operation_subquery(cls, db: Session):
        return (
            db.query(
                cls.device_id,
                func.max(cls.timestamp).label('last_operation_timestamp')
            )
            .group_by(cls.device_id)
            .subquery()
        )
    
    @classmethod
    def get_owned_by_user(cls, db: Session, user_id: int) -> List["DeviceOperation"]:
        last_operation_subquery = cls.last_operation_subquery(db)

        query = (
            db.query(cls)
            .join(last_operation_subquery,
                  (cls.device_id == last_operation_subquery.c.device_id) & 
                  (cls.timestamp == last_operation_subquery.c.last_operation_timestamp)
            )
            .join(IssueReturnSession, cls.session)
            .filter(IssueReturnSession.user_id == user_id)
            .filter(cls.operation_type == "pobranie")
            .order_by(cls.timestamp.asc())
        )

        operations = query.all()

        if not operations:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} doesn't have any devices"
            )

        return operations
    
    @classmethod
    def create_operation(cls,
                         db: Session,
                         operation_data: schemas.DeviceOperation,
                         commit: Optional[bool] = True) ->"DeviceOperation":
        
        """
        Creates a new operation in the database.

        Args:
            operation (DeviceOperation): The data required to create a new operation.

        Returns:
            DeviceOperation: The newly created operation.
        """
        new_operation = DeviceOperation(**operation_data)
        new_operation.timestamp = datetime.datetime.now()

        db.add(new_operation)
        if commit:
            db.commit()
            db.refresh(new_operation)
        return new_operation
    
    @classmethod
    def get_all_operations(cls, db: Session) -> List["DeviceOperation"]:
        operations = db.query(DeviceOperation).all()
        if not operations:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"There is no operation")
        return operations

    @classmethod
    def get_operation_id(cls, db, operation_id: int) -> "DeviceOperation":
        operation = db.query(DeviceOperation).filter(DeviceOperation.id == operation_id).first()
        if not operation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Operation with id: {operation_id} doesn't exist")
        return operation
    
    @classmethod
    def get_last_dev_operation_or_none(cls, db: Session,  device_id: int) -> "DeviceOperation":
        subquery = (
            db.query(func.max(DeviceOperation.timestamp))
            .filter(DeviceOperation.device_id == device_id)
            .subquery()
        )
        operation = (
            db.query(DeviceOperation)
            .filter(
                DeviceOperation.device_id == device_id,
                DeviceOperation.timestamp == subquery
            )
            .first()
        )
        return operation