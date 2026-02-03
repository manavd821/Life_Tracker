from pathlib import Path
from fastapi import FastAPI
from app.core.middleware import logging_middleware

def read_secret(name : str):
    path = Path('/run/secrets') / name
    if not path.exists():
        raise RuntimeError(f"secret {name} not found")
    return path.read_text().strip()

def add_all_middlewares(app : FastAPI):
    app.middleware("http")(logging_middleware)