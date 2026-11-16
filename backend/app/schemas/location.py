from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.schemas.product import ProductListItem


class LocationTypeOption(BaseModel):
    value: str
    label: str


class LocationFilterOptions(BaseModel):
    types: list[LocationTypeOption]
    districts: list[str]


class LocationListItem(BaseModel):
    id: int
    name: str
    slug: str
    type: str
    type_label: str
    kind: Literal["attraction", "shop"] = "attraction"
    district: str
    address: str
    latitude: float
    longitude: float
    opening_hours: str | None
    ticket_price: float | None
    services: list[str]
    description: str | None
    rating_avg: float
    primary_image_url: str | None


class LocationListResponse(BaseModel):
    items: list[LocationListItem]
    page: int
    page_size: int
    total: int


class LocationImageRead(BaseModel):
    id: int
    image_url: str
    is_primary: bool
    sort_order: int
    # Ảnh lấy từ web để minh họa có ghi nguồn; ảnh chủ thể tự tải lên thì để trống.
    source_url: str | None = None
    credit: str | None = None
    license: str | None = None


class LocationSubjectRead(BaseModel):
    id: int
    name: str
    district: str


class MapSubjectRead(BaseModel):
    id: int
    name: str
    district: str


class MapProductRead(BaseModel):
    id: int
    name: str
    slug: str
    star: int
    primary_image_url: str | None
    # Vai trò của sản phẩm tại điểm: produced_here, sold_here hoặc displayed.
    role: Literal["produced_here", "sold_here", "displayed"] = "sold_here"


class ProductLocationItem(LocationListItem):
    """Điểm bán hoặc giới thiệu một sản phẩm, kèm vai trò của sản phẩm tại điểm."""

    role: Literal["produced_here", "sold_here", "displayed"]


class ProductLocationResponse(BaseModel):
    product_id: int
    product_name: str
    product_slug: str
    items: list[ProductLocationItem]


class PublicSubjectDetail(BaseModel):
    """Chủ thể đã duyệt cùng mọi điểm và sản phẩm công khai của chủ thể đó."""

    id: int
    name: str
    district: str
    address: str
    locations: list[LocationListItem]
    products: list[ProductListItem]


class LocationDetail(LocationListItem):
    contact_phone: str | None
    website: str | None
    source_url: str | None
    views: int
    images: list[LocationImageRead]
    subject: LocationSubjectRead | None
    products: list[ProductListItem]
    updated_at: datetime


class PointGeometryRead(BaseModel):
    type: Literal["Point"] = "Point"
    coordinates: tuple[float, float]


class MapFeatureProperties(BaseModel):
    id: int
    slug: str
    name: str
    type: str
    type_label: str
    kind: Literal["attraction", "shop"] = "attraction"
    district: str
    address: str
    opening_hours: str | None
    ticket_price: float | None
    services: list[str] = []
    description: str | None = None
    contact_phone: str | None = None
    website: str | None = None
    rating_avg: float
    primary_image_url: str | None
    subject: MapSubjectRead | None = None
    products: list[MapProductRead] = []


class MapFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    geometry: PointGeometryRead
    properties: MapFeatureProperties


class MapFeatureCollection(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[MapFeature]


class Coordinate(BaseModel):
    latitude: float
    longitude: float


class NearbyLocation(LocationListItem):
    distance_m: float


class NearbyLocationResponse(BaseModel):
    origin: Coordinate
    radius_m: float
    items: list[NearbyLocation]


class LineStringGeometryRead(BaseModel):
    type: Literal["LineString"] = "LineString"
    coordinates: list[tuple[float, float]]


class RouteDestination(BaseModel):
    slug: str
    name: str
    latitude: float
    longitude: float


class RouteResponse(BaseModel):
    provider: Literal["OSRM"] = "OSRM"
    profile: Literal["driving"] = "driving"
    origin: Coordinate
    destination: RouteDestination
    distance_m: float
    duration_s: float
    geometry: LineStringGeometryRead
