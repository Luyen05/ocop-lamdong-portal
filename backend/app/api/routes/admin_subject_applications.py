from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.api.dependencies import CurrentUser
from app.core.database import get_db
from app.core.roles import RoleName
from app.models.role import Role
from app.models.subject import Subject
from app.models.user import User
from app.schemas.error import ErrorResponse
from app.schemas.subject import (
    AdminSubjectApplicationRead,
    ApplicantRead,
    SubjectApplicationListResponse,
    SubjectModerationRequest,
)


router = APIRouter()
ApplicationStatus = Literal["pending", "approved", "rejected"]


def to_admin_subject_application_read(subject: Subject) -> AdminSubjectApplicationRead:
    return AdminSubjectApplicationRead(
        id=subject.id,
        user_id=subject.user_id,
        name=subject.name,
        type=subject.type,
        tax_code=subject.tax_code,
        representative=subject.representative,
        phone=subject.phone,
        email=subject.email,
        address=subject.address,
        district=subject.district,
        status=subject.status,
        moderation_note=subject.rejection_reason,
        created_at=subject.created_at,
        updated_at=subject.updated_at,
        applicant=ApplicantRead(
            id=subject.user.id,
            email=subject.user.email,
            full_name=subject.user.full_name,
            role=RoleName(subject.user.role.name),
            is_active=subject.user.is_active,
        ),
    )


@router.get(
    "",
    response_model=SubjectApplicationListResponse,
    responses={status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorResponse}},
)
def list_subject_applications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    application_status: ApplicationStatus | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None, min_length=1, max_length=150),
    db: Session = Depends(get_db),
) -> SubjectApplicationListResponse:
    filters = []
    if application_status:
        filters.append(Subject.status == application_status)
    if search:
        keyword = f"%{search.strip()}%"
        filters.append(
            or_(
                Subject.name.ilike(keyword),
                Subject.tax_code.ilike(keyword),
                User.email.ilike(keyword),
                User.full_name.ilike(keyword),
            )
        )

    total = db.scalar(
        select(func.count(Subject.id)).join(Subject.user).where(*filters)
    ) or 0
    status_order = case(
        (Subject.status == "pending", 0),
        (Subject.status == "rejected", 1),
        else_=2,
    )
    subjects = list(
        db.scalars(
            select(Subject)
            .join(Subject.user)
            .where(*filters)
            .options(joinedload(Subject.user).joinedload(User.role))
            .order_by(status_order, Subject.updated_at.desc(), Subject.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return SubjectApplicationListResponse(
        items=[to_admin_subject_application_read(subject) for subject in subjects],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.patch(
    "/{application_id}/moderation",
    response_model=AdminSubjectApplicationRead,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_409_CONFLICT: {"model": ErrorResponse},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorResponse},
    },
)
def moderate_subject_application(
    application_id: int,
    payload: SubjectModerationRequest,
    current_admin: CurrentUser,
    db: Session = Depends(get_db),
) -> AdminSubjectApplicationRead:
    subject = db.scalar(
        select(Subject)
        .where(Subject.id == application_id)
        .with_for_update()
    )
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "SUBJECT_APPLICATION_NOT_FOUND",
                "message": "Không tìm thấy hồ sơ chủ thể.",
                "details": {"application_id": application_id},
            },
        )
    applicant = db.scalar(
        select(User)
        .where(User.id == subject.user_id)
        .options(selectinload(User.role))
        .with_for_update()
    )
    if applicant is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "SUBJECT_APPLICANT_NOT_FOUND",
                "message": "Tài khoản gửi hồ sơ không còn tồn tại.",
                "details": None,
            },
        )
    subject.user = applicant
    if subject.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "SUBJECT_APPLICATION_ALREADY_REVIEWED",
                "message": "Hồ sơ này đã được xử lý.",
                "details": {"current_status": subject.status},
            },
        )
    if payload.status == "approved" and not subject.user.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "INACTIVE_APPLICANT",
                "message": "Không thể duyệt hồ sơ của tài khoản đã bị khóa.",
                "details": None,
            },
        )

    target_role = db.scalar(
        select(Role).where(
            Role.name == (
                RoleName.SUBJECT if payload.status == "approved" else RoleName.USER
            )
        )
    )
    if target_role is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "ROLE_CONFIGURATION_ERROR",
                "message": "Hệ thống chưa cấu hình đầy đủ vai trò.",
                "details": None,
            },
        )

    subject.status = payload.status
    subject.reviewed_by = current_admin.id
    subject.reviewed_at = datetime.now(timezone.utc)
    subject.rejection_reason = payload.note if payload.status == "rejected" else None
    subject.user.role = target_role
    db.add_all([subject, subject.user])
    db.commit()
    return to_admin_subject_application_read(subject)
