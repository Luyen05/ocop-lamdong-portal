from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.product import Product


class DataSource(Base):
    """Nguon tai lieu dung de doi chieu va xac minh du lieu OCOP."""

    __tablename__ = "data_sources"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    document_number: Mapped[str | None] = mapped_column(String(100))
    issuing_body: Mapped[str | None] = mapped_column(String(255))
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    published_at: Mapped[date | None] = mapped_column(Date)
    source_url: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    local_path: Mapped[str | None] = mapped_column(String(500))
    sha256: Mapped[str | None] = mapped_column(String(64))
    retrieved_at: Mapped[date] = mapped_column(Date, nullable=False)

    product_links: Mapped[list[ProductSource]] = relationship(
        back_populates="source",
        cascade="all, delete-orphan",
    )


class ProductSource(Base):
    """Chung cu lien ket mot san pham voi mot nguon tai lieu."""

    __tablename__ = "product_sources"

    product_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("ocop_products.id", ondelete="CASCADE"),
        primary_key=True,
    )
    source_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("data_sources.id", ondelete="CASCADE"),
        primary_key=True,
    )
    evidence_role: Mapped[str] = mapped_column(
        String(30),
        primary_key=True,
        default="recognition",
    )
    verification_level: Mapped[str] = mapped_column(String(2), nullable=False)
    original_address: Mapped[str | None] = mapped_column(Text)
    verified_at: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    product: Mapped[Product] = relationship(back_populates="source_links")
    source: Mapped[DataSource] = relationship(back_populates="product_links")
