from datetime import datetime

from pydantic import BaseModel


class NewsItem(BaseModel):
    id: str
    title: str
    summary: str
    published_at: datetime | None
    source_name: str
    source_url: str
    image_url: str | None
    category: str


class NewsListResponse(BaseModel):
    items: list[NewsItem]
    page: int
    page_size: int
    total: int
