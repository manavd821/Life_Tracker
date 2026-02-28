from fastapi import APIRouter, Path
from fastapi.responses import JSONResponse
from app.auth.security import (
    generate_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
)
from app.auth.utils import (
    # verify_credentinal_for_email_signin,
    verify_credentinal_for_email_signup,
)
from app.auth.service import (
    create_user_with_email_identity,
    get_user_by_email,
)
from app.db.config import DbSession
from app.auth.schemas import AuthEmailSignUpInitRequest
from typing import Annotated

router = APIRouter()

@router.get('/set_in_cookie_test')
async def generate_access():
    token = generate_access_token("manav123", "s1")
    refresh_token = hash_refresh_token(generate_refresh_token())
    res = JSONResponse(
        content={
            "msg" : "successful", 
            "token" : token,
        }
    )
    res.set_cookie("access_token", token, max_age=20, httponly=True, samesite="lax", secure=True)
    res.set_cookie("refresh_token", refresh_token, max_age=3600, httponly=True, samesite="lax", secure=True)
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
