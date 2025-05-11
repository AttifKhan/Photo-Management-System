from pydantic import BaseModel, EmailStr, Field, ConfigDict
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
from .base import BaseModelConfig

class UserCreate(BaseModel):
    model_config: ConfigDict  = BaseModelConfig
    username:   str           = Field(..., min_length=3, max_length=50)
    email:      EmailStr
    password:   str           = Field(..., min_length=6)
    is_photographer: Optional[bool] = False
    is_admin: Optional[bool] = False

class UserOut(BaseModel):
    model_config: ConfigDict = BaseModelConfig
    id:             int
    username:       str
    email:          EmailStr
    is_photographer: bool
    is_admin:       bool
    created_at:     datetime

class Token(BaseModel):
    access_token: str
    token_type: str
