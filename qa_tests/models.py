from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegistrationRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)


class UserRegistrationResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str


class AuthRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    """Ответ с токенами (поддержка snake_case и camelCase от User Service)."""
    model_config = ConfigDict(populate_by_name=True)

    access_token: str = Field(alias="accessToken")
    refresh_token: Optional[str] = Field(default=None, alias="refreshToken")
    token_type: str = Field(default="Bearer", alias="tokenType")


class CreateSessionRequest(BaseModel):
    user_id: str
    reason: str


class CreateSessionResponse(BaseModel):
    session_id: str
    ws_url: str


class JoinSessionRequest(BaseModel):
    operator_id: str
    session_id: str


class ChatMessage(BaseModel):
    sender_id: str
    content: str
    timestamp: float


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: Optional[dict]

