from typing import Any
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app import schemas
import app.models.user as muser
import app.models.device as mdevice
import app.models.permission as mpermission
import app.models.operation as moperation
from datetime import datetime

client = TestClient(app)

# device routers

# get_devices_filtered
def test_get_all_devices(test_device: mdevice.Device,
                         test_device_microphone: mdevice.Device,
                         concierge_token: str):
    response = client.get(
        "/devices/", headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 2


def test_get_devices_type_version(test_device: mdevice.Device,
                                  test_device_microphone: mdevice.Device,
                                  concierge_token: str):
    response = client.get("/devices/?dev_type=klucz&dev_version=podstawowa",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert response.json()[0]["dev_type"] == "klucz"
    assert response.json()[0]["dev_version"] == "podstawowa"
    assert len(response.json()) == 1


def test_get_all_devices_room(test_device: mdevice.Device,
                              test_room: mdevice.Room,
                              test_device_microphone: mdevice.Device,
                              concierge_token: str):
    response = client.get(f"/devices/?room_number={test_room.number}",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert response.json()[0]["room_number"] == test_room.number
    assert len(response.json()) == 1


def test_get_all_devices_type_version_room(test_device: mdevice.Device,
                                           test_room: mdevice.Room,
                                           test_device_microphone: mdevice.Device,
                                           concierge_token: str):
    response = client.get(f"/devices/?dev_type=klucz&dev_version=podstawowa&room_number={test_room.number}",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert response.json()[0]["dev_type"] == "klucz"
    assert response.json()[0]["dev_version"] == "podstawowa"
    assert response.json()[0]["room_number"] == test_room.number
    assert response.json()[0]["owner_name"] == None
    assert response.json()[0]["owner_surname"] == None
    assert len(response.json()) == 1


def test_get_all_devices_invalid_type(test_device: mdevice.Device,
                                      test_device_microphone: mdevice.Device,
                                      concierge_token: str):

    response = client.get("/devices/?dev_type=computer",
                          headers={"Authorization": f"Bearer {concierge_token}"})

    assert response.status_code == 422


def test_get_all_devices_invalid_version(test_device: mdevice.Device,
                                         test_device_microphone: mdevice.Device,
                                         concierge_token: str):
    response = client.get("/devices/?dev_version=first",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 422


def test_get_all_devices_type_version_invalid(test_device: mdevice.Device,
                                              test_device_microphone: mdevice.Device,
                                              concierge_token: str):
    response = client.get("/devices/?dev_version=zapasowa&dev_type=pilot",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 204
    assert response.text == ""
    
# get_dev_code

def test_get_dev_by_code(test_device: mdevice.Device,
                         concierge_token: str):
    response = client.get(f"/devices/code/{test_device.code}",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert response.json()["dev_type"] == test_device.dev_type.value


def test_get_dev_by_invalid_code(concierge_token: str):
    response = client.get("/devices/code/-5",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 204
    assert response.text == ""

# get_dev_id

def test_get_dev_by_id(test_device: mdevice.Device,
                         concierge_token: str):
    response = client.get(f"/devices/{test_device.id}",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert response.json()["dev_type"] == test_device.dev_type.value


def test_get_dev_by_invalid_id(concierge_token: str):
    response = client.get("/devices/-5",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 204
    assert response.text == ""

# create_device

def test_create_device(test_room: mdevice.Room,
                       test_concierge: muser.User,
                       concierge_token: str):
    device_data: dict[str, Any] = {
        "room_id": test_room.id,
        "dev_version": "podstawowa",
        "dev_type": "mikrofon",
        "code": "123467"
    }

    response = client.post("/devices/", json=device_data,
                           headers={"Authorization": f"Bearer {concierge_token}"})

    assert response.status_code == 201
    assert response.json()["dev_type"] == "mikrofon"


def test_create_device_with_invalid_data(concierge_token: str):
    device_data: dict[str, Any] = {
        "is_taken": False,
        "room": 6
    }
    response = client.post("/devices/", json=device_data,
                           headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 422

# update_device

def test_update_device(test_room: mdevice.Room,
                       test_device: mdevice.Device,
                       test_concierge: muser.User,
                       concierge_token: str):
    device_data: dict[str, Any] = {
        "room_id": test_room.id,
        "dev_version": "zapasowa",
        "dev_type": "mikrofon",
        "code": test_device.code
    }

    response = client.post(f"/devices/{test_device.id}", json=device_data,
                           headers={"Authorization": f"Bearer {concierge_token}"})

    assert response.status_code == 200
    assert response.json()["dev_type"] == "mikrofon"
    assert response.json()["dev_version"] == "zapasowa"


def test_update_device_with_invalid_data(concierge_token: str, 
                                         test_device: mdevice.Device,):
    device_data: dict[str, Any] = {
        "is_taken": False,
        "room": 6
    }
    response = client.post(f"/devices/{test_device.id}", json=device_data,
                           headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 422


def test_update_device_with_duplicated_code(test_room: mdevice.Room,
                       test_device: mdevice.Device,
                       test_concierge: muser.User,
                       concierge_token: str):
    device_data: dict[str, Any] = {
        "room_id": test_room.id,
        "dev_version": "zapasowa",
        "dev_type": "mikrofon",
        "code": "123467"
    }

    response = client.post(f"/devices/{test_device.id}", json=device_data,
                           headers={"Authorization": f"Bearer {concierge_token}"})

    assert response.status_code == 500


def test_update_device_with_invalid_id(concierge_token: str, 
                                       test_room: mdevice.Room):
    device_data: dict[str, Any] = {
        "room_id": test_room.id,
        "dev_version": "zapasowa",
        "dev_type": "mikrofon",
        "code": "123487"
    }
    response = client.post("/devices/-5", json=device_data,
                           headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 404

#  delete_device

def test_delete_device_invalid_id(test_concierge: muser.User,
                                  concierge_token: str):
    response1 = client.delete("/devices/-5",
                           headers={"Authorization": f"Bearer {concierge_token}"})

    assert response1.status_code == 404


def test_delete_device(test_concierge: muser.User,
                       test_room: mdevice.Room,
                       concierge_token: str):
    device_data: dict[str, Any] = {
        "room_id": test_room.id,
        "dev_version": "zapasowa",
        "dev_type": "pilot",
        "code": "1234"
    }

    response = client.post("/devices/", json=device_data,
                           headers={"Authorization": f"Bearer {concierge_token}"})

    assert response.status_code == 201

    response = client.delete(f"/devices/{response.json()['id']}",
                           headers={"Authorization": f"Bearer {concierge_token}"})

    assert response.status_code == 204

# notes

# get_user_notes_filtered

def test_get_all_user_notes(concierge_token: str,
                            test_user_note: muser.UserNote):
    response = client.get("/notes/users",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["note"] == "Test Note"


def test_get_user_notes_user_id(test_user: muser.User,
                                concierge_token: str,
                                test_specific_user_note: muser.UserNote):
    response = client.get(f"/notes/users/?user_id={test_user.id}",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert response.json()[1]["note"] == "Test Specific Note"

def test_get_user_notes_invalid_user_id(concierge_token: str,
                                        test_specific_user_note: muser.UserNote):
    response = client.get("/notes/users/?user_id=-6",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 204
    assert response.text == ""

# get_user_notes_id

def test_get_user_notes_id(test_user: muser.User,
                           concierge_token: str,
                           test_specific_user_note: muser.UserNote):
    response = client.get(f"/notes/users/{test_specific_user_note.id}",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert response.json()["note"] == "Test Specific Note"


def test_get_user_notes_id_invalid(test_user: muser.User,
                                   concierge_token: str):
    response = client.get(f"/notes/users/-7",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 204
    assert response.text == ""

# add_user_note

def test_add_user_note(test_user: muser.User,
                       concierge_token: str):
    note_data: dict[str, Any] = {
        "user_id": test_user.id, "note": "New note for user"}
    response = client.post(f"/notes/users",
                           headers={
                               "Authorization": f"Bearer {concierge_token}"},
                           json=note_data)

    assert response.status_code == 201
    assert response.json()["note"] == "New note for user"


def test_add_user_note_invalid_data(test_user: muser.User,
                                    concierge_token: str):
    note_data = {"note": "Invalid note data"}
    response = client.post(f"/notes/users",
                           headers={
                               "Authorization": f"Bearer {concierge_token}"},
                           json=note_data)

    assert response.status_code == 422

# edit_user_note

def test_edit_user_note(test_user: muser.User,
                        concierge_token: str,
                        test_user_note: muser.UserNote):
    note_data: dict[str, Any] = {
        "note": "Edited note"}
    response = client.put(f"/notes/users/{test_user_note.id}",
                          headers={
        "Authorization": f"Bearer {concierge_token}"},
        json=note_data)

    assert response.status_code == 200
    assert response.json()["note"] == "Edited note"
    assert response.json()["user"]["id"] == test_user.id


def test_edit_user_note_invalid_data(test_user: muser.User,
                        concierge_token: str,
                        test_user_note: muser.UserNote):
    note_data: dict[str, Any] = {
        "user_id": test_user.id}
    response = client.put(f"/notes/users/{test_user_note.id}",
                          headers={
        "Authorization": f"Bearer {concierge_token}"},
        json=note_data)

    assert response.status_code == 422

# get_devices_notes_filtered

def test_get_all_device_notes(test_device_note: mdevice.DeviceNote,
                              concierge_token: str):
    response = client.get("/notes/devices",
                          headers={"Authorization": f"Bearer {concierge_token}"})

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["note"] == "Device note content"


def test_get_device_notes_dev_id(test_device: mdevice.Device,
                                 test_room: mdevice.Room,
                                 concierge_token: str):
    response = client.get(f"/notes/devices/?device_id={test_device.id}",
                          headers={"Authorization": f"Bearer {concierge_token}"})

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["note"] == "Device note content"
    assert response.json()[0]["device"]["room"]["number"] == test_room.number


def test_get_device_notes_not_found(concierge_token: str):
    response = client.get("/notes/devices/?device_id=-5",
                          headers={"Authorization": f"Bearer {concierge_token}"})

    assert response.status_code == 204
    assert response.text == ""

# get_device_notes_id

def test_get_device_notes_id(test_device: mdevice.Device,
                             test_device_note: mdevice.DeviceNote,
                             concierge_token: str):
    response = client.get(f"/notes/devices/{test_device_note.id}",
                          headers={"Authorization": f"Bearer {concierge_token}"})

    assert response.status_code == 200
    assert response.json()["note"] == "Device note content"


def test_get_device_notes_id_invalid(test_device: mdevice.Device,
                                     concierge_token: str):
    response = client.get("/notes/devices/-2",
                          headers={"Authorization": f"Bearer {concierge_token}"})

    assert response.status_code == 204
    assert response.text == ""

# add_device_note

def test_add_device_note(db: Session,
                         test_session: moperation.UserSession,
                         test_device: mdevice.Device,
                         concierge_token: str):
    note_data: dict[str, Any] = {"device_id": test_device.id,
                                 "note": "New note for device"}
    response = client.post("/notes/devices", json=note_data,
                           headers={"Authorization": f"Bearer {concierge_token}"})

    assert response.status_code == 201
    assert response.json()["note"] == "New note for device"


def test_add_device_note_invalid_data(concierge_token: str):
    note_data = {"note": "Invalid device note data"}
    response = client.post("/notes/devices", json=note_data,
                           headers={"Authorization": f"Bearer {concierge_token}"})

    assert response.status_code == 422

# edit_device_note

def test_edit_device_note(db: Session,
                          test_session: moperation.UserSession,
                          test_device: mdevice.Device,
                          concierge_token: str,
                          test_device_note: mdevice.DeviceNote):
    note_data: dict[str, Any] = {"device_id": test_device.id,
                                 "note": "Edited dev note"}
    response = client.put(f"/notes/devices/{test_device_note.id}", json=note_data,
                          headers={"Authorization": f"Bearer {concierge_token}"})

    assert response.status_code == 200
    assert response.json()["note"] == "Edited dev note"
    assert response.json()["device"]["id"] == test_device.id


def test_edit_device_note_invalid_data(test_device: mdevice.Device,
                        concierge_token: str,
                        test_user_note: muser.UserNote):
    note_data: dict[str, Any] = {
        "device_id": test_device.id}
    response = client.put(f"/notes/devices/{test_user_note.id}",
                          headers={
        "Authorization": f"Bearer {concierge_token}"},
        json=note_data)

    assert response.status_code == 422

# delete_device_note

def test_delete_device_note_invalid_id(db: Session,
                            concierge_token: str,
                            test_device_note: mdevice.DeviceNote):
    response = client.delete("/notes/devices/-5",
                             headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 404
    assert response.json()[
        "detail"] == f"Note not found"
    

def test_delete_device_note(db: Session,
                            concierge_token: str,
                            test_device: mdevice.DeviceNote,
                            test_device_note: mdevice.DeviceNote):
    response = client.delete(f"/notes/devices/{test_device_note.id}",
                             headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 204
    response = client.get(f"/notes/devices/{test_device_note.id}",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 204
    assert response.text == ""

# operation

#change-status

def test_changeStatus_invalid_session(test_device: mdevice.Device,
                                      test_concierge: muser.User,
                                      concierge_token: str):
    response = client.post("/operations/change-status",
                           headers={
                               "Authorization": f"Bearer {concierge_token}"},
                           json={"session_id": 0, "device_code": test_device.code})
    assert response.status_code == 404
    assert response.json()["detail"] == "Session doesn't exist"


def test_changeStatus_with_valid_id_taking(test_concierge: muser.User,
                                           test_user: muser.User,
                                           test_device: mdevice.Device,
                                           test_permission: mpermission.Permission,
                                           concierge_token: str):

    login_data = {
        "username": test_user.email,
        "password": "password456"
    }
    response1 = client.post("/start-session/login",
                            headers={"Authorization": f"Bearer {concierge_token}"}, data=login_data)
    assert response1.status_code == 200
    response = client.post("/operations/change-status",
                           headers={
                               "Authorization": f"Bearer {concierge_token}"},
                           json={"session_id": response1.json()["id"], "device_code": test_device.code})
    assert response.status_code == 200
    assert response.json()["device"]["code"] == test_device.code
    assert response.json()["session"]["status"] == "w trakcie"
    assert response.json()["operation_type"] == "pobranie"
    assert response.json()["entitled"] is True


def test_changeStatus_without_permission(test_concierge: muser.User,
                                         test_user: muser.User,
                                         test_device_microphone: mdevice.Device,
                                         test_permission: mpermission.Permission,
                                         test_room_2: mdevice.Room,
                                         concierge_token: str):

    login_data = {
        "username": test_user.email,
        "password": "password456"
    }
    response1 = client.post("/start-session/login",
                            headers={"Authorization": f"Bearer {concierge_token}"}, data=login_data)
    assert response1.status_code == 200
    response = client.post("/operations/change-status",
                           headers={
                               "Authorization": f"Bearer {concierge_token}"},
                           json={"session_id": response1.json()["id"], "device_code": test_device_microphone.code})
    assert response.status_code == 403
    assert response.json()[
        "detail"] == f"User has no permission to perform the operation"


def test_changeStatus_with_force(test_concierge: muser.User,
                                 test_user: muser.User,
                                 test_device_microphone: mdevice.Device,
                                 concierge_token: str):

    login_data = {
        "username": test_user.email,
        "password": "password456"
    }
    response1 = client.post("/start-session/login",
                            headers={"Authorization": f"Bearer {concierge_token}"}, data=login_data)
    assert response1.status_code == 200
    response = client.post("/operations/change-status",
                           headers={
                               "Authorization": f"Bearer {concierge_token}"},
                           json={"session_id": response1.json()["id"],
                                 "force": True,
                                 "device_code": test_device_microphone.code})
    assert response.status_code == 200
    assert response.json()["entitled"] is False
    assert response.json()["operation_type"] == "pobranie"


def test_changeStatus_again_return(test_concierge: muser.User,
                            test_user: muser.User,
                            test_device: mdevice.Device,
                            concierge_token: str):

    login_data = {
        "username": test_user.email,
        "password": "password456"
    }

    response1 = client.post("/start-session/login",
                            headers={"Authorization": f"Bearer {concierge_token}"}, data=login_data)
    assert response1.status_code == 200

    client.post("/operations/change-status",
                headers={"Authorization": f"Bearer {concierge_token}"},
                json={"session_id": response1.json()["id"],
                      "device_code": test_device.code})

    response = client.post("/operations/change-status",
                           headers={
                               "Authorization": f"Bearer {concierge_token}"},
                           json={"session_id": response1.json()["id"],
                                 "device_code": test_device.code})
    assert response.json()["detail"] == "Operation removed."


def test_changeStatus_again_issue(test_concierge: muser.User,
                            test_user: muser.User,
                            test_device_microphone: mdevice.Device,
                            concierge_token: str,
                            test_permission_2: mpermission.Permission):

    login_data = {
        "username": test_user.email,
        "password": "password456"
    }

    response1 = client.post("/start-session/login",
                            headers={"Authorization": f"Bearer {concierge_token}"}, data=login_data)
    assert response1.status_code == 200

    client.post("/operations/change-status",
                headers={"Authorization": f"Bearer {concierge_token}"},
                json={"session_id": response1.json()["id"],
                      "device_code": test_device_microphone.code})

    response = client.post("/operations/change-status",
                           headers={
                               "Authorization": f"Bearer {concierge_token}"},
                           json={"session_id": response1.json()["id"],
                                 "device_code": test_device_microphone.code})
    assert response.json()["detail"] == "Operation removed."


def test_all_change_status(test_user: muser.User,
                           test_concierge: muser.User,
                           concierge_token: str,
                           test_device: mdevice.Device):
    login_data = {
        "username": test_user.email,
        "password": "password456"
    }
    login_data_concierge = {
        "username": test_concierge.email,
        "password": "password123"
    }
    response_start_session = client.post("/start-session/login",
                            headers={"Authorization": f"Bearer {concierge_token}"}, data=login_data)
    assert response_start_session.status_code == 200
    response_change_status = client.post("/operations/change-status",
                           headers={
                               "Authorization": f"Bearer {concierge_token}"},
                           json={"session_id": response_start_session.json()["id"],
                                 "device_code": test_device.code})
    assert response_change_status.status_code == 200
    assert response_change_status.json()["device"]["code"] == test_device.code
    assert response_change_status.json()["session"]["status"] == "w trakcie"
    assert response_change_status.json()["operation_type"] == "pobranie"
    assert response_change_status.json()["entitled"] is True

    response_approve = client.post(
        f"/approve/login/session/{response_start_session.json()['id']}",
        headers={"Authorization": f"Bearer {concierge_token}"},
        data=login_data_concierge
    )
    assert response_approve.status_code == 200
    assert response_approve.json()[0]["operation_type"] == "pobranie"


# get_devs_owned_by_user

def test_get_all_user_devices(db: Session,
                              test_user: muser.User,
                              test_concierge: muser.User,
                              test_device: mdevice.Device,
                              concierge_token: str):
    session = moperation.UserSession.create_session(
        db, test_user.id, test_concierge.id)
    new_data = schemas.DevOperation(device_id=test_device.id,
                                    session_id=session.id,
                                    operation_type="pobranie",
                                    entitled=False)
    moperation.DeviceOperation.create_operation(db, new_data)
    response = client.get(f"/operations/users/{test_user.id}",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert response.json()[0]['session']['user_id'] == test_user.id
    assert response.json()[0]['operation_type'] == "pobranie"


def test_get_all_user_devices_no_device(db: Session,
                                        test_user: muser.User,
                                        test_concierge: muser.User,
                                        test_device: mdevice.Device,
                                        concierge_token: str):
    session = moperation.UserSession.create_session(
        db, test_user.id, test_concierge.id)
    new_data = schemas.DevOperation(device_id=test_device.id,
                                    session_id=session.id,
                                    operation_type="pobranie",
                                    entitled=False)
    moperation.DeviceOperation.create_operation(db, new_data)
    response = client.get(f"/operations/users/{test_concierge.id}",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 204
    assert response.text == ""


def test_get_all_user_devices_invalid_id(db: Session,
                                        test_user: muser.User,
                                        test_concierge: muser.User,
                                        test_device: mdevice.Device,
                                        concierge_token: str):
    response = client.get(f"/operations/users/-5",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 204
    assert response.text == ""

# get_unapproved_operations

def test_get_unapproved_operations(db: Session, 
                                              concierge_token: str):
    response = client.get("/operations/unapproved", 
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert len(response.json()) > 0


def test_get_unapproved_operations_with_session(db: Session, 
                                                concierge_token: str, 
                                                test_session: moperation.UserSession, 
                                                test_operation: moperation.DeviceOperation):
    response = client.get(f"/operations/unapproved?session_id={test_session.id}", 
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 204
    assert response.text == ""


def test_get_unapproved_operations_with_type_filter(db: Session, 
                                                    concierge_token: str, 
                                                    test_session: moperation.UserSession, 
                                                    test_operation: moperation.DeviceOperation):
    response = client.get(f"/operations/unapproved?operation_type=pobranie", 
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert all(op["operation_type"] == "pobranie" for op in response.json())


# get_operations_filtered

def test_get_operations_no_results(db: Session, 
                                   concierge_token: str):
    response = client.get("/operations?session_id=-5", 
                          headers={"Authorization": f"Bearer {concierge_token}"})

    assert response.status_code == 204
    assert response.text == ""


def test_get_operations_all(db: Session, 
                            concierge_token: str):
    response = client.get("/operations", 
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert len(response.json()) > 0 


def test_get_operations_filtered(db: Session, 
                                 concierge_token: str, 
                                 test_session: moperation.UserSession):
    response = client.get(f"/operations?session_id={test_session.id}", 
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert all(op["session"]["id"] == test_session.id for op in response.json())

# get_operation_id

def test_get_operation_by_id(db: Session, 
                             concierge_token: str, 
                             test_operation: moperation.DeviceOperation):
    response = client.get(f"/operations/{test_operation.id}", 
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert response.json()["id"] == test_operation.id


def test_get_operation_by_invalid_id(db: Session, 
                             concierge_token: str):
    response = client.get("/operations/9999", 
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 204
    assert response.text == ""

#get_last_dev_operation_or_none

def test_get_last_dev_operation(db: Session,
                                concierge_token: str, 
                                test_device: mdevice.Device, 
                                test_operation: moperation.DeviceOperation):
    response = client.get(f"/operations/device/{test_device.id}", 
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert response.json()["device"]["id"] == test_device.id
    assert response.json()["id"] == test_operation.id

def test_get_last_dev_operation_invalid_id(db: Session,
                                     concierge_token: str, 
                                     test_device: mdevice.Device):
    response = client.get(f"/operations/device/-5", 
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 204
    assert response.text == ""

# get_permissions

def test_get_permission_with_valid_user_surname(db: Session,
                                           test_concierge: muser.User,
                                           test_user: muser.User,
                                           test_room: mdevice.Room,
                                           concierge_token: str):
    response = client.get(
        f"/permissions?surname={test_user.surname}",
        headers={"Authorization": f"Bearer {concierge_token}"}
    )
    assert response.status_code == 200
    assert response.json()[0]["user"]["id"] == test_user.id


def test_get_permission_with_invalid_user_surname(test_concierge: muser.User,
                                             concierge_token: str):
    response = client.get("/permissions?surname=-1",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 204
    assert response.text == ""


def test_get_permission_with_valid_room_id(db: Session,
                                           test_concierge: muser.User,
                                           test_room: mdevice.Room,
                                           concierge_token: str):
    response = client.get(
        f"/permissions?room_id={test_room.id}",
        headers={"Authorization": f"Bearer {concierge_token}"}
    )
    assert response.status_code == 200
    assert response.json()[0]["room"]["id"] == test_room.id


def test_get_permission_with_invalid_room_id(test_concierge: muser.User,
                                             concierge_token: str):
    response = client.get("/permissions?room_id=-1",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 204
    assert response.text == ""


def test_get_permission_with_room_user_id(test_concierge: muser.User,
                                          test_user: muser.User,
                                          test_room: mdevice.Room,
                                          concierge_token: str):
    response = client.get(f"/permissions?room_id={test_room.id}&user_id={test_user.id}",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["room"]["id"] == test_room.id
    assert response.json()[0]["user"]["id"] == test_user.id


def test_get_permission_with_date_start_time(test_concierge: muser.User,
                                             test_permission: mpermission.Permission,
                                             concierge_token: str):
    response = client.get(f"/permissions?date={test_permission.date}&start_time={test_permission.start_time}",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200

    response_data = response.json()[0]

    assert datetime.strptime(response_data["date"], '%Y-%m-%d').date() == test_permission.date
    assert datetime.strptime(response_data["start_time"], '%H:%M:%S.%f').time() == test_permission.start_time
    assert len(response.json()) == 1


def test_get_permission_with_invalid_date(test_concierge: muser.User,
                                             test_permission: mpermission.Permission,
                                             concierge_token: str):
    
    response = client.get(f"/permissions?date=2024-10-10&start_time={test_permission.start_time}",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 204
    assert response.text == ""

# create_permission

def test_create_permission_success(concierge_token: str,
                                   test_user: muser.User,
                                   test_room: mdevice.Room):

    valid_permission_data: dict[str, Any] = {
        "user_id": test_user.id,
        "room_id": test_room.id,
        "date": '2024-12-04',
        "start_time": "10:00:00",
        "end_time": "12:00:00"
    }
    response = client.post("/permissions/", json=valid_permission_data,
                           headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 201
    assert response.json()["user"]["id"] == valid_permission_data["user_id"]
    assert response.json()["room"]["id"] == valid_permission_data["room_id"]


def test_create_permission_invalid_data(concierge_token: str):

    valid_permission_data: dict[str, Any] = {
        "user_id": 1,
        "room_id": 101
    }
    response = client.post("/permissions/", json=valid_permission_data,
                           headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 422

# update_permission

def test_update_permission_success(test_permission: mpermission.Permission, 
                                   concierge_token: str,
                                   test_user: muser.User,
                                   test_room: mdevice.Room):
    updated_permission: dict[str, Any] = {
        "user_id":test_user.id,
        "room_id":test_room.id,
        "date":'2024-03-12',
        "start_time":"10:00:00",
        "end_time":"13:00:00"
        }
    
    response = client.post(f"/permissions/update/{test_permission.id}", json=updated_permission,
                           headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert response.json()["start_time"] == "10:00:00"


def test_update_permission_invalid_id(test_permission: mpermission.Permission, 
                                   concierge_token: str,
                                                                      test_user: muser.User,
                                   test_room: mdevice.Room):
    updated_permission: dict[str, Any] = {
        "user_id":test_user.id,
        "room_id":test_room.id,
        "date":'2024-03-12',
        "start_time":"10:00:00",
        "end_time":"13:00:00"
        }
    
    response = client.post(f"/permissions/update/-5", json=updated_permission,
                           headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 404
    assert response.json()['detail'] == "Permission doesn't exist"


def test_update_permission_invalid_data(test_permission: mpermission.Permission, 
                                   concierge_token: str):
    updated_permission: dict[str, Any] = {
        "date":'2024-03-12',
        "start_time":"10:00:00",
        "end_time":"13:00:00"
        }
    
    response = client.post(f"/permissions/update/{test_permission.id}", json=updated_permission,
                           headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 422


# delete_permission

def test_delete_permission_invalid_id(test_permission: mpermission.Permission, 
                                   concierge_token: str):
    response = client.delete(f"/permissions/-5",
                           headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 404
    assert response.json()['detail'] == "Permission doesn't exist"


def test_delete_permission_success(test_permission: mpermission.Permission, 
                                   concierge_token: str):
    response = client.delete(f"/permissions/{test_permission.id}",
                           headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 204

# get_active_permissions

def test_get_active_permissions_success(test_user: muser.User, 
                                        concierge_token: str):
    response = client.get(f"/permissions/active?user_id={test_user.id}", 
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_active_permissions_filtered(test_user: muser.User, 
                                        concierge_token: str):
    today = datetime.today().date()
    now = datetime.now().time()
    response = client.get(f"/permissions/active?user_id={test_user.id}&date={today}&time={now}", 
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    response_date = datetime.strptime(response.json()[0]["date"], "%Y-%m-%d").date()

    assert response_date == today


def test_get_active_permissions_filtered_invalid(test_user: muser.User, 
                                        concierge_token: str):
    response = client.get(f"/permissions/active?user_id={test_user.id}&date=2023-10-12", 
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 204
    assert response.text == ""

#room

#get_rooms

def test_get_all_rooms(test_concierge: muser.User,
                       concierge_token: str):
    response = client.get(
        "/rooms", headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_room_number(test_room: mdevice.Room,
                        test_concierge: muser.User,
                        concierge_token: str):
    response = client.get(
        f"/rooms/?number={test_room.number}", headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert response.json()[0]["number"] == test_room.number


# get_room_id
def test_get_room_by_id(test_room: mdevice.Room,
                        test_concierge: muser.User,
                        concierge_token: str):
    response = client.get(
        f"/rooms/{test_room.id}", headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert response.json()["number"] == test_room.number


def test_get_room_by_invalid_id(test_concierge: muser.User,
                                concierge_token: str):
    response = client.get(
        f"/rooms/{-5}", headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 204
    assert response.text == ""

# create_room

def test_create_room(test_concierge: muser.User,
                     concierge_token: str):
    response = client.post(f"/rooms", json={"number": "12345"},
                           headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 201
    assert response.json()["number"] == '12345'


def test_create_room_duplicated(test_concierge: muser.User,
                     concierge_token: str):
    response = client.post(f"/rooms", json={"number": "12345"},
                           headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 400
    assert response.json()['detail'] == "Room with this number already exists"


def test_create_room_invalid(test_concierge: muser.User,
                     concierge_token: str):
    response = client.post(f"/rooms", json={"number": 56687},
                           headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 422

#update_room

def test_update_room(test_concierge: muser.User,
                     test_room: mdevice.Room,
                     concierge_token: str):
    response = client.post(f"/rooms/{test_room.id}", json={"number": "12345A"},
                           headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert response.json()["number"] == '12345A'


def test_update_room_invalid_id(test_concierge: muser.User,
                                concierge_token: str):
    response = client.post(f"/rooms/-5", json={"number": "12345A"},
                           headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 404
    assert response.json()["detail"] == 'Room not found'


def test_update_room_invalid_data(test_concierge: muser.User,
                                   test_room: mdevice.Room,
                                   concierge_token: str):
    response = client.post(f"/rooms/{test_room.id}", json={"id": 12},
                           headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 422

# delete_room

def test_delete_room(test_concierge: muser.User, concierge_token: str):
    response = client.post(f"/rooms", json={"number": "12345ABC"},
                           headers={"Authorization": f"Bearer {concierge_token}"})
    room_id = response.json()["id"]
    response = client.delete(f"/rooms/{room_id}", headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 204



def test_delete_room_invalid_id(test_concierge: muser.User,
                     concierge_token: str):
    response = client.delete(f"/rooms/-5",
                           headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Room doesn't exist"


def test_delete_room_invalid_constraint(test_concierge: muser.User,
                                        test_room: mdevice.Room,
                                        concierge_token: str):
    response = client.delete(f"/rooms/{test_room.id}",
                           headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 500
    assert response.json()["detail"] == "An internal error occurred while deleting room"

# session

# start_login_session

def test_start_session_login(test_user: muser.User,
                             concierge_token: str):
    login_data = {
        "username": test_user.email,
        "password": "password456"
    }
    response = client.post("/start-session/login",
                           headers={"Authorization": f"Bearer {concierge_token}"}, data=login_data)
    assert response.status_code == 200


def test_start_session_invalid_credentials(test_user: muser.User,
                                           concierge_token: str):
    login_data = {
        "password": "password456"
    }
    response = client.post("/start-session/login",
                           headers={"Authorization": f"Bearer {concierge_token}"}, data=login_data)
    assert response.status_code == 422

# start_card_session

def test_start_session_card(test_user: muser.User,
                            concierge_token: str):
    card_data = {"card_id": "7890"}
    response = client.post("/start-session/card",
                           headers={"Authorization": f"Bearer {concierge_token}"}, json=card_data)
    assert response.status_code == 200


def test_start_session_invalid_card(test_user: muser.User,
                                    concierge_token: str):
    card_data = {"card_id": "7891"}
    response = client.post("/start-session/card",
                           headers={"Authorization": f"Bearer {concierge_token}"}, json=card_data)
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid credentials"

# start_unauthorized_session

def test_start_session_unauthorized(concierge_token: str):
    user_data = {
        "name": "Unauthorized",
        "surname": "User",
        "email": "user1234567@gmail.com"
    }
    response = client.post("/unauthorized-users", json=user_data,
                           headers={"Authorization": f"Bearer {concierge_token}"})
    unauthorized_id = response.json()["id"]
    response1 = client.post(f"/start-session/unauthorized/{unauthorized_id}",
                            headers={"Authorization": f"Bearer {concierge_token}"})
    assert response1.status_code == 200


def test_start_session_unauthorized_invalid(concierge_token: str):
    response = client.post("/start-session/unauthorized/-11",
                           headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 404
    assert response.json()[
        "detail"] == f"Unauthorized user not found"

# get_session_id

def test_get_session_id(concierge_token: str,
                        test_session: moperation.UserSession):
    response = client.get(f"/session/{test_session.id}",
                           headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert response.json()["id"] == test_session.id

# approve_session_login

def test_approve_session_login_success(db: Session,
                                       test_concierge: muser.User,
                                       test_device: mdevice.Device,
                                       test_user: muser.User,
                                       test_session: moperation.UserSession,
                                       concierge_token: str):
    session = moperation.UserSession.create_session(
        db, test_user.id, test_concierge.id)
    new_data = schemas.DevOperation(device_id=test_device.id,
                                    session_id=session.id,
                                    operation_type="zwrot",
                                    entitled=False)

    moperation.UnapprovedOperation.create_unapproved_operation(db, new_data)

    login_data = {
        "username": test_concierge.email,
        "password": "password123"
    }
    response = client.post(
        f"/approve/login/session/{session.id}",
        headers={"Authorization": f"Bearer {concierge_token}"},
        data=login_data
    )
    assert response.status_code == 200
    assert response.json()[0]["operation_type"] == "zwrot"


def test_approve_session_login_ended(db: Session,
                                       test_concierge: muser.User,
                                       test_device: mdevice.Device,
                                       test_user: muser.User,
                                       test_session: moperation.UserSession,
                                       concierge_token: str):
    session = moperation.UserSession.create_session(
        db, test_user.id, test_concierge.id)
    new_data = schemas.DevOperation(device_id=test_device.id,
                                    session_id=session.id,
                                    operation_type="zwrot",
                                    entitled=False)

    moperation.UnapprovedOperation.create_unapproved_operation(db, new_data)

    login_data = {
        "username": test_concierge.email,
        "password": "password123"
    }
    client.post(
        f"/approve/login/session/{session.id}",
        headers={"Authorization": f"Bearer {concierge_token}"},
        data=login_data
    )

    response = client.post(
        f"/approve/login/session/{session.id}",
        headers={"Authorization": f"Bearer {concierge_token}"},
        data=login_data
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Session has been already ended"


def test_approve_session_login_invalid_credentials(test_concierge: muser.User,
                                                   test_session: moperation.UserSession,
                                                   concierge_token: str):
    login_data = {
        "username": test_concierge.email,
        "password": "invalidpassword123"
    }
    response = client.post(
        f"/approve/login/session/{test_session.id}",
        headers={"Authorization": f"Bearer {concierge_token}"},
        data=login_data
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "Invalid credentials"}


def test_approve_session_login_no_permission(test_user: muser.User,
                                             test_session: moperation.UserSession,
                                             concierge_token: str):
    login_data = {
        "username": test_user.email,
        "password": "password456"
    }
    response = client.post(
        f"/approve/login/session/{test_session.id}",
        headers={"Authorization": f"Bearer {concierge_token}"},
        data=login_data
    )
    assert response.status_code == 403
    assert response.json() == {
        "detail": "You cannot perform this operation without the appropriate role"}

# approve_session_card

def test_approve_session_card_no_devices(test_session: moperation.UserSession,
                                         concierge_token: str):
    response = client.post(
        f"/approve/card/session/{test_session.id}",
        headers={"Authorization": f"Bearer {concierge_token}"},
        json={"card_id": "123456"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "No unapproved operations found"


def test_approve_session_card_invalid_card(test_session: moperation.UserSession,
                                           concierge_token: str):
    response = client.post(
        f"/approve/card/session/{test_session.id}",
        headers={"Authorization": f"Bearer {concierge_token}"},
        json={"card_id": "87635refw"}
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "Invalid credentials"}


def test_approve_session_card_success(db: Session,
                                      test_device: mdevice.Device,
                                      test_user: muser.User,
                                      test_concierge: muser.User,
                                      concierge_token: str):

    session = moperation.UserSession.create_session(
        db, test_user.id, test_concierge.id)
    new_data = schemas.DevOperation(device_id=test_device.id,
                                    session_id=session.id,
                                    operation_type="zwrot",
                                    entitled=False)

    moperation.UnapprovedOperation.create_unapproved_operation(db, new_data)

    response = client.post(
        f"/approve/card/session/{session.id}",
        headers={"Authorization": f"Bearer {concierge_token}"},
        json={"card_id": "123456"}
    )
    assert response.status_code == 200
    assert response.json()[0]["operation_type"] == "zwrot"

# reject_session

def test_reject_session(db:Session, 
                        test_concierge: muser.User,
                        test_device: mdevice.Device,
                        test_user: muser.User,
                        concierge_token: str):
    session = moperation.UserSession.create_session(
        db, test_user.id, test_concierge.id)
    new_data = schemas.DevOperation(device_id=test_device.id,
                                    session_id=session.id,
                                    operation_type="zwrot",
                                    entitled=False)

    moperation.UnapprovedOperation.create_unapproved_operation(db, new_data)
    response = client.post(
        f"/reject/session/{session.id}",
        headers={"Authorization": f"Bearer {concierge_token}"}
    )
    assert response.status_code == 200


def test_reject_session_approved(test_session: moperation.UserSession,
                                 concierge_token: str):
    response = client.post(
        f"/reject/session/{test_session.id}",
        headers={"Authorization": f"Bearer {concierge_token}"}
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "Session has been already ended"}


def test_reject_session_invalid_id(concierge_token: str):
    response = client.post(
        f"/reject/session/-5",
        headers={"Authorization": f"Bearer {concierge_token}"}
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Session not found"}

# unathorizedUser

# create_or_get_unauthorized_user

def test_create_unauthorized_user(test_concierge: muser.User,
                                  concierge_token: str):
    user_data = {
        "name": "Unauthorized",
        "surname": "User",
        "email": "user@gmail.com"
    }
    response = client.post("/unauthorized-users", json=user_data,
                           headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 201
    assert response.json()["surname"] == user_data["surname"]


def test_create_unauthorized_user_duplicated(test_concierge: muser.User,
                                             concierge_token: str):
    user_data = {
        "name": "Unauthorized",
        "surname": "User",
        "email": "user@gmail.com",
    }
    response = client.post("/unauthorized-users", json=user_data,
                           headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert response.json()["surname"] == user_data["surname"]


def test_create_unauthorized_user_duplicated_invalid(test_concierge: muser.User,
                                                     concierge_token: str):
    user_data = {
        "name": "Unauthorized1",
        "surname": "User1",
        "email": "user@gmail.com",
    }
    response = client.post("/unauthorized-users", json=user_data,
                           headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 409
    assert response.json()[
        "detail"] == "User with this email already exists but with a different name or surname"
 

def test_create_unauthorized_user_with_missing_data(test_concierge: muser.User,
                                                    concierge_token: str):
    user_data = {
        "name": "Unauthorized User"
    }
    response = client.post("/unauthorized-users", json=user_data,
                           headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 422

# get_all_unathorized_users

def test_get_all_unauthorized_users(test_concierge: muser.User,
                                    concierge_token: str):
    response = client.get("/unauthorized-users/",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert len(response.json()) >= 1

#get_unathorized_user_id

def test_get_unauthorized_user_by_id(db: Session,
                                     test_concierge: muser.User,
                                     concierge_token: str):
    user = muser.UnauthorizedUser(name="Unauthorized",
                                  surname="User 2",
                                  email="user123@gmail.com")
    db.add(user)
    db.commit()
    db.refresh(user)

    response = client.get(
        f"/unauthorized-users/{user.id}", headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert response.json()["surname"] == user.surname


def test_get_unauthorized_user_with_invalid_id(test_concierge: muser.User,
                                               concierge_token: str):
    response = client.get("/unauthorized-users/9999",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 204
    assert response.text == ""

# get_unathorized_user_email

def test_get_unauthorized_user_email(db: Session, 
                                     test_unauthorized_user: muser.UnauthorizedUser,
                                     concierge_token: str):

    email =test_unauthorized_user.email
    assert isinstance(email, str)

    response = client.get(f"unauthorized-users/email/{email}",
                           headers={"Authorization": f"Bearer {concierge_token}"})

    assert response.status_code == 200
    data = response.json()

    assert data["email"] == email
    assert data["name"] == test_unauthorized_user.name
    assert data["surname"] == test_unauthorized_user.surname


def test_get_unauthorized_user_email_invalid(db: Session,
                                     concierge_token: str):

    response = client.get(f"unauthorized-users/email/niepoprawny@example.pl",
                           headers={"Authorization": f"Bearer {concierge_token}"})

    assert response.status_code == 204
    assert response.text == ""

# update_unauthorized_user

def test_update_unauthorized_user(db: Session, 
                                  test_unauthorized_user: muser.UnauthorizedUser, 
                                  concierge_token: str):

    user_id = test_unauthorized_user.id
    update_data = {
        "name": "Jane Updated",
        "surname": "Doe Updated",
        "email": "john.doe@example.com"
    }

    response = client.post(
        f"/unauthorized-users/{user_id}",
        json=update_data,
        headers={"Authorization": f"Bearer {concierge_token}"}
    )

    assert response.status_code == 200
    updated_user = response.json()
    assert updated_user["id"] == user_id
    assert updated_user["name"] == update_data["name"]
    assert updated_user["surname"] == update_data["surname"]
    assert updated_user["email"] == update_data["email"]

    db.refresh(test_unauthorized_user)
    assert test_unauthorized_user.name == update_data["name"]
    assert test_unauthorized_user.surname == update_data["surname"]
    assert test_unauthorized_user.email == update_data["email"]


def test_update_unauthorized_user_invalid(db: Session, 
                                  test_unauthorized_user: muser.UnauthorizedUser, 
                                  concierge_token: str):

    user_id = test_unauthorized_user.id
    update_data = {
        "name": "Jane Updated",
        "surname": "Doe Updated",
    }

    response = client.post(
        f"/unauthorized-users/{user_id}",
        json=update_data,
        headers={"Authorization": f"Bearer {concierge_token}"}
    )

    assert response.status_code == 422
     
# delete_unauthorized_user

def test_delete_unauthorized_user_invalid_id(concierge_token: str):
    response = client.delete("/unauthorized-users/9999",
                             headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 404
    assert response.json()[
        "detail"] == "Unauthorized user doesn't exist"


def test_delete_unauthorized_user_valid(db: Session,
                                        concierge_token: str):

    user = muser.UnauthorizedUser(name="Unauthorized",
                                  surname="User 2",
                                  email="2user2@kskk.cck")
    db.add(user)
    db.commit()
    db.refresh(user)
    response = client.delete(
        f"/unauthorized-users/{user.id}", headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 204

#users

#get_all_users

def test_get_all_users(concierge_token: str):
    response = client.get("/users/", headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert len(response.json()) >= 1

# get_user_id

def test_get_user_by_id(test_concierge: muser.User,
                        concierge_token: str):
    response = client.get(f"/users/{test_concierge.id}",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert response.json()["surname"] == test_concierge.surname


def test_get_user_by_invalid_id(concierge_token: str):
    response = client.get(f"/users/{-1}",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 204
    assert response.text == ""

# create_user

def test_create_user_success(concierge_token: str,
                             test_user: muser.User):

    user_data : dict[str, Any] = {
        "email":"testuser123@example.com",
        "password":"password456789",
        "card_code":"7890123",
        "role":"student",
        "name":"New",
        "surname":"User",
        "faculty":"Geodezji i Kartografii"
}
    response = client.post("/users/", json=user_data,
                           headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 201


def test_create_user_invalid(concierge_token: str,
                             test_user: muser.User):

    user_data : dict[str, Any] = {
        "email":"testuser123@example.com",
        "password":"password456789",
        "card_code":"7890123",
        "role":"geodeta",
        "name":"New",
        "surname":"User",
        "faculty":"Geodezji i Kartografii"
}
    response = client.post("/users/", json=user_data,
                           headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 422

def test_create_user_invalid_2(concierge_token: str,
                             test_user: muser.User):

    user_data : dict[str, Any] = {
        "email":"testuser123@example.com",
        "password":"password456789",
        "card_code":"7890123",
        "role":"student",
        "name":"New",
        "surname":"User",
        "faculty":"Przykładowy Wydział"
}
    response = client.post("/users/", json=user_data,
                           headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 500


def test_create_user_duplicated(concierge_token: str,
                             test_user: muser.User):
    user_data : dict[str, Any] = {
        "email":"testuser123@example.com",
        "password":"password456789",
        "card_code":"7890123",
        "role":"student",
        "name":"New",
        "surname":"User",
        "faculty":"Geodezji i Kartografii"
}
    response = client.post("/users/", json=user_data,
                           headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 500

# delete_user

def test_delete_user_invalid_id(test_permission: mpermission.Permission, 
                                   concierge_token: str):
    response = client.delete(f"/users/-5",
                           headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 404
    assert response.json()['detail'] == "User doesn't exist"

def test_delete_user_success(test_user: muser.User,  
                             concierge_token: str):
    user_data : dict[str, Any] = {
        "email":"testuser1234@example.com",
        "password":"password456789",
        "card_code":"789012345",
        "role":"student",
        "name":"New",
        "surname":"User",
        "faculty":"Geodezji i Kartografii"
}
    response = client.post("/users/", json=user_data,
                           headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 201
    user_id = response.json()["id"]
    response1 = client.delete(f"/users/{user_id}",
                           headers={"Authorization": f"Bearer {concierge_token}"})
    assert response1.status_code == 204

# update_user

def test_update_user_invalid_id(test_permission: mpermission.Permission, 
                                   concierge_token: str,
                                   test_user: muser.User,
                                   test_room: mdevice.Room):
    user_data : dict[str, Any] = {
        "email":"testuser123@example.com",
        "password":"password456789",
        "card_code":"7890123",
        "role":"student",
        "name":"New",
        "surname":"User",
        "faculty":"Geodezji i Kartografii"
    }
    response = client.post(f"/users/update/-5", json=user_data,
                           headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 404
    assert response.json()['detail'] == "User not found"


def test_update_user_success(test_permission: mpermission.Permission, 
                                   concierge_token: str,
                                   test_user: muser.User,
                                   test_room: mdevice.Room):
    user_data : dict[str, Any] = {
        "email":"testuser1234@example.com",
        "password":"password456789",
        "card_code":"789012345",
        "role":"student",
        "name":"New",
        "surname": "portier",
        "faculty":"Geodezji i Kartografii"
    }
    response = client.post(f"/users/update/{test_user.id}", json=user_data,
                           headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert response.json()['email'] == "testuser1234@example.com"
    assert response.json()['id'] == test_user.id

# auth

# login

def test_login_with_correct_credentials(test_concierge: muser.User):
    login_data = {
        "username": test_concierge.email,
        "password": "password123"
    }
    response = client.post("/login", data=login_data)
    assert response.status_code == 200


def test_login_with_incorrect_credentials(test_concierge: muser.User):
    login_data = {
        "username": test_concierge.email,
        "password": "wrongpassword"
    }
    response = client.post("/login", data=login_data)
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid credentials"


def test_login_without_all_credentials(test_concierge: muser.User):
    login_data = {
        "password": "wrongpassword"
    }
    response = client.post("/login", data=login_data)
    assert response.status_code == 422

# card_login

def test_card_login_with_valid_card_id():
    card_data = {"card_id": "123456"}
    response = client.post("/login/card", json=card_data)
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_card_login_with_invalid_card_id():
    card_data = {"card_id": "invalid_card"}
    response = client.post("/login/card", json=card_data)
    assert response.status_code == 403
    assert response.json()["detail"] == "Password could not be identified"

# get_current_user

def test_get_current_user(test_concierge: muser.User,
                          concierge_token: str):
    response = client.get("/concierge",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert response.json()["surname"] == test_concierge.surname

# logout

def test_logout_with_valid_token(test_concierge: muser.User,
                                 concierge_token: str):
    response = client.post(
        "/logout", headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert response.json() == {"detail": "User logged out successfully"}


def test_logout_with_invalid_token():
    response = client.post(
        "/logout", cookies={"access_token": "concierge_token"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_logout_with_blacklisted_token(test_concierge: muser.User,
                                       concierge_token: str):
    client.post(
        "/logout", headers={"Authorization": f"Bearer {concierge_token}"})
    response2 = client.post(
        "/logout", headers={"Authorization": f"Bearer {concierge_token}"})
    assert response2.status_code == 403
    assert response2.json()["detail"] == "Concierge is logged out"
