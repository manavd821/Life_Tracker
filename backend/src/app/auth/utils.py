from app.auth.schemas import AuthSignUpInitRequest
from app.core.enums import AuthProvider
from app.core.exceptions import ClientError

async def verify_credentinal(data : AuthSignUpInitRequest) -> None:
    # if provide is email and password is not there
    if data.provider == AuthProvider.EMAIL:
        if not data.password:
            raise ClientError("Password required for EMAIL signup")
        
        if len(data.password) < 5 :
            raise ClientError("Password must be at least 5 character")
    # if provide is other than email and password is present
    if data.provider != AuthProvider.EMAIL:
        if data.password:
            raise ClientError("Password is not required for 3rd party Provider")
    
    
    