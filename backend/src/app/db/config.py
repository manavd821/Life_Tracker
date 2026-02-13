from typing import Annotated
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from fastapi import Depends
from app.core.setting import settings

database = settings.database

POSTGRES_DB = database.POSTGRES_DB
POSTGRES_PASSWORD = database.POSTGRES_PASSWORD
POSTGRES_USER = database.POSTGRES_USER
POSTGRES_PORT = database.POSTGRES_PORT
POSTGRES_HOST = database.POSTGRES_HOST

DB_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

engine = create_async_engine(DB_URL, echo = True)

async_session = async_sessionmaker(engine, expire_on_commit=False)

async def get_db_session():
    async with async_session() as session:
        yield session

DbSession = Annotated[AsyncSession, Depends(get_db_session)]