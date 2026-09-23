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


class LocationSubjectRead(BaseModel):
    id: int
    name: str
    district: str


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
    district: str
    address: str
    opening_hours: str | None
    ticket_price: float | None
    rating_avg: float
    primary_image_url: str | None


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
