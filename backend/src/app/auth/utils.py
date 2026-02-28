import logging
import uuid

from fastapi import Request, Response
from app.core.exceptions import AuthError, ClientError, DomainError, ServerError
from app.core.setting import settings
from app.auth.models import AuthIdentity, RefreshToken
from app.auth.schemas import (
    AuthEmailSignInInitRequest, 
    AuthEmailSignUpInitRequest,
    RedisSignInData,
    RedisSignUpData,
)
from app.auth.service import (
    get_user_by_email,
    revoke_all_auth_session,
    revoke_auth_session_by_token_object,
    update_password_hash,
    get_refresh_token_data_by_hashed_token,
    rotate_and_insert_new_refresh_token
)
from app.auth.security import (
    generate_access_token,
    generate_refresh_token,
    hash_password,
    verify_password,
    hash_refresh_token,
)
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from redis.exceptions import RedisError
from app.core.enums import ENV, MAX_OTP_ATTEMPTS
import datetime

async def extract_refresh_token(request : Request, not_found_ok : bool = False):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            refresh_token = auth_header.split(" ")[1]
        elif not not_found_ok:
            raise DomainError(
                "Refresh token not found",
                code="MISSING_REFRESH_TOKEN",
            )
    return refresh_token
    
async def verify_credentinal_for_email_signup(session : AsyncSession, data : AuthEmailSignUpInitRequest) -> None:
        
    if len(data.password) < 5 :
        raise ClientError("Password must be at least 5 character")
    
    if await get_user_by_email(session, data.email):
        raise DomainError(
                message="Can't create user. Email already exist",
                code="EMAIL_ALREADY_EXISTS",
        )
    
async def verify_credentinal_for_email_signin(session : AsyncSession, data : AuthEmailSignInInitRequest) -> AuthIdentity | None:
    
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
    
    # user must be verified for signin
    if not user.is_verified:
        raise AuthError(
            message="Email not verified",
            code="EMAIL_NOT_VERIFIED"
        )
    return user
    
async def authenticate_refresh_token(session : AsyncSession, token : str) -> RefreshToken | None:
    # hash refresh token and find it in db
    refresh_token_hash = hash_refresh_token(token)
    # find token in DB
    db_refresh_token = await get_refresh_token_data_by_hashed_token(session, refresh_token_hash)

    # if not found -> reject
    if not db_refresh_token:
        raise DomainError(
            "Invalid or expired refresh token",
            code="REFRESH_TOKEN_INVALID"
        )
    # - if rotated_at != NULL -> SECURITY ALERT(reuse detected)
    if db_refresh_token.rotated_at:
        # revoke all session
        await revoke_all_auth_session(session, db_refresh_token.user_id)
        
        raise DomainError(
            "Refresh token reuse detected",
            code="REFRESH_TOKEN_REUSE_DETECTED",
            log_level=logging.CRITICAL,
        )
    # - if revoked_at != NULL -> reject
    if db_refresh_token.revoked_at:
        raise DomainError(
            "Refresh token has been revoked",
            code="REFRESH_TOKEN_REVOKED",
        )
    # - if expired_at < now> -> reject
    if db_refresh_token.expires_at <= datetime.datetime.now(datetime.UTC):
        raise DomainError(
            "Refresh token has expired",
            code="REFRESH_TOKEN_EXPIRED"
        )
    
    return db_refresh_token

async def set_new_refresh_token_with_rotation(
    session : AsyncSession, 
    user_id : uuid.UUID,
    user_agent : str,
    session_id : str = "",
    db_refresh_token : RefreshToken | None = None,
    rotate : bool = True,
    ):
    """
    params:
        rotate: is it token rotation flow; if yes then old token will be marked as rotated
    """
    # Rotate:
#     - Insert new refresh token row
    new_refresh_token = generate_refresh_token()
    new_refresh_token_hash = hash_refresh_token(new_refresh_token)
    
    if not session_id:
        session_id = str(uuid.uuid4())
#     - set rotated_at = now() in old token
    new_refresh_token_db = await rotate_and_insert_new_refresh_token(
        session=session,
        user_id= user_id,
        session_id=session_id,
        new_refresh_token_hash=new_refresh_token_hash,
        user_agent=user_agent,
        db_refresh_token=db_refresh_token,
        rotate=rotate,
    )
    # 4. issue new_access_token
    new_access_token = generate_access_token(
        user_id=new_refresh_token_db.user_id,
        session_id=new_refresh_token_db.session_id,
    ) if new_refresh_token_db else None
    
    return new_refresh_token, new_access_token

async def signout_user(session : AsyncSession, token : str, all_session : bool = False):
    refresh_token_hash = hash_refresh_token(token)
    # find token in DB
    db_refresh_token = await get_refresh_token_data_by_hashed_token(session, refresh_token_hash)
    
    if db_refresh_token and all_session:
        await revoke_all_auth_session(session, db_refresh_token.user_id)
    elif db_refresh_token and not db_refresh_token.revoked_at:
        # 2. set revoke_at : now() (through token) in database
        await revoke_auth_session_by_token_object(session, db_refresh_token)
    
