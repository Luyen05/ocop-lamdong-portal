import re
import unicodedata


def slugify(value: str, fallback: str = "muc") -> str:
    """Chuyển tên tiếng Việt thành slug không dấu: "Đồ uống" -> "do-uong"."""

    normalized = unicodedata.normalize("NFKD", value.replace("đ", "d").replace("Đ", "D"))
    ascii_text = normalized.encode("ascii", "ignore").decode().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")
    return slug[:150].strip("-") or fallback
