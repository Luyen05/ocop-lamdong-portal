"""Lưu ảnh chủ thể tải lên (ảnh sản phẩm, ảnh điểm du lịch) vào thư mục uploads.

Ảnh được lưu tại ``<upload_directory>/<folder>/<subject_id>/<uuid>.<ext>`` và phục vụ công khai
qua ``/uploads/<folder>/...`` (xem app/main.py). Chỉ nhận JPEG, PNG, WebP; kiểm tra chữ ký file
chứ không tin loại file trình duyệt khai báo.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from fastapi import UploadFile, status
from uuid import uuid4

from app.core.config import get_settings
from app.services.product_workflow import workflow_error


ALLOWED_IMAGES = {
    "image/jpeg": ("jpg", lambda header: header.startswith(b"\xff\xd8\xff")),
    "image/png": ("png", lambda header: header.startswith(b"\x89PNG\r\n\x1a\n")),
    "image/webp": (
        "webp",
        lambda header: header.startswith(b"RIFF") and header[8:12] == b"WEBP",
    ),
}
IMAGE_FILE_NAME_PATTERN = r"^[0-9a-f]{32}\.(jpg|png|webp)$"


@dataclass(frozen=True)
class StoredImage:
    image_url: str
    storage_path: str
    content_type: str
    size_bytes: int


def subject_image_directory(folder: str, subject_id: int) -> Path:
    directory = get_settings().upload_directory / folder / str(subject_id)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def subject_image_pattern(folder: str, subject_id: int) -> str:
    return rf"{folder}/{subject_id}/[0-9a-f]{{32}}\.(jpg|png|webp)"


def is_subject_image_path(storage_path: str, folder: str, subject_id: int) -> bool:
    return re.fullmatch(subject_image_pattern(folder, subject_id), storage_path) is not None


def uploaded_file_exists(storage_path: str) -> bool:
    return (get_settings().upload_directory / storage_path).is_file()


async def store_subject_image(
    file: UploadFile,
    *,
    folder: str,
    subject_id: int,
    base_url: str,
) -> StoredImage:
    settings = get_settings()
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
    storage_path = f"{folder}/{subject_id}/{file_name}"
    target = subject_image_directory(folder, subject_id) / file_name
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

    return StoredImage(
        image_url=f"{base_url.rstrip('/')}/uploads/{storage_path}",
        storage_path=storage_path,
        content_type=content_type,
        size_bytes=total,
    )


def delete_unlinked_subject_image(
    *,
    folder: str,
    subject_id: int,
    file_name: str,
    in_use: bool,
    error_prefix: str,
    in_use_message: str,
) -> None:
    """Xóa ảnh tạm (đã tải lên nhưng chưa gắn vào hồ sơ nào) của chủ thể."""

    if in_use:
        raise workflow_error(status.HTTP_409_CONFLICT, f"{error_prefix}_IN_USE", in_use_message)
    target = subject_image_directory(folder, subject_id) / file_name
    if not target.is_file():
        raise workflow_error(
            status.HTTP_404_NOT_FOUND,
            f"{error_prefix}_NOT_FOUND",
            "Không tìm thấy ảnh tạm thuộc chủ thể hiện tại.",
        )
    target.unlink()
