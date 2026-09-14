from __future__ import annotations

from datetime import datetime
from email.utils import parsedate_to_datetime
from hashlib import sha256
from html import unescape
from html.parser import HTMLParser
from threading import Lock
from time import monotonic
from urllib.parse import urljoin, urlparse, urlunparse
from zoneinfo import ZoneInfo

import httpx
from defusedxml import ElementTree

from app.core.config import get_settings
from app.schemas.news import NewsItem


ALLOWED_RSS_HOSTS = {"ocoplamdong.gov.vn", "www.ocoplamdong.gov.vn"}
LEGACY_RSS_HOSTS = {"ocopdaknong.vn", "www.ocopdaknong.vn"}
SOURCE_NAME = "Cổng TTĐT OCOP Lâm Đồng"
DEFAULT_CATEGORY = "Tin tức - Sự kiện"
LOCAL_TIMEZONE = ZoneInfo("Asia/Ho_Chi_Minh")


class NewsFeedUnavailableError(RuntimeError):
    pass


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if text:
            self.parts.append(text)


_cache_lock = Lock()
_cached_items: list[NewsItem] = []
_cache_expires_at = 0.0


def _clean_text(value: str | None, *, max_length: int) -> str:
    parser = _TextExtractor()
    parser.feed(unescape(value or ""))
    text = " ".join(" ".join(parser.parts).split())
    return text[:max_length].strip()


def _normalize_source_url(value: str | None, feed_url: str) -> str | None:
    if not value:
        return None
    absolute = urljoin(feed_url, value.strip())
    parsed = urlparse(absolute)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return None
    hostname = parsed.hostname.lower()
    if hostname in LEGACY_RSS_HOSTS:
        parsed = parsed._replace(scheme="https", netloc="ocoplamdong.gov.vn")
    elif hostname not in ALLOWED_RSS_HOSTS:
        return None
    elif parsed.scheme == "http":
        parsed = parsed._replace(scheme="https")
    return urlunparse(parsed)


def _parse_published_at(value: str | None) -> datetime | None:
    if not value:
        return None
    raw_value = value.strip()
    try:
        parsed = parsedate_to_datetime(raw_value)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=LOCAL_TIMEZONE)
    except (TypeError, ValueError):
        pass
    for date_format in ("%m/%d/%Y %I:%M:%S %p", "%m/%d/%Y %H:%M:%S"):
        try:
            return datetime.strptime(raw_value, date_format).replace(tzinfo=LOCAL_TIMEZONE)
        except ValueError:
            continue
    return None


def parse_news_feed(content: bytes, feed_url: str) -> list[NewsItem]:
    try:
        root = ElementTree.fromstring(content)
    except ElementTree.ParseError as exc:
        raise NewsFeedUnavailableError("Nguồn RSS trả về XML không hợp lệ.") from exc

    items: list[NewsItem] = []
    seen_urls: set[str] = set()
    for element in root.findall("./channel/item"):
        title = _clean_text(element.findtext("title"), max_length=300)
        source_url = _normalize_source_url(element.findtext("link"), feed_url)
        if not title or not source_url or source_url in seen_urls:
            continue
        image_url = _normalize_source_url(element.findtext("image"), feed_url)
        summary = _clean_text(element.findtext("description"), max_length=600)
        published_at = _parse_published_at(element.findtext("pubDate"))
        item_id = sha256(source_url.encode("utf-8")).hexdigest()[:20]
        items.append(
            NewsItem(
                id=item_id,
                title=title,
                summary=summary,
                published_at=published_at,
                source_name=SOURCE_NAME,
                source_url=source_url,
                image_url=image_url,
                category=DEFAULT_CATEGORY,
            )
        )
        seen_urls.add(source_url)

    items.sort(
        key=lambda item: item.published_at or datetime.min.replace(tzinfo=LOCAL_TIMEZONE),
        reverse=True,
    )
    return items


def _fetch_news_items() -> list[NewsItem]:
    settings = get_settings()
    parsed_url = urlparse(settings.news_rss_url)
    if parsed_url.scheme != "https" or (parsed_url.hostname or "").lower() not in ALLOWED_RSS_HOSTS:
        raise NewsFeedUnavailableError("Nguồn RSS chưa được cho phép.")

    try:
        with httpx.Client(
            timeout=settings.news_rss_timeout_seconds,
            follow_redirects=True,
            headers={"User-Agent": "OCOP-Lam-Dong-Portal/1.0"},
        ) as client:
            response = client.get(settings.news_rss_url)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise NewsFeedUnavailableError("Không thể kết nối nguồn RSS.") from exc

    content = response.content
    if len(content) > settings.news_rss_max_bytes:
        raise NewsFeedUnavailableError("Nguồn RSS vượt quá dung lượng cho phép.")
    if b"<rss" not in content[:500].lower():
        raise NewsFeedUnavailableError("Nguồn RSS không trả về định dạng tin tức hợp lệ.")
    return parse_news_feed(content, settings.news_rss_url)


def get_news_items() -> list[NewsItem]:
    global _cache_expires_at, _cached_items

    now = monotonic()
    with _cache_lock:
        if _cached_items and now < _cache_expires_at:
            return list(_cached_items)
        try:
            fresh_items = _fetch_news_items()
        except NewsFeedUnavailableError:
            if _cached_items:
                return list(_cached_items)
            raise
        _cached_items = fresh_items
        _cache_expires_at = now + get_settings().news_cache_ttl_seconds
        return list(_cached_items)


def clear_news_cache() -> None:
    global _cache_expires_at, _cached_items
    with _cache_lock:
        _cached_items = []
        _cache_expires_at = 0.0
