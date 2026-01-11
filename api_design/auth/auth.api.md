# signup
## POST /api/v1/auth/signup/init
- Intent: create account via email OTP and authenticate user
- Input: email, username ,provider, password(Optional), device_info(Optional)
- Output: 
    - Send OTP message(provider:EMAIL)
    - OR access_token + refresh_token(3rd party provider only)
- Errors: email exists, otp invalid
### Server Logic
1. Verify Credentials
2. Look up for provider
    - if provider = EMAIL -> Send OTP message to client's email -> client verify OTP on /auth/verify route
    - Provider is 3rd party(i.e. Google, Github) -> authentication succesful
3. generate access + refresh tokens
4. Upadate db with email, provider, is_verified:true, hashed_refresh_tokens, etc .
5. Store access + refresh token in headers or cookie.

# signin
## POST /api/v1/auth/signin/init
- Intent: authenticate the user through credentials 
- Input: email, provider ,password(Optional)
- Output: 
    - Send OTP message(provider:EMAIL)
    - OR access_token + refresh_token(3rd party provider only)
- Error: email does not exists, otp invalid
### Server Logic
1. Verify credentials
2. Look up for provider
    - If provider = Email -> send OTP to client't email -> client verify OTP on /auth/verify route
    - Provider is 3rd party -> authentication succesfull
4. Generate access token and refresh token 
5. Store it in users header or cookie


# Verify
## POST /api/v1/auth/verify
- Intent: verify the email if provider is EMAIL, create user and issue token
- input: provider, email, OTP
- Output: access_token, refresh_token
- Error: Invalid or Expired OTP
### Server Logic
1. If provider != EMAIl -> reject
2. If OTP Invalid or expired -> reject
2. Look up for email in db
   - if exists → signin path
   - if not exists → signup path (create User + identity)
3. Mark identity as verified(is_verified: true)
4. Issue access + refresh tokens
5. Store access + refresh token in headers or cookie.


# refresh token
## POST /api/v1/auth/refresh
- Intent: Generate the access token and rotate the refresh token
- Input: refresh_token(Through headers or cookie)
- Output: access_token, new_refresh_token
- Error: token not found, token is expired, token is revoked
### Server Logic
1. Extract refresh token and hash it
2. find token in DB
    - if not found -> reject
    - if revoked_at != NULL -> reject
    - if rotated_at != NULL -> SECURITY ALERT(resue detected)
    - if expired_at < now> -> reject
3. Rotate:
    - set rotated_at = now() in old token
    - Insert new refresh token row
4. issue new_access_token
5. store access_token and new_refresh_token in client's header/cookie and return it.

# signout
## POST /api/v1/auth/signout
- Intent: signout current session of the user
- Input: refresh_token (from cookie/header)
- Output: success message
- Error: token does not exists
### Server Logic
1. Extract refresh_token
2. If refresh_token is not available -> send error message
3. set revoke_at : now() (through token) in database
4. return success message
## POST /api/v1/auth/signout-all
- Intent: signout all session of the user
- Input:  refresh_token (from cookie/header)
- Output: success message
- Error: token does not exists
### Server Logic
1. Extract refresh_token
2. If refresh_token is not available -> send error message
3. set revoke_at : now() (through token) for all the token in database
4. return success message