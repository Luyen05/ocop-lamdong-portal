"""Giới hạn số lần nhập sai mật khẩu, đếm trong bộ nhớ của tiến trình.

Dùng cho đăng nhập và kiểm tra mật khẩu hiện tại khi đổi mật khẩu:

- quá ``EMAIL_FAILURE_LIMIT`` lần sai trong ``WINDOW_SECONDS`` cho cùng một email, hoặc
- quá ``IP_FAILURE_LIMIT`` lần sai trong cùng khoảng thời gian từ cùng một địa chỉ IP

thì từ chối (HTTP 429) tới khi lần sai cũ nhất ra khỏi cửa sổ thời gian. Nhập đúng thì xóa bộ đếm của email.

Bộ đếm nằm trong bộ nhớ nên mất khi khởi động lại và không chia sẻ giữa nhiều tiến trình uvicorn
(đủ cho đồ án chạy một tiến trình; triển khai nhiều tiến trình thì cần Redis hoặc tương đương).
"""

from __future__ import annotations

import math
from collections import deque
from collections.abc import Callable
from threading import Lock
from time import monotonic


WINDOW_SECONDS = 15 * 60
EMAIL_FAILURE_LIMIT = 5
IP_FAILURE_LIMIT = 20
# Giới hạn số khóa giữ trong bộ nhớ; vượt thì dọn các khóa đã hết hạn.
MAX_TRACKED_KEYS = 10_000


class SlidingWindowCounter:
    """Đếm số lần thất bại theo khóa trong cửa sổ thời gian trượt. An toàn khi gọi từ nhiều luồng."""

    def __init__(
        self,
        *,
        limit: int,
        window_seconds: float,
        clock: Callable[[], float] = monotonic,
        max_keys: int = MAX_TRACKED_KEYS,
    ) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self.clock = clock
        self.max_keys = max_keys
        self._events: dict[str, deque[float]] = {}
        self._lock = Lock()

    def _prune(self, key: str, now: float) -> deque[float] | None:
        events = self._events.get(key)
        if events is None:
            return None
        cutoff = now - self.window_seconds
        while events and events[0] <= cutoff:
            events.popleft()
        if not events:
            del self._events[key]
            return None
        return events

    def retry_after(self, key: str) -> int:
        """Số giây phải chờ trước khi được thử lại; 0 nếu chưa bị chặn."""

        with self._lock:
            now = self.clock()
            events = self._prune(key, now)
            if events is None or len(events) < self.limit:
                return 0
            # Được thử lại khi số lần sai trong cửa sổ xuống dưới giới hạn.
            unblock_at = events[len(events) - self.limit] + self.window_seconds
            return max(1, math.ceil(unblock_at - now))

    def record(self, key: str) -> None:
        with self._lock:
            now = self.clock()
            if key not in self._events and len(self._events) >= self.max_keys:
                for tracked in list(self._events):
                    self._prune(tracked, now)
                if len(self._events) >= self.max_keys:
                    # Vẫn đầy (đang bị tấn công dồn dập): bỏ khóa cũ nhất để không tăng bộ nhớ vô hạn.
                    oldest = min(self._events, key=lambda name: self._events[name][-1])
                    del self._events[oldest]
            self._events.setdefault(key, deque()).append(now)

    def reset(self, key: str) -> None:
        with self._lock:
            self._events.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._events.clear()


class PasswordAttemptLimiter:
    """Kết hợp bộ đếm theo email và theo địa chỉ IP."""

    def __init__(
        self,
        *,
        email_limit: int = EMAIL_FAILURE_LIMIT,
        ip_limit: int = IP_FAILURE_LIMIT,
        window_seconds: float = WINDOW_SECONDS,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        self.by_email = SlidingWindowCounter(limit=email_limit, window_seconds=window_seconds, clock=clock)
        self.by_ip = SlidingWindowCounter(limit=ip_limit, window_seconds=window_seconds, clock=clock)

    @staticmethod
    def _email_key(email: str) -> str:
        return email.strip().lower()

    def retry_after(self, *, email: str, ip: str) -> int:
        return max(self.by_email.retry_after(self._email_key(email)), self.by_ip.retry_after(ip))

    def record_failure(self, *, email: str, ip: str) -> None:
        self.by_email.record(self._email_key(email))
        self.by_ip.record(ip)

    def record_success(self, *, email: str) -> None:
        self.by_email.reset(self._email_key(email))

    def clear(self) -> None:
        self.by_email.clear()
        self.by_ip.clear()


password_attempts = PasswordAttemptLimiter()


def reset_rate_limits() -> None:
    """Xóa toàn bộ bộ đếm (dùng trong kiểm thử)."""

    password_attempts.clear()
