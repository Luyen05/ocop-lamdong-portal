from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.core.database import get_db
from app.models.data_source import DataSource, ProductSource
from app.models.product import Product
from app.models.subject import Subject
from app.models.user import User
from app.schemas.error import ErrorResponse
from app.schemas.product_management import (
    ManagedProductListResponse,
    ManagedProductRead,
    EvidenceRole,
    ProductEvidenceLinkCreate,
    ProductEvidenceLinkUpdate,
    ProductEvidenceResponse,
    ProductModerationRequest,
    ProductVerificationStatus,
    ProductWorkflowStatus,
    VerificationLevel,
)
from app.services.product_workflow import (
    get_product_for_admin,
    product_load_options,
    to_managed_product_read,
    to_product_evidence_response,
    validate_certificate_is_current,
    workflow_error,
)
from app.api.routes.subject_product_certificates import certificate_response


router = APIRouter(prefix="/products")


def source_exists(*conditions):
    return (
        select(ProductSource.product_id)
        .join(DataSource, DataSource.id == ProductSource.source_id)
        .where(ProductSource.product_id == Product.id, *conditions)
        .exists()
    )


def effective_level_filter(level: VerificationLevel):
    has_a = source_exists(ProductSource.verification_level == "A")
    has_b1 = source_exists(ProductSource.verification_level == "B1")
    has_b2 = source_exists(ProductSource.verification_level == "B2")
    has_c = source_exists(ProductSource.verification_level == "C")
    if level == "A":
        return has_a
    if level == "B1":
        return and_(~has_a, has_b1)
    if level == "B2":
        return and_(~has_a, ~has_b1, has_b2)
    return and_(~has_a, ~has_b1, ~has_b2, has_c)


