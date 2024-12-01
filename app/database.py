from sqlalchemy import create_engine, exc
from app.models import base
from sqlalchemy.orm import sessionmaker
from app.config import settings, logger
import time

SQLALCHEMY_DATABASE_URL = f'postgresql://{settings.db_username}:{settings.db_password}@{settings.db_hostname}:{settings.db_port}/{settings.db_name}'

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """
    Creates all tables in the database.
    """
    try:
        logger.info("Creating all tables in the database.")
        base.Base.metadata.create_all(bind=engine)
        logger.info("Tables created successfully.")
    except Exception as e:
        logger.error(f"Error while creating tables: {e}")
        raise


def get_db():
    """
    Retrieves a database session and ensures that it is properly closed after use.
    Implements retry logic in case of database connection errors.

    This function attempts to establish a connection to the database up to a specified number of retries 
    in case of operational errors (e.g., network issues, database downtime). If the connection fails after 
    the maximum number of retries, a critical error is logged and the function raises an exception.

    Yields:
        Session: A SQLAlchemy database session object that can be used to query the database.

    Raises:
        HTTPException: If the maximum retry attempts are exhausted and the database connection cannot be established.
    """
    db = None
    retries = 3
    for attempt in range(retries):
        try:
            db = SessionLocal()
            logger.info("Database session opened.")
            yield db
            break
        except exc.OperationalError as e:
            logger.critical(f"Database connection error: {e}. Attempt {attempt + 1} of {retries}.")
            if attempt < retries - 1:
                time.sleep(5)
            else:
                logger.critical("Max retries reached. Unable to connect to the database.")
                raise
        finally:
            if db:
                logger.info("Closing database session.")
                db.close()
                logger.info("Database session closed successfully.")
