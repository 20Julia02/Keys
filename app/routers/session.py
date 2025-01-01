from fastapi import APIRouter, Depends, HTTPException, status
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


@router.post("/start-session/login", response_model=schemas.SessionOut, responses={
     403: {
            "description": "If the credentials are invalid or the user does not have the required role",
                     "content": {
                         "application/json": {
                             "example": {
                                 "invalid_card_code": {
                                     "detail": "Invalid credentials"
                                 },
                                 "not_entitled": {
                                     "detail": "You cannot perform this operation without the concierge role"
                                 }
                             }
                         }
            }
            },
     500: {
            "description": "If an error occurs while committing the transaction",
                     "content": {
                         "application/json": {
                             "example": {
                                    "detail": "An internal error occurred while creating session"
                             }
                         }
            }
            },
})
def start_login_session(user_credentials: OAuth2PasswordRequestForm = Depends(),
                        current_concierge: muser.User = Depends(
                            oauth2.get_current_concierge),
                        db: Session = Depends(database.get_db)) -> schemas.SessionOut:
    """
    Start a session for a user using login credentials.

    This endpoint allows a concierge to create a session for a user by authenticating 
    them with their username and password. Once authenticated, the session is assigned 
    to the current concierge and is ready for operations.

    If the authentication fails, an error message is returned.

    """
    logger.info(
        f"POST request to start new session by user using login and password")
    
    auth_service = securityService.AuthorizationService(db)

    user = auth_service.authenticate_user_login(
        user_credentials.username, user_credentials.password, "employee")
    return moperation.UserSession.create_session(db, user.id, current_concierge.id)


@router.post("/start-session/card", response_model=schemas.SessionOut, responses={
     403: {
            "description": "If the card code are invalid or the user does not have the required role",
                     "content": {
                         "application/json": {
                             "example": {
                                 "invalid_card_code": {
                                     "detail": "Invalid credentials"
                                 },
                                 "not_entitled": {
                                     "detail": "You cannot perform this operation without the concierge role"
                                 }
                             }
                         }
            }
            },
     500: {
            "description": "If an error occurs while committing the transaction",
                     "content": {
                         "application/json": {
                             "example": {
                                    "detail": "An internal error occurred while creating session"
                             }
                         }
            }
            },
})
def start_card_session(card_id: schemas.CardId,
                       current_concierge: muser.User = Depends(
                           oauth2.get_current_concierge),
                       db: Session = Depends(database.get_db)) -> schemas.SessionOut:
    """
    Start a session for a user using a card ID.

    This endpoint allows a concierge to create a session for a user by authenticating 
    them with their card ID. Once authenticated, the session is assigned to the current 
    concierge and is ready for operations.

    If the authentication fails, an error message is returned.

    """
    logger.info(f"POST request to start new session by user using card")
    
    auth_service = securityService.AuthorizationService(db)
    user = auth_service.authenticate_user_card(card_id, "employee")
    return moperation.UserSession.create_session(db, user.id, current_concierge.id)


@router.post("/start-session/unauthorized/{unauthorized_id}", response_model=schemas.Session, responses={
     404: {
            "description": "If no unauthorized user with the given ID exists",
                     "content": {
                         "application/json": {
                             "example": {
                                     "detail": "Unauthorized user not found"
                                 },
                         }
            }
            },
     500: {
            "description": "If an error occurs while committing the transaction",
                     "content": {
                         "application/json": {
                             "example": {
                                    "detail": "An internal error occurred while creating session"
                             }
                         }
            }
            },
})
def start_unauthorized_session(unauthorized_id: int,
                               current_concierge: muser.User = Depends(
                                   oauth2.get_current_concierge),
                               db: Session = Depends(database.get_db)) -> schemas.Session:
    """
    Start a session for an unauthorized user.

    This endpoint allows a concierge to create a session for an unauthorized user 
    identified by their unique ID. If the unauthorized user exists in the database, 
    the session is assigned to the current concierge.

    If the unauthorized user ID is invalid, a 404 error is returned.

    """
    logger.info(
        f"POST request to start new session by unauthorized user with ID {unauthorized_id}")
    
    user = db.query(muser.UnauthorizedUser).filter_by(
        id=unauthorized_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="Unauthorized user not found"
        )
    return moperation.UserSession.create_session(db, unauthorized_id, current_concierge.id)


