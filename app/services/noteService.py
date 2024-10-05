import datetime
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

    def create_user_note(self, note_data: schemas.UserNote):
        """Create a new user note."""
        note_data = models.UserNote(**note_data)
        self.db.add(note_data)
        self.db.commit()
        self.db.refresh(note_data)
        return note_data

    def get_dev_notes(self, dev_code=Optional[str], activity_id=Optional[int]):
        """Retrieve all operation notes."""
        query = self.db.query(models.DeviceNote)
        if dev_code:
            query = query.filter(models.DeviceNote.device_code.ilike(f"%{dev_code}%"))
        if activity_id:
            query = query.filter(models.DeviceNote.activity_id.ilike(f"%{activity_id}%"))

        notes = query.all()

        if not notes:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                                detail="There are no notes that match the given criteria")
        
        return notes

    def create_dev_note(self, note_data: schemas.DeviceNote):
        """Create a new operation note."""
        note_data = models.DeviceNote(**note_data)
        self.db.add(note_data)
        self.db.commit()
        self.db.refresh(note_data)
        return note_data