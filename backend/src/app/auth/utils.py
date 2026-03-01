from fastapi import Request, Response, status
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
    generate_numeric_otp,
    generate_refresh_token,
    hash_password,
    verify_password,
    hash_refresh_token,
)
from app.core.enums import (
    ENV, 
    MAX_OTP_ATTEMPTS, 
    OTP_COOLDOWN_TIME_SECONDS, 
    OTP_EXPIRE_TIME_REDIS_SECONDS, 
    SENDGRID_URL,
)
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from redis.exceptions import RedisError
from typing import Literal
import httpx
import datetime
import logging
import uuid

# < ----------- Access and Refresh Token Utilities ----------->

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
   
# < -------------Redis Utilities --------------->
async def rate_limit_otp_redis(
    redis_client : Redis,
    email : str,
    flow : Literal["signup", "signin", "resend"],
):
    try:
        cooldown_key = f"auth:{flow}:otp:cooldown:{email}"
        count_key = f"auth:{flow}:otp:attempts:{email}"
        
        # increment count_key by 1
        count = await redis_client.incrby(count_key, 1)
        # if does not exist, create with value 1 and attach expire time 15 minutes
        if count == 1:
            await redis_client.expire(
                count_key,
                time=15 * 60,
            )
        # if count_key > 5 within 15 minutes -> raise error with msg = "To many attempts"
        if count > 5:
            raise ClientError(
                message="Too many attmepts within 15 minutes. Please try again after some time.",
                code="TOO_MANY_ATTEMPTS",
            )
            
        # if cooldown_key exists: -> too many requests within OTP_COOLDOWN_TIME_SECONDS
        cooldown_set = await redis_client.set(
            cooldown_key,
            "1",
            ex=OTP_COOLDOWN_TIME_SECONDS,
            nx=True,
        )
        if not cooldown_set:
            raise ClientError(
                message=f"Too many request! Wait at least {OTP_COOLDOWN_TIME_SECONDS} seconds",
                code = "TOO_MANY_REQUESTS",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            )
    
    except RedisError as e:
        raise ServerError(str(e))
    
    except Exception:
        raise

async def get_redis_hash_data(
    redis_client : Redis,
    verification_id : str
) -> dict:
    try:
        key_type = await redis_client.type(verification_id)
        print(key_type)
        # If data does not exists
        if key_type == "none":
            raise ClientError(
                message="Verification expired! Please signin/signup again.",
                code="VERIFICATION_EXPIRED",
            )
        if key_type != "hash":
            raise ClientError(
                "Invalid verification id",
                "INVALID_VERIFICATION_ID"
            )
        return await redis_client.hgetall(verification_id) # type: ignore
    
    except RedisError as e:
        raise ServerError(str(e))
    
    except Exception:
        raise
 
async def set_hash_with_verification_id_and_set_cooldown_key(
    redis_client : Redis,
    verification_id : str,
    data : dict,
    DATA_EXPIRE_TIME_REDIS_IN_SECOND : int = OTP_EXPIRE_TIME_REDIS_SECONDS
) -> str:
    try:
        async with redis_client.pipeline(transaction=True) as pipe:
            pipe.hset(
                verification_id,
                mapping=data,
            ) # type: ignore
            # auto delete/expire after 15 mins
            pipe.expire(
                verification_id,
                DATA_EXPIRE_TIME_REDIS_IN_SECOND,
            )
            await pipe.execute()
            return verification_id
        
    except RedisError as e:
        raise ServerError(str(e))
    
    except Exception:
        raise
   
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
    
    signup_verification_id = "auth:otp:signup:" + generate_refresh_token()
    
    data = RedisSignUpData(
        signup_verification_id=signup_verification_id,
        otp_hash= hash_password(str(otp)),
        username=username,
        email=email.strip().lower(),
        password_hash=password_hash,
        attempts=0,
    )
    
    await rate_limit_otp_redis(
        redis_client=redis_client,
        email=email,
        flow="signup",
    )
    
    await set_hash_with_verification_id_and_set_cooldown_key(
        redis_client=redis_client,
        verification_id=signup_verification_id,
        data=data.model_dump(),
    )
    return signup_verification_id
    
