from collections.abc import Callable
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.roles import RoleName
from app.core.security import decode_access_token
from app.models.user import User


bearer_scheme = HTTPBearer(auto_error=False)


def _credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "code": "INVALID_TOKEN",
            "message": "Token không hợp lệ hoặc đã hết hạn.",
            "details": None,
        },
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _credentials_exception()

    try:
        payload = decode_access_token(credentials.credentials)
        if payload.get("type") != "access":
            raise _credentials_exception()
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError) as exc:
        raise _credentials_exception() from exc

    user = db.scalar(
        select(User)
        .options(joinedload(User.role))
        .where(User.id == user_id)
    )
    if user is None:
        raise _credentials_exception()
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "ACCOUNT_INACTIVE",
                "message": "Tài khoản đã bị khóa hoặc ngừng hoạt động.",
                "details": None,
            },
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*allowed_roles: RoleName | str) -> Callable:
    allowed = {str(role) for role in allowed_roles}

    def role_checker(current_user: CurrentUser) -> User:
        if current_user.role.name not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "INSUFFICIENT_PERMISSIONS",
                    "message": "Bạn không có quyền thực hiện thao tác này.",
                    "details": {"required_roles": sorted(allowed)},
                },
            )
        return current_user

    return role_checker


AdminUser = Annotated[User, Depends(require_roles(RoleName.ADMIN))]
SubjectUser = Annotated[User, Depends(require_roles(RoleName.SUBJECT))]
AdminOrSubjectUser = Annotated[
    User,
    Depends(require_roles(RoleName.ADMIN, RoleName.SUBJECT)),
]
