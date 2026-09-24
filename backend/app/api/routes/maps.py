from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.geometry import GeoPoint, distance_meters, within_meters
from app.models.location import TourismLocation
from app.schemas.error import ErrorResponse
from app.schemas.location import (
    Coordinate,
    LineStringGeometryRead,
    MapFeatureCollection,
    NearbyLocation,
    NearbyLocationResponse,
    RouteDestination,
    RouteResponse,
)
from app.services.location_catalog import (
    LocationTypeCode,
    public_location_filters,
    to_location_list_item,
    to_map_feature,
)
from app.services.routing import (
    RouteNotFoundError,
    RoutingUnavailableError,
    get_driving_route,
)


router = APIRouter(prefix="/map", tags=["Map"])

MAX_MAP_FEATURES = 2000
# Điểm xuất phát chỉ đường phải nằm trong lãnh thổ Việt Nam (khung bao gần đúng).
VIETNAM_LATITUDE_RANGE = (8.0, 23.5)
VIETNAM_LONGITUDE_RANGE = (102.0, 110.0)


@router.get("/locations", response_model=MapFeatureCollection)
def get_map_locations(
    search: str | None = Query(default=None, min_length=1, max_length=150),
    location_type: LocationTypeCode | None = Query(default=None, alias="type"),
    district: str | None = Query(default=None, min_length=1, max_length=100),
    db: Session = Depends(get_db),
) -> MapFeatureCollection:
    """Trả các điểm đã duyệt dưới dạng GeoJSON FeatureCollection."""

    locations = db.scalars(
        select(TourismLocation)
        .where(
            *public_location_filters(
                search=search,
                location_type=location_type,
                district=district,
            )
        )
        .options(selectinload(TourismLocation.images))
        .order_by(TourismLocation.name.asc(), TourismLocation.id.asc())
        .limit(MAX_MAP_FEATURES)
    ).all()
    return MapFeatureCollection(features=[to_map_feature(location) for location in locations])


@router.get(
    "/nearby",
    response_model=NearbyLocationResponse,
    responses={status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorResponse}},
)
def get_nearby_locations(
    latitude: float = Query(ge=-90, le=90),
    longitude: float = Query(ge=-180, le=180),
    radius_km: float = Query(default=25, gt=0, le=200),
    limit: int = Query(default=10, ge=1, le=50),
    location_type: LocationTypeCode | None = Query(default=None, alias="type"),
    db: Session = Depends(get_db),
) -> NearbyLocationResponse:
    """Tìm điểm đã duyệt gần nhất trong bán kính, sắp xếp theo khoảng cách."""

    radius_m = radius_km * 1000
    distance = distance_meters(TourismLocation.geom, longitude, latitude)
    rows = db.execute(
        select(TourismLocation, distance.label("distance_m"))
        .where(
            *public_location_filters(location_type=location_type),
            within_meters(TourismLocation.geom, longitude, latitude, radius_m),
        )
        .options(selectinload(TourismLocation.images))
        .order_by(distance.asc(), TourismLocation.id.asc())
        .limit(limit)
    ).all()
    return NearbyLocationResponse(
        origin=Coordinate(latitude=latitude, longitude=longitude),
        radius_m=radius_m,
        items=[
            NearbyLocation(
                **to_location_list_item(location).model_dump(),
                distance_m=round(float(distance_m), 1),
            )
            for location, distance_m in rows
        ],
    )


@router.get(
    "/route",
    response_model=RouteResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorResponse},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponse},
    },
)
def get_route_to_location(
    destination: str = Query(min_length=1, max_length=255, description="Slug điểm đến"),
    from_latitude: float = Query(ge=-90, le=90),
    from_longitude: float = Query(ge=-180, le=180),
    db: Session = Depends(get_db),
) -> RouteResponse:
    """Gợi ý tuyến đường bộ từ vị trí người dùng tới một điểm du lịch đã duyệt."""

    if not (
        VIETNAM_LATITUDE_RANGE[0] <= from_latitude <= VIETNAM_LATITUDE_RANGE[1]
        and VIETNAM_LONGITUDE_RANGE[0] <= from_longitude <= VIETNAM_LONGITUDE_RANGE[1]
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "ORIGIN_OUT_OF_RANGE",
                "message": "Vị trí xuất phát cần nằm trong lãnh thổ Việt Nam để gợi ý tuyến đường.",
                "details": {"latitude": from_latitude, "longitude": from_longitude},
            },
        )

    location = db.scalar(
        select(TourismLocation).where(
            TourismLocation.slug == destination,
            *public_location_filters(),
        )
    )
    if location is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "LOCATION_NOT_FOUND",
                "message": "Không tìm thấy điểm đến.",
                "details": {"destination": destination},
            },
        )

    origin = GeoPoint(longitude=from_longitude, latitude=from_latitude)
    try:
        route = get_driving_route(origin, location.geom)
    except RouteNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "ROUTE_NOT_FOUND",
                "message": "Không tìm thấy tuyến đường bộ phù hợp tới điểm này.",
                "details": None,
            },
        ) from exc
    except RoutingUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "ROUTING_UNAVAILABLE",
                "message": "Dịch vụ chỉ đường tạm thời không phản hồi. Vui lòng thử lại hoặc mở bằng ứng dụng bản đồ.",
                "details": None,
            },
        ) from exc

    return RouteResponse(
        origin=Coordinate(latitude=from_latitude, longitude=from_longitude),
        destination=RouteDestination(
            slug=location.slug,
            name=location.name,
            latitude=location.geom.latitude,
            longitude=location.geom.longitude,
        ),
        distance_m=round(route.distance_m, 1),
        duration_s=round(route.duration_s, 1),
        geometry=LineStringGeometryRead(coordinates=route.coordinates),
    )
