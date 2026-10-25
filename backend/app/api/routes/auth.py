from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.api.dependencies import CurrentUser
from app.core.config import get_settings
from app.core.database import get_db
from app.core.rate_limit import password_attempts
from app.core.roles import RoleName
from app.core.security import (
    DUMMY_PASSWORD_HASH,
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.role import Role
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UpdateMeRequest,
    UserRead,
)
from app.schemas.error import ErrorResponse


router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def ensure_password_attempts_allowed(*, email: str, ip: str) -> None:
    """429 khi email hoặc địa chỉ IP đã nhập sai mật khẩu quá nhiều lần gần đây."""

    retry_after = password_attempts.retry_after(email=email, ip=ip)
    if retry_after > 0:
        minutes = max(1, -(-retry_after // 60))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "TOO_MANY_LOGIN_ATTEMPTS",
                "message": f"Bạn đã nhập sai mật khẩu quá nhiều lần. Vui lòng thử lại sau khoảng {minutes} phút.",
                "details": {"retry_after_seconds": retry_after},
            },
            headers={"Retry-After": str(retry_after)},
        )


def to_user_read(user: User) -> UserRead:
    return UserRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        avatar_url=user.avatar_url,
        is_active=user.is_active,
        role=user.role.name,
        has_password=user.hashed_password is not None,
        social_providers=[account.provider for account in user.social_accounts],
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {"model": ErrorResponse},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponse},
    },
)
def register(
    payload: RegisterRequest,
    db: Annotated[Session, Depends(get_db)],
) -> UserRead:
    existing_user = db.scalar(
        select(User.id).where(func.lower(User.email) == payload.email)
    )
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "EMAIL_ALREADY_EXISTS",
                "message": "Email đã được sử dụng.",
                "details": {"field": "email"},
            },
        )

    user_role = db.scalar(select(Role).where(Role.name == RoleName.USER))
    if user_role is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "ROLE_CONFIGURATION_ERROR",
                "message": "Hệ thống chưa cấu hình vai trò người dùng.",
                "details": None,
            },
        )

    user = User(
        role=user_role,
        email=payload.email,
        hashed_password=hash_password(payload.password.get_secret_value()),
        full_name=payload.full_name,
        phone=payload.phone,
        is_active=True,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "EMAIL_ALREADY_EXISTS",
                "message": "Email đã được sử dụng.",
                "details": {"field": "email"},
            },
        ) from exc
    db.refresh(user)
    return to_user_read(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
        status.HTTP_403_FORBIDDEN: {"model": ErrorResponse},
        status.HTTP_429_TOO_MANY_REQUESTS: {"model": ErrorResponse},
    },
)
def login(
    payload: LoginRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    ip = client_ip(request)
    ensure_password_attempts_allowed(email=payload.email, ip=ip)
    user = db.scalar(
        select(User)
        .options(joinedload(User.role))
        .where(func.lower(User.email) == payload.email)
    )
    # Vẫn băm với tài khoản không tồn tại hoặc chưa có mật khẩu (tạo bằng Google/Facebook)
    # để thời gian phản hồi như nhau, không lộ email nào đã đăng ký.
    stored_hash = user.hashed_password if user is not None else None
    password_matches = verify_password(
        payload.password.get_secret_value(),
        stored_hash or DUMMY_PASSWORD_HASH,
    ) and stored_hash is not None
    if user is None or not password_matches:
        password_attempts.record_failure(email=payload.email, ip=ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_CREDENTIALS",
                "message": "Email hoặc mật khẩu không chính xác.",
                "details": None,
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    password_attempts.record_success(email=payload.email)
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "ACCOUNT_INACTIVE",
                "message": "Tài khoản đã bị khóa hoặc ngừng hoạt động.",
                "details": None,
            },
        )

    access_token = create_access_token(user_id=user.id, role=user.role.name)
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


@router.get(
    "/me",
    response_model=UserRead,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
        status.HTTP_403_FORBIDDEN: {"model": ErrorResponse},
    },
)
def get_me(current_user: CurrentUser) -> UserRead:
    return to_user_read(current_user)


@router.patch(
    "/me",
    response_model=UserRead,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
        status.HTTP_403_FORBIDDEN: {"model": ErrorResponse},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorResponse},
    },
)
def update_me(
    payload: UpdateMeRequest,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> UserRead:
    fields = payload.model_fields_set
    if "full_name" in fields:
        current_user.full_name = payload.full_name
    if "phone" in fields:
        current_user.phone = payload.phone
    if "avatar_url" in fields:
        current_user.avatar_url = (
            str(payload.avatar_url) if payload.avatar_url is not None else None
        )

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return to_user_read(current_user)


def password_error(status_code: int, code: str, message: str, field: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message, "details": {"field": field}},
    )


@router.post(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorResponse},
        status.HTTP_429_TOO_MANY_REQUESTS: {"model": ErrorResponse},
    },
)
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    """Đổi mật khẩu; tài khoản tạo bằng Google/Facebook (chưa có mật khẩu) thì đặt mật khẩu lần đầu."""

    new_password = payload.new_password.get_secret_value()
    if current_user.hashed_password is not None:
        if payload.current_password is None:
            raise password_error(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "CURRENT_PASSWORD_REQUIRED",
                "Vui lòng nhập mật khẩu hiện tại.",
                "current_password",
            )
        ip = client_ip(request)
        ensure_password_attempts_allowed(email=current_user.email, ip=ip)
        if not verify_password(payload.current_password.get_secret_value(), current_user.hashed_password):
            password_attempts.record_failure(email=current_user.email, ip=ip)
            raise password_error(
                status.HTTP_400_BAD_REQUEST,
                "INVALID_CURRENT_PASSWORD",
                "Mật khẩu hiện tại không đúng.",
                "current_password",
            )
        password_attempts.record_success(email=current_user.email)
        if verify_password(new_password, current_user.hashed_password):
            raise password_error(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "PASSWORD_UNCHANGED",
                "Mật khẩu mới phải khác mật khẩu hiện tại.",
                "new_password",
            )

    current_user.hashed_password = hash_password(new_password)
    db.add(current_user)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
