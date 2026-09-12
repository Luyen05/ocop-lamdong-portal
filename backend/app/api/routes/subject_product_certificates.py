from pathlib import Path as FilePath
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Path, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.core.config import get_settings
from app.core.database import get_db
from app.models.product import Product
from app.schemas.product_management import ProductCertificateUploadResponse
from app.services.product_workflow import get_approved_subject, get_owned_product, workflow_error


router = APIRouter(prefix="/product-certificates")
settings = get_settings()
ALLOWED_CERTIFICATES = {
    "application/pdf": ("pdf", lambda header: header.startswith(b"%PDF-")),
    "image/jpeg": ("jpg", lambda header: header.startswith(b"\xff\xd8\xff")),
    "image/png": ("png", lambda header: header.startswith(b"\x89PNG\r\n\x1a\n")),
}


def subject_certificate_directory(subject_id: int) -> FilePath:
    directory = settings.upload_directory / "certificates" / str(subject_id)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def certificate_response(product: Product) -> FileResponse:
    if not product.certificate_storage_path:
        raise workflow_error(
            status.HTTP_404_NOT_FOUND,
            "PRODUCT_CERTIFICATE_NOT_FOUND",
            "Sản phẩm chưa có file chứng nhận tải lên hệ thống.",
        )
    target = settings.upload_directory / product.certificate_storage_path
    if not target.is_file():
        raise workflow_error(
            status.HTTP_404_NOT_FOUND,
            "PRODUCT_CERTIFICATE_FILE_MISSING",
            "File chứng nhận không còn tồn tại trên máy chủ.",
        )
    media_types = {".pdf": "application/pdf", ".jpg": "image/jpeg", ".png": "image/png"}
    return FileResponse(target, media_type=media_types[target.suffix.lower()], filename=target.name)


@router.post("", response_model=ProductCertificateUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_product_certificate(
    current_user: CurrentUser,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ProductCertificateUploadResponse:
    subject = get_approved_subject(db, current_user)
    content_type = (file.content_type or "").lower()
    config = ALLOWED_CERTIFICATES.get(content_type)
    if config is None:
        raise workflow_error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "INVALID_CERTIFICATE_TYPE",
            "Chỉ chấp nhận chứng nhận PDF, JPEG hoặc PNG.",
        )
    extension, signature_matches = config
    header = await file.read(16)
    if not signature_matches(header):
        raise workflow_error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "INVALID_CERTIFICATE_CONTENT",
            "Nội dung file không khớp định dạng đã khai báo.",
        )
    file_name = f"{uuid4().hex}.{extension}"
    storage_path = f"certificates/{subject.id}/{file_name}"
    target = subject_certificate_directory(subject.id) / file_name
    total = 0
    try:
        with target.open("wb") as output:
            chunk = header
            while chunk:
                total += len(chunk)
                if total > settings.certificate_upload_max_bytes:
                    raise workflow_error(
                        status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        "CERTIFICATE_TOO_LARGE",
                        "File chứng nhận không được vượt quá 10 MB.",
                        {"max_bytes": settings.certificate_upload_max_bytes},
                    )
                output.write(chunk)
                chunk = await file.read(1024 * 1024)
    except Exception:
        target.unlink(missing_ok=True)
        raise
    finally:
        await file.close()
    return ProductCertificateUploadResponse(
        storage_path=storage_path,
        content_type=content_type,
        size_bytes=total,
        original_filename=file.filename or file_name,
    )


@router.delete("/{file_name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_unlinked_product_certificate(
    current_user: CurrentUser,
    file_name: str = Path(pattern=r"^[0-9a-f]{32}\.(pdf|jpg|png)$"),
    db: Session = Depends(get_db),
) -> Response:
    subject = get_approved_subject(db, current_user)
    storage_path = f"certificates/{subject.id}/{file_name}"
    if db.scalar(select(Product.id).where(Product.certificate_storage_path == storage_path)) is not None:
        raise workflow_error(
            status.HTTP_409_CONFLICT,
            "PRODUCT_CERTIFICATE_IN_USE",
            "File chứng nhận đã được liên kết với sản phẩm.",
        )
    target = subject_certificate_directory(subject.id) / file_name
    if not target.is_file():
        raise workflow_error(
            status.HTTP_404_NOT_FOUND,
            "PRODUCT_CERTIFICATE_NOT_FOUND",
            "Không tìm thấy file chứng nhận tạm của chủ thể hiện tại.",
        )
    target.unlink()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/products/{product_id}", response_class=FileResponse)
def download_my_product_certificate(
    product_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> FileResponse:
    subject = get_approved_subject(db, current_user)
    return certificate_response(get_owned_product(db, product_id, subject.id))
