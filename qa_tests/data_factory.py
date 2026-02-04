from __future__ import annotations

from typing import Any, Dict, Optional

from faker import Faker

from .models import UserRegistrationRequest


faker = Faker()


def build_user_registration() -> Dict[str, str]:
    """Генерация валидных данных для регистрации (формат User Service: username, email, password, role)."""
    user = UserRegistrationRequest(
        email=faker.unique.email(),
        password=faker.password(length=12),
        full_name=faker.name(),
    )
    return {
        "username": user.full_name,
        "email": user.email,
        "password": user.password,
        "role": "client",
    }


def build_invalid_registration_short_password() -> Dict[str, str]:
    """Неверные данные: слишком короткий пароль (User Service: min 6 символов)."""
    return {
        "username": faker.name(),
        "email": faker.unique.email(),
        "password": "123",
        "role": "client",
    }


def build_invalid_registration_bad_email() -> Dict[str, str]:
    """Неверные данные: некорректный email."""
    return {
        "username": faker.name(),
        "email": "not-an-email",
        "password": faker.password(length=12),
        "role": "client",
    }


def build_invalid_registration_invalid_role() -> Dict[str, str]:
    """Неверные данные: недопустимая роль."""
    return {
        "username": faker.name(),
        "email": faker.unique.email(),
        "password": faker.password(length=12),
        "role": "superadmin",
    }


def build_login_payload(email: str, password: str) -> Dict[str, str]:
    return {"email": email, "password": password}


def build_invalid_login_empty_email() -> Dict[str, str]:
    return {"email": "", "password": faker.password(length=12)}


def build_invalid_login_empty_password() -> Dict[str, str]:
    return {"email": faker.unique.email(), "password": ""}


def build_refresh_payload(refresh_token: str) -> Dict[str, str]:
    return {"refresh_token": refresh_token}


def build_invalid_refresh_empty() -> Dict[str, str]:
    return {"refresh_token": ""}


def build_create_session_payload(
    session_type: str = "consultation",
    session_external_id: Optional[str] = None,
    participant_role: str = "host",
) -> Dict[str, str]:
    return {
        "session_type": session_type,
        "session_external_id": session_external_id or faker.uuid4(),
        "participant_role": participant_role,
    }


def build_validate_session_payload(
    user_id: str,
    session_external_id: Optional[str] = None,
    participant_role: str = "host",
) -> Dict[str, Any]:
    return {
        "user_id": user_id,
        "session_external_id": session_external_id or faker.uuid4(),
        "participant_role": participant_role,
    }

