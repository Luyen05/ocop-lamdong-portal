from pydantic import BaseModel, ConfigDict


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    description: str | None
    icon: str | None


class CategoryListResponse(BaseModel):
    items: list[CategoryRead]
    page: int
    page_size: int
    total: int
