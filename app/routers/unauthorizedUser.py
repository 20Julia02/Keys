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
    Checks whether an unauthorised user with a given email exists in the database.
    If so and his name and surname matches those in the database it returns an existing user, 
    if the email was not in the database it creates a new user. If the email address was registered 
    and the user provides a different first and last name than in the database, the error is raised.
    """
    logger.info(
        f"POST request to retrieve unauthorized user if exists or create new one if not")
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
def get_all_unathorized_users(current_concierge: muser.User = Depends(oauth2.get_current_concierge),
                              db: Session = Depends(database.get_db)) -> Sequence[schemas.UnauthorizedUserOut]:
    """
    Retrieves all unauthorized users from the database.
    Raises an exception if no users are found.
    """
    logger.info(
        f"GET request to retrieve unauthorized users")
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
def get_unathorized_user(user_id: int,
                         current_concierge: muser.User = Depends(
                             oauth2.get_current_concierge),
                         db: Session = Depends(database.get_db)) -> schemas.UnauthorizedUserOut:
    """
    Retrieves an unauthorized user by their ID.
    Raises an exception if the user is not found.
    """
    logger.info(
        f"GET request to retrieve unauthorized user with ID: {user_id}.")
    return muser.UnauthorizedUser.get_unathorized_user(db, user_id)


@router.get("/email/{email}",
            response_model=schemas.UnauthorizedUserOut)
def get_unathorized_user_email(email: str,
                               current_concierge: muser.User = Depends(
                                   oauth2.get_current_concierge),
                                db: Session = Depends(database.get_db)) -> schemas.UnauthorizedUserOut:
    """
    Retrieves an unauthorized user by their email.
    Raises an exception if the user is not found.
    """
    logger.info(
        f"GET request to retrieve unauthorized user with email: {email}.")
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
def update_unauthorized_user(user_id: int,
                             user_data: schemas.UnauthorizedUser,
                             db: Session = Depends(database.get_db),
                             current_concierge: muser.User = Depends(
                                 oauth2.get_current_concierge)
                             ) -> schemas.UnauthorizedUserOut:
    """
    Updates an unauthorized user's information.
    """
    logger.info(
        f"POST request to update unauthorized user with user_id {user_id}")
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
def delete_unauthorized_user(user_id: int,
                             db: Session = Depends(database.get_db),
                             current_concierge: muser.User = Depends(oauth2.get_current_concierge)):
    """
    Deletes an unauthorized user by their ID from the database.
    Raises an exception if the user is not found.
    """
    logger.info(
        f"DELETE request to delete unauthorized user with ID: {user_id}")
    return muser.UnauthorizedUser.delete_unauthorized_user(db, user_id)
