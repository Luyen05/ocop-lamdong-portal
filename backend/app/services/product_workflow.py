from __future__ import annotations

import re
import unicodedata
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.category import Category
from app.models.data_source import ProductSource
from app.models.product import Product, ProductChangeRequest, ProductImage
from app.models.subject import Subject
from app.models.user import User
from app.schemas.product_management import (
    ManagedProductCategoryRead,
    ManagedProductImageRead,
    ManagedProductRead,
    ManagedProductSubjectRead,
    ProductEvidenceResponse,
    ProductDraftCreate,
    ProductDraftUpdate,
    ProductEvidenceSourceRead,
    ProductSnapshotRead,
    ProductWritePayload,
    ProductChangeRequestRead,
    DataSourceRead,
)
from app.core.config import get_settings


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
        joinedload(Product.subject).joinedload(Subject.user),
        joinedload(Product.reviewer),
        selectinload(Product.images),
        selectinload(Product.source_links).joinedload(ProductSource.source),
    )


def build_evidence_summary(product: Product) -> dict:
    """Tinh trang thai xac minh tu chung cu, khong luu lap vao bang san pham."""

    level_rank = {"A": 0, "B1": 1, "B2": 2, "C": 3}
    valid_links = [
        link for link in product.source_links if link.verification_level in level_rank
    ]
    recognition_links = [
        link for link in valid_links if link.evidence_role == "recognition"
    ]
    levels = {link.verification_level for link in valid_links}
    verification_level = min(levels, key=level_rank.get) if levels else None

    recognition_levels = {link.verification_level for link in recognition_links}
    if "A" in recognition_levels:
        verification_status = "verified_official_decision"
    elif "B1" in recognition_levels:
        verification_status = "verified_government_source"
    else:
        verification_status = "pending_verification"

    has_decision = any(
        link.source.document_number and link.source.document_number.strip()
        for link in recognition_links
    )
    issues = []
    if not recognition_links:
        issues.append("no_recognition_source")
    if not has_decision:
        issues.append("missing_decision")
    if product.cert_issued_at is None:
        issues.append("missing_issued_at")
    if product.cert_expires_at is None:
        issues.append("missing_expires_at")

    return {
        "verification_level": verification_level,
        "verification_status": verification_status,
        "evidence_count": len(valid_links),
        "missing_decision": "missing_decision" in issues,
        "missing_issued_at": "missing_issued_at" in issues,
        "issues": issues,
    }


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
        statement = statement.with_for_update(of=Product)
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


def replace_product_images(
    product: Product,
    payload: ProductWritePayload | ProductDraftCreate | ProductDraftUpdate,
) -> None:
    if payload.images is None:
        return
    product.images.clear()
    for image in payload.images:
        image_kwargs = {}
        if image.storage_path is not None:
            storage_pattern = rf"products/{product.subject_id}/[0-9a-f]{{32}}\.(jpg|png|webp)"
            if re.fullmatch(storage_pattern, image.storage_path) is None:
                raise workflow_error(
                    status.HTTP_403_FORBIDDEN,
                    "PRODUCT_IMAGE_NOT_OWNED",
                    "Ảnh tải lên không thuộc chủ thể hiện tại.",
                )
            if not (get_settings().upload_directory / image.storage_path).is_file():
                raise workflow_error(
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    "PRODUCT_IMAGE_NOT_FOUND",
                    "Không tìm thấy file ảnh đã tải lên.",
                )
            image_kwargs["storage_path"] = image.storage_path
        product.images.append(
            ProductImage(
                image_url=image.image_url,
                alt_text=product.name,
                is_primary=image.is_primary,
                sort_order=image.sort_order,
                **image_kwargs,
            )
        )


def validate_certificate_storage(product: Product, storage_path: str | None) -> None:
    if storage_path is None:
        return
    storage_pattern = rf"certificates/{product.subject_id}/[0-9a-f]{{32}}\.(pdf|jpg|png)"
    if re.fullmatch(storage_pattern, storage_path) is None:
        raise workflow_error(
            status.HTTP_403_FORBIDDEN,
            "PRODUCT_CERTIFICATE_NOT_OWNED",
            "File chứng nhận không thuộc chủ thể hiện tại.",
        )
    if not (get_settings().upload_directory / storage_path).is_file():
        raise workflow_error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "PRODUCT_CERTIFICATE_NOT_FOUND",
            "Không tìm thấy file chứng nhận đã tải lên.",
        )