@router.get("/session/{session_id}", response_model=schemas.Session, responses={
    404: {
        "description": "If no session with the given ID exists.",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Session doesn't exist"
                }
            }
        }
    },
})
def get_session_id(session_id: int,
                   current_concierge: muser.User = Depends(
                       oauth2.get_current_concierge),
                   db: Session = Depends(database.get_db)) -> schemas.Session:
    """
    Retrieve details of a specific session by its ID.

    This endpoint fetches detailed information about a session, including its status, 
    associated operations, and the user responsible for it. The session is identified 
    by its unique ID.

    If the session ID is invalid, an appropriate error message is returned.

    """
    logger.info(
        f"GET request to retrieve session with ID {session_id}.")
    
    session = moperation.UserSession.get_session_id(db, session_id)
    if not session:
        logger.warning(f"Session with ID {session_id} not found.")
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)

    logger.debug(f"Retrieved session")
    return session


@router.post("/approve/login/session/{session_id}",
             response_model=Sequence[schemas.DevOperationOut],
             responses={
                 403: {
                     "description": "If the credentials are invalid, the user does not have the required role or higher or the user does not have the required role or if the session was already ended",
                     "content": {
                         "application/json": {
                             "example": {
                                 "invalid_credentials": {
                                     "detail": "Invalid credential"
                                 },
                                 "not_entitled": {
                                     "detail": "You cannot perform this operation without the concierge role"
                                 },
                                 "session_ended": {
                                     "detail": "Session has been already ended."
                                 }
                             }
                         }
                     }
                 },
                 404: {
                     "description": "If the session with the given ID does not exist or if no unapproved operations match the given criteria.",
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
                     "description": "If an error occurs during the commit",
                     "content": {
                         "application/json": {
                             "example": {
                             "operation_transfer": {
                                     "detail": "An internal error occurred during operation transfer"
                                 },
                                 "creating_operation": {
                                     "detail": "An internal error occurred while creating operation"
                                 }
                             }
                             
                         }
                     }
                 },
             }
             )
def approve_session_login(session_id: int = Path(description="Unique identifier of the session that contains operations awaiting approval."),
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

    """
    logger.info(f"POST request to approve session by login and password")
    
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
                     "description": "If the card code are invalid, the user does not have the required role or higher or the user does not have the required role or if the session was already ended",
                     "content": {
                         "application/json": {
                             "example": {
                                 "invalid_card_code": {
                                     "detail": "Invalid credential"
                                 },
                                 "not_entitled": {
                                     "detail": "You cannot perform this operation without the concierge role"
                                 },
                                 "session_ended": {
                                     "detail": "Session has been already ended."
                                 }
                             }
                         }
                     }
                 },
                 404: {
                     "description": "If the session with the given ID does not exist or if no unapproved operations match the given criteria.",
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
                     "description": "If an error occurs during the commit",
                     "content": {
                         "application/json": {
                             "example": {
                             "operation_transfer": {
                                     "detail": "An internal error occurred during operation transfer"
                                 },
                                 "creating_operation": {
                                     "detail": "An internal error occurred while creating operation"
                                 }
                             }
                             
                         }
                     }
                 },
             }
             )
def approve_session_card(
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

    """
    logger.info(f"POST request to approve session by card")
    
    auth_service = securityService.AuthorizationService(db)
    auth_service.authenticate_user_card(card_data, "concierge")

    moperation.UserSession.end_session(db, session_id)

    operations = moperation.UnapprovedOperation.create_operation_from_unapproved(
        db, session_id)

    return operations


@router.post("/reject/session/{session_id}", responses={
                 403: {
                     "description": "If the session was already ended",
                     "content": {
                         "application/json": {
                             "example": {
                                     "detail": "Session has been already ended."
                             }
                         }
                     }
                 },
                 404: {
                     "description": "If the session with the given ID does not exist or if no unapproved operations match the given criteria.",
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
                     "description": "If an error occurs during the commit.",
                     "content": {
                         "application/json": {
                             "example": {
                                     "detail": "An internal error occurred while deleting unapproved operations"
                             }
                             
                         }
                     }
                 },
})
def reject_session(session_id: int = Path(description="Unique identifier of the session"),
                   db: Session = Depends(database.get_db),
                   current_concierge: User = Depends(oauth2.get_current_concierge)):
    """
    Reject a session and its associated operations.

    This endpoint allows a concierge to reject all operations within a session, 
    effectively canceling the session. The associated unapproved operations are 
    deleted, and the session is marked as rejected.

    If the session ID is invalid, an appropriate error message is returned.

    """
    logger.info(f"POST request to reject session by login and password")
    
    moperation.UserSession.end_session(db, session_id, reject=True)

    return moperation.UnapprovedOperation.delete_all_for_session(db, session_id)



