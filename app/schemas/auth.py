from pydantic import BaseModel, EmailStr, Field

class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User's email address")
    password: str    = Field(..., min_length=6, description="User's password")

class Token(BaseModel):
    access_token: str
    token_type: str
