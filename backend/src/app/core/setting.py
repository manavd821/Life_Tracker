from dataclasses import dataclass
from app.core.utils import read_secret
from app.core.enums import ENV
import os


@dataclass
class DatabaseConfig:
    POSTGRES_DB : str
    POSTGRES_PASSWORD : str
    POSTGRES_USER : str
    POSTGRES_PORT : str = "5432"
    POSTGRES_HOST : str = "postgresql"

@dataclass
class Setting:
    app_env : ENV
    log_level : str
    database : DatabaseConfig
    jwt_secret_key : str
    access_token_expires_minutes : float
    
def load_settings() -> Setting:
    database = {
        "POSTGRES_DB" : read_secret("POSTGRES_DB"),
        "POSTGRES_PASSWORD" : read_secret("POSTGRES_PASSWORD"),
        "POSTGRES_USER" : read_secret("POSTGRES_USER"),
    }
    
    raw_env = os.getenv("APP_ENV", ENV.PRODUCTION.value)
    try:
        app_env = ENV(raw_env.upper())
    except ValueError:
        raise RuntimeError(f"Invalid APP_ENV: {raw_env}")
    
    log_level = os.getenv("LOG_LEVEL")
    if not log_level:
        log_level = "DEBUG" if app_env == ENV.DEVELOPMENT else "INFO"
    
    jwt_secret_key = read_secret("JWT_SECRET_KEY")
    access_token_expires_minutes = float(os.getenv("access_token_expires_minutes", 30.0))
    return Setting(
        app_env = app_env,
        log_level=log_level,
        database = DatabaseConfig(**database),
        jwt_secret_key = jwt_secret_key,
        access_token_expires_minutes=access_token_expires_minutes,
    )