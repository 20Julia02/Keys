from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import relationship, mapped_column, Mapped, Session
import enum
from typing import Optional, List, TYPE_CHECKING, Any, Tuple
import datetime
from fastapi import HTTPException, status
from app import schemas
from app.models.base import Base, timestamp
from sqlalchemy import Enum as SAEnum
from app.config import logger
from app.models.base import get_enum_values


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
    admin = ("administrator", 1)
    concierge = ("portier", 2)
    employee = ("pracownik", 3)
    student = ("student", 4)
    guest = ("gość", 5)

    def __init__(self, value: str, weight: int):
        self._value_ = value
        self.weight = weight


class Faculty(enum.Enum):
    geodesy = "Geodezji i Kartografii"


class User(BaseUser):
    __tablename__ = 'user'
    id: Mapped[int] = mapped_column(ForeignKey(
        'base_user.id'), primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    surname: Mapped[str] = mapped_column(String(50))
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, values_callable=get_enum_values))
    faculty: Mapped[Optional[Faculty]] = mapped_column(
        SAEnum(Faculty, values_callable=get_enum_values))
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

        If no users are found, an HTTPException is raised.

        Args:
            db (Session): The database session used to execute the query.

        Returns:
            List[User]: A list of all users in the database.

        Raises:
            HTTPException: 
                - 204 No Content: If no users are found in the database.
        """

        logger.info("Fetching users from the database.")
        users = db.query(User).all()
        if (not users):
            logger.warning(f"No users found")
            raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)
        logger.debug(
            f"Retrieved {len(users)} users that match given criteria.")
        return users

    @classmethod
    def get_user_id(cls,
                    db: Session,
                    user_id: int) -> "User":
        """
        Retrieves a user by their ID from the database.

        Args:
            db (Session): The database session used to execute the query.
            user_id (int): The ID of the user to retrieve.

        Returns:
            User: The user object with the specified ID.

        Raises:
            HTTPException: 
                - 204 No Content: If no user with the given ID exists in the database.
        """
        logger.info(f"Attempting to retrieve user with ID: {user_id}")
        user = db.query(User).filter(User.id == user_id).first()
        if (not user):
            logger.warning(
                f"User with ID {user_id} not found")
            raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)
        logger.debug(f"User retrieved")
        return user

    @classmethod
    def create_user(cls,
                    db: Session,
                    user_data: schemas.UserCreate,
                    commit: bool = True) -> "User":
        """
        Creates a new user in the database.

        Commits the transaction unless specified otherwise.

        Args:
            db (Session): The database session used to execute the operation.
            user_data (schemas.UserCreate): The data required to create a new user.
            commit (bool, optional): Whether to commit the transaction immediately. Default is True.

        Returns:
            User: The newly created user object.

        Raises:
            HTTPException: 
                - 500 Internal Server Error: If an error occurs during the commit process.
        """
        from app.services.securityService import PasswordService
        logger.info("Creating a new user")
        logger.debug(f"User data provided: {user_data}")

        user_data.password = PasswordService().hash_password(user_data.password)
        new_user = cls(**user_data.model_dump())
        db.add(new_user)
        if commit:
            try:
                db.commit()
                logger.info("User created and committed to the database.")
            except Exception as e:
                db.rollback()
                logger.error(
                    f"Error while creating user: {e}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail="An internal error occurred while creating user")
        return new_user

    @classmethod
    def delete_user(cls,
                    db: Session,
                    user_id: int,
                    commit: bool = True) -> bool:
        """
        Deletes a user by their ID from the database.

        Commits the transaction unless specified otherwise.

        Args:
            db (Session): The database session used to execute the operation.
            user_id (int): The ID of the user to delete.
            commit (bool, optional): Whether to commit the transaction immediately. Default is True.

        Returns:
            bool: True if the user was successfully deleted.

        Raises:
            HTTPException: 
                - 404 Not Found: If no user with the given ID exists in the database.
                - 500 Internal Server Error: If an error occurs during the commit process.
        """

        logger.info(f"Attempting to delete user with ID: {user_id}")

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"User with ID {user_id} not found")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="User doesn't exist")
        db.delete(user)
        if commit:
            try:
                db.commit()
                logger.info(f"User with ID: {user_id} deleted successfully.")
            except Exception as e:
                logger.error(
                    f"Error while deleting user with ID {user_id}: {e}")
                db.rollback()
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail="An internal error occurred while deleting user")
        return True

    @classmethod
    def update_user(cls,
                    db: Session,
                    user_id: int,
                    user_data: schemas.UserCreate,
                    commit: bool = True) -> "User":
        """
        Updates a user's information in the database.

        Commits the transaction unless specified otherwise.

        Args:
            db (Session): The database session used to execute the operation.
            user_id (int): The ID of the user to update.
            user_data (schemas.UserCreate): The updated data for the user.
            commit (bool, optional): Whether to commit the transaction immediately. Default is True.

        Returns:
            User: The updated user object.

        Raises:
            HTTPException: 
                - 404 Not Found: If no user with the given ID exists in the database.
                - 500 Internal Server Error: If an error occurs during the commit process.
        """
        from app.services.securityService import PasswordService
        logger.info(f"Attempting to update user with ID: {user_id}")
        logger.debug(f"New user data: {user_data}")
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            logger.warning(f"User with ID {user_id} not found")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="User not found")
        
        user_data.password = PasswordService().hash_password(user_data.password)
        for key, value in user_data.model_dump().items():
            setattr(user, key, value)

        if commit:
            try:
                db.commit()
                logger.info(f"User with ID {user_id} updated successfully.")
            except Exception as e:
                logger.error(
                    f"Error while updating user with ID {user_id}: {e}")
                db.rollback()
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail="An internal error occurred while updating user")
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
        Checks if an unauthorized user with the given email exists in the database.

        If a user with the email exists and their name and surname match the provided values, 
        the existing user is returned. If the email exists but the name or surname differ, 
        an HTTPException is raised. If the email does not exist in the database, a new user is created.

        Commits the transaction unless specified otherwise.

        Args:
            db (Session): The database session used to execute the operation.
            name (str): The first name of the unauthorized user.
            surname (str): The last name of the unauthorized user.
            email (str): The email address of the unauthorized user.
            commit (bool, optional): Whether to commit the transaction immediately. Default is True.

        Returns:
            Tuple[UnauthorizedUser, bool]: A tuple containing the unauthorized user object and 
            a boolean indicating whether the user is newly created.

        Raises:
            HTTPException: 
                - 409 Conflict: If a user with the same email exists but the name or surname does not match.
                - 500 Internal Server Error: If an error occurs during the commit process.
        """
        logger.info(
            "Creating a new unauthorized user or retriving existing one if exists")
        logger.debug(
            f"Unauthorized user data provided: email: {email}, name: {name}, surname: {surname}")

        existing_user = db.query(
            UnauthorizedUser).filter_by(email=email).first()

        if existing_user:
            if existing_user.name != name or existing_user.surname != surname:
                logger.warning(
                    f"User with email {email} already exists but with a different name or surname")
                raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                    detail="User with this email already exists but with a different name or surname")
            logger.debug(
                f"Existing unauthorized user retrieved")
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
                logger.info(
                    "New unauthorized user created and committed to the database.")
            except Exception as e:
                db.rollback()
                logger.error(
                    f"Error while creating new unauthorized user: {e}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail="An internal error occurred while creating unauthorized user")
        return new_user, True

    @classmethod
    def get_all_unathorized_users(cls,
                                  db: Session) -> List["UnauthorizedUser"]:
        """
        Retrieves all unauthorized users from the database.

        Raises an exception if no unauthorized users are found.

        Args:
            db (Session): The database session used to execute the query.

        Returns:
            List[UnauthorizedUser]: A list of all unauthorized users in the database.

        Raises:
            HTTPException: 
                - 204 No Content: If no unauthorized users are found in the database.
        """
        logger.info("Retrieving all unauthorized users")

        users = db.query(UnauthorizedUser).all()
        if (not users):
            logger.warning(
                "No unauthorized users found")
            raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)
        logger.debug(f"Unauthorized users found")
        return users

    @classmethod
    def get_unathorized_user(cls,
                             db: Session,
                             user_id: int) -> "UnauthorizedUser":
        """
        Retrieves an unauthorized user by their ID from the database.

        Raises an exception if the user is not found.

        Args:
            db (Session): The database session used to execute the query.
            user_id (int): The ID of the unauthorized user to retrieve.

        Returns:
            UnauthorizedUser: The unauthorized user object with the specified ID.

        Raises:
            HTTPException: 
                - 204 No Content: If no unauthorized user with the given ID exists in the database.
        """
        logger.info(
            f"Attempting to retrieve unauthorized user with ID: {user_id}")
        user = db.query(UnauthorizedUser).filter(
            UnauthorizedUser.id == user_id).first()
        if not user:
            logger.warning(f"Unauthorized user with ID {user_id} not found")
            raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)
        logger.debug(f"Unauthorized user retrieved")
        return user
    
    @classmethod
    def get_unathorized_user_email(cls,
                             db: Session,
                             email: str) -> "UnauthorizedUser":
        """
        Retrieves an unauthorized user by their email from the database.

        Raises an exception if the user is not found.

        Args:
            db (Session): The database session used to execute the query.
            email (str): The email of the unauthorized user to retrieve.

        Returns:
            UnauthorizedUser: The unauthorized user object with the specified email.

        Raises:
            HTTPException: 
                - 204 No Content: If no unauthorized user with the given email exists in the database.
        """
        logger.info(
            f"Attempting to retrieve unauthorized user with email: {email}")
        user = db.query(UnauthorizedUser).filter(
            UnauthorizedUser.email == email).first()
        if not user:
            logger.warning(f"Unauthorized user with email {email} not found")
            raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)
        logger.debug(f"Unauthorized user retrieved: {user}")
        return user

    @classmethod
    def update_unauthorized_user(cls,
                                 db: Session,
                                 user_id: int,
                                 user_data: schemas.UnauthorizedUser,
                                 commit: bool = True) -> "UnauthorizedUser":
        """
        Updates an unauthorized user's information in the database.

        Commits the transaction unless specified otherwise.

        Args:
            db (Session): The database session used to execute the operation.
            user_id (int): The ID of the unauthorized user to update.
            user_data (schemas.UnauthorizedUser): The updated data for the unauthorized user.
            commit (bool, optional): Whether to commit the transaction immediately. Default is True.

        Returns:
            UnauthorizedUser: The updated unauthorized user object.

        Raises:
            HTTPException: 
                - 404 Not Found: If no unauthorized user with the given ID exists in the database.
                - 500 Internal Server Error: If an error occurs during the commit process.
        """
        logger.info(
            f"Attempting to update unauthorized user with ID: {user_id}")
        logger.debug(f"New unaauthorized user data: {user_data}")

        user = db.query(UnauthorizedUser).filter(
            UnauthorizedUser.id == user_id).first()

        if not user:
            logger.warning(f"Unauthorized user with id {user_id} not found.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Unauthorized user not found")

        for key, value in user_data.model_dump().items():
            setattr(user, key, value)

        if commit:
            try:
                db.commit()
                logger.info(
                    f"Unauthorized user with ID {user_id} updated successfully.")
            except Exception as e:
                logger.error(
                    f"Error while updating unauthorized user with ID {user_id}: {e}")
                db.rollback()
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail="An internal error occurred while updating unauthorized user")

        return user

    @classmethod
    def delete_unauthorized_user(cls,
                                 db: Session,
                                 user_id: int,
                                 commit: bool = True) -> bool:
        """
        Deletes an unauthorized user by their ID from the database.

        Commits the transaction unless specified otherwise.

        Args:
            db (Session): The database session used to execute the operation.
            user_id (int): The ID of the unauthorized user to delete.
            commit (bool, optional): Whether to commit the transaction immediately. Default is True.

        Returns:
            bool: `True` if the unauthorized user was successfully deleted.

        Raises:
            HTTPException: 
                - 404 Not Found: If no unauthorized user with the given ID exists in the database.
                - 500 Internal Server Error: If an error occurs during the commit process.
        """
        logger.info(
            f"Attempting to delete unauthorized user with ID: {user_id}")

        user = db.query(UnauthorizedUser).filter(
            UnauthorizedUser.id == user_id).first()

        if not user:
            logger.warning(f"Unauthorized user with id {user_id} not found.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Unauthorized user doesn't exist")

        db.delete(user)
        if commit:
            try:
                logger.info(
                    f"Unauthorized user with ID {user_id} deleted successfully.")
                db.commit()
            except Exception as e:
                logger.error(
                    f"Error while deleting unauthorized user with ID {user_id}: {e}")
                db.rollback()
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail="An internal error occurred while deleting unauthorized user")
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

        Raises an exception if no notes are found that match the filter criteria.

        Args:
            db (Session): The database session used to execute the query.
            user_id (Optional[int]): The ID of the user to filter notes by. Default is `None`.

        Returns:
            List[UserNote]: A list of user notes matching the filter criteria.

        Raises:
            HTTPException: 
                - 204 No Content: If no user notes are found that match the given criteria.
        """
        logger.info("Attempting to retrieve user notes.")
        logger.debug(f"Filtering notes by user ID: {user_id}")

        notes = db.query(UserNote)
        if user_id:
            notes = notes.filter(UserNote.user_id == user_id)
        notes = notes.all()
        if not notes:
            logger.warning(f"No user notes found that match given criteria")
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT)
        logger.debug(
            f"Retrieved {len(notes)} user notes that match given criteria")
        return notes

    @classmethod
    def get_user_note_id(cls,
                         db: Session,
                         note_id: int) -> "UserNote":
        """
        Retrieves a user note by its ID.

        Raises an exception if the note with the specified ID is not found.

        Args:
            db (Session): The database session used to execute the query.
            note_id (int): The ID of the note to retrieve.

        Returns:
            UserNote: The user note with the specified ID.

        Raises:
            HTTPException: 
                - 204 No Content: If no user note with the given ID exists in the database.
        """
        logger.info(f"Attempting to retrieve user note with ID: {note_id}")
        note = db.query(UserNote).filter(UserNote.id == note_id).first()
        if not note:
            logger.warning(f"Note with ID {note_id} not found.")
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT)

        logger.debug(f"Retrieved user note")
        return note

    @classmethod
    def create_user_note(cls,
                         db: Session,
                         note_data: schemas.UserNoteCreate,
                         commit: bool = True) -> "UserNote":
        """
        Creates a new user note with the specified data and saves it to the database.

        Commits the transaction and refreshes the note object if `commit` is `True`.

        Args:
            db (Session): The database session used to execute the operation.
            note_data (schemas.UserNoteCreate): The data for creating a new user note.
            commit (bool, optional): Whether to commit the transaction immediately. Default is `True`.

        Returns:
            UserNote: The newly created user note.

        Raises:
            HTTPException: 
                - 500 Internal Server Error: If an error occurs during the commit process.
        """
        logger.info("Creating a new user note.")
        logger.debug(f"Note data provided: {note_data}")

        note_data_dict = note_data.model_dump()
        note_data_dict["timestamp"] = datetime.datetime.now()
        note = UserNote(**note_data_dict)
        db.add(note)
        if commit:
            try:
                db.commit()
                logger.info(
                    "User note created and committed to the database.")
            except Exception as e:
                db.rollback()
                logger.error(
                    f"Error while creating user note': {e}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail="An internal error occurred while creating user note")
        return note

    @classmethod
    def update_user_note(cls,
                         db: Session,
                         note_id: int,
                         note_data: schemas.NoteUpdate,
                         commit: bool = True) -> "UserNote":
        """
        Updates a user note by ID with new data, or deletes the note if the new content is `None`.

        Commits the transaction and refreshes the note object if `commit` is `True`.

        Args:
            db (Session): The database session used to execute the operation.
            note_id (int): The ID of the note to update.
            note_data (schemas.NoteUpdate): The new data for updating the note.
            commit (bool, optional): Whether to commit the transaction immediately. Default is `True`.

        Returns:
            UserNote: The updated user note.

        Raises:
            HTTPException: 
                - 404 Not Found: If no user note with the given ID exists in the database.
                - 204 No Content: If the note is deleted.
                - 500 Internal Server Error: If an error occurs during the commit process.
        """
        logger.info(f"Attempting to update user note with ID: {note_id}")

        note = db.query(UserNote).filter(UserNote.id == note_id).first()

        if not note:
            logger.warning(f"User note with id {note_id} not found for update")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Note not found")
        if note_data.note is None:
            logger.info(
                f"Deleting user note with ID: {note_id} as new content is None.")
            cls.delete_user_note(db, note_id)
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT)

        logger.debug(f"Updating user note content to: {note_data.note}")
        note.note = note_data.note
        note.timestamp = datetime.datetime.now()

        if commit:
            try:
                db.commit()
                logger.info(
                    f"User note with ID {note_id} updated successfully.")
            except Exception as e:
                db.rollback()
                logger.error(
                    f"Error while updating user note with ID {note_id}: {e}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail="An internal error occurred while updating user note")

        return note

    @classmethod
    def delete_user_note(cls,
                         db: Session,
                         note_id: int,
                         commit: Optional[bool] = True) -> bool:
        """
        Deletes a user note by its ID.

        Commits the transaction after deleting the note if `commit` is `True`.

        Args:
            db (Session): The database session used to execute the operation.
            note_id (int): The ID of the note to delete.
            commit (bool, optional): Whether to commit the transaction after deleting the note. Default is `True`.

        Returns:
            bool: `True` if the note was successfully deleted.

        Raises:
            HTTPException: 
            - 404 Not Found: If no user note with the given ID exists in the database.
            - 500 Internal Server Error: If an error occurs during the commit process.
        """
        logger.info(f"Attempting to delete user note with ID: {note_id}")

        note = db.query(UserNote).filter(UserNote.id == note_id).first()
        if not note:
            logger.warning(
                f"User note with ID {note_id} not found for deletion")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Note doesn't exist")
        db.delete(note)
        if commit:
            try:
                db.commit()
                logger.info(
                    f"User mote with ID {note_id} deleted successfully.")
            except Exception as e:
                db.rollback()
                logger.error(
                    f"Error while deleting user note with ID {note_id}: {e}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail="An internal error occurred while deleting user note")
        return True
