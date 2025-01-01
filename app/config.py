from pydantic_settings import BaseSettings
import logging
from logging.handlers import RotatingFileHandler


class Settings(BaseSettings):
    db_hostname: str = ""
    db_port: str = ""
    db_password: str = ""
    db_name: str = ""
    db_username: str = ""
    secret_key: str = ""
    algorithm: str = ""
    access_token_expire_minutes: int = 0
    refresh_token_expire_minutes: int = 0

    class Config:
        env_file = "_env"
        env_file_encoding = "utf-8"


try:
    settings = Settings()
except Exception as e:
    raise ValueError("Failed to load settings:") from e

handler = RotatingFileHandler(
    "app.log",
    maxBytes=5 * 1024 * 1024,
    backupCount=2
)

formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)

logger = logging.getLogger("app_logger")
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)