def apply_product_payload(
    db: Session,
    product: Product,
    payload: ProductWritePayload,
    *,
    update_slug: bool,
) -> None:
    validate_certificate_storage(product, payload.certificate_storage_path)
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


def apply_product_draft_payload(
    db: Session,
    product: Product,
    payload: ProductDraftCreate | ProductDraftUpdate,
    *,
    partial: bool,
) -> None:
    values = payload.model_dump(exclude_unset=partial, exclude={"category_id", "images"})
    fields = payload.model_fields_set if partial else set(type(payload).model_fields)
    if "category_id" in fields:
        if payload.category_id is None:
            raise workflow_error(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "CATEGORY_REQUIRED",
                "Danh mục sản phẩm không được để trống.",
            )
        product.category = get_category(db, payload.category_id)
    if "certificate_storage_path" in fields:
        validate_certificate_storage(product, payload.certificate_storage_path)
    if "name" in values and values["name"] is None:
        raise workflow_error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "PRODUCT_NAME_REQUIRED",
            "Tên sản phẩm không được để trống.",
        )
    for field, value in values.items():
        setattr(product, field, value)
    if "name" in values:
        product.slug = build_unique_slug(db, product.name, product.id)
    if "cert_issued_at" in values:
        product.cert_year = product.cert_issued_at.year if product.cert_issued_at else None
    if (
        product.cert_issued_at is not None
        and product.cert_expires_at is not None
        and product.cert_expires_at <= product.cert_issued_at
    ):
        raise workflow_error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "INVALID_CERTIFICATE_DATES",
            "Ngày hết hạn phải sau ngày cấp chứng nhận.",
        )
    if "images" in fields:
        replace_product_images(product, payload)


def validate_product_submission(product: Product) -> None:
    required_values = {
        "description": product.description,
        "star": product.star,
        "cert_code": product.cert_code,
        "cert_issued_at": product.cert_issued_at,
        "cert_expires_at": product.cert_expires_at,
        "issuing_authority": product.issuing_authority,
        "certificate_document": product.certificate_storage_path or product.certificate_url,
    }
    missing_fields = [field for field, value in required_values.items() if value in (None, "")]
    if product.price is not None and product.price > 0 and not product.unit:
        missing_fields.append("unit")
    if not product.images or sum(image.is_primary for image in product.images) != 1:
        missing_fields.append("primary_image")
    if missing_fields:
        raise workflow_error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "PRODUCT_SUBMISSION_INCOMPLETE",
            "Hồ sơ sản phẩm chưa đủ điều kiện gửi duyệt.",
            {"missing_fields": missing_fields},
        )
    if product.cert_issued_at and product.cert_issued_at > date.today():
        raise workflow_error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "CERTIFICATE_NOT_ACTIVE",
            "Ngày cấp chứng nhận không được ở tương lai.",
        )
    validate_certificate_is_current(product)


def validate_certificate_is_current(product: Product) -> None:
    if product.cert_expires_at is None or product.cert_expires_at < date.today():
        raise workflow_error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "CERTIFICATE_EXPIRED",
            "Giấy chứng nhận đã hết hạn hoặc chưa có ngày hết hạn hợp lệ.",
            {"cert_expires_at": str(product.cert_expires_at)},
        )


def to_managed_product_read(product: Product) -> ManagedProductRead:
    evidence = build_evidence_summary(product)
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
        certificate_storage_path=product.certificate_storage_path,
        vietgap_code=product.vietgap_code,
        description=product.description,
        story=product.story,
        ingredients=product.ingredients,
        usage_instructions=product.usage_instructions,
        status=product.status,
        submitted_at=product.submitted_at,
        reviewed_at=product.reviewed_at,
        reviewed_by_name=product.reviewer.full_name if product.reviewer else None,
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
            status=product.subject.status,
            is_active=product.subject.user.is_active,
        ),
        images=[
            ManagedProductImageRead(
                id=image.id,
                image_url=image.image_url,
                storage_path=image.storage_path,
                is_primary=image.is_primary,
                sort_order=image.sort_order,
            )
            for image in product.images
        ],
        verification_level=evidence["verification_level"],
        verification_status=evidence["verification_status"],
        evidence_count=evidence["evidence_count"],
        missing_decision=evidence["missing_decision"],
        missing_issued_at=evidence["missing_issued_at"],
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


