import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
import httpx
from app.core.middleware import logging_middleware
from app.core.exceptions import AppError
from app.core.exception_handler import (
    handle_app_error, 
    unknown_error_handler,
    validation_error_handler,
)
from app.db.redis.config import create_redis

logger = logging.getLogger("redis_logger")


def add_all_middlewares(app : FastAPI):
    app.middleware("http")(logging_middleware)
    
def register_exception_handlers(app : FastAPI):
    app.exception_handler(AppError)(handle_app_error)
    app.exception_handler(Exception)(unknown_error_handler)
    app.exception_handler(RequestValidationError)(validation_error_handler)
    
@asynccontextmanager
async def app_lifespan(app : FastAPI):
    # before startup
    # create redis client and store it in app state
    app.state.redis = create_redis()
    # storehttpx client in app state
    app.state.httpx_client = httpx.AsyncClient(timeout=10)
     
    logger.log(
        level=logging.INFO,
        msg="Redis client has been initialized successfully",
    )
    yield
    # Shutdown
    await app.state.redis.aclose()
    await app.state.httpx_client.aclose()
    logger.log(
        level=logging.INFO,
        msg="Redis client has been shutdown successfully",
    )