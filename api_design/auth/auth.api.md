# signup
## POST /api/v1/auth/signup/init
- Intent: create account via email OTP and authenticate user
- Input: email, username ,provider, password(Optional), device_info(Optional)
- Output: access_token, refresh_token, send OTP message
- Errors: email exists, otp invalid
### Server Logic
1. Verify Credentials
2. Look up for provider
    - if provider is EMAIL -> Send OTP message to client's email -> client verify OTP on /auth/verify route
3. Provider is third party (i.e. Google, Github) -> generate access + refresh tokens
4. Upadate db with email, provider, is_verified:true, hashed_refresh_tokens, etc .
5. Store access + refresh token in headers or cookie.

# signin
## POST /api/v1/auth/signin/init



## POST /api/v1/auth/verify
- Intent: verify the email if provider is EMAIL, create user and issue token
- input: provider, email, OTP
- Output: access_token, refresh_token
- Error: Invalid or Expired OTP
### Server Logic
1. Verify identity (OTP or provider)
2. Look up AuthIdentity
   - if exists → signin path
   - if not exists → signup path (create User + identity)
3. Mark identity as verified
4. Issue access + refresh tokens
5. Store access + refresh token in headers or cookie.

## POST /api/v1/auth/signin/verify

# refresh token
## POST /api/v1/auth/refresh

# signout
## POST /api/v1/auth/signout
## POST /api/v1/auth/signout-all
