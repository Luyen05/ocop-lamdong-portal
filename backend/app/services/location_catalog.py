"""Quy tắc công khai và chuyển đổi dữ liệu điểm du lịch nông nghiệp."""

from __future__ import annotations

from typing import Literal

from sqlalchemy import func, or_

from app.models.location import TourismLocation
from app.schemas.location import (
    LocationListItem,
    MapFeature,
    MapFeatureProperties,
    PointGeometryRead,
)
from app.schemas.product import ProductRelatedLocation


# Danh mục loại hình dùng chung cho API, bộ lọc và công cụ sinh seed
# (tools/build_tourism_seed.py). Thêm loại hình mới phải cập nhật cả hai nơi.
LOCATION_TYPES: dict[str, str] = {
    "tea_coffee_farm": "Đồi chè & cà phê",
    "fruit_garden": "Vườn trái cây",
    "flower_garden": "Vườn hoa",
    "dairy_farm": "Nông trại chăn nuôi",
    "vegetable_farm": "Nông trại rau & nấm",
    "craft_village": "Làng nghề",
    "farmstay": "Farmstay & nghỉ dưỡng",
    "other": "Loại hình khác",
}
LocationTypeCode = Literal[
    "tea_coffee_farm",
    "fruit_garden",
    "flower_garden",
    "dairy_farm",
    "vegetable_farm",
    "craft_village",
    "farmstay",
    "other",
]
PUBLIC_LOCATION_STATUS = "approved"


def location_type_label(code: str) -> str:
    return LOCATION_TYPES.get(code, LOCATION_TYPES["other"])


def public_location_filters(
    *,
    search: str | None = None,
    location_type: str | None = None,
    district: str | None = None,
) -> list:
    """Điều kiện chung cho danh sách, bản đồ và tìm điểm gần: chỉ điểm đã duyệt."""

    filters: list = [TourismLocation.status == PUBLIC_LOCATION_STATUS]
    if search and search.strip():
        keyword = f"%{search.strip()}%"
        filters.append(
            or_(
                TourismLocation.name.ilike(keyword),
                TourismLocation.description.ilike(keyword),
                TourismLocation.address.ilike(keyword),
            )
        )
    if location_type:
        filters.append(TourismLocation.type == location_type)
    if district and district.strip():
        filters.append(func.lower(TourismLocation.district) == func.lower(district.strip()))
    return filters


def primary_image_url(location: TourismLocation) -> str | None:
    return location.images[0].image_url if location.images else None


def to_location_list_item(location: TourismLocation) -> LocationListItem:
    return LocationListItem(
        id=location.id,
        name=location.name,
        slug=location.slug,
        type=location.type,
        type_label=location_type_label(location.type),
        district=location.district,
        address=location.address,
        latitude=location.geom.latitude,
        longitude=location.geom.longitude,
        opening_hours=location.opening_hours,
        ticket_price=float(location.ticket_price) if location.ticket_price is not None else None,
        services=list(location.services or []),
        description=location.description,
        rating_avg=float(location.rating_avg or 0),
        primary_image_url=primary_image_url(location),
    )


def to_product_related_location(location: TourismLocation) -> ProductRelatedLocation:
    return ProductRelatedLocation(
        id=location.id,
        name=location.name,
        slug=location.slug,
        type_label=location_type_label(location.type),
        district=location.district,
    )


def to_map_feature(location: TourismLocation) -> MapFeature:
    return MapFeature(
        geometry=PointGeometryRead(
            coordinates=(location.geom.longitude, location.geom.latitude),
        ),
        properties=MapFeatureProperties(
            id=location.id,
            slug=location.slug,
            name=location.name,
            type=location.type,
            type_label=location_type_label(location.type),
            district=location.district,
            address=location.address,
            opening_hours=location.opening_hours,
            ticket_price=(
                float(location.ticket_price) if location.ticket_price is not None else None
            ),
            rating_avg=float(location.rating_avg or 0),
            primary_image_url=primary_image_url(location),
        ),
    )
