from collections.abc import Generator
from datetime import date, timedelta

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import app
from app.models.category import Category
from app.models.data_source import DataSource, ProductSource
from app.models.product import Product
from app.models.role import Role
from app.models.subject import Subject
from app.models.user import User
from app.api.routes import subject_product_certificates, subject_product_images
from app.schemas.product_management import ProductImagePayload
from app.services.product_workflow import get_change_request, get_product_for_admin


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


def test_postgresql_row_locks_target_only_the_workflow_table() -> None:
    class CapturingSession:
        statements = []

        def scalar(self, statement):
            self.statements.append(statement)
            return None

    session = CapturingSession()
    with pytest.raises(HTTPException):
        get_product_for_admin(session, 10, lock=True)
    with pytest.raises(HTTPException):
        get_change_request(session, 20, lock=True)

    product_sql = str(session.statements[0].compile(dialect=postgresql.dialect()))
    request_sql = str(session.statements[1].compile(dialect=postgresql.dialect()))
    assert "FOR UPDATE OF ocop_products" in product_sql
    assert "FOR UPDATE OF product_change_requests" in request_sql


def test_product_image_accepts_legacy_local_asset_url() -> None:
    image = ProductImagePayload(
        image_url="/assets/demo/products/public-reference.svg",
        is_primary=True,
        sort_order=0,
    )
    assert image.image_url == "/assets/demo/products/public-reference.svg"


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


def test_subject_saves_incomplete_draft_but_cannot_submit(subject_product_context) -> None:
    client, _ = subject_product_context
    headers = auth_header(1, "subject")
    created = client.post(
        "/api/v1/subject/products",
        headers=headers,
        json={"category_id": 1, "name": "Bản nháp trà atiso"},
    )

    assert created.status_code == 201
    assert created.json()["status"] == "draft"
    assert created.json()["star"] is None
    assert created.json()["description"] is None

    patched = client.patch(
        f"/api/v1/subject/products/{created.json()['id']}",
        headers=headers,
        json={"description": "Mô tả sản phẩm đang được hoàn thiện."},
    )
    submitted = client.post(
        f"/api/v1/subject/products/{created.json()['id']}/submit",
        headers=headers,
    )

    assert patched.status_code == 200
    assert submitted.status_code == 422
    assert submitted.json()["code"] == "PRODUCT_SUBMISSION_INCOMPLETE"
    assert "certificate_document" in submitted.json()["details"]["missing_fields"]
    assert "primary_image" in submitted.json()["details"]["missing_fields"]


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
    assert approved.json()["reviewed_by_name"] == "Quản trị viên"
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


def test_admin_can_view_official_product_evidence(subject_product_context) -> None:
    client, testing_session = subject_product_context
    created = client.post(
        "/api/v1/subject/products",
        headers=auth_header(1, "subject"),
        json=product_payload("OCOP-LD-EVIDENCE-A"),
    )
    product_id = created.json()["id"]

    with testing_session() as session:
        source = DataSource(
            title="Quyết định công nhận sản phẩm OCOP",
            document_number="3981/QĐ-UBND",
            issuing_body="UBND tỉnh Lâm Đồng",
            source_type="official_decision",
            published_at=date.today(),
            source_url="https://example.com/sources/decision-3981.pdf",
            retrieved_at=date.today(),
        )
        session.add(source)
        session.flush()
        session.add(
            ProductSource(
                product_id=product_id,
                source_id=source.id,
                evidence_role="recognition",
                verification_level="A",
                original_address="Lâm Đồng",
                verified_at=date.today(),
            )
        )
        session.commit()

    evidence = client.get(
        f"/api/v1/admin/products/{product_id}/evidence",
        headers=auth_header(4, "admin"),
    )
    filtered = client.get(
        "/api/v1/admin/products",
        headers=auth_header(4, "admin"),
        params={
            "verification_level": "A",
            "verification_status": "verified_official_decision",
            "missing_decision": False,
        },
    )

    assert evidence.status_code == 200
    assert evidence.json()["verification_level"] == "A"
    assert evidence.json()["verification_status"] == "verified_official_decision"
    assert evidence.json()["issues"] == []
    assert evidence.json()["sources"][0]["source"]["document_number"] == "3981/QĐ-UBND"
    assert filtered.status_code == 200
    assert [item["id"] for item in filtered.json()["items"]] == [product_id]


