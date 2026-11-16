"""Liên kết dữ liệu bản đồ: điểm du lịch và cửa hàng, sản phẩm, chủ thể."""

from collections.abc import Generator
from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, insert
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.geometry import GeoPoint, register_sqlite_geo_functions
from app.main import app
from app.models.category import Category
from app.models.location import TourismLocation, location_ocop_products
from app.models.product import Product
from app.models.role import Role
from app.models.subject import Subject
from app.models.user import User


CAU_DAT = GeoPoint(longitude=108.547398, latitude=11.879583)
SHOP_CENTER = GeoPoint(longitude=108.4383, latitude=11.9404)
WORKSHOP = GeoPoint(longitude=108.47, latitude=11.92)


def _product(product_id: int, subject_id: int, category_id: int, name: str, slug: str, status: str = "approved") -> Product:
    return Product(
        id=product_id,
        subject_id=subject_id,
        category_id=category_id,
        name=name,
        slug=slug,
        star=4,
        price=Decimal("50000"),
        unit="hộp",
        cert_code=f"OCOP-{product_id}",
        cert_year=2025,
        cert_issued_at=date(2025, 1, 1),
        cert_expires_at=date(2099, 1, 1),
        issuing_authority="UBND tỉnh Lâm Đồng",
        description=f"Mô tả {name}.",
        status=status,
    )


def _location(
    location_id: int,
    name: str,
    slug: str,
    loc_type: str,
    geom: GeoPoint,
    status: str = "approved",
    subject_id: int | None = None,
) -> TourismLocation:
    return TourismLocation(
        id=location_id,
        subject_id=subject_id,
        name=name,
        slug=slug,
        type=loc_type,
        district="Đà Lạt",
        address="Đà Lạt, Lâm Đồng",
        geom=geom,
        services=[],
        status=status,
        contact_phone="0263 379 8888" if loc_type == "ocop_store" else None,
        website="https://example.com/" if loc_type == "ocop_store" else None,
    )


@pytest.fixture
def link_client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    event.listen(engine, "connect", register_sqlite_geo_functions)
    testing_session = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(engine)

    with testing_session() as session:
        role = Role(id=2, name="subject", description="Chủ thể")
        session.add_all(
            [
                User(id=1, role=role, email="a@example.com", hashed_password="x", full_name="A", is_active=True),
                User(id=2, role=role, email="b@example.com", hashed_password="x", full_name="B", is_active=True),
                User(id=3, role=role, email="c@example.com", hashed_password="x", full_name="C", is_active=False),
                Category(id=1, name="Đồ uống", slug="do-uong"),
                Category(id=2, name="Thực phẩm", slug="thuc-pham"),
            ]
        )
        session.flush()
        for subject_id, user_id, name in (
            (1, 1, "HTX Chè Cầu Đất"),
            (2, 2, "Công ty Mứt Đà Lạt"),
            (3, 3, "Chủ thể bị khóa"),
        ):
            session.add(
                Subject(
                    id=subject_id,
                    user_id=user_id,
                    name=name,
                    type="cooperative",
                    representative="Nguyễn Văn A",
                    phone="0912345678",
                    address="Đà Lạt",
                    district="Đà Lạt",
                    status="approved",
                )
            )
        session.flush()
        session.add_all(
            [
                _product(1, 1, 1, "Trà xanh Cầu Đất", "tra-xanh-cau-dat"),
                _product(2, 2, 2, "Mứt dâu tây", "mut-dau-tay"),
                _product(3, 1, 1, "Trà chưa duyệt", "tra-chua-duyet", status="pending"),
                _location(1, "Đồi chè Cầu Đất", "doi-che-cau-dat", "tea_coffee_farm", CAU_DAT, subject_id=1),
                _location(2, "Cửa hàng OCOP trung tâm", "cua-hang-ocop-trung-tam", "ocop_store", SHOP_CENTER),
                _location(3, "Xưởng mứt Đà Lạt", "xuong-mut-da-lat", "workshop", WORKSHOP, subject_id=2),
                _location(4, "Cửa hàng chờ duyệt", "cua-hang-cho-duyet", "ocop_store", SHOP_CENTER, status="pending"),
                _location(5, "Cửa hàng của chủ thể bị khóa", "cua-hang-bi-khoa", "ocop_store", SHOP_CENTER, subject_id=3),
            ]
        )
        session.flush()
        session.execute(
            insert(location_ocop_products),
            [
                {"location_id": 1, "product_id": 1, "role": "displayed"},
                {"location_id": 2, "product_id": 1, "role": "sold_here"},
                {"location_id": 2, "product_id": 2, "role": "sold_here"},
                {"location_id": 3, "product_id": 2, "role": "produced_here"},
                {"location_id": 2, "product_id": 3, "role": "sold_here"},
                {"location_id": 4, "product_id": 1, "role": "sold_here"},
            ],
        )
        session.commit()

    def override_get_db() -> Generator[Session, None, None]:
        with testing_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


def slugs(response) -> set[str]:
    return {feature["properties"]["slug"] for feature in response.json()["features"]}


def test_map_returns_attractions_and_shops_by_default(link_client: TestClient) -> None:
    response = link_client.get("/api/v1/map/locations")

    assert response.status_code == 200
    assert slugs(response) == {"doi-che-cau-dat", "cua-hang-ocop-trung-tam", "xuong-mut-da-lat"}
    kinds = {f["properties"]["slug"]: f["properties"]["kind"] for f in response.json()["features"]}
    assert kinds == {
        "doi-che-cau-dat": "attraction",
        "cua-hang-ocop-trung-tam": "shop",
        "xuong-mut-da-lat": "shop",
    }


