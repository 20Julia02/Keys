import datetime
from fastapi import status, Depends, APIRouter, HTTPException
from typing import List

from sqlalchemy import cast, String
from ..schemas.device import DeviceCreate, DeviceOut
from .. import database, models, utils, oauth2
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter(
    prefix="/devices",
    tags=['Devices']
)


@router.get("/", response_model=List[DeviceOut])
def get_all_devices(current_user=Depends(oauth2.get_current_user),
                    type: str = "",
                    db: Session = Depends(database.get_db)):
    dev = db.query(models.Devices).filter(
        cast(models.Devices.type, String).contains(type)).all()
    if dev is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"There is no {type} in database")
    return dev


@router.get("/{id}", response_model=DeviceOut)
def get_device(id: int,
               current_user=Depends(oauth2.get_current_user),
               db: Session = Depends(database.get_db)):
    dev = db.query(models.Devices).filter(models.Devices.id ==
                                          id).first()
    if not dev:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Device with id: {id} doesn't exist")
    return dev


@router.post("/", response_model=DeviceOut, status_code=status.HTTP_201_CREATED)
def create_device(device: DeviceCreate,
                  db: Session = Depends(database.get_db),
                  current_user=Depends(oauth2.get_current_user)):
    utils.check_if_entitled("admin", current_user)
    new_device = models.Devices(**device.model_dump())
    db.add(new_device)
    db.commit()
    db.refresh(new_device)
    return new_device


@router.patch("/changeStatus/{id}", response_model=DeviceOut)
def change_status(id: int,
                  db: Session = Depends(database.get_db),
                  current_user: int = Depends(oauth2.get_current_user)):
    dev_query = db.query(models.Devices).filter(models.Devices.id == id)
    dev = dev_query.first()
    if not dev:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Device with id: {id} doesn't exist")
    new_status = not bool(dev.is_taken)

    try:
        dev_query.update({"is_taken": new_status, "last_returned": datetime.datetime.now(
        )}, synchronize_session=False)
        db.commit()
        db.refresh(dev)
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"An error occurred: {str(e)}")
    return dev
