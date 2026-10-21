from collections.abc import Generator
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.geometry import GeoPoint, register_sqlite_geo_functions
from app.core.security import create_access_token
from app.main import app
from app.models.category import Category
from app.models.location import TourismLocation
from app.models.product import Product
from app.models.role import Role
from app.models.subject import Subject
from app.models.user import SocialAccount, User


ADMIN_ID = 1
SECOND_ADMIN_ID = 2
SUBJECT_USER_ID = 3
PLAIN_USER_ID = 4
LOCKED_USER_ID = 5


def make_user(user_id: int, role_id: int, email: str, full_name: str, **kwargs) -> User:
    return User(
        id=user_id,
        role_id=role_id,
        email=email,
        hashed_password=kwargs.pop("hashed_password", "not-used"),
        full_name=full_name,
        is_active=kwargs.pop("is_active", True),
        created_at=datetime(2026, 9, user_id, tzinfo=timezone.utc),
        **kwargs,
    )


@pytest.fixture
def admin_context() -> Generator[tuple[TestClient, sessionmaker], None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    event.listen(engine, "connect", register_sqlite_geo_functions)
    testing_session = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(engine)

    with testing_session() as session:
        session.add_all(
            [
                Role(id=1, name="admin", description="Quản trị"),
                Role(id=2, name="subject", description="Chủ thể"),
                Role(id=3, name="user", description="Người dùng"),
            ]
        )
        session.flush()
        session.add_all(
            [
                make_user(ADMIN_ID, 1, "admin@example.com", "Quản trị chính"),
                make_user(SECOND_ADMIN_ID, 1, "admin2@example.com", "Quản trị phụ"),
                make_user(SUBJECT_USER_ID, 2, "htx@example.com", "Chủ HTX Cầu Đất", phone="0912345678"),
                make_user(PLAIN_USER_ID, 3, "khach_50%@example.com", "Khách tham quan", hashed_password=None),
                make_user(LOCKED_USER_ID, 3, "khoa@example.com", "Tài khoản đã khóa", is_active=False),
                Category(id=1, name="Đồ uống", slug="do-uong"),
            ]
        )
        session.flush()
        session.add_all(
            [
                SocialAccount(user_id=PLAIN_USER_ID, provider="google", provider_user_id="g-1"),
                Subject(
                    id=1,
                    user_id=SUBJECT_USER_ID,
                    name="HTX Chè Cầu Đất",
                    type="cooperative",
                    representative="Nguyễn Văn A",
                    phone="0912345678",
                    address="Xuân Trường, Đà Lạt",
                    district="Đà Lạt",
                    status="approved",
                ),
            ]
        )
        session.flush()
        session.add_all(
            [
                Product(
                    id=1,
                    subject_id=1,
                    category_id=1,
                    name="Trà xanh Cầu Đất",
                    slug="tra-xanh-cau-dat",
                    star=4,
                    price=Decimal("120000"),
                    unit="hộp",
                    cert_code="OCOP-LD-TRA",
                    cert_year=2025,
                    cert_issued_at=date(2025, 1, 1),
                    cert_expires_at=date(2099, 1, 1),
                    issuing_authority="UBND tỉnh Lâm Đồng",
                    description="Trà xanh từ đồi chè Cầu Đất.",
                    status="approved",
                ),
                TourismLocation(
                    id=1,
                    subject_id=1,
                    name="Cầu Đất Farm",
                    slug="cau-dat-farm",
                    type="tea_coffee_farm",
                    district="Đà Lạt",
                    address="Xuân Trường, Đà Lạt",
                    geom=GeoPoint(longitude=108.547398, latitude=11.879583),
                    status="approved",
                ),
                TourismLocation(
                    id=2,
                    name="Nông trại Dalat Milk",
                    slug="nong-trai-dalat-milk",
                    type="dairy_farm",
                    district="Đơn Dương",
                    address="Tu Tra, Đơn Dương",
                    geom=GeoPoint(longitude=108.437725, latitude=11.739771),
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


ADMIN = auth(ADMIN_ID, "admin")


@pytest.mark.parametrize(
    ("user_id", "role"),
    [(SUBJECT_USER_ID, "subject"), (PLAIN_USER_ID, "user")],
)
def test_admin_user_endpoints_reject_non_admin(admin_context, user_id: int, role: str) -> None:
    client, _ = admin_context
    headers = auth(user_id, role)

    assert client.get("/api/v1/admin/users", headers=headers).status_code == 403
    response = client.patch(
        f"/api/v1/admin/users/{LOCKED_USER_ID}/status",
        json={"is_active": True},
        headers=headers,
    )
    assert response.status_code == 403
    assert response.json()["code"] == "INSUFFICIENT_PERMISSIONS"


def test_admin_user_endpoints_require_login(admin_context) -> None:
    client, _ = admin_context

    assert client.get("/api/v1/admin/users").status_code == 401


def test_list_users_returns_account_details(admin_context) -> None:
    client, _ = admin_context

    response = client.get("/api/v1/admin/users", headers=ADMIN)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 5
    assert body["page"] == 1
    assert [item["id"] for item in body["items"]] == [5, 4, 3, 2, 1]
    subject_user = next(item for item in body["items"] if item["id"] == SUBJECT_USER_ID)
    assert subject_user["role"] == "subject"
    assert subject_user["phone"] == "0912345678"
    assert subject_user["subject"] == {"id": 1, "name": "HTX Chè Cầu Đất", "status": "approved"}
    social_user = next(item for item in body["items"] if item["id"] == PLAIN_USER_ID)
    assert social_user["has_password"] is False
    assert social_user["social_providers"] == ["google"]
    assert social_user["subject"] is None
    assert "hashed_password" not in social_user


def test_list_users_filters_by_role_status_and_pagination(admin_context) -> None:
    client, _ = admin_context

    admins = client.get("/api/v1/admin/users", params={"role": "admin"}, headers=ADMIN).json()
    assert {item["id"] for item in admins["items"]} == {ADMIN_ID, SECOND_ADMIN_ID}

    locked = client.get("/api/v1/admin/users", params={"is_active": "false"}, headers=ADMIN).json()
    assert [item["id"] for item in locked["items"]] == [LOCKED_USER_ID]

    paged = client.get(
        "/api/v1/admin/users",
        params={"role": "user", "is_active": "true", "page": 1, "page_size": 1},
        headers=ADMIN,
    ).json()
    assert paged["total"] == 1
    assert [item["id"] for item in paged["items"]] == [PLAIN_USER_ID]

    invalid = client.get("/api/v1/admin/users", params={"role": "khach"}, headers=ADMIN)
    assert invalid.status_code == 422
    assert invalid.json()["code"] == "VALIDATION_ERROR"


def test_list_users_search_by_email_or_name(admin_context) -> None:
    client, _ = admin_context

    by_name = client.get("/api/v1/admin/users", params={"q": "HTX"}, headers=ADMIN).json()
    assert [item["id"] for item in by_name["items"]] == [SUBJECT_USER_ID]

    by_email = client.get("/api/v1/admin/users", params={"q": "ADMIN2@"}, headers=ADMIN).json()
    assert [item["id"] for item in by_email["items"]] == [SECOND_ADMIN_ID]


@pytest.mark.parametrize(("keyword", "expected"), [("_", [PLAIN_USER_ID]), ("%", [PLAIN_USER_ID]), ("\\", [])])
def test_list_users_search_escapes_like_wildcards(admin_context, keyword: str, expected: list[int]) -> None:
    client, _ = admin_context

    response = client.get("/api/v1/admin/users", params={"q": keyword}, headers=ADMIN)

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["items"]] == expected


def test_admin_can_lock_and_unlock_user(admin_context) -> None:
    client, testing_session = admin_context

    locked = client.patch(
        f"/api/v1/admin/users/{PLAIN_USER_ID}/status",
        json={"is_active": False},
        headers=ADMIN,
    )
    assert locked.status_code == 200
    assert locked.json()["is_active"] is False
    assert locked.json()["role"] == "user"

    me = client.get("/api/v1/auth/me", headers=auth(PLAIN_USER_ID, "user"))
    assert me.status_code == 403
    assert me.json()["code"] == "ACCOUNT_INACTIVE"

    unlocked = client.patch(
        f"/api/v1/admin/users/{PLAIN_USER_ID}/status",
        json={"is_active": True},
        headers=ADMIN,
    )
    assert unlocked.status_code == 200
    assert unlocked.json()["is_active"] is True
    with testing_session() as session:
        assert session.get(User, PLAIN_USER_ID).is_active is True


def test_status_update_rejects_role_change_and_unknown_user(admin_context) -> None:
    client, _ = admin_context

    with_role = client.patch(
        f"/api/v1/admin/users/{PLAIN_USER_ID}/status",
        json={"is_active": False, "role": "admin"},
        headers=ADMIN,
    )
    assert with_role.status_code == 422

    missing = client.patch(
        "/api/v1/admin/users/999/status",
        json={"is_active": False},
        headers=ADMIN,
    )
    assert missing.status_code == 404
    assert missing.json()["code"] == "USER_NOT_FOUND"


def test_admin_cannot_lock_self(admin_context) -> None:
    client, _ = admin_context

    response = client.patch(
        f"/api/v1/admin/users/{ADMIN_ID}/status",
        json={"is_active": False},
        headers=ADMIN,
    )

    assert response.status_code == 409
    assert response.json() == {
        "code": "CANNOT_LOCK_SELF",
        "message": "Bạn không thể tự khóa tài khoản của mình.",
        "details": None,
    }


def test_last_active_admin_cannot_be_locked(admin_context) -> None:
    client, _ = admin_context

    other = client.patch(
        f"/api/v1/admin/users/{SECOND_ADMIN_ID}/status",
        json={"is_active": False},
        headers=ADMIN,
    )
    assert other.status_code == 200

    last = client.patch(
        f"/api/v1/admin/users/{ADMIN_ID}/status",
        json={"is_active": False},
        headers=ADMIN,
    )
    assert last.status_code == 409
    assert last.json()["code"] == "LAST_ACTIVE_ADMIN"


def test_locking_subject_hides_products_and_locations_from_public(admin_context) -> None:
    client, _ = admin_context

    assert client.get("/api/v1/products").json()["total"] == 1
    assert client.get("/api/v1/locations").json()["total"] == 2

    response = client.patch(
        f"/api/v1/admin/users/{SUBJECT_USER_ID}/status",
        json={"is_active": False},
        headers=ADMIN,
    )
    assert response.status_code == 200

    assert client.get("/api/v1/products").json()["total"] == 0
    assert client.get("/api/v1/products/tra-xanh-cau-dat").status_code == 404
    assert client.get("/api/v1/products/filter-options").json() == {"districts": []}

    locations = client.get("/api/v1/locations").json()
    assert [item["slug"] for item in locations["items"]] == ["nong-trai-dalat-milk"]
    assert client.get("/api/v1/locations/cau-dat-farm").status_code == 404
    assert client.get("/api/v1/locations/filter-options").json()["types"] == [
        {"value": "dairy_farm", "label": "Nông trại chăn nuôi"}
    ]
    features = client.get("/api/v1/map/locations").json()["features"]
    assert [feature["properties"]["slug"] for feature in features] == ["nong-trai-dalat-milk"]
    nearby = client.get(
        "/api/v1/map/nearby",
        params={"latitude": 11.9404, "longitude": 108.4383, "radius_km": 50},
    ).json()
    assert [item["slug"] for item in nearby["items"]] == ["nong-trai-dalat-milk"]

    client.patch(
        f"/api/v1/admin/users/{SUBJECT_USER_ID}/status",
        json={"is_active": True},
        headers=ADMIN,
    )
    assert client.get("/api/v1/products").json()["total"] == 1
    assert client.get("/api/v1/locations/cau-dat-farm").status_code == 200


def test_reference_data_account_stays_public_while_locked(admin_context) -> None:
    """Tài khoản kỹ thuật @local.invalid của dữ liệu nguồn công khai luôn khóa nhưng sản phẩm vẫn hiện."""

    client, testing_session = admin_context
    with testing_session() as session:
        user = session.get(User, SUBJECT_USER_ID)
        user.email = "ocop-source-abc@local.invalid"
        user.is_active = False
        session.commit()

    assert client.get("/api/v1/products").json()["total"] == 1
    assert client.get("/api/v1/products/tra-xanh-cau-dat").status_code == 200
    assert client.get("/api/v1/locations/cau-dat-farm").status_code == 200
