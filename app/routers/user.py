from fastapi import Depends, APIRouter, status
from typing import Sequence
from app.schemas import UserOut, UserCreate
from app import database, oauth2
from sqlalchemy.orm import Session
import app.models.user as muser

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
def get_all_users(current_concierge: muser.User = Depends(oauth2.get_current_concierge),
                  db: Session = Depends(database.get_db)) -> Sequence[UserOut]:
    """
    Retrieves all users from the database.
    If no users are found, raises an exception.
    """
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
def get_user(user_id: int,
             current_concierge: muser.User = Depends(
                 oauth2.get_current_concierge),
             db: Session = Depends(database.get_db)) -> UserOut:
    """
    Retrieves a user by their ID from the database.
    Raises an exception if the user is not found.
    """
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
def create_user(user_data: UserCreate,
                current_concierge: muser.User = Depends(oauth2.get_current_concierge),
                db: Session = Depends(database.get_db)) -> UserOut:
    """
    Creates a new user in the database.
    """
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
def delete_user(user_id: int,
                current_concierge: muser.User = Depends(oauth2.get_current_concierge),
                db: Session = Depends(database.get_db)):
    """
    Deletes a user by their ID from the database.
    """
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
def update_user(user_id: int,
                user_data: UserCreate,
                current_concierge: muser.User = Depends(oauth2.get_current_concierge),
                db: Session = Depends(database.get_db)) -> UserOut:
    """
    Updates a user's information in the database.
    """
    return muser.User.update_user(db, user_id, user_data)
