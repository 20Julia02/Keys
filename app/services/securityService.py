from typing import Any, Literal
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from passlib.context import CryptContext
import datetime
from zoneinfo import ZoneInfo
from jose import JWTError, jwt
from app.config import settings
from app import schemas
import app.models.permission as mpermission
import app.models.user as muser
from app.config import logger


class PasswordService:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash_password(self,
                      password: str) -> str:
        """
        Hashes the given password using the bcrypt algorithm.

        Args:
            password (str): The plain text password to hash.

        Returns:
            str: The hashed password.
        """
        logger.info("Hashing given password")
        return self.pwd_context.hash(password)

    def verify_hashed(self,
                      plain_text: str,
                      hashed_text: str) -> bool:
        """
        Verifies that the given plain text password matches the hashed password.

        Args:
            plain_password (str): The plain text password to verify.
            hashed_password (str): The hashed password to compare against.

        Returns:
            bool: True if the passwords match, False otherwise.
        """
        logger.info("Verifing if given plain text matches the hashed one")
        verified = self.pwd_context.verify(plain_text, hashed_text)
        logger.debug(f"Text verified with response: {verified}")
        return verified


class TokenService:
    def __init__(self,
                 db: Session):
        self.db = db
        self.SECRET_KEY = settings.secret_key
        self.ALGORITHM = settings.algorithm
        self.ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
        self.REFRESH_TOKEN_EXPIRE_MINUTES = settings.refresh_token_expire_minutes

    def create_token(self,
                     data: dict[str, Any],
                     token_type: Literal['access', 'refresh']) -> str:
        """
        Creates a JWT token with the given data and token type (access or refresh).

        Args:
            data (dict[str, Any]): The data to encode in the token, such as user information.
            token_type (str): The type of token ('access' or 'refresh').

        Returns:
            str: The encoded JWT token.
        """

        logger.info("Creating a JWT token")
        logger.debug(
            f"Given  parameters - token_type: {token_type}, data: {data}")
        if token_type == "refresh":
            time_delta = self.REFRESH_TOKEN_EXPIRE_MINUTES
        else:
            time_delta = self.ACCESS_TOKEN_EXPIRE_MINUTES
        to_encode = data.copy()

        expire = datetime.datetime.now(
            ZoneInfo("Europe/Warsaw")) + datetime.timedelta(minutes=time_delta)
        to_encode.update({"exp": expire})

        encoded_jwt = jwt.encode(
            to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        logger.debug(f"Token created")
        return encoded_jwt

    def verify_concierge_token(self,
                               token: str) -> schemas.TokenData:
        """
        Verifies the given JWT token and extracts the token data.

        Args:
            token (str): The JWT token to verify.

        Returns:
            TokenData: An object containing the extracted token data (user_id and user_role).

        Raises:
            HTTPException: 
                - 401 Unauthorized: If the token is invalid or if the token is missing required data.
        """
        logger.info("Verifying the given token")
        try:
            payload = jwt.decode(token, self.SECRET_KEY,
                                 algorithms=[self.ALGORITHM])
            user_id = payload.get("user_id")
            role = payload.get("user_role")

            if user_id is None or role is None:
                logger.warning(
                    "Token does not contain information about the user id and role")
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                    detail="Invalid token")
            token_data = schemas.TokenData(id=user_id, role=role)
        except JWTError as e:
            logger.error(f"Failed to verify token: {str(e)}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Failed to verify token")
        logger.debug(
            f"Given token is verified and data are extracted: {token_data}")
        return token_data

    def is_token_blacklisted(self,
                             token: str) -> bool:
        """
        Checks if a token is in the blacklist.

        Args:
            token (str): The token to check.

        Returns:
            bool: True if the token is blacklisted, False otherwise.
        """
        logger.info("Checking if given token is not blacklisted")
        is_blacklisted = self.db.query(mpermission.TokenBlacklist).filter_by(
            token=token).first() is not None
        logger.debug(f"Token checked with response: {is_blacklisted}")
        return is_blacklisted

    def add_token_to_blacklist(self,
                               token: str,
                               commit: bool = True) -> bool:
        """
        Adds the token to the blacklist in the database if not already blacklisted.
        If `commit` is `True`, the transaction will be committed after the operation.

        Args:
            token (str): The token to blacklist.
            commit (bool, optional): Whether to commit the transaction after updating the blacklist. Defaults to `True`.

        Returns:
            bool: True if the token was successfully added to the blacklist, False if the token was already blacklisted.

        Raises:
            HTTPException: 
                - 500 Internal Server Error: If there is an error while adding the token to the blacklist.
        """
        logger.info("Adding the token to blacklist")
        if not self.is_token_blacklisted(token):
            db_token = mpermission.TokenBlacklist(token=token)
            self.db.add(db_token)
            if commit:
                try:
                    self.db.commit()
                    logger.debug("Token added to blacklist")
                except Exception as e:
                    self.db.rollback()
                    logger.error(
                        f"Error while adding token to blacklist: {e}")
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                        detail="An internal error occurred while adding token to blacklist")
            return True
        logger.debug("Token has been already blackllisted")
        return False

    def generate_tokens(self,
                        user_id: int,
                        role: str) -> schemas.Token:
        """
        Generates a pair of JWT tokens (access and refresh) for a user, based on their user ID and role.

        Args:
            user_id (int): The ID of the user for whom tokens are generated.
            role (str): The role of the user, which will be included in the token payload.

        Returns:
            Token: An object containing the access token, refresh token, and token type.
        """
        logger.info("Generating a pair of JWT tokens (access and refresh)")
        access_token = self.create_token(
            {"user_id": user_id, "user_role": role}, "access")
        refresh_token = self.create_token(
            {"user_id": user_id, "user_role": role}, "refresh")
        tokens = schemas.Token(access_token=access_token,
                               refresh_token=refresh_token, token_type="bearer")
        logger.debug("Tokens created")
        return tokens


