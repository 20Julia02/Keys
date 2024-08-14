import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app import models, database, oauth2, utils
from app.schemas import UserCreate

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
def test_user(db: Session):
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


# Test get_all_users
def test_get_all_users(db: Session, test_user: models.User):
    response = client.get("/users/", headers={"Authorization": f"Bearer {oauth2.create_token({'user_id': test_user.id, 'user_role': test_user.role.value}, 'access')}"})
    assert response.status_code == 200
    assert len(response.json()) >= 1  # Ensure there's at least one user


# Test get_user by ID
def test_get_user_by_id(db: Session, test_user: models.User):
    response = client.get(f"/users/{test_user.id}", headers={"Authorization": f"Bearer {oauth2.create_token({'user_id': test_user.id, 'user_role': test_user.role.value}, 'access')}"})
    assert response.status_code == 200
    assert response.json()["surname"] == test_user.surname


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
def test_create_user_duplicate_email(db: Session, test_user: models.User):
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
def test_login_with_correct_credentials(test_user: models.User):
    login_data = {
        "username": test_user.email,
        "password": "password123"
    }
    response = client.post("/login", data=login_data)
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()


# Test login with incorrect credentials
def test_login_with_incorrect_credentials(test_user: models.User):
    login_data = {
        "username": test_user.email,
        "password": "wrongpassword"
    }
    response = client.post("/login", data=login_data)
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid credentials"


