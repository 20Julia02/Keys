import datetime
from fastapi import status, HTTPException
from app import models, schemas
from sqlalchemy.orm import Session
from typing import Optional, List


class NoteService:
    """Service for handling user and operation notes in the database."""

    def __init__(self, db: Session):
        self.db = db

    def get_all_user_notes(self) -> List[models.UserNote]:
        """Retrieve all user notes."""
        notes = self.db.query(models.UserNote).all()
        if not notes:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No user notes found.")
        return notes

    def get_user_note_by_id(self, user_id: int) -> models.UserNote:
        """Retrieve a specific user note by user_id."""
        notes = self.db.query(models.UserNote).filter(models.UserNote.user_id == user_id).all()
        if not notes:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No note found for user id: {user_id}")
        return notes

    def create_user_note(self, note_data: schemas.UserNoteCreate, commit: bool = True) -> models.UserNote:
        """Create a new user note."""
        note_data_dict = note_data.model_dump()
        note_data_dict["timestamp"] = datetime.datetime.now()
        note = models.UserNote(**note_data_dict)
        self.db.add(note)
        if commit:
            try:
                self.db.commit()
                self.db.refresh(note)
            except Exception as e:
                self.db.rollback()
                raise e 
        return note
    
    def get_dev_notes(self) -> List[models.DeviceNote]:
        notes = self.db.query(models.DeviceNote).all()
        if not notes:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="There are no device notes in database")

        return notes

    def get_dev_notes_id(self, dev_id: int) -> models.DeviceNote:
        """Retrieve all device notes filtered by device ID or issue/return session ID."""
        notes = self.db.query(models.DeviceNote).filter(models.DeviceNote.device_id == dev_id).all()

        if not notes:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="There are no notes that match the given criteria")
        return notes

    def create_dev_note(self, note_data: schemas.DeviceNote, commit: bool = True) -> models.DeviceNote:
        """Create a new device note."""
        note_data_dict = note_data.model_dump()
        note_data_dict["timestamp"] = datetime.datetime.now()
        note = models.DeviceNote(**note_data_dict)
        self.db.add(note)
        if commit:
            try:
                self.db.commit()
                self.db.refresh(note)
            except Exception as e:
                self.db.rollback()
                raise e 
        return note
