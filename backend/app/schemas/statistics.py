from datetime import datetime

from pydantic import BaseModel, Field


class KeyCount(BaseModel):
    """Một nhóm đếm theo mã (trạng thái, loại hình...); nhãn hiển thị do giao diện quyết định."""

    key: str
    count: int


class StarCount(BaseModel):
    star: int
    count: int


class CategoryCount(BaseModel):
    id: int
    name: str
    slug: str
    count: int


class DistrictCount(BaseModel):
    district: str
    count: int


class MonthCount(BaseModel):
    month: str = Field(description="Tháng theo giờ Việt Nam, dạng YYYY-MM")
    count: int


class YearCount(BaseModel):
    year: int
    count: int


class CertificateStatistics(BaseModel):
    expired: int = Field(description="Sản phẩm đang công khai có giấy chứng nhận đã hết hạn")
    expiring_soon: int = Field(description="Sản phẩm đang công khai hết hạn trong số ngày expiring_window_days")
    expiring_window_days: int
    by_year: list[YearCount]


class ViewedProduct(BaseModel):
    id: int
    name: str
    slug: str
    views: int


class AdminStatisticsResponse(BaseModel):
    generated_at: datetime
    products_by_status: list[KeyCount]
    approved_by_star: list[StarCount]
    approved_by_category: list[CategoryCount]
    approved_by_district: list[DistrictCount]
    approved_by_month: list[MonthCount]
    approved_without_review_date: int = Field(
        description="Sản phẩm đã duyệt nhưng không có ngày duyệt (dữ liệu nhập sẵn), không nằm trong approved_by_month",
    )
    certificates: CertificateStatistics
    top_viewed_products: list[ViewedProduct]
    subjects_by_status: list[KeyCount]
    locations_by_type: list[KeyCount]
