from fastapi import Request
import logging, time


logger = logging.getLogger("http.request")

async def logging_middleware(request : Request, call_next):
    start_time = time.monotonic()
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
                "duration" : round(duration*1000, 2),
            }
        )