"""Tìm kiếm chứa chuỗi (ILIKE) an toàn: ký tự đặc biệt người dùng gõ được hiểu theo nghĩa đen."""

from __future__ import annotations

from sqlalchemy.sql.elements import ColumnElement

# Ký tự thoát dùng chung cho mọi câu ILIKE ... ESCAPE '\'.
LIKE_ESCAPE = "\\"


def escape_like(value: str) -> str:
    """Thoát `\\`, `%`, `_` để "50%" hay "a_b" không bị hiểu là ký tự đại diện."""

    return (
        value.replace(LIKE_ESCAPE, LIKE_ESCAPE * 2)
        .replace("%", f"{LIKE_ESCAPE}%")
        .replace("_", f"{LIKE_ESCAPE}_")
    )


def contains_pattern(value: str) -> str:
    return f"%{escape_like(value.strip())}%"


def ilike_contains(column, value: str) -> ColumnElement[bool]:
    """`column ILIKE '%value%'` với value đã thoát ký tự đại diện."""

    return column.ilike(contains_pattern(value), escape=LIKE_ESCAPE)
