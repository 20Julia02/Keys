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
        note_data = models.UserNote(**note_data)
        self.db.add(note_data)
        if commit:
            self.db.commit()
        return note_data

    def get_dev_notes(self, dev_code=Optional[str], issue_return_session_id=Optional[int]):
        """Retrieve all operation notes."""
        query = self.db.query(models.DeviceNote)
        if dev_code:
            query = query.filter(models.DeviceNote.device_code.ilike(f"%{dev_code}%"))
        if issue_return_session_id:
            query = query.filter(models.DeviceNote.issue_return_session_id.ilike(f"%{issue_return_session_id}%"))

        notes = query.all()

        if not notes:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="There are no notes that match the given criteria")

        return notes

    def create_dev_note(self, note_data: schemas.DeviceNote, commit: bool = True):
        """Create a new operation note."""
        note_data = models.DeviceNote(**note_data)
        self.db.add(note_data)
        if commit:
            self.db.commit()
        return note_data
