import datetime
from fastapi import status, Depends, APIRouter, HTTPException
from typing import List

from sqlalchemy import cast, String
from ..schemas import DeviceCreate, DeviceOut
from .. import database, models, utils, oauth2
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter(
    prefix="/devices",
    tags=['Devices']
)


@router.get("/", response_model=List[DeviceOut])
def get_all_devices(current_concierge=Depends(oauth2.get_current_concierge),
                    type: str = "",
                    db: Session = Depends(database.get_db)) -> List[DeviceOut]:
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
    query = db.query(models.Devices)
    if type:
        query = query.filter(cast(models.Devices.type, String).contains(type))
    dev = query.all()
    if not dev:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"There are no devices of given type in the database")
    return dev


@router.get("/{id}", response_model=DeviceOut)
def get_device(id: int,
               current_concierge=Depends(oauth2.get_current_concierge),
               db: Session = Depends(database.get_db)) -> DeviceOut:
    """
    Retrieves a device by its ID from the database.

    Args:
        id (int): The ID of the device.
        current_concierge: The current user object (used for authorization).
        db (Session): The database session.

    Returns:
        DeviceOut: The device with the specified ID.

    Raises:
        HTTPException: If the device with the specified ID doesn't exist.
    """
    dev = db.query(models.Devices).filter(models.Devices.id ==
                                          id).first()
    if not dev:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Device with id: {id} doesn't exist")
    return dev


@router.post("/", response_model=DeviceOut, status_code=status.HTTP_201_CREATED)
def create_device(device: DeviceCreate,
                  db: Session = Depends(database.get_db),
                  current_concierge=Depends(oauth2.get_current_concierge)) -> DeviceOut:
    """
    Creates a new device in the database.

    Args:
        device (DeviceCreate): The data required to create a new device.
        db (Session): The database session.
        current_concierge: The current user object (used for authorization).

    Returns:
        DeviceOut: The newly created device.

    Raises:
        HTTPException: If the user is not authorized to create a device.
    """
    utils.check_if_entitled("admin", current_concierge)
    new_device = models.Devices(**device.model_dump())
    db.add(new_device)
    db.commit()
    db.refresh(new_device)
    return new_device


@router.patch("/changeStatus/{id}", response_model=DeviceOut)
def changeStatus(id: int,
                  db: Session = Depends(database.get_db),
                  current_concierge: int = Depends(oauth2.get_current_concierge)) -> DeviceOut:
    """
    Changes the status of a device (whether it is taken or not).

    Args:
        id (int): The ID of the device.
        db (Session): The database session.
        current_concierge: The current user object (used for authorization).

    Returns:
        DeviceOut: The updated device object.

    Raises:
        HTTPException: If the device with the specified ID doesn't exist.
        HTTPException: If an error occurs while updating the device status.
    """
    dev_query = db.query(models.Devices).filter(models.Devices.id == id)
    dev = dev_query.first()
    if not dev:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Device with id: {id} doesn't exist")
    if bool(dev.is_taken):
        new_data = {"is_taken": False, "last_returned": datetime.datetime.now(datetime.timezone.utc)}
    else:
        user_query = db.query(models.User).filter(
        models.User.is_active == True)
        if user_query.count()> 1:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="There are more than one active user")
        elif user_query.count()== 0:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="There is no active user")
        user = user_query.first()
        new_data = {"is_taken": True, "last_taken": datetime.datetime.now(datetime.timezone.utc), "last_owner_id": user.id}
       
    try:
        dev_query.update(new_data, synchronize_session=False)
        db.commit()
        db.refresh(dev)
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"An error occurred: {str(e)}")
    return dev
