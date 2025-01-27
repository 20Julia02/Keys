# type: ignore

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from faker import Faker
from app import models, database, schemas
from app.services import securityService
import random
from sqlalchemy import func
from sqlalchemy import text
import sqlalchemy

fake = Faker()


def create_fake_user(session: Session):
    while True:
        email = fake.email()
        if session.query(models.user.User).filter_by(email=email).first():
            continue
        
        user_data = schemas.UserCreate(
            email=email,
            password=fake.word(),
            card_code=fake.uuid4(),
            role=random.choice(["pracownik", "administrator", "portier", "student", "gość"]),
            name=fake.first_name(),
            surname=fake.last_name(),
            faculty="Geodezji i Kartografii"
        )
        password_service = securityService.PasswordService()
        hashed_password = password_service.hash_password(user_data.password)
        user_data.password = hashed_password
        
        try:
            user = models.user.User(**user_data.model_dump())
            session.add(user)
            session.commit()
            session.refresh(user)
            return user
        except sqlalchemy.exc.IntegrityError:
            session.rollback()
            continue



def add_fake_users():
    session = database.SessionLocal()
    try:
        password_service = securityService.PasswordService()
        user_data = schemas.UserCreate(
            email="julia@example.com",
            password=password_service.hash_password("haslo123"),
            card_code=fake.uuid4(),
            role="portier",
            name=fake.first_name(),
            surname=fake.last_name(),
            faculty="Geodezji i Kartografii"
        )
        user = models.user.User(**user_data.model_dump())
        session.add(user)
        session.commit()
        session.refresh(user)
        for _ in range(400):
            create_fake_user(session)
    finally:
        session.close()


def create_fake_device(session: Session):
    rooms = session.query(models.device.Room).all()

    if not rooms:
        raise ValueError("Brak pokoi w bazie. Nie można utworzyć urządzenia.")

    device_combinations = [
        (dev_type, dev_version) for dev_type in ["klucz", "mikrofon", "pilot"]
        for dev_version in ["podstawowa", "zapasowa"]
    ]

    while True:
        room = random.choice(rooms)
        dev_type, dev_version = random.choice(device_combinations)

        if session.query(models.device.Device).filter_by(
            dev_type=dev_type, room_id=room.id, dev_version=dev_version
        ).first():
            continue

        device_data = schemas.DeviceCreate(
            code=fake.uuid4(),
            dev_type=dev_type,
            room_id=room.id,
            dev_version=dev_version,
        )

        try:
            device = models.device.Device(**device_data.model_dump())
            session.add(device)
            session.commit()
            session.refresh(device)
            return device
        except sqlalchemy.exc.IntegrityError:
            session.rollback()
            continue


def add_fake_devices():
    session = database.SessionLocal()
    try:
        total_devices = 0
        while total_devices < 2000:
            device = create_fake_device(session)
            if device:
                total_devices += 1
    finally:
        session.close()


def create_fake_device_operation(session: Session):
    while True:
        device = session.query(models.device.Device).order_by(
            func.random()).first()
        confirmed_session = session.query(models.operation.UserSession).filter(
            models.operation.UserSession.status == "potwierdzona"
        ).order_by(func.random()).first()

        if not device or not confirmed_session:
            continue

        existing_device_operation = session.query(models.operation.DeviceOperation).filter_by(
            device_id=device.id,
            session_id=confirmed_session.id,
        ).first()

        if existing_device_operation:
            continue

        hours_back = random.randint(0, 10)
        timestamp = datetime.now() - timedelta(hours=hours_back)

        device_operation_data = models.operation.DeviceOperation(
            device_id=device.id,
            session_id=confirmed_session.id,
            operation_type=fake.random_element(elements=["pobranie", "zwrot"]),
            entitled=fake.boolean(),
            timestamp=timestamp
        )

        try:
            session.add(device_operation_data)
            session.commit()
            session.refresh(device_operation_data)
            return device_operation_data
        except sqlalchemy.exc.IntegrityError:
            session.rollback()
            continue


