from pathlib import Path as FilePath
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Path, Request, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.core.config import get_settings
from app.core.database import get_db
from app.models.product import ProductImage
from app.schemas.product_management import ProductImageUploadResponse
from app.services.product_workflow import get_approved_subject, workflow_error


router = APIRouter(prefix="/product-images")
settings = get_settings()
ALLOWED_IMAGES = {
    "image/jpeg": ("jpg", lambda header: header.startswith(b"\xff\xd8\xff")),
    "image/png": ("png", lambda header: header.startswith(b"\x89PNG\r\n\x1a\n")),
    "image/webp": (
        "webp",
        lambda header: header.startswith(b"RIFF") and header[8:12] == b"WEBP",
    ),
}


def subject_upload_directory(subject_id: int) -> FilePath:
    directory = settings.upload_directory / "products" / str(subject_id)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


@router.post("", response_model=ProductImageUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_product_image(
    request: Request,
    current_user: CurrentUser,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ProductImageUploadResponse:
    subject = get_approved_subject(db, current_user)
    content_type = (file.content_type or "").lower()
    image_config = ALLOWED_IMAGES.get(content_type)
    if image_config is None:
        raise workflow_error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "INVALID_IMAGE_TYPE",
            "Chỉ chấp nhận ảnh JPEG, PNG hoặc WebP.",
        )

    extension, signature_matches = image_config
    header = await file.read(16)
    if not signature_matches(header):
        raise workflow_error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "INVALID_IMAGE_CONTENT",
            "Nội dung file không khớp định dạng ảnh đã khai báo.",
        )

    file_name = f"{uuid4().hex}.{extension}"
    storage_path = f"products/{subject.id}/{file_name}"
    target = subject_upload_directory(subject.id) / file_name
    total = 0
    try:
        with target.open("wb") as output:
            chunk = header
            while chunk:
                total += len(chunk)
                if total > settings.upload_max_bytes:
                    raise workflow_error(
                        status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        "IMAGE_TOO_LARGE",
                        "Ảnh không được vượt quá 5 MB.",
                        {"max_bytes": settings.upload_max_bytes},
                    )
                output.write(chunk)
                chunk = await file.read(1024 * 1024)
    except Exception:
        target.unlink(missing_ok=True)
        raise
    finally:
        await file.close()

    image_url = f"{str(request.base_url).rstrip('/')}/uploads/{storage_path}"
    return ProductImageUploadResponse(
        image_url=image_url,
        storage_path=storage_path,
        content_type=content_type,
        size_bytes=total,
    )


@router.delete(
    "/{file_name}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_unlinked_product_image(
    current_user: CurrentUser,
    file_name: str = Path(pattern=r"^[0-9a-f]{32}\.(jpg|png|webp)$"),
    db: Session = Depends(get_db),
) -> Response:
    subject = get_approved_subject(db, current_user)
    storage_path = f"products/{subject.id}/{file_name}"
    if db.scalar(
        select(ProductImage.id).where(ProductImage.storage_path == storage_path)
    ) is not None:
        raise workflow_error(
            status.HTTP_409_CONFLICT,
            "PRODUCT_IMAGE_IN_USE",
            "Ảnh đã được liên kết với sản phẩm và không thể xóa như ảnh tạm.",
        )
    target = subject_upload_directory(subject.id) / file_name
    if not target.is_file():
        raise workflow_error(
            status.HTTP_404_NOT_FOUND,
            "PRODUCT_IMAGE_NOT_FOUND",
            "Không tìm thấy ảnh tạm thuộc chủ thể hiện tại.",
        )
    target.unlink()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
