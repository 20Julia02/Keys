from fastapi import Depends, APIRouter, status, Response
from typing import Sequence
from app.schemas import UserOut, UserCreate
from app import database, oauth2
from sqlalchemy.orm import Session
import app.models.user as muser
from app.config import logger

router = APIRouter(
    prefix="/users",
    tags=['Users']
)


@router.get("/",
            response_model=Sequence[UserOut],
            responses={
                200: {
                    "description": "List of all users.",
                    "content": {
                        "application/json": {
                            "example": [
                                {
                                    "id": 1,
                                    "name": "John",
                                    "surname": "Doe",
                                    "role": "employee",
                                    "faculty": "Geodesy and Cartography",
                                    "photo_url": "http://example.com/photo.jpg"
                                }
                            ]
                        }
                    },
                },
                404: {
                    "description": "No users found in the database.",
                    "content": {
                        "application/json": {
                            "example": {
                                "detail": "There is no user in the database"
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
def get_all_users(response: Response,
                  current_concierge: muser.User = Depends(oauth2.get_current_concierge),
                  db: Session = Depends(database.get_db)) -> Sequence[UserOut]:
    """
    Retrieve all users from the database.

    This endpoint fetches a list of all users stored in the database. If no users are found,
    an exception is raised with a descriptive error message.

    The operation ensures that the requesting user is authenticated and updates their access token.
    """
    logger.info(
        f"GET request to retrieve users")
    oauth2.set_access_token_cookie(response, current_concierge.id, current_concierge.role.value, db)
    return muser.User.get_all_users(db)


@router.get("/{user_id}",
            response_model=UserOut,
            responses={
                200: {
                    "description": "Data of the user with the specified ID.",
                    "content": {
                        "application/json": {
                            "example": {
                                "id": 1,
                                "name": "John",
                                "surname": "Doe",
                                "role": "employee",
                                "faculty": "Geodesy and Cartography",
                                "photo_url": "http://example.com/photo.jpg"
                            }
                        }
                    },
                },
                404: {
                    "description": "User with the specified ID not found.",
                    "content": {
                        "application/json": {
                            "example": {
                                "detail": "User with id: {user_id} doesn't exist"
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
def get_user(response: Response,
             user_id: int,
             current_concierge: muser.User = Depends(
                 oauth2.get_current_concierge),
             db: Session = Depends(database.get_db)) -> UserOut:
    """
    Retrieve a user by their ID from the database.

    This endpoint fetches details of a user identified by their unique ID. If the user does not exist, 
    an exception is raised with a descriptive error message.

    The operation ensures that the requesting user is authenticated and updates their access token.
    """
    logger.info(
        f"GET request to retrieve user with ID: {user_id}")
    oauth2.set_access_token_cookie(response, current_concierge.id, current_concierge.role.value, db)
    return muser.User.get_user_id(db, user_id)


@router.post("/",
             response_model=UserOut,
             status_code=status.HTTP_201_CREATED,
             responses={
                 201: {
                     "description": "User created successfully.",
                     "content": {
                         "application/json": {
                             "example": {
                                 "id": 1,
                                 "name": "John",
                                 "surname": "Doe",
                                 "role": "employee",
                                 "faculty": "Geodesy and Cartography",
                                 "photo_url": "http://example.com/photo.jpg"
                             }
                         }
                     }
                 },
                 400: {
                     "description": "Bad request. Invalid input data.",
                     "content": {
                         "application/json": {
                             "example": {
                                 "detail": "Invalid input data"
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
def create_user(response: Response,
                user_data: UserCreate,
                current_concierge: muser.User = Depends(
                    oauth2.get_current_concierge),
                db: Session = Depends(database.get_db)) -> UserOut:
    """
    Create a new user in the database.

    This endpoint allows the creation of a new user with the provided details. If the input 
    data is invalid, a 400 error is returned. Upon successful creation, the new user's details 
    are returned.

    The operation ensures that the requesting user is authenticated and updates their access token.
    """
    logger.info("POST request to create user")
    oauth2.set_access_token_cookie(response, current_concierge.id, current_concierge.role.value, db)
    return muser.User.create_user(db, user_data)


@router.delete("/{user_id}",
               status_code=status.HTTP_204_NO_CONTENT,
               responses={
                   204: {
                       "description": "User deleted successfully."
                   },
                   404: {
                       "description": "User with the specified ID not found.",
                       "content": {
                           "application/json": {
                               "example": {
                                   "detail": "User with id: {user_id} doesn't exist"
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
def delete_user(response: Response,
                user_id: int,
                current_concierge: muser.User = Depends(
                    oauth2.get_current_concierge),
                db: Session = Depends(database.get_db)):
    """
    Delete a user by their ID from the database.

    This endpoint removes a user from the database using their unique ID. If the user does not exist, 
    an exception is raised with a descriptive error message.

    The operation ensures that the requesting user is authenticated and updates their access token.
    """
    logger.info(
        f"DELETE request to delete user with ID: {user_id}")
    oauth2.set_access_token_cookie(response, current_concierge.id, current_concierge.role.value, db)
    return muser.User.delete_user(db, user_id)


@router.post("/{user_id}",
             response_model=UserOut,
             responses={
                 200: {
                     "description": "User updated successfully.",
                     "content": {
                         "application/json": {
                             "example": {
                                 "id": 1,
                                 "name": "John",
                                 "surname": "Doe",
                                 "role": "employee",
                                 "faculty": "Geodesy and Cartography",
                                 "photo_url": "http://example.com/photo.jpg"
                             }
                         }
                     }
                 },
                 404: {
                     "description": "User with the specified ID not found.",
                     "content": {
                         "application/json": {
                             "example": {
                                 "detail": "User with id: {user_id} doesn't exist"
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
def update_user(response: Response,
                user_id: int,
                user_data: UserCreate,
                current_concierge: muser.User = Depends(
                    oauth2.get_current_concierge),
                db: Session = Depends(database.get_db)) -> UserOut:
    """
    Update a user's information in the database.

    This endpoint updates the details of a user identified by their unique ID. If the user does not exist, 
    an exception is raised with a descriptive error message.

    The operation ensures that the requesting user is authenticated and updates their access token.
    """
    logger.info(f"POST request to edit user with ID: {user_id}")
    oauth2.set_access_token_cookie(response, current_concierge.id, current_concierge.role.value, db)
    return muser.User.update_user(db, user_id, user_data)
