from pydantic import BaseModel

from app.schemas.location import LocationListItem


class RouteListItem(BaseModel):
    id: int
    slug: str
    name: str
    description: str | None
    duration_text: str | None
    stop_count: int


class RouteStopRead(BaseModel):
    # Thứ tự hiển thị 1, 2, 3... theo các chặng còn công khai.
    position: int
    note: str | None
    location: LocationListItem


class RouteDetail(RouteListItem):
    stops: list[RouteStopRead]
