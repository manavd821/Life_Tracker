from pathlib import Path
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from app.core.middleware import logging_middleware
from app.core.exceptions import AppError
from app.core.exception_handler import (
    handle_app_error, 
    unknown_error_handler,
    validation_error_handler,
)

def read_secret(name : str):
    path = Path('/run/secrets') / name
    if not path.exists():
        raise RuntimeError(f"secret {name} not found")
    return path.read_text().strip()

def add_all_middlewares(app : FastAPI):
    app.middleware("http")(logging_middleware)
    
def register_exception_handlers(app : FastAPI):
    app.exception_handler(AppError)(handle_app_error)
    app.exception_handler(Exception)(unknown_error_handler)
    app.exception_handler(RequestValidationError)(validation_error_handler)