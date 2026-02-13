from typing import Annotated
from fastapi import (
    APIRouter, 
    Path, 
)
from fastapi.responses import JSONResponse
from app.auth.schemas import (
    AuthEmailSignUpInitRequest, 
    AuthEmailInitResponse,
    AuthEmailSignInInitRequest,
)
from app.auth.utils import (
    verify_credentinal_for_email_signup,
    verify_credentinal_for_email_signin,
)
from app.auth.security import (
    generate_access_token, 
    generate_numeric_otp, 
    hash_password,
)
from app.core.exceptions import DomainError
from app.db.config import DbSession

from app.auth.service import (
    create_user_with_email_identity,
    get_user_by_email,
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

@router.get('/set_in_cookie_test')
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

@router.get('/set_in_header_test')
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

@router.post('/create_user_test')
async def create_user_test(session : DbSession, user_data : AuthEmailSignUpInitRequest):
    await verify_credentinal_for_email_signup(session,user_data)
    
    # hash the password
    password_hash = hash_password(user_data.password)
    
    user, auth = await create_user_with_email_identity(
        session, 
        username=user_data.username,
        email=user_data.email,
        password_hash=password_hash,
        )
    
    return {
        "msg" : "User creation successful",
        "user_id" : user.user_id,
        "username" : user.username,
        "provider" : auth.provider,
        "email" : auth.email,
        "password_hash" : auth.password_hash,
        "is_verified" : auth.is_verified,
        "created_at" : auth.created_at,
    }
    
@router.get('/user_test/{email:str}')
async def get_user(session : DbSession, email : Annotated[str, Path()]):
    result = await get_user_by_email(session=session, email=email)
    
    password_hash = result.password_hash if result else ""
    print(password_hash)
    return {
        'result' :  result,
    }
    
@router.post('/email/signup', response_model=AuthEmailInitResponse)
async def email_signup(session : DbSession, user_data : AuthEmailSignUpInitRequest):
    
    # check is email exists or not
    await verify_credentinal_for_email_signup(session,user_data)
    
    # hash the password
    password_hash = hash_password(user_data.password)
    print(f"{password_hash=}")
    
    # generate otp
    otp = generate_numeric_otp()
    print(f"{otp=}")
    # send otp to user's email
    
    # Store temporary record in redis to remember state 
    # - (verification_id, email, username, password_hash, otp_hash, issued_at ,expired_at, attempts)
    
    return {
        "message" : "OTP sent Successfully",
        "verification_id" : str(otp),
    }

@router.post('/email/signin', response_model=AuthEmailInitResponse)
async def email_signin(session : DbSession, user_data : AuthEmailSignInInitRequest):
    
    # Verify credentials
    await verify_credentinal_for_email_signin(session, user_data)
    
    # generate otp
    otp = generate_numeric_otp()
    print(f"{otp=}")
    
    # Store temporary record in redis to remember state 
    # - (verification_id, email, username, password_hash, otp_hash, issued_at ,expired_at, attempts)
    
    return {
        "message" : "OTP sent Successfully",
        "verification_id" : "vid12345"
    }
    

@router.post('/verify')
async def verify_otp():
    # Fetch PendingAuthVerification by verification_id.
    
    return {
        "msg" : "otp sent successfully",
    }