import datetime
from fastapi import status, HTTPException
from app import models
from sqlalchemy.orm import Session


class NoteService:
    """Service for handling user and operation notes in the database."""

    def __init__(self, db: Session):
        self.db = db

    def get_all_user_notes(self):
        """Retrieve all user notes."""
        notes = self.db.query(models.UserNote).all()
        if not notes:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No user notes found.")
        return notes

    def get_user_note_by_id(self, user_id: int):
        """Retrieve a specific user note by user_id."""
        notes = self.db.query(models.UserNote).filter(models.UserNote.user_id == user_id).all()
        if not notes:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No note found for user id: {user_id}")
        return notes

    def create_user_note(self, user_id: int, note_text: str):
        """Create a new user note."""
        note_data = models.UserNote(
            user_id=user_id,
            note=note_text,
            time=datetime.datetime.now(datetime.timezone.utc)
        )
        self.db.add(note_data)
        self.db.commit()
        self.db.refresh(note_data)
        return note_data

    def get_all_operation_notes(self):
        """Retrieve all operation notes."""
        notes = self.db.query(models.OperationNote).all()
        if not notes:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No operation notes found.")
        return notes

    def get_operation_note_by_id(self, operation_id: int):
        """Retrieve a specific operation note by operation_id."""
        notes = self.db.query(models.OperationNote).filter(models.OperationNote.operation_id == operation_id).all()
        if not notes:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No note found for operation id: {operation_id}")
        return notes
    
    def get_dev_notes_by_code(self, dev_code: str):
        operation_ids_subquery = self.db.query(models.Operation.id).filter(models.Operation.device_code == dev_code)
        notes = self.db.query(models.OperationNote).filter(models.OperationNote.operation_id.in_(operation_ids_subquery)).all()
        if not notes:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No note found for device id: {dev_code}")
        return notes

    def create_operation_note(self, operation_id: int, note_text: str):
        """Create a new operation note."""
        note_data = models.OperationNote(
            operation_id=operation_id,
            note=note_text,
            time=datetime.datetime.now(datetime.timezone.utc)
        )
        self.db.add(note_data)
        self.db.commit()
        self.db.refresh(note_data)
        return note_data