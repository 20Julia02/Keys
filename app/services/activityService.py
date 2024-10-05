from sqlalchemy.orm import Session
import datetime
from app import models
from app.services import securityService
from app.schemas import Token, Activity
from fastapi import status, HTTPException


class ActivityService:
    def __init__(self, db: Session):
        self.db = db

    def create_activity(self, user_id: int, concierge_id: int) -> Activity:
        """
        Creates a new activity in the database for a given user and concierge.

        Args:
            user_id (int): The ID of the user associated with the activity.
            concierge_id (int): The ID of the concierge managing the activity.

        Returns:
            int: The ID of the newly created activity.
        """

        start_time = datetime.datetime.now(datetime.timezone.utc)
        new_activity = models.Activity(
            user_id=user_id,
            concierge_id=concierge_id,
            start_time=start_time,
            status=models.Status.in_progress
        )
        self.db.add(new_activity)
        self.db.commit()
        self.db.refresh(new_activity)
        return new_activity

    def end_activity(self, activity_id: int, reject: str = False) -> Activity:
        """
        Changes the status of the activity to rejected or completed
        depending on the given value of the reject argument. The default
        (reject = False) changes the status to completed.

        Args:
            activity_id (int): the ID of the activity

        Returns:
            _type_: schemas.Activity. The activity with completed status

        Raises:
            HTTPException: If the activity with given ID doesn't exist
        """
        activity = self.db.query(models.Activity).filter_by(id=activity_id).first()
        if not activity:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")
        activity.status = models.Status.rejected if reject else models.Status.completed
        activity.end_time = datetime.datetime.now(datetime.timezone.utc)
        self.db.commit()
        return activity

    def get_activity_id(self, activity_id: int) -> Activity:
        activity = self.db.query(models.Activity).filter(
                    models.Activity.id == activity_id
                ).first()

        if not activity:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Activity doesn't exist")
        return activity
