"""Lỗi 500 trả JSON kèm CORS, chặn JWT secret mẫu, giới hạn số lần đăng nhập sai."""

import logging

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import DEV_JWT_SECRET, JWT_SECRET_PLACEHOLDER, Settings
from app.core.rate_limit import PasswordAttemptLimiter, SlidingWindowCounter, password_attempts
from app.main import app
from test_auth import auth_context, register_user  # noqa: F401


ORIGIN = "http://localhost:5173"


# ---------------------------------------------------------------------------
# Lỗi chưa xử lý
# ---------------------------------------------------------------------------


def test_unhandled_error_returns_json_with_cors_headers(monkeypatch, caplog) -> None:
    def broken() -> list:
        raise RuntimeError("lỗi giả lập")

    monkeypatch.setattr("app.api.routes.news.get_news_items", broken)
    client = TestClient(app, raise_server_exceptions=True)

    with caplog.at_level(logging.ERROR, logger="app.errors"):
        response = client.get("/api/v1/news", headers={"Origin": ORIGIN})

    assert response.status_code == 500
    assert response.json() == {
        "code": "INTERNAL_ERROR",
        "message": "Đã có lỗi xảy ra. Vui lòng thử lại sau.",
        "details": None,
    }
    assert response.headers["access-control-allow-origin"] == ORIGIN
    assert "lỗi giả lập" not in response.text
    assert any("GET /api/v1/news" in record.getMessage() for record in caplog.records)


def test_handled_errors_still_use_their_own_handlers() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/auth/me", headers={"Origin": ORIGIN})

    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_TOKEN"
    assert response.headers["access-control-allow-origin"] == ORIGIN


# ---------------------------------------------------------------------------
# JWT secret
# ---------------------------------------------------------------------------


def test_settings_reject_example_jwt_secret() -> None:
    with pytest.raises(ValidationError, match="JWT_SECRET_KEY"):
        Settings(_env_file=None, jwt_secret_key=JWT_SECRET_PLACEHOLDER)
    with pytest.raises(ValidationError, match="JWT_SECRET_KEY"):
        Settings(_env_file=None, jwt_secret_key=f"  {JWT_SECRET_PLACEHOLDER} ")


def test_settings_warn_when_using_development_jwt_secret(caplog) -> None:
    with caplog.at_level(logging.WARNING, logger="app.core.config"):
        settings = Settings(_env_file=None)
    assert settings.jwt_secret_key.get_secret_value() == DEV_JWT_SECRET
    assert any("JWT_SECRET_KEY" in record.getMessage() for record in caplog.records)

    caplog.clear()
    with caplog.at_level(logging.WARNING, logger="app.core.config"):
        Settings(_env_file=None, jwt_secret_key="k" * 48)
    assert not any("JWT_SECRET_KEY" in record.getMessage() for record in caplog.records)


# ---------------------------------------------------------------------------
# Bộ đếm
# ---------------------------------------------------------------------------


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def test_sliding_window_counter_blocks_and_expires() -> None:
    clock = FakeClock()
    counter = SlidingWindowCounter(limit=3, window_seconds=60, clock=clock)

    for _ in range(2):
        counter.record("a")
        clock.now += 10
    assert counter.retry_after("a") == 0
    counter.record("a")  # t=1020, lần thứ 3
    assert counter.retry_after("a") == 40  # lần đầu (t=1000) hết hạn ở t=1060
    assert counter.retry_after("b") == 0

    clock.now = 1061
    assert counter.retry_after("a") == 0
    counter.record("a")
    assert counter.retry_after("a") > 0

    counter.reset("a")
    assert counter.retry_after("a") == 0


def test_sliding_window_counter_caps_tracked_keys() -> None:
    clock = FakeClock()
    counter = SlidingWindowCounter(limit=1, window_seconds=60, clock=clock, max_keys=3)
    for key in "abcd":
        counter.record(key)
        clock.now += 1

    assert len(counter._events) == 3
    assert counter.retry_after("a") == 0  # khóa cũ nhất bị bỏ
    assert counter.retry_after("d") > 0


def test_password_attempt_limiter_checks_email_and_ip() -> None:
    limiter = PasswordAttemptLimiter(email_limit=2, ip_limit=3, window_seconds=60, clock=FakeClock())

    limiter.record_failure(email="A@example.com", ip="1.1.1.1")
    limiter.record_failure(email="a@example.com", ip="1.1.1.1")
    assert limiter.retry_after(email="a@example.com", ip="2.2.2.2") > 0
    limiter.record_success(email="a@example.com")
    assert limiter.retry_after(email="a@example.com", ip="2.2.2.2") == 0

    limiter.record_failure(email="b@example.com", ip="1.1.1.1")
    assert limiter.retry_after(email="c@example.com", ip="1.1.1.1") > 0
    assert limiter.retry_after(email="c@example.com", ip="2.2.2.2") == 0


# ---------------------------------------------------------------------------
# Đăng nhập
# ---------------------------------------------------------------------------


def login(client: TestClient, email: str, password: str):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def test_login_is_blocked_after_five_failures_for_same_email(auth_context) -> None:
    client, _ = auth_context
    register_user(client)

    for _ in range(5):
        assert login(client, "user@example.com", "SaiMatKhau1").status_code == 401
    blocked = login(client, "USER@example.com", "MatKhauAnToan123")

    assert blocked.status_code == 429
    assert blocked.json()["code"] == "TOO_MANY_LOGIN_ATTEMPTS"
    assert 0 < int(blocked.headers["retry-after"]) <= 15 * 60
    assert blocked.json()["details"]["retry_after_seconds"] == int(blocked.headers["retry-after"])
    # Email khác từ cùng IP vẫn đăng nhập được (chưa tới giới hạn theo IP).
    register_user(client, "other@example.com")
    assert login(client, "other@example.com", "MatKhauAnToan123").status_code == 200


def test_successful_login_clears_email_counter(auth_context) -> None:
    client, _ = auth_context
    register_user(client)

    for _ in range(4):
        assert login(client, "user@example.com", "SaiMatKhau1").status_code == 401
    assert login(client, "user@example.com", "MatKhauAnToan123").status_code == 200
    for _ in range(4):
        assert login(client, "user@example.com", "SaiMatKhau1").status_code == 401
    assert login(client, "user@example.com", "MatKhauAnToan123").status_code == 200


def test_login_is_blocked_after_twenty_failures_from_same_ip(auth_context) -> None:
    client, _ = auth_context
    register_user(client)

    for index in range(20):
        assert login(client, f"khong-co-{index}@example.com", "SaiMatKhau1").status_code == 401
    blocked = login(client, "user@example.com", "MatKhauAnToan123")

    assert blocked.status_code == 429
    assert "retry-after" in blocked.headers


def test_rate_limit_state_is_reset_between_tests() -> None:
    assert password_attempts.retry_after(email="user@example.com", ip="testclient") == 0
