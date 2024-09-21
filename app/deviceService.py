from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List
from . import models
from sqlalchemy import Column, Integer


class DeviceService:
    def __init__(self, db: Session):
        self.db = db

    def get_device(self, device_id: int) -> models.Devices:
        """
        Retrieves a device from the devices table by its ID.

        Args:
            device_id: The ID of the device to retrieve.

        Returns:
            The device object if found.

        Raises:
            HTTPException: If the device is not found, a 404 error is raised.
        """
        device = self.db.query(models.Devices).filter(models.Devices.id == device_id).first()
        if not device:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Device with id: {device_id} doesn't exist")
        return device

    def clone_device_to_unapproved(self, device: models.Devices,
                                   activity_id: Column[Integer]) -> models.DevicesUnapproved:
        """
        Clones a device from the approved devices table to the unapproved devices table.

        Args:
            device: The device object to clone.
            activity_id: The ID of the associated activity.

        Returns:
            The newly created unapproved device object.
        """
        new_device = models.DevicesUnapproved(
            device_id=device.id,
            is_taken=device.is_taken,
            last_taken=device.last_taken,
            last_returned=device.last_returned,
            last_owner_id=device.last_owner_id,
            activity_id=activity_id
        )
        self.db.add(new_device)
        self.db.commit()
        self.db.refresh(new_device)
        return new_device


class UnapprovedDeviceService:
    def __init__(self, db: Session):
        self.db = db

    def delete_if_rescaned(self, device_id: int) -> bool:
        """
        Deletes a device from the unapproved devices table if it exists.

        Args:
            device_id: The ID of the device to be deleted.

        Returns:
            True if the device was found and deleted, False otherwise.
        """
        device_query = self.db.query(models.DevicesUnapproved).filter(models.DevicesUnapproved.device_id == device_id)
        device = device_query.first()
        if device:
            self.db.delete(device)
            self.db.commit()
        return bool(device)

    def update_device_status(self, device: models.DevicesUnapproved, new_data: dict) -> models.DevicesUnapproved:
        """
        Updates the status of a device in the unapproved devices table.

        Args:
            device: The unapproved device object to update.
            new_data: A dictionary containing the updated data.

        Returns:
            The updated unapproved device object.
        """
        for key, value in new_data.items():
            setattr(device, key, value)
        self.db.commit()
        self.db.refresh(device)
        return device

    def unapproved_devices_activity(self, activity_id: int):
        unapproved_devs = self.db.query(models.DevicesUnapproved).filter_by(activity_id=activity_id).all()
        if not unapproved_devs:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="No unapproved devices found for this activity")
        return unapproved_devs

    def unapproved_devices_all(self):
        unapproved_devs = self.db.query(models.DevicesUnapproved).all()
        if not unapproved_devs:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No unapproved devices found")
        return unapproved_devs

    def transfer_devices(self, unapproved_devs: List[models.DevicesUnapproved]):
        if not unapproved_devs:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="There is no unapproved device in database")
        for unapproved in unapproved_devs:
            device = self.db.query(models.Devices).filter_by(id=unapproved.device_id).first()
            if device:
                device.is_taken = unapproved.is_taken
                device.last_taken = unapproved.last_taken
                device.last_returned = unapproved.last_returned
                device.last_owner_id = unapproved.last_owner_id
            else:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device is not saved in database")
            self.db.delete(unapproved)
        self.db.commit()
