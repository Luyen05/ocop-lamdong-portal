"""Lưu ảnh lên Cloudinary: gọi API có chữ ký bằng httpx; kiểm thử dùng MockTransport nên không chạm mạng thật."""

import hashlib
import re
from urllib.parse import unquote_plus

import httpx
import pytest
from pydantic import ValidationError

from app.api.routes import subject_product_images
from app.core.config import Settings
from app.services import image_storage
from test_subject_products import auth_header, product_payload, subject_product_context  # noqa: F401

PNG = b"\x89PNG\r\n\x1a\n" + b"test-image"


class FakeCloudinary:
    """Giả lập Cloudinary: ghi lại mọi yêu cầu, lưu ảnh đã tải lên theo public_id."""

    def __init__(self, *, upload_status: int = 200) -> None:
        self.requests: list[httpx.Request] = []
        self.stored: set[str] = set()
        self.upload_status = upload_status

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        url = str(request.url)
        if url.endswith("/image/upload") and request.method == "POST":
            if self.upload_status != 200:
                return httpx.Response(self.upload_status, json={"error": {"message": "lỗi giả lập"}})
            public_id = self.field(request, "public_id")
            self.stored.add(public_id)
            return httpx.Response(
                200,
                json={"secure_url": f"https://res.cloudinary.com/demo/image/upload/v1/{public_id}.png"},
            )
        if url.endswith("/image/destroy") and request.method == "POST":
            public_id = self.field(request, "public_id")
            found = public_id in self.stored
            self.stored.discard(public_id)
            return httpx.Response(200, json={"result": "ok" if found else "not found"})
        if request.method == "GET" and url.startswith("https://res.cloudinary.com/demo/image/upload/"):
            public_id = url.removeprefix("https://res.cloudinary.com/demo/image/upload/").rsplit(".", 1)[0]
            return httpx.Response(200 if public_id in self.stored else 404)
        return httpx.Response(500)

    @staticmethod
    def field(request: httpx.Request, name: str) -> str:
        body = request.read().decode("latin-1")
        multipart = re.search(rf'name="{name}"\r\n\r\n(.*?)\r\n--', body, re.S)
        if multipart:
            return multipart.group(1)
        form = re.search(rf"(?:^|&){name}=([^&]*)", body)
        assert form, f"thiếu trường {name} trong yêu cầu gửi Cloudinary"
        return unquote_plus(form.group(1))

    def calls(self, suffix: str) -> list[httpx.Request]:
        return [request for request in self.requests if str(request.url).endswith(suffix)]


@pytest.fixture
def cloudinary(monkeypatch, tmp_path) -> FakeCloudinary:
    fake = FakeCloudinary()
    settings = image_storage.get_settings()
    monkeypatch.setattr(settings, "image_storage", "cloudinary")
    monkeypatch.setattr(settings, "cloudinary_cloud_name", "demo")
    monkeypatch.setattr(settings, "cloudinary_api_key", "key-123")
    monkeypatch.setattr(settings, "cloudinary_api_secret", type(settings.jwt_secret_key)("secret-abc"))
    monkeypatch.setattr(settings, "cloudinary_folder", "ocop")
    monkeypatch.setattr(settings, "upload_directory", tmp_path)
    monkeypatch.setattr(image_storage, "cloudinary_transport", lambda: httpx.MockTransport(fake.handler))
    return fake


def test_cloudinary_signature_matches_documented_algorithm(cloudinary) -> None:
    params = {"timestamp": "1315060510", "public_id": "sample_image"}
    expected = hashlib.sha1(b"public_id=sample_image&timestamp=1315060510secret-abc").hexdigest()

    assert image_storage.cloudinary_signature(params) == expected


def test_cloudinary_settings_require_credentials() -> None:
    with pytest.raises(ValidationError, match="CLOUDINARY_CLOUD_NAME"):
        Settings(_env_file=None, image_storage="cloudinary")

    ok = Settings(
        _env_file=None,
        image_storage="cloudinary",
        cloudinary_cloud_name="demo",
        cloudinary_api_key="key",
        cloudinary_api_secret="secret",
    )
    assert ok.image_storage == "cloudinary"
    assert Settings(_env_file=None).image_storage == "local"


