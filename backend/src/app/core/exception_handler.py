from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import ResponseValidationError
from fastapi.responses import JSONResponse

# raise ResponseValidationError(
# fastapi.exceptions.ResponseValidationError: 1 validation error:
#   {'type': 'missing', 'loc': ('response', 'message'), 'msg': 'Field required', 'input': {'msg': 'all iz well'}}
def register_validation_handler(app : FastAPI):
    @app.exception_handler(ResponseValidationError)
    async def res_validation_exeception_handler(request : Request, exec : ResponseValidationError):
        print(f"{type(exec)=}")
        print(f"{exec.errors()=}")
        detail = {
            "message" : "Internal Server Error",
            "loc" : "response_body",
            "error" : exec.errors(),
        }
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )
        