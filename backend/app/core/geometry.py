"""Kiểu dữ liệu và hàm không gian dùng chung cho PostGIS.

Cột ``GEOMETRY(Point, 4326)`` được đọc/ghi qua ``PointGeometry``. Trên PostgreSQL,
giá trị đi qua ``ST_GeomFromText``/``ST_AsText`` và khoảng cách được tính bằng
``ST_Distance``/``ST_DWithin`` trên kiểu ``geography`` (đơn vị mét). SQLite chỉ dùng
trong kiểm thử: điểm được lưu dạng WKT và khoảng cách dùng hàm Haversine đăng ký
qua ``register_sqlite_geo_functions``.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any

from sqlalchemy import Boolean, Float
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import FunctionElement
from sqlalchemy.types import UserDefinedType


SRID = 4326
EARTH_RADIUS_METERS = 6_371_008.8
_WKT_POINT_PATTERN = re.compile(
    r"^\s*(?:SRID=\d+;)?\s*POINT\s*\(\s*(?P<lng>[-+]?[\d.]+(?:[eE][-+]?\d+)?)"
    r"\s+(?P<lat>[-+]?[\d.]+(?:[eE][-+]?\d+)?)\s*\)\s*$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class GeoPoint:
    """Tọa độ WGS84; thứ tự lưu trữ theo chuẩn GeoJSON là kinh độ trước, vĩ độ sau."""

    longitude: float
    latitude: float

    def __post_init__(self) -> None:
        if not -180 <= self.longitude <= 180 or not -90 <= self.latitude <= 90:
            raise ValueError("Tọa độ nằm ngoài phạm vi WGS84.")

    def to_wkt(self) -> str:
        return f"POINT({self.longitude:.7f} {self.latitude:.7f})"

    @classmethod
    def from_wkt(cls, value: str) -> GeoPoint:
        match = _WKT_POINT_PATTERN.match(value)
        if match is None:
            raise ValueError(f"Không đọc được tọa độ điểm: {value!r}")
        return cls(longitude=float(match["lng"]), latitude=float(match["lat"]))


def haversine_meters(first: GeoPoint, second: GeoPoint) -> float:
    lat1, lat2 = math.radians(first.latitude), math.radians(second.latitude)
    delta_lat = lat2 - lat1
    delta_lng = math.radians(second.longitude - first.longitude)
    value = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lng / 2) ** 2
    )
    return 2 * EARTH_RADIUS_METERS * math.asin(min(1.0, math.sqrt(value)))


class _GeomFromText(FunctionElement):
    inherit_cache = True
    name = "geom_from_text"


class _GeomAsText(FunctionElement):
    inherit_cache = True
    name = "geom_as_text"


class PointGeometry(UserDefinedType):
    """Cột ``GEOMETRY(Point, 4326)`` ánh xạ sang ``GeoPoint``."""

    cache_ok = True

    def get_col_spec(self, **kw: Any) -> str:
        return f"GEOMETRY(Point, {SRID})"

    def bind_expression(self, bindvalue):
        return _GeomFromText(bindvalue)

    def column_expression(self, colexpr):
        return _GeomAsText(colexpr)

    def bind_processor(self, dialect):
        def process(value: GeoPoint | None) -> str | None:
            if value is None:
                return None
            if not isinstance(value, GeoPoint):
                raise TypeError("Cột tọa độ chỉ nhận giá trị GeoPoint.")
            return value.to_wkt()

        return process

    def result_processor(self, dialect, coltype):
        def process(value: str | None) -> GeoPoint | None:
            return GeoPoint.from_wkt(value) if value is not None else None

        return process


_GeomAsText.type = PointGeometry()


@compiles(PointGeometry, "sqlite")
def _compile_point_type_sqlite(type_, compiler, **kw) -> str:
    return "TEXT"


@compiles(_GeomFromText)
def _compile_geom_from_text(element, compiler, **kw) -> str:
    return f"ST_GeomFromText({compiler.process(element.clauses, **kw)}, {SRID})"


@compiles(_GeomFromText, "sqlite")
def _compile_geom_from_text_sqlite(element, compiler, **kw) -> str:
    return compiler.process(element.clauses, **kw)


@compiles(_GeomAsText)
def _compile_geom_as_text(element, compiler, **kw) -> str:
    return f"ST_AsText({compiler.process(element.clauses, **kw)})"


@compiles(_GeomAsText, "sqlite")
def _compile_geom_as_text_sqlite(element, compiler, **kw) -> str:
    return compiler.process(element.clauses, **kw)


class distance_meters(FunctionElement):
    """Khoảng cách (mét) từ cột điểm tới tọa độ ``(longitude, latitude)``."""

    type = Float()
    inherit_cache = True
    name = "distance_meters"


class within_meters(FunctionElement):
    """Điều kiện cột điểm nằm trong bán kính (mét) quanh ``(longitude, latitude)``."""

    type = Boolean()
    inherit_cache = True
    name = "within_meters"


def _arguments(element, compiler, **kw) -> list[str]:
    return [compiler.process(argument, **kw) for argument in element.clauses]


def _postgis_point(longitude: str, latitude: str) -> str:
    return f"ST_SetSRID(ST_MakePoint({longitude}, {latitude}), {SRID})::geography"


@compiles(distance_meters)
def _compile_distance(element, compiler, **kw) -> str:
    geom, longitude, latitude = _arguments(element, compiler, **kw)
    return f"ST_Distance(({geom})::geography, {_postgis_point(longitude, latitude)})"


@compiles(distance_meters, "sqlite")
def _compile_distance_sqlite(element, compiler, **kw) -> str:
    geom, longitude, latitude = _arguments(element, compiler, **kw)
    return f"ocop_distance_m({geom}, {longitude}, {latitude})"


@compiles(within_meters)
def _compile_within(element, compiler, **kw) -> str:
    geom, longitude, latitude, meters = _arguments(element, compiler, **kw)
    return (
        f"ST_DWithin(({geom})::geography, {_postgis_point(longitude, latitude)}, {meters})"
    )


@compiles(within_meters, "sqlite")
def _compile_within_sqlite(element, compiler, **kw) -> str:
    geom, longitude, latitude, meters = _arguments(element, compiler, **kw)
    return f"(ocop_distance_m({geom}, {longitude}, {latitude}) <= {meters})"


def _sqlite_distance(wkt: str | None, longitude: float, latitude: float) -> float | None:
    if wkt is None:
        return None
    return haversine_meters(GeoPoint.from_wkt(wkt), GeoPoint(longitude, latitude))


def register_sqlite_geo_functions(dbapi_connection, _connection_record=None) -> None:
    """Đăng ký hàm khoảng cách cho kết nối SQLite (chỉ dùng trong kiểm thử)."""

    dbapi_connection.create_function("ocop_distance_m", 3, _sqlite_distance, deterministic=True)
