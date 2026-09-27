from fastapi import APIRouter, Depends, File, Path, Request, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.core.config import get_settings
from app.core.database import get_db
from app.models.product import ProductImage
from app.schemas.product_management import ProductImageUploadResponse
from app.services.image_storage import (
    IMAGE_FILE_NAME_PATTERN,
    delete_unlinked_subject_image,
    store_subject_image,
)
from app.services.product_workflow import get_approved_subject


router = APIRouter(prefix="/product-images")
settings = get_settings()
IMAGE_FOLDER = "products"


@router.post("", response_model=ProductImageUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_product_image(
    request: Request,
    current_user: CurrentUser,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ProductImageUploadResponse:
    subject = get_approved_subject(db, current_user)
    stored = await store_subject_image(
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
        in_use=db.scalar(
            select(ProductImage.id).where(ProductImage.storage_path == storage_path)
        )
        is not None,
        error_prefix="PRODUCT_IMAGE",
        in_use_message="Ảnh đã được liên kết với sản phẩm và không thể xóa như ảnh tạm.",
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