@router.get("", response_model=ManagedProductListResponse)
def list_products_for_moderation(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    product_status: ProductWorkflowStatus | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None, min_length=1, max_length=150),
    verification_level: VerificationLevel | None = Query(default=None),
    verification_status: ProductVerificationStatus | None = Query(default=None),
    missing_decision: bool | None = Query(default=None),
    missing_issued_at: bool | None = Query(default=None),
    db: Session = Depends(get_db),
) -> ManagedProductListResponse:
    filters = []
    if product_status:
        filters.append(Product.status == product_status)
    if search:
        keyword = f"%{search.strip()}%"
        filters.append(
            or_(
                Product.name.ilike(keyword),
                Product.cert_code.ilike(keyword),
                Subject.name.ilike(keyword),
            )
        )
    if verification_level:
        filters.append(effective_level_filter(verification_level))

    has_official_recognition = source_exists(
        ProductSource.evidence_role == "recognition",
        ProductSource.verification_level == "A",
    )
    has_government_recognition = source_exists(
        ProductSource.evidence_role == "recognition",
        ProductSource.verification_level == "B1",
    )
    if verification_status == "verified_official_decision":
        filters.append(has_official_recognition)
    elif verification_status == "verified_government_source":
        filters.extend([~has_official_recognition, has_government_recognition])
    elif verification_status == "pending_verification":
        filters.extend([~has_official_recognition, ~has_government_recognition])

    has_decision = source_exists(
        ProductSource.evidence_role == "recognition",
        DataSource.document_number.is_not(None),
        func.length(func.trim(DataSource.document_number)) > 0,
    )
    if missing_decision is not None:
        filters.append(~has_decision if missing_decision else has_decision)
    if missing_issued_at is not None:
        filters.append(
            Product.cert_issued_at.is_(None)
            if missing_issued_at
            else Product.cert_issued_at.is_not(None)
        )

    total = db.scalar(
        select(func.count(Product.id)).join(Product.subject).where(*filters)
    ) or 0
    status_order = case(
        (Product.status == "pending", 0),
        (Product.status == "needs_revision", 1),
        (Product.status == "draft", 2),
        else_=3,
    )
    products = list(
        db.scalars(
            select(Product)
            .join(Product.subject)
            .where(*filters)
            .options(*product_load_options())
            .order_by(status_order, Product.submitted_at.desc(), Product.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return ManagedProductListResponse(
        items=[to_managed_product_read(product) for product in products],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/{product_id}/evidence", response_model=ProductEvidenceResponse)
def get_product_evidence(
    product_id: int,
    db: Session = Depends(get_db),
) -> ProductEvidenceResponse:
    return to_product_evidence_response(get_product_for_admin(db, product_id))


@router.get("/{product_id}/certificate", response_class=FileResponse)
def download_product_certificate(
    product_id: int,
    db: Session = Depends(get_db),
) -> FileResponse:
    return certificate_response(get_product_for_admin(db, product_id))


@router.post(
    "/{product_id}/evidence",
    response_model=ProductEvidenceResponse,
    status_code=status.HTTP_201_CREATED,
)
def link_product_evidence(
    product_id: int,
    payload: ProductEvidenceLinkCreate,
    db: Session = Depends(get_db),
) -> ProductEvidenceResponse:
    product = get_product_for_admin(db, product_id)
    if db.get(DataSource, payload.source_id) is None:
        raise workflow_error(
            status.HTTP_404_NOT_FOUND,
            "DATA_SOURCE_NOT_FOUND",
            "Không tìm thấy nguồn dữ liệu cần liên kết.",
            {"source_id": payload.source_id},
        )
    link = ProductSource(product_id=product.id, **payload.model_dump())
    db.add(link)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise workflow_error(
            status.HTTP_409_CONFLICT,
            "PRODUCT_EVIDENCE_LINK_EXISTS",
            "Nguồn này đã được liên kết với cùng vai trò chứng cứ.",
        ) from exc
    db.expire_all()
    return to_product_evidence_response(get_product_for_admin(db, product.id))


def get_product_evidence_link(
    db: Session,
    product_id: int,
    source_id: int,
    evidence_role: EvidenceRole,
) -> ProductSource:
    link = db.get(ProductSource, (product_id, source_id, evidence_role))
    if link is None:
        raise workflow_error(
            status.HTTP_404_NOT_FOUND,
            "PRODUCT_EVIDENCE_LINK_NOT_FOUND",
            "Không tìm thấy liên kết chứng cứ của sản phẩm.",
        )
    return link


@router.patch(
    "/{product_id}/evidence/{source_id}/{evidence_role}",
    response_model=ProductEvidenceResponse,
)
def update_product_evidence_link(
    product_id: int,
    source_id: int,
    evidence_role: EvidenceRole,
    payload: ProductEvidenceLinkUpdate,
    db: Session = Depends(get_db),
) -> ProductEvidenceResponse:
    get_product_for_admin(db, product_id)
    link = get_product_evidence_link(db, product_id, source_id, evidence_role)
    for field, value in payload.model_dump().items():
        setattr(link, field, value)
    db.add(link)
    db.commit()
    db.expire_all()
    return to_product_evidence_response(get_product_for_admin(db, product_id))


@router.delete(
    "/{product_id}/evidence/{source_id}/{evidence_role}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def unlink_product_evidence(
    product_id: int,
    source_id: int,
    evidence_role: EvidenceRole,
    db: Session = Depends(get_db),
) -> None:
    get_product_for_admin(db, product_id)
    link = get_product_evidence_link(db, product_id, source_id, evidence_role)
    db.delete(link)
    db.commit()


@router.get("/{product_id}", response_model=ManagedProductRead)
def get_product_for_moderation(
    product_id: int,
    db: Session = Depends(get_db),
) -> ManagedProductRead:
    return to_managed_product_read(get_product_for_admin(db, product_id))


@router.patch(
    "/{product_id}/moderation",
    response_model=ManagedProductRead,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_409_CONFLICT: {"model": ErrorResponse},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorResponse},
    },
)
def moderate_product(
    product_id: int,
    payload: ProductModerationRequest,
    current_admin: CurrentUser,
    db: Session = Depends(get_db),
) -> ManagedProductRead:
    product = get_product_for_admin(db, product_id, lock=True)
    if product.status != "pending":
        raise workflow_error(
            status.HTTP_409_CONFLICT,
            "PRODUCT_ALREADY_REVIEWED",
            "Sản phẩm không còn ở trạng thái chờ duyệt.",
            {"current_status": product.status},
        )

    subject = db.scalar(
        select(Subject).where(Subject.id == product.subject_id).with_for_update()
    )
    owner = (
        db.scalar(select(User).where(User.id == subject.user_id).with_for_update())
        if subject
        else None
    )
    if subject is None or subject.status != "approved" or owner is None or not owner.is_active:
        raise workflow_error(
            status.HTTP_409_CONFLICT,
            "PRODUCT_SUBJECT_INACTIVE",
            "Không thể duyệt sản phẩm vì chủ thể không còn hợp lệ hoặc đã bị khóa.",
        )
    if payload.status == "approved":
        validate_certificate_is_current(product)

    product.status = payload.status
    product.reviewed_by = current_admin.id
    product.reviewer = current_admin
    product.reviewed_at = datetime.now(timezone.utc)
    product.review_note = payload.note
    if payload.status == "approved":
        product.version += 1
    db.add(product)
    db.commit()
    return to_managed_product_read(get_product_for_admin(db, product.id))
