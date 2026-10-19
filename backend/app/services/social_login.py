"""Đăng nhập bằng Google, Facebook theo luồng OAuth 2.0 "authorization code".

Luồng:
1. Frontend tạo `state` ngẫu nhiên (và `code_verifier` cho Google), gọi
   POST /auth/social/{provider}/authorize để lấy địa chỉ trang đăng nhập rồi chuyển người dùng sang đó.
2. Google/Facebook trả người dùng về {FRONTEND_BASE_URL}/dang-nhap/mang-xa-hoi/{provider}?code=…&state=….
   Frontend so `state` với giá trị đã lưu (chống giả mạo yêu cầu), rồi gửi `code` cho
   POST /auth/social/{provider}/callback.
3. Backend đổi `code` lấy access token (kèm client secret, chỉ backend biết), đọc thông tin người dùng
   và cấp JWT của hệ thống như đăng nhập bằng mật khẩu.
   Người dùng đang đăng nhập muốn liên kết thêm Google/Facebook thì bước 3 gọi
   POST /auth/social/{provider}/link (kèm JWT) thay cho /callback.

Gọi Google/Facebook bằng httpx có sẵn, không thêm thư viện. Thông tin người dùng lấy trực tiếp từ máy chủ
của nhà cung cấp qua HTTPS bằng access token vừa đổi được, nên không cần tự kiểm chữ ký ID token.
"""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.config import Settings
from app.core.roles import RoleName
from app.models.role import Role
from app.models.user import SocialAccount, User

SocialProvider = Literal["google", "facebook"]

PROVIDER_LABELS: dict[str, str] = {"google": "Google", "facebook": "Facebook"}

GOOGLE_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
FACEBOOK_GRAPH_URL = "https://graph.facebook.com"
FACEBOOK_DIALOG_URL = "https://www.facebook.com"


@dataclass(frozen=True)
class SocialProfile:
    provider: str
    provider_user_id: str
    email: str | None
    email_verified: bool
    full_name: str | None
    avatar_url: str | None


def social_error(status_code: int, code: str, message: str, details: dict | None = None) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message, "details": details},
    )


def ensure_provider_enabled(settings: Settings, provider: str) -> None:
    if provider not in settings.social_providers:
        raise social_error(
            status.HTTP_404_NOT_FOUND,
            "SOCIAL_PROVIDER_DISABLED",
            f"Chưa bật đăng nhập bằng {PROVIDER_LABELS.get(provider, provider)}.",
            {"provider": provider},
        )


def redirect_uri(settings: Settings, provider: str) -> str:
    return f"{settings.frontend_base_url}/dang-nhap/mang-xa-hoi/{provider}"


def authorization_url(settings: Settings, provider: str, state: str, code_challenge: str | None) -> str:
    if provider == "google":
        if not code_challenge:
            raise social_error(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "SOCIAL_PKCE_REQUIRED",
                "Thiếu mã kiểm tra PKCE cho đăng nhập Google.",
            )
        params = {
            "client_id": settings.google_client_id,
            "redirect_uri": redirect_uri(settings, provider),
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "prompt": "select_account",
        }
        return f"{GOOGLE_AUTHORIZE_URL}?{urlencode(params)}"

    params = {
        "client_id": settings.facebook_app_id,
        "redirect_uri": redirect_uri(settings, provider),
        "response_type": "code",
        "scope": "email,public_profile",
        "state": state,
    }
    return f"{FACEBOOK_DIALOG_URL}/{settings.facebook_graph_version}/dialog/oauth?{urlencode(params)}"


def _provider_unavailable(provider: str) -> HTTPException:
    return social_error(
        status.HTTP_502_BAD_GATEWAY,
        "SOCIAL_PROVIDER_UNAVAILABLE",
        f"Không kết nối được với {PROVIDER_LABELS[provider]}. Vui lòng thử lại sau.",
        {"provider": provider},
    )


def _auth_failed(provider: str) -> HTTPException:
    return social_error(
        status.HTTP_400_BAD_REQUEST,
        "SOCIAL_AUTH_FAILED",
        f"Đăng nhập bằng {PROVIDER_LABELS[provider]} không thành công hoặc đã hết hạn. Vui lòng thử lại.",
        {"provider": provider},
    )


def _json_or_fail(response: httpx.Response, provider: str) -> dict:
    if response.status_code >= 500:
        raise _provider_unavailable(provider)
    if response.status_code != 200:
        raise _auth_failed(provider)
    try:
        body = response.json()
    except ValueError as exc:
        raise _provider_unavailable(provider) from exc
    if not isinstance(body, dict):
        raise _provider_unavailable(provider)
    return body


def _clean_text(value: object, max_length: int) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = " ".join(value.split())
    return cleaned[:max_length] or None


def _clean_email(value: object) -> str | None:
    """Email quá dài thì bỏ hẳn (không cắt bớt, tránh trùng với email khác)."""

    if not isinstance(value, str):
        return None
    email = value.strip().lower()
    if not email or len(email) > 150 or "@" not in email:
        return None
    return email


