# Authentication middleware
- Applied on protected route
## Server logic
- extracts access_token(from Authoriation: Bearer)
    - if missing -> 401 Unauthorized
- verify JWT signature
    - if invalid -> 401 Unauthorized
- check exp claim
    - if expired -> 401 Unauthorized
- extract user_id(sub)
- attach user_id to request context
- proceed to next handler