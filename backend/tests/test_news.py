from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.news import NewsItem
from app.services.news_feed import NewsFeedUnavailableError, parse_news_feed


RSS_URL = "https://ocoplamdong.gov.vn/rssChanel/tin-tuc-su-kien.rss"
client = TestClient(app)


def sample_items() -> list[NewsItem]:
    return [
        NewsItem(
            id="tin-moi",
            title="Tin OCOP Lâm Đồng mới",
            summary="Hoạt động xúc tiến sản phẩm OCOP.",
            published_at=datetime(2026, 8, 12, 10, 0, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh")),
            source_name="Cổng TTĐT OCOP Lâm Đồng",
            source_url="https://ocoplamdong.gov.vn/tin-tuc/tin-moi.html",
            image_url=None,
            category="Tin tức - Sự kiện",
        ),
        NewsItem(
            id="du-lich",
            title="Du lịch nông nghiệp",
            summary="Trải nghiệm nông nghiệp tại Lâm Đồng.",
            published_at=datetime(2026, 7, 1, 8, 30, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh")),
            source_name="Cổng TTĐT OCOP Lâm Đồng",
            source_url="https://ocoplamdong.gov.vn/tin-tuc/du-lich.html",
            image_url="https://ocoplamdong.gov.vn/Media/du-lich.png",
            category="Tin tức - Sự kiện",
        ),
    ]


def test_parse_rss_cleans_content_and_normalizes_legacy_domain() -> None:
    content = b"""<?xml version="1.0" encoding="utf-8"?>
    <rss version="2.0"><channel><item>
      <title>Tin &amp; su kien OCOP</title>
      <link>http://ocopdaknong.vn/tin-tuc/tin-1.html</link>
      <image>http://ocopdaknong.vn/Media/tin-1.png</image>
      <description><![CDATA[<p>Noi dung <strong>da lam sach</strong>.</p>]]></description>
      <pubDate>8/12/2026 2:55:37 PM</pubDate>
    </item></channel></rss>"""

    items = parse_news_feed(content, RSS_URL)

    assert len(items) == 1
    assert items[0].title == "Tin & su kien OCOP"
    assert items[0].summary == "Noi dung da lam sach ."
    assert items[0].source_url == "https://ocoplamdong.gov.vn/tin-tuc/tin-1.html"
    assert items[0].image_url == "https://ocoplamdong.gov.vn/Media/tin-1.png"
    assert items[0].published_at is not None
    assert items[0].published_at.year == 2026


def test_list_news_supports_search_and_pagination(monkeypatch) -> None:
    monkeypatch.setattr("app.api.routes.news.get_news_items", sample_items)

    response = client.get(
        "/api/v1/news",
        params={"page": 1, "page_size": 1, "search": "OCOP"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["page"] == 1
    assert body["page_size"] == 1
    assert body["items"][0]["id"] == "tin-moi"


def test_list_news_returns_friendly_error_when_source_is_unavailable(
    monkeypatch,
) -> None:
    def unavailable() -> list[NewsItem]:
        raise NewsFeedUnavailableError("timeout")

    monkeypatch.setattr("app.api.routes.news.get_news_items", unavailable)
    response = client.get("/api/v1/news")

    assert response.status_code == 503
    assert response.json() == {
        "code": "NEWS_SOURCE_UNAVAILABLE",
        "message": "Nguồn tin OCOP đang tạm thời không phản hồi. Vui lòng thử lại sau.",
        "details": None,
    }
