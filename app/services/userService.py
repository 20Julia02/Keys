from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List
from app import models

class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_all_users(self) -> List[models.User]:
        user = self.db.query(models.User).all()
        if (user is None):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="There is no user in database")
        return user

    def get_user_id(self, user_id: int) -> models.User:
        user = self.db.query(models.User).filter(models.User.id == user_id).first()
        if (not user):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"User with id: {user_id} doesn't exist")
        return user
