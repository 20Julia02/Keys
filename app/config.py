from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    db_hostname: str
    db_port: str
    db_password: str
    db_name: str
    db_username: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_minutes: int

    model_config = ConfigDict(env_file="_env")


# USOS API OAuth credentials
CONSUMER_KEY = ''
CONSUMER_SECRET = ''


# LDAP server configuration
LDAP_SERVER = ''
LDAP_USER = ''
LDAP_PASSWORD = ''


settings = Settings()
