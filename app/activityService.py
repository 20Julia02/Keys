from sqlalchemy.orm import Session
import datetime
from . import models, securityService
from .schemas import Token
from fastapi import status, HTTPException

class ActivityService:
    def __init__(self, db: Session):
        """
        Initializes the ActivityService with a given database session.
        """
        self.db = db
    
    def create_activity(self, user_id: int, concierge_id: int) -> int:
        """
        Creates a new activity in the database for a given user and concierge.
        
        Args:
            user_id (int): The ID of the user associated with the activity.
            concierge_id (int): The ID of the concierge managing the activity.
        
        Returns:
            int: The ID of the newly created activity.
        """
        start_time = datetime.datetime.now(datetime.timezone.utc)
        new_activity = models.Activities(
            user_id=user_id, 
            concierge_id=concierge_id, 
            start_time=start_time, 
            status="in_progress"
        )
        self.db.add(new_activity)
        self.db.commit()
        self.db.refresh(new_activity)
        return new_activity.id
    
    def change_activity_status(self, activity_id: int):
        activity = self.db.query(models.Activities).filter_by(id=activity_id).first()
        if not activity:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")
        activity.status = models.Status.completed
        self.db.commit()
        return activity
    
    def validate_activity(self, token: Token) -> models.Activities:
        """
        Validates an activity based on the provided authentication token.

        The token is verified to retrieve the associated activity.

        Args:
            token (Token): The authentication token containing user and activity information.

        Returns:
            models.Activities: The activity associated with the token.

        Raises:
            HTTPException: If the activity associated with the token does not exist.
        """
        token_data = securityService.TokenService(self.db).verify_user_token(token.access_token)
        activity = self.db.query(models.Activities).filter(
                    models.Activities.id == token_data.activity
                ).first()

        if not activity:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Activity doesn't exist")
        return activity
    