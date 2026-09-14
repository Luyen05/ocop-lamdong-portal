from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.error import ErrorResponse
from app.schemas.news import NewsListResponse
from app.services.news_feed import NewsFeedUnavailableError, get_news_items


router = APIRouter(prefix="/news", tags=["News"])


@router.get(
    "",
    response_model=NewsListResponse,
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponse},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorResponse},
    },
)
def list_news(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=50),
    search: str | None = Query(default=None, min_length=1, max_length=150),
) -> NewsListResponse:
    try:
        items = get_news_items()
    except NewsFeedUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "NEWS_SOURCE_UNAVAILABLE",
                "message": "Nguồn tin OCOP đang tạm thời không phản hồi. Vui lòng thử lại sau.",
                "details": None,
            },
        ) from exc

    if search:
        keyword = search.strip().casefold()
        items = [
            item
            for item in items
            if keyword in item.title.casefold() or keyword in item.summary.casefold()
        ]
    total = len(items)
    start = (page - 1) * page_size
    return NewsListResponse(
        items=items[start : start + page_size],
        page=page,
        page_size=page_size,
        total=total,
    )
