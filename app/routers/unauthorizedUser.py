from fastapi import status, HTTPException, Depends, APIRouter

from ..schemas.unauthorizedUser import UnauthorizedUserCreate, UnauthorizedUserOut
from .. import database, models, utils, oauth2
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/unauthorizedUsers",
    tags=['UnauthorizedUsers']
)


@router.get("/{id}", response_model=UnauthorizedUserOut)
def get_user(id: int,
             current_user=Depends(oauth2.get_current_user),
             db: Session = Depends(database.get_db)):
    utils.check_if_entitled("concierge", current_user)
    user = db.query(models.UnauthorizedUsers).filter(
        models.UnauthorizedUsers.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Unauthorized user with id: {id} doesn't exist")
    return user


@router.post("/", response_model=UnauthorizedUserOut, status_code=status.HTTP_201_CREATED)
def create_user(user: UnauthorizedUserCreate,
                db: Session = Depends(database.get_db),
                current_user=Depends(oauth2.get_current_user)):
    utils.check_if_entitled("concierge", current_user)
    new_user = models.UnauthorizedUsers(**user.model_dump())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
