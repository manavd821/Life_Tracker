from pathlib import Path
from fastapi import FastAPI
from app.core.exception_handler import register_validation_handler # response validation error
from app.auth.exception_handler import register_auth_handler
from app.core.middleware import logging_middleware

def read_secret(name : str):
    path = Path('/run/secrets') / name
    if not path.exists():
        raise RuntimeError(f"secret {name} not found")
    return path.read_text().strip()

def register_execption_handler(app : FastAPI):
    register_validation_handler(app)
    register_auth_handler(app)
    
def add_all_middlewares(app : FastAPI):
    app.middleware("http")(logging_middleware)