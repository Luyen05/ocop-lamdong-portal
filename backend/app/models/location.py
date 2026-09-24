from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Table,
    Text,
    desc,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.geometry import GeoPoint, PointGeometry

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.subject import Subject


ID_TYPE = BigInteger().with_variant(Integer, "sqlite")

location_ocop_products = Table(
    "location_ocop_products",
    Base.metadata,
    Column(
        "location_id",
        ID_TYPE,
        ForeignKey("tourism_locations.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "product_id",
        ID_TYPE,
        ForeignKey("ocop_products.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class TourismLocation(Base):
    """Điểm du lịch nông nghiệp (trang trại, nhà vườn, làng nghề...) có tọa độ."""

    __tablename__ = "tourism_locations"

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True)
    subject_id: Mapped[int | None] = mapped_column(
        ID_TYPE,
        ForeignKey("subjects.id", ondelete="SET NULL"),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    district: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    geom: Mapped[GeoPoint] = mapped_column(PointGeometry(), nullable=False)
    contact_phone: Mapped[str | None] = mapped_column(String(20))
    opening_hours: Mapped[str | None] = mapped_column(String(100))
    ticket_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    services: Mapped[list[str]] = mapped_column(
        ARRAY(Text).with_variant(JSON(), "sqlite"),
        nullable=False,
        default=list,
    )
    description: Mapped[str | None] = mapped_column(Text)
    website: Mapped[str | None] = mapped_column(String(500))
    source_url: Mapped[str | None] = mapped_column(Text)
    rating_avg: Mapped[Decimal] = mapped_column(
        Numeric(3, 2),
        nullable=False,
        default=Decimal("0"),
    )
    views: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    subject: Mapped[Subject | None] = relationship()
    images: Mapped[list[LocationImage]] = relationship(
        back_populates="location",
        cascade="all, delete-orphan",
        order_by=lambda: (
            desc(LocationImage.is_primary),
            LocationImage.sort_order,
            LocationImage.id,
        ),
    )
    products: Mapped[list[Product]] = relationship(secondary=location_ocop_products)


class LocationImage(Base):
    __tablename__ = "location_images"

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True)
    location_id: Mapped[int] = mapped_column(
        ID_TYPE,
        ForeignKey("tourism_locations.id", ondelete="CASCADE"),
        nullable=False,
    )
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    location: Mapped[TourismLocation] = relationship(back_populates="images")