async def store_data_in_redis_signup(
    redis_client : Redis, 
    email : str, 
    password_hash : str,
    otp : int,
    username : str = "",
    ) -> str:
    """
    stores (verification_id, email, username, password_hash, otp_hash, issued_at ,expired_at, attempts)

    """
    
    now = datetime.datetime.now(datetime.timezone.utc)
    signup_verification_id = "signup:" + generate_refresh_token()
    
    data = RedisSignUpData(
        signup_verification_id=signup_verification_id,
        otp_hash= hash_password(str(otp)),
        username=username,
        email=email,
        password_hash=password_hash,
        issued_at=str(now),
        expired_at=str(now + datetime.timedelta(minutes=15)),
        attempts=0,
    )
    try:
        await redis_client.hset(
            signup_verification_id,
            mapping=data.model_dump(),
        ) # type: ignore
        # auto delete/expire after 15 mins
        await redis_client.expire(
            signup_verification_id,
            datetime.timedelta(minutes=15),
        )
        return signup_verification_id
    except RedisError as e:
        raise ServerError(str(e))

async def store_data_in_redis_signin(
    redis_client : Redis,
    user_id : str,
    otp : int,
) -> str:
    # - (verification_id, user_id, otp_hash, issued_at ,expired_at, attempts)
    now = datetime.datetime.now(datetime.timezone.utc)
    signin_verification_id = "signin:" + generate_refresh_token()
    data = RedisSignInData(
        signin_verification_id = signin_verification_id,
        user_id = user_id,
        otp_hash = hash_password(str(otp)),
        issued_at = str(now),
        expired_at = str(now + datetime.timedelta(minutes=15)),
        attempts = 0,    
    )
    
    try:
        await redis_client.hset(
            signin_verification_id,
            mapping=data.model_dump(),
        ) # type: ignore
        # auto delete/expire after 15 mins
        await redis_client.expire(
            signin_verification_id,
            datetime.timedelta(minutes=15),
        )
        
        return signin_verification_id
        
    except RedisError as e:
        raise ServerError(str(e))

async def fetch_and_verify_pending_user_from_redis(
    redis_client : Redis,
    verification_id : str,
    user_otp : str,
) -> dict:
    """
    fetch and verify pending state of user from redis
    1. If not found → Invalid or expired request.
    2. Check expiration.
    3. Compare hashed OTP.
    4. If mismatch:
        - increment attempts
        - if attempts exceed threshold → delete record
        - return error
    """
    try:
        redis_data = await redis_client.hgetall(verification_id) # type: ignore
        
        # If data does not exists
        if not redis_data:
            raise ClientError(
                "Invalid or expired OTP",
                "INVALID_OR_EXPIRED_OTP",
        )
        now = datetime.datetime.now(datetime.timezone.utc) 
        # increment attempts
        user_attempts = int(redis_data["attempts"]) + 1
        # if attempts exceed threshold → delete record
        if user_attempts > MAX_OTP_ATTEMPTS :
            await redis_client.delete(verification_id)
            raise ClientError(
                "Too many invalid verification attempts. Please restart the signup/signin process.",
                "TOO_MANY_OTP_ATTMPTS",
                400,
            )
        # update attempts
        redis_data["attempts"] = user_attempts
        await redis_client.hset(verification_id, mapping=redis_data) # type: ignore
        # check if otp right or not
        if len(user_otp) != 6:
            raise ClientError(
                "OTP must be of 6 digit",
                "INVALID_OTP",
            )
        valid, new_hash = verify_password(user_otp, redis_data["otp_hash"])
        if not valid or redis_data["expired_at"] <= str(now):
            raise ClientError(
                "Invalid or expired OTP",
                "INVALID_OR_EXPIRED_OTP",
            )
        if new_hash:
            redis_data["otp_hash"] = new_hash
            await redis_client.hset(verification_id, mapping=redis_data) # type: ignore
            
        
        # After successful verification delete the key
        await redis_client.delete(verification_id)
        
        return redis_data
    except RedisError as e:
        raise ServerError(str(e))
    
async def set_access_and_refresh_token_in_cookie(
    response : Response,
    access_token : str,
    refresh_token : str,
) -> None:
    cookie_payload = {
        "httponly": True,
        "samesite": "lax",
        "secure" : settings.app_env == ENV.PRODUCTION,
    }
    response.set_cookie(
            key="access_token", 
            value=access_token,
            max_age=int(settings.access_token_expires_minutes) * 60,
            **cookie_payload,
        )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=int(settings.refresh_token_expires_minutes) * 60,
        **cookie_payload,
    )

