from fastapi import status, Depends, APIRouter, Response
from typing import Sequence
from app import database, oauth2, schemas
import app.models.user as muser
from sqlalchemy.orm import Session
from app.config import logger


router = APIRouter(
    prefix="/unauthorized-users",
    tags=['Unauthorized users']
)


@router.post("/",
             response_model=schemas.UnauthorizedUserOut,
             responses={
                 201: {
                     "description": "A new unauthorized user has been created.",
                     "content": {
                         "application/json": {
                             "example": {
                                 "id": 1,
                                 "name": "John",
                                 "surname": "Doe",
                                 "email": "john.doe@example.com",
                             }
                         }
                     },
                 },
                 200: {
                     "description": "The user already exists and has been returned.",
                     "content": {
                         "application/json": {
                             "example": {
                                 "id": 1,
                                 "name": "John",
                                 "surname": "Doe",
                                 "email": "john.doe@example.com",
                             }
                         }
                     }
                 },
                 403: {
                     "description": "A user with this email already exists but has a different first or last name.",
                     "content": {
                         "application/json": {
                             "example": {
                                 "detail": "User with this email already exists but with a different name or surname"
                             }
                         }
                     }
                 },
                 500: {
                     "description": "An internal server error occurred.",
                     "content": {
                         "application/json": {
                             "example": {
                                 "detail": "Internal server error"
                             }
                         }
                     }
                 }
             })
def create_or_get_unauthorized_user(user: schemas.UnauthorizedUserNote,
                                    response: Response,
                                    db: Session = Depends(database.get_db),
                                    current_concierge: muser.User = Depends(
                                        oauth2.get_current_concierge)
                                    ) -> schemas.UnauthorizedUserOut:
    """
    Create a new unauthorized user or retrieve an existing one.

    This endpoint checks if an unauthorized user with the given email exists in the database:
    - If the user exists and the name and surname match, the existing user is returned.
    - If the user does not exist, a new unauthorized user is created and returned.
    - If the email exists but the provided name and surname do not match, an error is raised.

    Additionally, a note can be attached to the user if provided in the request.

    The operation ensures that the requesting user is authenticated and updates their access token.
    """
    logger.info(
        f"POST request to retrieve unauthorized user if exists or create new one if not")
    oauth2.set_access_token_cookie(response, current_concierge.id, current_concierge.role.value, db)
    new_user, created = muser.UnauthorizedUser.create_or_get_unauthorized_user(
        db, user.name, user.surname, user.email)

    if created:
        logger.debug("Unauthorized user has been created")
        response.status_code = status.HTTP_201_CREATED
    else:
        logger.debug("Existing unauthorized user has been retrieved")
        response.status_code = status.HTTP_200_OK

    if user.note:
        logger.debug("Note was provided and will be added to database")
        note_data = schemas.UserNoteCreate(user_id=new_user.id, note=user.note)
        muser.UserNote.create_user_note(db, note_data)

    return new_user


@router.get("/",
            response_model=Sequence[schemas.UnauthorizedUserOut],
            responses={
                200: {
                    "description": "List of all unauthorized users.",
                    "content": {
                        "application/json": {
                            "example": [
                                {
                                    "id": 1,
                                    "name": "John",
                                    "surname": "Doe",
                                    "email": "john.doe@example.com",
                                }
                            ]
                        }
                    }
                },
                404: {
                    "description": "No unauthorized users found in the database.",
                    "content": {
                        "application/json": {
                            "example": {
                                "detail": "There is no unauthorized user in database"
                            }
                        }
                    }
                },
                500: {
                    "description": "An internal server error occurred.",
                    "content": {
                        "application/json": {
                            "example": {
                                "detail": "Internal server error"
                            }
                        }
                    }
                }
            })
def get_all_unathorized_users(response: Response,
                              current_concierge: muser.User = Depends(oauth2.get_current_concierge),
                              db: Session = Depends(database.get_db)) -> Sequence[schemas.UnauthorizedUserOut]:
    """
    Retrieve all unauthorized users from the database.

    This endpoint fetches a list of all unauthorized users stored in the database.
    If no users are found, an exception is raised.

    The operation ensures that the requesting user is authenticated and updates their access token.
    """
    logger.info(
        f"GET request to retrieve unauthorized users")
    oauth2.set_access_token_cookie(response, current_concierge.id, current_concierge.role.value, db)
    return muser.UnauthorizedUser.get_all_unathorized_users(db)


@router.get("/{user_id}",
            response_model=schemas.UnauthorizedUserOut,
            responses={
                200: {
                    "description": "Data of the unauthorized user with the specified ID.",
                    "content": {
                        "application/json": {
                            "example": {
                                "id": 1,
                                "name": "John",
                                "surname": "Doe",
                                "email": "john.doe@example.com",
                            }
                        }
                    }
                },
                404: {
                    "description": "Unauthorized user with the specified ID not found.",
                    "content": {
                        "application/json": {
                            "example": {
                                "detail": "Unauthorized user with id: {user_id} doesn't exist"
                            }
                        }
                    }
                },
                422: {
                    "description": "Validation error: User ID must be an integer.",
                    "content": {
                        "application/json": {
                            "example": {
                                "detail": [
                                    {
                                        "loc": ["path", "user_id"],
                                        "msg": "User ID must be an integer",
                                        "type": "type_error.integer"
                                    }
                                ]
                            }
                        }
                    }
                },
                500: {
                    "description": "An internal server error occurred.",
                    "content": {
                        "application/json": {
                            "example": {
                                "detail": "Internal server error"
                            }
                        }
                    }
                }
            })