def _fetch_google_profile(client: httpx.Client, settings: Settings, code: str, code_verifier: str | None) -> SocialProfile:
    if not code_verifier:
        raise social_error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "SOCIAL_PKCE_REQUIRED",
            "Thiếu mã kiểm tra PKCE cho đăng nhập Google.",
        )
    token = _json_or_fail(
        client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret.get_secret_value(),
                "redirect_uri": redirect_uri(settings, "google"),
                "grant_type": "authorization_code",
                "code_verifier": code_verifier,
            },
        ),
        "google",
    )
    access_token = token.get("access_token")
    if not isinstance(access_token, str) or not access_token:
        raise _auth_failed("google")

    info = _json_or_fail(
        client.get(GOOGLE_USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"}),
        "google",
    )
    subject = info.get("sub")
    if not isinstance(subject, str) or not subject:
        raise _auth_failed("google")
    picture = info.get("picture")
    return SocialProfile(
        provider="google",
        provider_user_id=subject,
        email=_clean_email(info.get("email")),
        email_verified=info.get("email_verified") is True,
        full_name=_clean_text(info.get("name"), 150),
        avatar_url=picture if isinstance(picture, str) and picture.startswith("https://") and len(picture) <= 500 else None,
    )


def _fetch_facebook_profile(client: httpx.Client, settings: Settings, code: str) -> SocialProfile:
    graph = f"{FACEBOOK_GRAPH_URL}/{settings.facebook_graph_version}"
    app_secret = settings.facebook_app_secret.get_secret_value()
    token = _json_or_fail(
        client.get(
            f"{graph}/oauth/access_token",
            params={
                "client_id": settings.facebook_app_id,
                "client_secret": app_secret,
                "redirect_uri": redirect_uri(settings, "facebook"),
                "code": code,
            },
        ),
        "facebook",
    )
    access_token = token.get("access_token")
    if not isinstance(access_token, str) or not access_token:
        raise _auth_failed("facebook")

    # appsecret_proof chứng minh lệnh gọi đến từ máy chủ có khóa bí mật của ứng dụng.
    proof = hmac.new(app_secret.encode(), access_token.encode(), hashlib.sha256).hexdigest()
    info = _json_or_fail(
        client.get(
            f"{graph}/me",
            params={"fields": "id,name,email", "access_token": access_token, "appsecret_proof": proof},
        ),
        "facebook",
    )
    subject = info.get("id")
    if not isinstance(subject, str) or not subject:
        raise _auth_failed("facebook")
    # Facebook không cam kết email đã được xác nhận, nên email chỉ dùng làm email của tài khoản mới,
    # không bao giờ dùng để liên kết với tài khoản có sẵn. Ảnh đại diện Facebook có hạn dùng nên không lưu.
    return SocialProfile(
        provider="facebook",
        provider_user_id=subject,
        email=_clean_email(info.get("email")),
        email_verified=False,
        full_name=_clean_text(info.get("name"), 150),
        avatar_url=None,
    )


def fetch_profile(
    client: httpx.Client,
    settings: Settings,
    provider: str,
    code: str,
    code_verifier: str | None,
) -> SocialProfile:
    try:
        if provider == "google":
            return _fetch_google_profile(client, settings, code, code_verifier)
        return _fetch_facebook_profile(client, settings, code)
    except httpx.HTTPError as exc:
        raise _provider_unavailable(provider) from exc


def _display_name(profile: SocialProfile) -> str:
    if profile.full_name and len(profile.full_name) >= 2:
        return profile.full_name
    if profile.email:
        local_part = profile.email.split("@", 1)[0]
        if len(local_part) >= 2:
            return local_part[:150]
    return "Người dùng"


def _ensure_can_sign_in(user: User) -> None:
    if user.role.name == RoleName.ADMIN:
        raise social_error(
            status.HTTP_403_FORBIDDEN,
            "SOCIAL_LOGIN_NOT_ALLOWED",
            "Tài khoản quản trị chỉ đăng nhập bằng email và mật khẩu.",
        )
    if not user.is_active:
        raise social_error(
            status.HTTP_403_FORBIDDEN,
            "ACCOUNT_INACTIVE",
            "Tài khoản đã bị khóa hoặc ngừng hoạt động.",
        )


@dataclass(frozen=True)
class SocialLoginResult:
    user: User
    created: bool


def _find_link(db: Session, profile: SocialProfile) -> SocialAccount | None:
    return db.scalar(
        select(SocialAccount)
        .options(joinedload(SocialAccount.user).joinedload(User.role))
        .where(
            SocialAccount.provider == profile.provider,
            SocialAccount.provider_user_id == profile.provider_user_id,
        )
    )


def _commit_or_conflict(db: Session, label: str) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        # Hai yêu cầu cùng lúc cho cùng một tài khoản: yêu cầu sau gặp ràng buộc unique.
        db.rollback()
        raise social_error(
            status.HTTP_409_CONFLICT,
            "SOCIAL_ACCOUNT_CONFLICT",
            f"Tài khoản {label} đang được xử lý ở một phiên khác. Vui lòng thử lại.",
        ) from exc


def sign_in_with_profile(db: Session, profile: SocialProfile) -> SocialLoginResult:
    """Đăng nhập hoặc tạo người dùng bằng tài khoản Google/Facebook.

    - Đã liên kết: đăng nhập vào người dùng đã liên kết (trừ tài khoản quản trị).
    - Chưa liên kết, email đã có tài khoản: từ chối. Không tự liên kết theo email vì đăng ký bằng mật khẩu
      không xác minh email (ai cũng có thể đăng ký trước bằng email của người khác) và Facebook không cam kết
      email đã xác nhận. Người dùng đăng nhập bằng mật khẩu rồi liên kết trong trang Tài khoản.
    - Email chưa có: tạo tài khoản vai trò người dùng, không có mật khẩu.
    """

    now = datetime.now(timezone.utc)
    label = PROVIDER_LABELS[profile.provider]
    account = _find_link(db, profile)
    if account is not None:
        _ensure_can_sign_in(account.user)
        account.last_login_at = now
        if profile.email:
            account.email = profile.email
        db.commit()
        return SocialLoginResult(user=account.user, created=False)

    if not profile.email:
        raise social_error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "SOCIAL_EMAIL_REQUIRED",
            f"Tài khoản {label} không cung cấp email. Hãy cho phép chia sẻ email hoặc đăng ký bằng email.",
        )
    if profile.provider == "google" and not profile.email_verified:
        raise social_error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "SOCIAL_EMAIL_UNVERIFIED",
            f"Email của tài khoản {label} chưa được xác minh.",
        )

    existing = db.scalar(select(User.id).where(func.lower(User.email) == profile.email))
    if existing is not None:
        raise social_error(
            status.HTTP_409_CONFLICT,
            "SOCIAL_EMAIL_EXISTS",
            f"Email {profile.email} đã có tài khoản. Hãy đăng nhập bằng email và mật khẩu, "
            f"rồi liên kết {label} trong trang Tài khoản.",
            {"email": profile.email},
        )

    user_role = db.scalar(select(Role).where(Role.name == RoleName.USER))
    if user_role is None:
        raise social_error(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "ROLE_CONFIGURATION_ERROR",
            "Hệ thống chưa cấu hình vai trò người dùng.",
        )
    user = User(
        role=user_role,
        email=profile.email,
        hashed_password=None,
        full_name=_display_name(profile),
        avatar_url=profile.avatar_url,
        is_active=True,
    )
    user.social_accounts.append(
        SocialAccount(
            provider=profile.provider,
            provider_user_id=profile.provider_user_id,
            email=profile.email,
            last_login_at=now,
        )
    )
    db.add(user)
    _commit_or_conflict(db, label)
    db.refresh(user)
    return SocialLoginResult(user=user, created=True)


