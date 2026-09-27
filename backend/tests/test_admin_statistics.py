from collections.abc import Generator
from datetime import date, datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.routes import admin_statistics
from app.core.database import Base, get_db
from app.core.geometry import GeoPoint, register_sqlite_geo_functions
from app.core.security import create_access_token
from app.main import app
from app.models.category import Category
from app.models.location import TourismLocation
from app.models.product import Product
from app.models.role import Role
from app.models.subject import Subject
from app.models.user import User


FIXED_NOW = datetime(2026, 9, 26, 10, 0, tzinfo=admin_statistics.LOCAL_TIMEZONE)


def product(
    product_id: int,
    *,
    subject_id: int = 1,
    category_id: int = 1,
    status: str = "approved",
    star: int | None = 3,
    reviewed_at: datetime | None = None,
    cert_year: int | None = None,
    cert_expires_at: date | None = None,
    views: int = 0,
) -> Product:
    return Product(
        id=product_id,
        subject_id=subject_id,
        category_id=category_id,
        name=f"Sản phẩm {product_id}",
        slug=f"san-pham-{product_id}",
        star=star,
        status=status,
        reviewed_at=reviewed_at,
        cert_year=cert_year,
        cert_expires_at=cert_expires_at,
        views=views,
    )


def subject(subject_id: int, user_id: int, district: str, status: str = "approved") -> Subject:
    return Subject(
        id=subject_id,
        user_id=user_id,
        name=f"Chủ thể {subject_id}",
        type="cooperative",
        representative="Nguyễn Văn A",
        phone="0912345678",
        address=district,
        district=district,
        status=status,
    )


def location(location_id: int, location_type: str, status: str = "approved") -> TourismLocation:
    return TourismLocation(
        id=location_id,
        name=f"Điểm {location_id}",
        slug=f"diem-{location_id}",
        type=location_type,
        district="Đà Lạt",
        address="Đà Lạt",
        geom=GeoPoint(longitude=108.44, latitude=11.94),
        services=[],
        status=status,
    )


def utc(year: int, month: int, day: int, hour: int = 12) -> datetime:
    return datetime(year, month, day, hour, tzinfo=timezone.utc)


