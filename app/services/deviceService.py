from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from app import models
from app.schemas import DeviceUnapproved, DeviceOut, DeviceCreate, DetailMessage


class DeviceService:
    def __init__(self, db: Session):
        self.db = db

    def create_dev(self, device: DeviceCreate, commit: bool=True) -> DeviceOut:
        """
        Creates a new device in the database.

        Args:
            device (DeviceCreate): The data required to create a new device.

        Returns:
            DeviceOut: The newly created device.
        """
        new_device = models.Device(**device.model_dump())
        self.db.add(new_device)
        if commit:
            self.db.commit()
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
        device = self.db.query(models.Device).filter(models.Device.code == dev_code).first()
        if not device:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Device with code: {dev_code} doesn't exist")
        return device

    def get_all_devs(self, dev_type: Optional[str] = None, dev_version: Optional[str] = None) -> List[DeviceOut]:
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
        query = self.db.query(models.Device)
    
        if dev_type:
            query = query.filter(models.Device.type.ilike(f"%{dev_type}%"))
        if dev_version:
            query = query.filter(models.Device.version.ilike(f"%{dev_version}%"))

        dev = query.all()

        if not dev:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="There are no devices that match the given criteria in the database")
        
        return dev


class UnapprovedDeviceService:
    def __init__(self, db: Session):
        self.db = db

    def get_dev_code(self, dev_code: str) -> models.DeviceUnapproved:
        device = self.db.query(models.DeviceUnapproved).filter(models.DeviceUnapproved.device_code == dev_code).first()
        if not device:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Device with id: {dev_code} doesn't exist")
        return device
    
    def create_unapproved(self, new_data: dict, commit: bool = True)-> DeviceUnapproved:
        new_device = models.DeviceUnapproved(**new_data)
        self.db.add(new_device)
        if commit:
            self.db.commit()
        return new_device

    def get_unapproved_dev_session(self, issue_return_session_id: int) -> List[DeviceUnapproved]:
        unapproved_devs = self.db.query(models.DeviceUnapproved).filter_by(issue_return_session_id=issue_return_session_id).all()
        if not unapproved_devs:
            print(issue_return_session_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="No unapproved devices found for this session")
        return unapproved_devs

    def get_unapproved_dev_all(self) -> List[DeviceUnapproved]:
        unapproved_devs = self.db.query(models.DeviceUnapproved).all()
        if not unapproved_devs:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No unapproved devices found")
        return unapproved_devs

    def transfer_devices(self, issue_return_session_id: Optional[int], commit: bool=True) -> bool:
        unapproved_devs = (
        self.get_unapproved_dev_session(issue_return_session_id) if issue_return_session_id
        else self.get_unapproved_dev_all()
    )
        
        if not unapproved_devs:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="There is no unapproved device in database")
        try:
            for unapproved in unapproved_devs:
                device = self.db.query(models.Device).filter_by(code=unapproved.device_code).first()

                if not device:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                        detail=f"Device with code {unapproved.device_code} is not saved in database")
                device.is_taken = unapproved.is_taken
                device.last_taken = unapproved.last_taken
                device.last_returned = unapproved.last_returned
                device.last_owner_id = unapproved.last_owner_id

                transaction_type = (
                    models.TransactionType.issue_dev if device.is_taken else models.TransactionType.return_dev
                )

                device_session = models.DeviceTransaction(
                    device_code=unapproved.device_code,
                    issue_return_session_id=unapproved.issue_return_session_id,
                    transaction_type=transaction_type
                )
                
                self.db.add(device_session)
                self.db.delete(unapproved)
                
            if commit:
                self.db.commit()

        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Error during device transfer: {str(e)}")

        return True
