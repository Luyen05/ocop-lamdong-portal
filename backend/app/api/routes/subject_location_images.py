"""Chủ thể tải ảnh điểm du lịch lên trước, rồi gắn đường dẫn vào hồ sơ điểm."""

from fastapi import APIRouter, Depends, File, Path, Request, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.core.database import get_db
from app.models.location import LocationImage, TourismLocationChangeRequest
from app.schemas.location_management import LocationImageUploadResponse
from app.services.image_storage import (
    IMAGE_FILE_NAME_PATTERN,
    delete_unlinked_subject_image,
    store_subject_image,
)
from app.services.location_workflow import (
    ACTIVE_CHANGE_REQUEST_STATUSES,
    LOCATION_IMAGE_FOLDER,
    get_location_subject,
)


router = APIRouter(prefix="/location-images")


def image_in_use(db: Session, subject_id: int, storage_path: str) -> bool:
    """Ảnh đang gắn vào điểm, hoặc nằm trong yêu cầu cập nhật chưa xử lý, không được xóa."""

    if db.scalar(select(LocationImage.id).where(LocationImage.storage_path == storage_path)) is not None:
        return True
    proposals = db.scalars(
        select(TourismLocationChangeRequest.proposed_data).where(
            TourismLocationChangeRequest.subject_id == subject_id,
            TourismLocationChangeRequest.request_type == "update",
            TourismLocationChangeRequest.status.in_(ACTIVE_CHANGE_REQUEST_STATUSES),
        )
    )
    return any(
        image.get("storage_path") == storage_path
        for proposal in proposals
        for image in (proposal or {}).get("images", [])
    )


@router.post("", response_model=LocationImageUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_location_image(
    request: Request,
    current_user: CurrentUser,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> LocationImageUploadResponse:
    subject = get_location_subject(db, current_user)
    stored = await store_subject_image(
        file,
        folder=LOCATION_IMAGE_FOLDER,
        subject_id=subject.id,
        base_url=str(request.base_url),
    )
    return LocationImageUploadResponse(
        image_url=stored.image_url,
        storage_path=stored.storage_path,
        content_type=stored.content_type,
        size_bytes=stored.size_bytes,
    )


@router.delete("/{file_name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_unlinked_location_image(
    current_user: CurrentUser,
    file_name: str = Path(pattern=IMAGE_FILE_NAME_PATTERN),
    db: Session = Depends(get_db),
) -> Response:
    subject = get_location_subject(db, current_user)
    storage_path = f"{LOCATION_IMAGE_FOLDER}/{subject.id}/{file_name}"
    delete_unlinked_subject_image(
        folder=LOCATION_IMAGE_FOLDER,
        subject_id=subject.id,
        file_name=file_name,
        in_use=image_in_use(db, subject.id, storage_path),
        error_prefix="LOCATION_IMAGE",
        in_use_message="Ảnh đã được gắn vào điểm du lịch và không thể xóa như ảnh tạm.",
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
