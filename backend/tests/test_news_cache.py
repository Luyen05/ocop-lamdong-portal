"""Bộ nhớ đệm tin tức RSS: gia hạn bản cũ khi nguồn lỗi, không để nhiều request cùng gọi nguồn."""

import threading
import time

import pytest

from app.schemas.news import NewsItem
from app.services import news_feed
from app.services.news_feed import NewsFeedUnavailableError
from test_news import sample_items


class FakeClock:
    def __init__(self) -> None:
        self.now = 10_000.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def feed(monkeypatch):
    """Nguồn RSS giả: đếm số lần gọi, có thể cho lỗi hoặc chặn lại giữa chừng."""

    clock = FakeClock()
    state = {"calls": 0, "fail": False, "gate": None, "started": threading.Event()}

    def fake_fetch() -> list[NewsItem]:
        state["calls"] += 1
        state["started"].set()
        if state["gate"] is not None:
            assert state["gate"].wait(5)
        if state["fail"]:
            raise NewsFeedUnavailableError("nguồn lỗi")
        return sample_items()

    news_feed.clear_news_cache()
    monkeypatch.setattr(news_feed, "monotonic", clock)
    monkeypatch.setattr(news_feed, "_fetch_news_items", fake_fetch)
    yield state, clock
    news_feed.clear_news_cache()


def test_cache_is_reused_until_it_expires(feed) -> None:
    state, clock = feed
    ttl = news_feed.get_settings().news_cache_ttl_seconds

    assert len(news_feed.get_news_items()) == 2
    clock.now += ttl - 1
    news_feed.get_news_items()
    assert state["calls"] == 1

    clock.now += 2
    news_feed.get_news_items()
    assert state["calls"] == 2


def test_failed_refresh_extends_stale_cache_for_a_minute(feed) -> None:
    state, clock = feed
    ttl = news_feed.get_settings().news_cache_ttl_seconds
    news_feed.get_news_items()

    clock.now += ttl + 1
    state["fail"] = True
    assert len(news_feed.get_news_items()) == 2  # bản cũ
    assert state["calls"] == 2

    clock.now += news_feed.STALE_RETRY_SECONDS - 1
    for _ in range(5):
        assert len(news_feed.get_news_items()) == 2
    assert state["calls"] == 2, "trong thời gian gia hạn không được gọi lại nguồn đang lỗi"

    clock.now += 2
    news_feed.get_news_items()
    assert state["calls"] == 3


def test_failure_without_cache_raises(feed) -> None:
    state, _ = feed
    state["fail"] = True

    with pytest.raises(NewsFeedUnavailableError):
        news_feed.get_news_items()
    state["fail"] = False
    assert len(news_feed.get_news_items()) == 2


def make_workers(count: int) -> tuple[list[threading.Thread], list]:
    results: list = []

    def worker() -> None:
        try:
            results.append(news_feed.get_news_items())
        except NewsFeedUnavailableError as exc:
            results.append(exc)

    return [threading.Thread(target=worker) for _ in range(count)], results


def test_concurrent_requests_with_stale_cache_do_not_wait_for_network(feed) -> None:
    state, clock = feed
    news_feed.get_news_items()
    clock.now += news_feed.get_settings().news_cache_ttl_seconds + 1
    state["gate"] = threading.Event()
    state["started"].clear()

    refresher, refresher_results = make_workers(1)
    refresher[0].start()
    assert state["started"].wait(5)
    # Trong lúc request đầu đang gọi nguồn, các request khác trả bản cũ ngay, không chờ.
    others, other_results = make_workers(5)
    for thread in others:
        thread.start()
    for thread in others:
        thread.join(5)
        assert not thread.is_alive()

    assert len(other_results) == 5
    assert all(len(items) == 2 for items in other_results)
    assert state["calls"] == 2

    state["gate"].set()
    refresher[0].join(5)
    assert len(refresher_results[0]) == 2


def test_concurrent_requests_without_cache_share_one_fetch(feed) -> None:
    state, _ = feed
    state["gate"] = threading.Event()

    threads, results = make_workers(5)
    threads[0].start()
    assert state["started"].wait(5)
    for thread in threads[1:]:
        thread.start()
    time.sleep(0.3)  # để các request sau kịp tới bước chờ lần gọi đang chạy
    state["gate"].set()
    for thread in threads:
        thread.join(5)

    assert state["calls"] == 1
    assert len(results) == 5
    assert all(isinstance(items, list) and len(items) == 2 for items in results)


def test_concurrent_requests_without_cache_share_one_failure(feed) -> None:
    state, _ = feed
    state["gate"] = threading.Event()
    state["fail"] = True

    threads, results = make_workers(4)
    threads[0].start()
    assert state["started"].wait(5)
    for thread in threads[1:]:
        thread.start()
    time.sleep(0.3)  # để các request sau kịp tới bước chờ lần gọi đang chạy
    state["gate"].set()
    for thread in threads:
        thread.join(5)

    assert state["calls"] == 1
    assert len(results) == 4
    assert all(isinstance(result, NewsFeedUnavailableError) for result in results)
