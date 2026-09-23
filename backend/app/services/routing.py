"""Gợi ý tuyến đường qua dịch vụ OSRM với thời gian chờ giới hạn."""

from __future__ import annotations

import math
from dataclasses import dataclass

import httpx

from app.core.config import get_settings
from app.core.geometry import GeoPoint


MAX_RESPONSE_BYTES = 2 * 1024 * 1024
ROUTE_NOT_FOUND_CODES = {"NoRoute", "NoSegment"}


class RoutingUnavailableError(RuntimeError):
    """Dịch vụ chỉ đường không phản hồi hoặc trả dữ liệu không hợp lệ."""


class RouteNotFoundError(RuntimeError):
    """Không có tuyến đường bộ giữa hai điểm."""


@dataclass(frozen=True)
class RouteResult:
    distance_m: float
    duration_s: float
    coordinates: list[tuple[float, float]]


def _create_client(timeout: float) -> httpx.Client:
    return httpx.Client(
        timeout=timeout,
        follow_redirects=False,
        headers={"User-Agent": "OCOP-Lam-Dong-Portal/1.0"},
    )


def _parse_coordinates(raw: object) -> list[tuple[float, float]]:
    if not isinstance(raw, list) or len(raw) < 2:
        raise RoutingUnavailableError("Dữ liệu tuyến đường không hợp lệ.")
    coordinates: list[tuple[float, float]] = []
    for point in raw:
        if (
            not isinstance(point, list)
            or len(point) < 2
            or not all(isinstance(value, (int, float)) for value in point[:2])
        ):
            raise RoutingUnavailableError("Dữ liệu tuyến đường không hợp lệ.")
        coordinates.append((float(point[0]), float(point[1])))
    return coordinates


def get_driving_route(origin: GeoPoint, destination: GeoPoint) -> RouteResult:
    settings = get_settings()
    url = (
        f"{settings.osrm_base_url}/route/v1/driving/"
        f"{origin.longitude:.6f},{origin.latitude:.6f};"
        f"{destination.longitude:.6f},{destination.latitude:.6f}"
    )
    params = {
        "overview": "full",
        "geometries": "geojson",
        "alternatives": "false",
        "steps": "false",
    }
    try:
        with _create_client(settings.osrm_timeout_seconds) as client:
            response = client.get(url, params=params)
    except httpx.HTTPError as exc:
        raise RoutingUnavailableError("Không thể kết nối dịch vụ chỉ đường.") from exc

    if len(response.content) > MAX_RESPONSE_BYTES:
        raise RoutingUnavailableError("Dữ liệu tuyến đường vượt quá dung lượng cho phép.")
    try:
        payload = response.json()
    except ValueError as exc:
        raise RoutingUnavailableError("Dịch vụ chỉ đường trả dữ liệu không hợp lệ.") from exc
    if not isinstance(payload, dict):
        raise RoutingUnavailableError("Dịch vụ chỉ đường trả dữ liệu không hợp lệ.")

    code = payload.get("code")
    if code in ROUTE_NOT_FOUND_CODES:
        raise RouteNotFoundError("Không tìm thấy tuyến đường phù hợp.")
    routes = payload.get("routes")
    if response.status_code != 200 or code != "Ok" or not isinstance(routes, list) or not routes:
        raise RoutingUnavailableError("Dịch vụ chỉ đường không trả về tuyến hợp lệ.")

    route = routes[0] if isinstance(routes[0], dict) else {}
    geometry = route.get("geometry") if isinstance(route.get("geometry"), dict) else {}
    try:
        distance = float(route["distance"])
        duration = float(route["duration"])
    except (KeyError, TypeError, ValueError) as exc:
        raise RoutingUnavailableError("Dữ liệu tuyến đường không hợp lệ.") from exc
    if not math.isfinite(distance) or not math.isfinite(duration) or distance < 0 or duration < 0:
        raise RoutingUnavailableError("Dữ liệu tuyến đường không hợp lệ.")

    return RouteResult(
        distance_m=distance,
        duration_s=duration,
        coordinates=_parse_coordinates(geometry.get("coordinates")),
    )
