from fastapi import APIRouter
from app.auth.schemas import AuthSignUpInitRequest, AuthSignUpInitResponse
from app.auth.utils import verify_credentinal

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

@router.post('/signup', response_model=AuthSignUpInitResponse)
async def signup(data : AuthSignUpInitRequest):
    await verify_credentinal(data)
    
    # check if user already exists
    
    return {
        "message" : "all iz well",
        # "data" : data 
        }