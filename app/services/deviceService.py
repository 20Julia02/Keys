from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List
from app import models
from sqlalchemy import cast, String
from app.schemas import DeviceUnapproved, DeviceOut, DeviceCreate, DetailMessage


class DeviceService:
    def __init__(self, db: Session):
        self.db = db

    def create_dev(self, device: DeviceCreate) -> DeviceOut:
        """
        Creates a new device in the database.

        Args:
            device (DeviceCreate): The data required to create a new device.

        Returns:
            DeviceOut: The newly created device.
        """
        new_device = models.Devices(**device.model_dump())
        self.db.add(new_device)
        self.db.commit()
        self.db.refresh(new_device)
        return new_device

    def get_dev_code(self, dev_code: str) -> DeviceOut:
        """
        Retrieves a device from the devices table by its code.

        Args:
            device_code: The code of the device to retrieve.

        Returns:
            The device object if found.

        Raises:
            HTTPException: If the device is not found, a 404 error is raised.
        """
        device = self.db.query(models.Devices).filter(models.Devices.code == dev_code).first()
        if not device:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Device with code: {dev_code} doesn't exist")
        return device

    def get_all_devs(self, dev_type="", dev_version="") -> List[DeviceOut]:
        """
        Retrieves all devices from the database that match the specified type.

        Args:
            current_concierge: The current user object (used for authorization).
            type (str): The type of device to filter by.
            version (str): The version of device to filter by.
            db (Session): The database session.

        Returns:
            List[DeviceOut]: A list of devices that match the specified type.

        Raises:
            HTTPException: If no devices are found in the database.
        """
        if dev_type:
            dev = self.db.query(models.Devices).filter(cast(models.Devices.type, String).contains(dev_type), 
                                                       cast(models.Devices.version, String).contains(dev_version)).all()
        else:
            dev = self.db.query(models.Devices).all()
        if not dev:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="There are no devices of the given type and version in the database")
        return dev


class UnapprovedDeviceService:
    def __init__(self, db: Session):
        self.db = db

    def get_dev_code(self, dev_code: str) -> models.DevicesUnapproved:
        device = self.db.query(models.DevicesUnapproved).filter(models.DevicesUnapproved.device_code == dev_code).first()
        if not device:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Device with id: {dev_code} doesn't exist")
        return device
    
    def create_unapproved(self, dev_code: str,
                            activity_id: int,
                            new_data: dict = None)-> DeviceUnapproved:
        new_device = models.DevicesUnapproved(
            device_code=dev_code,
            activity_id=activity_id
        )
        if new_data is not None:
            for key, value in new_data.items():
                setattr(new_device, key, value)
        self.db.add(new_device)
        self.db.commit()
        self.db.refresh(new_device)

        return new_device

    def get_unapproved_dev_activity(self, activity_id: int) -> List[DeviceUnapproved]:
        unapproved_devs = self.db.query(models.DevicesUnapproved).filter_by(activity_id=activity_id).all()
        if not unapproved_devs:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="No unapproved devices found for this activity")
        return unapproved_devs

    def get_unapproved_dev_all(self) -> List[DeviceUnapproved]:
        unapproved_devs = self.db.query(models.DevicesUnapproved).all()
        if not unapproved_devs:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No unapproved devices found")
        return unapproved_devs

    def transfer_devices(self, unapproved_devs: List[DeviceUnapproved]) -> bool:
        if not unapproved_devs:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="There is no unapproved device in database")
        for unapproved in unapproved_devs:
            device = self.db.query(models.Devices).filter_by(code=unapproved.device_code).first()
            if device:
                device.is_taken = unapproved.is_taken
                device.last_taken = unapproved.last_taken
                device.last_returned = unapproved.last_returned
                device.last_owner_id = unapproved.last_owner_id
            else:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device is not saved in database")
            self.db.delete(unapproved)
        self.db.commit()
        return True
