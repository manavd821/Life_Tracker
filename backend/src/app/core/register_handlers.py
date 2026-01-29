from fastapi import FastAPI
from app.core.exception_handler import register_validation_handler # response validation error
from app.auth.exception_handler import register_auth_handler

def register_execption_hander(app : FastAPI):
    register_validation_handler(app)
    register_auth_handler(app)