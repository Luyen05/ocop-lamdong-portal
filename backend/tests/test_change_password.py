"""POST /auth/change-password: đổi mật khẩu, đặt mật khẩu cho tài khoản Google/Facebook."""

from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.models.user import SocialAccount, User
from test_auth import auth_context, login_user, register_user  # noqa: F401


URL = "/api/v1/auth/change-password"
OLD = "MatKhauAnToan123"
NEW = "MatKhauMoi456789"


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def login(client: TestClient, password: str, email: str = "user@example.com"):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def test_change_password_requires_correct_current_password(auth_context) -> None:
    client, _ = auth_context
    register_user(client)
    headers = bearer(login_user(client))

    changed = client.post(URL, headers=headers, json={"current_password": OLD, "new_password": NEW})

    assert changed.status_code == 204
    assert changed.content == b""
    assert login(client, OLD).status_code == 401
    assert login(client, NEW).status_code == 200


def test_change_password_rejects_wrong_or_missing_current_password(auth_context) -> None:
    client, _ = auth_context
    register_user(client)
    headers = bearer(login_user(client))

    wrong = client.post(URL, headers=headers, json={"current_password": "SaiMatKhau1", "new_password": NEW})
    missing = client.post(URL, headers=headers, json={"new_password": NEW})

    assert wrong.status_code == 400
    assert wrong.json()["code"] == "INVALID_CURRENT_PASSWORD"
    assert missing.status_code == 422
    assert missing.json()["code"] == "CURRENT_PASSWORD_REQUIRED"
    assert login(client, OLD).status_code == 200


def test_change_password_rejects_same_password_and_invalid_length(auth_context) -> None:
    client, _ = auth_context
    register_user(client)
    headers = bearer(login_user(client))

    same = client.post(URL, headers=headers, json={"current_password": OLD, "new_password": OLD})
    short = client.post(URL, headers=headers, json={"current_password": OLD, "new_password": "ngan"})
    long = client.post(URL, headers=headers, json={"current_password": OLD, "new_password": "a" * 129})
    extra = client.post(URL, headers=headers, json={"current_password": OLD, "new_password": NEW, "email": "x@y.vn"})

    assert same.status_code == 422
    assert same.json()["code"] == "PASSWORD_UNCHANGED"
    assert short.status_code == 422
    assert long.status_code == 422
    assert extra.status_code == 422


def test_change_password_requires_authentication(auth_context) -> None:
    client, _ = auth_context

    response = client.post(URL, json={"current_password": OLD, "new_password": NEW})

    assert response.status_code == 401


def test_wrong_current_password_is_rate_limited(auth_context) -> None:
    client, _ = auth_context
    register_user(client)
    headers = bearer(login_user(client))

    for _ in range(5):
        response = client.post(URL, headers=headers, json={"current_password": "SaiMatKhau1", "new_password": NEW})
        assert response.status_code == 400
    blocked = client.post(URL, headers=headers, json={"current_password": OLD, "new_password": NEW})

    assert blocked.status_code == 429
    assert blocked.json()["code"] == "TOO_MANY_LOGIN_ATTEMPTS"
    assert int(blocked.headers["retry-after"]) > 0
    # Bộ đếm theo email dùng chung với đăng nhập.
    assert login(client, OLD).status_code == 429


def create_social_user(testing_session) -> int:
    with testing_session() as session:
        user = User(
            role_id=3,
            email="google@example.com",
            hashed_password=None,
            full_name="Người dùng Google",
            is_active=True,
        )
        session.add(user)
        session.flush()
        session.add(SocialAccount(user_id=user.id, provider="google", provider_user_id="g-123", email=user.email))
        session.commit()
        return user.id


def test_social_account_sets_first_password_without_current(auth_context) -> None:
    client, testing_session = auth_context
    user_id = create_social_user(testing_session)
    headers = bearer(create_access_token(user_id=user_id, role="user"))
    assert client.get("/api/v1/auth/me", headers=headers).json()["has_password"] is False

    response = client.post(URL, headers=headers, json={"new_password": NEW})

    assert response.status_code == 204
    me = client.get("/api/v1/auth/me", headers=headers).json()
    assert me["has_password"] is True
    assert me["social_providers"] == ["google"]
    assert login(client, NEW, "google@example.com").status_code == 200
    # Đã có mật khẩu thì lần sau phải nhập mật khẩu hiện tại.
    again = client.post(URL, headers=headers, json={"new_password": "MatKhauKhac999"})
    assert again.status_code == 422
    assert again.json()["code"] == "CURRENT_PASSWORD_REQUIRED"


def test_social_account_ignores_current_password_field(auth_context) -> None:
    client, testing_session = auth_context
    user_id = create_social_user(testing_session)
    headers = bearer(create_access_token(user_id=user_id, role="user"))

    response = client.post(URL, headers=headers, json={"current_password": "bat-ky", "new_password": NEW})

    assert response.status_code == 204
