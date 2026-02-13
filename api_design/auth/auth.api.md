# signup
## POST /api/v1/auth/email/signup/init
- Intent: create account via email OTP and authenticate user
- Input: email, username, password, device_info(Optional)
- Output: 
    - Send OTP message(provider:EMAIL)
    - OR access_token + refresh_token(3rd party provider only)
- Errors: email exists, otp invalid
### Server Logic
1. Verify Credentials
2. provider is EMAIL here.
3. It must have password & username. If not -> raise InvalidInputException 
4. check if email already exists or not
    - DB select query with provided email
    - if response is not None -> raise AuthError("Email already exists")
5. Generate OTP
    - Store temporary record in redis to remember state 
        - (verification_id, email, username, password_hash, otp_hash, issued_at ,expired_at, attempts)
    - return response with verification_id and message : "OTP sent successfully"
    - Now, it's frontend responsiblity to redirect client to this route: POST /api/v1/auth/email/verify
    
# signin
## POST /api/v1/auth/email/signin/init
- Intent: authenticate the user through credentials 
- Input: email, password, device_info(Optional)
- Output: 
    - Send OTP message(provider:EMAIL)
    - OR access_token + refresh_token(3rd party provider only)
- Error: email does not exists, otp invalid
### Server Logic
1. Verify credentials
2. Check If email exists
    - it not -> AuthError("Email doesn't exists")
3. Generate OTP
    - Store temporary record in redis to remember state 
        - (verification_id, email, username, password_hash, otp_hash, issued_at ,expired_at, attempts)
    - return response with verification_id and message : "OTP sent successfully"
    - Now, it's frontend responsiblity to redirect client to this route: POST /api/v1/auth/email/verify

## POST /api/v1/auth/oauth/google
1. Provider is 3rd party(i.e. Google, Github) -> authentication succesful
2. generate access + refresh tokens
3. Upadate db with email, provider, is_verified:true, hashed_refresh_tokens, etc .
4. Store access + refresh token in headers or cookie.
## POST /api/v1/auth/oauth/github

# Verify
## POST /api/v1/auth/verify
- Intent: verify the email if provider is EMAIL, create user and issue token
- input: verification_id, OTP(from cookie)
- Output: access_token, refresh_token
- Error: Invalid or Expired OTP
### Server Logic
1. Fetch PendingAuthVerification by verification_id.
2. If not found → Invalid or expired request.
3. Check expiration.
4. Compare hashed OTP.
5. If mismatch:
    - increment attempts
    - if attempts exceed threshold → delete record
    - return error
6. If valid:
    - Create User
    - Create AuthIdentity (provider=EMAIL, is_verified=True)
    - Delete PendingAuthVerification record
    - Issue session token (JWT or session cookie)
7. Return success response with token.


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