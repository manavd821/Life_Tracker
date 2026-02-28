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
    
class AuthEmailSignUpInitRequest(BaseModel):
    email : EmailStr
    username : str
    password : str
    device_info : Optional[DeviceInfo] = None

class AuthEmailInitResponse(BaseModel):
    message : str
    verification_id : str
    
class AuthEmailSignInInitRequest(BaseModel):
    email : EmailStr
    password : str

class RedisSignInData(BaseModel):
    signin_verification_id : str
    user_id : str
    otp_hash : str
    attempts : int

class RedisSignUpData(BaseModel):
    signup_verification_id : str
    otp_hash : str
    username : str
    email : str
    password_hash : str
    attempts : int
