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


def test_get_all_users(concierge_token: str):
    response = client.get("/users/", headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_get_user_by_id(test_concierge: muser.User,
                        concierge_token: str):
    response = client.get(f"/users/{test_concierge.id}",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert response.json()["surname"] == test_concierge.surname


def test_get_user_by_invalid_id(concierge_token: str):
    response = client.get(f"/users/{-1}",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 404
    assert response.json()["detail"] == "User doesn't exist"


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


def test_card_login_with_valid_card_id():
    card_data = {"card_id": "123456"}
    response = client.post("/login/card", json=card_data)
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_card_login_with_invalid_card_id():
    card_data = {"card_id": "invalid_card"}
    response = client.post("/login/card", json=card_data)
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid credentials"


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



def test_get_all_devices(test_device: mdevice.Device,
                         test_device_mikrofon: mdevice.Device,
                         concierge_token: str):
    response = client.get(
        "/devices/", headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 2


def test_get_devices_type_version(test_device: mdevice.Device,
                                  test_device_mikrofon: mdevice.Device,
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
                              test_device_mikrofon: mdevice.Device,
                              concierge_token: str):
    response = client.get(f"/devices/?room_number={test_room.number}",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert response.json()[0]["room_number"] == test_room.number
    assert len(response.json()) == 1


def test_get_all_devices_type_version_room(test_device: mdevice.Device,
                                           test_room: mdevice.Room,
                                           test_device_mikrofon: mdevice.Device,
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
                                      test_device_mikrofon: mdevice.Device,
                                      concierge_token: str):

    response = client.get("/devices/?dev_type=computer",
                          headers={"Authorization": f"Bearer {concierge_token}"})

    assert response.status_code == 422


def test_get_all_devices_invalid_version(test_device: mdevice.Device,
                                         test_device_mikrofon: mdevice.Device,
                                         concierge_token: str):
    response = client.get("/devices/?dev_version=first",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 422


def test_get_all_devices_type_version_invalid(test_device: mdevice.Device,
                                              test_device_mikrofon: mdevice.Device,
                                              concierge_token: str):
    response = client.get("/devices/?dev_version=zapasowa&dev_type=pilot",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 404
    assert response.json()[
        "detail"] == "No devices found matching criteria"


def test_get_dev_by_code(test_device: mdevice.Device,
                         concierge_token: str):
    response = client.get(f"/devices/code/{test_device.code}",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert response.json()["dev_type"] == test_device.dev_type.value


def test_get_dev_by_invalid_code(concierge_token: str):
    response = client.get("/devices/code/-5",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Device not found"


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
                                         test_device_mikrofon: mdevice.Device,
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
                           json={"session_id": response1.json()["id"], "device_code": test_device_mikrofon.code})
    assert response.status_code == 403
    assert response.json()[
        "detail"] == f"User has no permission to perform the operation"


def test_changeStatus_with_force(test_concierge: muser.User,
                                 test_user: muser.User,
                                 test_device_mikrofon: mdevice.Device,
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
                                 "device_code": test_device_mikrofon.code})
    assert response.status_code == 200
    assert response.json()["entitled"] is False
    assert response.json()["operation_type"] == "pobranie"


def test_changeStatus_again(test_concierge: muser.User,
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


def test_get_permission_with_valid_user_id(db: Session,
                                           test_concierge: muser.User,
                                           test_user: muser.User,
                                           test_room: mdevice.Room,
                                           concierge_token: str):
    response = client.get(
        f"/permissions?user_id={test_user.id}",
        headers={"Authorization": f"Bearer {concierge_token}"}
    )
    assert response.status_code == 200
    assert response.json()[0]["user"]["id"] == test_user.id


def test_get_permission_with_invalid_user_id(test_concierge: muser.User,
                                             concierge_token: str):
    response = client.get("/permissions?user_id=-1",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 404
    assert response.json()[
        "detail"] == "No permissions found that match given criteria"


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
    assert response.status_code == 404
    assert response.json()[
        "detail"] == "No permissions found that match given criteria"


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


def test_get_all_rooms(test_concierge: muser.User,
                       concierge_token: str):
    response = client.get(
        "/rooms", headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)


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
    assert response.status_code == 404
    assert response.json()["detail"] == "Room not found"


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


def test_get_all_unauthorized_users(test_concierge: muser.User,
                                    concierge_token: str):
    response = client.get("/unauthorized-users/",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert len(response.json()) >= 1


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
    assert response.status_code == 404
    assert response.json()[
        "detail"] == "Unauthorized user doesn't exist"


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


def test_approve_session_card_no_devices(test_session: moperation.UserSession,
                                         concierge_token: str):
    response = client.post(
        f"/approve/card/session/{test_session.id}",
        headers={"Authorization": f"Bearer {concierge_token}"},
        json={"card_id": "123456"}
    )
    assert response.status_code == 404
    assert response.json() == {
        "detail": "No unapproved operations found for this session"}


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
    response1 = client.post("/start-session/login",
                            headers={"Authorization": f"Bearer {concierge_token}"}, data=login_data)
    assert response1.status_code == 200
    response = client.post("/operations/change-status",
                           headers={
                               "Authorization": f"Bearer {concierge_token}"},
                           json={"session_id": response1.json()["id"],
                                 "device_code": test_device.code})
    assert response.status_code == 200
    assert response.json()["device"]["code"] == test_device.code
    assert response.json()["session"]["status"] == "w trakcie"
    assert response.json()["operation_type"] == "pobranie"
    assert response.json()["entitled"] is True

    response2 = client.post(
        f"/approve/login/session/{response1.json()['id']}",
        headers={"Authorization": f"Bearer {concierge_token}"},
        data=login_data_concierge
    )
    assert response2.status_code == 200
    assert response2.json()[0]["operation_type"] == "pobranie"


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


def test_get_all_devices_with_owner(test_device: mdevice.Device,
                                    test_room: mdevice.Room,
                                    test_user: muser.User,
                                    test_device_mikrofon: mdevice.Device,
                                    concierge_token: str):
    response = client.get(f"/devices/?dev_type=klucz&dev_version=podstawowa&room_number={test_room.number}",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert response.json()[0]["dev_type"] == "klucz"
    assert response.json()[0]["dev_version"] == "podstawowa"
    assert response.json()[0]["room_number"] == test_room.number
    assert response.json()[0]["owner_name"] == test_user.name
    assert response.json()[0]["owner_surname"] == test_user.surname


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
    assert response.status_code == 404
    assert response.json()[
        'detail'] == f"No operations that match given criteria found"


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
    assert response.status_code == 404

    assert response.json()["detail"] == "There is no user note with this id"


def test_get_user_notes_not_found(concierge_token: str):
    response = client.get("/notes/users/?user_id=-2",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 404
    assert response.json()["detail"] == "No user notes found"


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


def test_edit_user_note(test_user: muser.User,
                        concierge_token: str,
                        test_user_note: muser.UserNote):
    note_data: dict[str, Any] = {
        "user_id": test_user.id, "note": "Edited note"}
    response = client.put(f"/notes/users/{test_user_note.id}",
                          headers={
        "Authorization": f"Bearer {concierge_token}"},
        json=note_data)

    assert response.status_code == 200
    assert response.json()["note"] == "Edited note"
    assert response.json()["user"]["id"] == test_user.id


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

    assert response.status_code == 404
    assert response.json()[
        "detail"] == "No device notes that match given criteria found"


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

    assert response.status_code == 404
    assert response.json()["detail"] == "No device note found"


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


def test_delete_device_note(db: Session,
                            concierge_token: str,
                            test_device: mdevice.DeviceNote,
                            test_device_note: mdevice.DeviceNote):
    response = client.delete(f"/notes/devices/{test_device_note.id}",
                             headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 204
    response = client.get(f"/notes/devices/{test_device_note.id}",
                          headers={"Authorization": f"Bearer {concierge_token}"})

    assert response.status_code == 404
    assert response.json()[
        "detail"] == f"No device note found"


def test_logout_with_valid_token(test_concierge: muser.User,
                                 concierge_refresh_token: str,
                                 concierge_token: str):
    response = client.post(
        "/logout", headers={"Authorization": f"Bearer {concierge_token}"},
        json={"refresh_token":concierge_refresh_token})
    assert response.status_code == 200
    assert response.json() == {"detail": "User logged out successfully"}


def test_logout_with_invalid_token():
    response = client.post(
        "/logout", cookies={"access_token": "concierge_token"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_logout_with_blacklisted_token(test_concierge: muser.User,
                                       concierge_refresh_token: str,
                                       concierge_token: str):
    client.post(
        "/logout", headers={"Authorization": f"Bearer {concierge_token}"},
        json={"refresh_token":concierge_refresh_token})
    response2 = client.post(
        "/logout", headers={"Authorization": f"Bearer {concierge_token}"},
        json={"refresh_token":concierge_refresh_token})
    assert response2.status_code == 403
    assert response2.json()["detail"] == "Concierge is logged out"
