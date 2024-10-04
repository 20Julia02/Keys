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
    Retrieve all user notes from the database.

    Args:
        current_concierge: The currently authenticated concierge.
        db: The database session.

    Returns:
        A list of all user notes.
    """
    note_service = noteService.NoteService(db)
    return note_service.get_all_user_notes()


@router.get("/users/{user_id}", response_model=List[schemas.UserNote])
def get_user_note(user_id: int,
                  current_concierge=Depends(oauth2.get_current_concierge),
                  db: Session = Depends(database.get_db)) -> List[schemas.UserNote]:
    """
    Retrieve a specific user note by user ID.

    Args:
        user_id: The ID of the user.
        current_concierge: The currently authenticated concierge.
        db: The database session.

    Returns:
        The user note for the given user ID.
    """
    note_service = noteService.NoteService(db)
    return note_service.get_user_note_by_id(user_id)


@router.post("/users/{user_id}", response_model=schemas.UserNote)
def add_user_note(user_id: int,
                  note: str,
                  current_concierge=Depends(oauth2.get_current_concierge),
                  db: Session = Depends(database.get_db)) -> schemas.UserNote:
    """
    Create a new user note for a specific user.

    Args:
        user_id: The ID of the user.
        note: The note text.
        current_concierge: The currently authenticated concierge.
        db: The database session.

    Returns:
        The created user note.
    """
    note_service = noteService.NoteService(db)
    return note_service.create_user_note(user_id, note)


@router.get("/operations", response_model=List[schemas.OperationNote])
def get_all_operation_note(
        current_concierge=Depends(oauth2.get_current_concierge),
        db: Session = Depends(database.get_db)) -> List[schemas.OperationNote]:
    """
    Retrieve all operation notes from the database.

    Args:
        current_concierge: The currently authenticated concierge.
        db: The database session.

    Returns:
        A list of all operation notes.
    """
    note_service = noteService.NoteService(db)
    return note_service.get_all_operation_notes()


@router.get("/operations/{operation_id}", response_model=List[schemas.OperationNote])
def get_operation_note(operation_id: int,
                       current_concierge=Depends(oauth2.get_current_concierge),
                       db: Session = Depends(database.get_db)) -> List[schemas.OperationNote]:
    """
    Retrieve a specific operation note by operation ID.

    Args:
        operation_id: The ID of the operation.
        current_concierge: The currently authenticated concierge.
        db: The database session.

    Returns:
        The operation note for the given operation ID.
    """
    note_service = noteService.NoteService(db)
    return note_service.get_operation_note_by_id(operation_id)


@router.get("/devices/{dev_code}", response_model=List[schemas.OperationNote])
def get_dev_notes(dev_code: str,
                 current_concierge=Depends(oauth2.get_current_concierge),
                 db: Session = Depends(database.get_db)) -> List[schemas.OperationNote]:

    note_service = noteService.NoteService(db)
    return note_service.get_dev_notes_by_code(dev_code)


@router.post("/operations/{operation_id}", response_model=schemas.OperationNote)
def add_operation_note(operation_id: int,
                       note: str,
                       current_concierge=Depends(oauth2.get_current_concierge),
                       db: Session = Depends(database.get_db)) -> schemas.OperationNote:
    """
    Create a new operation note for a specific operation.

    Args:
        operation_id: The ID of the operation.
        note: The note text.
        current_concierge: The currently authenticated concierge.
        db: The database session.

    Returns:
        The created operation note.
    """
    note_service = noteService.NoteService(db)
    return note_service.create_operation_note(operation_id, note)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_unauthorized_user(note_id: int,
                             db: Session = Depends(database.get_db),
                             current_concierge=Depends(oauth2.get_current_concierge)):
    note = db.query(models.OperationNote).filter(
            models.OperationNote.id == note_id).first()

    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Note with id: {note_id} doesn't exist")

    db.delete(note)
    db.commit()