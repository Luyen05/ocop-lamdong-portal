"""Đăng nhập bằng Google/Facebook: giả lập máy chủ của nhà cung cấp bằng httpx.MockTransport."""

from collections.abc import Generator
import hashlib
import hmac
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.routes.auth_social import get_social_http_client
from app.core.config import get_settings
from app.core.database import Base, get_db
from app.core.security import hash_password
from app.main import app
from app.models.role import Role
from app.models.user import SocialAccount, User

STATE = "s" * 40
VERIFIER = "v" * 64
CHALLENGE = "c" * 43


class FakeProviders:
    """Trả lời như Google/Facebook; ghi lại các request để kiểm tra tham số gửi đi."""

    def __init__(self) -> None:
        self.google_user: dict = {
            "sub": "google-123",
            "email": "Khach@Gmail.com",
            "email_verified": True,
            "name": "Khách Du Lịch",
            "picture": "https://lh3.googleusercontent.com/a/anh-dai-dien",
        }
        self.facebook_user: dict = {"id": "fb-456", "name": "Người Dùng Facebook", "email": "fb@example.com"}
        self.token_status = 200
        self.raise_network_error = False
        self.requests: list[httpx.Request] = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if self.raise_network_error:
            raise httpx.ConnectError("không có mạng", request=request)
        url = str(request.url)
        if url.startswith("https://oauth2.googleapis.com/token"):
            if self.token_status != 200:
                return httpx.Response(self.token_status, json={"error": "invalid_grant"})
            return httpx.Response(200, json={"access_token": "google-access", "id_token": "khong-dung"})
        if url.startswith("https://openidconnect.googleapis.com/v1/userinfo"):
            assert request.headers["Authorization"] == "Bearer google-access"
            return httpx.Response(200, json=self.google_user)
        if "/oauth/access_token" in url:
            if self.token_status != 200:
                return httpx.Response(self.token_status, json={"error": {"message": "Invalid code"}})
            return httpx.Response(200, json={"access_token": "fb-access", "token_type": "bearer"})
        if url.startswith("https://graph.facebook.com/v26.0/me"):
            return httpx.Response(200, json=self.facebook_user)
        return httpx.Response(404, json={"error": "unexpected"})


@pytest.fixture
def social_context(monkeypatch) -> Generator[tuple[TestClient, sessionmaker, FakeProviders], None, None]:
    settings = get_settings()
    monkeypatch.setattr(settings, "frontend_base_url", "http://localhost:5173")
    monkeypatch.setattr(settings, "google_client_id", "google-client-id")
    monkeypatch.setattr(settings, "google_client_secret", SecretStr("google-secret"))
    monkeypatch.setattr(settings, "facebook_app_id", "fb-app-id")
    monkeypatch.setattr(settings, "facebook_app_secret", SecretStr("fb-secret"))
    monkeypatch.setattr(settings, "facebook_graph_version", "v26.0")

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
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

    providers = FakeProviders()

    def override_get_db() -> Generator[Session, None, None]:
        with testing_session() as session:
            yield session

    def override_http_client() -> Generator[httpx.Client, None, None]:
        with httpx.Client(transport=httpx.MockTransport(providers.handler)) as client:
            yield client

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_social_http_client] = override_http_client
    with TestClient(app) as client:
        yield client, testing_session, providers
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


def add_user(testing_session: sessionmaker, email: str, role_id: int = 3, *, active: bool = True) -> int:
    with testing_session() as session:
        user = User(
            role_id=role_id,
            email=email,
            hashed_password=hash_password("MatKhauAnToan123"),
            full_name="Tài khoản có sẵn",
            is_active=active,
        )
        session.add(user)
        session.commit()
        return user.id


def google_callback(client: TestClient):
    return client.post(
        "/api/v1/auth/social/google/callback",
        json={"code": "ma-tu-google", "code_verifier": VERIFIER},
    )


def test_providers_hidden_until_keys_configured(social_context, monkeypatch) -> None:
    client, _, _ = social_context
    assert client.get("/api/v1/auth/social/providers").json() == {"providers": ["google", "facebook"]}

    settings = get_settings()
    monkeypatch.setattr(settings, "facebook_app_secret", SecretStr(""))
    assert client.get("/api/v1/auth/social/providers").json() == {"providers": ["google"]}

    response = client.post("/api/v1/auth/social/facebook/authorize", json={"state": STATE})
    assert response.status_code == 404
    assert response.json()["code"] == "SOCIAL_PROVIDER_DISABLED"
    assert client.post(
        "/api/v1/auth/social/facebook/callback", json={"code": "abc"}
    ).json()["code"] == "SOCIAL_PROVIDER_DISABLED"