def test_admin_filters_products_with_incomplete_evidence(subject_product_context) -> None:
    client, testing_session = subject_product_context
    payload = product_payload("OCOP-LD-EVIDENCE-B1")
    payload["name"] = "Trà atiso cần bổ sung hồ sơ"
    created = client.post(
        "/api/v1/subject/products",
        headers=auth_header(1, "subject"),
        json=payload,
    )
    product_id = created.json()["id"]

    with testing_session() as session:
        product = session.get(Product, product_id)
        product.cert_issued_at = None
        source = DataSource(
            title="Bài viết cơ quan nhà nước xác nhận trao chứng nhận",
            issuing_body="Báo Lâm Đồng",
            source_type="government_news",
            published_at=date.today(),
            source_url="https://example.com/sources/government-news.html",
            retrieved_at=date.today(),
        )
        session.add(source)
        session.flush()
        session.add(
            ProductSource(
                product_id=product_id,
                source_id=source.id,
                evidence_role="recognition",
                verification_level="B1",
                verified_at=date.today(),
                notes="Chưa tìm thấy phụ lục quyết định.",
            )
        )
        session.commit()

    filtered = client.get(
        "/api/v1/admin/products",
        headers=auth_header(4, "admin"),
        params={
            "verification_status": "verified_government_source",
            "missing_decision": True,
            "missing_issued_at": True,
        },
    )

    assert filtered.status_code == 200
    assert filtered.json()["total"] == 1
    item = filtered.json()["items"][0]
    assert item["id"] == product_id
    assert item["verification_level"] == "B1"
    assert item["missing_decision"] is True
    assert item["missing_issued_at"] is True


def test_admin_manages_data_source_and_product_link(subject_product_context) -> None:
    client, _ = subject_product_context
    admin_headers = auth_header(4, "admin")
    created_product = client.post(
        "/api/v1/subject/products",
        headers=auth_header(1, "subject"),
        json=product_payload("OCOP-LD-MANAGED-SOURCE"),
    )
    product_id = created_product.json()["id"]
    source_payload = {
        "title": "Quyết định công nhận đợt kiểm thử",
        "document_number": "100/QĐ-UBND",
        "issuing_body": "UBND tỉnh Lâm Đồng",
        "source_type": "recognition_decision",
        "published_at": date.today().isoformat(),
        "source_url": "https://example.com/sources/managed-source.pdf",
        "retrieved_at": date.today().isoformat(),
    }

    created_source = client.post(
        "/api/v1/admin/data-sources",
        headers=admin_headers,
        json=source_payload,
    )
    assert created_source.status_code == 201
    source_id = created_source.json()["id"]

    source_payload["title"] = "Quyết định công nhận đã cập nhật"
    updated_source = client.patch(
        f"/api/v1/admin/data-sources/{source_id}",
        headers=admin_headers,
        json=source_payload,
    )
    assert updated_source.status_code == 200
    assert updated_source.json()["title"] == source_payload["title"]

    linked = client.post(
        f"/api/v1/admin/products/{product_id}/evidence",
        headers=admin_headers,
        json={
            "source_id": source_id,
            "evidence_role": "recognition",
            "verification_level": "A",
            "verified_at": date.today().isoformat(),
            "original_address": "Đà Lạt, Lâm Đồng",
            "notes": "Đã đối chiếu phụ lục.",
        },
    )
    assert linked.status_code == 201
    assert linked.json()["verification_status"] == "verified_official_decision"
    assert linked.json()["sources"][0]["source"]["id"] == source_id

    updated_link = client.patch(
        f"/api/v1/admin/products/{product_id}/evidence/{source_id}/recognition",
        headers=admin_headers,
        json={
            "verification_level": "B1",
            "verified_at": date.today().isoformat(),
            "original_address": None,
            "notes": "Cần đối chiếu lại bản ký.",
        },
    )
    assert updated_link.status_code == 200
    assert updated_link.json()["verification_level"] == "B1"
    assert updated_link.json()["sources"][0]["notes"] == "Cần đối chiếu lại bản ký."

    unlinked = client.delete(
        f"/api/v1/admin/products/{product_id}/evidence/{source_id}/recognition",
        headers=admin_headers,
    )
    assert unlinked.status_code == 204
    evidence = client.get(
        f"/api/v1/admin/products/{product_id}/evidence",
        headers=admin_headers,
    )
    assert evidence.json()["evidence_count"] == 0


