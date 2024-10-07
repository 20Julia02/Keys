from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from app import models
from app.schemas import DeviceUnapproved, DeviceOut, DeviceCreate


class DeviceService:
    def __init__(self, db: Session):
        self.db = db

    def create_dev(self, device: DeviceCreate, commit: bool = True) -> DeviceOut:
        new_device = models.Device(**device.model_dump())
        self.db.add(new_device)
        if commit:
            self.db.commit()
        return new_device

    def get_dev_code(self, dev_code: str) -> DeviceOut:
        device = self.db.query(models.Device).filter(models.Device.code == dev_code).first()
        if not device:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Device with code: {dev_code} doesn't exist")
        return device

    def get_all_devs(self, dev_type: Optional[str] = None, dev_version: Optional[str] = None) -> List[DeviceOut]:
        query = self.db.query(models.Device)
        if dev_type:
            if dev_type not in [dev_type.value for dev_type in models.DeviceType]:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail=f"Invalid device type: {dev_type}")
            query = query.filter(models.Device.dev_type == models.DeviceType[dev_type])
        if dev_version:
            if dev_version not in [version.value for version in models.DeviceVersion]:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail=f"Invalid device version: {dev_version}")
            query = query.filter(models.Device.version == models.DeviceVersion[dev_version])
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

    def create_unapproved(self, new_data: dict, commit: bool = True) -> DeviceUnapproved:
        new_device = models.DeviceUnapproved(**new_data)
        self.db.add(new_device)
        if commit:
            self.db.commit()
        return new_device

    def get_unapproved_dev_session(self, issue_return_session_id: int) -> List[DeviceUnapproved]:
        unapproved_devs = self.db.query(models.DeviceUnapproved).filter_by(issue_return_session_id=issue_return_session_id).all()
        if not unapproved_devs:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="No unapproved devices found for this session")
        return unapproved_devs

    def get_unapproved_dev_all(self) -> List[DeviceUnapproved]:
        unapproved_devs = self.db.query(models.DeviceUnapproved).all()
        if not unapproved_devs:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No unapproved devices found")
        return unapproved_devs

    def transfer_devices(self, issue_return_session_id: int = None, commit: bool = True) -> bool:
        dev_service = DeviceService(self.db)
        unapproved_devs = (
            self.get_unapproved_dev_session(issue_return_session_id) if issue_return_session_id
            else self.get_unapproved_dev_all()
        )

        if not unapproved_devs:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="There is no unapproved device in database")

        for unapproved in unapproved_devs:
            device = dev_service.get_dev_code(unapproved.device_code)
            device.is_taken = unapproved.is_taken
            device.last_taken = unapproved.last_taken
            device.last_returned = unapproved.last_returned
            device.last_owner_id = unapproved.last_owner_id

            operation_type = (
                models.OperationType.issue_dev if device.is_taken else models.OperationType.return_dev
            )

            device_session = models.DeviceOperation(
                device_code=unapproved.device_code,
                issue_return_session_id=unapproved.issue_return_session_id,
                operation_type=operation_type
            )

            self.db.add(device_session)
            self.db.delete(unapproved)

        try:
            if commit:
                self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Error during device transfer: {str(e)}")
        return True
