from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from app import database, oauth2, schemas
from app.services import securityService
import app.models.operation as moperation
from app.models.user import User
import app.models.user as muser
from typing import Sequence
from fastapi import Path
from app.config import logger


router = APIRouter(
    tags=['Session']
)


@router.post("/approve/login/session/{session_id}",
             response_model=Sequence[schemas.DevOperationOut],
             responses={
                 403: {
                     "description": "Authentication failed due to incorrect login credentials.",
                     "content": {
                         "application/json": {
                             "example": {
                                 "invalid_card_code": {
                                     "detail": "Invalid credential"
                                 },
                                 "not_entitled": {
                                     "detail": "You cannot perform this operation without the concierge role"
                                 }
                             }
                         }
                     }
                 },
                 404: {
                     "description": "Session not found or no unapproved operations for the session.",
                     "content": {
                         "application/json": {
                             "example": {
                                 "session_not_found": {
                                     "detail": "Session not found"
                                 },
                                 "no_operations_found": {
                                     "detail": "No unapproved operations found for this session"
                                 }
                             }
                         }
                     }
                 },
                 500: {
                     "description": "Internal server error occurred during the operation transfer process..",
                     "content": {
                         "application/json": {
                             "example": {
                                 "detail": "Error during operation transfer"
                             }
                         }
                     }
                 },
             }
             )
def approve_session_login(response: Response,
                          session_id: int = Path(description="Unique identifier of the session that contains operations awaiting approval."),
                          db: Session = Depends(database.get_db),
                          concierge_credentials: OAuth2PasswordRequestForm = Depends(),
                          current_concierge: User = Depends(oauth2.get_current_concierge)):
    """
    Approve a session and its associated operations using login credentials.

    This endpoint finalizes a session, allowing a concierge to approve operations 
    that modify devices during the session. Authentication is performed using login 
    credentials (username and password). Once approved, the operations are moved 
    from the unapproved state to the approved operations data.

    If the session ID is invalid or there are no unapproved operations, appropriate 
    error messages are returned.

    The operation ensures that the requesting user is authenticated and updates their access token.
    """
    logger.info(f"POST request to approve session by login and password")
    oauth2.set_access_token_cookie(response, current_concierge.id, current_concierge.role.value, db)
    auth_service = securityService.AuthorizationService(db)
    auth_service.authenticate_user_login(
        concierge_credentials.username, concierge_credentials.password, "concierge")
    moperation.UserSession.end_session(db, session_id)
    operations = moperation.UnapprovedOperation.create_operation_from_unapproved(
        db, session_id)
    return operations


@router.post("/approve/card/session/{session_id}",
             response_model=Sequence[schemas.DevOperationOut],
             responses={
                 403: {
                     "description": "Authentication failed due to incorrect login credentials.",
                     "content": {
                         "application/json": {
                             "example": {
                                 "invalid_card_code": {
                                     "detail": "Invalid credential"
                                 },
                                 "not_entitled": {
                                     "detail": "You cannot perform this operation without the concierge role"
                                 },
                                 "session_already_approved": {
                                     "detail": "Session has been allready ended with status potwierdzona"
                                 }
                             }
                         }
                     }
                 },
                 404: {
                     "description": "Session not found or no unapproved operations for the session.",
                     "content": {
                         "application/json": {
                             "example": {
                                 "session_not_found": {
                                     "detail": "Session not found"
                                 },
                                 "no_operations_found": {
                                     "detail": "No unapproved operations found for this session"
                                 }
                             }
                         }
                     }
                 },
                 500: {
                     "description": "Internal server error occurred during the operation transfer process..",
                     "content": {
                         "application/json": {
                             "example": {
                                 "detail": "Error during operation transfer"
                             }
                         }
                     }
                 },
             }
             )
def approve_session_card(
    response: Response,
    card_data: schemas.CardId,
    session_id: int = Path(
        description="Unique identifier of the session that contains operations awaiting approval."),
    db: Session = Depends(database.get_db),
    current_concierge: User = Depends(oauth2.get_current_concierge)
) -> Sequence[schemas.DevOperationOut]:
    """
    Approve a session and its associated operations using a card ID.

    This endpoint finalizes a session, allowing a concierge to approve operations 
    that modify devices during the session. Authentication is performed using the 
    concierge's card ID. Once approved, the operations are moved from the unapproved 
    state to the approved operations data.

    If the session ID is invalid or there are no unapproved operations, appropriate 
    error messages are returned.

    The operation ensures that the requesting user is authenticated and updates their access token.
    """
    logger.info(f"POST request to approve session by card")
    oauth2.set_access_token_cookie(response, current_concierge.id, current_concierge.role.value, db)
    auth_service = securityService.AuthorizationService(db)
    auth_service.authenticate_user_card(card_data, "concierge")

    moperation.UserSession.end_session(db, session_id)

    operations = moperation.UnapprovedOperation.create_operation_from_unapproved(
        db, session_id)

    return operations


