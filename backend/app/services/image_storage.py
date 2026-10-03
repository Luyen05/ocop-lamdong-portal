"""Lưu ảnh chủ thể tải lên (ảnh sản phẩm, ảnh điểm du lịch).

Có hai nơi lưu, chọn bằng biến môi trường ``IMAGE_STORAGE``:

- ``local`` (mặc định): ``<upload_directory>/<folder>/<subject_id>/<uuid>.<ext>``, phục vụ công khai qua
  ``/uploads/<folder>/...`` (xem app/main.py). Dùng khi phát triển và khi chạy kiểm thử.
- ``cloudinary``: tải lên Cloudinary bằng API có chữ ký (``httpx``, không dùng SDK). ``storage_path`` vẫn là
  ``<folder>/<subject_id>/<uuid>.<ext>`` nên mọi chỗ kiểm tra quyền sở hữu không đổi.

Chỉ nhận JPEG, PNG, WebP; kiểm tra chữ ký file chứ không tin loại file trình duyệt khai báo. File chứng nhận
sản phẩm không đi qua đây: luôn lưu cục bộ và chỉ tải được qua API có kiểm tra quyền.
"""

from __future__ import annotations

import hashlib
import re
import time
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import httpx
from fastapi import UploadFile, status

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
    """Ảnh đã tải lên còn tồn tại ở nơi lưu đang dùng (thư mục cục bộ hoặc Cloudinary)."""

    if get_settings().image_storage == "cloudinary":
        return cloudinary_image_exists(storage_path)
    return (get_settings().upload_directory / storage_path).is_file()


# ---------------------------------------------------------------------------
# Cloudinary (gọi API bằng httpx, không thêm thư viện)
# ---------------------------------------------------------------------------


def cloudinary_transport() -> httpx.BaseTransport | None:
    """Kiểm thử ghi đè hàm này để chặn mạng thật; chạy thật thì dùng mặc định của httpx."""

    return None


def cloudinary_signature(params: dict[str, str]) -> str:
    """Chữ ký Cloudinary: SHA-1 của các tham số (trừ file, api_key) sắp theo tên, nối bằng ``&``, rồi cộng API secret."""

    to_sign = "&".join(f"{key}={params[key]}" for key in sorted(params))
    secret = get_settings().cloudinary_api_secret.get_secret_value()
    return hashlib.sha1(f"{to_sign}{secret}".encode("utf-8")).hexdigest()


def cloudinary_public_id(storage_path: str) -> str:
    """``products/3/abc.jpg`` → ``<thư mục gốc>/products/3/abc`` (Cloudinary không đưa đuôi file vào public_id)."""

    settings = get_settings()
    return f"{settings.cloudinary_folder}/{storage_path.rsplit('.', 1)[0]}"


def cloudinary_image_url(storage_path: str) -> str:
    settings = get_settings()
    return (
        f"https://res.cloudinary.com/{settings.cloudinary_cloud_name}/image/upload/"
        f"{settings.cloudinary_folder}/{storage_path}"
    )


def cloudinary_api_url(action: str) -> str:
    return f"https://api.cloudinary.com/v1_1/{get_settings().cloudinary_cloud_name}/image/{action}"


def image_storage_unavailable(reason: str) -> Exception:
    return workflow_error(
        status.HTTP_502_BAD_GATEWAY,
        "IMAGE_STORAGE_UNAVAILABLE",
        "Không lưu được ảnh lên dịch vụ lưu trữ. Vui lòng thử lại sau.",
        {"reason": reason},
    )


