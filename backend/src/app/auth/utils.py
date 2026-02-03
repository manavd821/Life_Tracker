from app.auth.schemas import AuthSignUpInitRequest
from app.core.enums import AuthProvider

async def verify_credentinal(data : AuthSignUpInitRequest) -> None:
    # if provide is email and password is not there
    if data.provider == AuthProvider.EMAIL:
        if not data.password:
            raise Exception("Password required for EMAIL signup")
        
    # if provide is other than email and password is present
    if data.provider != AuthProvider.EMAIL:
        if data.password:
            raise Exception("Password is not required for 3rd party Provider")
    
    