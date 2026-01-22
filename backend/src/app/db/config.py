from pathlib import Path
from typing import Annotated
from sqlalchemy.ext.asyncio import create_async_engine, AsyncConnection
from fastapi import Depends

def read_secret(name : str):
    path = Path('/run/secrets') / name
    if not path.exists():
        raise RuntimeError(f"secret {name} not found")
    return path.read_text().strip()

POSTGRES_DB = read_secret("POSTGRES_DB")
POSTGRES_PASSWORD = read_secret("POSTGRES_PASSWORD")
POSTGRES_USER = read_secret("POSTGRES_USER")

DB_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@postgresql:5432/{POSTGRES_DB}"

engine = create_async_engine(DB_URL, echo = True)

async def get_db_session():
    async with engine.connect() as session:
        yield session

DbSession = Annotated[AsyncConnection, Depends(get_db_session)]