async def cloudinary_upload(content: bytes, storage_path: str, file_name: str, content_type: str) -> str:
    """Tải ảnh lên Cloudinary, trả về đường dẫn https công khai của ảnh."""

    settings = get_settings()
    signed = {"public_id": cloudinary_public_id(storage_path), "timestamp": str(int(time.time()))}
    data = {**signed, "api_key": settings.cloudinary_api_key, "signature": cloudinary_signature(signed)}
    try:
        async with httpx.AsyncClient(
            timeout=settings.cloudinary_timeout_seconds,
            transport=cloudinary_transport(),
        ) as client:
            response = await client.post(
                cloudinary_api_url("upload"),
                data=data,
                files={"file": (file_name, content, content_type)},
            )
    except httpx.HTTPError as error:
        raise image_storage_unavailable(type(error).__name__) from error
    if response.status_code != 200:
        raise image_storage_unavailable(f"HTTP {response.status_code}")
    secure_url = response.json().get("secure_url")
    if not isinstance(secure_url, str) or not secure_url.startswith("https://"):
        raise image_storage_unavailable("INVALID_RESPONSE")
    return secure_url


def cloudinary_image_exists(storage_path: str) -> bool:
    settings = get_settings()
    try:
        with httpx.Client(
            timeout=settings.cloudinary_timeout_seconds,
            transport=cloudinary_transport(),
            follow_redirects=True,
        ) as client:
            with client.stream("GET", cloudinary_image_url(storage_path)) as response:
                return response.status_code == 200
    except httpx.HTTPError as error:
        raise image_storage_unavailable(type(error).__name__) from error


def cloudinary_destroy(storage_path: str) -> None:
    settings = get_settings()
    signed = {
        "invalidate": "true",
        "public_id": cloudinary_public_id(storage_path),
        "timestamp": str(int(time.time())),
    }
    data = {**signed, "api_key": settings.cloudinary_api_key, "signature": cloudinary_signature(signed)}
    try:
        with httpx.Client(
            timeout=settings.cloudinary_timeout_seconds,
            transport=cloudinary_transport(),
        ) as client:
            response = client.post(cloudinary_api_url("destroy"), data=data)
    except httpx.HTTPError as error:
        raise image_storage_unavailable(type(error).__name__) from error
    if response.status_code != 200 or response.json().get("result") not in {"ok", "not found"}:
        raise image_storage_unavailable(f"HTTP {response.status_code}")


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
    if settings.image_storage == "cloudinary":
        return await store_in_cloudinary(
            file,
            header=header,
            storage_path=storage_path,
            file_name=file_name,
            content_type=content_type,
        )
    target = subject_image_directory(folder, subject_id) / file_name
    total = 0
    try:
        with target.open("wb") as output:
            chunk = header
            while chunk:
                total += len(chunk)
                if total > settings.upload_max_bytes:
                    raise image_too_large()
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


def image_too_large() -> Exception:
    return workflow_error(
        status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        "IMAGE_TOO_LARGE",
        "Ảnh không được vượt quá 5 MB.",
        {"max_bytes": get_settings().upload_max_bytes},
    )


async def store_in_cloudinary(
    file: UploadFile,
    *,
    header: bytes,
    storage_path: str,
    file_name: str,
    content_type: str,
) -> StoredImage:
    """Đọc ảnh vào bộ nhớ (tối đa ``upload_max_bytes``) rồi tải lên Cloudinary."""

    limit = get_settings().upload_max_bytes
    chunks = [header]
    total = len(header)
    try:
        chunk = await file.read(1024 * 1024)
        while chunk:
            total += len(chunk)
            if total > limit:
                raise image_too_large()
            chunks.append(chunk)
            chunk = await file.read(1024 * 1024)
    finally:
        await file.close()
    image_url = await cloudinary_upload(b"".join(chunks), storage_path, file_name, content_type)
    return StoredImage(
        image_url=image_url,
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
    storage_path = f"{folder}/{subject_id}/{file_name}"
    if not uploaded_file_exists(storage_path):
        raise workflow_error(
            status.HTTP_404_NOT_FOUND,
            f"{error_prefix}_NOT_FOUND",
            "Không tìm thấy ảnh tạm thuộc chủ thể hiện tại.",
        )
    if get_settings().image_storage == "cloudinary":
        cloudinary_destroy(storage_path)
        return
    (subject_image_directory(folder, subject_id) / file_name).unlink()
