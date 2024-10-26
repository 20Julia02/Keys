from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.orm import relationship, mapped_column, Mapped, Session
import enum
from typing import Optional, List, TYPE_CHECKING
import datetime
from fastapi import HTTPException, status
from app import schemas
from app.models.base import Base, intpk, timestamp


if TYPE_CHECKING:
    from app.models.operation import IssueReturnSession
    from app.models.permission import Permission


class BaseUser(Base):
    __tablename__ = "base_user"
    id: Mapped[intpk]
    user_type = Column(String(50))

    __mapper_args__ = {
        'polymorphic_on': user_type,
        'polymorphic_identity': 'base_user'
    }

    notes: Mapped[List["UserNote"]] = relationship(back_populates="user")
    sessions: Mapped[List["IssueReturnSession"]] = relationship(back_populates="user")


class UserRole(enum.Enum):
    admin = "admin"
    concierge = "concierge"
    employee = "employee"
    student = "student"
    guest = "guest"


class Faculty(enum.Enum):
    geodesy = "Geodezji i Kartografii"


class User(BaseUser):
    __tablename__ = 'user'
    id: Mapped[intpk] = mapped_column(ForeignKey('base_user.id'))
    name: Mapped[str] = mapped_column(String(50))
    surname: Mapped[str] = mapped_column(String(50))
    role: Mapped[UserRole]
    faculty: Mapped[Optional[Faculty]]
    photo_url: Mapped[Optional[str]]
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str]
    card_code: Mapped[str] = mapped_column(unique=True)

    __mapper_args__ = {
        'polymorphic_identity': 'user'
    }

    permissions: Mapped[List["Permission"]] = relationship(back_populates="user")
    sessions: Mapped[List["IssueReturnSession"]] = relationship(back_populates="concierge")


class UnauthorizedUser(BaseUser):
    __tablename__ = "unauthorized_user"
    id: Mapped[intpk] = mapped_column(ForeignKey('base_user.id'))
    name: Mapped[str] = mapped_column(String(50))
    surname: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(50), unique=True)
    added_at: Mapped[Optional[timestamp]]

    __mapper_args__ = {
        'polymorphic_identity': 'unauthorized_user'
    }



class UserNote(Base):
    __tablename__ = "user_note"

    id: Mapped[intpk]
    user_id: Mapped[int] = mapped_column(ForeignKey("base_user.id"))
    note: Mapped[str]
    timestamp: Mapped[Optional[timestamp]]

    user: Mapped["BaseUser"] = relationship(back_populates="notes")

    @classmethod
    def get_all_user_notes(cls, db: Session) -> List["UserNote"]:
        """Retrieve all user notes."""
        notes = db.query(UserNote).all()
        if not notes:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No user notes found.")
        return notes
    
    @classmethod
    def get_user_note_by_id(cls, db: Session, user_id: int) -> List["UserNote"]:
        """Retrieve a specific user note by user_id."""
        notes = (db.query(UserNote)
                 .filter(UserNote.user_id == user_id)
                 .order_by(UserNote.timestamp.asc())
                 .all())
        if not notes:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No note found for user id: {user_id}")
        return notes
    
    @classmethod
    def create_user_note(cls, db: Session, note_data: schemas.UserNoteCreate, commit: bool = True) -> "UserNote":
        """Create a new user note."""
        note_data_dict = note_data.model_dump()
        note_data_dict["timestamp"] = datetime.datetime.now()
        note = UserNote(**note_data_dict)
        db.add(note)
        if commit:
            try:
                db.commit()
                db.refresh(note)
            except Exception as e:
                db.rollback()
                raise e 
        return note

    @classmethod
    def update_user_note(cls, db: Session, note_id: int, note_data: schemas.NoteUpdate, commit: bool = True) -> "UserNote":

        note = db.query(UserNote).filter(UserNote.id == note_id).first()
        
        if not note:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Note with id {note_id} not found")

        note.note = note_data.note
        note.timestamp = datetime.datetime.now()

        if commit:
            try:
                db.commit()
                db.refresh(note)
            except Exception as e:
                db.rollback()
                raise e 

        return note