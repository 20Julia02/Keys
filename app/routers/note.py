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
    It fetches all user-related notes stored in the database. 

    User notes are filtered by user ID if provided.
    """
    logger.info(
        f"GET request to retrieve user notes filtered by user ID: {user_id}")
    oauth2.set_access_token_cookie(response, current_concierge.id, current_concierge.role.value, db)
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
    It fetches user-related note stored in the database with given note_id. 
    """
    logger.info(
        f"GET request to retrieve user notes filtered by note ID: {note_id}")
    oauth2.set_access_token_cookie(response, current_concierge.id, current_concierge.role.value, db)
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
    It allows to add a new note to a specific user.
    """
    logger.info("POST request to create user note")
    oauth2.set_access_token_cookie(response, current_concierge.id, current_concierge.role.value, db)
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
    Updates a user note by ID with new data, or deletes the note if the new content is None.
    """
    logger.info("PUT request to edit user note")
    oauth2.set_access_token_cookie(response, current_concierge.id, current_concierge.role.value, db)
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
    Retrieves all notes associated with a specified device.

    If a device ID is provided, only notes for that device are returned. 
    """
    logger.info(
        f"GET request to retrieve device notes filtered by user ID: {device_id}.")
    oauth2.set_access_token_cookie(response, current_concierge.id, current_concierge.role.value, db)
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
    Retrieves a specific note by its unique ID. 
    """
    logger.info(
        f"GET request to retrieve device notes filtered by note ID: {note_id}.")
    oauth2.set_access_token_cookie(response, current_concierge.id, current_concierge.role.value, db)
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
    It allows to add a note to a specific operation. The operation is identified
    by its unique ID, and the note is saved in the database.
    """
    logger.info("POST request to create device note")
    oauth2.set_access_token_cookie(response, current_concierge.id, current_concierge.role.value, db)
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
    Updates an existing device note with the specified ID.
    """
    logger.info("PUT request to edit device note")
    oauth2.set_access_token_cookie(response, current_concierge.id, current_concierge.role.value, db)
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
    Deletes a specific device note by its unique ID. 
    """
    logger.info(
        f"DELETE request to delete device note with ID: {note_id}")
    oauth2.set_access_token_cookie(response, current_concierge.id, current_concierge.role.value, db)
    return mdevice.DeviceNote.delete_dev_note(db, note_id)
