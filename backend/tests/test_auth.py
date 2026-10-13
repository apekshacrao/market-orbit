from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.schemas.auth import Token
from app.services.auth_service import AuthService


def fake_db(user):
    return SimpleNamespace(query=lambda model: SimpleNamespace(
        filter=lambda condition: SimpleNamespace(first=lambda: user)
    ))


def test_login_returns_token_and_only_public_user_fields():
    user = SimpleNamespace(
        id="user-1", email="asha@example.com", full_name="Asha Rao",
        hashed_password="hash", is_active=True,
    )
    with patch("app.services.auth_service.verify_password", return_value=True), \
         patch("app.services.auth_service.create_access_token", return_value="jwt"):
        result = AuthService.authenticate(
            SimpleNamespace(email=user.email, password="secret"), fake_db(user)
        )

    response = Token(**result).model_dump()
    assert response == {
        "access_token": "jwt",
        "token_type": "bearer",
        "user": {"id": "user-1", "name": "Asha Rao", "email": "asha@example.com"},
    }


@pytest.mark.parametrize("user", [None, SimpleNamespace(hashed_password="hash")])
def test_login_rejects_unknown_user_or_invalid_password(user):
    with patch("app.services.auth_service.verify_password", return_value=False):
        with pytest.raises(HTTPException) as error:
            AuthService.authenticate(
                SimpleNamespace(email="asha@example.com", password="wrong"),
                fake_db(user),
            )
    assert error.value.status_code == 401
