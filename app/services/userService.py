from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List
import app.models.user as muser

class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_all_users(self) -> List[muser.User]:
        user = self.db.query(muser.User).all()
        if (user is None):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="There is no user in database")
        return user

    def get_user_id(self, user_id: int) -> muser.User:
        user = self.db.query(muser.User).filter(muser.User.id == user_id).first()
        if (not user):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"User with id: {user_id} doesn't exist")
        return user