def get_unathorized_user(response: Response,
                         user_id: int,
                         current_concierge: muser.User = Depends(
                             oauth2.get_current_concierge),
                         db: Session = Depends(database.get_db)) -> schemas.UnauthorizedUserOut:
    """
    Retrieve an unauthorized user by their ID.

    This endpoint fetches an unauthorized user based on their unique ID. If the user
    does not exist, an exception is raised with a descriptive error message.

    The operation ensures that the requesting user is authenticated and updates their access token.
    """
    logger.info(
        f"GET request to retrieve unauthorized user with ID: {user_id}.")
    oauth2.set_access_token_cookie(response, current_concierge.id, current_concierge.role.value, db)
    return muser.UnauthorizedUser.get_unathorized_user(db, user_id)


@router.get("/email/{email}",
            response_model=schemas.UnauthorizedUserOut)
def get_unathorized_user_email(response: Response,
                               email: str,
                               current_concierge: muser.User = Depends(
                                   oauth2.get_current_concierge),
                                db: Session = Depends(database.get_db)) -> schemas.UnauthorizedUserOut:
    """
    Retrieve an unauthorized user by their email.

    This endpoint fetches an unauthorized user based on their email address. If the user
    does not exist, an exception is raised with a descriptive error message.

    The operation ensures that the requesting user is authenticated and updates their access token.
    """
    logger.info(
        f"GET request to retrieve unauthorized user with email: {email}.")
    oauth2.set_access_token_cookie(response, current_concierge.id, current_concierge.role.value, db)
    return muser.UnauthorizedUser.get_unathorized_user_email(db, email)


@router.post("/{user_id}",
             response_model=schemas.UnauthorizedUserOut,
             responses={
                 200: {
                     "description": "Unauthorized user updated successfully.",
                     "content": {
                         "application/json": {
                             "example": {
                                 "id": 1,
                                 "name": "John",
                                 "surname": "Doe",
                                 "email": "john.doe@example.com",
                             }
                         }
                     }
                 },
                 404: {
                     "description": "Unauthorized user with the specified ID not found.",
                     "content": {
                         "application/json": {
                             "example": {
                                 "detail": "Unauthorized user with id: {user_id} doesn't exist"
                             }
                         }
                     }
                 },
                 422: {
                     "description": "Validation error: User ID must be an integer.",
                     "content": {
                         "application/json": {
                             "example": {
                                 "detail": [
                                    {
                                        "loc": ["path", "user_id"],
                                        "msg": "User ID must be an integer",
                                        "type": "type_error.integer"
                                    }
                                 ]
                             }
                         }
                     }
                 },
                 500: {
                     "description": "Internal server error occurred.",
                     "content": {
                         "application/json": {
                             "example": {
                                 "detail": "Internal server error"
                             }
                         }
                     }
                 }
             })
def update_unauthorized_user(response: Response,
                             user_id: int,
                             user_data: schemas.UnauthorizedUser,
                             db: Session = Depends(database.get_db),
                             current_concierge: muser.User = Depends(
                                 oauth2.get_current_concierge)
                             ) -> schemas.UnauthorizedUserOut:
    """
    Update an unauthorized user's information.

    This endpoint updates the details of an unauthorized user identified by their unique ID.
    If the user does not exist, an exception is raised with a descriptive error message.

    The operation ensures that the requesting user is authenticated and updates their access token.
    """
    logger.info(
        f"POST request to update unauthorized user with user_id {user_id}")
    oauth2.set_access_token_cookie(response, current_concierge.id, current_concierge.role.value, db)
    return muser.UnauthorizedUser.update_unauthorized_user(db, user_id, user_data)


@router.delete("/{user_id}",
               status_code=status.HTTP_204_NO_CONTENT,
               responses={
                   404: {
                       "description": "Unauthorized user with the specified ID not found.",
                       "content": {
                           "application/json": {
                               "example": {
                                   "detail": "Unauthorized user with id: {user_id} doesn't exist"
                               }
                           }
                       }
                   },
                   422: {
                       "description": "Validation error: User ID must be an integer.",
                       "content": {
                           "application/json": {
                               "example": {
                                   "detail": [
                                       {
                                           "loc": ["path", "user_id"],
                                           "msg": "User ID must be an integer",
                                           "type": "type_error.integer"
                                       }
                                   ]
                               }
                           }
                       }
                   },
                   500: {
                       "description": "An internal server error occurred.",
                       "content": {
                           "application/json": {
                               "example": {
                                   "detail": "Internal server error"
                               }
                           }
                       }
                   }
               })
def delete_unauthorized_user(response: Response,
                             user_id: int,
                             db: Session = Depends(database.get_db),
                             current_concierge: muser.User = Depends(oauth2.get_current_concierge)):
    """
    Delete an unauthorized user by their ID.

    This endpoint removes an unauthorized user from the database using their unique ID.
    If the user does not exist, an exception is raised with a descriptive error message.

    The operation ensures that the requesting user is authenticated and updates their access token.
    """
    logger.info(
        f"DELETE request to delete unauthorized user with ID: {user_id}")
    oauth2.set_access_token_cookie(response, current_concierge.id, current_concierge.role.value, db)
    return muser.UnauthorizedUser.delete_unauthorized_user(db, user_id)
