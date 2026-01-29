
class AuthError(Exception):
    message : str
    code : str
    status_code : int
    def __init__(self, message : str = "") -> None:
        self.message = message or self.message
    
    def __repr__(self) -> str:
        return f"<AuthError(message={self.message}, code={self.code}, status_code={self.status_code})>"
    
class InvalidAuthRequest(AuthError):
    message = "Invalid authentication request"
    code = "INVALID_AUTH_REQUEST"
    status_code = 400