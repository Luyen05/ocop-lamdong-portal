"""Ảnh/chứng nhận tạm đang được dùng không xóa được; PUBLIC_BASE_URL; các lỗi nhỏ khi tải file."""

import inspect

import httpx
import pytest
from pydantic import ValidationError
from sqlalchemy import update

from app.api.routes import (
    subject_location_images,
    subject_product_certificates,
    subject_product_images,
)
from app.core.config import Settings
from app.models.product import Product
from app.services import image_storage
from test_subject_products import (  # noqa: F401
    auth_header,
    create_approved_product,
    product_payload,
    subject_product_context,
)

PNG = b"\x89PNG\r\n\x1a\n" + b"test-image"
PDF = b"%PDF-1.7\ncertificate"


@pytest.fixture
def local_uploads(monkeypatch, tmp_path):
    settings = image_storage.get_settings()
    monkeypatch.setattr(settings, "upload_directory", tmp_path)
    monkeypatch.setattr(settings, "image_storage", "local")
    monkeypatch.setattr(settings, "public_base_url", "")
    return tmp_path


def upload_image(client, headers=None) -> dict:
    response = client.post(
        "/api/v1/subject/product-images",
        headers=headers or auth_header(1, "subject"),
        files={"file": ("a.png", PNG, "image/png")},
    )
    assert response.status_code == 201
    return response.json()


def upload_certificate(client) -> dict:
    response = client.post(
        "/api/v1/subject/product-certificates",
        headers=auth_header(1, "subject"),
        files={"file": ("cert.pdf", PDF, "application/pdf")},
    )
    assert response.status_code == 201
    return response.json()


def file_name(storage_path: str) -> str:
    return storage_path.rsplit("/", 1)[1]


def test_unlinked_product_image_can_be_deleted(subject_product_context, local_uploads) -> None:
    client, _ = subject_product_context
    uploaded = upload_image(client)

    deleted = client.delete(
        f"/api/v1/subject/product-images/{file_name(uploaded['storage_path'])}",
        headers=auth_header(1, "subject"),
    )

    assert deleted.status_code == 204
    assert not (local_uploads / uploaded["storage_path"]).exists()


def test_image_in_pending_change_request_cannot_be_deleted(subject_product_context, local_uploads) -> None:
    client, _ = subject_product_context
    product, headers, admin_headers = create_approved_product(client, "OCOP-LD-IN-USE")
    uploaded = upload_image(client)
    certificate = upload_certificate(client)
    proposed = product_payload("OCOP-LD-IN-USE")
    proposed["certificate_url"] = None
    proposed["certificate_storage_path"] = certificate["storage_path"]
    proposed["images"] = [
        {
            "image_url": uploaded["image_url"],
            "storage_path": uploaded["storage_path"],
            "is_primary": True,
            "sort_order": 0,
        }
    ]
    requested = client.post(
        f"/api/v1/subject/products/{product['id']}/change-requests",
        headers=headers,
        json={"proposed_data": proposed, "reason": "Đổi ảnh và giấy chứng nhận."},
    )
    assert requested.status_code == 201

    image_delete = client.delete(
        f"/api/v1/subject/product-images/{file_name(uploaded['storage_path'])}", headers=headers
    )
    certificate_delete = client.delete(
        f"/api/v1/subject/product-certificates/{file_name(certificate['storage_path'])}", headers=headers
    )

    assert image_delete.status_code == 409
    assert image_delete.json()["code"] == "PRODUCT_IMAGE_IN_USE"
    assert certificate_delete.status_code == 409
    assert certificate_delete.json()["code"] == "PRODUCT_CERTIFICATE_IN_USE"
    assert (local_uploads / uploaded["storage_path"]).is_file()
    assert (local_uploads / certificate["storage_path"]).is_file()

    # Hủy yêu cầu thì ảnh và chứng nhận lại là file tạm, xóa được.
    cancelled = client.post(
        f"/api/v1/subject/product-change-requests/{requested.json()['id']}/cancel", headers=headers
    )
    assert cancelled.status_code == 200
    assert client.delete(
        f"/api/v1/subject/product-images/{file_name(uploaded['storage_path'])}", headers=headers
    ).status_code == 204
    assert client.delete(
        f"/api/v1/subject/product-certificates/{file_name(certificate['storage_path'])}", headers=headers
    ).status_code == 204


def test_linked_certificate_cannot_be_deleted(subject_product_context, local_uploads) -> None:
    client, _ = subject_product_context
    certificate = upload_certificate(client)
    payload = product_payload("OCOP-LD-CERT-LINKED")
    payload["certificate_url"] = None
    payload["certificate_storage_path"] = certificate["storage_path"]
    assert client.post("/api/v1/subject/products", headers=auth_header(1, "subject"), json=payload).status_code == 201

    response = client.delete(
        f"/api/v1/subject/product-certificates/{file_name(certificate['storage_path'])}",
        headers=auth_header(1, "subject"),
    )

    assert response.status_code == 409
    assert response.json()["code"] == "PRODUCT_CERTIFICATE_IN_USE"


