from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.data_source import DataSource
from app.schemas.error import ErrorResponse
from app.schemas.product_management import (
    DataSourceListResponse,
    DataSourceRead,
    DataSourceType,
    DataSourceWrite,
)
from app.services.product_workflow import workflow_error


router = APIRouter(prefix="/data-sources")


def to_data_source_read(source: DataSource) -> DataSourceRead:
    return DataSourceRead(
        id=source.id,
        title=source.title,
        document_number=source.document_number,
        issuing_body=source.issuing_body,
        source_type=source.source_type,
        published_at=source.published_at,
        source_url=source.source_url,
        local_path=source.local_path,
        sha256=source.sha256,
        retrieved_at=source.retrieved_at,
    )


def get_data_source(db: Session, source_id: int, *, lock: bool = False) -> DataSource:
    statement = select(DataSource).where(DataSource.id == source_id)
    if lock:
        statement = statement.with_for_update()
    source = db.scalar(statement)
    if source is None:
        raise workflow_error(
            status.HTTP_404_NOT_FOUND,
            "DATA_SOURCE_NOT_FOUND",
            "Không tìm thấy nguồn dữ liệu.",
            {"source_id": source_id},
        )
    return source


def save_source(db: Session, source: DataSource) -> None:
    db.add(source)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise workflow_error(
            status.HTTP_409_CONFLICT,
            "DATA_SOURCE_URL_EXISTS",
            "Đường dẫn nguồn này đã tồn tại.",
        ) from exc


@router.get("", response_model=DataSourceListResponse)
def list_data_sources(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    search: str | None = Query(default=None, min_length=1, max_length=150),
    source_type: DataSourceType | None = Query(default=None),
    db: Session = Depends(get_db),
) -> DataSourceListResponse:
    filters = []
    if search:
        keyword = f"%{search.strip()}%"
        filters.append(
            or_(
                DataSource.title.ilike(keyword),
                DataSource.document_number.ilike(keyword),
                DataSource.issuing_body.ilike(keyword),
            )
        )
    if source_type:
        filters.append(DataSource.source_type == source_type)

    total = db.scalar(select(func.count(DataSource.id)).where(*filters)) or 0
    sources = list(
        db.scalars(
            select(DataSource)
            .where(*filters)
            .order_by(DataSource.published_at.desc(), DataSource.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return DataSourceListResponse(
        items=[to_data_source_read(source) for source in sources],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.post(
    "",
    response_model=DataSourceRead,
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_409_CONFLICT: {"model": ErrorResponse}},
)
def create_data_source(
    payload: DataSourceWrite,
    db: Session = Depends(get_db),
) -> DataSourceRead:
    source = DataSource(**payload.model_dump())
    save_source(db, source)
    db.refresh(source)
    return to_data_source_read(source)


@router.patch(
    "/{source_id}",
    response_model=DataSourceRead,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_409_CONFLICT: {"model": ErrorResponse},
    },
)
def update_data_source(
    source_id: int,
    payload: DataSourceWrite,
    db: Session = Depends(get_db),
) -> DataSourceRead:
    source = get_data_source(db, source_id, lock=True)
    for field, value in payload.model_dump().items():
        setattr(source, field, value)
    save_source(db, source)
    return to_data_source_read(get_data_source(db, source_id))
