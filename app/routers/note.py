import datetime
from fastapi import status, Depends, APIRouter, HTTPException
from typing import List
from app import database, models, oauth2, schemas
from app.services import securityService
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/notes",
    tags=['Notes']
)

@router.get("/users", response_model=List[schemas.UserNote])
def get_all_user_note(current_concierge=Depends(oauth2.get_current_concierge),
                  db: Session = Depends(database.get_db)) -> schemas.UserNote:
    notes = db.query(models.UserNote).all()
    if (notes is None):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="There is no user note in database")
    return notes

@router.get("/users/{user_id}", response_model=List[schemas.UserNote])
def get_user_note(user_id:int,
                      current_concierge=Depends(oauth2.get_current_concierge),
                      db: Session = Depends(database.get_db)) -> schemas.UserNote:
    note = db.query(models.UserNote).filter(models.UserNote.user_id == user_id).first()
    if (note is None):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User with id: {user_id} doesn't have note")
    return note


@router.post("/users/{user_id}", response_model=schemas.UserNote)
def add_user_note(user_id: int,
                  note: str,
                  current_concierge=Depends(oauth2.get_current_concierge),
                  db: Session = Depends(database.get_db)) -> schemas.UserNote:
    
    note_data = schemas.UserNote(
        user_id=user_id,
        note=note,
        time=datetime.datetime.now(datetime.timezone.utc)
    )

    new_note = models.UserNote(note_data)
    db.add(new_note)
    db.commit()
    db.refresh(new_note)
    return new_note


@router.get("/operations", response_model=List[schemas.OperationNote])
def get_all_operation_note(current_concierge=Depends(oauth2.get_current_concierge),
                  db: Session = Depends(database.get_db)) -> schemas.OperationNote:
    notes = db.query(models.OperationNote).all()
    if (notes is None):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="There is no operation note in database")
    return notes


@router.get("/operations/{operation_id}", response_model=List[schemas.UserNote])
def get_operation_note(operation_id:int,
                  current_concierge=Depends(oauth2.get_current_concierge),
                  db: Session = Depends(database.get_db)) -> schemas.UserNote:
    note = db.query(models.OperationNote).filter(models.OperationNote.operation_id == operation_id).first()
    if (note is None):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Operation with id: {operation_id} doesn't have note")
    return note


@router.post("/operations/{operation_id}", response_model=schemas.OperationNote)
def add_operation_note(operation_id: int,
                       note: str,
                       current_concierge=Depends(oauth2.get_current_concierge),
                       db: Session = Depends(database.get_db)) -> schemas.OperationNote:
    
    note_data = schemas.OperationNote(
        operation_id=operation_id,
        note=note,
        time=datetime.datetime.now(datetime.timezone.utc)
    )

    new_note = models.OperationNote(note_data)
    db.add(new_note)
    db.commit()
    db.refresh(new_note)
    return new_note