def test_upload_link_and_delete_product_image_on_cloudinary(subject_product_context, cloudinary, tmp_path) -> None:
    client, _ = subject_product_context
    headers = auth_header(1, "subject")

    uploaded = client.post(
        "/api/v1/subject/product-images",
        headers=headers,
        files={"file": ("product.png", PNG, "image/png")},
    )

    assert uploaded.status_code == 201
    data = uploaded.json()
    assert data["storage_path"].startswith("products/1/")
    assert data["image_url"].startswith("https://res.cloudinary.com/demo/image/upload/")
    assert data["size_bytes"] == len(PNG)
    assert not any(tmp_path.rglob("*.png")), "ở chế độ Cloudinary không được ghi ảnh ra thư mục cục bộ"
    (upload_request,) = cloudinary.calls("/image/upload")
    public_id = cloudinary.field(upload_request, "public_id")
    assert public_id == "ocop/" + data["storage_path"].removesuffix(".png")
    timestamp = cloudinary.field(upload_request, "timestamp")
    assert cloudinary.field(upload_request, "api_key") == "key-123"
    assert cloudinary.field(upload_request, "signature") == hashlib.sha1(
        f"public_id={public_id}&timestamp={timestamp}secret-abc".encode()
    ).hexdigest()

    payload = product_payload("OCOP-LD-CLOUD")
    payload["images"] = [
        {"image_url": data["image_url"], "storage_path": data["storage_path"], "is_primary": True, "sort_order": 0}
    ]
    created = client.post("/api/v1/subject/products", headers=headers, json=payload)
    assert created.status_code == 201
    assert created.json()["images"][0]["image_url"] == data["image_url"]

    file_name = data["storage_path"].rsplit("/", 1)[1]
    assert client.delete(f"/api/v1/subject/product-images/{file_name}", headers=headers).status_code == 409
    assert cloudinary.calls("/image/destroy") == []


def test_delete_unlinked_image_destroys_it_on_cloudinary(subject_product_context, cloudinary) -> None:
    client, _ = subject_product_context
    headers = auth_header(1, "subject")
    uploaded = client.post(
        "/api/v1/subject/product-images", headers=headers, files={"file": ("a.png", PNG, "image/png")}
    ).json()
    file_name = uploaded["storage_path"].rsplit("/", 1)[1]

    other_owner = client.delete(f"/api/v1/subject/product-images/{file_name}", headers=auth_header(2, "subject"))
    deleted = client.delete(f"/api/v1/subject/product-images/{file_name}", headers=headers)
    again = client.delete(f"/api/v1/subject/product-images/{file_name}", headers=headers)

    assert other_owner.status_code == 404
    assert deleted.status_code == 204
    assert again.status_code == 404
    (destroy,) = cloudinary.calls("/image/destroy")
    assert cloudinary.field(destroy, "invalidate") == "true"
    assert cloudinary.field(destroy, "public_id") == "ocop/" + uploaded["storage_path"].removesuffix(".png")


def test_link_rejects_image_missing_on_cloudinary(subject_product_context, cloudinary) -> None:
    client, _ = subject_product_context
    payload = product_payload("OCOP-LD-MISSING")
    payload["images"] = [
        {
            "image_url": "https://res.cloudinary.com/demo/image/upload/ocop/products/1/" + "a" * 32 + ".png",
            "storage_path": "products/1/" + "a" * 32 + ".png",
            "is_primary": True,
            "sort_order": 0,
        }
    ]

    response = client.post("/api/v1/subject/products", headers=auth_header(1, "subject"), json=payload)

    assert response.status_code == 422
    assert response.json()["code"] == "PRODUCT_IMAGE_NOT_FOUND"


def test_cloudinary_errors_return_502_and_large_files_never_leave_server(subject_product_context, cloudinary) -> None:
    client, _ = subject_product_context
    headers = auth_header(1, "subject")

    oversized = client.post(
        "/api/v1/subject/product-images",
        headers=headers,
        files={"file": ("big.png", b"\x89PNG\r\n\x1a\n" + b"0" * (5 * 1024 * 1024), "image/png")},
    )
    assert oversized.status_code == 413
    assert cloudinary.requests == []

    cloudinary.upload_status = 500
    failed = client.post(
        "/api/v1/subject/product-images", headers=headers, files={"file": ("a.png", PNG, "image/png")}
    )
    assert failed.status_code == 502
    assert failed.json()["code"] == "IMAGE_STORAGE_UNAVAILABLE"
    assert "secret-abc" not in failed.text


def test_certificates_stay_local_when_images_use_cloudinary(subject_product_context, cloudinary, tmp_path) -> None:
    from app.api.routes import subject_product_certificates

    client, _ = subject_product_context
    uploaded = client.post(
        "/api/v1/subject/product-certificates",
        headers=auth_header(1, "subject"),
        files={"file": ("cert.pdf", b"%PDF-1.4 demo", "application/pdf")},
    )

    assert uploaded.status_code == 201
    assert (tmp_path / uploaded.json()["storage_path"]).is_file()
    assert cloudinary.requests == []
