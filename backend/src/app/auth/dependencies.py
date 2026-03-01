from typing import Annotated
from fastapi import Depends, Request
from httpx import AsyncClient
from app.auth.security import decode_access_token
from app.core.exceptions import AuthError
from redis.asyncio import Redis

async def get_current_user(request : Request):
    token = request.cookies.get("access_token")
    
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        else:
            raise AuthError("Access token required", code="MISSING_ACCESS_TOKEN")
    
    payload = decode_access_token(token)
    
    user_id = payload.get("sub")
    session_id = payload.get("session_id")
    role = payload.get("role")
    
    if not user_id:
        raise AuthError("Invalid token payload", code="INVALID_ACCESS_TOKEN_PAYLOAD")
    
    # Inject into request context
    request.state.user_id = user_id
    request.state.session_id = session_id
    request.state.role = role
    
    return user_id

async def get_redis_client(request : Request):
    return request.app.state.redis

async def get_httpx_client(request : Request):
    return request.app.state.httpx_client

current_user = Annotated[dict, Depends(get_current_user)]
redis_client = Annotated[Redis, Depends(get_redis_client)]
httpx_client = Annotated[AsyncClient, Depends(get_httpx_client)]