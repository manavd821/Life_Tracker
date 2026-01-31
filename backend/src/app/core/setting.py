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
    
    
    return Setting(
        app_env = app_env,
        log_level=log_level,
        database = DatabaseConfig(**database),
    )