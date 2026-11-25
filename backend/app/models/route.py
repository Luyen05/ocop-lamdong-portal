from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, SmallInteger, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.location import ID_TYPE, TourismLocation

ROUTE_STATUSES = ("draft", "published", "archived")


class TourismRoute(Base):
    """Tuyến tham quan: chuỗi điểm theo thứ tự, chỉ tuyến published hiện công khai."""

    __tablename__ = "tourism_routes"
    __table_args__ = (
        CheckConstraint(
            f"status IN ({', '.join(repr(value) for value in ROUTE_STATUSES)})",
            name="tourism_routes_status_check",
        ),
    )

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    duration_text: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft", server_default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    stops: Mapped[list[TourismRouteStop]] = relationship(
        back_populates="route",
        cascade="all, delete-orphan",
        order_by=lambda: TourismRouteStop.position,
    )


class TourismRouteStop(Base):
    __tablename__ = "tourism_route_stops"
    __table_args__ = (
        CheckConstraint("position >= 1", name="tourism_route_stops_position_check"),
        UniqueConstraint("route_id", "position", name="uq_tourism_route_stops_position"),
        Index("idx_tourism_route_stops_location", "location_id"),
    )

    route_id: Mapped[int] = mapped_column(
        ID_TYPE, ForeignKey("tourism_routes.id", ondelete="CASCADE"), primary_key=True
    )
    location_id: Mapped[int] = mapped_column(
        ID_TYPE, ForeignKey("tourism_locations.id", ondelete="CASCADE"), primary_key=True
    )
    position: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    note: Mapped[str | None] = mapped_column(Text)

    route: Mapped[TourismRoute] = relationship(back_populates="stops")
    location: Mapped[TourismLocation] = relationship()
