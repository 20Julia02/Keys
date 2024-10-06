import datetime
from sqlalchemy.orm import Session
from app import models, schemas
from fastapi import HTTPException, status


class DeviceTransactionService:
    def __init__(self, db: Session):
        self.db = db

    def create_transaction(self, transaction_data: schemas.DeviceTransaction, commit: bool = True) -> schemas.DeviceTransactionOut:
        """
        Creates a new transaction in the database.

        Args:
            transaction (DeviceTransaction): The data required to create a new transaction.

        Returns:
            DeviceTransaction: The newly created transaction.
        """
        new_transaction = models.DeviceTransaction(**transaction_data)
        
        self.db.add(new_transaction)
        if commit:
            self.db.commit()
        return new_transaction

    def get_transaction_id(self, transaction_id: int) -> schemas.DeviceTransactionOut:
        transaction = self.db.query(models.DeviceTransaction).filter(models.DeviceTransaction.id == transaction_id).first()
        if not transaction:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Device with id: {transaction_id} doesn't exist")
        return transaction
