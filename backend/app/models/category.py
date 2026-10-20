from sqlalchemy import BigInteger, Boolean, CheckConstraint, Integer, String, Text, true
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (
        CheckConstraint("sort_order >= 0", name="categories_sort_order_check"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    icon: Mapped[str | None] = mapped_column(String(100))
    # Danh mục ẩn: không còn trong bộ lọc công khai và ô chọn khi tạo sản phẩm mới,
    # nhưng sản phẩm đã thuộc danh mục vẫn hiển thị (quy tắc nhóm trưởng chốt 28/09).
    is_visible: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=true(),
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
