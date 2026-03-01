from fastapi import (
    APIRouter,
    Request,
    Response, 
    status,
)
from app.auth.schemas import (
    AuthEmailSignUpInitRequest, 
    AuthEmailInitResponse,
    AuthEmailSignInInitRequest,
    RedisSignUpData,
    VerifyOTPRequest,
)
from app.auth.service import (
    create_user_with_email_identity, 
)
from app.auth.utils import (
    extract_refresh_token,
    fetch_and_verify_pending_user_from_redis,
    resend_otp_using_redis,
    send_otp_to_user,
    set_access_and_refresh_token_in_cookie,
    set_new_refresh_token_with_rotation,
    signout_user,
    store_data_in_redis_signin,
    store_data_in_redis_signup,
    verify_credentinal_for_email_signup,
    verify_credentinal_for_email_signin,
    authenticate_refresh_token,
)
from app.auth.security import (
    generate_numeric_otp, 
    hash_password,
)
from app.db.config import DbSession
from app.auth.dependencies import (
    redis_client,
    httpx_client,
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

    
@router.post('/email/signup', response_model=AuthEmailInitResponse)
async def email_signup(
    session : DbSession, 
    user_data : AuthEmailSignUpInitRequest,
    redis_client : redis_client,
    httpx_client : httpx_client,
    ):
    
    # check is email exists or not
    await verify_credentinal_for_email_signup(session,user_data)
    
    # hash the password
    password_hash = hash_password(user_data.password)
    
    # generate otp
    otp = generate_numeric_otp()
    
    # send otp to user's email
    await send_otp_to_user(str(otp), httpx_client, user_data.email)
    
    # Store temporary record in redis to remember state 
    # - (verification_id, email, username, password_hash, otp_hash, issued_at ,expired_at, attempts)
    verification_id = await store_data_in_redis_signup(
        redis_client=redis_client,
        email=user_data.email,
        password_hash=password_hash,
        otp=otp,
        username=user_data.username,
    )
    
    return {
        "message" : "OTP sent successfully! Please check your email",
        "verification_id" : verification_id,
    }

@router.post('/email/signin', response_model=AuthEmailInitResponse)
async def email_signin(
    session : DbSession, 
    user_data : AuthEmailSignInInitRequest,
    redis_client : redis_client,
    httpx_client : httpx_client,
    ):
    
    # Verify credentials
    db_user = await verify_credentinal_for_email_signin(session, user_data)
    
    # generate otp
    otp = generate_numeric_otp()
    
    # Store temporary record in redis to remember state 
    # - (verification_id, user_id, otp_hash, issued_at ,expired_at, attempts)
    verification_id = await store_data_in_redis_signin(
        redis_client=redis_client,
        user_id= str(db_user.user_id), # type: ignore
        # str("user_id123456789"),
        otp=otp,
        email=user_data.email,
    )
    # send email to client
    await send_otp_to_user(str(otp), httpx_client, user_data.email)
    
    return {
        "message" : "OTP sent successfully! Please check your email",
        "verification_id" : verification_id
    }  

@router.post('/email/verify')
async def verify_otp(
    request : Request,
    session : DbSession, 
    redis_client : redis_client,
    payload: VerifyOTPRequest,
    ):
    # 1. Fetch PendingAuthVerification by verification_id.
    # 2. If not found → Invalid or expired request.
    # 3. Check expiration.
    # 4. Compare hashed OTP.
    # 5. If mismatch:
    #     - increment attempts
    #     - if attempts exceed threshold → delete record
    #     - return error
    user_data = await fetch_and_verify_pending_user_from_redis(
        redis_client,
        payload.verification_id,
        str(payload.user_otp),
    )
    new_refresh_token = new_access_token = None
    user_id = None
    # 6. If valid:
    if "signup_verification_id" in user_data: #sigup flow
        # - Create User
        # - Create AuthIdentity (provider=EMAIL, is_verified=True)
        # get user_id
        data = RedisSignUpData(**user_data)
        user, _ = await create_user_with_email_identity(
            session=session,
            username=data.username,
            email=data.email,
            password_hash=data.password_hash
        )
        user_id = user.user_id
        
    else: # signin 
        # just get user_id because we need it in token generation
        user_id = user_data["user_id"]
    # generate access token
    # generate refresh token and insert  and refresh token in db
    user_agent = request.headers.get("User-Agent") or ""
    new_refresh_token, new_access_token = await set_new_refresh_token_with_rotation(
        session=session,
        user_id=user_id, # type: ignore
        user_agent = user_agent,
        rotate=False,
    )
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    # Issue session token (cookie)
    if new_refresh_token and new_access_token:
        await set_access_and_refresh_token_in_cookie(
            response=response,
            access_token=new_access_token,
            refresh_token=new_refresh_token,
        )
    # 7. Return success response with token.
    return response

@router.post('/resend-otp')
async def resend_otp(
    redis_client : redis_client, 
    httpx_client : httpx_client, 
    verification_id : str
    ):
    # set up new otp in redis
    new_otp, user_email = await resend_otp_using_redis(redis_client, verification_id)
    
    # send new otp to the client's email
    await send_otp_to_user(str(new_otp), httpx_client, user_email)
    print(new_otp)
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    return response
     
@router.post('/refresh')
async def rotate_refresh_token(session : DbSession, request : Request):
    # extract refresh token
    refresh_token = await extract_refresh_token(request)
    
    db_refresh_token = await authenticate_refresh_token(session, refresh_token) # type: ignore
    
    new_refresh_token, new_access_token = await set_new_refresh_token_with_rotation(
        session=session,
        user_id=db_refresh_token.user_id, # type: ignore
        session_id=db_refresh_token.session_id, # type: ignore
        user_agent=db_refresh_token.user_agent, # type: ignore
        db_refresh_token=db_refresh_token,
        rotate=True,
    )

    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    # 5. store access_token and new_refresh_token in client's header/cookie and return it.
    if new_refresh_token and new_access_token:
        await set_access_and_refresh_token_in_cookie(
            response=response,
            access_token=new_access_token,
            refresh_token=new_refresh_token,
        )
 
    return response

@router.post('/signout')
async def signout(session : DbSession, request : Request):
    # 1. Extract refresh_token
    refresh_token = await extract_refresh_token(request, not_found_ok=True)
    access_token = request.cookies.get("access_token")
    
    if refresh_token :  
        await signout_user(session, refresh_token)
        
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    cookie_payload = {
            "httponly": True,
            "samesite": "lax",
            "secure" : True,
        }
    response.delete_cookie(
        "access_token", 
        path='/',
        **cookie_payload
        ) if access_token else None
    response.delete_cookie(
        "refresh_token", 
        path='/',
        **cookie_payload,
        ) if refresh_token else None
        
    return response

@router.post('/signout-all')
async def signout_all(session : DbSession, request : Request):
    refresh_token = await extract_refresh_token(request, not_found_ok=True)
    access_token = request.cookies.get("access_token")
    
    if refresh_token:
        await signout_user(session, refresh_token, all_session=True)
    
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    
    cookie_payload = {
            "httponly": True,
            "samesite": "lax",
            "secure" : True,
        }
    response.delete_cookie(
        "access_token", 
        path='/',
        **cookie_payload
        ) if access_token else None
    response.delete_cookie(
        "refresh_token", 
        path='/',
        **cookie_payload,
        ) if refresh_token else None
        
    return response
