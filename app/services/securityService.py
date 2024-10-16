from sqlalchemy import Column, Integer
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from passlib.context import CryptContext
import datetime
from zoneinfo import ZoneInfo
from jose import JWTError, jwt
from app.config import settings
from app import models, schemas


class PasswordService:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash_password(self, password: str) -> str:
        """
        Hashes the given password using the bcrypt algorithm.

        Args:
            password (str): The plain text password to hash.

        Returns:
            str: The hashed password.
        """
        return self.pwd_context.hash(password)

    def verify_hashed(self, plain_text: str, hashed_text: str) -> bool:
        """
        Verifies that the given plain text password matches the hashed password.

        Args:
            plain_password (str): The plain text password to verify.
            hashed_password (str): The hashed password to compare against.

        Returns:
            bool: True if the passwords match, False otherwise.
        """

        return self.pwd_context.verify(plain_text, hashed_text)


class TokenService:
    def __init__(self, db: Session):
        """
        Initializes the TokenService with a given database session and token settings.
        """
        self.db = db
        self.SECRET_KEY = settings.secret_key
        self.ALGORITHM = settings.algorithm
        self.ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
        self.REFRESH_TOKEN_EXPIRE_MINUTES = settings.refresh_token_expire_minutes

    def create_token(self, data: dict, token_type: str) -> str:
        """
        Creates a JWT token with the given data and token type (refresh or access).

        Args:
            data (dict): The data to encode in the token.
            type (str): The type of token ('refresh' or 'access').

        Returns:
            str: The encoded JWT token.
        """
        if token_type == "refresh":
            time_delta = self.REFRESH_TOKEN_EXPIRE_MINUTES
        else:
            time_delta = self.ACCESS_TOKEN_EXPIRE_MINUTES
        to_encode = data.copy()

        expire = datetime.datetime.now(ZoneInfo("Europe/Warsaw")) + datetime.timedelta(minutes=time_delta)
        to_encode.update({"exp": expire})

        encoded_jwt = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)

        return encoded_jwt

    def verify_concierge_token(self, token: str) -> schemas.TokenData:
        """
        Verifies the given JWT token and extracts the token data.

        Args:
            token (str): The JWT token to verify.
            credentials_exception: The exception to raise if the token is invalid.

        Returns:
            TokenData: An object containing the extracted token data (user_id and user_role).

        Raises:
            HTTPException: If the token is invalid or missing required data.
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            user_id = payload.get("user_id")
            role = payload.get("user_role")

            if user_id is None or role is None:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                    detail="Invalid token")
            token_data = schemas.TokenData(id=user_id, role=role)
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Invalid token")
        return token_data

    def is_token_blacklisted(self, token: str) -> bool:
        """
        Checks if a token is in the blacklist.

        Args:
            db (Session): The database session.
            token (str): The token to check.

        Returns:
            bool: True if the token is blacklisted, False otherwise.
        """
        return self.db.query(models.TokenBlacklist).filter_by(token=token).first() is not None

    def add_token_to_blacklist(self, token: str, commit: bool = True) -> bool:
        """
        Adds a token to the blacklist in the database.

        Args:
            db (Session): The database session.
            token (str): The token to blacklist.

        Returns:
            bool: True after the token is successfully added to the blacklist.
        """
        if not self.is_token_blacklisted(token):
            db_token = models.TokenBlacklist(token=token)
            self.db.add(db_token)
            if commit:
                self.db.commit()
                self.db.refresh(db_token)
        return True

    def generate_tokens(self, user_id: Column[Integer], role: str) -> schemas.Token:
        access_token = self.create_token({"user_id": user_id, "user_role": role}, "access")
        refresh_token = self.create_token({"user_id": user_id, "user_role": role}, "refresh")
        return schemas.Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")


class AuthorizationService:
    def __init__(self, db: Session):
        """
        Initializes the AuthorizationService with a given database session.
        """
        self.db = db

    def check_if_entitled(self, role: str, user: models.User) -> None:
        """
        Checks if the current user has the required role or is an admin.
        Raises an HTTP 403 Forbidden exception if the user is not entitled.

        Args:
            role (str): The required role.
            current_concierge: The current user object, containing the user's role.

        Raises:
            HTTPException: If the user does not have the required role.
        """
        if not (user.role.value == role or user.role.value == "admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You cannot perform this operation without the {role} role")

    def get_current_concierge(self, token: str) -> models.User:
        """
        Retrieves the current concierge from the database using the provided JWT token.

        Args:
            token (str): The JWT token.
            db (Session): The database session.

        Returns:
            User: The user object corresponding to the token's concierge ID and role.

        Raises:
            HTTPException: If the token is invalid, blacklisted, or the user is not found.
        """
        token_service = TokenService(self.db)
        if token_service.is_token_blacklisted(token):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="You are logged out")

        token_data = token_service.verify_concierge_token(token)

        user = self.db.query(models.User).filter(
            models.User.id == token_data.id,
            models.User.role == token_data.role
        ).first()

        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Could not validate credentials",
                                headers={"Authenticate": "Bearer"})
        self.check_if_entitled("concierge", user)
        return user

    def get_current_concierge_token(self, token: str) -> str:
        """
        Retrieves the current user's token after validating the user's identity.

        Args:
            token (str): The JWT token.
            db (Session): The database session.

        Returns:
            str: The validated JWT token.
        """
        _ = self.get_current_concierge(token)
        return token

    def authenticate_user_login(self, username: str, password: str, role: str) -> models.User:
        """Authenticate user by email and password."""
        password_service = PasswordService()
        user = self.db.query(models.User).filter_by(email=username).first()
        if not (user and password_service.verify_hashed(password, user.password)):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid credentials")
        self.check_if_entitled(role, user)
        return user

    def authenticate_user_card(self, card_id: schemas.CardId, role: str) -> models.User:
        password_service = PasswordService()
        users = self.db.query(models.User).filter(models.User.card_code.isnot(None)).all()
        for user in users:
            if password_service.verify_hashed(card_id.card_id, user.card_code):
                self.check_if_entitled(role, user)
                return user

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid credentials")
