from fastapi import Depends, APIRouter, status
from typing import Sequence, Optional
from app.schemas import RoomOut, Room
from app import database, oauth2
from sqlalchemy.orm import Session
import app.models.device as mdevice
from app.models.user import User
from app.services import securityService

router = APIRouter(
    prefix="/rooms",
    tags=['Rooms']
)


@router.get("/",
            response_model=Sequence[RoomOut],
            responses={
                200: {
                    "description": "List of all rooms matching the specified number.",
                    "content": {
                        "application/json": {
                            "example": [
                                {
                                    "id": 1,
                                    "number": "101",
                                }
                            ]
                        }
                    }
                },
                404: {
                    "description": "No rooms found that match the specified number.",
                    "content": {
                        "application/json": {
                            "example": {
                                "detail": "No rooms found"
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
def get_rooms(current_concierge: User = Depends(oauth2.get_current_concierge),
              number: Optional[str] = None,
              db: Session = Depends(database.get_db)) -> Sequence[RoomOut]:
    """
    Retrieves a list of rooms from the database. If `room_number` is specified, 
    only returns the room with the matching number.
    """
    return mdevice.Room.get_rooms(db, number)


@router.get("/{room_id}",
            response_model=RoomOut,
            responses={
                200: {
                    "description": "Details of the room with the specified ID.",
                    "content": {
                        "application/json": {
                            "example": {
                                "id": 1,
                                "number": "101"
                            }
                        }
                    }
                },
                404: {
                    "description": "Room with the specified ID not found.",
                    "content": {
                        "application/json": {
                            "example": {
                                "detail": "Room with id: {room_id} doesn't exist"
                            }
                        }
                    }
                },
                422: {
                    "description": "Validation error: Room ID must be an integer.",
                    "content": {
                        "application/json": {
                            "example": {
                                "detail": [
                                    {
                                        "loc": ["path", "room_id"],
                                        "msg": "Room ID must be an integer",
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
def get_room_id(room_id: int,
                current_concierge: User = Depends(
                    oauth2.get_current_concierge),
                db: Session = Depends(database.get_db)) -> RoomOut:
    """
    Retrieves a room by its ID from the database.
    """
    return mdevice.Room.get_room_id(db, room_id)


@router.post("/",
             response_model=RoomOut,
             status_code=status.HTTP_201_CREATED,
             responses={
                 201: {
                     "description": "Room created successfully.",
                     "content": {
                         "application/json": {
                             "example": {
                                 "id": 1,
                                 "number": "101"
                             }
                         }
                     }
                 },
                 400: {
                     "description": "Room with the specified number already exists.",
                     "content": {
                         "application/json": {
                             "example": {
                                 "detail": "Room with number '101' already exists."
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
def create_room(room_data: Room,
                current_concierge: User = Depends(
                    oauth2.get_current_concierge),
                db: Session = Depends(database.get_db)) -> RoomOut:
    """
    Creates a new room in the database.
    """
    auth_service = securityService.AuthorizationService(db)
    auth_service.entitled_or_error("admin", current_concierge)
    return mdevice.Room.create_room(db, room_data)


@router.post("/{room_id}",
             response_model=RoomOut,
             responses={
                 200: {
                     "description": "Room updated successfully.",
                     "content": {
                         "application/json": {
                             "example": {
                                 "id": 1,
                                 "number": "101"
                             }
                         }
                     }
                 },
                 400: {
                     "description": "Room with the specified number already exists.",
                     "content": {
                         "application/json": {
                             "example": {
                                 "detail": "Room with number '101' already exists."
                             }
                         }
                     }
                 },
                 404: {
                     "description": "Room with the specified ID not found.",
                     "content": {
                         "application/json": {
                             "example": {
                                 "detail": "Room with id: {room_id} doesn't exist"
                             }
                         }
                     }
                 },
                 422: {
                     "description": "Validation error: Room ID must be an integer.",
                     "content": {
                         "application/json": {
                             "example": {
                                 "detail": [
                                    {
                                        "loc": ["path", "room_id"],
                                        "msg": "Room ID must be an integer",
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
def update_room(room_id: int,
                room_data: Room,
                current_concierge: User = Depends(
                    oauth2.get_current_concierge),
                db: Session = Depends(database.get_db)) -> RoomOut:
    """
    Updates an existing room in the database.
    """
    auth_service = securityService.AuthorizationService(db)
    auth_service.entitled_or_error("admin", current_concierge)
    return mdevice.Room.update_room(db, room_id, room_data)


@router.delete("/{room_id}",
               status_code=status.HTTP_204_NO_CONTENT,
               responses={
                   204: {
                       "description": "Room deleted successfully."
                   },
                   404: {
                       "description": "Room with the specified ID not found.",
                       "content": {
                           "application/json": {
                               "example": {
                                   "detail": "Room with id: {room_id} doesn't exist"
                               }
                           }
                       }
                   },
                   422: {
                       "description": "Validation error: Room ID must be an integer.",
                       "content": {
                           "application/json": {
                               "example": {
                                   "detail": [
                                       {
                                           "loc": ["path", "room_id"],
                                           "msg": "Room ID must be an integer",
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
def delete_room(room_id: int,
                current_concierge: User = Depends(
                    oauth2.get_current_concierge),
                db: Session = Depends(database.get_db)):
    """
    Deletes a room by its ID from the database.
    """
    auth_service = securityService.AuthorizationService(db)
    auth_service.entitled_or_error("admin", current_concierge)
    return mdevice.Room.delete_room(db, room_id)
