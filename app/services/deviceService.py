from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from typing import List, Optional
from app import models, schemas
from app.services import roomService


class DeviceService:
    def __init__(self, db: Session):
        self.db = db

    def get_dev_id(self, dev_id: int) -> models.Device:
        device = self.db.query(models.Device).filter(
            models.Device.id == dev_id).first()
        if not device:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Device with id: {dev_id} doesn't exist")
        return device

    def create_dev(self, device: schemas.DeviceCreate, commit: bool = True) -> schemas.DeviceOut:
        new_device = models.Device(**device.model_dump())
        self.db.add(new_device)
        if commit:
            self.db.commit()
            self.db.refresh(new_device)
        return new_device

    def get_dev_code(self, dev_code: str) -> schemas.DeviceOut:
        device = self.db.query(models.Device).filter(
            models.Device.code == dev_code).first()
        if not device:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Device with code: {dev_code} doesn't exist")
        return device

    def get_all_devs(self, dev_type: Optional[str] = None, dev_version: Optional[str] = None, room_number: Optional[str] = None) -> List[schemas.DeviceOut]:
        query = self.db.query(models.Device).join(models.Room, models.Device.room_id == models.Room.id)
        if dev_type:
            if dev_type not in [dev_type.value for dev_type in models.DeviceType]:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail=f"Invalid device type: {dev_type}")
            query = query.filter(models.Device.dev_type ==
                                 models.DeviceType[dev_type])
        if dev_version:
            if dev_version not in [version.value for version in models.DeviceVersion]:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail=f"Invalid device version: {dev_version}")
            query = query.filter(models.Device.version ==
                                 models.DeviceVersion[dev_version])
        if room_number:
            query = query.filter(models.Room.number == room_number)
        dev = query.order_by(models.Room.number).all()

        if not dev:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="There are no devices that match the given criteria in the database")

        return dev

    def get_dev_owned_by_user(self, user_id: int) -> List[schemas.DeviceOut]:
        devices = self.db.query(models.Device).filter(
            models.Device.last_owner_id == user_id, models.Device.is_taken == True).all()
        if not devices:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"User with id {user_id} doesn't have any devices")
        return devices


class UnapprovedDeviceService:
    def __init__(self, db: Session):
        self.db = db

    def get_dev_id(self, dev_id: int) -> models.DeviceUnapproved:
        device = self.db.query(models.DeviceUnapproved).filter(
            models.DeviceUnapproved.device_id == dev_id).first()
        if not device:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Device with id: {dev_id} doesn't exist")
        return device

    def create_unapproved(self, new_data: dict, commit: bool = True) -> schemas.DeviceUnapproved:
        new_device = models.DeviceUnapproved(**new_data)
        self.db.add(new_device)
        if commit:
            self.db.commit()
            self.db.refresh(new_device)

        return new_device

    def get_unapproved_dev_session(self, session_id: int) -> List[schemas.DeviceUnapproved]:
        unapproved_devs = self.db.query(models.DeviceUnapproved).filter(
            models.DeviceUnapproved.issue_return_session_id == session_id).all()
        if not unapproved_devs:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="No unapproved devices found for this session")
        return unapproved_devs

    def get_unapproved_dev_all(self) -> List[schemas.DeviceUnapproved]:
        unapproved_devs = self.db.query(models.DeviceUnapproved).all()
        if not unapproved_devs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="No unapproved devices found")
        return unapproved_devs

    def delete_if_rescanned(self, device_id: int, session_id: int):
        dev_unapproved = self.db.query(models.DeviceUnapproved).filter(models.DeviceUnapproved.device_id == device_id,
                                                                       models.DeviceUnapproved.issue_return_session_id == session_id).first()
        if dev_unapproved:
            self.db.delete(dev_unapproved)
            self.db.commit()
            return True
        return False

    def transfer_devices(self, issue_return_session_id: Optional[int] = None, commit: Optional[bool] = True) -> bool:
        dev_service = DeviceService(self.db)
        unapproved_devs = (
            self.get_unapproved_dev_session(issue_return_session_id) if issue_return_session_id
            else self.get_unapproved_dev_all()
        )

        if not unapproved_devs:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="There is no unapproved device in database")

        for unapproved in unapproved_devs:
            device = dev_service.get_dev_id(unapproved.device_id)
            device.is_taken = unapproved.is_taken
            device.last_taken = unapproved.last_taken
            device.last_returned = unapproved.last_returned
            device.last_owner_id = unapproved.last_owner_id

            operation_type = (
                models.OperationType.issue_dev if device.is_taken else models.OperationType.return_dev
            )

            device_session = models.DeviceOperation(
                device_id=unapproved.device_id,
                issue_return_session_id=unapproved.issue_return_session_id,
                operation_type=operation_type
            )

            self.db.add(device_session)
            self.db.delete(unapproved)

        try:
            if commit:
                self.db.commit()
                self.db.refresh(device_session)
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Error during device transfer: {str(e)}")
        return True
