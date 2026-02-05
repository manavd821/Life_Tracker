import logging

class AppError(Exception):
    """
    Base class for all intentional application-level errors.
    """
    status_code: int
    code: str
    log_level: int
    expose: bool

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)

    
class ClientError(AppError):
    status_code = 400
    log_level = logging.INFO
    expose = True
   
class DomainError(AppError):
    """
    Business rule violation.
    Example : task already completed, invalid state transition
    """
    status_code = 400
    log_level = logging.INFO
    expose = True
     
class ServerError(AppError):
    status_code = 500
    log_level = logging.ERROR
    expose = False