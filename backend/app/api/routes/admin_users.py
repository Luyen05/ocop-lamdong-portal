"""Quản lý tài khoản người dùng cho admin: tìm kiếm, lọc, khóa và mở khóa."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.api.dependencies import CurrentUser
from app.core.database import get_db
from app.core.roles import RoleName
from app.core.search import ilike_contains
from app.models.role import Role
from app.models.user import User
from app.schemas.admin_user import (
    AdminUserListResponse,
    AdminUserRead,
    AdminUserStatusUpdate,
    AdminUserSubjectRead,
)
from app.schemas.error import ErrorResponse


router = APIRouter(prefix="/users")


def user_load_options() -> tuple:
    return (
        joinedload(User.role),
        joinedload(User.subject),
        selectinload(User.social_accounts),
    )


def to_admin_user_read(user: User) -> AdminUserRead:
    subject = user.subject
    return AdminUserRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        role=RoleName(user.role.name),
        is_active=user.is_active,
        created_at=user.created_at,
        has_password=user.hashed_password is not None,
        social_providers=[account.provider for account in user.social_accounts],
        subject=(
            AdminUserSubjectRead(id=subject.id, name=subject.name, status=subject.status)
            if subject is not None
            else None
        ),
    )


def user_error(status_code: int, code: str, message: str, details: dict | None = None) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message, "details": details},
    )


@router.get(
    "",
    response_model=AdminUserListResponse,
    responses={status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorResponse}},
)
def list_users(
    q: str | None = Query(default=None, max_length=150),
    role: RoleName | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> AdminUserListResponse:
    filters = []
    if q and q.strip():
        filters.append(or_(ilike_contains(User.email, q), ilike_contains(User.full_name, q)))
    if role is not None:
        filters.append(Role.name == role.value)
    if is_active is not None:
        filters.append(User.is_active.is_(is_active))

    total = db.scalar(
        select(func.count(User.id)).join(User.role).where(*filters)
    ) or 0
    users = db.scalars(
        select(User)
        .join(User.role)
        .where(*filters)
        .options(*user_load_options())
        .order_by(User.created_at.desc(), User.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).unique().all()
    return AdminUserListResponse(
        items=[to_admin_user_read(user) for user in users],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.patch(
    "/{user_id}/status",
    response_model=AdminUserRead,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_409_CONFLICT: {"model": ErrorResponse},
    },
)
def update_user_status(
    user_id: int,
    payload: AdminUserStatusUpdate,
    current_admin: CurrentUser,
    db: Session = Depends(get_db),
) -> AdminUserRead:
    target = db.scalar(
        select(User)
        .where(User.id == user_id)
        .options(joinedload(User.role))
        .with_for_update(of=User)
    )
    if target is None:
        raise user_error(
            status.HTTP_404_NOT_FOUND,
            "USER_NOT_FOUND",
            "Không tìm thấy tài khoản.",
            {"user_id": user_id},
        )

    if not payload.is_active and target.is_active:
        if target.role.name == RoleName.ADMIN:
            # Khóa các admin còn hoạt động để hai admin không thể khóa lẫn nhau cùng lúc
            # rồi để hệ thống không còn ai quản trị.
            other_active_admins = db.scalars(
                select(User.id)
                .join(User.role)
                .where(
                    Role.name == RoleName.ADMIN.value,
                    User.is_active.is_(True),
                    User.id != target.id,
                )
                .with_for_update(of=User)
            ).all()
            if not other_active_admins:
                raise user_error(
                    status.HTTP_409_CONFLICT,
                    "LAST_ACTIVE_ADMIN",
                    "Không thể khóa quản trị viên cuối cùng còn hoạt động.",
                )
        if target.id == current_admin.id:
            raise user_error(
                status.HTTP_409_CONFLICT,
                "CANNOT_LOCK_SELF",
                "Bạn không thể tự khóa tài khoản của mình.",
            )

    target.is_active = payload.is_active
    db.add(target)
    db.commit()

    user = db.scalar(select(User).where(User.id == user_id).options(*user_load_options()))
    return to_admin_user_read(user or target)
