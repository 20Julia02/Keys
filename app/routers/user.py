from fastapi import status, HTTPException, Depends, APIRouter
from .. import schema, database, models, utils
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/users",
    tags=['Users']
)


@router.get("/{id}", response_model=schema.UserOut)
def get_user(id: int, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User with id: {id} doesn't exist")
    return user


@router.post("/", response_model=schema.UserOut, status_code=status.HTTP_201_CREATED)
def create_user(user: schema.UserCreate, db: Session = Depends(database.get_db)):
    hashed_password = utils.hash(user.password)
    user.password = hashed_password
    new_user = models.User(**user.model_dump())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