def test_certificate_with_unknown_extension_is_served_as_octet_stream(
    subject_product_context, local_uploads
) -> None:
    client, testing_session = subject_product_context
    created = client.post(
        "/api/v1/subject/products",
        headers=auth_header(1, "subject"),
        json={"category_id": 1, "name": "Sản phẩm có chứng nhận cũ"},
    )
    product_id = created.json()["id"]
    legacy = local_uploads / "certificates" / "1" / "chung-nhan-cu.tiff"
    legacy.parent.mkdir(parents=True, exist_ok=True)
    legacy.write_bytes(b"legacy")
    with testing_session() as session:
        session.execute(
            update(Product)
            .where(Product.id == product_id)
            .values(certificate_storage_path="certificates/1/chung-nhan-cu.tiff")
        )
        session.commit()

    response = client.get(
        f"/api/v1/subject/product-certificates/products/{product_id}",
        headers=auth_header(1, "subject"),
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"
    assert response.content == b"legacy"


# ---------------------------------------------------------------------------
# PUBLIC_BASE_URL
# ---------------------------------------------------------------------------


def test_local_image_url_uses_request_base_url_by_default(subject_product_context, local_uploads) -> None:
    client, _ = subject_product_context

    uploaded = upload_image(client)

    assert uploaded["image_url"] == f"http://testserver/uploads/{uploaded['storage_path']}"


def test_local_image_url_uses_public_base_url_when_configured(
    subject_product_context, local_uploads, monkeypatch
) -> None:
    client, _ = subject_product_context
    monkeypatch.setattr(image_storage.get_settings(), "public_base_url", "https://ocop.example.vn")

    uploaded = upload_image(client)

    assert uploaded["image_url"] == f"https://ocop.example.vn/uploads/{uploaded['storage_path']}"


def test_public_base_url_setting_is_normalized_and_validated() -> None:
    assert Settings(_env_file=None).public_base_url == ""
    assert Settings(_env_file=None, public_base_url="  ").public_base_url == ""
    assert Settings(_env_file=None, public_base_url="https://ocop.example.vn/").public_base_url == (
        "https://ocop.example.vn"
    )
    assert Settings(_env_file=None, public_base_url="https://example.vn/api/").public_base_url == (
        "https://example.vn/api"
    )
    with pytest.raises(ValidationError, match="PUBLIC_BASE_URL"):
        Settings(_env_file=None, public_base_url="ocop.example.vn")
    with pytest.raises(ValidationError, match="PUBLIC_BASE_URL"):
        Settings(_env_file=None, public_base_url="https://ocop.example.vn/?a=1")


# ---------------------------------------------------------------------------
# Cloudinary trả 200 nhưng không phải JSON; route tải file chạy đồng bộ
# ---------------------------------------------------------------------------


def configure_cloudinary(monkeypatch, tmp_path, handler) -> None:
    settings = image_storage.get_settings()
    monkeypatch.setattr(settings, "image_storage", "cloudinary")
    monkeypatch.setattr(settings, "cloudinary_cloud_name", "demo")
    monkeypatch.setattr(settings, "cloudinary_api_key", "key-123")
    monkeypatch.setattr(settings, "cloudinary_api_secret", type(settings.jwt_secret_key)("secret-abc"))
    monkeypatch.setattr(settings, "upload_directory", tmp_path)
    monkeypatch.setattr(image_storage, "cloudinary_transport", lambda: httpx.MockTransport(handler))


@pytest.mark.parametrize(
    "body",
    [b"<html>Bad gateway</html>", b"[1, 2]", b"{\"secure_url\": \"http://not-https\"}"],
)
def test_cloudinary_non_json_success_response_returns_502(
    subject_product_context, monkeypatch, tmp_path, body
) -> None:
    client, _ = subject_product_context
    configure_cloudinary(monkeypatch, tmp_path, lambda request: httpx.Response(200, content=body))

    response = client.post(
        "/api/v1/subject/product-images",
        headers=auth_header(1, "subject"),
        files={"file": ("a.png", PNG, "image/png")},
    )

    assert response.status_code == 502
    assert response.json()["code"] == "IMAGE_STORAGE_UNAVAILABLE"
    assert response.json()["details"]["reason"] == "INVALID_RESPONSE"


def test_cloudinary_destroy_non_json_returns_502(monkeypatch, tmp_path) -> None:
    configure_cloudinary(monkeypatch, tmp_path, lambda request: httpx.Response(200, content=b"ok"))

    with pytest.raises(Exception) as error:
        image_storage.cloudinary_destroy("products/1/" + "a" * 32 + ".png")

    assert getattr(error.value, "status_code", None) == 502


def test_upload_endpoints_are_sync_so_they_run_in_threadpool() -> None:
    for endpoint in (
        subject_product_images.upload_product_image,
        subject_location_images.upload_location_image,
        subject_product_certificates.upload_product_certificate,
        image_storage.store_subject_image,
    ):
        assert not inspect.iscoroutinefunction(endpoint), endpoint.__name__
