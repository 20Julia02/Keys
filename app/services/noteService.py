from fastapi import status, HTTPException
from app import models, schemas
from sqlalchemy.orm import Session
from typing import Optional


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

    def create_user_note(self, note_data: schemas.UserNote, commit: bool = True):
        """Create a new user note."""
        note_data = models.UserNote(**note_data.model_dump())
        self.db.add(note_data)
        if commit:
            self.db.commit()
            self.db.refresh(note_data)
        return note_data
    
    def get_dev_notes(self):
        notes = self.db.query(models.DeviceNote).all()
        if not notes:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="There are no device notes in database")

        return notes

    def get_dev_notes_id(self, dev_id: int, issue_return_session_id: Optional[int] = None):
        """Retrieve all device notes filtered by device ID or issue/return session ID."""
        query_note = self.db.query(models.DeviceNote).join(models.DeviceOperation)
        if dev_id is not None:
            query_note = query_note.filter(models.DeviceOperation.device_id == dev_id)
        notes = query_note.all()
        results = []
        for note in notes:
            note_data = {
                "note": note.note,
                "device_operation_id": note.device_operation_id,
                "operation_user_id": note.operation_user_id,
                "note_device": note.note_device
            }
            results.append(note_data)

        if not results:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="There are no notes that match the given criteria")
        return results

    def create_dev_note(self, note_data: schemas.DeviceNote, commit: bool = True):
        """Create a new operation note."""
        note_data = models.DeviceNote(**note_data.model_dump())
        self.db.add(note_data)
        if commit:
            self.db.commit()
            self.db.refresh(note_data)
        return note_data
