from fastapi import status, Depends, APIRouter, Response
from typing import Sequence, Optional
from app import database, oauth2, schemas
import app.models.user as muser
import app.models.device as mdevice
from sqlalchemy.orm import Session
from app.config import logger

router = APIRouter(
    prefix="/notes",
    tags=['Notes']
)


@router.get("/users", response_model=Sequence[schemas.UserNote], responses={
    404: {
        "description": "If no user notes are found that match the given criteria",
        "content": {
            "application/json": {
                "example": {
                    "detail": "No user notes found"
                }
            }
        }
    },
})
def get_user_notes_filtered(
        response: Response,
        user_id: Optional[int] = None,
        current_concierge: muser.User = Depends(oauth2.get_current_concierge),
        db: Session = Depends(database.get_db)) -> Sequence[schemas.UserNote]:
    """
    Retrieve all user-related notes stored in the database.

    This endpoint fetches notes associated with users and allows filtering by a specific user ID.
    If no notes match the criteria, a 404 response is returned with an appropriate error message.

    """
    logger.info(
        f"GET request to retrieve user notes filtered by user ID: {user_id}")
    
    return muser.UserNote.get_user_notes_filter(db, user_id)


@router.get("/users/{note_id}", response_model=schemas.UserNote, responses={
    404: {
        "description": "If no user note with the given ID exists in the database",
        "content": {
            "application/json": {
                "example": {
                    "detail": "There is no user note with this id"
                }
            }
        }
    },
})
def get_user_notes_id(
        response: Response,
        note_id: int,
        current_concierge: muser.User = Depends(oauth2.get_current_concierge),
        db: Session = Depends(database.get_db)) -> schemas.UserNote:
    """
    Retrieve a specific user-related note by its unique ID.

    This endpoint fetches a note linked to a user, identified by the provided note ID.
    If the note does not exist, a 404 response is returned.

    """
    logger.info(
        f"GET request to retrieve user notes filtered by note ID: {note_id}")
    
    return muser.UserNote.get_user_note_id(db, note_id)


@router.post("/users", response_model=schemas.UserNote, status_code=status.HTTP_201_CREATED, responses={
    500: {
        "description": "If an error occurs during the commit process",
        "content": {
            "application/json": {
                "example": {
                    "detail": "An internal error occurred while creating user note"
                }
            }
        }
    },
})
def add_user_note(note_data: schemas.UserNoteCreate,
                  response: Response,
                  current_concierge: muser.User = Depends(
                      oauth2.get_current_concierge),
                  db: Session = Depends(database.get_db)) -> schemas.UserNote:
    """
    Create a new note associated with a specific user.

    This endpoint allows adding notes to a user by providing necessary data in the request body.
    Upon successful creation, the newly created note is returned.

    """
    logger.info("POST request to create user note")
    
    return muser.UserNote.create_user_note(db, note_data)


@router.put("/users/{note_id}", response_model=schemas.UserNote, responses={
    500: {
        "description": "If an error occurs during the commit process",
        "content": {
            "application/json": {
                "example": {
                    "detail": "An internal error occurred while updating user note"
                }
            }
        }
    },
    404: {
        "description": "If no user note with the given ID exists in the database",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Note not found"
                }
            }
        }
    },
    204: {
        "description": "If the note is deleted",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Note deleted"
                }
            }
        }
    },
})
def edit_user_note(note_id: int,
                   response: Response,
                   note_data: schemas.NoteUpdate,
                   current_concierge: muser.User = Depends(
                       oauth2.get_current_concierge),
                   db: Session = Depends(database.get_db)) -> schemas.UserNote:
    """
    Update or delete a user note by its unique ID.

    This endpoint allows modifying an existing note. If the new content is `None`, the note is deleted.
    If the note does not exist, a 404 response is returned.

    """
    logger.info("PUT request to edit user note")
    
    return muser.UserNote.update_user_note(db, note_id, note_data)


