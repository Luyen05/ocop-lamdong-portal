from datetime import datetime

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
    price: float
    unit: str
    description: str
    rating_avg: float
    primary_image_url: str | None
    category: ProductCategoryRead
    subject: ProductSubjectRead
    created_at: datetime


class ProductListResponse(BaseModel):
    items: list[ProductListItem]
    page: int
    page_size: int
    total: int
