from fastapi import status, HTTPException, Depends, APIRouter
from .. import schema, database, models, utils, oauth2
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/users",
    tags=['Users']
)


@router.get("/{id}", response_model=schema.UserOut)
def get_user(id: int,
             current_user=Depends(oauth2.get_current_user),
             db: Session = Depends(database.get_db)):
    utils.check_if_admin(current_user)
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User with id: {id} doesn't exist")
    return user


@router.post("/", response_model=schema.UserOut, status_code=status.HTTP_201_CREATED)
def create_user(user: schema.UserCreate,
                db: Session = Depends(database.get_db),
                current_user=Depends(oauth2.get_current_user)):
    utils.check_if_admin(current_user)
    hashed_password = utils.hash(user.password)
    user.password = hashed_password
    new_user = models.User(**user.model_dump())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
