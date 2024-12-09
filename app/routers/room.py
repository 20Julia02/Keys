from fastapi import Depends, APIRouter, status, Response
from typing import Sequence, Optional
from app.schemas import RoomOut, Room
from app import database, oauth2
from sqlalchemy.orm import Session
import app.models.device as mdevice
from app.models.user import User
from app.services import securityService
from app.config import logger
import app.models.user as muser

router = APIRouter(
    prefix="/rooms",
    tags=['Rooms']
)


@router.get("/",
            response_model=Sequence[RoomOut],
            responses={
                404: {
                    "description": "If no rooms are found in the database.",
                    "content": {
                        "application/json": {
                            "example": {
                                "detail": "No rooms found"
                            }
                        }
                    }
                }
            })
def get_rooms(response: Response,
              current_concierge: User = Depends(oauth2.get_current_concierge),
              number: Optional[str] = None,
              db: Session = Depends(database.get_db)) -> Sequence[RoomOut]:
    """
    Retrieve a list of rooms from the database.

    This endpoint fetches all rooms stored in the database. If a specific `number` 
    is provided, it filters and returns the room with the matching number.

    """
    logger.info(f"GET request to retrieve rooms filtered by number {number}")
    
    return mdevice.Room.get_rooms(db, number)


@router.get("/{room_id}",
            response_model=RoomOut,
            responses={
                404: {
                    "description": "If no room with the given ID exists in the database",
                    "content": {
                        "application/json": {
                            "example": {
                                "detail": "Room not found"
                            }
                        }
                    }
                },
            })
def get_room_id(response: Response,
                room_id: int,
                current_concierge: User = Depends(
                    oauth2.get_current_concierge),
                db: Session = Depends(database.get_db)) -> RoomOut:
    """
    Retrieve a room by its ID.

    This endpoint fetches a room from the database using the provided `room_id`. 
    If the room does not exist, a 404 error is returned.

    """
    logger.info(f"GET request to retrieve room by ID: {room_id}")
    
    return mdevice.Room.get_room_id(db, room_id)


@router.post("/",
             response_model=RoomOut,
             status_code=status.HTTP_201_CREATED,
             responses={
                 403: {
                     "description": "If the user does not have the required role or higher.",
                     "content": {
                         "application/json": {
                             "example": {
                                 "detail": "You cannot perform this operation without the appropriate role"
                             }
                         }
                     }
                 },
                 500: {
                     "description": "If an internal error occurs during the commit",
                     "content": {
                         "application/json": {
                             "example": {
                                 "detail": "An internal error occurred while creating room."
                             }
                         }
                     }
                 }
             })
def create_room(response: Response,
                room_data: Room,
                current_concierge: User = Depends(
                    oauth2.get_current_concierge),
                db: Session = Depends(database.get_db)) -> RoomOut:
    """
    Create a new room in the database.

    This endpoint creates a new room using the provided data. If a room with the 
    specified number already exists, a 400 error is returned. The requesting user must 
    have the 'admin' role to perform this action.

    """
    logger.info(f"POST request to create room with number: {room_data.number}")
    
    auth_service = securityService.AuthorizationService(db)
    auth_service.entitled_or_error(muser.UserRole.admin, current_concierge)
    return mdevice.Room.create_room(db, room_data)


@router.post("/{room_id}",
             response_model=RoomOut,
             responses={
                 403: {
                     "description": "If the user does not have the required role or higher.",
                     "content": {
                         "application/json": {
                             "example": {
                                 "detail": "You cannot perform this operation without the appropriate role"
                             }
                         }
                     }
                 },
                 404: {
                     "description": "If the room is not found.",
                     "content": {
                         "application/json": {
                             "example": {
                                 "detail": "Room not found"
                             }
                         }
                     }
                 },
                 400: {
                     "description": "If a room with the new number already exists.",
                     "content": {
                         "application/json": {
                             "example": {
                                 "detail": "Room with this number already exists."
                             }
                         }
                     }
                 },
                 500: {
                     "description": "If an internal error occurs during the commit.",
                     "content": {
                         "application/json": {
                             "example": {
                                 "detail": "An internal error occurred while updating room"
                             }
                         }
                     }
                 }
             })
def update_room(response: Response,
                room_id: int,
                room_data: Room,
                current_concierge: User = Depends(
                    oauth2.get_current_concierge),
                db: Session = Depends(database.get_db)) -> RoomOut:
    """
    Update an existing room in the database.

    This endpoint updates the details of an existing room using the provided `room_id`. 
    If the room does not exist, a 404 error is returned. The requesting user must have 
    the 'admin' role to perform this action.

    """
    logger.info(
        f"POST request to update room with ID: {room_id}")
    
    auth_service = securityService.AuthorizationService(db)
    auth_service.entitled_or_error(muser.UserRole.admin, current_concierge)
    return mdevice.Room.update_room(db, room_id, room_data)


@router.delete("/{room_id}",
               status_code=status.HTTP_204_NO_CONTENT,
               responses={
                   403: {
                     "description": "If the user does not have the required role or higher.",
                     "content": {
                         "application/json": {
                             "example": {
                                 "detail": "You cannot perform this operation without the appropriate role"
                             }
                         }
                     }
                 },
                   404: {
                       "description": "If the room with the given ID does not exist.",
                       "content": {
                           "application/json": {
                               "example": {
                                   "detail": "Room doesn't exist"
                               }
                           }
                       }
                   },
                   500: {
                       "description": "If an internal error occurs during the commit.",
                       "content": {
                           "application/json": {
                               "example": {
                                   "detail": "An internal error occurred while deleting room"
                               }
                           }
                       }
                   }
               })
def delete_room(response: Response,
                room_id: int,
                current_concierge: User = Depends(
                    oauth2.get_current_concierge),
                db: Session = Depends(database.get_db)):
    """
    Delete a room by its ID from the database.

    This endpoint removes a room using the specified `room_id`. If the room does not exist, 
    a 404 error is returned. The requesting user must have the 'admin' role to perform this action.

    """
    logger.info(f"DELETE request to delete room with ID: {room_id}")
    
    auth_service = securityService.AuthorizationService(db)
    auth_service.entitled_or_error(muser.UserRole.admin, current_concierge)
    return mdevice.Room.delete_room(db, room_id)
