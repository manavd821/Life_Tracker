from typing import Annotated
from fastapi import APIRouter, Path, Request
from fastapi.responses import JSONResponse
from app.auth.schemas import AuthSignUpInitRequest, AuthSignUpInitResponse
from app.auth.utils import verify_credentinal
from app.auth.security import generate_access_token
from app.db.config import DbSession

from app.auth.service import (
    create_user_with_email_identity,
    get_user_by_email
)

router = APIRouter()
### Server Logic
# 1. Verify Credentials
# 2. Look up for provider
#     - if provider = EMAIL -> Send OTP message to client's email -> client verify OTP on /auth/verify route
#     - Provider is 3rd party(i.e. Google, Github) -> authentication succesful
# 3. generate access + refresh tokens
# 4. Upadate db with email, provider, is_verified:true, hashed_refresh_tokens, etc .
# 5. Store access + refresh token in headers or cookie.
# Password → argon2 (slow, salted)
# Refresh token → SHA256 (fast, deterministic)

# jwt payload
# {
#   "sub": "user_id",
#   "session_id": "uuid",
#   "iat": 1710000000,
#   "exp": 1710000900,
#   "type": "access"
# }

@router.get('/set_in_cookie')
async def generate_access():
    token = generate_access_token("manav123", "s1")
    res = JSONResponse(
        content={
            "msg" : "successful", 
            "token" : token,
        }
    )
    res.set_cookie("access_token", token, max_age=20, httponly=True, samesite="lax", secure=True)
    return res

@router.get('/set_in_header')
async def generate_access_header():
    token = generate_access_token("manav123", "s1")
    res = JSONResponse(
        content={
            "msg" : "successful", 
            "token" : token,
        }
    )
    res.headers.append("Authorization", f"Bearer {token}")
    return res

@router.get('/user/{email:str}')
async def get_user(session : DbSession, email : Annotated[str, Path()]):
    result = await get_user_by_email(session=session, email=email)
    
    return {
        'result' :  result,
    }
    
@router.post('/signup', response_model=AuthSignUpInitResponse)
async def signup(session : DbSession, data : AuthSignUpInitRequest):
    await verify_credentinal(data)
    # check is email exists or not
    await create_user_with_email_identity(
        session,
        username=data.username,
        email=data.email,
        password_hash=data.password
    )
    
    
    return {
        "message" : "all iz well",
    }

@router.post('/verify')
async def verify_otp():
    return {
        "msg" : "otp sent successfully",
    }