def test_unknown_provider_and_bad_state_rejected(social_context) -> None:
    client, _, _ = social_context
    assert client.post("/api/v1/auth/social/github/authorize", json={"state": STATE}).status_code == 422
    assert client.post("/api/v1/auth/social/facebook/authorize", json={"state": "ngan"}).status_code == 422
    assert client.post(
        "/api/v1/auth/social/facebook/authorize", json={"state": "x" * 31 + "<"}
    ).status_code == 422


def test_google_authorize_url_uses_pkce_and_configured_redirect(social_context) -> None:
    client, _, _ = social_context
    missing = client.post("/api/v1/auth/social/google/authorize", json={"state": STATE})
    assert missing.status_code == 422
    assert missing.json()["code"] == "SOCIAL_PKCE_REQUIRED"

    response = client.post(
        "/api/v1/auth/social/google/authorize", json={"state": STATE, "code_challenge": CHALLENGE}
    )
    assert response.status_code == 200
    url = urlparse(response.json()["authorization_url"])
    query = parse_qs(url.query)
    assert f"{url.scheme}://{url.netloc}{url.path}" == "https://accounts.google.com/o/oauth2/v2/auth"
    assert query["client_id"] == ["google-client-id"]
    assert query["redirect_uri"] == ["http://localhost:5173/dang-nhap/mang-xa-hoi/google"]
    assert query["state"] == [STATE]
    assert query["code_challenge"] == [CHALLENGE]
    assert query["code_challenge_method"] == ["S256"]
    assert query["scope"] == ["openid email profile"]
    assert "google-secret" not in response.text


def test_facebook_authorize_url(social_context) -> None:
    client, _, _ = social_context
    response = client.post("/api/v1/auth/social/facebook/authorize", json={"state": STATE})
    url = urlparse(response.json()["authorization_url"])
    query = parse_qs(url.query)
    assert f"{url.scheme}://{url.netloc}{url.path}" == "https://www.facebook.com/v26.0/dialog/oauth"
    assert query["client_id"] == ["fb-app-id"]
    assert query["redirect_uri"] == ["http://localhost:5173/dang-nhap/mang-xa-hoi/facebook"]
    assert query["scope"] == ["email,public_profile"]
    assert "fb-secret" not in response.text


def test_google_creates_user_without_password_then_reuses_link(social_context) -> None:
    client, testing_session, providers = social_context
    response = google_callback(client)
    assert response.status_code == 200
    body = response.json()
    assert body["is_new_user"] is True

    token_request = providers.requests[0]
    form = parse_qs(token_request.content.decode())
    assert form["code"] == ["ma-tu-google"]
    assert form["code_verifier"] == [VERIFIER]
    assert form["client_secret"] == ["google-secret"]
    assert form["redirect_uri"] == ["http://localhost:5173/dang-nhap/mang-xa-hoi/google"]

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"}).json()
    assert me["email"] == "khach@gmail.com"
    assert me["role"] == "user"
    assert me["full_name"] == "Khách Du Lịch"
    assert me["avatar_url"] == "https://lh3.googleusercontent.com/a/anh-dai-dien"
    assert me["has_password"] is False
    assert me["social_providers"] == ["google"]

    # Tài khoản không có mật khẩu: đăng nhập bằng mật khẩu luôn báo sai, cùng thông báo như email không tồn tại.
    password_login = client.post(
        "/api/v1/auth/login", json={"email": "khach@gmail.com", "password": "bat-ky"}
    )
    assert password_login.status_code == 401
    assert password_login.json()["code"] == "INVALID_CREDENTIALS"

    # Đổi email trên Google vẫn vào đúng tài khoản cũ vì nhận diện theo mã người dùng của Google.
    providers.google_user["email"] = "email-moi@gmail.com"
    again = google_callback(client)
    assert again.status_code == 200
    assert again.json()["is_new_user"] is False
    with testing_session() as session:
        assert session.scalar(select(func.count(User.id))) == 1
        account = session.scalar(select(SocialAccount))
        assert account.email == "email-moi@gmail.com"


def auth_header(client: TestClient, email: str) -> dict:
    token = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "MatKhauAnToan123"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize("role_id", [1, 2, 3])
def test_existing_email_is_never_linked_automatically(social_context, role_id: int) -> None:
    """Đăng ký bằng mật khẩu không xác minh email: tự liên kết theo email sẽ cho phép chiếm tài khoản."""

    client, testing_session, _ = social_context
    add_user(testing_session, "khach@gmail.com", role_id=role_id)

    response = google_callback(client)
    assert response.status_code == 409
    assert response.json()["code"] == "SOCIAL_EMAIL_EXISTS"
    assert "liên kết Google trong trang Tài khoản" in response.json()["message"]
    with testing_session() as session:
        assert session.scalar(select(func.count(SocialAccount.id))) == 0


