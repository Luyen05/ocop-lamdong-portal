from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.models.location import TourismLocation
from app.models.route import TourismRoute, TourismRouteStop
from app.schemas.error import ErrorResponse
from app.schemas.route import RouteDetail, RouteListItem, RouteStopRead
from app.services.location_catalog import public_location_filters, to_location_list_item


# Tuyến tham quan. Dùng tiền tố /tours để không trùng /map/route (chỉ đường OSRM).
router = APIRouter(prefix="/tours", tags=["Tours"])


def _visible_stops(db: Session, route: TourismRoute) -> list[TourismRouteStop]:
    """Chặng còn công khai (điểm đã duyệt, chủ thể không bị khóa), giữ nguyên thứ tự."""

    visible_ids = set(
        db.scalars(
            select(TourismLocation.id).where(
                TourismLocation.id.in_([stop.location_id for stop in route.stops]),
                *public_location_filters(),
            )
        ).all()
    )
    return [stop for stop in route.stops if stop.location_id in visible_ids]


@router.get("", response_model=list[RouteListItem])
def list_tours(db: Session = Depends(get_db)) -> list[RouteListItem]:
    routes = db.scalars(
        select(TourismRoute)
        .where(TourismRoute.status == "published")
        .options(selectinload(TourismRoute.stops))
        .order_by(TourismRoute.name.asc(), TourismRoute.id.asc())
    ).all()
    items = []
    for route in routes:
        stop_count = len(_visible_stops(db, route))
        if stop_count:
            items.append(
                RouteListItem(
                    id=route.id,
                    slug=route.slug,
                    name=route.name,
                    description=route.description,
                    duration_text=route.duration_text,
                    stop_count=stop_count,
                )
            )
    return items


@router.get(
    "/{slug}",
    response_model=RouteDetail,
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorResponse}},
)
def get_tour(slug: str, db: Session = Depends(get_db)) -> RouteDetail:
    route = db.scalar(
        select(TourismRoute)
        .where(TourismRoute.slug == slug, TourismRoute.status == "published")
        .options(
            selectinload(TourismRoute.stops)
            .selectinload(TourismRouteStop.location)
            .selectinload(TourismLocation.images)
        )
    )
    stops = _visible_stops(db, route) if route is not None else []
    if route is None or not stops:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "ROUTE_NOT_FOUND",
                "message": "Không tìm thấy tuyến tham quan.",
                "details": {"slug": slug},
            },
        )
    return RouteDetail(
        id=route.id,
        slug=route.slug,
        name=route.name,
        description=route.description,
        duration_text=route.duration_text,
        stop_count=len(stops),
        stops=[
            RouteStopRead(
                position=index,
                note=stop.note,
                location=to_location_list_item(stop.location),
            )
            for index, stop in enumerate(stops, start=1)
        ],
    )
