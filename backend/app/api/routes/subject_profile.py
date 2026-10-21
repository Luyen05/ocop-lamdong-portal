"""Chủ thể đã duyệt xem và sửa thông tin liên hệ của đơn vị.

Tên đơn vị, loại hình và mã số thuế đã được quản trị viên xác minh nên không sửa ở đây (liên hệ quản trị viên).
Router cha (/subject) đã chặn tài khoản không phải vai trò subject (403).
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.api.routes.subject_applications import save_application, to_subject_application_read
from app.core.database import get_db
from app.schemas.error import ErrorResponse
from app.schemas.subject import SubjectApplicationRead, SubjectProfileUpdate
from app.services.product_workflow import get_approved_subject, workflow_error


router = APIRouter(prefix="/profile")


@router.get(
    "",
    response_model=SubjectApplicationRead,
    responses={status.HTTP_403_FORBIDDEN: {"model": ErrorResponse}},
)
def get_subject_profile(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> SubjectApplicationRead:
    return to_subject_application_read(get_approved_subject(db, current_user))


@router.patch(
    "",
    response_model=SubjectApplicationRead,
    responses={
        status.HTTP_403_FORBIDDEN: {"model": ErrorResponse},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorResponse},
    },
)
def update_subject_profile(
    payload: SubjectProfileUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> SubjectApplicationRead:
    subject = get_approved_subject(db, current_user)
    if payload.locked_fields:
        raise workflow_error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "SUBJECT_IDENTITY_LOCKED",
            "Tên đơn vị, loại hình và mã số thuế đã được xác minh, không sửa được tại đây. "
            "Vui lòng liên hệ quản trị viên nếu cần thay đổi.",
            {"fields": payload.locked_fields},
        )
    for field, value in payload.editable_values().items():
        setattr(subject, field, str(value) if field == "email" and value is not None else value)
    save_application(db, subject)
    return to_subject_application_read(subject)
