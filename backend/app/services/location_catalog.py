"""Quy tắc công khai và chuyển đổi dữ liệu điểm du lịch nông nghiệp."""

from __future__ import annotations

from typing import Literal

from sqlalchemy import exists, func, or_, select

from app.core.geometry import GeoPoint
from app.core.search import LIKE_ESCAPE, contains_pattern
from app.models.category import Category
from app.models.location import TourismLocation, location_ocop_products
from app.models.product import Product
from app.models.subject import Subject
from app.models.user import User
from app.services.visibility import account_allows_public_content
from app.schemas.location import (
    LocationListItem,
    MapFeature,
    MapSubjectRead,
    MapFeatureProperties,
    PointGeometryRead,
)


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
    "ocop_store": "Cửa hàng OCOP",
    "workshop": "Cơ sở sản xuất",
    "other": "Loại hình khác",
}
# Loại hình thuộc nhóm "cửa hàng" (nơi mua sản phẩm); các loại còn lại là điểm du lịch.
# Nhóm được suy ra từ loại hình nên không cần thêm cột và không thể lệch nhau.
SHOP_LOCATION_TYPES: frozenset[str] = frozenset({"ocop_store", "workshop"})
LocationKind = Literal["attraction", "shop"]
# Giá trị của tham số `kind` trong API: thêm "all" để lấy cả hai nhóm.
LocationKindFilter = Literal["attraction", "shop", "all"]
LocationTypeCode = Literal[
    "tea_coffee_farm",
    "fruit_garden",
    "flower_garden",
    "dairy_farm",
    "vegetable_farm",
    "craft_village",
    "farmstay",
    "ocop_store",
    "workshop",
    "other",
]
PUBLIC_LOCATION_STATUS = "approved"


def kind_filter_value(kind: LocationKindFilter) -> LocationKind | None:
    return None if kind == "all" else kind


def location_kind(code: str) -> LocationKind:
    return "shop" if code in SHOP_LOCATION_TYPES else "attraction"


def location_type_label(code: str) -> str:
    return LOCATION_TYPES.get(code, LOCATION_TYPES["other"])


def public_location_filters(
    *,
    search: str | None = None,
    location_type: str | None = None,
    district: str | None = None,
    kind: LocationKind | None = None,
    product_id: int | None = None,
    category_slug: str | None = None,
    subject_id: int | None = None,
) -> list:
    """Điều kiện chung cho danh sách, bản đồ và tìm điểm gần: chỉ điểm đã duyệt.

    Điểm của chủ thể có tài khoản bị khóa không hiện công khai; điểm admin nhập sẵn
    (không gắn chủ thể) vẫn hiện.
    """

    subject_account_active = (
        select(User.id)
        .join(Subject, Subject.user_id == User.id)
        .where(Subject.id == TourismLocation.subject_id, account_allows_public_content())
        .correlate(TourismLocation)
        .exists()
    )
    filters: list = [
        TourismLocation.status == PUBLIC_LOCATION_STATUS,
        or_(TourismLocation.subject_id.is_(None), subject_account_active),
    ]
    if search and search.strip():
        keyword = contains_pattern(search)
        filters.append(
            or_(
                TourismLocation.name.ilike(keyword, escape=LIKE_ESCAPE),
                TourismLocation.description.ilike(keyword, escape=LIKE_ESCAPE),
                TourismLocation.address.ilike(keyword, escape=LIKE_ESCAPE),
            )
        )
    if location_type:
        filters.append(TourismLocation.type == location_type)
    if kind == "shop":
        filters.append(TourismLocation.type.in_(SHOP_LOCATION_TYPES))
    elif kind == "attraction":
        filters.append(TourismLocation.type.not_in(SHOP_LOCATION_TYPES))
    if district and district.strip():
        filters.append(func.lower(TourismLocation.district) == func.lower(district.strip()))
    if subject_id is not None:
        filters.append(TourismLocation.subject_id == subject_id)
    if product_id is not None or category_slug:
        filters.append(_has_public_product(product_id=product_id, category_slug=category_slug))
    return filters


def _has_public_product(*, product_id: int | None, category_slug: str | None):
    """Điểm có gắn ít nhất một sản phẩm công khai (đúng sản phẩm hoặc đúng nhóm được chọn)."""

    # Nhập muộn để tránh vòng nhập: routes.products dùng chính module này.
    from app.api.routes.products import public_product_filters

    conditions = [location_ocop_products.c.location_id == TourismLocation.id, *public_product_filters()]
    if product_id is not None:
        conditions.append(Product.id == product_id)
    if category_slug:
        conditions.append(Category.slug == category_slug)
    return (
        exists(
            select(1)
            .select_from(location_ocop_products)
            .join(Product, Product.id == location_ocop_products.c.product_id)
            .join(Subject, Subject.id == Product.subject_id)
            .join(Category, Category.id == Product.category_id)
            .where(*conditions)
        )
        .correlate(TourismLocation)
    )


def public_point(location: TourismLocation) -> GeoPoint:
    """Tọa độ của điểm công khai; database bắt buộc có khi điểm không còn là bản nháp."""

    if location.geom is None:
        raise ValueError(f"Điểm du lịch {location.id} chưa có tọa độ.")
    return location.geom


def primary_image_url(location: TourismLocation) -> str | None:
    return location.images[0].image_url if location.images else None


def to_location_list_item(location: TourismLocation) -> LocationListItem:
    return LocationListItem(
        id=location.id,
        name=location.name,
        slug=location.slug,
        type=location.type,
        type_label=location_type_label(location.type),
        kind=location_kind(location.type),
        district=location.district or "",
        address=location.address or "",
        latitude=public_point(location).latitude,
        longitude=public_point(location).longitude,
        opening_hours=location.opening_hours,
        ticket_price=float(location.ticket_price) if location.ticket_price is not None else None,
        services=list(location.services or []),
        description=location.description,
        rating_avg=float(location.rating_avg or 0),
        primary_image_url=primary_image_url(location),
    )


def to_map_feature(location: TourismLocation) -> MapFeature:
    return MapFeature(
        geometry=PointGeometryRead(
            coordinates=(public_point(location).longitude, public_point(location).latitude),
        ),
        properties=MapFeatureProperties(
            id=location.id,
            slug=location.slug,
            name=location.name,
            type=location.type,
            type_label=location_type_label(location.type),
            kind=location_kind(location.type),
            district=location.district or "",
            address=location.address or "",
            opening_hours=location.opening_hours,
            ticket_price=(
                float(location.ticket_price) if location.ticket_price is not None else None
            ),
            services=list(location.services or []),
            description=location.description,
            rating_avg=float(location.rating_avg or 0),
            primary_image_url=primary_image_url(location),
            subject=(
                MapSubjectRead(
                    id=location.subject.id,
                    name=location.subject.name,
                    district=location.subject.district,
                )
                if location.subject is not None and location.subject.status == "approved"
                else None
            ),
        ),
    )
