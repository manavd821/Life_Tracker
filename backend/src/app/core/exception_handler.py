import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.exceptions import AppError
from app.core.log_context import request_id_ctx
from app.core.context import bind_request_context

logger = logging.getLogger("app.exceptions")

async def unknown_error_handler(request : Request, exec : Exception):
    
    async with bind_request_context(request):
        logger.critical(
            "Unhandled exception",
            exc_info=True,
        )
        return JSONResponse(
            content={
                "code" : "INTERNAL_SERVER_ERROR",
                "message" : "Something went wrong",
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
        
async def handle_app_error(request : Request,exec : AppError):
    
    async with bind_request_context(request):
        logging.log(
            exec.log_level,
            exec.message,
            exc_info=exec.log_level >= logging.ERROR,
            extra={"error_code" : exec.code},
        )
        payload = {
            "code" : exec.code,
        }
        
        if exec.expose:
            payload["message"] = exec.message
            
        return JSONResponse(
            content=payload,
            status_code=exec.status_code,
        )
    

async def validation_error_handler(request : Request,exec: RequestValidationError):
    # client error
    async with bind_request_context(request):
        details = [{
            "field" : error["loc"][-1],
            "reason" :  error["msg"],
        } for error in exec.errors()]
            
        payload = {
            "code" : "VALIDATION_ERROR",
            "message" : "Invalid request payload",
            "details" : details
        }
        return JSONResponse(
            content=payload,
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )
        