from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Table,
    Text,
    desc,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.geometry import GeoPoint, PointGeometry

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.subject import Subject
    from app.models.user import User


# Trạng thái kiểm duyệt, cùng quy trình với sản phẩm (database/migrations/009, 011).
# archived: điểm đã duyệt được ngừng hiển thị theo yêu cầu của chủ thể.
LOCATION_STATUSES = ("draft", "pending", "needs_revision", "approved", "rejected", "archived")
# Trạng thái cho phép thiếu vị trí, xã/phường, địa chỉ (đang soạn hoặc đang bổ sung).
LOCATION_INCOMPLETE_STATUSES = ("draft", "needs_revision")
# Cách lấy vị trí: admin_import là dữ liệu nhóm nhập từ nguồn công khai, còn lại do chủ thể khai báo.
LOCATION_SOURCES = ("admin_import", "map_pin", "device_gps", "coordinates", "google_maps_link")
CHANGE_REQUEST_TYPES = ("update", "delete")
CHANGE_REQUEST_STATUSES = ("pending", "needs_revision", "approved", "rejected", "cancelled")


def _in(column: str, values: tuple[str, ...]) -> str:
    return f"{column} IN ({', '.join(repr(value) for value in values)})"


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
    __table_args__ = (
        CheckConstraint(_in("status", LOCATION_STATUSES), name="tourism_locations_status_check"),
        CheckConstraint(_in("location_source", LOCATION_SOURCES), name="tourism_locations_location_source_check"),
        CheckConstraint(
            "location_accuracy_m IS NULL OR location_accuracy_m >= 0",
            name="tourism_locations_location_accuracy_check",
        ),
        CheckConstraint("version >= 1", name="tourism_locations_version_check"),
        CheckConstraint(
            f"{_in('status', LOCATION_INCOMPLETE_STATUSES)}"
            " OR (geom IS NOT NULL AND district IS NOT NULL AND address IS NOT NULL)",
            name="tourism_locations_required_fields_check",
        ),
    )

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True)
    subject_id: Mapped[int | None] = mapped_column(
        ID_TYPE,
        ForeignKey("subjects.id", ondelete="SET NULL"),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    # Chỉ trống khi bản nháp chưa khai báo đủ; điểm công khai luôn có đủ (ràng buộc ở trên).
    district: Mapped[str | None] = mapped_column(String(100))
    address: Mapped[str | None] = mapped_column(Text)
    geom: Mapped[GeoPoint | None] = mapped_column(PointGeometry())
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
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    location_source: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="admin_import",
        server_default="admin_import",
    )
    location_accuracy_m: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_by: Mapped[int | None] = mapped_column(
        ID_TYPE,
        ForeignKey("users.id", ondelete="RESTRICT"),
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_note: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
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
    reviewer: Mapped[User | None] = relationship(foreign_keys=[reviewed_by])
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
    change_requests: Mapped[list[TourismLocationChangeRequest]] = relationship(
        back_populates="location",
        cascade="all, delete-orphan",
    )


class LocationImage(Base):
    __tablename__ = "location_images"
    # Giống schema.sql: mỗi điểm tối đa một ảnh chính (để SQLite trong kiểm thử cũng kiểm tra).
    __table_args__ = (
        Index(
            "uq_location_primary_image",
            "location_id",
            unique=True,
            sqlite_where=text("is_primary"),
            postgresql_where=text("is_primary"),
        ),
    )

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True)
    location_id: Mapped[int] = mapped_column(
        ID_TYPE,
        ForeignKey("tourism_locations.id", ondelete="CASCADE"),
        nullable=False,
    )
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Ảnh chủ thể tải lên có đường dẫn lưu trữ; ảnh cũ là link ngoài nên để trống.
    storage_path: Mapped[str | None] = mapped_column(String(500), unique=True)
    alt_text: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    location: Mapped[TourismLocation] = relationship(back_populates="images")


class TourismLocationChangeRequest(Base):
    """Yêu cầu cập nhật hoặc ngừng hiển thị điểm du lịch đã duyệt; điểm cũ vẫn hiển thị tới khi admin duyệt."""

    __tablename__ = "tourism_location_change_requests"
    __table_args__ = (
        CheckConstraint(_in("request_type", CHANGE_REQUEST_TYPES), name="location_change_request_type_check"),
        CheckConstraint(_in("status", CHANGE_REQUEST_STATUSES), name="location_change_request_status_check"),
        CheckConstraint("base_version >= 1", name="location_change_request_base_version_check"),
        CheckConstraint(
            "(request_type = 'update' AND proposed_data IS NOT NULL)"
            " OR (request_type = 'delete' AND proposed_data IS NULL)",
            name="location_change_payload",
        ),
    )

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True)
    location_id: Mapped[int] = mapped_column(
        ID_TYPE,
        ForeignKey("tourism_locations.id", ondelete="CASCADE"),
        nullable=False,
    )
    subject_id: Mapped[int] = mapped_column(
        ID_TYPE,
        ForeignKey("subjects.id", ondelete="RESTRICT"),
        nullable=False,
    )
    request_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # none_as_null: yêu cầu ngừng hiển thị lưu NULL thật (không phải JSON null) để khớp ràng buộc
    # location_change_payload.
    proposed_data: Mapped[dict | None] = mapped_column(JSON(none_as_null=True))
    reason: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    base_version: Mapped[int] = mapped_column(Integer, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    reviewed_by: Mapped[int | None] = mapped_column(
        ID_TYPE,
        ForeignKey("users.id", ondelete="RESTRICT"),
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_note: Mapped[str | None] = mapped_column(Text)
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

    location: Mapped[TourismLocation] = relationship(back_populates="change_requests")
    subject: Mapped[Subject] = relationship()
    reviewer: Mapped[User | None] = relationship(foreign_keys=[reviewed_by])