async def store_data_in_redis_signin(
    redis_client : Redis,
    user_id : str,
    otp : int,
    email : str,
) -> str:
    # - (verification_id, user_id, otp_hash, issued_at ,expired_at, attempts)
    signin_verification_id = "auth:otp:signin:" + generate_refresh_token()
    data = RedisSignInData(
        signin_verification_id = signin_verification_id,
        user_id = user_id,
        email=email.strip().lower(),
        otp_hash = hash_password(str(otp)),
        attempts = 0,    
    )
    
    await rate_limit_otp_redis(
        redis_client=redis_client,
        email=email,
        flow="signin",
    )
    await set_hash_with_verification_id_and_set_cooldown_key(
        redis_client=redis_client,
        verification_id=signin_verification_id,
        data=data.model_dump(),
    )
    return signin_verification_id

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
    redis_data = await get_redis_hash_data(
        redis_client=redis_client,
        verification_id=verification_id,
    )
    try:
        # increment attempts
        user_attempts = await redis_client.hincrby(
            verification_id,
            "attempts",
            1,
        ) # type: ignore
        # if attempts exceed threshold → delete record
        if user_attempts > MAX_OTP_ATTEMPTS :
            await redis_client.delete(verification_id)
            raise ClientError(
                "Too many invalid verification attempts. Please restart the signup/signin process.",
                "TOO_MANY_OTP_ATTMPTS",
                400,
            )
        valid, new_hash = verify_password(user_otp, redis_data["otp_hash"])
        if not valid:
            raise ClientError(
                "Invalid or expired OTP",
                "INVALID_OR_EXPIRED_OTP",
            )
        if new_hash:
            redis_data["otp_hash"] = new_hash
            await redis_client.hset(
                verification_id, 
                mapping={
                    "otp_hash" : new_hash,
                }) # type: ignore
            
        
        # After successful verification delete the key
        await redis_client.delete(verification_id)
        
        return redis_data
    except RedisError as e:
        raise ServerError(str(e))
    
    except Exception:
        raise
    
async def resend_otp_using_redis(
    redis_client : Redis,
    verification_id : str,
) -> tuple[int, str] :
    redis_data = await get_redis_hash_data(
        redis_client=redis_client,
        verification_id=verification_id,
    ) 
    # Rate limit otp and max 3 resends in total
    await rate_limit_otp_redis(
        redis_client=redis_client,
        email=redis_data["email"],
        flow="resend",
    )
    # generate otp
    new_otp = generate_numeric_otp()
    # store it in redis:
    # create otp_hash
    new_otp_hash = hash_password(str(new_otp))
    # change otp_hash, reset attempts to zero and reset expire time
    data = {
        "otp_hash" : new_otp_hash,
        "attempts" : 0,
    }
    await set_hash_with_verification_id_and_set_cooldown_key(
        redis_client=redis_client,
        verification_id=verification_id,
        data=data,
        DATA_EXPIRE_TIME_REDIS_IN_SECOND=15 * 60
    )  
    return new_otp, redis_data["email"]
        
# < -------------SendGrid Utilities --------------->
def create_payload_and_headers_for_sendgrid(
    receiver_email : str, 
    otp : str
) -> tuple[dict, dict]:
    payload = {
        "personalizations" : [
            {
                "to" : [
                    {
                        "email" : receiver_email,
                        "name": "Optional",
                    },
                    
                ],
            },
        ],
        "from" : {"email" : settings.SENDGRID.SENDGRID_SENDER_EMAIL},
        "subject" : "OTP Verification",
        "content" : [
            {
                "type" : "text/plain",
                "value" : f"Your OTP is {otp}",
            },
        ],
    }
    headers = {
        "Authorization" : f"Bearer {settings.SENDGRID.SENDGRID_API_KEY}",
        "Content-Type": "application/json",
    }
    return payload, headers

async def send_otp_to_user(
    otp : str,
    httpx_client : httpx.AsyncClient,
    receiver_email : str,
):
    
    payload, headers = create_payload_and_headers_for_sendgrid(receiver_email, otp)
    try:
        response = await httpx_client.post(
            url = SENDGRID_URL,
            headers=headers,
            json = payload,
        )
        print(response.status_code)
        print(response.text)
        if response.status_code != 202:
            raise ServerError(
                message="OTP email delivery failed",
                code=  "OTP_EMAIL_DELIVERY_FAILED"
            )
        return response
    except Exception:
        raise