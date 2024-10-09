import pytest
import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import text, true
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app import models, database
from app.services import securityService, deviceService, sessionService, operationService
from app.schemas import UserCreate
from app.database import Base

client = TestClient(app)


@pytest.fixture(scope="module")
def db():
    session = database.SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="module")
def test_concierge(db: Session):
    user_data = UserCreate(
        email="testconcierge@example.com",
        password="password123",
        card_code="123456",
        role="admin",
        name="Test",
        surname="Concierge",
        faculty="geodesy"
    )

    password_service = securityService.PasswordService()
    hashed_password = password_service.hash_password(user_data.password)
    hashed_card_code = password_service.hash_password(user_data.card_code)
    user_data.password = hashed_password
    user_data.card_code = hashed_card_code

    user = models.User(**user_data.model_dump())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="module")
def test_user(db: Session):
    user_data = UserCreate(
        email="testuser@example.com",
        password="password456",
        card_code="7890",
        role="employee",
        name="Test",
        surname="User",
        faculty="geodesy"
    )
    password_service = securityService.PasswordService()
    hashed_password = password_service.hash_password(user_data.password)
    hashed_card_code = password_service.hash_password(user_data.card_code)
    user_data.password = hashed_password
    user_data.card_code = hashed_card_code

    user = models.User(**user_data.model_dump())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="module")
def test_room(db: Session):
    room = models.Room(number="101")
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


@pytest.fixture(scope="module")
def test_room_2(db: Session):
    room = models.Room(number="102")
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


@pytest.fixture(scope="module")
def test_permission(db: Session, test_user, test_room):
    permission = models.Permission(user_id=test_user.id, room_id=test_room.id,
                                   start_reservation=datetime.datetime(
                                       2024, 12, 6, 12, 45, tzinfo=ZoneInfo("Europe/Warsaw")).isoformat(),
                                   end_reservation=datetime.datetime(2024, 12, 6, 14, 45, tzinfo=ZoneInfo("Europe/Warsaw")).isoformat())
    db.add(permission)
    db.commit()
    db.refresh(permission)
    return permission