def test_map_features_include_contact_phone_and_website(link_client: TestClient) -> None:
    response = link_client.get("/api/v1/map/locations", params={"kind": "shop"})
    features = {f["properties"]["slug"]: f["properties"] for f in response.json()["features"]}

    assert features["cua-hang-ocop-trung-tam"]["contact_phone"] == "0263 379 8888"
    assert features["cua-hang-ocop-trung-tam"]["website"] == "https://example.com/"
    assert features["xuong-mut-da-lat"]["contact_phone"] is None


def test_map_kind_filter_splits_attractions_and_shops(link_client: TestClient) -> None:
    attractions = link_client.get("/api/v1/map/locations", params={"kind": "attraction"})
    shops = link_client.get("/api/v1/map/locations", params={"kind": "shop"})

    assert slugs(attractions) == {"doi-che-cau-dat"}
    assert slugs(shops) == {"cua-hang-ocop-trung-tam", "xuong-mut-da-lat"}
    assert link_client.get("/api/v1/map/locations", params={"kind": "khac"}).status_code == 422


def test_map_features_report_product_role_and_hide_unapproved_products(link_client: TestClient) -> None:
    response = link_client.get("/api/v1/map/locations", params={"kind": "shop"})
    features = {f["properties"]["slug"]: f["properties"] for f in response.json()["features"]}

    assert {(p["slug"], p["role"]) for p in features["cua-hang-ocop-trung-tam"]["products"]} == {
        ("tra-xanh-cau-dat", "sold_here"),
        ("mut-dau-tay", "sold_here"),
    }
    assert [(p["slug"], p["role"]) for p in features["xuong-mut-da-lat"]["products"]] == [
        ("mut-dau-tay", "produced_here")
    ]


def test_map_filters_by_product_category_and_subject(link_client: TestClient) -> None:
    by_product = link_client.get("/api/v1/map/locations", params={"product_id": 2})
    by_category = link_client.get("/api/v1/map/locations", params={"category": "do-uong"})
    by_subject = link_client.get("/api/v1/map/locations", params={"subject_id": 2})
    pending_product = link_client.get("/api/v1/map/locations", params={"product_id": 3})

    assert slugs(by_product) == {"cua-hang-ocop-trung-tam", "xuong-mut-da-lat"}
    assert slugs(by_category) == {"doi-che-cau-dat", "cua-hang-ocop-trung-tam"}
    assert slugs(by_subject) == {"xuong-mut-da-lat"}
    assert slugs(pending_product) == set()


def test_location_list_defaults_to_attractions_only(link_client: TestClient) -> None:
    default = link_client.get("/api/v1/locations")
    shops = link_client.get("/api/v1/locations", params={"kind": "shop"})
    options = link_client.get("/api/v1/locations/filter-options")

    assert [item["slug"] for item in default.json()["items"]] == ["doi-che-cau-dat"]
    assert default.json()["items"][0]["kind"] == "attraction"
    assert {item["slug"] for item in shops.json()["items"]} == {
        "cua-hang-ocop-trung-tam",
        "xuong-mut-da-lat",
    }
    assert [option["value"] for option in options.json()["types"]] == ["tea_coffee_farm"]


def test_nearby_can_return_shops(link_client: TestClient) -> None:
    response = link_client.get(
        "/api/v1/map/nearby",
        params={"latitude": SHOP_CENTER.latitude, "longitude": SHOP_CENTER.longitude, "kind": "shop"},
    )

    assert response.status_code == 200
    assert response.json()["items"][0]["slug"] == "cua-hang-ocop-trung-tam"
    assert all(item["kind"] == "shop" for item in response.json()["items"])


def test_product_locations_lists_where_to_buy_with_role(link_client: TestClient) -> None:
    response = link_client.get("/api/v1/products/mut-dau-tay/locations")

    assert response.status_code == 200
    data = response.json()
    assert data["product_slug"] == "mut-dau-tay"
    assert {(item["slug"], item["role"], item["kind"]) for item in data["items"]} == {
        ("cua-hang-ocop-trung-tam", "sold_here", "shop"),
        ("xuong-mut-da-lat", "produced_here", "shop"),
    }
    # Điểm chờ duyệt không xuất hiện dù có gắn sản phẩm.
    tra = link_client.get("/api/v1/products/tra-xanh-cau-dat/locations").json()
    assert {item["slug"] for item in tra["items"]} == {"doi-che-cau-dat", "cua-hang-ocop-trung-tam"}


def test_product_locations_404_for_unpublished_product(link_client: TestClient) -> None:
    for slug in ("tra-chua-duyet", "khong-ton-tai"):
        response = link_client.get(f"/api/v1/products/{slug}/locations")
        assert response.status_code == 404
        assert response.json()["code"] == "PRODUCT_NOT_FOUND"


def test_public_subject_lists_its_locations_and_products(link_client: TestClient) -> None:
    response = link_client.get("/api/v1/subjects/2")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Công ty Mứt Đà Lạt"
    assert [item["slug"] for item in data["locations"]] == ["xuong-mut-da-lat"]
    assert [item["slug"] for item in data["products"]] == ["mut-dau-tay"]


def test_public_subject_404_for_missing_or_locked_account(link_client: TestClient) -> None:
    for subject_id in (3, 999):
        response = link_client.get(f"/api/v1/subjects/{subject_id}")
        assert response.status_code == 404
        assert response.json()["code"] == "SUBJECT_NOT_FOUND"
