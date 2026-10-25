from fastapi import APIRouter, Depends, File, Path, Request, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.core.config import get_settings
from app.core.database import get_db
from app.models.product import ProductChangeRequest, ProductImage
from app.schemas.product_management import ProductImageUploadResponse
from app.services.image_storage import (
    IMAGE_FILE_NAME_PATTERN,
    delete_unlinked_subject_image,
    store_subject_image,
)
from app.services.product_workflow import ACTIVE_CHANGE_REQUEST_STATUSES, get_approved_subject


router = APIRouter(prefix="/product-images")
settings = get_settings()
IMAGE_FOLDER = "products"


def active_product_proposals(db: Session, subject_id: int) -> list[dict]:
    """Dữ liệu đề xuất của các yêu cầu cập nhật sản phẩm chưa xử lý xong (chờ duyệt hoặc cần bổ sung)."""

    return [
        proposal or {}
        for proposal in db.scalars(
            select(ProductChangeRequest.proposed_data).where(
                ProductChangeRequest.subject_id == subject_id,
                ProductChangeRequest.request_type == "update",
                ProductChangeRequest.status.in_(ACTIVE_CHANGE_REQUEST_STATUSES),
            )
        )
    ]


def product_image_in_use(db: Session, subject_id: int, storage_path: str) -> bool:
    """Ảnh đang gắn vào sản phẩm, hoặc nằm trong yêu cầu cập nhật chưa xử lý, không được xóa."""

    if db.scalar(select(ProductImage.id).where(ProductImage.storage_path == storage_path)) is not None:
        return True
    return any(
        isinstance(image, dict) and image.get("storage_path") == storage_path
        for proposal in active_product_proposals(db, subject_id)
        for image in proposal.get("images") or []
    )


@router.post("", response_model=ProductImageUploadResponse, status_code=status.HTTP_201_CREATED)
def upload_product_image(
    request: Request,
    current_user: CurrentUser,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ProductImageUploadResponse:
    subject = get_approved_subject(db, current_user)
    stored = store_subject_image(
        file,
        folder=IMAGE_FOLDER,
        subject_id=subject.id,
        base_url=str(request.base_url),
    )
    return ProductImageUploadResponse(
        image_url=stored.image_url,
        storage_path=stored.storage_path,
        content_type=stored.content_type,
        size_bytes=stored.size_bytes,
    )


@router.delete(
    "/{file_name}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_unlinked_product_image(
    current_user: CurrentUser,
    file_name: str = Path(pattern=IMAGE_FILE_NAME_PATTERN),
    db: Session = Depends(get_db),
) -> Response:
    subject = get_approved_subject(db, current_user)
    storage_path = f"{IMAGE_FOLDER}/{subject.id}/{file_name}"
    delete_unlinked_subject_image(
        folder=IMAGE_FOLDER,
        subject_id=subject.id,
        file_name=file_name,
        in_use=product_image_in_use(db, subject.id, storage_path),
        error_prefix="PRODUCT_IMAGE",
        in_use_message=(
            "Ảnh đang được dùng cho sản phẩm hoặc yêu cầu cập nhật đang chờ duyệt, không thể xóa như ảnh tạm."
        ),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
