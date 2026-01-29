from app.auth.exceptions import AuthError
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

def register_auth_handler(app : FastAPI):
    @app.exception_handler(AuthError)
    async def auth_error_handler(request : Request, exec : AuthError):
        return JSONResponse(
            status_code=exec.status_code,
            content={
                "error" : exec.code,
                "message" : exec.message,
            },
        )