def test_subject_cannot_manage_data_sources(subject_product_context) -> None:
    client, _ = subject_product_context
    response = client.get(
        "/api/v1/admin/data-sources",
        headers=auth_header(1, "subject"),
    )
    assert response.status_code == 403


def test_admin_dashboard_uses_database_counts(subject_product_context) -> None:
    client, _ = subject_product_context
    created = client.post(
        "/api/v1/subject/products",
        headers=auth_header(1, "subject"),
        json=product_payload("OCOP-LD-DASHBOARD"),
    )
    client.post(
        f"/api/v1/subject/products/{created.json()['id']}/submit",
        headers=auth_header(1, "subject"),
    )

    dashboard = client.get(
        "/api/v1/admin/dashboard",
        headers=auth_header(4, "admin"),
    )
    forbidden = client.get(
        "/api/v1/admin/dashboard",
        headers=auth_header(1, "subject"),
    )

    assert dashboard.status_code == 200
    assert dashboard.json()["total_products"] == 1
    assert dashboard.json()["pending_products"] == 1
    assert dashboard.json()["approved_products"] == 0
    assert dashboard.json()["products_missing_decision"] == 1
    assert forbidden.status_code == 403


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
    assert requested.json()["current_data"]["name"] == "Cà phê Arabica Cầu Đất"
    assert requested.json()["current_data"]["price"] == "180000.00"
    assert requested.json()["proposed_data"]["price"] == "195000"
    assert public_before.json()["name"] == "Cà phê Arabica Cầu Đất"
    assert moderated.status_code == 200
    assert moderated.json()["status"] == "approved"
    assert moderated.json()["reviewed_by_name"] == "Quản trị viên"
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


def test_subject_uploads_and_links_local_product_image(
    subject_product_context,
    tmp_path,
    monkeypatch,
) -> None:
    client, _ = subject_product_context
    monkeypatch.setattr(subject_product_images.settings, "upload_directory", tmp_path)
    png_content = b"\x89PNG\r\n\x1a\n" + b"test-image"

    uploaded = client.post(
        "/api/v1/subject/product-images",
        headers=auth_header(1, "subject"),
        files={"file": ("product.png", png_content, "image/png")},
    )

    assert uploaded.status_code == 201
    uploaded_data = uploaded.json()
    assert uploaded_data["storage_path"].startswith("products/1/")
    stored_file = tmp_path / uploaded_data["storage_path"]
    assert stored_file.read_bytes() == png_content

    payload = product_payload("OCOP-LD-UPLOAD")
    payload["images"] = [
        {
            "image_url": uploaded_data["image_url"],
            "storage_path": uploaded_data["storage_path"],
            "is_primary": True,
            "sort_order": 0,
        }
    ]
    created = client.post(
        "/api/v1/subject/products",
        headers=auth_header(1, "subject"),
        json=payload,
    )
    assert created.status_code == 201
    assert created.json()["images"][0]["storage_path"] == uploaded_data["storage_path"]

    file_name = uploaded_data["storage_path"].rsplit("/", 1)[1]
    cannot_delete_linked = client.delete(
        f"/api/v1/subject/product-images/{file_name}",
        headers=auth_header(1, "subject"),
    )
    cannot_delete_other_owner = client.delete(
        f"/api/v1/subject/product-images/{file_name}",
        headers=auth_header(2, "subject"),
    )
    assert cannot_delete_linked.status_code == 409
    assert cannot_delete_other_owner.status_code == 404


