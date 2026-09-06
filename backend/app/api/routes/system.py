from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.error import ErrorResponse


router = APIRouter(prefix="/health", tags=["System"])


@router.get(
    "/database",
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponse}},
)
def database_health(db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "DATABASE_UNAVAILABLE",
                "message": "Không thể kết nối cơ sở dữ liệu.",
                "details": None,
            },
        ) from exc
    return {"status": "ok", "database": "reachable"}
