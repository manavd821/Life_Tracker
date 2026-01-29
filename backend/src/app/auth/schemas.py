from typing import Optional
from pydantic import BaseModel, EmailStr
from app.core.enums import AuthProvider

class DeviceInfo(BaseModel):
    device_id : Optional[str]
    device_type : Optional[str] # mobile | desktop | tablet | unknown
    os : Optional[str] # android | ios | windows | macos | linux
    os_version : Optional[str]
    browser: Optional[str]
    browser_version: Optional[str]
    app_version: Optional[str] #  if mobile / desktop app
   
# - Input: email, username ,provider, password(Optional), device_info(Optional)
class AuthSignUpInitRequest(BaseModel):
    email : EmailStr
    username : str
    provider : AuthProvider
    password : Optional[str]
    device_info : Optional[DeviceInfo]

class AuthSignUpInitResponse(BaseModel):
    message : str
    