def test_logged_in_user_links_google_then_signs_in_with_it(social_context) -> None:
    client, testing_session, providers = social_context
    user_id = add_user(testing_session, "matkhau@example.com")
    headers = auth_header(client, "matkhau@example.com")
    # Email Google khác email tài khoản vẫn liên kết được: người dùng đã chứng minh sở hữu cả hai.
    response = client.post(
        "/api/v1/auth/social/google/link",
        json={"code": "ma-tu-google", "code_verifier": VERIFIER},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["id"] == user_id
    assert response.json()["social_providers"] == ["google"]
    assert response.json()["has_password"] is True

    # Liên kết lại cùng tài khoản Google: không lỗi.
    again = client.post(
        "/api/v1/auth/social/google/link",
        json={"code": "ma-tu-google", "code_verifier": VERIFIER},
        headers=headers,
    )
    assert again.status_code == 200

    login = google_callback(client)
    assert login.status_code == 200
    assert login.json()["is_new_user"] is False
    me = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {login.json()['access_token']}"}
    ).json()
    assert me["id"] == user_id
    assert client.post(
        "/api/v1/auth/login", json={"email": "matkhau@example.com", "password": "MatKhauAnToan123"}
    ).status_code == 200


def test_link_requires_login(social_context) -> None:
    client, _, providers = social_context
    response = client.post(
        "/api/v1/auth/social/google/link", json={"code": "abc", "code_verifier": VERIFIER}
    )
    assert response.status_code == 401
    assert providers.requests == []


def test_google_account_linked_to_someone_else_cannot_be_linked_again(social_context) -> None:
    client, testing_session, _ = social_context
    assert google_callback(client).status_code == 200  # tạo tài khoản khach@gmail.com
    add_user(testing_session, "nguoi-khac@example.com")
    response = client.post(
        "/api/v1/auth/social/google/link",
        json={"code": "abc", "code_verifier": VERIFIER},
        headers=auth_header(client, "nguoi-khac@example.com"),
    )
    assert response.status_code == 409
    assert response.json()["code"] == "SOCIAL_ACCOUNT_IN_USE"


def test_admin_cannot_link(social_context) -> None:
    client, testing_session, providers = social_context
    add_user(testing_session, "admin.ocop@gmail.com", role_id=1)
    response = client.post(
        "/api/v1/auth/social/facebook/link",
        json={"code": "abc"},
        headers=auth_header(client, "admin.ocop@gmail.com"),
    )
    assert response.status_code == 403
    assert response.json()["code"] == "SOCIAL_LOGIN_NOT_ALLOWED"


def test_subject_can_link_and_unlink(social_context) -> None:
    client, testing_session, _ = social_context
    add_user(testing_session, "namanhfarm.chuthe@gmail.com", role_id=2)
    headers = auth_header(client, "namanhfarm.chuthe@gmail.com")
    linked = client.post("/api/v1/auth/social/facebook/link", json={"code": "abc"}, headers=headers)
    assert linked.status_code == 200
    assert linked.json()["social_providers"] == ["facebook"]

    unlinked = client.delete("/api/v1/auth/social/facebook", headers=headers)
    assert unlinked.status_code == 200
    assert unlinked.json()["social_providers"] == []
    missing = client.delete("/api/v1/auth/social/facebook", headers=headers)
    assert missing.status_code == 404
    assert missing.json()["code"] == "SOCIAL_ACCOUNT_NOT_LINKED"


def test_cannot_unlink_the_only_login_method(social_context) -> None:
    client, _, providers = social_context
    token = google_callback(client).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = client.delete("/api/v1/auth/social/google", headers=headers)
    assert response.status_code == 409
    assert response.json()["code"] == "SOCIAL_UNLINK_LAST_METHOD"

    # Có thêm Facebook thì bỏ được Google.
    providers.facebook_user["email"] = "khac@example.com"
    assert client.post(
        "/api/v1/auth/social/facebook/link", json={"code": "abc"}, headers=headers
    ).status_code == 200
    response = client.delete("/api/v1/auth/social/google", headers=headers)
    assert response.status_code == 200
    assert response.json()["social_providers"] == ["facebook"]


