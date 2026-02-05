from app.core.log_context import request_id_ctx
from contextlib import asynccontextmanager

@asynccontextmanager
async def bind_request_context(request):
    token = request_id_ctx.set(
        getattr(request.state, "request_id", None)
    )
    try:
        yield
    finally:
        request_id_ctx.reset(token)