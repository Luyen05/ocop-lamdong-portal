from fastapi import APIRouter, Depends, status

from app.api.dependencies import CurrentUser, require_roles
from app.core.roles import RoleName
from app.schemas.access import AdminAccessResponse
from app.schemas.error import ErrorResponse


router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(require_roles(RoleName.ADMIN))],
)


@router.get(
    "/access",
    response_model=AdminAccessResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
        status.HTTP_403_FORBIDDEN: {"model": ErrorResponse},
    },
)
def check_admin_access(current_user: CurrentUser) -> AdminAccessResponse:
    """Xác nhận JWT hiện tại thuộc một tài khoản admin đang hoạt động."""
    return AdminAccessResponse(role=RoleName(current_user.role.name))

