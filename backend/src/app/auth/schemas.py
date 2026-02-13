from typing import Optional
from pydantic import BaseModel, EmailStr
from app.core.enums import AuthProvider

class DeviceInfo(BaseModel):
    device_id : Optional[str] = None
    device_type : Optional[str] = None # mobile | desktop | tablet | unknown
    os : Optional[str] = None # android | ios | windows | macos | linux
    os_version : Optional[str] = None
    browser: Optional[str] = None
    browser_version: Optional[str] = None
    app_version: Optional[str] = None #  if mobile / desktop app
   
# - Input: email, username ,provider, password(Optional), device_info(Optional)
class AuthSignUpInitRequest(BaseModel):
    email : EmailStr
    username : str
    provider : AuthProvider
    password : str = ""
    device_info : Optional[DeviceInfo] = None

class AuthSignUpInitResponse(BaseModel):
    message : str
    verification_id : Optional[str] = None
    