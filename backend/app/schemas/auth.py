from typing import Optional
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class LoginUserResponse(BaseModel):
    id: str
    name: Optional[str] = None
    email: EmailStr

class Token(BaseModel):
    access_token: str
    token_type: str
    user: LoginUserResponse

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    name: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True