def add_fake_device_operations():
    session = database.SessionLocal()
    try:
        total_operations = 0
        while total_operations < 8000:
            created_operation = create_fake_device_operation(session)
            if created_operation:
                total_operations += 1
    finally:
        session.close()


def create_fake_session(session: Session):
    users = session.query(models.user.User).all()
    concierges = session.query(models.user.User).filter(
        models.user.User.role == "portier").all()
    user = random.choice(users) if users else None
    concierge = random.choice(concierges) if concierges else None
    if concierge and user:
        session_data = models.operation.UserSession(
            user_id=user.id,
            concierge_id=concierge.id,
            start_time=fake.date_this_year(),
            end_time=fake.date_this_year(),
            status=fake.random_element(
                elements=["w trakcie", "potwierdzona", "odrzucona"])
        )
        session.add(session_data)
        session.commit()
        session.refresh(session_data)
        return session_data


def add_fake_sessions():
    session = database.SessionLocal()
    try:
        for _ in range(5000):
            create_fake_session(session)
    finally:
        session.close()


def create_fake_device_note(session: Session):
    devices = session.query(models.device.Device).all()
    device = random.choice(devices) if devices else None

    device_note_data = models.device.DeviceNote(
        device_id=device.id if device else None,
        note=fake.sentence(),
        timestamp=datetime.now()
    )
    session.add(device_note_data)
    session.commit()
    session.refresh(device_note_data)
    return device_note_data


def add_fake_device_notes():
    session = database.SessionLocal()
    try:
        for _ in range(200):
            create_fake_device_note(session)
    finally:
        session.close()


def create_fake_user_note(session: Session):
    users = session.query(models.user.BaseUser).all()
    user = random.choice(users) if users else None

    user_note_data = models.user.UserNote(
        user_id=user.id if user else None,
        note=fake.sentence(),
        timestamp=datetime.now()
    )
    session.add(user_note_data)
    session.commit()
    session.refresh(user_note_data)
    return user_note_data


def add_fake_user_notes():
    session = database.SessionLocal()
    try:
        for _ in range(400):
            create_fake_user_note(session)
    finally:
        session.close()


def create_fake_permission(session: Session):
    users = session.query(models.user.User).all()
    rooms = session.query(models.device.Room).all()

    user = random.choice(users) if users else None
    room = random.choice(rooms) if rooms else None

    if not user or not room:
        return None

    today = datetime.today().date()
    max_date = today + timedelta(days=365)
    reservation_date = fake.date_between_dates(
        date_start=today, date_end=max_date
    )

    start_hour = random.randint(8, 17)
    start_minute = random.choice([0, 15, 30, 45])

    start_time = datetime.min.time().replace(hour=start_hour, minute=start_minute)

    duration_in_minutes = random.choice([15, 30, 45, 60, 90, 120])
    end_time = (datetime.combine(today, start_time) +
                timedelta(minutes=duration_in_minutes)).time()

    permission_data = models.permission.Permission(
        user_id=user.id,
        room_id=room.id,
        date=reservation_date,
        start_time=start_time,
        end_time=end_time
    )

    session.add(permission_data)
    session.commit()
    session.refresh(permission_data)
    return permission_data


def add_fake_permissions():
    session = database.SessionLocal()
    try:
        for _ in range(400):
            create_fake_permission(session)
    finally:
        session.close()


def initialize_room_table_if_empty():
    session = database.SessionLocal()
    room_count = session.execute(text("SELECT COUNT(*) FROM room")).scalar()
    if room_count == 0:
        session.execute(text("""
            COPY room (number)
            FROM 'C:\\Users\\Julia\\Desktop\\praca_front_back\\praca_back\\rooms_baza.csv'
            DELIMITER ','
            CSV HEADER;
        """))
        session.commit()


if __name__ == "__main__":
    initialize_room_table_if_empty()
    add_fake_users()
    add_fake_permissions()
    add_fake_devices()
    add_fake_sessions()
    add_fake_device_operations()
    add_fake_device_notes()
    add_fake_user_notes()
