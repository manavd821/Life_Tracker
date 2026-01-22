from app.db.utils import read_secret
from pathlib import Path

def read_secret(name : str):
    path = Path('/run/secrets') / name
    if not path.exists():
        raise RuntimeError(f"secret {name} not found")
    return path.read_text().strip()

POSTGRES_DB = read_secret("POSTGRES_DB")
POSTGRES_PASSWORD = read_secret("POSTGRES_PASSWORD")
POSTGRES_USER = read_secret("POSTGRES_USER")

DB_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@postgresql:5432/{POSTGRES_DB}"

