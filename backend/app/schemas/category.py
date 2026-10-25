from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


SLUG_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"


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


class AdminCategoryRead(CategoryRead):
    is_visible: bool
    sort_order: int
    product_count: int


class AdminCategoryListResponse(BaseModel):
    items: list[AdminCategoryRead]
    total: int


def _strip_or_none(value: object) -> object:
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value


class _CategoryFields(BaseModel):
    model_config = ConfigDict(extra="forbid")

    @field_validator("name", "slug", "description", "icon", mode="before", check_fields=False)
    @classmethod
    def normalize_text(cls, value: object) -> object:
        return _strip_or_none(value)

    @field_validator("slug", mode="before", check_fields=False)
    @classmethod
    def normalize_slug(cls, value: object) -> object:
        return value.lower() if isinstance(value, str) else value


class AdminCategoryCreate(_CategoryFields):
    name: str = Field(min_length=2, max_length=150)
    # Để trống thì tự sinh từ tên (bỏ dấu, nối bằng gạch ngang).
    slug: str | None = Field(default=None, min_length=1, max_length=150, pattern=SLUG_PATTERN)
    description: str | None = Field(default=None, max_length=2000)
    icon: str | None = Field(default=None, max_length=100)
    is_visible: bool = True
    sort_order: int = Field(default=0, ge=0, le=1_000_000)


class AdminCategoryUpdate(_CategoryFields):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    slug: str | None = Field(default=None, min_length=1, max_length=150, pattern=SLUG_PATTERN)
    description: str | None = Field(default=None, max_length=2000)
    icon: str | None = Field(default=None, max_length=100)
    is_visible: bool | None = None
    sort_order: int | None = Field(default=None, ge=0, le=1_000_000)

    @model_validator(mode="after")
    def validate_patch(self) -> "AdminCategoryUpdate":
        if not self.model_fields_set:
            raise ValueError("Cần ít nhất một trường để cập nhật.")
        for field in ("name", "slug", "is_visible", "sort_order"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"Trường {field} không được để trống.")
        return self
