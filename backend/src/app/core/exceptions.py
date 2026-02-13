import logging

class AppError(Exception):
    """
    Base class for all intentional application-level errors.
    """
    status_code: int
    code: str
    log_level: int
    expose: bool

    def __init__(self, message: str = "", code: str = "", status_code : int | None = None):
        self.message = message
        self.code = code or self.code
        self.status_code = status_code or self.status_code
        super().__init__(message)

    
class ClientError(AppError):
    status_code = 400
    log_level = logging.INFO
    expose = True
    code = "CLIENT_ERROR"
   
class DomainError(AppError):
    """
    Business rule violation.
    Example : task already completed, invalid state transition
    """
    status_code = 400
    log_level = logging.INFO
    expose = True
    code="DOMAIN_ERROR"
     
class ServerError(AppError):
    status_code = 500
    log_level = logging.ERROR
    expose = False
    code = "SERVER_ERROR"
    
class AuthError(AppError):
    status_code = 401
    log_level = logging.INFO
    expose = True
    code = "AUTH_ERROR"