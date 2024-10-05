import datetime
from app.schemas import Operation, OperationOut
from sqlalchemy.orm import Session
from app import models
from fastapi import HTTPException, status


class OperationService:
    def __init__(self, db: Session):
        self.db = db

    # def create_operation(self, dev_code: str, activity_id: int, entitled: bool, operation_type: str) -> OperationOut:
    #     """
    #     Creates a new operation in the database.

    #     Args:
    #         operation (Operation): The data required to create a new operation.

    #     Returns:
    #         Operation: The newly created operation.
    #     """
    #     operation_data = {
    #         "device_code": dev_code,
    #         "activity_id": activity_id,
    #         "entitled": entitled,
    #         "time": datetime.datetime.now(datetime.timezone.utc),
    #         "operation_type": operation_type
    #     }

    #     new_operation = models.Operation(**operation_data)
        
    #     self.db.add(new_operation)
    #     self.db.commit()
    #     self.db.refresh(new_operation)

    #     return  OperationOut.model_validate(new_operation)

    # def get_operation_id(self, operation_id: int):
    #     operation = self.db.query(models.Operation).filter(models.Operation.id == operation_id).first()
    #     if not operation:
    #         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
    #                             detail=f"Device with id: {operation_id} doesn't exist")
    #     return operation
