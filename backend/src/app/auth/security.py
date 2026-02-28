import hashlib
import secrets
from datetime import datetime, timedelta, timezone
import uuid

import jwt
from passlib.context import LazyCryptContext
from passlib.exc import UnknownHashError, InvalidHashError

from app.core.exceptions import AuthError, ServerError
from app.main import settings

_pwd_ctx = LazyCryptContext(
    schemes=["argon2"],
    deprecated="auto",
)
#  <---------- Password hashing(Argon2) ---------->
def hash_password(password : str) -> str:
    """
    hash plain password with argon2 hashing alogorthm
    """
    return _pwd_ctx.hash(password)

def verify_password(password : str, password_hash : str) -> tuple[bool, str | None]:
    """
    Verify a password against argon2 hash
    """
    try:
        valid =  _pwd_ctx.verify(password, password_hash)
        
        if valid and _pwd_ctx.needs_update(password_hash):
            new_hash = _pwd_ctx.hash(password)
            return True, new_hash
        
        return valid, None
    
    except InvalidHashError:
        return False, None
    
    except UnknownHashError:
        raise ServerError(
            message="Convert password_hash with argon2 properly",
            code="UNKNOWN_HASH_ERROR",
        )
    except Exception as e:
        raise Exception(str(e))

#  <---------- Refresh token ---------->
def generate_refresh_token() -> str:
    # 265 bits entropy
    return secrets.token_urlsafe(32)

def hash_refresh_token(token : str) -> str:
    """
    Hash a refresh token using SHA256.
    Returns hex digest.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

#  <---------- Access token(JWT)(HMAC) ---------->
def generate_access_token(
    user_id : str | uuid.UUID,
    session_id : str,
    role : str = "USER",
    expire_delta : timedelta | None = None
) -> str:
    
    now = datetime.now(timezone.utc)
    if not expire_delta:
        expire_delta = timedelta(minutes=settings.access_token_expires_minutes)
    
    payload = {
        "sub" : str(user_id),
        "session_id" : session_id,
        "role" : role,
        "iat" : now,
        "exp" : now + expire_delta,
        "type" : "access",
    }
    
    return jwt.encode(
        payload=payload,
        key=settings.jwt_secret_key,
        algorithm="HS256",
    )
    
def decode_access_token(token : str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
        
        if payload["type"] != "access":
            raise AuthError(f"Invalid token type : {payload["type"]}")
        
        return payload
    except jwt.InvalidSignatureError:
        raise AuthError("Invalid signature", code="INVALID_SIGNATURE")
    except jwt.ExpiredSignatureError:
        raise AuthError("Token expired", code="ACCESS_TOKEN_EXPIRED")
    except jwt.InvalidTokenError:
        raise AuthError("Invalid token", code="INVALID_ACCESS_TOKEN")
    
#  <---------- OTP Generation ---------->
def generate_numeric_otp(length = 6) -> int:
    """
    returns 6 digit number
    """
    otp_range_start = 10**(length-1)
    otp_range_end = 10**length - 1
    
    return secrets.randbelow(otp_range_end - otp_range_start + 1) + otp_range_start