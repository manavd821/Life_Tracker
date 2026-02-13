from app.auth.schemas import AuthEmailSignInInitRequest, AuthEmailSignUpInitRequest
from app.core.exceptions import AuthError, ClientError, DomainError
from app.auth.service import (
    get_user_by_email,
    update_password_hash,
)
from app.auth.security import verify_password
from sqlalchemy.ext.asyncio import AsyncSession

async def verify_credentinal_for_email_signup(session : AsyncSession, data : AuthEmailSignUpInitRequest) -> None:
        
    if len(data.password) < 5 :
        raise ClientError("Password must be at least 5 character")
    
    if await get_user_by_email(session, data.email):
        raise DomainError(
                message="Can't create user. Email already exist",
                code="EMAIL_ALREADY_EXISTS",
        )
    
async def verify_credentinal_for_email_signin(session : AsyncSession, data : AuthEmailSignInInitRequest) -> None:
    
    user = await get_user_by_email(session, data.email)
    
    # check if email exists
    if not user:
        raise DomainError(
            message="Email doesn't exists",
            code="EMAIL_DOES_NOT_EXIST",
        )
    # verify password 
    valid, new_hash = verify_password(data.password, user.password_hash)
    if not valid:
        raise AuthError(
            message="Invalid email or password",
            code="INVALID_CREDENTIALS"
        )
    # if hashing algorith updated then store new hashed password inside db
    if new_hash:
        await update_password_hash(session, user, new_hash)
    