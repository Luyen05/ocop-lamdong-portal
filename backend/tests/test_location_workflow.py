"""Chủ thể khai báo điểm du lịch, admin kiểm duyệt và yêu cầu thay đổi điểm đã duyệt."""

from collections.abc import Generator
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, update
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.core.database import Base, get_db
from app.core.geometry import GeoPoint, haversine_meters, register_sqlite_geo_functions
from app.core.security import create_access_token
from app.main import app
from app.models.category import Category
from app.models.location import TourismLocation
from app.models.product import Product
from app.models.role import Role
from app.models.subject import Subject
from app.models.user import User
from app.services.location_workflow import parse_coordinate_text


# Điểm mẫu trong thiết kế: Vườn dâu Langbiang Demo, cách Vườn dâu tây Cô Liên khoảng 10 km.
DEMO_POINT = {"latitude": 12.047, "longitude": 108.441}
CO_LIEN = GeoPoint(longitude=108.4417, latitude=11.9500)
PNG = b"\x89PNG\r\n\x1a\n" + b"location-image"
DESCRIPTION = "Vườn dâu tây trồng trong nhà kính, du khách được tự tay hái dâu và thưởng thức tại vườn."


@pytest.fixture
def workflow_context(tmp_path, monkeypatch) -> Generator[tuple[TestClient, sessionmaker], None, None]:
    monkeypatch.setattr(get_settings(), "upload_directory", tmp_path)
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    event.listen(engine, "connect", register_sqlite_geo_functions)
    testing_session = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
    Base.metadata.create_all(engine)
    with testing_session() as session:
        session.add_all(
            [
                Role(id=1, name="admin", description="Quản trị"),
                Role(id=2, name="subject", description="Chủ thể"),
                Role(id=3, name="user", description="Người dùng"),
                Category(id=1, name="Nông sản", slug="nong-san"),
            ]
        )
        session.flush()
        session.add_all(
            [
                User(id=1, role_id=2, email="s1@example.com", hashed_password="x", full_name="Chủ thể 1", is_active=True),
                User(id=2, role_id=2, email="s2@example.com", hashed_password="x", full_name="Chủ thể 2", is_active=True),
                User(id=3, role_id=3, email="u@example.com", hashed_password="x", full_name="Người dùng", is_active=True),
                User(id=4, role_id=1, email="a@example.com", hashed_password="x", full_name="Quản trị viên", is_active=True),
                User(id=5, role_id=2, email="s3@example.com", hashed_password="x", full_name="Chờ duyệt", is_active=True),
            ]
        )
        session.flush()
        # Giống ràng buộc ck_subjects_review_state trên PostgreSQL: hồ sơ đã duyệt có người duyệt.
        approved = {"status": "approved", "reviewed_by": 4, "reviewed_at": datetime.now(timezone.utc)}
        subject_values = {
            "type": "cooperative",
            "representative": "Nguyễn Văn A",
            "address": "Lạc Dương",
            "district": "Lạc Dương",
        }
        session.add_all(
            [
                Subject(id=1, user_id=1, name="HTX Langbiang", phone="0901000002", **approved, **subject_values),
                Subject(id=2, user_id=2, name="HTX Khác", phone="0901000003", **approved, **subject_values),
                Subject(id=3, user_id=5, name="HTX Chờ", phone="0901000004", status="pending", **subject_values),
            ]
        )
        session.flush()
        product_values = {
            "category_id": 1,
            "star": 4,
            "cert_year": 2025,
            "cert_issued_at": date(2025, 1, 1),
            "cert_expires_at": date(2099, 1, 1),
            "issuing_authority": "UBND tỉnh Lâm Đồng",
            "description": "Sản phẩm OCOP của đơn vị.",
        }
        session.add_all(
            [
                Product(id=1, subject_id=1, name="Hồng treo gió", slug="hong-treo-gio", cert_code="C1", status="approved", **product_values),
                Product(id=2, subject_id=1, name="Mứt dâu", slug="mut-dau", cert_code="C2", status="pending", **product_values),
                Product(id=3, subject_id=2, name="Cà phê", slug="ca-phe", cert_code="C3", status="approved", **product_values),
                TourismLocation(
                    id=1,
                    name="Vườn dâu tây Cô Liên",
                    slug="vuon-dau-tay-co-lien",
                    type="fruit_garden",
                    district="Đà Lạt",
                    address="Phường 12, Đà Lạt",
                    geom=CO_LIEN,
                    services=[],
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


def auth(user_id: int, role: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user_id=user_id, role=role)}"}


SUBJECT = auth(1, "subject")
OTHER_SUBJECT = auth(2, "subject")
ADMIN = auth(4, "admin")


def upload_image(client: TestClient, headers: dict[str, str] = SUBJECT) -> dict:
    response = client.post(
        "/api/v1/subject/location-images",
        headers=headers,
        files={"file": ("vuon.png", PNG, "image/png")},
    )
    assert response.status_code == 201, response.text
    return response.json()


def complete_fields(image: dict, **overrides) -> dict:
    values = {
        "name": "Vườn dâu Langbiang Demo",
        "type": "fruit_garden",
        **DEMO_POINT,
        "location_source": "map_pin",
        "district": "Phường Lang Biang - Đà Lạt",
        "address": "Thôn Đan Kia, Phường Lang Biang - Đà Lạt",
        "description": DESCRIPTION,
        "opening_hours": "07:00 - 17:00",
        "ticket_price": "50000",
        "services": ["Tham quan vườn", "Tự tay thu hoạch", "tham quan vườn"],
        "contact_phone": "0901000002",
        "images": [{"image_url": image["image_url"], "storage_path": image["storage_path"], "is_primary": True}],
        "product_ids": [1],
    }
    values.update(overrides)
    return values


def create_draft(client: TestClient, **fields) -> dict:
    response = client.post(
        "/api/v1/subject/locations",
        headers=SUBJECT,
        json={"name": "Vườn dâu Langbiang Demo", "type": "fruit_garden", **fields},
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_pending(client: TestClient, **overrides) -> dict:
    draft = create_draft(client, **complete_fields(upload_image(client), **overrides))
    submitted = client.post(f"/api/v1/subject/locations/{draft['id']}/submit", headers=SUBJECT)
    assert submitted.status_code == 200, submitted.text
    return submitted.json()


def create_approved(client: TestClient, **overrides) -> dict:
    pending = create_pending(client, **overrides)
    approved = client.patch(
        f"/api/v1/admin/locations/{pending['id']}/moderation",
        headers=ADMIN,
        json={"status": "approved"},
    )
    assert approved.status_code == 200, approved.text
    return approved.json()


def test_location_endpoints_require_approved_subject(workflow_context) -> None:
    client, _ = workflow_context
    body = {"name": "Vườn thử", "type": "fruit_garden"}

    assert client.post("/api/v1/subject/locations", json=body).status_code == 401
    assert client.post("/api/v1/subject/locations", headers=auth(3, "user"), json=body).status_code == 403
    pending_subject = client.post("/api/v1/subject/locations", headers=auth(5, "subject"), json=body)
    assert pending_subject.status_code == 403
    assert pending_subject.json()["code"] == "APPROVED_SUBJECT_REQUIRED"
    assert client.get("/api/v1/admin/locations", headers=SUBJECT).status_code == 403


def test_subject_saves_draft_step_by_step(workflow_context) -> None:
    client, _ = workflow_context

    draft = create_draft(client)
    assert draft["status"] == "draft"
    assert draft["slug"] == "vuon-dau-langbiang-demo"
    assert draft["latitude"] is None
    assert draft["location_source"] is None
    assert draft["position_check"] is None

    with_position = client.patch(
        f"/api/v1/subject/locations/{draft['id']}",
        headers=SUBJECT,
        json={**DEMO_POINT, "location_source": "device_gps", "location_accuracy_m": 15},
    )
    assert with_position.status_code == 200, with_position.text
    data = with_position.json()
    assert (data["latitude"], data["longitude"]) == (12.047, 108.441)
    assert data["location_source"] == "device_gps"
    assert data["location_accuracy_m"] == 15
    check = data["position_check"]
    assert check["inside_lam_dong"] is True
    assert check["nearest"]["slug"] == "vuon-dau-tay-co-lien"
    assert 10_000 < check["nearest"]["distance_m"] < 11_000
    assert check["duplicate_warning"] is False

    # Đổi sang ghim bản đồ thì độ chính xác GPS không còn ý nghĩa.
    moved = client.patch(
        f"/api/v1/subject/locations/{draft['id']}",
        headers=SUBJECT,
        json={"latitude": 12.0471, "longitude": 108.4411, "location_source": "map_pin"},
    )
    assert moved.json()["location_accuracy_m"] is None

    listed = client.get("/api/v1/subject/locations", headers=SUBJECT)
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["status_counts"] == {"draft": 1}


@pytest.mark.parametrize(
    "body",
    [
        {"latitude": 12.0},
        {"latitude": 12.0, "longitude": 108.4},
        {**DEMO_POINT, "location_source": "map_pin", "location_accuracy_m": 10},
        {"services": ["x" * 61]},
        {"contact_phone": "abc"},
        {"name": None},
        {"images": [{"image_url": "https://example.com/a.jpg"}]},
    ],
)
def test_draft_update_rejects_invalid_fields(workflow_context, body) -> None:
    client, _ = workflow_context
    draft = create_draft(client)

    response = client.patch(f"/api/v1/subject/locations/{draft['id']}", headers=SUBJECT, json=body)

    assert response.status_code == 422


def test_submission_lists_missing_fields(workflow_context) -> None:
    client, _ = workflow_context
    draft = create_draft(client, description="Quá ngắn")

    response = client.post(f"/api/v1/subject/locations/{draft['id']}/submit", headers=SUBJECT)

    assert response.status_code == 422
    assert response.json()["code"] == "LOCATION_SUBMISSION_INCOMPLETE"
    assert response.json()["details"]["missing_fields"] == [
        "position",
        "district",
        "address",
        "description",
        "primary_image",
    ]


def test_submission_blocks_position_outside_lam_dong(workflow_context) -> None:
    client, _ = workflow_context
    # Nhầm thứ tự vĩ độ/kinh độ kiểu Hà Nội: tọa độ hợp lệ nhưng ngoài tỉnh.
    draft = create_draft(client, **complete_fields(upload_image(client), latitude=21.0285, longitude=105.8542))
    assert draft["position_check"]["inside_lam_dong"] is False

    response = client.post(f"/api/v1/subject/locations/{draft['id']}/submit", headers=SUBJECT)

    assert response.status_code == 422
    assert response.json()["code"] == "LOCATION_OUTSIDE_LAM_DONG"


def test_full_moderation_flow_with_revision_and_pin_adjustment(workflow_context) -> None:
    client, _ = workflow_context
    pending = create_pending(client)
    assert pending["status"] == "pending"
    assert pending["submitted_at"] is not None
    assert pending["services"] == ["Tham quan vườn", "Tự tay thu hoạch"]
    assert [product["id"] for product in pending["products"]] == [1]

    locked = client.patch(f"/api/v1/subject/locations/{pending['id']}", headers=SUBJECT, json={"opening_hours": "8h"})
    assert locked.status_code == 409
    assert locked.json()["code"] == "LOCATION_NOT_EDITABLE"
    assert client.delete(f"/api/v1/subject/locations/{pending['id']}", headers=SUBJECT).status_code == 409

    queue = client.get("/api/v1/admin/locations", headers=ADMIN)
    assert queue.status_code == 200
    items = queue.json()["items"]
    assert items[0]["id"] == pending["id"]
    assert items[0]["position_check"]["inside_lam_dong"] is True
    assert items[0]["subject"]["name"] == "HTX Langbiang"
    assert queue.json()["status_counts"] == {"approved": 1, "pending": 1}
    assert client.get("/api/v1/admin/locations?origin=subject", headers=ADMIN).json()["total"] == 1
    assert client.get("/api/v1/admin/locations?origin=import", headers=ADMIN).json()["total"] == 1

    dashboard = client.get("/api/v1/admin/dashboard", headers=ADMIN).json()
    assert dashboard["pending_locations"] == 1

    missing_note = client.patch(
        f"/api/v1/admin/locations/{pending['id']}/moderation",
        headers=ADMIN,
        json={"status": "needs_revision"},
    )
    assert missing_note.status_code == 422
    revision = client.patch(
        f"/api/v1/admin/locations/{pending['id']}/moderation",
        headers=ADMIN,
        json={"status": "needs_revision", "note": "Bổ sung ảnh cổng vào."},
    )
    assert revision.status_code == 200
    assert revision.json()["status"] == "needs_revision"
    assert revision.json()["reviewed_by_name"] == "Quản trị viên"

    edited = client.patch(
        f"/api/v1/subject/locations/{pending['id']}",
        headers=SUBJECT,
        json={"opening_hours": "07:30 - 17:00"},
    )
    assert edited.status_code == 200
    resubmitted = client.post(f"/api/v1/subject/locations/{pending['id']}/submit", headers=SUBJECT)
    assert resubmitted.json()["status"] == "pending"
    assert resubmitted.json()["review_note"] is None
    assert resubmitted.json()["reviewed_by_name"] is None

    approved = client.patch(
        f"/api/v1/admin/locations/{pending['id']}/moderation",
        headers=ADMIN,
        json={"status": "approved", "latitude": 12.0468, "longitude": 108.4415},
    )
    assert approved.status_code == 200, approved.text
    data = approved.json()
    assert data["status"] == "approved"
    assert data["version"] == 2
    assert (data["latitude"], data["longitude"]) == (12.0468, 108.4415)
    assert "12.047000, 108.441000" in data["review_note"]
    assert "12.046800, 108.441500" in data["review_note"]

    public = client.get(f"/api/v1/locations/{data['slug']}")
    assert public.status_code == 200
    assert public.json()["address"] == "Thôn Đan Kia, Phường Lang Biang - Đà Lạt"
    features = client.get("/api/v1/map/locations").json()["features"]
    assert data["slug"] in {feature["properties"]["slug"] for feature in features}

    again = client.patch(
        f"/api/v1/admin/locations/{pending['id']}/moderation",
        headers=ADMIN,
        json={"status": "approved"},
    )
    assert again.status_code == 409


def test_rejected_location_is_final_but_deletable(workflow_context) -> None:
    client, _ = workflow_context
    pending = create_pending(client)
    rejected = client.patch(
        f"/api/v1/admin/locations/{pending['id']}/moderation",
        headers=ADMIN,
        json={"status": "rejected", "note": "Không phải điểm du lịch nông nghiệp."},
    )
    assert rejected.json()["status"] == "rejected"

    assert client.patch(f"/api/v1/subject/locations/{pending['id']}", headers=SUBJECT, json={"opening_hours": "8h"}).status_code == 409
    assert client.post(f"/api/v1/subject/locations/{pending['id']}/submit", headers=SUBJECT).status_code == 409
    assert client.delete(f"/api/v1/subject/locations/{pending['id']}", headers=SUBJECT).status_code == 204
    assert client.get(f"/api/v1/subject/locations/{pending['id']}", headers=SUBJECT).status_code == 404


def test_admin_cannot_approve_when_subject_account_is_locked(workflow_context) -> None:
    client, testing_session = workflow_context
    pending = create_pending(client)
    with testing_session() as session:
        session.execute(update(User).where(User.id == 1).values(is_active=False))
        session.commit()

    response = client.patch(
        f"/api/v1/admin/locations/{pending['id']}/moderation",
        headers=ADMIN,
        json={"status": "approved"},
    )

    assert response.status_code == 409
    assert response.json()["code"] == "LOCATION_SUBJECT_INACTIVE"


def test_admin_pin_adjustment_must_stay_in_lam_dong(workflow_context) -> None:
    client, _ = workflow_context
    pending = create_pending(client)

    response = client.patch(
        f"/api/v1/admin/locations/{pending['id']}/moderation",
        headers=ADMIN,
        json={"status": "approved", "latitude": 10.77, "longitude": 106.70},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "LOCATION_OUTSIDE_LAM_DONG"


def test_duplicate_warning_within_200_meters(workflow_context) -> None:
    client, _ = workflow_context
    near = {"latitude": CO_LIEN.latitude + 0.001, "longitude": CO_LIEN.longitude}
    expected = haversine_meters(CO_LIEN, GeoPoint(longitude=near["longitude"], latitude=near["latitude"]))

    check = client.get("/api/v1/subject/locations/position-check", headers=SUBJECT, params=near)

    assert check.status_code == 200
    assert check.json()["duplicate_warning"] is True
    # SQLite dùng Haversine, PostGIS tính trên elipxoit: lệch nhau dưới 1%.
    assert check.json()["nearest"]["distance_m"] == pytest.approx(expected, rel=0.01)
    # Chỉ cảnh báo: vẫn gửi duyệt được để admin quyết định.
    pending = create_pending(client, **near)
    assert pending["position_check"]["duplicate_warning"] is True


def test_subject_cannot_touch_other_or_imported_locations(workflow_context) -> None:
    client, _ = workflow_context
    draft = create_draft(client)

    assert client.get(f"/api/v1/subject/locations/{draft['id']}", headers=OTHER_SUBJECT).status_code == 404
    assert client.patch(f"/api/v1/subject/locations/{draft['id']}", headers=OTHER_SUBJECT, json={"opening_hours": "8h"}).status_code == 404
    assert client.delete(f"/api/v1/subject/locations/{draft['id']}", headers=OTHER_SUBJECT).status_code == 404
    assert client.get("/api/v1/subject/locations/1", headers=SUBJECT).status_code == 404
    assert client.get("/api/v1/subject/locations", headers=OTHER_SUBJECT).json()["total"] == 0
    # Admin không thấy bản nháp trong hàng chờ.
    assert client.get("/api/v1/admin/locations?status=pending", headers=ADMIN).json()["total"] == 0


def test_only_own_approved_products_and_images_can_be_linked(workflow_context) -> None:
    client, _ = workflow_context
    draft = create_draft(client)

    for product_ids in ([2], [3], [999]):
        response = client.patch(
            f"/api/v1/subject/locations/{draft['id']}",
            headers=SUBJECT,
            json={"product_ids": product_ids},
        )
        assert response.status_code == 422
        assert response.json()["code"] == "LOCATION_PRODUCT_INVALID"

    other_image = upload_image(client, OTHER_SUBJECT)
    stolen = client.patch(
        f"/api/v1/subject/locations/{draft['id']}",
        headers=SUBJECT,
        json={"images": [{"image_url": other_image["image_url"], "storage_path": other_image["storage_path"], "is_primary": True}]},
    )
    assert stolen.status_code == 403
    assert stolen.json()["code"] == "LOCATION_IMAGE_NOT_OWNED"


def test_location_images_upload_replace_and_delete(workflow_context, tmp_path) -> None:
    client, _ = workflow_context
    first = upload_image(client)
    second = upload_image(client)
    assert first["storage_path"].startswith("locations/1/")
    assert (tmp_path / first["storage_path"]).read_bytes() == PNG
    assert "/uploads/locations/1/" in first["image_url"]

    draft = create_draft(
        client,
        images=[{"image_url": first["image_url"], "storage_path": first["storage_path"], "is_primary": True}],
    )
    replaced = client.patch(
        f"/api/v1/subject/locations/{draft['id']}",
        headers=SUBJECT,
        json={
            "images": [
                {"image_url": second["image_url"], "storage_path": second["storage_path"], "is_primary": True},
                {"image_url": first["image_url"], "storage_path": first["storage_path"], "sort_order": 1},
            ]
        },
    )
    assert replaced.status_code == 200, replaced.text
    assert [image["storage_path"] for image in replaced.json()["images"]] == [
        second["storage_path"],
        first["storage_path"],
    ]
    assert replaced.json()["images"][0]["alt_text"] == "Vườn dâu Langbiang Demo"

    file_name = first["storage_path"].rsplit("/", 1)[1]
    in_use = client.delete(f"/api/v1/subject/location-images/{file_name}", headers=SUBJECT)
    assert in_use.status_code == 409
    assert in_use.json()["code"] == "LOCATION_IMAGE_IN_USE"
    assert client.delete(f"/api/v1/subject/location-images/{file_name}", headers=OTHER_SUBJECT).status_code == 404

    unused = upload_image(client)
    unused_name = unused["storage_path"].rsplit("/", 1)[1]
    assert client.delete(f"/api/v1/subject/location-images/{unused_name}", headers=SUBJECT).status_code == 204
    assert not (tmp_path / unused["storage_path"]).exists()

    fake = client.post(
        "/api/v1/subject/location-images",
        headers=SUBJECT,
        files={"file": ("fake.png", b"not-a-png", "image/png")},
    )
    assert fake.json()["code"] == "INVALID_IMAGE_CONTENT"


def test_update_request_keeps_public_version_until_approved(workflow_context) -> None:
    client, _ = workflow_context
    approved = create_approved(client)
    assert client.patch(f"/api/v1/subject/locations/{approved['id']}", headers=SUBJECT, json={"opening_hours": "8h"}).status_code == 409

    image = upload_image(client)
    proposal = complete_fields(image, name="Vườn dâu Langbiang", opening_hours="06:30 - 18:00", product_ids=[])
    created = client.post(
        f"/api/v1/subject/locations/{approved['id']}/change-requests",
        headers=SUBJECT,
        json={"proposed_data": proposal, "reason": "Đổi giờ mở cửa mùa cao điểm."},
    )
    assert created.status_code == 201, created.text
    request = created.json()
    assert request["status"] == "pending"
    assert request["base_version"] == approved["version"]
    assert request["current_data"]["opening_hours"] == "07:00 - 17:00"

    duplicate = client.post(
        f"/api/v1/subject/locations/{approved['id']}/deletion-requests",
        headers=SUBJECT,
        json={"reason": "Tạm đóng cửa."},
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "ACTIVE_LOCATION_CHANGE_REQUEST_EXISTS"

    listed = client.get("/api/v1/subject/locations", headers=SUBJECT).json()["items"]
    assert listed[0]["open_change_request_id"] == request["id"]
    assert client.get(f"/api/v1/locations/{approved['slug']}").json()["opening_hours"] == "07:00 - 17:00"

    admin_view = client.get(f"/api/v1/admin/location-change-requests/{request['id']}", headers=ADMIN)
    assert admin_view.json()["proposed_position_check"]["inside_lam_dong"] is True

    applied = client.patch(
        f"/api/v1/admin/location-change-requests/{request['id']}/moderation",
        headers=ADMIN,
        json={"status": "approved"},
    )
    assert applied.status_code == 200, applied.text
    public = client.get(f"/api/v1/locations/{approved['slug']}")
    assert public.status_code == 200
    assert public.json()["name"] == "Vườn dâu Langbiang"
    assert public.json()["opening_hours"] == "06:30 - 18:00"
    assert public.json()["products"] == []
    detail = client.get(f"/api/v1/subject/locations/{approved['id']}", headers=SUBJECT).json()
    assert detail["version"] == approved["version"] + 1
    assert detail["slug"] == approved["slug"]
    assert detail["open_change_request_id"] is None


def test_stale_update_request_is_rejected_with_version_conflict(workflow_context) -> None:
    client, testing_session = workflow_context
    approved = create_approved(client)
    request = client.post(
        f"/api/v1/subject/locations/{approved['id']}/change-requests",
        headers=SUBJECT,
        json={"proposed_data": complete_fields(upload_image(client))},
    ).json()
    with testing_session() as session:
        session.execute(
            update(TourismLocation).where(TourismLocation.id == approved["id"]).values(version=TourismLocation.version + 1)
        )
        session.commit()

    response = client.patch(
        f"/api/v1/admin/location-change-requests/{request['id']}/moderation",
        headers=ADMIN,
        json={"status": "approved"},
    )

    assert response.status_code == 409
    assert response.json()["code"] == "LOCATION_VERSION_CONFLICT"


def test_revise_cancel_and_delete_requests(workflow_context) -> None:
    client, _ = workflow_context
    approved = create_approved(client)
    request = client.post(
        f"/api/v1/subject/locations/{approved['id']}/deletion-requests",
        headers=SUBJECT,
        json={"reason": "Tạm dừng đón khách."},
    ).json()

    cannot_edit = client.put(
        f"/api/v1/subject/location-change-requests/{request['id']}",
        headers=SUBJECT,
        json={"reason": "Sửa lý do"},
    )
    assert cannot_edit.status_code == 409
    revision = client.patch(
        f"/api/v1/admin/location-change-requests/{request['id']}/moderation",
        headers=ADMIN,
        json={"status": "needs_revision", "note": "Ghi rõ thời gian tạm dừng."},
    )
    assert revision.json()["status"] == "needs_revision"
    resubmitted = client.put(
        f"/api/v1/subject/location-change-requests/{request['id']}",
        headers=SUBJECT,
        json={"reason": "Tạm dừng đón khách đến hết năm 2026."},
    )
    assert resubmitted.status_code == 200
    assert resubmitted.json()["status"] == "pending"
    assert resubmitted.json()["review_note"] is None
    assert client.get(f"/api/v1/subject/location-change-requests/{request['id']}", headers=OTHER_SUBJECT).status_code == 404

    archived = client.patch(
        f"/api/v1/admin/location-change-requests/{request['id']}/moderation",
        headers=ADMIN,
        json={"status": "approved"},
    )
    assert archived.status_code == 200
    detail = client.get(f"/api/v1/subject/locations/{approved['id']}", headers=SUBJECT).json()
    assert detail["status"] == "archived"
    assert client.get(f"/api/v1/locations/{approved['slug']}").status_code == 404
    assert client.post(
        f"/api/v1/subject/location-change-requests/{request['id']}/cancel", headers=SUBJECT
    ).status_code == 409

    requests = client.get("/api/v1/admin/location-change-requests?request_type=delete", headers=ADMIN)
    assert requests.json()["total"] == 1


def test_subject_can_cancel_open_request(workflow_context) -> None:
    client, _ = workflow_context
    approved = create_approved(client)
    request = client.post(
        f"/api/v1/subject/locations/{approved['id']}/deletion-requests",
        headers=SUBJECT,
        json={"reason": "Tạm dừng đón khách."},
    ).json()

    cancelled = client.post(f"/api/v1/subject/location-change-requests/{request['id']}/cancel", headers=SUBJECT)

    assert cancelled.json()["status"] == "cancelled"
    assert client.get("/api/v1/subject/location-change-requests?status=cancelled", headers=SUBJECT).json()["total"] == 1


def test_parse_coordinates_endpoint(workflow_context) -> None:
    client, _ = workflow_context

    response = client.post(
        "/api/v1/subject/locations/parse-coordinates",
        headers=SUBJECT,
        json={"text": "https://www.google.com/maps/place/V%C6%B0%E1%BB%9Dn/@12.04,108.43,17z/data=!3m1!4b1!3d12.047!4d108.441"},
    )

    assert response.status_code == 200
    assert response.json()["location_source"] == "google_maps_link"
    assert (response.json()["latitude"], response.json()["longitude"]) == (12.047, 108.441)
    assert response.json()["position_check"]["inside_lam_dong"] is True


@pytest.mark.parametrize(
    ("text", "expected", "source"),
    [
        ("12.047000, 108.441000", (12.047, 108.441), "coordinates"),
        ("108.441 12.047", (12.047, 108.441), "coordinates"),
        ("(11.9404; 108.4383)", (11.9404, 108.4383), "coordinates"),
        ("12°02'49.2\"N 108°26'27.6\"E", (12.047, 108.441), "coordinates"),
        ("https://maps.google.com/?q=11.94,108.43", (11.94, 108.43), "google_maps_link"),
        ("https://www.google.com/maps/@11.9404,108.4383,15z", (11.9404, 108.4383), "google_maps_link"),
    ],
)
def test_parse_coordinate_text(text, expected, source) -> None:
    point, parsed_source = parse_coordinate_text(text)

    assert (point.latitude, point.longitude) == pytest.approx(expected, abs=1e-6)
    assert parsed_source == source


@pytest.mark.parametrize(
    ("text", "code"),
    [
        ("https://maps.app.goo.gl/AbCdEf123", "SHORT_MAPS_LINK_UNSUPPORTED"),
        ("https://www.google.com/maps/search/vuon+dau", "MAPS_LINK_WITHOUT_COORDINATES"),
        ("vườn dâu Đà Lạt", "INVALID_COORDINATES"),
        ("200, 300", "INVALID_COORDINATES"),
        ("12°75'99\"N 108°26'27.6\"E", "INVALID_COORDINATES"),
    ],
)
def test_parse_coordinate_text_errors(text, code) -> None:
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as error:
        parse_coordinate_text(text)

    assert error.value.detail["code"] == code


def test_ticket_price_is_decimal_and_draft_can_clear_position(workflow_context) -> None:
    client, _ = workflow_context
    draft = create_draft(client, **DEMO_POINT, location_source="coordinates", ticket_price="25000.50")
    assert Decimal(draft["ticket_price"]) == Decimal("25000.50")

    cleared = client.patch(
        f"/api/v1/subject/locations/{draft['id']}",
        headers=SUBJECT,
        json={"latitude": None, "longitude": None},
    )

    assert cleared.status_code == 200
    assert cleared.json()["latitude"] is None
    assert cleared.json()["position_check"] is None


def test_image_of_one_location_cannot_be_reused_for_another(workflow_context) -> None:
    client, _ = workflow_context
    image = upload_image(client)
    first = create_draft(client, **complete_fields(image))
    second = create_draft(client, name="Vườn dâu thứ hai")

    reused = client.patch(
        f"/api/v1/subject/locations/{second['id']}",
        headers=SUBJECT,
        json={"images": complete_fields(image)["images"]},
    )
    assert reused.status_code == 422
    assert reused.json()["code"] == "LOCATION_IMAGE_USED_ELSEWHERE"
    # Gửi lại đúng ảnh cho chính điểm đó vẫn được.
    same = client.patch(
        f"/api/v1/subject/locations/{first['id']}",
        headers=SUBJECT,
        json={"images": complete_fields(image)["images"]},
    )
    assert same.status_code == 200


def test_update_request_cannot_take_image_of_another_location(workflow_context) -> None:
    client, _ = workflow_context
    first = create_approved(client)
    second = create_approved(client, latitude=12.05, longitude=108.45)
    second_image = second["images"][0]

    response = client.post(
        f"/api/v1/subject/locations/{first['id']}/change-requests",
        headers=SUBJECT,
        json={
            "proposed_data": complete_fields(
                {"image_url": second_image["image_url"], "storage_path": second_image["storage_path"]}
            )
        },
    )

    assert response.status_code == 422
    assert response.json()["code"] == "LOCATION_IMAGE_USED_ELSEWHERE"


def test_resubmitted_delete_request_needs_real_reason(workflow_context) -> None:
    client, _ = workflow_context
    approved = create_approved(client)
    request = client.post(
        f"/api/v1/subject/locations/{approved['id']}/deletion-requests",
        headers=SUBJECT,
        json={"reason": "Tạm dừng đón khách."},
    ).json()
    client.patch(
        f"/api/v1/admin/location-change-requests/{request['id']}/moderation",
        headers=ADMIN,
        json={"status": "needs_revision", "note": "Ghi rõ thời gian."},
    )

    response = client.put(
        f"/api/v1/subject/location-change-requests/{request['id']}",
        headers=SUBJECT,
        json={"reason": "ok"},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "DELETION_REASON_REQUIRED"


def test_admin_origin_filter_uses_owner_not_position_source(workflow_context) -> None:
    client, _ = workflow_context
    create_draft(client)

    subject_drafts = client.get("/api/v1/admin/locations?status=draft&origin=subject", headers=ADMIN)
    imported_drafts = client.get("/api/v1/admin/locations?status=draft&origin=import", headers=ADMIN)

    assert subject_drafts.json()["total"] == 1
    assert imported_drafts.json()["total"] == 0