@pytest.fixture(scope="module")
def test_session(db: Session, test_user: models.User, test_concierge: models.User):
    session = models.IssueReturnSession(
        user_id=test_user.id,
        concierge_id=test_concierge.id,
        start_time=datetime.datetime(
            2024, 12, 6, 12, 45, tzinfo=ZoneInfo("Europe/Warsaw")).isoformat(),
        status=models.SessionStatus.in_progress
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@pytest.fixture(scope="module")
def test_device(db: Session, test_room: models.Room):
    device = models.Device(
        dev_type="key",
        room_id=test_room.id,
        is_taken=False,
        version="primary",
        code="device_key_101"
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


@pytest.fixture(scope="module")
def test_device_microphone(db: Session, test_room_2: models.Room):
    device = models.Device(
        dev_type="microphone",
        room_id=test_room_2.id,
        is_taken=False,
        version="backup",
        code="device_mic_101"
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


@pytest.fixture
def create_user_note(db: Session, test_user: models.User):
    note = models.UserNote(user_id=test_user.id, note="Test Note")
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@pytest.fixture
def create_specific_user_note(db: Session, test_user: models.User):
    note = models.UserNote(user_id=test_user.id, note="Test Specific Note")
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@pytest.fixture
def create_device_note(db: Session, test_device: models.Device, test_session: models.IssueReturnSession):
    operation_service = operationService.DeviceOperationService(db)

    operation_data = {
        "device_id": test_device.id,
        "issue_return_session_id": test_session.id,
        "operation_type": "issue_dev",
        "entitled": True
    }
    operation = operation_service.create_operation(operation_data)
    note = models.DeviceNote(
        device_operation_id=operation.id, note="Device note content")
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@pytest.fixture(scope="module", autouse=True)
def cleanup_db_after_tests(db: Session):
    yield
    db.execute(text("SET session_replication_role = 'replica';"))

    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())

    db.commit()

    db.execute(text("SET session_replication_role = 'origin';"))


@pytest.fixture(scope="module")
def token_service(db: Session):
    return securityService.TokenService(db)


@pytest.fixture(scope="module")
def concierge_token(test_concierge, token_service):
    token_data = {'user_id': test_concierge.id,
                  'user_role': test_concierge.role.value}
    token = token_service.create_token(token_data, token_type="access")
    return token


def test_get_all_users(concierge_token: str):
    response = client.get("/users/",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_get_user_by_id(test_concierge: models.User, concierge_token: str):
    response = client.get(f"/users/{test_concierge.id}",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert response.json()["surname"] == test_concierge.surname


def test_get_user_by_invalid_id(concierge_token: str):
    response = client.get(f"/users/{-1}",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 404
    assert response.json()["detail"] == "User with id: -1 doesn't exist"


def test_login_with_correct_credentials(test_concierge: models.User):
    login_data = {
        "username": test_concierge.email,
        "password": "password123"
    }
    response = client.post("/login", data=login_data)
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()


def test_login_with_incorrect_credentials(test_concierge: models.User):
    login_data = {
        "username": test_concierge.email,
        "password": "wrongpassword"
    }
    response = client.post("/login", data=login_data)
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid credentials"


def test_login_without_all_credentials(test_concierge: models.User):
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
    assert "refresh_token" in response.json()


def test_card_login_with_invalid_card_id():
    card_data = {"card_id": "invalid_card"}
    response = client.post("/login/card", json=card_data)
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid credentials"


def test_refresh_token_with_valid_token(db: Session, test_concierge: models.User):
    token_service = securityService.TokenService(db)
    refresh_token = token_service.create_token({"user_id": test_concierge.id, "user_role": test_concierge.role.value},
                                               "refresh")
    response = client.post("/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_refresh_token_with_invalid_token():
    response = client.post("/refresh", json={"refresh_token": "invalid_token"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"


def test_get_all_devices(test_device: models.Device,
                         test_device_microphone: models.Device,
                         concierge_token: str):
    response = client.get(
        "/devices/", headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 2


def test_get_all_devices_type_version(test_device: models.Device,
                                      test_device_microphone: models.Device,
                                      concierge_token: str):
    response = client.get("/devices/?dev_type=key&dev_version=primary",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert response.json()[0]["dev_type"] == "key"
    assert response.json()[0]["version"] == "primary"
    assert len(response.json()) == 1


def test_get_all_devices_invalid_type(test_device: models.Device,
                                      test_device_microphone: models.Device,
                                      concierge_token: str):
    response = client.get("/devices/?dev_type=computer",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid device type: computer"


def test_get_all_devices_invalid_version(test_device: models.Device,
                                         test_device_microphone: models.Device,
                                         concierge_token: str):
    response = client.get("/devices/?dev_version=first",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid device version: first"


def test_get_dev_by_id(test_device: models.Device, concierge_token: str):
    response = client.get(f"/devices/{test_device.id}",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert response.json()["dev_type"] == test_device.dev_type.value


def test_get_dev_by_invalid_id(concierge_token: str):
    response = client.get("/devices/-5",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Device with id: -5 doesn't exist"


def test_create_device(test_room: models.Room, test_concierge: models.User, concierge_token: str):
    device_data = {
        "room_id": test_room.id,
        "version": "primary",
        "is_taken": False,
        "dev_type": "microphone",
        "code": "123467"
    }

    response = client.post("/devices/", json=device_data,
                           headers={"Authorization": f"Bearer {concierge_token}"})

    assert response.status_code == 201
    assert response.json()["dev_type"] == device_data["dev_type"]


def test_create_device_with_invalid_data(concierge_token: str):
    device_data = {
        "is_taken": False,
        "room": 6
    }
    response = client.post("/devices/", json=device_data,
                           headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 422


def test_start_session_login(test_user: models.User, concierge_token: str):
    login_data = {
        "username": test_user.email,
        "password": "password456"
    }
    response = client.post("/start-session",
                           headers={"Authorization": f"Bearer {concierge_token}"}, data=login_data)
    assert response.status_code == 200


def test_start_session_invalid_credentials(test_user: models.User, concierge_token: str):
    login_data = {
        "password": "password456"
    }
    response = client.post("/start-session",
                           headers={"Authorization": f"Bearer {concierge_token}"}, data=login_data)
    assert response.status_code == 422


def test_start_session_card(test_user: models.User, concierge_token: str):
    card_data = {"card_id": "7890"}
    response = client.post("/start-session/card",
                           headers={"Authorization": f"Bearer {concierge_token}"}, json=card_data)
    assert response.status_code == 200


def test_start_session_invalid_card(test_user: models.User, concierge_token: str):
    card_data = {"card_id": "7891"}
    response = client.post("/start-session/card",
                           headers={"Authorization": f"Bearer {concierge_token}"}, json=card_data)
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid credentials"


def test_changeStatus_invalid_session(test_device: models.Device,
                                      test_concierge: models.User,
                                      concierge_token: str):
    response = client.post("/devices/change-status",
                           headers={
                               "Authorization": f"Bearer {concierge_token}"},
                           json={"issue_return_session_id": 0, "device_id": test_device.id, "force": False})
    assert response.status_code == 404
    assert response.json()["detail"] == "IssueReturnSession doesn't exist"


def test_changeStatus_with_valid_id_taking(test_concierge: models.User,
                                           test_user: models.User,
                                           test_device: models.Device,
                                           test_permission: models.Permission,
                                           concierge_token: str):

    login_data = {
        "username": test_user.email,
        "password": "password456"
    }
    response1 = client.post("/start-session",
                            headers={"Authorization": f"Bearer {concierge_token}"}, data=login_data)
    assert response1.status_code == 200
    response = client.post("/devices/change-status",
                           headers={
                               "Authorization": f"Bearer {concierge_token}"},
                           json={"issue_return_session_id": response1.json()["id"], "device_id": test_device.id})
    assert response.status_code == 200
    assert response.json()["device"]["code"] == test_device.code
    assert response.json()["issue_return_session"]["status"] == "in_progress"
    assert response.json()["operation_type"] == "issue_device"
    assert response.json()["entitled"] is True


def test_changeStatus_without_permission(test_concierge: models.User,
                                         test_user: models.User,
                                         test_device_microphone: models.Device,
                                         test_permission: models.Permission,
                                         test_room_2: models.Room,
                                         concierge_token: str):

    login_data = {
        "username": test_user.email,
        "password": "password456"
    }
    response1 = client.post("/start-session",
                            headers={"Authorization": f"Bearer {concierge_token}"}, data=login_data)
    assert response1.status_code == 200
    response = client.post("/devices/change-status",
                           headers={
                               "Authorization": f"Bearer {concierge_token}"},
                           json={"issue_return_session_id": response1.json()["id"], "device_id": test_device_microphone.id})
    assert response.status_code == 403
    assert response.json()[
        "detail"] == f"User with id {test_user.id} does not have permission to access room with id {test_room_2.id}"


def test_changeStatus_without_permission_force(test_concierge: models.User,
                                               test_user: models.User,
                                               test_device_microphone: models.Device,
                                               concierge_token: str):

    login_data = {
        "username": test_user.email,
        "password": "password456"
    }
    response1 = client.post("/start-session",
                            headers={"Authorization": f"Bearer {concierge_token}"}, data=login_data)
    assert response1.status_code == 200
    response = client.post("/devices/change-status",
                           headers={
                               "Authorization": f"Bearer {concierge_token}"},
                           json={"issue_return_session_id": response1.json()["id"],
                                 "force": True,
                                 "device_id": test_device_microphone.id})
    assert response.status_code == 200
    assert response.json()["entitled"] is False
    assert response.json()["operation_type"] == "issue_device"


def test_changeStatus_again(test_concierge: models.User,
                            test_user: models.User,
                            test_device: models.Device,
                            concierge_token: str):

    login_data = {
        "username": test_user.email,
        "password": "password456"
    }

    response1 = client.post("/start-session",
                            headers={"Authorization": f"Bearer {concierge_token}"}, data=login_data)
    assert response1.status_code == 200

    client.post("/devices/change-status",
                headers={"Authorization": f"Bearer {concierge_token}"},
                json={"issue_return_session_id": response1.json()["id"],
                      "device_id": test_device.id})

    response = client.post("/devices/change-status",
                           headers={
                               "Authorization": f"Bearer {concierge_token}"},
                           json={"issue_return_session_id": response1.json()["id"],
                                 "device_id": test_device.id})
    assert response.json()["detail"] == "Device removed from unapproved data."


def test_get_user_permission_with_valid_user_id(db: Session,
                                                test_concierge: models.User,
                                                test_user: models.User,
                                                test_room: models.Room,
                                                concierge_token: str):
    response = client.get(
        f"/permissions/?user_id={test_user.id}",
        headers={"Authorization": f"Bearer {concierge_token}"}
    )
    assert response.status_code == 200
    assert response.json()[0]["user"]["id"] == test_user.id


def test_get_user_permission_with_invalid_user_id(test_concierge: models.User, concierge_token: str):
    response = client.get("/permissions?user_id=-1",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 404
    assert response.json()[
        "detail"] == "No permissions found that meet the stated criteria"


def test_get_key_permission_with_valid_room_id(db: Session,
                                               test_concierge: models.User,
                                               test_user: models.User,
                                               test_room: models.Room,
                                               concierge_token: str):
    response = client.get(
        f"/permissions?room_id={test_room.id}",
        headers={"Authorization": f"Bearer {concierge_token}"}
    )
    assert response.status_code == 200
    assert response.json()[0]["room"]["id"] == test_room.id


def test_get_key_permission_with_invalid_room_id(test_concierge: models.User, concierge_token: str):
    response = client.get("/permissions?user_id=-1",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 404
    assert response.json()[
        "detail"] == "No permissions found that meet the stated criteria"


def test_get_all_rooms(test_concierge: models.User, concierge_token: str):
    response = client.get(
        "/rooms", headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_room_by_id(test_room: models.Room, test_concierge: models.User, concierge_token: str):
    response = client.get(
        f"/rooms/{test_room.id}", headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert response.json()["number"] == test_room.number


def test_create_unauthorized_user(test_concierge: models.User, concierge_token: str):
    user_data = {
        "name": "Unauthorized",
        "surname": "User",
        "email": "user@gmail.com"
    }
    response = client.post("/unauthorized-users", json=user_data,
                           headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 201
    assert response.json()["surname"] == user_data["surname"]


def test_create_unauthorized_user_duplicated(test_concierge: models.User, concierge_token: str):
    user_data = {
        "name": "Unauthorized",
        "surname": "User",
        "email": "user@gmail.com",
    }
    response = client.post("/unauthorized-users", json=user_data,
                           headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 201
    assert response.json()["surname"] == user_data["surname"]


def test_create_unauthorized_user_duplicated_invalid(test_concierge: models.User, concierge_token: str):
    user_data = {
        "name": "Unauthorized1",
        "surname": "User1",
        "email": "user@gmail.com",
    }
    response = client.post("/unauthorized-users", json=user_data,
                           headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 403
    assert response.json()[
        "detail"] == "User with this email already exists but with different name or surname."


def test_create_unauthorized_user_with_missing_data(test_concierge: models.User, concierge_token: str):
    user_data = {
        "name": "Unauthorized User"
    }
    response = client.post("/unauthorized-users", json=user_data,
                           headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 422


def test_get_all_unauthorized_users(test_concierge: models.User, concierge_token: str):
    response = client.get("/unauthorized-users/",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_get_unauthorized_user_by_id(db: Session, test_concierge: models.User, concierge_token: str):
    user = models.UnauthorizedUser(name="Unauthorized",
                                   surname="User 2",
                                   email="user123@gmail.com")
    db.add(user)
    db.commit()
    db.refresh(user)

    response = client.get(
        f"/unauthorized-users/{user.id}", headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert response.json()["surname"] == user.surname


def test_get_unauthorized_user_with_invalid_id(test_concierge: models.User, concierge_token: str):
    response = client.get("/unauthorized-users/9999",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 404
    assert response.json()[
        "detail"] == "Unauthorized user with id: 9999 doesn't exist"


def test_delete_unauthorized_user_invalid_id(concierge_token: str):
    response = client.delete("/unauthorized-users/9999",
                             headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 404
    assert response.json()[
        "detail"] == "Unauthorized user with id: 9999 doesn't exist"


def test_delete_unauthorized_user_valid(db: Session, concierge_token: str):

    user = models.UnauthorizedUser(name="Unauthorized",
                                   surname="User 2",
                                   email="2user2@kskk.cck")
    db.add(user)
    db.commit()
    db.refresh(user)
    response = client.delete(
        f"/unauthorized-users/{user.id}", headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 204


def test_get_all_unapproved_no_devices(db: Session, test_concierge: models.User, concierge_token: str):
    devices = db.query(models.DeviceUnapproved).all()
    for device in devices:
        db.delete(device)
        db.commit()

    response = client.get(
        "/devices/unapproved",
        headers={"Authorization": f"Bearer {concierge_token}"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "No unapproved devices found"


def test_get_all_unapproved_authenticated(db: Session,
                                          test_session: models.IssueReturnSession,
                                          test_device: models.Device,
                                          concierge_token: str):
    device = models.DeviceUnapproved(
        is_taken=False,
        device_id=test_device.id,
        issue_return_session_id=test_session.id,
    )
    db.add(device)
    db.commit()
    db.refresh(device)

    response = client.get(
        "/devices/unapproved",
        headers={"Authorization": f"Bearer {concierge_token}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_all_unapproved_unauthorized(test_concierge: models.User):
    response = client.get("/devices/unapproved")
    assert response.status_code == 401


def test_get_unapproved_invalid_session(concierge_token: str):
    response = client.get(
        "/devices/unapproved/0",
        headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 404
    assert response.json()[
        "detail"] == "No unapproved devices found for this session"


def test_get_unapproved_valid_session(concierge_token: str,
                                      test_session: models.IssueReturnSession):
    response = client.get(
        f"/devices/unapproved/{test_session.id}",
        headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1


def test_approve_session_login_success(test_concierge: models.User,
                                       test_session: models.IssueReturnSession,
                                       concierge_token: str):
    login_data = {
        "username": test_concierge.email,
        "password": "password123"
    }
    response = client.post(
        f"/approve/login/session/{test_session.id}",
        headers={"Authorization": f"Bearer {concierge_token}"},
        data=login_data
    )
    assert response.status_code == 200
    assert response.json() == {
        "detail": "DeviceOperations approved and devices updated successfully."}


def test_approve_session_login_invalid_credentials(test_concierge: models.User,
                                                   test_session: models.IssueReturnSession,
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


def test_approve_session_login_no_permission(test_user: models.User,
                                             test_session: models.IssueReturnSession,
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
        "detail": "You cannot perform this operation without the concierge role"}


def test_approve_session_card_no_devices(test_session: models.IssueReturnSession,
                                         concierge_token: str):
    response = client.post(
        f"/approve/card/session/{test_session.id}",
        headers={"Authorization": f"Bearer {concierge_token}"},
        json={"card_id": "123456"}
    )
    assert response.status_code == 404
    assert response.json() == {
        "detail": "No unapproved devices found for this session"}


def test_approve_session_card_invalid_card(test_session: models.IssueReturnSession,
                                           concierge_token: str):
    response = client.post(
        f"/approve/card/session/{test_session.id}",
        headers={"Authorization": f"Bearer {concierge_token}"},
        json={"card_id": "87635refw"}
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "Invalid credentials"}


def test_approve_session_card_success(db: Session,
                                      test_device: models.Device,
                                      test_user: models.User,
                                      test_concierge: models.User,
                                      concierge_token: str):

    unapproved_dev_service = deviceService.UnapprovedDeviceService(db)
    session_service = sessionService.SessionService(db)
    session = session_service.create_session(test_user.id, test_concierge.id)

    new_data = {
        "device_id": test_device.id,
        "issue_return_session_id": session.id,
        "is_taken": False
    }
    unapproved_dev_service.create_unapproved(new_data)
    response = client.post(
        f"/approve/card/session/{session.id}",
        headers={"Authorization": f"Bearer {concierge_token}"},
        json={"card_id": "123456"}
    )
    assert response.status_code == 200
    assert response.json()[
        "detail"] == 'DeviceOperations approved and devices updated successfully.'


def test_approve_login_success(db: Session,
                               test_device: models.Device,
                               test_user: models.User,
                               test_concierge: models.User,
                               concierge_token: str):

    unapproved_dev_service = deviceService.UnapprovedDeviceService(db)
    session_service = sessionService.SessionService(db)
    session = session_service.create_session(test_user.id, test_concierge.id)

    login_data = {
        "username": test_concierge.email,
        "password": "password123"
    }

    new_data = {
        "device_id": test_device.id,
        "issue_return_session_id": session.id,
        "is_taken": False
    }
    unapproved_dev_service.create_unapproved(new_data)
    response = client.post(
        "/approve/login/",
        headers={"Authorization": f"Bearer {concierge_token}"},
        data=login_data
    )
    assert response.status_code == 200
    assert response.json()[
        "detail"] == 'All operations approved and devices updated successfully.'


def test_all_change_status(test_user: models.User,
                           test_concierge: models.User,
                           concierge_token: str,
                           test_device: models.Device):
    login_data = {
        "username": test_user.email,
        "password": "password456"
    }
    login_data_concierge = {
        "username": test_concierge.email,
        "password": "password123"
    }
    response1 = client.post("/start-session",
                            headers={"Authorization": f"Bearer {concierge_token}"}, data=login_data)
    assert response1.status_code == 200
    response = client.post("/devices/change-status",
                           headers={
                               "Authorization": f"Bearer {concierge_token}"},
                           json={"issue_return_session_id": response1.json()["id"],
                                 "device_id": test_device.id})
    assert response.status_code == 200
    assert response.json()["device"]["code"] == test_device.code
    assert response.json()["issue_return_session"]["status"] == "in_progress"
    assert response.json()["operation_type"] == "issue_device"
    assert response.json()["entitled"] is True

    response2 = client.post(
        f"/approve/login/session/{ response1.json()['id']}",
        headers={"Authorization": f"Bearer {concierge_token}"},
        data=login_data_concierge
    )
    assert response2.status_code == 200
    assert response2.json() == {
        "detail": "DeviceOperations approved and devices updated successfully."}

    response3 = client.get(f"/devices/{test_device.id}",
                           headers={"Authorization": f"Bearer {concierge_token}"})
    assert response3.json()["is_taken"] is True
    assert response3.json()["last_owner_id"] == test_user.id


def test_get_all_user_devices(test_user: models.User, concierge_token: str):
    response = client.get(f"/devices/users/{test_user.id}",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200


def test_get_all_user_notes(create_user_note, concierge_token: str):
    response = client.get("/notes/users",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["note"] == "Test Note"


def test_get_user_notes(test_user: models.User, create_specific_user_note, concierge_token: str):
    response = client.get(f"/notes/users/{test_user.id}",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert response.json()[1]["note"] == "Test Specific Note"


def test_get_user_notes_not_found(concierge_token: str):
    response = client.get("/notes/users/9999",
                          headers={"Authorization": f"Bearer {concierge_token}"})

    assert response.status_code == 404
    assert response.json()["detail"] == "No note found for user id: 9999"


def test_add_user_note(test_user: models.User, concierge_token: str):
    note_data = {"user_id": test_user.id, "note": "New note for user"}
    response = client.post(f"/notes/users",
                           headers={
                               "Authorization": f"Bearer {concierge_token}"},
                           json=note_data)

    assert response.status_code == 201
    assert response.json()["note"] == "New note for user"


def test_add_user_note_invalid_data(test_user: models.User, concierge_token: str):
    note_data = {"note": "Invalid note data"}
    response = client.post(f"/notes/users",
                           headers={
                               "Authorization": f"Bearer {concierge_token}"},
                           json=note_data)

    assert response.status_code == 422


def test_get_all_device_notes(create_device_note, concierge_token: str):
    response = client.get("/notes/devices",
                          headers={"Authorization": f"Bearer {concierge_token}"})

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["note"] == "Device note content"


def test_get_device_notes_by_id(test_device: models.Device,
                                test_room: models.Room,
                                concierge_token: str):
    response = client.get(f"/notes/devices/{test_device.id}",
                          headers={"Authorization": f"Bearer {concierge_token}"})

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["note"] == "Device note content"
    assert response.json()[
        0]["note_device"]["room"]["number"] == test_room.number


def test_get_device_notes_not_found(concierge_token: str):
    response = client.get("/notes/devices/-5",
                          headers={"Authorization": f"Bearer {concierge_token}"})

    assert response.status_code == 404
    assert response.json()[
        "detail"] == "There are no notes that match the given criteria"


def test_add_device_note(db: Session,
                         test_session: models.IssueReturnSession,
                         test_device: models.Device,
                         concierge_token: str):
    operation_data = {
        "device_id": test_device.id,
        "issue_return_session_id": test_session.id,
        "operation_type": "issue_dev",
        "entitled": True
    }
    operation_service = operationService.DeviceOperationService(db)
    operation = operation_service.create_operation(operation_data)
    note_data = {"device_operation_id": operation.id,
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


def test_logout_with_valid_token(test_concierge: models.User, concierge_token: str):
    response = client.post(
        "/logout", headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert response.json() == {"detail": "User logged out successfully"}


def test_logout_with_invalid_token():
    response = client.post(
        "/logout", headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"


def test_logout_with_blacklisted_token(test_concierge: models.User, concierge_token: str):
    client.post(
        "/logout", headers={"Authorization": f"Bearer {concierge_token}"})
    response2 = client.post(
        "/logout", headers={"Authorization": f"Bearer {concierge_token}"})
    assert response2.status_code == 403
    assert response2.json()["detail"] == "You are logged out"
