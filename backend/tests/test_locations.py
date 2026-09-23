from collections.abc import Generator
from datetime import date
from decimal import Decimal

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, insert, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.geometry import (
    GeoPoint,
    distance_meters,
    haversine_meters,
    register_sqlite_geo_functions,
    within_meters,
)
from app.main import app
from app.models.category import Category
from app.models.location import LocationImage, TourismLocation, location_ocop_products
from app.models.product import Product
from app.models.role import Role
from app.models.subject import Subject
from app.models.user import User
from app.services import routing


DA_LAT_CENTER = GeoPoint(longitude=108.4383, latitude=11.9404)
CAU_DAT = GeoPoint(longitude=108.547398, latitude=11.879583)
DALAT_MILK = GeoPoint(longitude=108.437725, latitude=11.739771)
TAM_CHAU = GeoPoint(longitude=107.742722, latitude=11.595286)


@pytest.fixture
def location_client() -> Generator[TestClient, None, None]:
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
                User(
                    id=1,
                    role=role,
                    email="farm@example.com",
                    hashed_password="not-used",
                    full_name="Nhà vườn Cầu Đất",
                    is_active=True,
                ),
                Category(id=1, name="Đồ uống", slug="do-uong"),
            ]
        )
        session.flush()
        session.add(
            Subject(
                id=1,
                user_id=1,
                name="HTX Chè Cầu Đất",
                type="cooperative",
                representative="Nguyễn Văn A",
                phone="0912345678",
                address="Xuân Trường, Đà Lạt",
                district="Đà Lạt",
                status="approved",
            )
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
                Product(
                    id=2,
                    subject_id=1,
                    category_id=1,
                    name="Trà chưa duyệt",
                    slug="tra-chua-duyet",
                    star=3,
                    description="Sản phẩm đang chờ kiểm duyệt.",
                    status="pending",
                ),
            ]
        )
        session.add_all(
            [
                TourismLocation(
                    id=1,
                    subject_id=1,
                    name="Cầu Đất Farm",
                    slug="cau-dat-farm",
                    type="tea_coffee_farm",
                    district="Đà Lạt",
                    address="Xuân Trường, Đà Lạt",
                    geom=CAU_DAT,
                    opening_hours="07:00 - 19:00",
                    ticket_price=Decimal("30000"),
                    services=["Tham quan đồi chè", "Chụp ảnh"],
                    description="Đồi chè lâu năm ở vùng Cầu Đất.",
                    contact_phone="0263000000",
                    source_url="https://example.com/cau-dat",
                    status="approved",
                ),
                TourismLocation(
                    id=2,
                    name="Nông trại Dalat Milk",
                    slug="nong-trai-dalat-milk",
                    type="dairy_farm",
                    district="Đơn Dương",
                    address="Tu Tra, Đơn Dương",
                    geom=DALAT_MILK,
                    ticket_price=Decimal("0"),
                    services=["Tham quan đồng cỏ"],
                    status="approved",
                ),
                TourismLocation(
                    id=3,
                    name="Đồi chè Tâm Châu",
                    slug="doi-che-tam-chau",
                    type="tea_coffee_farm",
                    district="Bảo Lâm",
                    address="Lộc Tân, Bảo Lâm",
                    geom=TAM_CHAU,
                    services=[],
                    status="approved",
                ),
                TourismLocation(
                    id=4,
                    name="Vườn chờ duyệt ở trung tâm",
                    slug="vuon-cho-duyet",
                    type="fruit_garden",
                    district="Đà Lạt",
                    address="Trung tâm Đà Lạt",
                    geom=DA_LAT_CENTER,
                    services=[],
                    status="pending",
                ),
                LocationImage(
                    id=1,
                    location_id=1,
                    image_url="https://example.com/cau-dat.jpg",
                    is_primary=True,
                ),
            ]
        )
        session.flush()
        session.execute(
            insert(location_ocop_products),
            [
                {"location_id": 1, "product_id": 1},
                {"location_id": 1, "product_id": 2},
                {"location_id": 4, "product_id": 1},
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


def mock_osrm(monkeypatch: pytest.MonkeyPatch, handler) -> list[httpx.Request]:
    requests: list[httpx.Request] = []

    def recording_handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return handler(request)

    monkeypatch.setattr(
        routing,
        "_create_client",
        lambda timeout: httpx.Client(transport=httpx.MockTransport(recording_handler)),
    )
    return requests


def test_geo_point_round_trips_wkt_and_rejects_invalid_values() -> None:
    point = GeoPoint.from_wkt("SRID=4326;POINT(108.547398 11.879583)")

    assert point == CAU_DAT
    assert GeoPoint.from_wkt(point.to_wkt()) == point
    with pytest.raises(ValueError):
        GeoPoint.from_wkt("LINESTRING(0 0, 1 1)")
    with pytest.raises(ValueError):
        GeoPoint(longitude=200, latitude=11)


def test_postgresql_uses_postgis_functions() -> None:
    dialect = postgresql.dialect()
    statement = select(
        TourismLocation.geom,
        distance_meters(TourismLocation.geom, 108.4, 11.9),
    ).where(within_meters(TourismLocation.geom, 108.4, 11.9, 5000))
    compiled = str(statement.compile(dialect=dialect))
    insert_sql = str(insert(TourismLocation).values(geom=CAU_DAT).compile(dialect=dialect))

    assert "ST_AsText(tourism_locations.geom)" in compiled
    assert "ST_Distance((tourism_locations.geom)::geography" in compiled
    assert "ST_DWithin((tourism_locations.geom)::geography" in compiled
    assert "ST_GeomFromText(" in insert_sql


def test_public_list_returns_only_approved_locations(location_client: TestClient) -> None:
    response = location_client.get("/api/v1/locations")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    # Thứ tự tên phụ thuộc collation của database nên chỉ kiểm tra tập kết quả.
    assert {item["slug"] for item in data["items"]} == {
        "cau-dat-farm",
        "doi-che-tam-chau",
        "nong-trai-dalat-milk",
    }
    cau_dat = next(item for item in data["items"] if item["slug"] == "cau-dat-farm")
    assert cau_dat["type_label"] == "Đồi chè & cà phê"
    assert cau_dat["latitude"] == pytest.approx(CAU_DAT.latitude)
    assert cau_dat["longitude"] == pytest.approx(CAU_DAT.longitude)
    assert cau_dat["ticket_price"] == 30000
    assert cau_dat["services"] == ["Tham quan đồi chè", "Chụp ảnh"]
    assert cau_dat["primary_image_url"] == "https://example.com/cau-dat.jpg"


def test_location_list_supports_search_filters_and_pagination(
    location_client: TestClient,
) -> None:
    by_keyword = location_client.get("/api/v1/locations", params={"search": "Tâm Châu"})
    by_type = location_client.get("/api/v1/locations", params={"type": "dairy_farm"})
    by_district = location_client.get("/api/v1/locations", params={"district": "Đà Lạt"})
    paged = location_client.get("/api/v1/locations", params={"page": 2, "page_size": 2})
    empty = location_client.get("/api/v1/locations", params={"search": "không tồn tại"})
    invalid_type = location_client.get("/api/v1/locations", params={"type": "casino"})

    assert [item["slug"] for item in by_keyword.json()["items"]] == ["doi-che-tam-chau"]
    assert [item["slug"] for item in by_type.json()["items"]] == ["nong-trai-dalat-milk"]
    assert [item["slug"] for item in by_district.json()["items"]] == ["cau-dat-farm"]
    assert paged.json()["total"] == 3
    assert len(paged.json()["items"]) == 1
    assert empty.json() == {"items": [], "page": 1, "page_size": 12, "total": 0}
    assert invalid_type.status_code == 422
    assert invalid_type.json()["code"] == "VALIDATION_ERROR"


def test_filter_options_only_list_public_values(location_client: TestClient) -> None:
    response = location_client.get("/api/v1/locations/filter-options")

    assert response.status_code == 200
    assert response.json() == {
        "types": [
            {"value": "tea_coffee_farm", "label": "Đồi chè & cà phê"},
            {"value": "dairy_farm", "label": "Nông trại chăn nuôi"},
        ],
        "districts": ["Bảo Lâm", "Đà Lạt", "Đơn Dương"],
    }


def test_location_detail_shows_contact_subject_and_public_products(
    location_client: TestClient,
) -> None:
    response = location_client.get("/api/v1/locations/cau-dat-farm")

    assert response.status_code == 200
    data = response.json()
    assert data["contact_phone"] == "0263000000"
    assert data["source_url"] == "https://example.com/cau-dat"
    assert data["subject"] == {"id": 1, "name": "HTX Chè Cầu Đất", "district": "Đà Lạt"}
    assert [product["slug"] for product in data["products"]] == ["tra-xanh-cau-dat"]
    assert data["images"][0]["is_primary"] is True


def test_hidden_or_unknown_location_returns_not_found(location_client: TestClient) -> None:
    pending = location_client.get("/api/v1/locations/vuon-cho-duyet")
    unknown = location_client.get("/api/v1/locations/khong-ton-tai")

    assert pending.status_code == 404
    assert pending.json()["code"] == "LOCATION_NOT_FOUND"
    assert unknown.status_code == 404


def test_map_locations_return_geojson_in_longitude_latitude_order(
    location_client: TestClient,
) -> None:
    response = location_client.get("/api/v1/map/locations")
    filtered = location_client.get("/api/v1/map/locations", params={"type": "tea_coffee_farm"})

    assert response.status_code == 200
    collection = response.json()
    assert collection["type"] == "FeatureCollection"
    assert len(collection["features"]) == 3
    feature = next(
        item for item in collection["features"] if item["properties"]["slug"] == "cau-dat-farm"
    )
    assert feature["type"] == "Feature"
    assert feature["geometry"] == {
        "type": "Point",
        "coordinates": [CAU_DAT.longitude, CAU_DAT.latitude],
    }
    assert {item["properties"]["slug"] for item in filtered.json()["features"]} == {
        "cau-dat-farm",
        "doi-che-tam-chau",
    }


def test_nearby_orders_by_distance_within_radius(location_client: TestClient) -> None:
    response = location_client.get(
        "/api/v1/map/nearby",
        params={
            "latitude": DA_LAT_CENTER.latitude,
            "longitude": DA_LAT_CENTER.longitude,
            "radius_km": 30,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["radius_m"] == 30000
    assert [item["slug"] for item in data["items"]] == ["cau-dat-farm", "nong-trai-dalat-milk"]
    expected = haversine_meters(DA_LAT_CENTER, CAU_DAT)
    assert data["items"][0]["distance_m"] == pytest.approx(expected, rel=0.01)
    assert data["items"][0]["distance_m"] < data["items"][1]["distance_m"]


def test_nearby_respects_limit_type_and_validates_input(location_client: TestClient) -> None:
    params = {"latitude": DA_LAT_CENTER.latitude, "longitude": DA_LAT_CENTER.longitude}
    limited = location_client.get("/api/v1/map/nearby", params={**params, "radius_km": 200, "limit": 1})
    typed = location_client.get(
        "/api/v1/map/nearby",
        params={**params, "radius_km": 200, "type": "tea_coffee_farm"},
    )
    none_found = location_client.get("/api/v1/map/nearby", params={**params, "radius_km": 1})
    invalid_latitude = location_client.get(
        "/api/v1/map/nearby",
        params={"latitude": 91, "longitude": 108},
    )
    invalid_radius = location_client.get("/api/v1/map/nearby", params={**params, "radius_km": 0})
    missing_origin = location_client.get("/api/v1/map/nearby")

    assert [item["slug"] for item in limited.json()["items"]] == ["cau-dat-farm"]
    assert [item["slug"] for item in typed.json()["items"]] == [
        "cau-dat-farm",
        "doi-che-tam-chau",
    ]
    assert none_found.json()["items"] == []
    assert invalid_latitude.status_code == 422
    assert invalid_radius.status_code == 422
    assert missing_origin.status_code == 422


def test_route_proxies_osrm_with_longitude_latitude_order(
    location_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests = mock_osrm(
        monkeypatch,
        lambda request: httpx.Response(
            200,
            json={
                "code": "Ok",
                "routes": [
                    {
                        "distance": 15234.56,
                        "duration": 1320.44,
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [[108.4383, 11.9404], [108.547398, 11.879583]],
                        },
                    }
                ],
            },
        ),
    )

    response = location_client.get(
        "/api/v1/map/route",
        params={
            "destination": "cau-dat-farm",
            "from_latitude": DA_LAT_CENTER.latitude,
            "from_longitude": DA_LAT_CENTER.longitude,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["distance_m"] == 15234.6
    assert data["duration_s"] == 1320.4
    assert data["destination"]["slug"] == "cau-dat-farm"
    assert data["geometry"]["coordinates"][-1] == [108.547398, 11.879583]
    assert "/route/v1/driving/108.438300,11.940400;108.547398,11.879583" in str(requests[0].url)
    assert requests[0].url.params["geometries"] == "geojson"


@pytest.mark.parametrize(
    ("handler", "status_code", "error_code"),
    [
        (
            lambda request: httpx.Response(200, json={"code": "NoRoute", "routes": []}),
            422,
            "ROUTE_NOT_FOUND",
        ),
        (lambda request: httpx.Response(502, text="Bad gateway"), 503, "ROUTING_UNAVAILABLE"),
        (
            lambda request: httpx.Response(200, json={"code": "Ok", "routes": [{"distance": 1}]}),
            503,
            "ROUTING_UNAVAILABLE",
        ),
    ],
)
def test_route_reports_friendly_errors(
    location_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    handler,
    status_code: int,
    error_code: str,
) -> None:
    mock_osrm(monkeypatch, handler)

    response = location_client.get(
        "/api/v1/map/route",
        params={"destination": "cau-dat-farm", "from_latitude": 11.94, "from_longitude": 108.43},
    )

    assert response.status_code == status_code
    assert response.json()["code"] == error_code


def test_route_handles_timeout(
    location_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("timeout", request=request)

    mock_osrm(monkeypatch, timeout)
    response = location_client.get(
        "/api/v1/map/route",
        params={"destination": "cau-dat-farm", "from_latitude": 11.94, "from_longitude": 108.43},
    )

    assert response.status_code == 503
    assert response.json()["code"] == "ROUTING_UNAVAILABLE"


def test_route_validates_origin_and_destination_before_calling_osrm(
    location_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests = mock_osrm(monkeypatch, lambda request: httpx.Response(500))

    outside = location_client.get(
        "/api/v1/map/route",
        params={"destination": "cau-dat-farm", "from_latitude": 48.85, "from_longitude": 2.35},
    )
    hidden = location_client.get(
        "/api/v1/map/route",
        params={"destination": "vuon-cho-duyet", "from_latitude": 11.94, "from_longitude": 108.43},
    )
    missing = location_client.get("/api/v1/map/route", params={"destination": "cau-dat-farm"})

    assert outside.status_code == 422
    assert outside.json()["code"] == "ORIGIN_OUT_OF_RANGE"
    assert hidden.status_code == 404
    assert hidden.json()["code"] == "LOCATION_NOT_FOUND"
    assert missing.status_code == 422
    assert requests == []


def test_product_detail_lists_only_approved_related_locations(
    location_client: TestClient,
) -> None:
    response = location_client.get("/api/v1/products/tra-xanh-cau-dat")

    assert response.status_code == 200
    assert response.json()["related_locations"] == [
        {
            "id": 1,
            "name": "Cầu Đất Farm",
            "slug": "cau-dat-farm",
            "type_label": "Đồi chè & cà phê",
            "district": "Đà Lạt",
        }
    ]
