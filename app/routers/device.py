from fastapi import status, Depends, APIRouter, HTTPException
from typing import List
from ..schemas.device import DeviceCreate, DeviceOut
from .. import database, models, utils, oauth2
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/devices",
    tags=['Devices']
)


@router.get("/{dev_type}", response_model=List[DeviceOut])
def get_all_devices(dev_type: str,
                    current_user=Depends(oauth2.get_current_user),
                    db: Session = Depends(database.get_db)):
    dev = db.query(models.devices).filter(
        models.devices.type == dev_type).all()
    if dev is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"There is no {dev_type} in database")
    return dev


@router.get("/{dev_type}/{id}", response_model=DeviceOut)
def get_device(id: int,
               dev_type: str,
               current_user=Depends(oauth2.get_current_user),
               db: Session = Depends(database.get_db)):
    dev = db.query(models.devices).filter(models.devices.id ==
                                          id, models.devices.type == dev_type).first()
    if not dev:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"{dev_type} with id: {id} doesn't exist")
    return dev


@router.post("/", response_model=DeviceCreate, status_code=status.HTTP_201_CREATED)
def create_device(device: DeviceCreate,
                  db: Session = Depends(database.get_db),
                  current_user=Depends(oauth2.get_current_user)):
    utils.check_if_entitled("admin", current_user)
    new_device = models.devices(**device.model_dump())
    db.add(new_device)
    db.commit()
    db.refresh(new_device)
    return new_device
