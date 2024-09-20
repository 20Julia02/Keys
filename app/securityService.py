from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from .config import settings
from .schemas import TokenData, TokenDataUser, CardLogin, LoginConcierge
from .models import TokenBlacklist, User


class PasswordService:
    def __init__(self):
        """
        Initializes the PasswordService with a password context that uses bcrypt for hashing.
        """
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

    def create_token(self, data: dict, type: str) -> str:
        """
        Creates a JWT token with the given data and token type (refresh or access).

        Args:
            data (dict): The data to encode in the token.
            type (str): The type of token ('refresh' or 'access').

        Returns:
            str: The encoded JWT token.
        """
        if type == "refresh":
            time_delta = self.REFRESH_TOKEN_EXPIRE_MINUTES
        else:
            time_delta = self.ACCESS_TOKEN_EXPIRE_MINUTES
        to_encode = data.copy()

        expire = datetime.now(timezone.utc) + timedelta(minutes=time_delta)
        to_encode.update({"exp": expire})

        encoded_jwt = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)

        return encoded_jwt

    def verify_concierge_token(self, token: str) -> TokenData:
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
            id = payload.get("user_id")
            role = payload.get("user_role")

            if id is None or role is None:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                    detail="Invalid token")
            token_data = TokenData(id=id, role=role)
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Invalid token")
        return token_data

    def verify_user_token(self, token: str) -> TokenDataUser:
        """
        Verifies the given JWT token and extracts user-specific token data.

        Args:
            token (str): The JWT token to verify.

        Returns:
            TokenDataUser: An object containing the extracted token data (user_id and activity_id).

        Raises:
            HTTPException: If the token is invalid or missing required data.
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            id = payload.get("user_id")
            activity = payload.get("activity_id")

            if id is None or activity is None:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                    detail="Invalid token")
            token_data = TokenDataUser(user_id=id, activity=activity)
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
        return self.db.query(TokenBlacklist).filter_by(token=token).first() is not None

    def add_token_to_blacklist(self, token: str) -> bool:
        """
        Adds a token to the blacklist in the database.

        Args:
            db (Session): The database session.
            token (str): The token to blacklist.

        Returns:
            bool: True after the token is successfully added to the blacklist.
        """
        if not self.is_token_blacklisted(token):
            db_token = TokenBlacklist(token=token)
            self.db.add(db_token)
            self.db.commit()
        return True

    def generate_tokens(self, user_id: int, role: str) -> LoginConcierge:
        access_token = self.create_token({"user_id": user_id, "user_role": role}, "access")
        refresh_token = self.create_token({"user_id": user_id, "user_role": role}, "refresh")
        return LoginConcierge(access_token=access_token, refresh_token=refresh_token, type="bearer")


class AuthorizationService:
    def __init__(self, db: Session):
        """
        Initializes the AuthorizationService with a given database session.
        """
        self.db = db

    def check_if_entitled(self, role: str, current_concierge):
        """
        Checks if the current user has the required role or is an admin.
        Raises an HTTP 403 Forbidden exception if the user is not entitled.

        Args:
            role (str): The required role.
            current_concierge: The current user object, containing the user's role.

        Raises:
            HTTPException: If the user does not have the required role.
        """
        if not (current_concierge.role.value == role or current_concierge.role.value == "admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You cannot perform this operation without the {role} role")

    def get_current_concierge(self, token: str) -> User:
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
        credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                              detail="Could not validate credentials",
                                              headers={"Authenticate": "Bearer"})
        token_service = TokenService(self.db)
        if token_service.is_token_blacklisted(token):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="You are logged out")

        token_data = token_service.verify_concierge_token(token)

        user = self.db.query(User).filter(
            User.id == token_data.id,
            User.role == token_data.role
        ).first()

        if user is None:
            raise credentials_exception
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

    # TODO
    # sprawdzic jak z tym entitled
    def authenticate_user_login(self, username: str, password: str) -> User:
        """Authenticate user by email and password."""
        password_service = PasswordService()
        user = self.db.query(User).filter_by(email=username).first()
        if not (user and password_service.verify_hashed(password, user.password)):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid credentials")
        return user

    def authenticate_user_card(self, card_id: CardLogin) -> User:
        password_service = PasswordService()
        users = self.db.query(User).filter(User.card_code.isnot(None)).all()
        if not users:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No users found in the database")

        for user in users:
            if password_service.verify_hashed(card_id.card_id, user.card_code):
                return user
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid credentials")
