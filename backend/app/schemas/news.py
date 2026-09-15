from datetime import datetime

from pydantic import BaseModel


class NewsImageRead(BaseModel):
    id: int
    image_url: str
    is_primary: bool
    sort_order: int


class NewsListItem(BaseModel):
    id: int
    title: str
    slug: str
    category: str
    summary: str
    primary_image_url: str | None
    published_at: datetime


class NewsListResponse(BaseModel):
    items: list[NewsListItem]
    page: int
    page_size: int
    total: int


class NewsDetail(NewsListItem):
    content: str
    views: int
    images: list[NewsImageRead]
    updated_at: datetime
