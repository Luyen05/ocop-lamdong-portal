from typing import Literal

from pydantic import BaseModel

from app.core.roles import RoleName


class AdminAccessResponse(BaseModel):
    authenticated: Literal[True] = True
    role: Literal[RoleName.ADMIN] = RoleName.ADMIN


class AdminDashboardResponse(BaseModel):
    total_products: int
    approved_products: int
    pending_products: int
    pending_subject_applications: int
    pending_change_requests: int
    products_missing_decision: int
