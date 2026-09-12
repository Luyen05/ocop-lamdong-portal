from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    SmallInteger,
    String,
    Text,
    desc,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.data_source import ProductSource
    from app.models.subject import Subject
    from app.models.user import User


class Product(Base):
    __tablename__ = "ocop_products"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
    )
    subject_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("subjects.id", ondelete="RESTRICT"),
        nullable=False,
    )
    category_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    star: Mapped[int | None] = mapped_column(SmallInteger)
    price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0"),
    )
    unit: Mapped[str | None] = mapped_column(String(50))
    cert_code: Mapped[str | None] = mapped_column(String(100), unique=True)
    cert_year: Mapped[int | None] = mapped_column(SmallInteger)
    cert_issued_at: Mapped[date | None] = mapped_column()
    cert_expires_at: Mapped[date | None] = mapped_column()
    issuing_authority: Mapped[str | None] = mapped_column(String(255))
    certificate_url: Mapped[str | None] = mapped_column(String(500))
    certificate_storage_path: Mapped[str | None] = mapped_column(String(500))
    vietgap_code: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    story: Mapped[str | None] = mapped_column(Text)
    ingredients: Mapped[str | None] = mapped_column(Text)
    usage_instructions: Mapped[str | None] = mapped_column(Text)
    rating_avg: Mapped[Decimal] = mapped_column(
        Numeric(3, 2),
        nullable=False,
        default=Decimal("0"),
    )
    views: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_demo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_by: Mapped[int | None] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
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

    subject: Mapped[Subject] = relationship(back_populates="products")
    category: Mapped[Category] = relationship()
    reviewer: Mapped[User | None] = relationship(foreign_keys=[reviewed_by])
    images: Mapped[list[ProductImage]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        order_by=lambda: (
            desc(ProductImage.is_primary),
            ProductImage.sort_order,
            ProductImage.id,
        ),
    )
    change_requests: Mapped[list[ProductChangeRequest]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )
    source_links: Mapped[list[ProductSource]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )


class ProductImage(Base):
    __tablename__ = "product_images"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
    )
    product_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("ocop_products.id", ondelete="CASCADE"),
        nullable=False,
    )
    storage_path: Mapped[str] = mapped_column(
        String(500),
        unique=True,
        nullable=False,
        default=lambda: f"external/product-images/{uuid4()}",
    )
    image_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    alt_text: Mapped[str | None] = mapped_column(String(255))
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    product: Mapped[Product] = relationship(back_populates="images")


class ProductChangeRequest(Base):
    __tablename__ = "product_change_requests"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
    )
    product_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("ocop_products.id", ondelete="CASCADE"),
        nullable=False,
    )
    subject_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("subjects.id", ondelete="RESTRICT"),
        nullable=False,
    )
    request_type: Mapped[str] = mapped_column(String(20), nullable=False)
    proposed_data: Mapped[dict | None] = mapped_column(JSON)
    reason: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    base_version: Mapped[int] = mapped_column(Integer, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    reviewed_by: Mapped[int | None] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
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

    product: Mapped[Product] = relationship(back_populates="change_requests")
    reviewer: Mapped[User | None] = relationship(foreign_keys=[reviewed_by])
