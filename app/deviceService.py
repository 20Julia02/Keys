from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from . import models
from datetime import datetime

class DeviceService:
    def __init__(self, db: Session):
        self.db = db

    def delete_if_rescaned(self, device_id: int) -> bool:
        device_query = self.db.query(models.DevicesUnapproved).filter(models.DevicesUnapproved.id == device_id)
        device = device_query.first()
        if device:
            self.db.delete(device)
            self.db.commit()
            return True
        return False

    def get_device(self, device_id: int) -> models.Devices:
        device = self.db.query(models.Devices).filter(models.Devices.id == device_id).first()
        if not device:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Device with id: {id} doesn't exist")
        return device

    def get_active_user(self) -> models.User:
        user_query = self.db.query(models.User).filter(models.User.is_active == True)
        if user_query.count()> 1:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="There are more than one active user")
        elif user_query.count()== 0:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="There is no active user")
        user = user_query.first()
        return user

    def clone_device_to_unapproved(self, device: models.Devices) -> models.DevicesUnapproved:
        new_device = models.DevicesUnapproved(
            id=device.id,
            type=device.type,
            room_id=device.room_id,
            is_taken=device.is_taken,
            last_taken=device.last_taken,
            last_returned=device.last_returned,
            last_owner_id=device.last_owner_id,
            version=device.version,
            code=device.code
        )
        self.db.add(new_device)
        self.db.commit()
        self.db.refresh(new_device)
        return new_device

    def update_device_status(self, device: models.DevicesUnapproved, new_data: dict):
        for key, value in new_data.items():
            setattr(device, key, value)
        self.db.commit()
        self.db.refresh(device)
        return device