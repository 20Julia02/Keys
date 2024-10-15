from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from typing import List, Optional
from app import models, schemas
from app.services import operationService
from sqlalchemy import String, func, case, and_, cast, Integer


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

    def create_dev(self, device: schemas.DeviceCreate, commit: bool = True) -> models.Device:
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

    def get_devs_filtered(self, dev_type: Optional[str] = None, dev_version: Optional[str] = None, room_number: Optional[str] = None) -> List[schemas.DeviceOutWithNote]:
        last_operation_subquery = (
            self.db.query(
                models.DeviceOperation.device_id,
                func.max(models.DeviceOperation.timestamp).label('last_operation_timestamp')
            )
            .group_by(models.DeviceOperation.device_id)
            .subquery()
        )

        query = (self.db.query(
            models.Device.id,
            models.Device.dev_type,
            models.Device.dev_version,
            models.Room.number.label("room_number"),
            case(
                (models.DeviceOperation.operation_type == models.OperationType.issue_device, True), 
                else_=False
            ).label('is_taken'),
            case(
                (func.count(models.DeviceNote.id) > 0, True), 
                else_=False
            ).label('has_note')
        )
        .join(models.Room, models.Device.room_id == models.Room.id)
        .outerjoin(
            last_operation_subquery, 
            models.Device.id == last_operation_subquery.c.device_id
        )
        .outerjoin(models.DeviceOperation, and_(
            models.Device.id == models.DeviceOperation.device_id,
            models.DeviceOperation.timestamp == last_operation_subquery.c.last_operation_timestamp
        ))
        .outerjoin(models.DeviceNote, models.Device.id == models.DeviceNote.device_id)
        )

        if dev_type:
            try:
                dev_type_enum = models.DeviceType[dev_type]
            except KeyError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail=f"Invalid device type: {dev_type}")
            query = query.filter(models.Device.dev_type == dev_type_enum)
            
        if dev_version:
            try:
                dev_version_enum = models.DeviceVersion[dev_version]
            except KeyError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail=f"Invalid device version: {dev_version}")
            query = query.filter(models.Device.dev_version ==dev_version_enum)

        if room_number:
            query = query.filter(models.Room.number == room_number)

        query = query.group_by(
            models.Device.id, models.Room.number, models.DeviceOperation.operation_type
        )

        numeric_part = func.regexp_replace(models.Room.number, '\D+', '', 'g')
        text_part = func.regexp_replace(models.Room.number, '\d+', '', 'g')

        query = query.order_by(
            case(
                (numeric_part != '', func.cast(numeric_part, Integer)),
                else_=None
            ).asc(),
            case(
                (numeric_part == '', text_part),
                else_=None
            ).asc(),
            text_part.asc()
        )

        devices = query.all()

        if not devices:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="There are no devices that match the given criteria in the database")

        return devices

    def get_devs_owned_by_user(self, user_id: int) -> List[models.DeviceOperation]:
        last_operation_subquery = (
            self.db.query(
                models.DeviceOperation.device_id,
                func.max(models.DeviceOperation.timestamp).label('last_operation_timestamp')
            )
            .join(models.IssueReturnSession, models.DeviceOperation.session_id == models.IssueReturnSession.id)
            .filter(models.IssueReturnSession.user_id == user_id)
            .group_by(models.DeviceOperation.device_id)
            .subquery()
        )

        query = (
            self.db.query(models.DeviceOperation)
            .join(last_operation_subquery, 
                (models.DeviceOperation.device_id == last_operation_subquery.c.device_id) & 
                (models.DeviceOperation.timestamp == last_operation_subquery.c.last_operation_timestamp)
            )
            .filter(models.DeviceOperation.operation_type == models.OperationType.issue_device)
            .order_by(models.DeviceOperation.timestamp.asc())
            .group_by(models.DeviceOperation.id)
        )

        operations = query.all()

        if not operations:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} doesn't have any devices"
            )
        
        return operations
