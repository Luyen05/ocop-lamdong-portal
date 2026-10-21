"""Bắt lỗi chưa xử lý và trả JSON thống nhất.

``@app.exception_handler(Exception)`` của Starlette chạy ở ServerErrorMiddleware, nằm ngoài CORSMiddleware,
nên phản hồi 500 không có header CORS và trình duyệt chỉ báo "lỗi mạng". Middleware ASGI này được thêm
trước CORSMiddleware (tức nằm bên trong) để phản hồi lỗi vẫn đi qua CORS.
"""

from __future__ import annotations

import json
import logging

from starlette.types import ASGIApp, Message, Receive, Scope, Send


logger = logging.getLogger("app.errors")

INTERNAL_ERROR_BODY = {
    "code": "INTERNAL_ERROR",
    "message": "Đã có lỗi xảy ra. Vui lòng thử lại sau.",
    "details": None,
}


class UnhandledErrorMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        response_started = False

        async def tracking_send(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, receive, tracking_send)
        except Exception:
            logger.exception(
                "Lỗi chưa xử lý khi xử lý %s %s",
                scope.get("method", ""),
                scope.get("path", ""),
            )
            if response_started:
                # Đã gửi một phần phản hồi, không thể đổi sang JSON nữa.
                raise
            body = json.dumps(INTERNAL_ERROR_BODY, ensure_ascii=False).encode("utf-8")
            await send(
                {
                    "type": "http.response.start",
                    "status": 500,
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"content-length", str(len(body)).encode("ascii")),
                    ],
                }
            )
            await send({"type": "http.response.body", "body": body})
