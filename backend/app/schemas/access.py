from typing import Literal

from pydantic import BaseModel

from app.core.roles import RoleName


class AdminAccessResponse(BaseModel):
    authenticated: Literal[True] = True
    role: Literal[RoleName.ADMIN] = RoleName.ADMIN


class AdminDashboardResponse(BaseModel):
    total_products: int
    approved_products: int
    # Sản phẩm thực sự hiện ở trang công khai (đã duyệt, không phải demo, đủ chứng nhận/nguồn công nhận,
    # chủ thể còn hoạt động).
    public_products: int = 0
    pending_products: int
    pending_subject_applications: int
    pending_change_requests: int
    products_missing_decision: int
    pending_locations: int = 0
    pending_location_change_requests: int = 0
    pending_reviews: int = 0