def test_product_image_upload_validates_role_type_content_and_size(
    subject_product_context,
    tmp_path,
    monkeypatch,
) -> None:
    client, _ = subject_product_context
    monkeypatch.setattr(subject_product_images.settings, "upload_directory", tmp_path)
    headers = auth_header(1, "subject")

    invalid_type = client.post(
        "/api/v1/subject/product-images",
        headers=headers,
        files={"file": ("notes.txt", b"not-an-image", "text/plain")},
    )
    invalid_content = client.post(
        "/api/v1/subject/product-images",
        headers=headers,
        files={"file": ("fake.png", b"not-a-png", "image/png")},
    )
    oversized = client.post(
        "/api/v1/subject/product-images",
        headers=headers,
        files={
            "file": (
                "large.png",
                b"\x89PNG\r\n\x1a\n" + b"0" * (5 * 1024 * 1024),
                "image/png",
            )
        },
    )
    forbidden = client.post(
        "/api/v1/subject/product-images",
        headers=auth_header(3, "user"),
        files={"file": ("product.png", b"\x89PNG\r\n\x1a\n", "image/png")},
    )

    assert invalid_type.status_code == 422
    assert invalid_type.json()["code"] == "INVALID_IMAGE_TYPE"
    assert invalid_content.status_code == 422
    assert invalid_content.json()["code"] == "INVALID_IMAGE_CONTENT"
    assert oversized.status_code == 413
    assert oversized.json()["code"] == "IMAGE_TOO_LARGE"
    assert forbidden.status_code == 403


def test_subject_uploads_private_certificate_for_admin_review(
    subject_product_context,
    tmp_path,
    monkeypatch,
) -> None:
    client, _ = subject_product_context
    monkeypatch.setattr(subject_product_certificates.settings, "upload_directory", tmp_path)
    pdf_content = b"%PDF-1.7\ncertificate"

    uploaded = client.post(
        "/api/v1/subject/product-certificates",
        headers=auth_header(1, "subject"),
        files={"file": ("chung-nhan.pdf", pdf_content, "application/pdf")},
    )
    assert uploaded.status_code == 201
    storage_path = uploaded.json()["storage_path"]
    assert storage_path.startswith("certificates/1/")

    payload = product_payload("OCOP-LD-CERTIFICATE-UPLOAD")
    payload["certificate_url"] = None
    payload["certificate_storage_path"] = storage_path
    created = client.post(
        "/api/v1/subject/products",
        headers=auth_header(1, "subject"),
        json=payload,
    )
    assert created.status_code == 201

    product_id = created.json()["id"]
    owner_download = client.get(
        f"/api/v1/subject/product-certificates/products/{product_id}",
        headers=auth_header(1, "subject"),
    )
    admin_download = client.get(
        f"/api/v1/admin/products/{product_id}/certificate",
        headers=auth_header(4, "admin"),
    )
    other_subject = client.get(
        f"/api/v1/subject/product-certificates/products/{product_id}",
        headers=auth_header(2, "subject"),
    )
    public_download = client.get(f"/uploads/{storage_path}")

    assert owner_download.status_code == 200
    assert owner_download.content == pdf_content
    assert admin_download.status_code == 200
    assert other_subject.status_code == 404
    assert public_download.status_code == 404


def test_certificate_upload_validates_type_content_size_and_role(
    subject_product_context,
    tmp_path,
    monkeypatch,
) -> None:
    client, _ = subject_product_context
    monkeypatch.setattr(subject_product_certificates.settings, "upload_directory", tmp_path)
    monkeypatch.setattr(subject_product_certificates.settings, "certificate_upload_max_bytes", 20)
    headers = auth_header(1, "subject")

    invalid_type = client.post(
        "/api/v1/subject/product-certificates",
        headers=headers,
        files={"file": ("notes.txt", b"plain text", "text/plain")},
    )
    invalid_content = client.post(
        "/api/v1/subject/product-certificates",
        headers=headers,
        files={"file": ("fake.pdf", b"not a pdf", "application/pdf")},
    )
    oversized = client.post(
        "/api/v1/subject/product-certificates",
        headers=headers,
        files={"file": ("large.pdf", b"%PDF-" + b"0" * 20, "application/pdf")},
    )
    forbidden = client.post(
        "/api/v1/subject/product-certificates",
        headers=auth_header(3, "user"),
        files={"file": ("certificate.pdf", b"%PDF-1.7", "application/pdf")},
    )

    assert invalid_type.status_code == 422
    assert invalid_type.json()["code"] == "INVALID_CERTIFICATE_TYPE"
    assert invalid_content.status_code == 422
    assert invalid_content.json()["code"] == "INVALID_CERTIFICATE_CONTENT"
    assert oversized.status_code == 413
    assert oversized.json()["code"] == "CERTIFICATE_TOO_LARGE"
    assert forbidden.status_code == 403
