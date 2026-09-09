from collections.abc import Generator
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import app
from app.models.category import Category
from app.models.role import Role
from app.models.subject import Subject
from app.models.user import User


@pytest.fixture
def subject_product_context() -> Generator[tuple[TestClient, sessionmaker], None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(engine)
    with testing_session() as session:
        session.add_all(
            [
                Role(id=1, name="admin", description="Quản trị"),
                Role(id=2, name="subject", description="Chủ thể"),
                Role(id=3, name="user", description="Người dùng"),
                Category(id=1, name="Đồ uống", slug="do-uong"),
            ]
        )
        session.flush()
        session.add_all(
            [
                User(
                    id=1,
                    role_id=2,
                    email="subject@example.com",
                    hashed_password="not-used",
                    full_name="Chủ thể đã duyệt",
                    is_active=True,
                ),
                User(
                    id=2,
                    role_id=2,
                    email="other@example.com",
                    hashed_password="not-used",
                    full_name="Chủ thể khác",
                    is_active=True,
                ),
                User(
                    id=3,
                    role_id=3,
                    email="user@example.com",
                    hashed_password="not-used",
                    full_name="Người dùng",
                    is_active=True,
                ),
                User(
                    id=4,
                    role_id=1,
                    email="admin@example.com",
                    hashed_password="not-used",
                    full_name="Quản trị viên",
                    is_active=True,
                ),
            ]
        )
        session.flush()
        session.add_all(
            [
                Subject(
                    id=1,
                    user_id=1,
                    name="HTX Đà Lạt",
                    type="cooperative",
                    representative="Nguyễn Văn A",
                    phone="0912345678",
                    address="Đà Lạt",
                    district="Đà Lạt",
                    status="approved",
                ),
                Subject(
                    id=2,
                    user_id=2,
                    name="HTX Khác",
                    type="cooperative",
                    representative="Nguyễn Văn B",
                    phone="0987654321",
                    address="Bảo Lộc",
                    district="Bảo Lộc",
                    status="approved",
                ),
            ]
        )
        session.commit()

    def override_get_db() -> Generator[Session, None, None]:
        with testing_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client, testing_session
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


def auth_header(user_id: int, role: str) -> dict[str, str]:
    token = create_access_token(user_id=user_id, role=role)
    return {"Authorization": f"Bearer {token}"}


def product_payload(cert_code: str = "OCOP-LD-001") -> dict:
    issued_at = date.today() - timedelta(days=30)
    expires_at = date.today() + timedelta(days=365 * 2)
    return {
        "category_id": 1,
        "name": "Cà phê Arabica Cầu Đất",
        "star": 4,
        "price": "180000",
        "unit": "hộp 500g",
        "cert_code": cert_code,
        "cert_issued_at": issued_at.isoformat(),
        "cert_expires_at": expires_at.isoformat(),
        "issuing_authority": "Cơ quan có thẩm quyền tỉnh Lâm Đồng",
        "certificate_url": "https://example.com/certificates/ocop-001.pdf",
        "vietgap_code": None,
        "description": "Cà phê rang xay nguyên chất từ vùng Cầu Đất.",
        "story": "Sản phẩm gắn với vùng nguyên liệu địa phương.",
        "ingredients": "100% cà phê Arabica.",
        "usage_instructions": "Pha phin hoặc pha máy.",
        "images": [
            {
                "image_url": "https://example.com/products/coffee.webp",
                "is_primary": True,
                "sort_order": 0,
            }
        ],
    }


def test_subject_creates_draft_and_submits_for_moderation(subject_product_context) -> None:
    client, _ = subject_product_context
    headers = auth_header(1, "subject")

    created = client.post(
        "/api/v1/subject/products",
        headers=headers,
        json=product_payload(),
    )
    assert created.status_code == 201
    assert created.json()["status"] == "draft"
    assert created.json()["subject_id"] == 1

    public_before = client.get(f"/api/v1/products/{created.json()['slug']}")
    assert public_before.status_code == 404

    submitted = client.post(
        f"/api/v1/subject/products/{created.json()['id']}/submit",
        headers=headers,
    )
    assert submitted.status_code == 200
    assert submitted.json()["status"] == "pending"
    assert submitted.json()["submitted_at"] is not None


def test_admin_approves_product_before_it_becomes_public(subject_product_context) -> None:
    client, _ = subject_product_context
    subject_headers = auth_header(1, "subject")
    admin_headers = auth_header(4, "admin")
    created = client.post(
        "/api/v1/subject/products",
        headers=subject_headers,
        json=product_payload("OCOP-LD-APPROVE"),
    )
    product_id = created.json()["id"]
    client.post(
        f"/api/v1/subject/products/{product_id}/submit",
        headers=subject_headers,
    )

    hidden = client.get("/api/v1/products/ca-phe-arabica-cau-dat")
    approved = client.patch(
        f"/api/v1/admin/products/{product_id}/moderation",
        headers=admin_headers,
        json={"status": "approved", "note": "Đã đối chiếu giấy chứng nhận."},
    )
    public = client.get("/api/v1/products/ca-phe-arabica-cau-dat")

    assert hidden.status_code == 404
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
    assert approved.json()["moderation_note"] == "Đã đối chiếu giấy chứng nhận."
    assert public.status_code == 200


def test_admin_must_explain_revision_or_rejection(subject_product_context) -> None:
    client, _ = subject_product_context
    subject_headers = auth_header(1, "subject")
    admin_headers = auth_header(4, "admin")
    created = client.post(
        "/api/v1/subject/products",
        headers=subject_headers,
        json=product_payload("OCOP-LD-REVISION"),
    )
    product_id = created.json()["id"]
    client.post(
        f"/api/v1/subject/products/{product_id}/submit",
        headers=subject_headers,
    )

    missing_note = client.patch(
        f"/api/v1/admin/products/{product_id}/moderation",
        headers=admin_headers,
        json={"status": "needs_revision"},
    )
    revision = client.patch(
        f"/api/v1/admin/products/{product_id}/moderation",
        headers=admin_headers,
        json={"status": "needs_revision", "note": "Ảnh chứng nhận chưa rõ."},
    )

    assert missing_note.status_code == 422
    assert revision.status_code == 200
    assert revision.json()["status"] == "needs_revision"


def test_subject_cannot_access_admin_product_queue(subject_product_context) -> None:
    client, _ = subject_product_context
    response = client.get(
        "/api/v1/admin/products",
        headers=auth_header(1, "subject"),
    )

    assert response.status_code == 403
    assert response.json()["code"] == "INSUFFICIENT_PERMISSIONS"


def create_approved_product(client: TestClient, cert_code: str) -> tuple[dict, dict, dict]:
    subject_headers = auth_header(1, "subject")
    admin_headers = auth_header(4, "admin")
    created = client.post(
        "/api/v1/subject/products",
        headers=subject_headers,
        json=product_payload(cert_code),
    )
    assert created.status_code == 201
    product_id = created.json()["id"]
    submitted = client.post(
        f"/api/v1/subject/products/{product_id}/submit",
        headers=subject_headers,
    )
    assert submitted.status_code == 200
    approved = client.patch(
        f"/api/v1/admin/products/{product_id}/moderation",
        headers=admin_headers,
        json={"status": "approved"},
    )
    assert approved.status_code == 200
    return approved.json(), subject_headers, admin_headers


def test_approved_product_update_waits_for_admin(subject_product_context) -> None:
    client, _ = subject_product_context
    product, subject_headers, admin_headers = create_approved_product(
        client,
        "OCOP-LD-UPDATE",
    )
    proposed = product_payload("OCOP-LD-UPDATE")
    proposed["name"] = "Cà phê Arabica Cầu Đất phiên bản mới"
    proposed["price"] = "195000"

    requested = client.post(
        f"/api/v1/subject/products/{product['id']}/change-requests",
        headers=subject_headers,
        json={"proposed_data": proposed, "reason": "Cập nhật bao bì và giá bán."},
    )
    public_before = client.get(f"/api/v1/products/{product['slug']}")
    moderated = client.patch(
        f"/api/v1/admin/product-change-requests/{requested.json()['id']}/moderation",
        headers=admin_headers,
        json={"status": "approved", "note": "Thông tin khớp chứng nhận."},
    )
    public_after = client.get(f"/api/v1/products/{product['slug']}")

    assert requested.status_code == 201
    assert public_before.json()["name"] == "Cà phê Arabica Cầu Đất"
    assert moderated.status_code == 200
    assert moderated.json()["status"] == "approved"
    assert public_after.json()["name"] == proposed["name"]
    assert public_after.json()["price"] == 195000


def test_approved_product_deletion_is_archived_after_admin_approval(
    subject_product_context,
) -> None:
    client, _ = subject_product_context
    product, subject_headers, admin_headers = create_approved_product(
        client,
        "OCOP-LD-DELETE",
    )

    requested = client.post(
        f"/api/v1/subject/products/{product['id']}/deletion-requests",
        headers=subject_headers,
        json={"reason": "Sản phẩm đã ngừng kinh doanh."},
    )
    still_public = client.get(f"/api/v1/products/{product['slug']}")
    approved = client.patch(
        f"/api/v1/admin/product-change-requests/{requested.json()['id']}/moderation",
        headers=admin_headers,
        json={"status": "approved", "note": "Đã xác nhận ngừng kinh doanh."},
    )
    hidden = client.get(f"/api/v1/products/{product['slug']}")

    assert requested.status_code == 201
    assert still_public.status_code == 200
    assert approved.status_code == 200
    assert hidden.status_code == 404


def test_product_allows_only_one_active_change_request(subject_product_context) -> None:
    client, _ = subject_product_context
    product, subject_headers, _ = create_approved_product(
        client,
        "OCOP-LD-ONE-REQUEST",
    )

    first = client.post(
        f"/api/v1/subject/products/{product['id']}/deletion-requests",
        headers=subject_headers,
        json={"reason": "Đề nghị ngừng kinh doanh sản phẩm."},
    )
    duplicate = client.post(
        f"/api/v1/subject/products/{product['id']}/deletion-requests",
        headers=subject_headers,
        json={"reason": "Gửi thêm một yêu cầu trùng lặp."},
    )

    assert first.status_code == 201
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "ACTIVE_PRODUCT_CHANGE_REQUEST_EXISTS"


def test_subject_cannot_read_product_owned_by_another_subject(subject_product_context) -> None:
    client, _ = subject_product_context
    created = client.post(
        "/api/v1/subject/products",
        headers=auth_header(1, "subject"),
        json=product_payload(),
    )

    response = client.get(
        f"/api/v1/subject/products/{created.json()['id']}",
        headers=auth_header(2, "subject"),
    )

    assert response.status_code == 404
    assert response.json()["code"] == "PRODUCT_NOT_FOUND"


def test_regular_user_cannot_manage_subject_products(subject_product_context) -> None:
    client, _ = subject_product_context
    response = client.get(
        "/api/v1/subject/products",
        headers=auth_header(3, "user"),
    )

    assert response.status_code == 403
    assert response.json()["code"] == "INSUFFICIENT_PERMISSIONS"


def test_product_requires_exactly_one_primary_image(subject_product_context) -> None:
    client, _ = subject_product_context
    payload = product_payload()
    payload["images"][0]["is_primary"] = False

    response = client.post(
        "/api/v1/subject/products",
        headers=auth_header(1, "subject"),
        json=payload,
    )

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"
