from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.category import Category
from app.models.location import TourismLocation
from app.models.product import Product
from app.models.subject import Subject
from app.schemas.error import ErrorResponse
from app.schemas.statistics import (
    AdminStatisticsResponse,
    CategoryCount,
    CertificateStatistics,
    DistrictCount,
    KeyCount,
    MonthCount,
    StarCount,
    ViewedProduct,
    YearCount,
)


router = APIRouter(prefix="/statistics")

LOCAL_TIMEZONE = ZoneInfo("Asia/Ho_Chi_Minh")
EXPIRING_WINDOW_DAYS = 90
TOP_DISTRICTS = 10
TOP_VIEWED = 5
MAX_MONTHS = 36


def current_local_time() -> datetime:
    return datetime.now(LOCAL_TIMEZONE)


def _month_key(value: datetime) -> tuple[int, int]:
    # SQLite trả về datetime không múi giờ (đã là UTC); PostgreSQL trả về có múi giờ.
    if value.tzinfo is None:
        value = value.replace(tzinfo=ZoneInfo("UTC"))
    local = value.astimezone(LOCAL_TIMEZONE)
    return local.year, local.month


def _monthly_series(reviewed: list[datetime], now: datetime) -> list[MonthCount]:
    """Chuỗi tháng liên tục từ tháng duyệt đầu tiên đến tháng hiện tại (tối đa MAX_MONTHS), kể cả tháng bằng 0."""
    if not reviewed:
        return []
    counts: dict[tuple[int, int], int] = {}
    for value in reviewed:
        key = _month_key(value)
        counts[key] = counts.get(key, 0) + 1

    end = (now.year, now.month)
    start = min(min(counts), end)
    months: list[tuple[int, int]] = []
    year, month = start
    while (year, month) <= end:
        months.append((year, month))
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    months = months[-MAX_MONTHS:]
    return [MonthCount(month=f"{y:04d}-{m:02d}", count=counts.get((y, m), 0)) for y, m in months]


def build_admin_statistics(db: Session, now: datetime) -> AdminStatisticsResponse:
    approved = Product.status == "approved"
    today = now.date()

    products_by_status = [
        KeyCount(key=key, count=count)
        for key, count in db.execute(
            select(Product.status, func.count(Product.id))
            .group_by(Product.status)
            .order_by(func.count(Product.id).desc(), Product.status)
        )
    ]

    approved_by_star = [
        StarCount(star=star, count=count)
        for star, count in db.execute(
            select(Product.star, func.count(Product.id))
            .where(approved, Product.star.is_not(None))
            .group_by(Product.star)
            .order_by(Product.star)
        )
    ]

    # Liệt kê cả nhóm chưa có sản phẩm để quản trị viên thấy nhóm còn trống.
    category_count = func.count(Product.id)
    approved_by_category = [
        CategoryCount(id=category_id, name=name, slug=slug, count=count)
        for category_id, name, slug, count in db.execute(
            select(Category.id, Category.name, Category.slug, category_count)
            .outerjoin(Product, (Product.category_id == Category.id) & approved)
            .group_by(Category.id, Category.name, Category.slug)
            .order_by(category_count.desc(), Category.name)
        )
    ]

    district_count = func.count(Product.id)
    approved_by_district = [
        DistrictCount(district=district, count=count)
        for district, count in db.execute(
            select(Subject.district, district_count)
            .join(Product, Product.subject_id == Subject.id)
            .where(approved)
            .group_by(Subject.district)
            .order_by(district_count.desc(), Subject.district)
            .limit(TOP_DISTRICTS)
        )
    ]

    reviewed_dates = list(
        db.scalars(select(Product.reviewed_at).where(approved, Product.reviewed_at.is_not(None)))
    )
    approved_without_review_date = db.scalar(
        select(func.count(Product.id)).where(approved, Product.reviewed_at.is_(None))
    ) or 0

    expired = db.scalar(
        select(func.count(Product.id)).where(approved, Product.cert_expires_at < today)
    ) or 0
    expiring_soon = db.scalar(
        select(func.count(Product.id)).where(
            approved,
            Product.cert_expires_at >= today,
            Product.cert_expires_at <= today + timedelta(days=EXPIRING_WINDOW_DAYS),
        )
    ) or 0
    by_year = [
        YearCount(year=year, count=count)
        for year, count in db.execute(
            select(Product.cert_year, func.count(Product.id))
            .where(Product.cert_year.is_not(None))
            .group_by(Product.cert_year)
            .order_by(Product.cert_year)
        )
    ]

    top_viewed_products = [
        ViewedProduct(id=product_id, name=name, slug=slug, views=views)
        for product_id, name, slug, views in db.execute(
            select(Product.id, Product.name, Product.slug, Product.views)
            .where(approved, Product.views > 0)
            .order_by(Product.views.desc(), Product.name)
            .limit(TOP_VIEWED)
        )
    ]

    subjects_by_status = [
        KeyCount(key=key, count=count)
        for key, count in db.execute(
            select(Subject.status, func.count(Subject.id))
            .group_by(Subject.status)
            .order_by(func.count(Subject.id).desc(), Subject.status)
        )
    ]

    location_count = func.count(TourismLocation.id)
    locations_by_type = [
        KeyCount(key=key, count=count)
        for key, count in db.execute(
            select(TourismLocation.type, location_count)
            .where(TourismLocation.status == "approved")
            .group_by(TourismLocation.type)
            .order_by(location_count.desc(), TourismLocation.type)
        )
    ]

    return AdminStatisticsResponse(
        generated_at=now,
        products_by_status=products_by_status,
        approved_by_star=approved_by_star,
        approved_by_category=approved_by_category,
        approved_by_district=approved_by_district,
        approved_by_month=_monthly_series(reviewed_dates, now),
        approved_without_review_date=approved_without_review_date,
        certificates=CertificateStatistics(
            expired=expired,
            expiring_soon=expiring_soon,
            expiring_window_days=EXPIRING_WINDOW_DAYS,
            by_year=by_year,
        ),
        top_viewed_products=top_viewed_products,
        subjects_by_status=subjects_by_status,
        locations_by_type=locations_by_type,
    )


@router.get(
    "",
    response_model=AdminStatisticsResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
        status.HTTP_403_FORBIDDEN: {"model": ErrorResponse},
    },
)
def get_admin_statistics(db: Session = Depends(get_db)) -> AdminStatisticsResponse:
    """Số liệu thống kê toàn cổng cho trang tổng quan quản trị (chỉ đọc)."""
    return build_admin_statistics(db, current_local_time())
