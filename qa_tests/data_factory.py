from __future__ import annotations

from typing import Dict

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