# Test card_login with valid card ID
def test_card_login_with_valid_card_id(test_user: models.User):
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
def test_refresh_token_with_valid_token(test_user: models.User):
    refresh_token = oauth2.create_token({"user_id": test_user.id, "user_role": test_user.role.value}, "refresh")
    response = client.post("/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    assert "access_token" in response.json()


# Test refresh_token with invalid token
def test_refresh_token_with_invalid_token():
    response = client.post("/refresh", json={"refresh_token": "invalid_token"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"


# Test logout with valid token
def test_logout_with_valid_token(test_user: models.User):
    token = oauth2.create_token({"user_id": test_user.id, "user_role": test_user.role.value}, "access")
    response = client.post("/logout", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == {"result": True}


# Test logout with invalid token
def test_logout_with_invalid_token():
    response = client.post("/logout", headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"

# Test logout with blacklisted token
def test_logout_with_invalid_token(test_user: models.User):
    token = oauth2.create_token({"user_id": test_user.id, "user_role": test_user.role.value}, "access")
    client.post("/logout", headers={"Authorization": f"Bearer {token}"})
    response2 = client.post("/logout", headers={"Authorization": f"Bearer {token}"})
    assert response2.status_code == 403
    assert response2.json()["detail"] == "You are logged out"

# #Test get_all_devices with and without filtering by type
# def test_get_all_devices(db: Session, test_user: models.User):
#     #Test without filtering
#     response = client.get("/devices/", headers={"Authorization": f"Bearer {oauth2.create_token({'user_id': test_user.id, 'user_role': test_user.role.value}, 'access')}"})
#     assert response.status_code == 200
#     assert isinstance(response.json(), list)

#     #Test with filtering by type
#     response = client.get("/devices/?type=key", headers={"Authorization": f"Bearer {oauth2.create_token({'user_id': test_user.id, 'user_role': test_user.role.value}, 'access')}"})
#     assert response.status_code == 200
#     assert isinstance(response.json(), list)


# # Test get_device by ID
# def test_get_device_by_id(db: Session, test_user: models.User):
#     device = models.Devices(type="key", is_taken=False)
#     db.add(device)
#     db.commit()
#     db.refresh(device)

#     response = client.get(f"/devices/{device.id}", headers={"Authorization": f"Bearer {oauth2.create_token({'user_id': test_user.id, 'user_role': test_user.role.value}, 'access')}"})
#     assert response.status_code == 200
#     assert response.json()["type"] == device.type


# Test create_device with valid data
# def test_create_device(db: Session, test_user: models.User):
#     device_data = {
#     "room_id": 3,
#     "version": "primary",
#     "is_taken": False,
#     "type": "microphone",
#     "code": "123467"
# }
#     response = client.post("/devices/", json=device_data, headers={"Authorization": f"Bearer {oauth2.create_token({'user_id': test_user.id, 'user_role': test_user.role.value}, 'access')}"})
#     assert response.status_code == 201
#     assert response.json()["type"] == device_data["type"]


# # Test create_device with invalid data (e.g., missing fields)
# def test_create_device_with_invalid_data(test_user: models.User):
#     device_data = {
#         "is_taken": False
#     }
#     response = client.post("/devices/", json=device_data, headers={"Authorization": f"Bearer {oauth2.create_token({'user_id': test_user.id, 'user_role': test_user.role.value}, 'access')}"})
#     assert response.status_code == 422  # Unprocessable Entity


# # Test change_status with valid ID
# def test_change_status_with_valid_id(db: Session, test_user: models.User):
#     device = models.Devices(type="tablet", is_taken=False)
#     db.add(device)
#     db.commit()
#     db.refresh(device)

#     response = client.patch(f"/devices/changeStatus/{device.id}", headers={"Authorization": f"Bearer {oauth2.create_token({'user_id': test_user.id, 'user_role': test_user.role.value}, 'access')}"})
#     assert response.status_code == 200
#     assert response.json()["is_taken"] == True  # Status should change


# # Test change_status with invalid ID
# def test_change_status_with_invalid_id(test_user: models.User):
#     response = client.patch("/devices/changeStatus/9999", headers={"Authorization": f"Bearer {oauth2.create_token({'user_id': test_user.id, 'user_role': test_user.role.value}, 'access')}"})
#     assert response.status_code == 404
#     assert response.json()["detail"] == "Device with id: 9999 doesn't exist"


# # Test get_user_permission with valid user ID
# def test_get_user_permission_with_valid_user_id(db: Session, test_user: models.User):
#     response = client.get(f"/devices/users/{test_user.id}", headers={"Authorization": f"Bearer {oauth2.create_token({'user_id': test_user.id, 'user_role': test_user.role.value}, 'access')}"})
#     assert response.status_code == 200
#     assert isinstance(response.json(), list)


# # Test get_user_permission with invalid user ID
# def test_get_user_permission_with_invalid_user_id(test_user: models.User):
#     response = client.get("/devices/users/9999", headers={"Authorization": f"Bearer {oauth2.create_token({'user_id': test_user.id, 'user_role': test_user.role.value}, 'access')}"})
#     assert response.status_code == 404
#     assert response.json()["detail"] == "User with id: 9999 doesn't exist"


# # Test get_key_permission with valid room ID
# def test_get_key_permission_with_valid_room_id(db: Session, test_user: models.User):
#     room = models.Room(number="101")
#     db.add(room)
#     db.commit()
#     db.refresh(room)

#     response = client.get(f"/devices/rooms/{room.id}", headers={"Authorization": f"Bearer {oauth2.create_token({'user_id': test_user.id, 'user_role': test_user.role.value}, 'access')}"})
#     assert response.status_code == 200
#     assert isinstance(response.json(), list)


# # Test get_key_permission with invalid room ID
# def test_get_key_permission_with_invalid_room_id(test_user: models.User):
#     response = client.get("/devices/rooms/9999", headers={"Authorization": f"Bearer {oauth2.create_token({'user_id': test_user.id, 'user_role': test_user.role.value}, 'access')}"})
#     assert response.status_code == 404
#     assert response.json()["detail"] == "Room with id: 9999 doesn't exist"


# # Test get_all_rooms
# def test_get_all_rooms(db: Session, test_user: models.User):
#     room = models.Room(number="202")
#     db.add(room)
#     db.commit()

#     response = client.get("/devices/rooms/", headers={"Authorization": f"Bearer {oauth2.create_token({'user_id': test_user.id, 'user_role': test_user.role.value}, 'access')}"})
#     assert response.status_code == 200
#     assert isinstance(response.json(), list)


# # Test get_room by ID
# def test_get_room_by_id(db: Session, test_user: models.User):
#     room = models.Room(number="303")
#     db.add(room)
#     db.commit()
#     db.refresh(room)

#     response = client.get(f"/devices/rooms/{room.id}", headers={"Authorization": f"Bearer {oauth2.create_token({'user_id': test_user.id, 'user_role': test_user.role.value}, 'access')}"})
#     assert response.status_code == 200
#     assert response.json()["number"] == room.number


# # Test create_unauthorized_user with valid data
# def test_create_unauthorized_user(db: Session, test_user: models.User):
#     user_data = {
#         "email": "unauthorizeduser@example.com",
#         "name": "Unauthorized User"
#     }
#     response = client.post("/unauthorized_users/", json=user_data, headers={"Authorization": f"Bearer {oauth2.create_token({'user_id': test_user.id, 'user_role': test_user.role.value}, 'access')}"})
#     assert response.status_code == 201
#     assert response.json()["email"] == user_data["email"]


# # Test create_unauthorized_user with missing data
# def test_create_unauthorized_user_with_missing_data(test_user: models.User):
#     user_data = {
#         "name": "Unauthorized User"
#     }
#     response = client.post("/unauthorized_users/", json=user_data, headers={"Authorization": f"Bearer {oauth2.create_token({'user_id': test_user.id, 'user_role': test_user.role.value}, 'access')}"})
#     assert response.status_code == 422  # Unprocessable Entity


# # Test get_unauthorized_user by ID
# def test_get_unauthorized_user_by_id(db: Session, test_user: models.User):
#     user = models.UnauthorizedUsers(email="unauthorizeduser2@example.com", name="Unauthorized User 2")
#     db.add(user)
#     db.commit()
#     db.refresh(user)

#     response = client.get(f"/unauthorized_users/{user.id}", headers={"Authorization": f"Bearer {oauth2.create_token({'user_id': test_user.id, 'user_role': test_user.role.value}, 'access')}"})
#     assert response.status_code == 200
#     assert response.json()["email"] == user.email


# # Test get_unauthorized_user with invalid ID
# def test_get_unauthorized_user_with_invalid_id(test_user: models.User):
#     response = client.get("/unauthorized_users/9999", headers={"Authorization": f"Bearer {oauth2.create_token({'user_id': test_user.id, 'user_role': test_user.role.value}, 'access')}"})
#     assert response.status_code == 404
#     assert response.json()["detail"] == "Unauthorized user with id: 9999 doesn't exist"
