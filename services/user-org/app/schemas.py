from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

# Auth
class SignUpIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_hours: int

class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    created_at: datetime

# Queries
class QueryCreateIn(BaseModel):
    original_query: str = Field(min_length=1, max_length=1000)
    is_active: bool = True

class QueryOut(BaseModel):
    id: UUID
    original_query: str
    is_active: bool
    created_at: datetime

class QueryListOut(BaseModel):
    items: list[QueryOut]