@pytest.fixture
def statistics_context(monkeypatch) -> Generator[tuple[TestClient, dict[str, str]], None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    event.listen(engine, "connect", register_sqlite_geo_functions)
    testing_session = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(engine)

    with testing_session() as session:
        admin_role = Role(id=1, name="admin", description="Quản trị")
        user_role = Role(id=3, name="user", description="Người dùng")
        session.add_all(
            [
                admin_role,
                user_role,
                User(id=1, role=admin_role, email="admin@example.com", hashed_password="x", full_name="Quản trị", is_active=True),
                User(id=2, role=user_role, email="a@example.com", hashed_password="x", full_name="Chủ thể A", is_active=True),
                User(id=3, role=user_role, email="b@example.com", hashed_password="x", full_name="Chủ thể B", is_active=True),
                User(id=4, role=user_role, email="c@example.com", hashed_password="x", full_name="Chủ thể C", is_active=True),
                Category(id=1, name="Thực phẩm", slug="thuc-pham"),
                Category(id=2, name="Đồ uống", slug="do-uong"),
                Category(id=3, name="Sinh vật cảnh", slug="sinh-vat-canh"),
                subject(1, 2, "Xã Đức Trọng"),
                subject(2, 3, "Đà Lạt"),
                subject(3, 4, "Bảo Lộc", status="pending"),
            ]
        )
        session.flush()
        session.add_all(
            [
                # 17h UTC ngày 31/7 là 0h ngày 1/8 giờ Việt Nam: phải tính vào tháng 8.
                product(1, star=3, reviewed_at=utc(2026, 7, 31, 17), cert_year=2025, views=12),
                product(2, star=4, reviewed_at=utc(2026, 9, 2), cert_year=2025, cert_expires_at=date(2026, 9, 1), views=40),
                product(3, category_id=2, star=4, reviewed_at=utc(2026, 6, 15), cert_year=2026, cert_expires_at=date(2027, 1, 10)),
                product(4, subject_id=2, star=5, reviewed_at=None, cert_year=2024, cert_expires_at=date(2027, 6, 1)),
                product(5, status="pending", star=None, cert_year=2026, views=99),
                product(6, status="draft", star=None),
                product(7, subject_id=2, status="rejected", star=3, cert_expires_at=date(2020, 1, 1)),
                location(1, "tea_coffee_farm"),
                location(2, "tea_coffee_farm"),
                location(3, "dairy_farm"),
                location(4, "flower_garden", status="pending"),
            ]
        )
        session.commit()

    def override_get_db() -> Generator[Session, None, None]:
        with testing_session() as session:
            yield session

    monkeypatch.setattr(admin_statistics, "current_local_time", lambda: FIXED_NOW)
    app.dependency_overrides[get_db] = override_get_db
    headers = {"Authorization": f"Bearer {create_access_token(user_id=1, role='admin')}"}
    with TestClient(app) as client:
        yield client, headers
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


def test_statistics_requires_admin(statistics_context) -> None:
    client, _ = statistics_context
    user_token = create_access_token(user_id=2, role="user")

    assert client.get("/api/v1/admin/statistics").status_code == 401
    forbidden = client.get("/api/v1/admin/statistics", headers={"Authorization": f"Bearer {user_token}"})
    assert forbidden.status_code == 403


def test_statistics_counts_products(statistics_context) -> None:
    client, headers = statistics_context

    response = client.get("/api/v1/admin/statistics", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert {item["key"]: item["count"] for item in body["products_by_status"]} == {
        "approved": 4,
        "pending": 1,
        "draft": 1,
        "rejected": 1,
    }
    assert body["products_by_status"][0] == {"key": "approved", "count": 4}
    # Chỉ tính sản phẩm đang công khai.
    assert body["approved_by_star"] == [
        {"star": 3, "count": 1},
        {"star": 4, "count": 2},
        {"star": 5, "count": 1},
    ]
    # Nhóm chưa có sản phẩm vẫn được liệt kê với số 0.
    assert [(item["slug"], item["count"]) for item in body["approved_by_category"]] == [
        ("thuc-pham", 3),
        ("do-uong", 1),
        ("sinh-vat-canh", 0),
    ]
    assert body["approved_by_district"] == [
        {"district": "Xã Đức Trọng", "count": 3},
        {"district": "Đà Lạt", "count": 1},
    ]


def test_statistics_monthly_series_is_continuous_in_local_time(statistics_context) -> None:
    client, headers = statistics_context

    body = client.get("/api/v1/admin/statistics", headers=headers).json()

    assert body["approved_by_month"] == [
        {"month": "2026-06", "count": 1},
        {"month": "2026-07", "count": 0},
        {"month": "2026-08", "count": 1},
        {"month": "2026-09", "count": 1},
    ]
    assert body["approved_without_review_date"] == 1


def test_statistics_certificates_views_subjects_locations(statistics_context) -> None:
    client, headers = statistics_context

    body = client.get("/api/v1/admin/statistics", headers=headers).json()

    assert body["certificates"] == {
        "expired": 1,
        "expiring_soon": 0,
        "expiring_window_days": 90,
        "by_year": [
            {"year": 2024, "count": 1},
            {"year": 2025, "count": 2},
            {"year": 2026, "count": 2},
        ],
    }
    # Sản phẩm chưa công khai không lọt vào bảng xếp hạng lượt xem.
    assert [item["id"] for item in body["top_viewed_products"]] == [2, 1]
    assert {item["key"]: item["count"] for item in body["subjects_by_status"]} == {"approved": 2, "pending": 1}
    assert body["locations_by_type"] == [
        {"key": "tea_coffee_farm", "count": 2},
        {"key": "dairy_farm", "count": 1},
    ]


def test_expiring_soon_uses_ninety_day_window(statistics_context, monkeypatch) -> None:
    client, headers = statistics_context
    monkeypatch.setattr(
        admin_statistics,
        "current_local_time",
        lambda: datetime(2026, 10, 15, 9, 0, tzinfo=admin_statistics.LOCAL_TIMEZONE),
    )

    certificates = client.get("/api/v1/admin/statistics", headers=headers).json()["certificates"]

    # 10/01/2027 cách 26/09/2026 là 106 ngày (ngoài cửa sổ) nhưng cách 15/10/2026 là 87 ngày (trong cửa sổ 90 ngày).
    assert certificates["expiring_soon"] == 1
    assert certificates["expired"] == 1
