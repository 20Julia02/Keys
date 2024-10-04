import datetime
from fastapi import status, Depends, APIRouter, HTTPException
from typing import List
from app import database, oauth2, schemas, models
from app.services import noteService
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/notes",
    tags=['Notes']
)


@router.get("/users", response_model=List[schemas.UserNote])
def get_all_user_note(
        current_concierge=Depends(oauth2.get_current_concierge),
        db: Session = Depends(database.get_db)) -> List[schemas.UserNote]:
    """
    It fetches all user-related notes stored in the database. User notes
    typically contain important information associated with users.

    Args:
        current_concierge: The currently authenticated concierge.
        db (Session): The database session to perform the query.

    Returns:
        List[schemas.UserNote]: A list of notes linked to a specific users in the system.

    Raises:
        HTTPException: If an error occurs while retrieving the user notes.
    """
    note_service = noteService.NoteService(db)
    return note_service.get_all_user_notes()


@router.get("/users/{user_id}", response_model=List[schemas.UserNote])
def get_user_note(user_id: int,
                  current_concierge=Depends(oauth2.get_current_concierge),
                  db: Session = Depends(database.get_db)) -> List[schemas.UserNote]:
    """
    It allows to fetch all notes associated with a specific user
    based on the user ID.

    Args:
        user_id (int): The unique ID of the user whose notes are being requested.
        current_concierge: The currently authenticated concierge.
        db (Session): The database session to perform the query.

    Returns:
        List[schemas.UserNote]: A list of notes corresponding to the given user ID.
    
    Raises:
        HTTPException: If no notes are found for the specified user ID.
    """
    note_service = noteService.NoteService(db)
    return note_service.get_user_note_by_id(user_id)


@router.post("/users/{user_id}", response_model=schemas.UserNote)
def add_user_note(user_id: int,
                  note: str,
                  current_concierge=Depends(oauth2.get_current_concierge),
                  db: Session = Depends(database.get_db)) -> schemas.UserNote:
    """
    It allows to add a new note to a specific user.
    The note is stored in the database along with the user ID.

    Args:
        user_id: The ID of the user for whom the note is being created.
        note: The content of the note being added (text).
        current_concierge: The currently authenticated concierge creating the note.
        db: The database session to perform the operation.

    Returns:
        schemas.UserNote: The newly created note associated with the specified user.
    
    Raises:
        HTTPException: If the note creation fails for any reason.
    """
    note_service = noteService.NoteService(db)
    return note_service.create_user_note(user_id, note)


@router.get("/operations", response_model=List[schemas.OperationNote])
def get_all_operation_note(
        current_concierge=Depends(oauth2.get_current_concierge),
        db: Session = Depends(database.get_db)) -> List[schemas.OperationNote]:
    """
    It allows to retrieve all operation-related notes from the system.

    Args:
        current_concierge: The currently authenticated concierge making the request.
        db(Session): The database session to perform the query.

    Returns:
        List[schemas.OperationNote]: A list of all operation notes stored in the system.
    
    Raises:
        HTTPException: If the retrieval of operation notes fails.
    """
    note_service = noteService.NoteService(db)
    return note_service.get_all_operation_notes()


@router.get("/operations/{operation_id}", response_model=List[schemas.OperationNote])
def get_operation_note(operation_id: int,
                       current_concierge=Depends(oauth2.get_current_concierge),
                       db: Session = Depends(database.get_db)) -> List[schemas.OperationNote]:
    """
    It allows to retrieve all notes related to a specific operation
    identified by its unique operation ID.

    Args:
        operation_id(int): The unique ID of the operation.
        current_concierge: The currently authenticated concierge.
        db(Session): The database session to perform the query.

    Returns:
        List[schemas.OperationNote]: A list of notes associated with the specified operation.
    
    Raises:
        HTTPException: If no notes are found for the given operation ID.
    """
    note_service = noteService.NoteService(db)
    return note_service.get_operation_note_by_id(operation_id)


@router.get("/devices/{dev_code}", response_model=List[schemas.OperationNote])
def get_dev_notes(dev_code: str,
                 current_concierge=Depends(oauth2.get_current_concierge),
                 db: Session = Depends(database.get_db)) -> List[schemas.OperationNote]:
    """
    It fetches all notes associated with operations involving a specific device, identified
    by its unique code.

    Args:
        dev_code: The unique code of the device whose notes are being requested.
        current_concierge: The currently authenticated concierge making the request.
        db: The database session to perform the query.

    Returns:
        List[schemas.OperationNote]: A list of notes associated with the specified device.
    
    Raises:
        HTTPException: If no notes are found for the given device code.
    """
    note_service = noteService.NoteService(db)
    return note_service.get_dev_notes_by_code(dev_code)


@router.post("/operations/{operation_id}", response_model=schemas.OperationNote)
def add_operation_note(operation_id: int,
                       note: str,
                       current_concierge=Depends(oauth2.get_current_concierge),
                       db: Session = Depends(database.get_db)) -> schemas.OperationNote:
    
    """
    It allows to add a note to a specific operation. The operation is identified
    by its unique ID, and the note is saved in the database.

    Args:
        operation_id: The ID of the operation for which the note is being created.
        note: The text content of the note.
        current_concierge: The currently authenticated concierge creating the note.
        db: The database session to perform the operation.

    Returns:
        schemas.OperationNote: The newly created operation note.
    
    Raises:
        HTTPException: If the note creation process encounters an error.
    """

    note_service = noteService.NoteService(db)
    return note_service.create_operation_note(operation_id, note)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_operation_notes(note_id: int,
                             db: Session = Depends(database.get_db),
                             current_concierge=Depends(oauth2.get_current_concierge)):
    note = db.query(models.OperationNote).filter(
            models.OperationNote.id == note_id).first()

    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Note with id: {note_id} doesn't exist")

    db.delete(note)
    db.commit()