@router.post("/reject/session/{session_id}")
def reject_session(response: Response,
                   session_id: int = Path(description="Unique identifier of the session"),
                   db: Session = Depends(database.get_db),
                   current_concierge: User = Depends(oauth2.get_current_concierge)):
    """
    Reject a session and its associated operations.

    This endpoint allows a concierge to reject all operations within a session, 
    effectively canceling the session. The associated unapproved operations are 
    deleted, and the session is marked as rejected.

    If the session ID is invalid, an appropriate error message is returned.

    The operation ensures that the requesting user is authenticated and updates their access token.
    """
    logger.info(f"POST request to reject session by login and password")
    oauth2.set_access_token_cookie(response, current_concierge.id, current_concierge.role.value, db)
    moperation.UserSession.end_session(db, session_id, reject=True)

    return moperation.UnapprovedOperation.delete_all_for_session(db, session_id)


@router.post("/start-session/login", response_model=schemas.SessionOut, responses={
    403: {
        "description": "Authentication failed due to incorrect login credentials.",
        "content": {
            "application/json": {
                "example": {
                    "invalid_card_code": {
                        "detail": "Invalid credentials"
                    },
                    "not_entitled": {
                        "detail": "You cannot perform this operation without the employee role"
                    }
                }
            }
        }
    },
})
def start_login_session(response: Response,
                        user_credentials: OAuth2PasswordRequestForm = Depends(),
                        current_concierge: muser.User = Depends(
                            oauth2.get_current_concierge),
                        db: Session = Depends(database.get_db)) -> schemas.SessionOut:
    """
    Start a session for a user using login credentials.

    This endpoint allows a concierge to create a session for a user by authenticating 
    them with their username and password. Once authenticated, the session is assigned 
    to the current concierge and is ready for operations.

    If the authentication fails, an error message is returned.

    The operation ensures that the requesting user is authenticated and updates their access token.
    """
    logger.info(
        f"POST request to start new session by user using login and password")
    oauth2.set_access_token_cookie(response, current_concierge.id, current_concierge.role.value, db)
    auth_service = securityService.AuthorizationService(db)

    user = auth_service.authenticate_user_login(
        user_credentials.username, user_credentials.password, "employee")
    return moperation.UserSession.create_session(db, user.id, current_concierge.id)


@router.post("/start-session/card", response_model=schemas.SessionOut, responses={
    403: {
        "description": "Authentication failed due to incorrect login credentials.",
        "content": {
            "application/json": {
                "example": {
                    "invalid_card_code": {
                        "detail": "Invalid credentials"
                    },
                    "not_entitled": {
                        "detail": "You cannot perform this operation without the employee role"
                    }
                }
            }
        }
    },
})
def start_card_session(response: Response,
                       card_id: schemas.CardId,
                       current_concierge: muser.User = Depends(
                           oauth2.get_current_concierge),
                       db: Session = Depends(database.get_db)) -> schemas.SessionOut:
    """
    Start a session for a user using a card ID.

    This endpoint allows a concierge to create a session for a user by authenticating 
    them with their card ID. Once authenticated, the session is assigned to the current 
    concierge and is ready for operations.

    If the authentication fails, an error message is returned.

    The operation ensures that the requesting user is authenticated and updates their access token.
    """
    logger.info(f"POST request to start new session by user using card")
    oauth2.set_access_token_cookie(response, current_concierge.id, current_concierge.role.value, db)
    auth_service = securityService.AuthorizationService(db)
    user = auth_service.authenticate_user_card(card_id, "employee")
    return moperation.UserSession.create_session(db, user.id, current_concierge.id)


@router.post("/start-session/unauthorized/{unauthorized_id}", response_model=schemas.Session, responses={
    404: {
        "description": "Unauthorized user not found.",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Unauthorized user with id 123 not found"
                }
            }
        }
    },
})
def start_unauthorized_session(response: Response,
                               unauthorized_id: int,
                               current_concierge: muser.User = Depends(
                                   oauth2.get_current_concierge),
                               db: Session = Depends(database.get_db)) -> schemas.Session:
    """
    Start a session for an unauthorized user.

    This endpoint allows a concierge to create a session for an unauthorized user 
    identified by their unique ID. If the unauthorized user exists in the database, 
    the session is assigned to the current concierge.

    If the unauthorized user ID is invalid, a 404 error is returned.

    The operation ensures that the requesting user is authenticated and updates their access token.
    """
    logger.info(
        f"POST request to start new session by unauthorized user with ID {unauthorized_id}")
    oauth2.set_access_token_cookie(response, current_concierge.id, current_concierge.role.value, db)
    user = db.query(muser.UnauthorizedUser).filter_by(
        id=unauthorized_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="Unauthorized user not found"
        )
    return moperation.UserSession.create_session(db, unauthorized_id, current_concierge.id)


@router.get("/session/{session_id}", response_model=schemas.Session)
def get_session_id(response: Response,
                   session_id: int,
                   current_concierge: muser.User = Depends(
                       oauth2.get_current_concierge),
                   db: Session = Depends(database.get_db)) -> schemas.Session:
    """
    Retrieve details of a specific session by its ID.

    This endpoint fetches detailed information about a session, including its status, 
    associated operations, and the user responsible for it. The session is identified 
    by its unique ID.

    If the session ID is invalid, an appropriate error message is returned.

    The operation ensures that the requesting user is authenticated and updates their access token.
    """
    logger.info(
        f"GET request to retrieve session with ID {session_id}.")
    oauth2.set_access_token_cookie(response, current_concierge.id, current_concierge.role.value, db)
    return moperation.UserSession.get_session_id(db, session_id)
