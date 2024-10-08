from sqlalchemy.orm import Session
from app import models, schemas
from fastapi import HTTPException, status


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

        self.db.add(new_operation)
        if commit:
            self.db.commit()
            self.db.refresh(new_operation)
        return new_operation

    def get_operation_id(self, operation_id: int) -> schemas.DeviceOperationOut:
        operation = self.db.query(models.DeviceOperation).filter(models.DeviceOperation.id == operation_id).first()
        if not operation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Device with id: {operation_id} doesn't exist")
        return operation
