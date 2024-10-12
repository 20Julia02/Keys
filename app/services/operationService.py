import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from app import models, schemas
from fastapi import HTTPException, status
from typing import List


class DeviceOperationService:
    def __init__(self, db: Session):
        self.db = db

    def create_operation(self,
                         operation_data: schemas.DeviceOperation,
                         commit: bool = True) -> schemas.DeviceOperationOut:
        """
        Creates a new operation in the database.

        Args:
            operation (DeviceOperation): The data required to create a new operation.

        Returns:
            DeviceOperation: The newly created operation.
        """
        new_operation = models.DeviceOperation(**operation_data)
        new_operation.timestamp = datetime.datetime.now()

        self.db.add(new_operation)
        if commit:
            self.db.commit()
            self.db.refresh(new_operation)
        return new_operation
    
    def get_all_operations(self) -> List[models.DeviceOperation]:
        operations = self.db.query(models.DeviceOperation).all()
        if not operations:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"There is no operation")
        return operations

    def get_operation_id(self, operation_id: int) -> models.DeviceOperation:
        operation = self.db.query(models.DeviceOperation).filter(models.DeviceOperation.id == operation_id).first()
        if not operation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Operation with id: {operation_id} doesn't exist")
        return operation
    
    def get_last_dev_operation_or_none(self, device_id: int) -> models.DeviceOperation:
        subquery = (
            self.db.query(func.max(models.DeviceOperation.timestamp))
            .filter(models.DeviceOperation.device_id == device_id)
            .subquery()
        )
        operation = (
            self.db.query(models.DeviceOperation)
            .filter(
                models.DeviceOperation.device_id == device_id,
                models.DeviceOperation.timestamp == subquery
            )
            .first()
        )
        return operation
        
class UnapprovedOperationService():
    def __init__(self, db: Session):
        self.db = db

    def delete_if_rescanned(self, device_id: int, session_id: int):
        operation_unapproved = self.db.query(models.UnapprovedOperation).filter(models.UnapprovedOperation.device_id == device_id,
                                                                       models.UnapprovedOperation.session_id == session_id).first()
        if operation_unapproved:
            self.db.delete(operation_unapproved)
            self.db.commit()
            return True
        return False
    
    def create_unapproved_operation(self,
                         operation_data: schemas.DeviceOperation,
                         commit: bool = True) -> schemas.DeviceOperationOut:
        """
        Creates a new operation in the database.

        Args:
            operation (DeviceOperation): The data required to create a new operation.

        Returns:
            DeviceOperation: The newly created operation.
        """
        new_operation = models.UnapprovedOperation(**operation_data)
        new_operation.timestamp = datetime.datetime.now()

        self.db.add(new_operation)
        if commit:
            self.db.commit()
            self.db.refresh(new_operation)
        return new_operation
    
    def get_unapproved_session(self, session_id: int) -> List[models.UnapprovedOperation]:
        unapproved = self.db.query(models.UnapprovedOperation).filter(models.UnapprovedOperation.session_id == session_id).all()
        if not unapproved:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No unapproved operations found for this session")
        return unapproved
    

    def create_operation_from_unappproved(self, session_id: int, commit: bool = True)-> schemas.DeviceOperationOut:
        unapproved_operations = self.get_unapproved_session(session_id)
        operation_list = []
        for unapproved_operation in unapproved_operations:
            operation_data = {
                "device_id": unapproved_operation.device_id,
                "session_id": unapproved_operation.session_id,
                "operation_type": unapproved_operation.operation_type,
                "timestamp": unapproved_operation.timestamp,
                "entitled": unapproved_operation.entitled
            }
            new_operation = models.DeviceOperation(**operation_data)
            self.db.add(new_operation)
            self.db.flush()
            self.db.delete(unapproved_operation)

            validated_operation = schemas.DeviceOperationOut.model_validate(new_operation)
            operation_list.append(validated_operation)
        
        if commit:
            try:
                self.db.commit()
            except Exception as e:
                self.db.rollback()
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail=f"Error during operation transfer: {str(e)}")
        return operation_list
