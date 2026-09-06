from collections.abc import Generator
from datetime import timedelta

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.dependencies import require_roles
from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.role import Role
from app.models.user import User


@pytest.fixture
def auth_context() -> Generator[tuple[TestClient, sessionmaker], None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(engine)

    with testing_session() as session:
        session.add_all(
            [
                Role(id=1, name="admin", description="Quản trị"),
                Role(id=2, name="subject", description="Chủ thể"),
                Role(id=3, name="user", description="Người dùng"),
            ]
        )
        session.commit()

    def override_get_db() -> Generator[Session, None, None]:
        with testing_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client, testing_session
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


def register_user(client: TestClient, email: str = "user@example.com") -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "MatKhauAnToan123",
            "full_name": "Nguyễn Văn A",
            "phone": "0912345678",
        },
    )
    assert response.status_code == 201
    return response.json()


def login_user(client: TestClient, email: str = "user@example.com") -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "MatKhauAnToan123"},
    )
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["expires_in"] == 3600
    return response.json()["access_token"]


def test_register_login_and_get_me(auth_context) -> None:
    client, testing_session = auth_context
    registered = register_user(client, "USER@EXAMPLE.COM")

    assert registered["email"] == "user@example.com"
    assert registered["role"] == "user"
    assert "hashed_password" not in registered

    with testing_session() as session:
        user = session.get(User, registered["id"])
        assert user is not None
        assert user.hashed_password != "MatKhauAnToan123"

    token = login_user(client)
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == registered["id"]
    assert response.json()["role"] == "user"


def test_register_rejects_duplicate_email(auth_context) -> None:
    client, _ = auth_context
    register_user(client)

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "USER@example.com",
            "password": "MatKhauKhac123",
            "full_name": "Nguyễn Văn B",
        },
    )

    assert response.status_code == 409
    assert response.json()["code"] == "EMAIL_ALREADY_EXISTS"


def test_register_rejects_client_supplied_role(auth_context) -> None:
    client, _ = auth_context

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "admin-attempt@example.com",
            "password": "MatKhauAnToan123",
            "full_name": "Admin giả mạo",
            "role_id": 1,
        },
    )

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_login_rejects_invalid_credentials(auth_context) -> None:
    client, _ = auth_context
    register_user(client)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "sai-mat-khau"},
    )

    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_CREDENTIALS"


def test_me_requires_valid_token(auth_context) -> None:
    client, _ = auth_context

    missing = client.get("/api/v1/auth/me")
    invalid = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer token-khong-hop-le"},
    )

    assert missing.status_code == 401
    assert invalid.status_code == 401
    assert missing.json()["code"] == "INVALID_TOKEN"
    assert invalid.json()["code"] == "INVALID_TOKEN"


def test_me_rejects_expired_token(auth_context) -> None:
    client, _ = auth_context
    user = register_user(client)
    token = create_access_token(
        user_id=user["id"],
        role="user",
        expires_delta=timedelta(seconds=-1),
    )

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_TOKEN"


def test_update_me_changes_only_profile_fields(auth_context) -> None:
    client, testing_session = auth_context
    registered = register_user(client)
    token = login_user(client)

    response = client.patch(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "full_name": "Nguyễn Văn B",
            "phone": None,
            "avatar_url": "https://example.com/avatar.webp",
        },
    )

    assert response.status_code == 200
    assert response.json()["full_name"] == "Nguyễn Văn B"
    assert response.json()["phone"] is None
    assert response.json()["avatar_url"] == "https://example.com/avatar.webp"
    assert response.json()["role"] == "user"

    with testing_session() as session:
        stored_user = session.get(User, registered["id"])
        assert stored_user is not None
        assert stored_user.full_name == "Nguyễn Văn B"
        assert stored_user.phone is None


def test_update_me_rejects_protected_fields(auth_context) -> None:
    client, _ = auth_context
    register_user(client)
    token = login_user(client)

    response = client.patch(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"role_id": 1, "is_active": False},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_update_me_requires_authentication(auth_context) -> None:
    client, _ = auth_context

    response = client.patch(
        "/api/v1/auth/me",
        json={"full_name": "Nguyễn Văn B"},
    )

    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_TOKEN"


def test_inactive_account_is_rejected(auth_context) -> None:
    client, testing_session = auth_context
    user = register_user(client)

    with testing_session() as session:
        stored_user = session.get(User, user["id"])
        assert stored_user is not None
        stored_user.is_active = False
        session.commit()

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "MatKhauAnToan123"},
    )

    assert login_response.status_code == 403
    assert login_response.json()["code"] == "ACCOUNT_INACTIVE"


def test_role_guard_allows_admin_and_denies_user() -> None:
    admin_role = Role(id=1, name="admin")
    user_role = Role(id=3, name="user")
    admin = User(
        id=1,
        role_id=1,
        role=admin_role,
        email="admin@example.com",
        hashed_password=hash_password("admin-password"),
        full_name="Admin",
        is_active=True,
    )
    user = User(
        id=2,
        role_id=3,
        role=user_role,
        email="user@example.com",
        hashed_password=hash_password("user-password"),
        full_name="User",
        is_active=True,
    )
    admin_only = require_roles("admin")

    assert admin_only(current_user=admin) is admin
    with pytest.raises(HTTPException) as exc_info:
        admin_only(current_user=user)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail["code"] == "INSUFFICIENT_PERMISSIONS"
