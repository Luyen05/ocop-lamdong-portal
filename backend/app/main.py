from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings


settings = get_settings()

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


@app.get("/health", tags=["System"])
def health() -> dict[str, str]:
    return {"status": "ok"}
