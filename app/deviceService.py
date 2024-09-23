from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List
from . import models
from sqlalchemy import cast, String
from .schemas import DeviceUnapproved, DeviceOut, DeviceCreate


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

    def get_dev_id(self, dev_id: int) -> DeviceOut:
        """
        Retrieves a device from the devices table by its ID.

        Args:
            device_id: The ID of the device to retrieve.

        Returns:
            The device object if found.

        Raises:
            HTTPException: If the device is not found, a 404 error is raised.
        """
        device = self.db.query(models.Devices).filter(models.Devices.id == dev_id).first()
        if not device:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Device with id: {dev_id} doesn't exist")
        return device

    def get_all_devs(self, dev_type="") -> List[DeviceOut]:
        """
        Retrieves all devices from the database that match the specified type.

        Args:
            current_concierge: The current user object (used for authorization).
            type (str): The type of device to filter by.
            db (Session): The database session.

        Returns:
            List[DeviceOut]: A list of devices that match the specified type.

        Raises:
            HTTPException: If no devices are found in the database.
        """
        if dev_type:
            dev = self.db.query(models.Devices).filter(cast(models.Devices.type, String).contains(dev_type)).all()
        else:
            dev = self.db.query(models.Devices).all()
        if not dev:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="There are no devices of the given type in the database")
        return dev


class UnapprovedDeviceService:
    def __init__(self, db: Session):
        self.db = db

    def get_dev_id(self, dev_id: int) -> models.DevicesUnapproved:
        """
        Retrieves a device from the unapproved devices table by its ID.

        Args:
            device_id: The ID of the device to retrieve.

        Returns:
            The unapproved device object if found.

        Raises:
            HTTPException: If the unapproved device is not found, a 404 error is raised.
        """
        device = self.db.query(models.DevicesUnapproved).filter(models.DevicesUnapproved.device_id == dev_id).first()
        if not device:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Device with id: {dev_id} doesn't exist")
        return device

    def create_unapproved(self, dev_id: int,
                          activity_id: int) -> DeviceUnapproved:
        """
        Clones a device from the approved devices table to the unapproved devices table.

        Args:
            device: The device object to clone.
            activity_id: The ID of the associated activity.

        Returns:
            The newly created unapproved device object.
        """
        device_service = DeviceService(self.db)
        device = device_service.get_dev_id(dev_id)
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

    def update_device_status(self, dev_id: int, new_data: dict) -> DeviceUnapproved:
        """
        Updates the status of a device in the unapproved devices table.

        Args:
            device: The unapproved device object to update.
            new_data: A dictionary containing the updated data.

        Returns:
            DeviceUnapproved: The updated unapproved device object.
        """
        device = self.get_dev_id(dev_id)
        for key, value in new_data.items():
            setattr(device, key, value)
        self.db.commit()
        self.db.refresh(device)
        return device

    def get_unapproved_dev_activity(self, activity_id: int) -> List[DeviceUnapproved]:
        """
        Returns every unapproved devices with given activity ID.

        Args:
            activity_id (int): activity ID associated with the unapproved devices

        Raises:
            HTTPException: if there is no unaproved devices in database associated with given activity ID

        Returns:
            List[DeviceUnapproved]: List of unapproved devices with given activity ID
        """
        unapproved_devs = self.db.query(models.DevicesUnapproved).filter_by(activity_id=activity_id).all()
        if not unapproved_devs:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="No unapproved devices found for this activity")
        return unapproved_devs

    def get_unapproved_dev_all(self) -> List[DeviceUnapproved]:
        """
        Returns every unapproved devices that are in database

        Raises:
            HTTPException: if there is no unaproved devices in database

        Returns:
            List[DeviceUnapproved]: List of unapproved devices
        """
        unapproved_devs = self.db.query(models.DevicesUnapproved).all()
        if not unapproved_devs:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No unapproved devices found")
        return unapproved_devs

    def transfer_devices(self, unapproved_devs: List[DeviceUnapproved]) -> bool:
        """
        Changes the data in the table of Devices according to the given data of unapproved devices

        Args:
            unapproved_devs (List[models.DevicesUnapproved]): List of the unapproved devices to transfer

        Raises:
            HTTPException: if there is no unapproved device in database
            HTTPException: if there is no device with given id in Devices table

        Returns:
            True if the unapproved devs were transformed to Devices table
        """
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
        return True