class AuthorizationService:
    def __init__(self,
                 db: Session):
        self.db = db

    @staticmethod
    def entitled_or_error(role: muser.UserRole,
                          user: muser.User) -> bool:
        """
        Checks if the current user has the required role or higher.
        Raises an HTTP exception if the user is not entitled.

        Args:
            role (UserRole): The required role for the user.
            user (User): The user object, containing the user's role.

        Returns:
            bool: True if the user has the required role or higher.

        Raises:
            HTTPException: 
                - 403 Forbidden: If the user does not have the required role or higher.
        """
        logger.info(
            f"Checking if user with email: {user.email} has at least role: {role.value}")

        user_role = muser.UserRole[user.role] if isinstance(
            user.role, str) else user.role

        if user_role.weight > role.weight:
            logger.warning(
                f"The user: {user.email} with role: {user_role.value} cannot perform this operation without the {role.value} role")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot perform this operation without the appropriate role")
        return True

    def get_current_concierge(self,
                              token: str) -> muser.User:
        """
        Retrieves the current concierge from the database using the provided JWT token.

        Args:
            token (str): The JWT token.

        Returns:
            User: The user object corresponding to the token's concierge ID and role.

        Raises:
            HTTPException:
                - 403 Forbidden: If the token is blacklisted.
                - 401 Unauthorized: If the token is invalid or the user cannot be found in the database.
        """
        logger.info(
            f"Retrieving the concierge from the database by token")
        token_service = TokenService(self.db)
        if token_service.is_token_blacklisted(token):
            logger.error(
                "Token has been blacklisted. Concierge is logged out.")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Concierge is logged out")

        token_data = token_service.verify_concierge_token(token)

        user = self.db.query(muser.User).filter(
            muser.User.id == token_data.id,
            muser.User.role == token_data.role
        ).first()

        if user is None:
            logger.warning(
                f"Could not validate credentials. User with id: {token_data.id} and role {token_data.role} doesn't exist")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Could not validate credentials")
        self.entitled_or_error(muser.UserRole.concierge, user)
        logger.debug(
            f"User that match given token retrieved")
        return user

    def get_current_concierge_token(self,
                                    token: str) -> str:
        """
        Returns the current user's (concierge) token after validating their identity.

        Args:
            token (str): The JWT token to be verified.

        Returns:
            str: The validated JWT token for the user.

        Raises:
            HTTPException:
                - 403 Forbidden: If the token is invalid or blacklisted.
                - 401 Unauthorized: If the user is not found or credentials do not match.
        """
        logger.info(
            f"Retrieving the concierge by token")
        _ = self.get_current_concierge(token)
        return token

    def authenticate_user_login(self,
                                username: str,
                                password: str,
                                role: Literal["admin", "concierge", "employee", "student", "guest"]) -> muser.User:
        """
        Authenticates a user using their username and password, verifying credentials and role entitlement.

        Args:
            username (str): The username (email) of the user to authenticate.
            password (str): The plaintext password of the user.
            role (str): The role required for authentication.

        Returns:
            muser.User: The authenticated user object if credentials and role are valid.

        Raises:
            HTTPException:
                - 403 Forbidden: If the credentials are invalid or the user does not have the required role.
        """
        logger.info("Authenticating user by login and password")
        password_service = PasswordService()
        user = self.db.query(muser.User).filter_by(email=username).first()
        if not (user and password_service.verify_hashed(password, user.password)):
            logger.warning(
                "User with provided username doesn't exist" if not user else "Invalid password provided for user")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Invalid credentials")

        required_role = muser.UserRole[role]
        self.entitled_or_error(required_role, user)
        logger.info("User authenticated")
        return user

    def authenticate_user_card(self,
                               card_id: schemas.CardId,
                               role: Literal["admin", "concierge", "employee", "student", "guest"]) -> muser.User:
        """
        Authenticates a user using their card ID, checking credentials and role entitlement.

        Args:
            card_id (schemas.CardId): The card ID used for authentication.
            role (str): The role required for authentication.

        Returns:
            muser.User: The authenticated user object if the card ID and role are valid.

        Raises:
            HTTPException:
                - 403 Forbidden: If the card ID is invalid or the user does not have the required role.
        """
        logger.info("Authenticating user by card")
        password_service = PasswordService()
        users = self.db.query(muser.User).filter(
            muser.User.card_code.isnot(None)).all()
        for user in users:
            if password_service.verify_hashed(card_id.card_id, user.card_code):
                required_role = muser.UserRole[role]
                self.entitled_or_error(required_role, user)
                logger.info("User authenticated")
                return user
        logger.error(f"There is no user with given card code")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid credentials")
