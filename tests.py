import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app import models, database, oauth2, utils
from app.schemas import UserCreate
from datetime import datetime

client = TestClient(app)


# Fixture to set up a test database session
@pytest.fixture(scope="module")
def db():
    session = database.SessionLocal()
    try:
        yield session
    finally:
        session.close()


# Fixture to create a test user
@pytest.fixture(scope="module")
def test_concierge(db: Session):
    user_data = UserCreate(
        email="testuser@example.com",
        password="password123",
        card_code="123456",
        role="admin",
        name="Test",
        surname="User",
        faculty="Engineering"
    )
    hashed_password = utils.hash_password(user_data.password)
    hashed_card_code = utils.hash_password(user_data.card_code)
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
        email="testuser1@example.com",
        password="password456",
        card_code="7890",
        role="employee",
        name="Test12",
        surname="User34",
        faculty="GiK"
    )
    hashed_password = utils.hash_password(user_data.password)
    hashed_card_code = utils.hash_password(user_data.card_code)
    user_data.password = hashed_password
    user_data.card_code = hashed_card_code

    user = models.User(**user_data.model_dump())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user



# Test get_all_users
def test_get_all_users(db: Session, test_concierge: models.User):
    response = client.get("/users/", headers={"Authorization": f"Bearer {oauth2.create_token({'user_id': test_concierge.id, 'user_role': test_concierge.role.value}, 'access')}"})
    assert response.status_code == 200
    assert len(response.json()) >= 1  # Ensure there's at least one user


# Test get_user by ID
def test_get_user_by_id(db: Session, test_concierge: models.User):
    response = client.get(f"/users/{test_concierge.id}", headers={"Authorization": f"Bearer {oauth2.create_token({'user_id': test_concierge.id, 'user_role': test_concierge.role.value}, 'access')}"})
    assert response.status_code == 200
    assert response.json()["surname"] == test_concierge.surname


# Test create_user with valid data
def test_create_user(db: Session):
    user_data = {
        "name": "Witold",
        "surname": "Zimny",
        "email": "newuser@example.com",
        "password": "password123",
        "card_code": "123456",
        "role": "concierge"
    }
    response = client.post("/users/", json=user_data)
    assert response.status_code == 201
    assert response.json()["surname"] == user_data["surname"]


# Test create_user with duplicate email
def test_create_user_duplicate_email(db: Session, test_concierge: models.User):
    user_data = {
        "email":"testuser@example.com",
        "password":"password123",
        "card_code":"123456",
        "photo_url":"6545321dhc",
        "role":"admin",
        "name":"Test",
        "surname":"User",
    }
    response = client.post("/users/", json=user_data)
    assert response.status_code == 422
    assert response.json()["detail"] == "Email is already registered"


#Test login with correct credentials
def test_login_with_correct_credentials(test_concierge: models.User):
    login_data = {
        "username": test_concierge.email,
        "password": "password123"
    }
    response = client.post("/login", data=login_data)
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()


# Test login with incorrect credentials
def test_login_with_incorrect_credentials(test_concierge: models.User):
    login_data = {
        "username": test_concierge.email,
        "password": "wrongpassword"
    }
    response = client.post("/login", data=login_data)
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid credentials"


# Test card_login with valid card ID
def test_card_login_with_valid_card_id(test_concierge: models.User):
    card_data = {"card_id": "123456"}  # Assuming the test user has this card code
    response = client.post("/card-login", json=card_data)
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()


# Test card_login with invalid card ID
def test_card_login_with_invalid_card_id():
    card_data = {"card_id": "invalid_card"}
    response = client.post("/card-login", json=card_data)
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid credentials"


