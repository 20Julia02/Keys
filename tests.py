import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app import models, database, securityService
from app.schemas import UserCreate
from datetime import datetime
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
        faculty="Engineering"
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
        faculty="GiK"
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
def test_device(db: Session, test_room: models.Room):
    device = models.Devices(
        type="key",
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
def test_device_microphone(db: Session, test_room: models.Room):
    device = models.Devices(
        type="microphone",
        room_id=test_room.id,
        is_taken=False,
        version="backup",
        code="device_mic_101"
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


@pytest.fixture(scope="module", autouse=True)
def cleanup_db_after_tests(db: Session):
    yield
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())
    db.commit()


@pytest.fixture(scope="module")
def token_service(db: Session):
    return securityService.TokenService(db)


@pytest.fixture(scope="module")
def concierge_token(test_concierge, token_service):
    token_data = {'user_id': test_concierge.id, 'user_role': test_concierge.role.value}
    token = token_service.create_token(token_data, type="access")
    return token


def test_get_all_users(db: Session, test_concierge: models.User, concierge_token: str):
    response = client.get("/users/",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_get_user_by_id(db: Session, test_concierge: models.User, concierge_token: str):
    response = client.get(f"/users/{test_concierge.id}",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert response.json()["surname"] == test_concierge.surname


def test_create_user(db: Session, test_concierge: models.User, concierge_token: str):
    user_data = {
        "name": "Witold",
        "surname": "Zimny",
        "email": "newuser@example.com",
        "password": "password123",
        "card_code": "123456",
        "role": "concierge"
    }
    response = client.post("/users/", headers={"Authorization": f"Bearer {concierge_token}"}, json=user_data)
    assert response.status_code == 201
    assert response.json()["surname"] == user_data["surname"]


def test_create_user_duplicate_email(db: Session, test_concierge: models.User, concierge_token: str):
    user_data = {
        "email": "testconcierge@example.com",
        "password": "password123",
        "card_code": "123456",
        "photo_url": "6545321dhc",
        "role": "admin",
        "name": "Test",
        "surname": "User",
    }
    response = client.post("/users/",
                           headers={"Authorization": f"Bearer {concierge_token}"},
                           json=user_data)
    assert response.status_code == 422
    assert response.json()["detail"] == "Email is already registered"


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


def test_card_login_with_valid_card_id():
    card_data = {"card_id": "123456"}
    response = client.post("/card-login", json=card_data)
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()


def test_card_login_with_invalid_card_id():
    card_data = {"card_id": "invalid_card"}
    response = client.post("/card-login", json=card_data)
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid credentials"


def test_refresh_token_with_valid_token(test_concierge: models.User):
    token_service = securityService.TokenService(db)
    refresh_token = token_service.create_token({"user_id": test_concierge.id, "user_role": test_concierge.role.value},
                                               "refresh")
    response = client.post("/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_get_all_devices(db: Session,
                         test_concierge: models.User,
                         test_device: models.Devices,
                         test_device_microphone: models.Devices,
                         concierge_token: str):
    response = client.get("/devices/", headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 2

    response = client.get("/devices/?type=key",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1


def test_get_dev_id_by_id(db: Session, test_concierge: models.User, concierge_token: str):
    room = models.Room(number="423")
    db.add(room)
    db.commit()
    db.refresh(room)
    device = models.Devices(room_id=room.id, type="key", is_taken=False, version="primary", code="ghjjkhn")
    db.add(device)
    db.commit()
    db.refresh(device)

    response = client.get(f"/devices/{device.id}",
                          headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert response.json()["type"] == device.type.value


def test_create_device(db: Session, test_concierge: models.User, concierge_token: str):
    room = models.Room(number="301")
    db.add(room)
    db.commit()
    db.refresh(room)

    device_data = {
        "room_id": room.id,
        "version": "primary",
        "is_taken": False,
        "type": "microphone",
        "code": "123467"
    }

    response = client.post("/devices/", json=device_data,
                           headers={"Authorization": f"Bearer {concierge_token}"})

    assert response.status_code == 201
    assert response.json()["type"] == device_data["type"]


def test_create_device_with_invalid_data(test_concierge: models.User, concierge_token: str):
    device_data = {
        "is_taken": False
    }
    response = client.post("/devices/", json=device_data,
                           headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 422


def test_changeStatus_invalid_activity(db: Session, test_concierge: models.User, concierge_token: str):
    room = models.Room(number="501")
    db.add(room)
    db.commit()
    db.refresh(room)

    device = models.Devices(room_id=room.id, type="remote_controler", version="primary", code="ghjjkhn122345")
    db.add(device)
    db.commit()
    db.refresh(device)

    response = client.post(f"/devices/change-status/{device.id}",
                           headers={"Authorization": f"Bearer {concierge_token}"},
                           json={"access_token": "7u56ytrh5hgw4erfcds", "type": "bearer"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"


def test_changeStatus_with_valid_id_taking(db: Session,
                                           test_concierge: models.User,
                                           test_user: models.User,
                                           concierge_token: str):
    room = models.Room(number="601")
    db.add(room)
    db.commit()
    db.refresh(room)

    device = models.Devices(room_id=room.id, type="microphone", version="primary", code="ghjjkhn1223")
    db.add(device)
    db.commit()
    db.refresh(device)

    login_data = {
        "username": test_user.email,
        "password": "password456"
    }

    response1 = client.post("/start-activity",
                            headers={"Authorization": f"Bearer {concierge_token}"}, data=login_data)
    assert response1.status_code == 200
    response = client.post(f"/devices/change-status/{device.id}",
                           headers={"Authorization": f"Bearer {concierge_token}"},
                           json=response1.json())
    assert response.status_code == 200
    assert response.json()["is_taken"] is True
    assert response.json()["last_owner_id"] == test_user.id


def test_changeStatus_with_valid_id_returning(db: Session,
                                              test_concierge: models.User,
                                              test_user: models.User,
                                              concierge_token: str):
    room = models.Room(number="701")
    db.add(room)
    db.commit()
    db.refresh(room)

    device = models.Devices(room_id=room.id, type="key", version="primary", code="12ghjjkhn1223")
    db.add(device)
    db.commit()
    db.refresh(device)

    login_data = {
        "username": test_user.email,
        "password": "password456"
    }

    response1 = client.post("/start-activity",
                            headers={"Authorization": f"Bearer {concierge_token}"}, data=login_data)
    assert response1.status_code == 200

    client.post(f"/devices/change-status/{device.id}",
                headers={"Authorization": f"Bearer {concierge_token}"},
                json=response1.json())

    response = client.post(f"/devices/change-status/{device.id}",
                           headers={"Authorization": f"Bearer {concierge_token}"},
                           json=response1.json())

    assert response.json()["detail"] == "Device removed from unapproved data."


def test_get_user_permission_with_valid_user_id(db: Session,
                                                test_concierge: models.User,
                                                test_user: models.User,
                                                concierge_token: str):
    room = models.Room(number="121")
    db.add(room)
    db.commit()
    db.refresh(room)

    permission_data = {
        "user_id": test_user.id,
        "room_id": room.id,
        "start_reservation": datetime(2024, 12, 6, 12, 45).isoformat(),
        "end_reservation": datetime(2024, 12, 6, 14, 45).isoformat()
    }
    response1 = client.post(
        "/permissions",
        headers={"Authorization": f"Bearer {concierge_token}"},
        json=permission_data
    )
    assert response1.status_code == 200
    response = client.get(
        f"/permissions/users/{test_user.id}",
        headers={"Authorization": f"Bearer {concierge_token}"}
    )
    assert response.status_code == 200
    assert response.json()[0]["start_reservation"] == "2024-12-06T12:45:00+01:00"
    assert response.json()[0]["end_reservation"] == "2024-12-06T14:45:00+01:00"
    assert response.json()[0]["user"]["id"] == test_user.id


def test_get_user_permission_with_invalid_user_id(test_concierge: models.User, concierge_token: str):
    response = client.get("/permissions/users/9999", headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 404
    assert response.json()["detail"] == "User with id: 9999 doesn't exist"


def test_get_key_permission_with_valid_room_id(db: Session,
                                               test_concierge: models.User,
                                               test_user: models.User,
                                               concierge_token: str):
    room = models.Room(number="132")
    db.add(room)
    db.commit()
    db.refresh(room)

    permission_data = {
        "user_id": test_user.id,
        "room_id": room.id,
        "start_reservation": datetime(2024, 8, 22, 11, 45).isoformat(),
        "end_reservation": datetime(2024, 8, 22, 13, 45).isoformat()
    }

    response1 = client.post(
        "/permissions",
        headers={"Authorization": f"Bearer {concierge_token}"},
        json=permission_data
    )
    assert response1.status_code == 200
    response = client.get(
        f"/permissions/rooms/{room.id}",
        headers={"Authorization": f"Bearer {concierge_token}"}
    )
    assert response.status_code == 200
    assert response.json()[0]["start_reservation"] == "2024-08-22T11:45:00+02:00"
    assert response.json()[0]["end_reservation"] == "2024-08-22T13:45:00+02:00"
    assert response.json()[0]["user"]["id"] == test_user.id


def test_get_key_permission_with_invalid_room_id(test_concierge: models.User, concierge_token: str):
    response = client.get("/permissions/rooms/9999", headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Room with id: 9999 doesn't exist"


def test_get_all_rooms(db: Session, test_concierge: models.User, concierge_token: str):
    room = models.Room(number="202")
    db.add(room)
    db.commit()

    response = client.get("/rooms", headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_room_by_id(db: Session, test_concierge: models.User, concierge_token: str):
    room = models.Room(number="303")
    db.add(room)
    db.commit()
    db.refresh(room)

    response = client.get(f"/rooms/{room.id}", headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert response.json()["number"] == room.number


def test_create_unauthorized_user(db: Session, test_concierge: models.User, concierge_token: str):
    user_data = {
        "name": "Unauthorized",
        "surname": "User"
    }
    response = client.post("/unauthorized-users", json=user_data,
                           headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 201
    assert response.json()["surname"] == user_data["surname"]


def test_create_unauthorized_user_with_missing_data(test_concierge: models.User, concierge_token: str):
    user_data = {
        "name": "Unauthorized User"
    }
    response = client.post("/unauthorized-users", json=user_data,
                           headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 422


def test_get_unauthorized_user_by_id(db: Session, test_concierge: models.User, concierge_token: str):
    user = models.unauthorized_users(name="Unauthorized", surname="User 2")
    db.add(user)
    db.commit()
    db.refresh(user)

    response = client.get(f"/unauthorized-users/{user.id}", headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert response.json()["surname"] == user.surname


def test_get_unauthorized_user_with_invalid_id(test_concierge: models.User, concierge_token: str):
    response = client.get("/unauthorized-users/9999", headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Unauthorized user with id: 9999 doesn't exist"


def test_refresh_token_with_invalid_token():
    response = client.post("/refresh", json={"refresh_token": "invalid_token"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"


def test_logout_with_valid_token(test_concierge: models.User, concierge_token: str):
    response = client.post("/logout", headers={"Authorization": f"Bearer {concierge_token}"})
    assert response.status_code == 200
    assert response.json() == {"result": True}


def test_logout_with_invalid_token():
    response = client.post("/logout", headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"


def test_logout_with_blacklisted_token(test_concierge: models.User, concierge_token: str):
    client.post("/logout", headers={"Authorization": f"Bearer {concierge_token}"})
    response2 = client.post("/logout", headers={"Authorization": f"Bearer {concierge_token}"})
    assert response2.status_code == 403
    assert response2.json()["detail"] == "You are logged out"
