import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import OperationalError, ProgrammingError, SQLAlchemyError

from app.api.router import api_router
from app.core.config import get_settings


settings = get_settings()
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="REST API cho cổng thông tin OCOP và du lịch nông nghiệp Lâm Đồng.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

public_product_uploads = settings.upload_directory / "products"
public_product_uploads.mkdir(parents=True, exist_ok=True)
app.mount(
    "/uploads/products",
    StaticFiles(directory=public_product_uploads),
    name="product-uploads",
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict) and {"code", "message"}.issubset(exc.detail):
        content = {
            "code": exc.detail["code"],
            "message": exc.detail["message"],
            "details": exc.detail.get("details"),
        }
    else:
        content = {
            "code": "HTTP_ERROR",
            "message": str(exc.detail),
            "details": None,
        }
    return JSONResponse(status_code=exc.status_code, content=content, headers=exc.headers)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "code": "VALIDATION_ERROR",
            "message": "Dữ liệu đầu vào không hợp lệ.",
            "details": jsonable_encoder(exc.errors()),
        },
    )


def is_schema_error(exc: SQLAlchemyError) -> bool:
    """PostgreSQL báo thiếu bảng/cột bằng ProgrammingError; SQLite dùng OperationalError."""

    if isinstance(exc, ProgrammingError):
        return True
    detail = str(getattr(exc, "orig", exc)).lower()
    return "no such column" in detail or "no such table" in detail


@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Trả lỗi JSON (kèm CORS) thay vì lỗi 500 trần để frontend hiển thị đúng nguyên nhân."""

    logger.exception("Lỗi cơ sở dữ liệu khi xử lý %s %s", request.method, request.url.path)
    if is_schema_error(exc):
        status_code = 503
        code = "DATABASE_SCHEMA_OUTDATED"
        message = (
            "Cơ sở dữ liệu chưa được cập nhật theo phiên bản mã nguồn hiện tại. "
            "Hãy chạy các migration còn thiếu trong thư mục database/migrations."
        )
    elif isinstance(exc, OperationalError):
        status_code = 503
        code = "DATABASE_UNAVAILABLE"
        message = "Không thể kết nối cơ sở dữ liệu. Vui lòng thử lại sau."
    else:
        status_code = 500
        code = "DATABASE_ERROR"
        message = "Có lỗi khi truy vấn cơ sở dữ liệu. Vui lòng thử lại sau."
    return JSONResponse(
        status_code=status_code,
        content={"code": code, "message": message, "details": None},
    )


@app.get("/health", tags=["System"])
def health() -> dict[str, str]:
    return {"status": "ok"}