def to_product_evidence_response(product: Product) -> ProductEvidenceResponse:
    evidence = build_evidence_summary(product)
    return ProductEvidenceResponse(
        product_id=product.id,
        product_name=product.name,
        verification_level=evidence["verification_level"],
        verification_status=evidence["verification_status"],
        evidence_count=evidence["evidence_count"],
        issues=evidence["issues"],
        sources=[
            ProductEvidenceSourceRead(
                evidence_role=link.evidence_role,
                verification_level=link.verification_level,
                original_address=link.original_address,
                verified_at=link.verified_at,
                notes=link.notes,
                source=DataSourceRead(
                    id=link.source.id,
                    title=link.source.title,
                    document_number=link.source.document_number,
                    issuing_body=link.source.issuing_body,
                    source_type=link.source.source_type,
                    published_at=link.source.published_at,
                    source_url=link.source.source_url,
                    local_path=link.source.local_path,
                    sha256=link.source.sha256,
                    retrieved_at=link.source.retrieved_at,
                ),
            )
            for link in sorted(
                product.source_links,
                key=lambda item: (item.verified_at, item.source_id),
                reverse=True,
            )
        ],
    )


def change_request_load_options() -> tuple:
    return (
        joinedload(ProductChangeRequest.product).joinedload(Product.subject),
        joinedload(ProductChangeRequest.product).selectinload(Product.images),
        joinedload(ProductChangeRequest.reviewer),
    )


def get_change_request(
    db: Session,
    request_id: int,
    *,
    subject_id: int | None = None,
    lock: bool = False,
) -> ProductChangeRequest:
    filters = [ProductChangeRequest.id == request_id]
    if subject_id is not None:
        filters.append(ProductChangeRequest.subject_id == subject_id)
    statement = select(ProductChangeRequest).where(*filters)
    if lock:
        statement = statement.with_for_update(of=ProductChangeRequest)
    change_request = db.scalar(statement.options(*change_request_load_options()))
    if change_request is None:
        raise workflow_error(
            status.HTTP_404_NOT_FOUND,
            "PRODUCT_CHANGE_REQUEST_NOT_FOUND",
            "Không tìm thấy yêu cầu thay đổi sản phẩm.",
            {"request_id": request_id},
        )
    return change_request


def to_change_request_read(change_request: ProductChangeRequest) -> ProductChangeRequestRead:
    product = change_request.product
    current_data = ProductSnapshotRead(
        category_id=product.category_id,
        name=product.name,
        star=product.star,
        price=product.price,
        unit=product.unit,
        cert_code=product.cert_code,
        cert_issued_at=product.cert_issued_at,
        cert_expires_at=product.cert_expires_at,
        issuing_authority=product.issuing_authority,
        certificate_url=product.certificate_url,
        certificate_storage_path=product.certificate_storage_path,
        vietgap_code=product.vietgap_code,
        description=product.description,
        story=product.story,
        ingredients=product.ingredients,
        usage_instructions=product.usage_instructions,
        images=[
            {
                "image_url": image.image_url,
                "storage_path": image.storage_path,
                "is_primary": image.is_primary,
                "sort_order": image.sort_order,
            }
            for image in product.images
        ],
    )
    return ProductChangeRequestRead(
        id=change_request.id,
        product_id=change_request.product_id,
        subject_id=change_request.subject_id,
        request_type=change_request.request_type,
        current_data=current_data,
        proposed_data=change_request.proposed_data,
        reason=change_request.reason,
        status=change_request.status,
        base_version=change_request.base_version,
        submitted_at=change_request.submitted_at,
        reviewed_at=change_request.reviewed_at,
        reviewed_by_name=(
            change_request.reviewer.full_name if change_request.reviewer else None
        ),
        review_note=change_request.review_note,
        product_name=change_request.product.name,
        subject_name=change_request.product.subject.name,
        created_at=change_request.created_at,
        updated_at=change_request.updated_at,
    )