def link_profile(db: Session, user: User, profile: SocialProfile) -> None:
    """Người dùng đang đăng nhập liên kết thêm tài khoản Google/Facebook (đã chứng minh sở hữu cả hai)."""

    label = PROVIDER_LABELS[profile.provider]
    if user.role.name == RoleName.ADMIN:
        raise social_error(
            status.HTTP_403_FORBIDDEN,
            "SOCIAL_LOGIN_NOT_ALLOWED",
            "Tài khoản quản trị chỉ đăng nhập bằng email và mật khẩu.",
        )
    account = _find_link(db, profile)
    if account is not None:
        if account.user_id == user.id:
            return
        raise social_error(
            status.HTTP_409_CONFLICT,
            "SOCIAL_ACCOUNT_IN_USE",
            f"Tài khoản {label} này đã liên kết với một tài khoản khác trên cổng.",
        )
    if any(item.provider == profile.provider for item in user.social_accounts):
        raise social_error(
            status.HTTP_409_CONFLICT,
            "SOCIAL_ACCOUNT_CONFLICT",
            f"Tài khoản của bạn đã liên kết với một tài khoản {label} khác. Bỏ liên kết cũ trước.",
        )
    user.social_accounts.append(
        SocialAccount(
            provider=profile.provider,
            provider_user_id=profile.provider_user_id,
            email=profile.email,
        )
    )
    _commit_or_conflict(db, label)
    db.refresh(user)


def unlink_provider(db: Session, user: User, provider: str) -> None:
    label = PROVIDER_LABELS[provider]
    account = next((item for item in user.social_accounts if item.provider == provider), None)
    if account is None:
        raise social_error(
            status.HTTP_404_NOT_FOUND,
            "SOCIAL_ACCOUNT_NOT_LINKED",
            f"Tài khoản chưa liên kết {label}.",
        )
    if user.hashed_password is None and len(user.social_accounts) == 1:
        raise social_error(
            status.HTTP_409_CONFLICT,
            "SOCIAL_UNLINK_LAST_METHOD",
            f"Không thể bỏ liên kết {label} vì đây là cách đăng nhập duy nhất của tài khoản.",
        )
    user.social_accounts.remove(account)
    db.commit()
    db.refresh(user)
