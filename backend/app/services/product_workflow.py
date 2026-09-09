from __future__ import annotations

import re
import unicodedata
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.category import Category
from app.models.product import Product, ProductImage
from app.models.subject import Subject
from app.models.user import User
from app.schemas.product_management import (
    ManagedProductCategoryRead,
    ManagedProductImageRead,
    ManagedProductRead,
    ManagedProductSubjectRead,
    ProductWritePayload,
)


def workflow_error(
    status_code: int,
    code: str,
    message: str,
    details: dict | None = None,
) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message, "details": details},
    )


def get_approved_subject(db: Session, user: User) -> Subject:
    subject = db.scalar(
        select(Subject).where(
            Subject.user_id == user.id,
            Subject.status == "approved",
        )
    )
    if subject is None:
        raise workflow_error(
            status.HTTP_403_FORBIDDEN,
            "APPROVED_SUBJECT_REQUIRED",
            "Chỉ chủ thể đã được duyệt mới có thể quản lý sản phẩm.",
        )
    return subject


def product_load_options() -> tuple:
    return (
        joinedload(Product.category),
        joinedload(Product.subject),
        selectinload(Product.images),
    )


def get_owned_product(db: Session, product_id: int, subject_id: int) -> Product:
    product = db.scalar(
        select(Product)
        .where(Product.id == product_id, Product.subject_id == subject_id)
        .options(*product_load_options())
    )
    if product is None:
        raise workflow_error(
            status.HTTP_404_NOT_FOUND,
            "PRODUCT_NOT_FOUND",
            "Không tìm thấy sản phẩm thuộc chủ thể hiện tại.",
            {"product_id": product_id},
        )
    return product


def get_product_for_admin(db: Session, product_id: int, *, lock: bool = False) -> Product:
    statement = select(Product).where(Product.id == product_id)
    if lock:
        statement = statement.with_for_update()
    product = db.scalar(statement.options(*product_load_options()))
    if product is None:
        raise workflow_error(
            status.HTTP_404_NOT_FOUND,
            "PRODUCT_NOT_FOUND",
            "Không tìm thấy sản phẩm.",
            {"product_id": product_id},
        )
    return product


def get_category(db: Session, category_id: int) -> Category:
    category = db.get(Category, category_id)
    if category is None:
        raise workflow_error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "CATEGORY_NOT_FOUND",
            "Danh mục sản phẩm không tồn tại.",
            {"category_id": category_id},
        )
    return category


def build_unique_slug(db: Session, name: str, product_id: int | None = None) -> str:
    normalized = unicodedata.normalize("NFKD", name.replace("đ", "d").replace("Đ", "D"))
    base = re.sub(r"[^a-z0-9]+", "-", normalized.encode("ascii", "ignore").decode().lower())
    base = base.strip("-") or "san-pham"
    candidate = base
    suffix = 2
    while db.scalar(
        select(Product.id).where(
            Product.slug == candidate,
            Product.id != product_id if product_id is not None else True,
        )
    ) is not None:
        candidate = f"{base}-{suffix}"
        suffix += 1
    return candidate


def replace_product_images(product: Product, payload: ProductWritePayload) -> None:
    product.images.clear()
    for image in payload.images:
        product.images.append(
            ProductImage(
                image_url=image.image_url,
                is_primary=image.is_primary,
                sort_order=image.sort_order,
            )
        )


def apply_product_payload(
    db: Session,
    product: Product,
    payload: ProductWritePayload,
    *,
    update_slug: bool,
) -> None:
    product.category = get_category(db, payload.category_id)
    if update_slug:
        product.slug = build_unique_slug(db, payload.name, product.id)
    for field, value in payload.model_dump(
        exclude={"category_id", "images", "cert_issued_at", "cert_expires_at"}
    ).items():
        setattr(product, field, value)
    product.cert_issued_at = payload.cert_issued_at
    product.cert_expires_at = payload.cert_expires_at
    product.cert_year = payload.cert_issued_at.year
    replace_product_images(product, payload)


def validate_certificate_is_current(product: Product) -> None:
    if product.cert_expires_at is None or product.cert_expires_at < date.today():
        raise workflow_error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "CERTIFICATE_EXPIRED",
            "Giấy chứng nhận đã hết hạn hoặc chưa có ngày hết hạn hợp lệ.",
            {"cert_expires_at": str(product.cert_expires_at)},
        )


def to_managed_product_read(product: Product) -> ManagedProductRead:
    return ManagedProductRead(
        id=product.id,
        subject_id=product.subject_id,
        category_id=product.category_id,
        name=product.name,
        slug=product.slug,
        star=product.star,
        price=product.price,
        unit=product.unit,
        cert_code=product.cert_code,
        cert_issued_at=product.cert_issued_at,
        cert_expires_at=product.cert_expires_at,
        issuing_authority=product.issuing_authority,
        certificate_url=product.certificate_url,
        vietgap_code=product.vietgap_code,
        description=product.description,
        story=product.story,
        ingredients=product.ingredients,
        usage_instructions=product.usage_instructions,
        status=product.status,
        submitted_at=product.submitted_at,
        reviewed_at=product.reviewed_at,
        moderation_note=product.review_note,
        version=product.version,
        category=ManagedProductCategoryRead(
            id=product.category.id,
            name=product.category.name,
            slug=product.category.slug,
        ),
        subject=ManagedProductSubjectRead(
            id=product.subject.id,
            name=product.subject.name,
            representative=product.subject.representative,
            tax_code=product.subject.tax_code,
        ),
        images=[
            ManagedProductImageRead(
                id=image.id,
                image_url=image.image_url,
                is_primary=image.is_primary,
                sort_order=image.sort_order,
            )
            for image in product.images
        ],
        created_at=product.created_at,
        updated_at=product.updated_at,
    )