@router.get("/devices", response_model=Sequence[schemas.DeviceNoteOut], responses={
    404: {
        "description": "If no device notes match the criteria",
        "content": {
            "application/json": {
                "example": {
                    "detail": "No device notes that match given criteria found"
                }
            }
        }
    },
})
def get_devices_notes_filtered(
                               response: Response,
                               device_id: Optional[int] = None,
                               current_concierge: muser.User = Depends(
                                   oauth2.get_current_concierge),
                               db: Session = Depends(database.get_db)) -> Sequence[schemas.DeviceNoteOut]:
    """
    Retrieve all notes associated with devices.

    This endpoint fetches notes linked to devices and allows filtering by device ID.
    If no notes match the criteria, a 404 response is returned.

    """
    logger.info(
        f"GET request to retrieve device notes filtered by user ID: {device_id}.")
    
    return mdevice.DeviceNote.get_dev_notes(db, device_id)


@router.get("/devices/{note_id}", response_model=schemas.DeviceNote, responses={
    404: {
        "description": "If no device note with the given ID exists",
        "content": {
            "application/json": {
                "example": {
                    "detail": "No device note found"
                }
            }
        }
    },
})
def get_device_notes_id(
        response: Response,
        note_id: int,
        current_concierge: muser.User = Depends(oauth2.get_current_concierge),
        db: Session = Depends(database.get_db)) -> schemas.DeviceNote:
    """
    Retrieve a specific device-related note by its unique ID.

    This endpoint fetches a note associated with a device, identified by its unique ID.
    If the note does not exist in the database, a 404 error is returned with a descriptive message.

    """
    logger.info(
        f"GET request to retrieve device notes filtered by note ID: {note_id}.")
    
    return mdevice.DeviceNote.get_device_note_id(db, note_id)


@router.post("/devices", response_model=schemas.DeviceNoteOut, status_code=status.HTTP_201_CREATED, responses={
    500: {
        "description": "If an error occurs during the commit",
        "content": {
            "application/json": {
                "example": {
                    "detail": "An internal error occurred while creating note"
                }
            }
        }
    },
})
def add_device_note(note_data: schemas.DeviceNote,
                    response: Response,
                    current_concierge: muser.User = Depends(
                        oauth2.get_current_concierge),
                    db: Session = Depends(database.get_db)) -> schemas.DeviceNoteOut:
    """
    Create a new note associated with a specific device.

    This endpoint allows authenticated users to add a note to a device. The note is 
    linked to the specified device and stored in the database.

    Upon successful creation, the newly added note is returned. If an error occurs 
    during the database operation, an error is returned.

    """
    logger.info("POST request to create device note")
    
    return mdevice.DeviceNote.create_dev_note(db, note_data)


@router.put("/devices/{note_id}", response_model=schemas.DeviceNoteOut, responses={
    500: {
        "description": "If an error occurs during the commit",
        "content": {
            "application/json": {
                "example": {
                    "detail": "An internal error occurred while updating device note"
                }
            }
        }
    },
    404: {
        "description": "If the note with the given ID does not exist.",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Note not found"
                }
            }
        }
    },
    204: {
        "description": "If the note is deleted due to `None` content",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Note deleted"
                }
            }
        }
    },
})
def edit_device_note(note_id: int,
                     response: Response,
                     note_data: schemas.NoteUpdate,
                     current_concierge: muser.User = Depends(
                         oauth2.get_current_concierge),
                     db: Session = Depends(database.get_db)) -> schemas.DeviceNoteOut:
    """
    Update or delete an existing device-related note.

    This endpoint allows authenticated users to update a device note by its unique ID. 
    The updated content is provided in the request body. If the updated content is `None`, 
    the note is deleted from the database.

    """
    logger.info("PUT request to edit device note")
    
    return mdevice.DeviceNote.update_dev_note(db, note_id, note_data)


@router.delete("/devices/{note_id}", status_code=status.HTTP_204_NO_CONTENT, responses={
    500: {
        "description": "If an error occurs during the commit",
        "content": {
            "application/json": {
                "example": {
                    "detail": "An internal error occurred while deleting device note"
                }
            }
        }
    },
    404: {
        "description": "If the note with the given ID does not exist.",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Note not found"
                }
            }
        }
    },
})
def delete_device_note(note_id: int,
                       response: Response,
                       db: Session = Depends(database.get_db),
                       current_concierge: muser.User = Depends(oauth2.get_current_concierge)):
    """
    Delete a device note by its unique ID.

    This endpoint removes a specific note from the database. If the note does not exist,
    a 404 response is returned.

    """
    logger.info(
        f"DELETE request to delete device note with ID: {note_id}")
    
    return mdevice.DeviceNote.delete_dev_note(db, note_id)
