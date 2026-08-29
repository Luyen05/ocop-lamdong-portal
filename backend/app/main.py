from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import get_connection

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


@app.get("/health", tags=["System"])
def health() -> dict[str, str]:
    return {"status": "ok"}

@app.get("/db-health", tags=["System"])
def database_health():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT current_database(), PostGIS_Version();")
            database, postgis_version = cur.fetchone()

    return {
        "status": "ok",
        "database": database,
        "postgis_version": postgis_version,
    }
    