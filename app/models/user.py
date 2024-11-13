from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import relationship, mapped_column, Mapped, Session
import enum
from typing import Optional, List, TYPE_CHECKING, Any, Tuple
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
    photo_url: Mapped[Optional[str]] = mapped_column(unique=True)
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
    def get_all_users(cls,
                      db: Session) -> List["User"]:
        """
        Retrieves all users from the database.
        If no users are found, raises an exception.

        Args:
            db (Session): Database session used for executing the query.

        Returns:
            List[User]: List of all users in the database.

        Raises:
            HTTPException: Raises a 404 error if no users are found with the message "There is no user in database".
        """
        user = db.query(User).all()
        if (not user):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="There is no user in the database")
        return user

    @classmethod
    def get_user_id(cls,
                    db: Session,
                    user_id: int) -> "User":
        """
        Retrieves a user by their ID from the database.
        Raises an exception if the user is not found.

        Args:
            db (Session): Database session used for executing the query.
            user_id (int): ID of the user to retrieve.

        Returns:
            User: The user object with the specified ID.

        Raises:
            HTTPException: Raises a 404 error if the user is not found.
        """
        user = db.query(User).filter(User.id == user_id).first()
        if (not user):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"User with id: {user_id} doesn't exist")
        return user
    
    @classmethod
    def create_user(cls,
                    db: Session,
                    user_data: schemas.UserCreate,
                    commit: bool = True)-> "User":
        """
        Creates a new user in the database.

        Args:
            db (Session): Database session used for executing the operation.
            user_data (schemas.UserCreate): Data for creating the new user.
            commit (bool, optional): Whether to commit the transaction after adding the user. Default is True.

        Returns:
            User: The newly created user object.
        """
        new_user = cls(**user_data.model_dump())
        db.add(new_user)
        if commit:
            try:
                db.commit()
                db.refresh(new_user)
            except Exception as e:
                db.rollback()
                raise e
        return new_user
    
    @classmethod
    def delete_user(cls,
                    db: Session,
                    user_id: int,
                    commit: bool = True)-> bool:
        """
        Deletes a user by their ID from the database.
        Raises an exception if the user is not found.

        Args:
            db (Session): Database session used for executing the operation.
            user_id (int): ID of the user to delete.
            commit (bool, optional): Whether to commit the transaction after adding the user. Default is True.

        Returns:
            bool: True if the user was successfully deleted.

        Raises:
            HTTPException: Raises a 404 error if the user is not found.
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"User with id: {user_id} doesn't exist")
        db.delete(user)
        if commit:
            try:
                db.commit()
            except Exception as e:
                db.rollback()
                raise e
        return True
    
    @classmethod
    def update_user(cls,
                    db: Session,
                    user_id: int,
                    user_data: schemas.UserCreate,
                    commit: bool = True)->"User":
        """
        Updates a user's information in the database.

        Args:
            db (Session): Database session used for executing the operation.
            user_id (int): ID of the user to update.
            user_data (schemas.UserCreate): Updated data for the user.
            commit (bool, optional): Whether to commit the transaction after updating the user. Default is True.

        Returns:
            User: The updated user object.

        Raises:
            HTTPException: Raises a 404 error if the user is not found.
            Exception: For any other issues during the commit.
        """
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"User with id {user_id} not found")
        user.name = user_data.name
        user.surname = user_data.surname
        user.email = user_data.email
        user.card_code = user_data.card_code
        user.role = UserRole(user_data.role)
        user.faculty = Faculty(user_data.faculty)
        user.photo_url = user_data.photo_url
        user.password = user_data.password

        if commit:
            try:
                db.commit()
                db.refresh(user)
            except Exception as e:
                db.rollback()
                raise e

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
    def create_or_get_unauthorized_user(cls,
                                        db: Session,
                                        name: str,
                                        surname: str,
                                        email: str,
                                        commit: bool = True) -> Tuple["UnauthorizedUser", bool]:
        """
        Checks whether an unauthorised user with a given email exists in the database.
        If so and his name and surname matches those in the database it returns an existing user, 
        if the email was not in the database it creates a new user. If the email address was registered 
        and the user provides a different first and last name than in the database, the method raises an error.

        Returns the user and a Boolean value indicating whether the user is new.

        Args:
            db (Session): Database session used for executing the query.
            name (str): First name of the user.
            surname (str): Last name of the user.
            email (str): Email address of the user.
            commit (bool, optional): Whether to commit the transaction after adding the user. Default is True.

        Returns:
            Tuple[UnauthorizedUser, bool]: Tuple containing the user object and a boolean indicating if the user is newly created.

        Raises:
            HTTPException: Raises a 403 error if an email conflict occurs with different name or surname.
        """
        existing_user = db.query(
            UnauthorizedUser).filter_by(email=email).first()

        if existing_user:
            if existing_user.name != name or existing_user.surname != surname:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "message": "User with this email already exists but with a different name or surname.",
                        "user": {
                            "id": existing_user.id,
                            "name": existing_user.name,
                            "surname": existing_user.surname,
                            "email": existing_user.email
                        }
                    }
                )
            return existing_user, False

        new_user = UnauthorizedUser(
            name=name,
            surname=surname,
            email=email
        )
        db.add(new_user)
        if commit:
            try:
                db.commit()
                db.refresh(new_user)
            except Exception as e:
                db.rollback()
                raise e
        return new_user, True

    @classmethod
    def get_all_unathorized_users(cls,
                                  db: Session) -> List["UnauthorizedUser"]:
        """
        Retrieves all unauthorized users from the database.
        Raises an exception if no users are found.

        Args:
            db (Session): Database session used for executing the query.

        Returns:
            List[UnauthorizedUser]: List of all unauthorized users in the database.

        Raises:
            HTTPException: Raises a 404 error if no unauthorized users are found with a relevant message.
        """
        user = db.query(UnauthorizedUser).all()
        if (not user):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="There is no unauthorized user in database")
        return user

    @classmethod
    def get_unathorized_user(cls,
                             db: Session,
                             user_id: int) -> "UnauthorizedUser":
        """
        Retrieves an unauthorized user by their ID.
        Raises an exception if the user is not found.

        Args:
            db (Session): Database session used for executing the query.
            user_id (int): ID of the unauthorized user to retrieve.

        Returns:
            UnauthorizedUser: The unauthorized user object with the specified ID.

        Raises:
            HTTPException: Raises a 404 error if the unauthorized user is not found.
        """
        user = db.query(UnauthorizedUser).filter(
            UnauthorizedUser.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Unauthorized user with id: {user_id} doesn't exist")
        return user
    
    @classmethod
    def update_unauthorized_user(cls,
                                 db: Session,
                                 user_id: int,
                                 user_data: schemas.UnauthorizedUser,
                                 commit: bool = True) -> "UnauthorizedUser":
        """
        Updates an unauthorized user's information in the database.

        Args:
            db (Session): Database session used for executing the operation.
            user_id (int): ID of the unauthorized user to update.
            user_data (schemas.UnauthorizedUser): New data for updating the user.
            commit (Optional[bool]): Whether to commit the transaction after updating the user. Default is True.

        Returns:
            UnauthorizedUser: The updated unauthorized user object.

        Raises:
            HTTPException: Raises a 404 error if the unauthorized user is not found.
            Exception: For any other issues during the commit.
        """
        user = db.query(UnauthorizedUser).filter(UnauthorizedUser.id == user_id).first()

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Unauthorized user with id {user_id} not found")

        user.name = user_data.name
        user.surname = user_data.surname
        user.email = user_data.email

        if commit:
            try:
                db.commit()
                db.refresh(user)
            except Exception as e:
                db.rollback()
                raise e

        return user

    @classmethod
    def delete_unauthorized_user(cls,
                                 db: Session,
                                 user_id: int,
                                 commit: bool = True)-> bool:
        """
        Deletes an unauthorized user by their ID from the database.
        Raises an exception if the user is not found.

        Args:
            db (Session): Database session used for executing the operation.
            user_id (int): ID of the unauthorized user to delete.
            commit (Optional[bool]): Whether to commit the transaction after deleting the user. Default is True.

        Returns:
            bool: `True` if the user was successfully deleted.

        Raises:
            HTTPException: Raises a 404 error if the user is not found.
        """

        user = db.query(UnauthorizedUser).filter(
            UnauthorizedUser.id == user_id).first()

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Unauthorized user with id: {user_id} doesn't exist")

        db.delete(user)
        if commit:
            try:
                db.commit()
            except Exception as e:
                db.rollback()
                raise e
        return True


class UserNote(Base):
    __tablename__ = "user_note"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("base_user.id"))
    note: Mapped[str]
    timestamp: Mapped[Optional[timestamp]]

    user: Mapped["BaseUser"] = relationship(back_populates="notes")

    @classmethod
    def get_user_notes_filter(cls,
                              db: Session,
                              user_id: Optional[int] = None) -> List["UserNote"]:
        """
        Retrieves user notes filtered by user ID if provided.
        Raises an exception if no notes are found.

        Args:
            db (Session): Database session used for executing the query.
            user_id (Optional[int]): ID of the user to filter notes. Default is `None`.

        Returns:
            List[UserNote]: List of user notes matching the filter criteria.

        Raises:
            HTTPException: Raises a 404 error if no user notes are found.
        """
        notes = db.query(UserNote)
        if user_id:
            notes = notes.filter(UserNote.user_id == user_id)
        notes = notes.all()
        if not notes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="No user notes found.")
        return notes

    @classmethod
    def get_user_note_id(cls,
                         db: Session,
                         note_id: int) -> "UserNote":
        """
        Retrieves a user note by its ID.
        Raises an exception if the note is not found.

        Args:
            db (Session): Database session used for executing the query.
            note_id (intl): ID of the note to retrieve.

        Returns:
            UserNote: The user note with the specified ID.

        Raises:
            HTTPException: Raises a 404 error if the note is not found.
        """
        note = db.query(UserNote).filter(UserNote.id == note_id).first()
        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"There is no user notes with id {note_id}.")
        return note

    @classmethod
    def create_user_note(cls,
                         db: Session,
                         note_data: schemas.UserNoteCreate,
                         commit: bool = True) -> "UserNote":
        """
        Creates a new user note with the specified data and saves it to the database.
        Commits and refreshes the note if `commit` is `True`.

        Args:
            db (Session): Database session used for executing the operation.
            note_data (schemas.UserNoteCreate): Data for creating a new user note.
            commit (optional[bool]): Whether to commit the transaction after adding the note. Default is `True`.

        Returns:
            UserNote: The newly created user note.

        Raises:
            ValueError: If the note text is empty.
            Exception: For any other issues during the commit.
        """
        if not note_data.note:
            raise ValueError("Note cannot be empty")
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
    def update_user_note(cls,
                         db: Session,
                         note_id: int,
                         note_data: schemas.NoteUpdate,
                         commit: bool = True) -> "UserNote":
        """
        Updates a user note by ID with new data, or deletes it if note content is `None`.
        Commits and refreshes the note if `commit` is `True`.

        Args:
            db (Session): Database session used for executing the operation.
            note_id (int): ID of the note to update.
            note_data (schemas.NoteUpdate): New data for updating the note.
            commit (optional[bool]): Whether to commit the transaction after updating the note. Default is `True`.

        Returns:
            UserNote: The updated user note.

        Raises:
            HTTPException: Raises a 404 error if the note is not found, or 204 if the note is deleted.
            Exception: For any issues during the commit.
        """
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
                         note_id: int,
                         commit: Optional[bool] = True) -> bool:
        """
        Deletes a user note by its ID.
        Raises an exception if the note is not found.

        Args:
            db (Session): Database session used for executing the operation.
            note_id (int): ID of the note to delete.
            commit (optional[bool]): Whether to commit the transaction after deleting the note. Default is `True`.

        Returns:
            bool: `True` if the note was successfully deleted.

        Raises:
            HTTPException: Raises a 404 error if the note is not found.
            Exception: For any issues during the commit.
        """
        note = db.query(UserNote).filter(UserNote.id == note_id).first()
        if not note:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Note with id: {note_id} doesn't exist")
        db.delete(note)
        if commit:
            try:
                db.commit()
            except Exception as e:
                db.rollback()
                raise e
        return True
