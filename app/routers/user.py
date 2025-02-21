from fastapi import Depends, APIRouter, status
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
                404: {
                    "description": "If no users are found in the database.",
                    "content": {
                        "application/json": {
                            "example": {
                                "detail": "There is no user in the database"
                            }
                        }
                    }
                },
            })
def get_all_users(current_concierge: muser.User = Depends(oauth2.get_current_concierge),
                  db: Session = Depends(database.get_db)) -> Sequence[UserOut]:
    """
    Retrieve all users from the database.

    This endpoint fetches a list of all users stored in the database. If no users are found,
    an exception is raised with a descriptive error message.

    """
    logger.info(
        f"GET request to retrieve users")
    
    return muser.User.get_all_users(db)


@router.get("/{user_id}",
            response_model=UserOut,
            responses={
                404: {
                    "description": "If no user with the given ID exists in the database.",
                    "content": {
                        "application/json": {
                            "example": {
                                "detail": "User doesn't exist"
                            }
                        }
                    }
                }
            })
def get_user_id(user_id: int,
             current_concierge: muser.User = Depends(
                 oauth2.get_current_concierge),
             db: Session = Depends(database.get_db)) -> UserOut:
    """
    Retrieve a user by their ID from the database.

    This endpoint fetches details of a user identified by their unique ID. If the user does not exist, 
    an exception is raised with a descriptive error message.

    """
    logger.info(
        f"GET request to retrieve user with ID: {user_id}")
    
    return muser.User.get_user_id(db, user_id)


@router.post("/",
             response_model=UserOut,
             status_code=status.HTTP_201_CREATED,
             responses={
                 500: {
                     "description": "If an error occurs during the commit process.",
                     "content": {
                         "application/json": {
                             "example": {
                                "detail": "An internal error occurred while creating user"
                             }
                         }
                     }
                 }
             })
def create_user(user_data: UserCreate,
                current_concierge: muser.User = Depends(
                    oauth2.get_current_concierge),
                db: Session = Depends(database.get_db)) -> UserOut:
    """
    Create a new user in the database.

    This endpoint allows the creation of a new user with the provided details. If the input 
    data is invalid, a 400 error is returned. Upon successful creation, the new user's details 
    are returned.

    """
    logger.info("POST request to create user")
    
    return muser.User.create_user(db, user_data)


@router.delete("/{user_id}",
               status_code=status.HTTP_204_NO_CONTENT,
               responses={
                   404: {
                       "description": "If no user with the given ID exists in the database.",
                       "content": {
                           "application/json": {
                               "example": {
                                   "detail": "User doesn't exist"
                               }
                           }
                       }
                   },
                   500: {
                       "description": "If an error occurs during the commit process.",
                       "content": {
                           "application/json": {
                               "example": {
                                   "detail": "An internal error occurred while deleting user"
                               }
                           }
                       }
                   }
               })
def delete_user(user_id: int,
                current_concierge: muser.User = Depends(
                    oauth2.get_current_concierge),
                db: Session = Depends(database.get_db)):
    """
    Delete a user by their ID from the database.

    This endpoint removes a user from the database using their unique ID. If the user does not exist, 
    an exception is raised with a descriptive error message.

    """
    logger.info(
        f"DELETE request to delete user with ID: {user_id}")
    
    return muser.User.delete_user(db, user_id)


@router.post("/update/{user_id}",
             response_model=UserOut,
             responses={
                 404: {
                     "description": "If no user with the given ID exists in the database.",
                     "content": {
                         "application/json": {
                             "example": {
                                 "detail": "User not found"
                             }
                         }
                     }
                 },
                 500: {
                     "description": "If an error occurs during the commit process.",
                     "content": {
                         "application/json": {
                             "example": {
                                 "detail": "An internal error occurred while updating user"
                             }
                         }
                     }
                 }
             })
def update_user(user_id: int,
                user_data: UserCreate,
                current_concierge: muser.User = Depends(
                    oauth2.get_current_concierge),
                db: Session = Depends(database.get_db)) -> UserOut:
    """
    Update a user's information in the database.

    This endpoint updates the details of a user identified by their unique ID. If the user does not exist, 
    an exception is raised with a descriptive error message.

    """
    logger.info(f"POST request to edit user with ID: {user_id}")
    
    return muser.User.update_user(db, user_id, user_data)
