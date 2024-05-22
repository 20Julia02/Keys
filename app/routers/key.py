from fastapi import status, HTTPException, Depends, APIRouter
from .. import schema, database, models, utils, oauth2
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

router = APIRouter(
    prefix="/keys",
    tags=['Keys']
)


@router.get("/{id}", response_model=schema.KeyOut)
def get_key(id: int,
            current_user=Depends(oauth2.get_current_user),
            db: Session = Depends(database.get_db)):
    utils.check_if_admin(current_user)
    key = db.query(models.Key).filter(models.Key.id == id).first()
    if not key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Key with id: {id} doesn't exist")
    return key


@router.post("/", response_model=schema.KeyCreate, status_code=status.HTTP_201_CREATED)
def create_user(key: schema.KeyCreate,
                db: Session = Depends(database.get_db),
                current_user=Depends(oauth2.get_current_user)):
    utils.check_if_admin(current_user)
    try:
        new_key = models.Key(**key.model_dump())
        db.add(new_key)
        db.commit()
        db.refresh(new_key)
        return new_key
    except IntegrityError as e:
        print(f'Error: {e}')
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="This key already exists")
    except Exception as e:
        print(f'Unexpected Error: {e}')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="An unexpected error occurred")
