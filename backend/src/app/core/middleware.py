from fastapi import Request
import logging
import time
import uuid
from app.core.log_context import request_id_ctx

logger = logging.getLogger("http.request")

async def logging_middleware(request : Request, call_next):
    start_time = time.monotonic()
    
    req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = req_id
    token = request_id_ctx.set(req_id)
    response = None
    
    try:
        response = await call_next(request)
        return response
    except Exception:
        logger.exception("Unhandled exception")
        raise
    finally:
        duration = time.monotonic() - start_time 
        status_code = response.status_code if response is not None else 500
        print(request.url.path)
        logger.info(
            "%s %s",
            request.method,
            request.url.path,
            extra={
                "status_code" : status_code,
                "duration_ms" : round(duration*1000, 2),
            }
        )
        request_id_ctx.reset(token)