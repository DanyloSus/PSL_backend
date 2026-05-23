from __future__ import annotations

import uuid

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserPublic(BaseModel):
    id: uuid.UUID
    email: EmailStr
    username: str
    role: UserRole
    global_xp: int
    global_level: int

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    user: UserPublic
