"""Tuyến tham quan: chỉ tuyến published, chỉ chặng còn công khai, đúng thứ tự."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.geometry import GeoPoint, register_sqlite_geo_functions
from app.main import app
from app.models.location import TourismLocation
from app.models.route import TourismRoute, TourismRouteStop


def _location(location_id: int, name: str, slug: str, loc_type: str, status: str = "approved") -> TourismLocation:
    return TourismLocation(
        id=location_id,
        name=name,
        slug=slug,
        type=loc_type,
        district="Đà Lạt",
        address="Đà Lạt, Lâm Đồng",
        geom=GeoPoint(longitude=108.4 + location_id / 100, latitude=11.9),
        services=[],
        status=status,
    )


@pytest.fixture
def tour_client() -> Generator[TestClient, None, None]:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    event.listen(engine, "connect", register_sqlite_geo_functions)
    testing_session = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(engine)

    with testing_session() as session:
        session.add_all(
            [
                _location(1, "Vườn dâu", "vuon-dau", "fruit_garden"),
                _location(2, "Cơ sở sản xuất", "co-so", "workshop"),
                _location(3, "Cửa hàng", "cua-hang", "ocop_store"),
                _location(4, "Điểm chờ duyệt", "cho-duyet", "ocop_store", status="pending"),
                TourismRoute(id=1, slug="dau-tay", name="Hành trình dâu tây", status="published", duration_text="Nửa ngày"),
                TourismRoute(id=2, slug="nhap", name="Tuyến nháp", status="draft"),
                TourismRoute(id=3, slug="rong", name="Tuyến chỉ có điểm chờ duyệt", status="published"),
            ]
        )
        session.flush()
        session.add_all(
            [
                # Cố ý chèn lệch thứ tự để kiểm tra việc sắp theo position.
                TourismRouteStop(route_id=1, location_id=3, position=3, note="Mua quà"),
                TourismRouteStop(route_id=1, location_id=1, position=1, note="Hái dâu"),
                TourismRouteStop(route_id=1, location_id=2, position=2),
                TourismRouteStop(route_id=1, location_id=4, position=4, note="Chưa duyệt"),
                TourismRouteStop(route_id=2, location_id=1, position=1),
                TourismRouteStop(route_id=3, location_id=4, position=1),
            ]
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


def test_list_only_published_routes_with_visible_stops(tour_client: TestClient) -> None:
    response = tour_client.get("/api/v1/tours")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 1,
            "slug": "dau-tay",
            "name": "Hành trình dâu tây",
            "description": None,
            "duration_text": "Nửa ngày",
            "stop_count": 3,
        }
    ]


def test_detail_returns_stops_in_order_without_hidden_locations(tour_client: TestClient) -> None:
    response = tour_client.get("/api/v1/tours/dau-tay")

    assert response.status_code == 200
    data = response.json()
    assert data["stop_count"] == 3
    assert [(stop["position"], stop["location"]["slug"]) for stop in data["stops"]] == [
        (1, "vuon-dau"),
        (2, "co-so"),
        (3, "cua-hang"),
    ]
    assert data["stops"][0]["note"] == "Hái dâu"
    assert data["stops"][2]["location"]["kind"] == "shop"
    assert data["stops"][0]["location"]["kind"] == "attraction"


@pytest.mark.parametrize("slug", ["nhap", "rong", "khong-ton-tai"])
def test_unpublished_empty_or_missing_route_is_404(tour_client: TestClient, slug: str) -> None:
    response = tour_client.get(f"/api/v1/tours/{slug}")

    assert response.status_code == 404
    assert response.json()["code"] == "ROUTE_NOT_FOUND"
