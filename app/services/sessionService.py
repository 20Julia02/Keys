from sqlalchemy.orm import Session
import datetime
from zoneinfo import ZoneInfo
from app import models
from app.schemas import IssueReturnSession
from fastapi import status, HTTPException


class SessionService:
    def __init__(self, db: Session):
        self.db = db

    def create_session(self, user_id: int, concierge_id: int, commit: bool = True) -> IssueReturnSession:
        """
        Creates a new session in the database for a given user and concierge.

        Args:
            user_id (int): The ID of the user associated with the session.
            concierge_id (int): The ID of the concierge managing the session.

        Returns:
            int: The ID of the newly created session.
        """

        start_time = datetime.datetime.now(ZoneInfo("Europe/Warsaw"))
        new_session = models.IssueReturnSession(
            user_id=user_id,
            concierge_id=concierge_id,
            start_time=start_time,
            status=models.SessionStatus.in_progress
        )
        self.db.add(new_session)
        if commit:
            self.db.commit()
            self.db.refresh(new_session)
        return new_session

    def end_session(self, session_id: int, reject: str = False, commit: bool = True) -> IssueReturnSession:
        """
        Changes the status of the session to rejected or completed
        depending on the given value of the reject argument. The default
        (reject = False) changes the status to completed.

        Args:
            session_id (int): the ID of the session

        Returns:
            _type_: schemas.IssueReturnSession. The session with completed status

        Raises:
            HTTPException: If the session with given ID doesn't exist
        """
        session = self.db.query(models.IssueReturnSession).filter_by(id=session_id).first()
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="IssueReturnSession not found")
        session.status = models.SessionStatus.rejected if reject else models.SessionStatus.completed
        session.end_time = datetime.datetime.now(ZoneInfo("Europe/Warsaw"))
        if commit:
            self.db.commit()
            self.db.refresh(session)
        return session

    def get_session_id(self, session_id: int) -> IssueReturnSession:
        session = self.db.query(models.IssueReturnSession).filter(
                    models.IssueReturnSession.id == session_id
                ).first()

        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="IssueReturnSession doesn't exist")
        return session
