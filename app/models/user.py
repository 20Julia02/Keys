from sqlalchemy import ForeignKey, String, Integer
from sqlalchemy.orm import relationship, mapped_column, Mapped, Session
import enum
from typing import Optional, List, TYPE_CHECKING, Any
import datetime
from fastapi import HTTPException, status
from app import schemas
from app.models.base import Base, timestamp


if TYPE_CHECKING:
    from app.models.operation import UserSession
    from app.models.permission import Permission


class BaseUser(Base):
    __tablename__ = "base_user"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_type: Mapped[str] = mapped_column(String(50))

    __mapper_args__: dict[str, Any] = {
        'polymorphic_on': user_type,
        'polymorphic_identity': 'base_user'
    }

    notes: Mapped[List["UserNote"]] = relationship(back_populates="user")
    sessions: Mapped[List["UserSession"]] = relationship(back_populates="user")


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
    id: Mapped[int] = mapped_column(ForeignKey(
        'base_user.id'), primary_key=True)
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

    permissions: Mapped[List["Permission"]
                        ] = relationship(back_populates="user")
    sessions: Mapped[List["UserSession"]] = relationship(
        back_populates="concierge")

    @classmethod
    def get_all_users(cls, db: Session) -> List["User"]:
        user = db.query(User).all()
        if (not user):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="There is no user in database")
        return user

    @classmethod
    def get_user_id(cls, db: Session, user_id: int) -> "User":
        user = db.query(User).filter(User.id == user_id).first()
        if (not user):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"User with id: {user_id} doesn't exist")
        return user


class UnauthorizedUser(BaseUser):
    __tablename__ = "unauthorized_user"
    id: Mapped[int] = mapped_column(ForeignKey(
        'base_user.id'), primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    surname: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(50), unique=True)
    added_at: Mapped[Optional[timestamp]]

    __mapper_args__ = {
        'polymorphic_identity': 'unauthorized_user'
    }

    @classmethod
    def create_or_get_unauthorized_user(cls, db: Session, name: str, surname: str, email: str) -> "UnauthorizedUser":
        """
        Creates a new unauthorized user in the database.
        """

        existing_user = db.query(UnauthorizedUser).filter_by(
            email=email).first()

        if existing_user:
            if existing_user.name != name or existing_user.surname != surname:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                    detail="User with this email already exists but with different name or surname.")
            return existing_user
        new_user = UnauthorizedUser(
            name=name,
            surname=surname,
            email=email
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    @classmethod
    def get_all_unathorized_users(cls, db: Session) -> List["UnauthorizedUser"]:
        """
        Retrieves all unathorized users from the database.
        """
        user = db.query(UnauthorizedUser).all()
        if (not user):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="There is no unauthorized user in database")
        return user

    @classmethod
    def get_unathorized_user(cls, db: Session, user_id: int) -> "UnauthorizedUser":
        """
        Retrieves an unauthorized user by their ID from the database.
        """
        user = db.query(UnauthorizedUser).filter(
            UnauthorizedUser.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Unauthorized user with id: {user_id} doesn't exist")
        return user

    @classmethod
    def delete_unauthorized_user(cls, db: Session, user_id: int):
        """
        Deletes an unauthorized user by their ID from the database.
        """
        user = db.query(UnauthorizedUser).filter(
            UnauthorizedUser.id == user_id).first()

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Unauthorized user with id: {user_id} doesn't exist")

        db.delete(user)
        db.commit()

        return True


class UserNote(Base):
    __tablename__ = "user_note"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("base_user.id"))
    note: Mapped[str]
    timestamp: Mapped[Optional[timestamp]]

    user: Mapped["BaseUser"] = relationship(back_populates="notes")

    @classmethod
    def get_all_user_notes(cls, db: Session) -> List["UserNote"]:
        """Retrieve all user notes."""
        notes = db.query(UserNote).all()
        if not notes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="No user notes found.")
        return notes

    @classmethod
    def get_user_note_by_id(cls, db: Session, user_id: int) -> List["UserNote"]:
        """Retrieve a specific user note by user_id."""
        notes = (db.query(UserNote)
                 .filter(UserNote.user_id == user_id)
                 .order_by(UserNote.timestamp.asc())
                 .all())
        if not notes:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"No note found for user id: {user_id}")
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
        if note_data.note is None:
            cls.delete_user_note(db, note_id)
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT, detail="Note deleted")
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

    @classmethod
    def delete_user_note(cls,
                         db: Session,
                         note_id: int):
        note = db.query(UserNote).filter(UserNote.id == note_id).first()
        if not note:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Note with id: {note_id} doesn't exist")
        db.delete(note)
        db.commit()
