from datetime import date, datetime

from pydantic import BaseModel


class ProductCategoryRead(BaseModel):
    id: int
    name: str
    slug: str


class ProductSubjectRead(BaseModel):
    id: int
    name: str
    district: str


class ProductListItem(BaseModel):
    id: int
    name: str
    slug: str
    star: int
    price: float | None
    unit: str | None
    description: str
    rating_avg: float
    vietgap_code: str | None
    primary_image_url: str | None
    category: ProductCategoryRead
    subject: ProductSubjectRead
    created_at: datetime


class ProductListResponse(BaseModel):
    items: list[ProductListItem]
    page: int
    page_size: int
    total: int


class ProductImageRead(BaseModel):
    id: int
    image_url: str
    is_primary: bool
    sort_order: int


class ProductDetail(ProductListItem):
    cert_code: str | None
    cert_year: int | None
    cert_issued_at: date | None
    cert_expires_at: date | None
    issuing_authority: str | None
    story: str | None
    ingredients: str | None
    usage_instructions: str | None
    views: int
    images: list[ProductImageRead]
    updated_at: datetime
