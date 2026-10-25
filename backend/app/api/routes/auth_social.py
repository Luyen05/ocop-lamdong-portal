from collections.abc import Generator
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.api.routes.auth import to_user_read
from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import create_access_token
from app.schemas.auth import (
    SocialAuthorizeRequest,
    SocialAuthorizeResponse,
    SocialCallbackRequest,
    SocialLoginResponse,
    SocialProvidersResponse,
    UserRead,
)
from app.schemas.error import ErrorResponse
from app.services.social_login import (
    SocialProvider,
    authorization_url,
    ensure_provider_enabled,
    fetch_profile,
    link_profile,
    sign_in_with_profile,
    unlink_provider,
)


router = APIRouter(prefix="/auth/social", tags=["Authentication"])


def get_social_http_client() -> Generator[httpx.Client, None, None]:
    """Client gọi Google/Facebook; test thay bằng httpx.MockTransport."""

    with httpx.Client(timeout=get_settings().social_login_timeout_seconds) as client:
        yield client


@router.get("/providers", response_model=SocialProvidersResponse)
def list_social_providers() -> SocialProvidersResponse:
    """Nhà cung cấp đã khai báo khóa; frontend chỉ hiện nút của các nhà cung cấp này."""

    return SocialProvidersResponse(providers=get_settings().social_providers)


@router.post(
    "/{provider}/authorize",
    response_model=SocialAuthorizeResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorResponse},
    },
)
def start_social_login(provider: SocialProvider, payload: SocialAuthorizeRequest) -> SocialAuthorizeResponse:
    settings = get_settings()
    ensure_provider_enabled(settings, provider)
    return SocialAuthorizeResponse(
        authorization_url=authorization_url(settings, provider, payload.state, payload.code_challenge)
    )


@router.post(
    "/{provider}/callback",
    response_model=SocialLoginResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
        status.HTTP_403_FORBIDDEN: {"model": ErrorResponse},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_409_CONFLICT: {"model": ErrorResponse},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorResponse},
        status.HTTP_502_BAD_GATEWAY: {"model": ErrorResponse},
    },
)
def finish_social_login(
    provider: SocialProvider,
    payload: SocialCallbackRequest,
    db: Annotated[Session, Depends(get_db)],
    client: Annotated[httpx.Client, Depends(get_social_http_client)],
) -> SocialLoginResponse:
    settings = get_settings()
    ensure_provider_enabled(settings, provider)
    profile = fetch_profile(client, settings, provider, payload.code, payload.code_verifier)
    result = sign_in_with_profile(db, profile)
    return SocialLoginResponse(
        access_token=create_access_token(user_id=result.user.id, role=result.user.role.name),
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        is_new_user=result.created,
    )


@router.post(
    "/{provider}/link",
    response_model=UserRead,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
        status.HTTP_403_FORBIDDEN: {"model": ErrorResponse},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_409_CONFLICT: {"model": ErrorResponse},
        status.HTTP_502_BAD_GATEWAY: {"model": ErrorResponse},
    },
)
def link_social_account(
    provider: SocialProvider,
    payload: SocialCallbackRequest,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    client: Annotated[httpx.Client, Depends(get_social_http_client)],
) -> UserRead:
    """Người dùng đang đăng nhập liên kết thêm Google/Facebook (bước cuối của luồng như /callback)."""

    settings = get_settings()
    ensure_provider_enabled(settings, provider)
    profile = fetch_profile(client, settings, provider, payload.code, payload.code_verifier)
    link_profile(db, current_user, profile)
    return to_user_read(current_user)


@router.delete(
    "/{provider}",
    response_model=UserRead,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_409_CONFLICT: {"model": ErrorResponse},
    },
)
def unlink_social_account(
    provider: SocialProvider,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> UserRead:
    """Bỏ liên kết; không cho bỏ nếu đó là cách đăng nhập duy nhất (tài khoản chưa có mật khẩu)."""

    unlink_provider(db, current_user, provider)
    return to_user_read(current_user)