def test_linked_account_promoted_to_admin_cannot_use_social_login(social_context) -> None:
    client, testing_session, _ = social_context
    assert google_callback(client).status_code == 200
    with testing_session() as session:
        user = session.scalar(select(User))
        user.role_id = 1
        session.commit()

    response = google_callback(client)
    assert response.status_code == 403
    assert response.json()["code"] == "SOCIAL_LOGIN_NOT_ALLOWED"


def test_linked_subject_account_can_still_sign_in(social_context) -> None:
    """Người dùng tạo bằng Google rồi được duyệt thành chủ thể vẫn đăng nhập được bằng Google."""

    client, testing_session, _ = social_context
    assert google_callback(client).status_code == 200
    with testing_session() as session:
        session.scalar(select(User)).role_id = 2
        session.commit()
    response = google_callback(client)
    assert response.status_code == 200


def test_inactive_user_is_rejected(social_context) -> None:
    client, testing_session, _ = social_context
    assert google_callback(client).status_code == 200
    with testing_session() as session:
        session.scalar(select(User)).is_active = False
        session.commit()
    response = google_callback(client)
    assert response.status_code == 403
    assert response.json()["code"] == "ACCOUNT_INACTIVE"


def test_unverified_google_email_is_rejected(social_context) -> None:
    client, testing_session, providers = social_context
    providers.google_user["email_verified"] = False
    response = google_callback(client)
    assert response.status_code == 422
    assert response.json()["code"] == "SOCIAL_EMAIL_UNVERIFIED"
    with testing_session() as session:
        assert session.scalar(select(func.count(User.id))) == 0


def test_google_requires_code_verifier(social_context) -> None:
    client, _, providers = social_context
    response = client.post("/api/v1/auth/social/google/callback", json={"code": "abc"})
    assert response.status_code == 422
    assert response.json()["code"] == "SOCIAL_PKCE_REQUIRED"
    assert providers.requests == []


def test_facebook_login_sends_appsecret_proof(social_context) -> None:
    client, _, providers = social_context
    response = client.post("/api/v1/auth/social/facebook/callback", json={"code": "ma-tu-facebook"})
    assert response.status_code == 200
    assert response.json()["is_new_user"] is True

    token_request, me_request = providers.requests
    token_query = parse_qs(token_request.url.query.decode())
    assert token_query["client_secret"] == ["fb-secret"]
    assert token_query["code"] == ["ma-tu-facebook"]
    me_query = parse_qs(me_request.url.query.decode())
    expected_proof = hmac.new(b"fb-secret", b"fb-access", hashlib.sha256).hexdigest()
    assert me_query["appsecret_proof"] == [expected_proof]
    assert me_query["fields"] == ["id,name,email"]

    me = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {response.json()['access_token']}"}
    ).json()
    assert me["email"] == "fb@example.com"
    assert me["avatar_url"] is None
    assert me["social_providers"] == ["facebook"]


def test_facebook_account_without_email_is_rejected(social_context) -> None:
    client, testing_session, providers = social_context
    providers.facebook_user.pop("email")
    response = client.post("/api/v1/auth/social/facebook/callback", json={"code": "abc"})
    assert response.status_code == 422
    assert response.json()["code"] == "SOCIAL_EMAIL_REQUIRED"
    with testing_session() as session:
        assert session.scalar(select(func.count(User.id))) == 0


def test_long_email_is_dropped_not_truncated(social_context) -> None:
    client, _, providers = social_context
    providers.google_user["email"] = "a" * 150 + "@gmail.com"
    response = google_callback(client)
    assert response.status_code == 422
    assert response.json()["code"] == "SOCIAL_EMAIL_REQUIRED"


def test_facebook_email_never_links_existing_account(social_context) -> None:
    client, testing_session, _ = social_context
    add_user(testing_session, "fb@example.com")
    response = client.post("/api/v1/auth/social/facebook/callback", json={"code": "abc"})
    assert response.status_code == 409
    assert response.json()["code"] == "SOCIAL_EMAIL_EXISTS"


@pytest.mark.parametrize(
    ("token_status", "network_error", "expected_status", "expected_code"),
    [
        (400, False, 400, "SOCIAL_AUTH_FAILED"),
        (503, False, 502, "SOCIAL_PROVIDER_UNAVAILABLE"),
        (200, True, 502, "SOCIAL_PROVIDER_UNAVAILABLE"),
    ],
)
def test_provider_errors(social_context, token_status, network_error, expected_status, expected_code) -> None:
    client, _, providers = social_context
    providers.token_status = token_status
    providers.raise_network_error = network_error
    response = google_callback(client)
    assert response.status_code == expected_status
    assert response.json()["code"] == expected_code
    assert "google-secret" not in response.text