# Test refresh_token with valid token
#TODO
#nie jestem pewna czy ten refresh tak powinien być
def test_refresh_token_with_valid_token(test_concierge: models.User):
    refresh_token = oauth2.create_token({"user_id": test_concierge.id, "user_role": test_concierge.role.value}, "refresh")
    response = client.post("/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    assert "access_token" in response.json()

# #Test get_all_devices with and without filtering by type
def test_get_all_devices(db: Session, test_concierge: models.User):
    #Test without filtering
    token = oauth2.create_token({"user_id": test_concierge.id, "user_role": test_concierge.role.value}, "access")
    response = client.get("/devices/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)

    #Test with filtering by type
    response = client.get("/devices/?type=key", headers={"Authorization": f"Bearer {oauth2.create_token({'user_id': test_concierge.id, 'user_role': test_concierge.role.value}, 'access')}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# Test get_device by ID
def test_get_device_by_id(db: Session, test_concierge: models.User):
    device = models.Devices(room_id=2, type="key", is_taken=False, version="primary", code="ghjjkhn")
    db.add(device)
    db.commit()
    db.refresh(device)

    response = client.get(f"/devices/{device.id}", headers={"Authorization": f"Bearer {oauth2.create_token({'user_id': test_concierge.id, 'user_role': test_concierge.role.value}, 'access')}"})
    assert response.status_code == 200
    assert response.json()["type"] == device.type.value


# Test create_device with valid data
def test_create_device(db: Session, test_concierge: models.User):
    device_data = {
    "room_id": 3,
    "version": "primary",
    "is_taken": False,
    "type": "microphone",
    "code": "123467"
}
    response = client.post("/devices/", json=device_data, headers={"Authorization": f"Bearer {oauth2.create_token({'user_id': test_concierge.id, 'user_role': test_concierge.role.value}, 'access')}"})
    assert response.status_code == 201
    assert response.json()["type"] == device_data["type"]


# Test create_device with invalid data (e.g., missing fields)
def test_create_device_with_invalid_data(test_concierge: models.User):
    device_data = {
        "is_taken": False
    }
    response = client.post("/devices/", json=device_data, headers={"Authorization": f"Bearer {oauth2.create_token({'user_id': test_concierge.id, 'user_role': test_concierge.role.value}, 'access')}"})
    assert response.status_code == 422

# Test changeStatus with not validated user
def test_changeStatus_with_invalid_user(db: Session, test_concierge: models.User):
    device = models.Devices(room_id=3, type="remote_controler", version="primary", code="ghjjkhn122345")
    db.add(device)
    db.commit()
    db.refresh(device)
    response = client.post(f"/devices/changeStatus/{device.id}", headers={"Authorization": f"Bearer {oauth2.create_token({'user_id': test_concierge.id, 'user_role': test_concierge.role.value}, 'access')}"})
    assert response.status_code == 403
    assert response.json()["detail"] == "There is no active user"

# Test changeStatus with valid ID - taking microphone
def test_changeStatus_with_valid_id_taking(db: Session, test_concierge: models.User, test_user: models.User):
    device = models.Devices(room_id=2, type="microphone", version="primary", code="ghjjkhn1223")
    db.add(device)
    db.commit()
    db.refresh(device)

    login_data = {
        "username": test_user.email,
        "password": "password456"
    }

    response1 = client.post("/validate", headers={"Authorization": f"Bearer {oauth2.create_token({'user_id': test_concierge.id, 'user_role': test_concierge.role.value}, 'access')}"}, data=login_data)
    response = client.post(f"/devices/changeStatus/{device.id}", headers={"Authorization": f"Bearer {oauth2.create_token({'user_id': test_concierge.id, 'user_role': test_concierge.role.value}, 'access')}"})
    assert response1.status_code == 200
    assert response1.json()["is_active"] == True
    assert response.status_code == 200
    assert response.json()["is_taken"] == True

# Test changeStatus with valid ID - rescanning microphone during a single activity
def test_changeStatus_with_valid_id_returning(db: Session, test_concierge: models.User, test_user: models.User): 
    device = db.query(models.Devices).filter(models.Devices.code ==
                                          "ghjjkhn1223").first()
    response = client.post(f"/devices/changeStatus/{device.id}", headers={"Authorization": f"Bearer {oauth2.create_token({'user_id': test_concierge.id, 'user_role': test_concierge.role.value}, 'access')}"})
    assert response.status_code == 200
    assert response.json()["detail"] == "Device removed from unapproved data."

# Test get_user_permission with valid user ID
def test_get_user_permission_with_valid_user_id(db: Session, test_concierge: models.User, test_user: models.User):
    permission_data = {
        "user_id": test_user.id,
        "room_id": 2,
        "start_reservation": datetime(2024, 12, 6, 12, 45).isoformat(),
        "end_reservation": datetime(2024, 12, 6, 14, 45).isoformat()
    }
    response1 = client.post(
        "/permissions",
        headers={"Authorization": f"Bearer {oauth2.create_token({'user_id': test_concierge.id, 'user_role': test_concierge.role.value}, 'access')}"}, 
        json=permission_data
    )
    assert response1.status_code == 200
    response = client.get(
        f"/permissions/users/{test_user.id}", 
        headers={"Authorization": f"Bearer {oauth2.create_token({'user_id': test_concierge.id, 'user_role': test_concierge.role.value}, 'access')}"}
    )
    assert response.status_code == 200
    assert response.json()[0]["start_reservation"] == "2024-12-06T12:45:00+01:00"
    assert response.json()[0]["end_reservation"]== "2024-12-06T14:45:00+01:00"
    assert response.json()[0]["room"]["id"] == 2
    assert response.json()[0]["user"]["id"] == test_user.id

# Test get_user_permission with invalid user ID
def test_get_user_permission_with_invalid_user_id(test_concierge: models.User):
    response = client.get("/permissions/users/9999", headers={"Authorization": f"Bearer {oauth2.create_token({'user_id': test_concierge.id, 'user_role': test_concierge.role.value}, 'access')}"})
    assert response.status_code == 404
    assert response.json()["detail"] == "User with id: 9999 doesn't exist"

# Test get_key_permission with valid room ID
def test_get_key_permission_with_valid_room_id(db: Session, test_concierge: models.User, test_user: models.User):
    permission_data = {
        "user_id": test_user.id,
        "room_id": 1,
        "start_reservation": datetime(2024, 8, 22, 11, 45).isoformat(),
        "end_reservation": datetime(2024, 8, 22, 13, 45).isoformat()
    }

    response1 = client.post(
        "/permissions",
        headers={"Authorization": f"Bearer {oauth2.create_token({'user_id': test_concierge.id, 'user_role': test_concierge.role.value}, 'access')}"}, 
        json=permission_data
    )
    assert response1.status_code == 200
    response = client.get(
        f"/permissions/rooms/{1}", 
        headers={"Authorization": f"Bearer {oauth2.create_token({'user_id': test_concierge.id, 'user_role': test_concierge.role.value}, 'access')}"}
    )
    assert response.status_code == 200
    assert response.json()[0]["start_reservation"] == "2024-08-22T11:45:00+02:00"
    assert response.json()[0]["end_reservation"]== "2024-08-22T13:45:00+02:00"
    assert response.json()[0]["room"]["id"] == 1
    assert response.json()[0]["user"]["id"] == test_user.id


    response = client.get(f"/permissions/rooms/1", 
                          headers={"Authorization": f"Bearer {oauth2.create_token({'user_id': test_concierge.id, 'user_role': test_concierge.role.value}, 'access')}"})
    assert response.status_code == 200


# Test get_key_permission with invalid room ID
def test_get_key_permission_with_invalid_room_id(test_concierge: models.User):
    response = client.get("/permissions/rooms/9999", headers={"Authorization": f"Bearer {oauth2.create_token({'user_id': test_concierge.id, 'user_role': test_concierge.role.value}, 'access')}"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Room with id: 9999 doesn't exist"


# Test get_all_rooms
def test_get_all_rooms(db: Session, test_concierge: models.User):
    room = models.Room(number="202")
    db.add(room)
    db.commit()

    response = client.get("/rooms", headers={"Authorization": f"Bearer {oauth2.create_token({'user_id': test_concierge.id, 'user_role': test_concierge.role.value}, 'access')}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# Test get_room by ID
def test_get_room_by_id(db: Session, test_concierge: models.User):
    room = models.Room(number="303")
    db.add(room)
    db.commit()
    db.refresh(room)

    response = client.get(f"/rooms/{room.id}", headers={"Authorization": f"Bearer {oauth2.create_token({'user_id': test_concierge.id, 'user_role': test_concierge.role.value}, 'access')}"})
    assert response.status_code == 200
    assert response.json()["number"] == room.number


# Test create_unauthorized_user with valid data
def test_create_unauthorized_user(db: Session, test_concierge: models.User):
    user_data = {
        "name": "Unauthorized",
        "surname": "User"
    }
    response = client.post("/unauthorized_users", json=user_data, headers={"Authorization": f"Bearer {oauth2.create_token({'user_id': test_concierge.id, 'user_role': test_concierge.role.value}, 'access')}"})
    assert response.status_code == 201
    assert response.json()["surname"] == user_data["surname"]


# Test create_unauthorized_user with missing data
def test_create_unauthorized_user_with_missing_data(test_concierge: models.User):
    user_data = {
        "name": "Unauthorized User"
    }
    response = client.post("/unauthorized_users", json=user_data, headers={"Authorization": f"Bearer {oauth2.create_token({'user_id': test_concierge.id, 'user_role': test_concierge.role.value}, 'access')}"})
    assert response.status_code == 422  # Unprocessable Entity


# Test get_unauthorized_user by ID
def test_get_unauthorized_user_by_id(db: Session, test_concierge: models.User):
    user = models.unauthorized_users(name="Unauthorized", surname="User 2")
    db.add(user)
    db.commit()
    db.refresh(user)

    response = client.get(f"/unauthorized_users/{user.id}", headers={"Authorization": f"Bearer {oauth2.create_token({'user_id': test_concierge.id, 'user_role': test_concierge.role.value}, 'access')}"})
    assert response.status_code == 200
    assert response.json()["surname"] == user.surname

# Test get_unauthorized_user with invalid ID
def test_get_unauthorized_user_with_invalid_id(test_concierge: models.User):
    response = client.get("/unauthorized_users/9999", headers={"Authorization": f"Bearer {oauth2.create_token({'user_id': test_concierge.id, 'user_role': test_concierge.role.value}, 'access')}"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Unauthorized user with id: 9999 doesn't exist"

# Test refresh_token with invalid token
def test_refresh_token_with_invalid_token():
    response = client.post("/refresh", json={"refresh_token": "invalid_token"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"

# Test logout with valid token
def test_logout_with_valid_token(test_concierge: models.User):
    token = oauth2.create_token({"user_id": test_concierge.id, "user_role": test_concierge.role.value}, "access")
    response = client.post("/logout", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == {"result": True}

# Test logout with invalid token
def test_logout_with_invalid_token():
    response = client.post("/logout", headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"

# Test logout with blacklisted token
def test_logout_with_blacklisted_token(test_concierge: models.User):
    token = oauth2.create_token({"user_id": test_concierge.id, "user_role": test_concierge.role.value}, "access")
    client.post("/logout", headers={"Authorization": f"Bearer {token}"})
    response2 = client.post("/logout", headers={"Authorization": f"Bearer {token}"})
    assert response2.status_code == 403
    assert response2.json()["detail"] == "You are logged out"