from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.core.database import get_db
from app.core.roles import RoleName
from app.models.subject import Subject
from app.schemas.error import ErrorResponse
from app.schemas.subject import SubjectApplicationPayload, SubjectApplicationRead


router = APIRouter(prefix="/subject-applications", tags=["Subject applications"])


def to_subject_application_read(subject: Subject) -> SubjectApplicationRead:
    return SubjectApplicationRead(
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
    )


def get_own_application(db: Session, user_id: int) -> Subject:
    subject = db.scalar(select(Subject).where(Subject.user_id == user_id))
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "SUBJECT_APPLICATION_NOT_FOUND",
                "message": "Bạn chưa có hồ sơ đăng ký chủ thể.",
                "details": None,
            },
        )
    return subject


def save_application(db: Session, subject: Subject) -> None:
    db.add(subject)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "SUBJECT_APPLICATION_CONFLICT",
                "message": "Mã số thuế hoặc thông tin hồ sơ đã được sử dụng.",
                "details": None,
            },
        ) from exc
    db.refresh(subject)


@router.post(
    "",
    response_model=SubjectApplicationRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
        status.HTTP_403_FORBIDDEN: {"model": ErrorResponse},
        status.HTTP_409_CONFLICT: {"model": ErrorResponse},
    },
)
def create_subject_application(
    payload: SubjectApplicationPayload,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> SubjectApplicationRead:
    if current_user.role.name != RoleName.USER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "SUBJECT_APPLICATION_NOT_ALLOWED",
                "message": "Chỉ tài khoản người dùng mới có thể gửi hồ sơ chủ thể.",
                "details": {"current_role": current_user.role.name},
            },
        )
    if db.scalar(select(Subject.id).where(Subject.user_id == current_user.id)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "SUBJECT_APPLICATION_ALREADY_EXISTS",
                "message": "Tài khoản đã có hồ sơ chủ thể.",
                "details": None,
            },
        )

    subject = Subject(
        user_id=current_user.id,
        **payload.model_dump(mode="json"),
        status="pending",
    )
    save_application(db, subject)
    return to_subject_application_read(subject)


@router.get(
    "/me",
    response_model=SubjectApplicationRead,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
    },
)
def get_my_subject_application(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> SubjectApplicationRead:
    return to_subject_application_read(get_own_application(db, current_user.id))


@router.put(
    "/me",
    response_model=SubjectApplicationRead,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_409_CONFLICT: {"model": ErrorResponse},
    },
)
def resubmit_subject_application(
    payload: SubjectApplicationPayload,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> SubjectApplicationRead:
    subject = get_own_application(db, current_user.id)
    if subject.status == "approved":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "APPROVED_SUBJECT_CANNOT_RESUBMIT",
                "message": "Hồ sơ đã được duyệt và không thể gửi lại tại đây.",
                "details": None,
            },
        )

    for field, value in payload.model_dump(mode="json").items():
        setattr(subject, field, value)
    subject.status = "pending"
    subject.reviewed_by = None
    subject.reviewed_at = None
    subject.rejection_reason = None
    save_application(db, subject)
    return to_subject_application_read(subject)
