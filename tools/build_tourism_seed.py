"""Sinh database/seed_tourism_locations.sql từ bộ dữ liệu khảo sát điểm du lịch.

Chạy từ thư mục gốc dự án:

    python tools/build_tourism_seed.py

Script chỉ dùng thư viện chuẩn, kiểm tra dữ liệu trước khi ghi file seed và
dừng với thông báo lỗi nếu có dòng không hợp lệ.
"""

from __future__ import annotations

import csv
import re
import sys
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = ROOT / "data" / "tourism" / "diem_du_lich_nong_nghiep_2026.csv"
SEED_PATH = ROOT / "database" / "seed_tourism_locations.sql"

# Phải trùng với LOCATION_TYPES trong backend/app/services/location_catalog.py.
ALLOWED_TYPES = {
    "tea_coffee_farm",
    "fruit_garden",
    "flower_garden",
    "dairy_farm",
    "vegetable_farm",
    "craft_village",
    "farmstay",
    "other",
}
# Khung bao tỉnh Lâm Đồng sau sắp xếp năm 2025 (gồm Bình Thuận, Đắk Nông trước đây).
LATITUDE_RANGE = (10.3, 12.95)
LONGITUDE_RANGE = (107.0, 109.3)
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REQUIRED_FIELDS = ("slug", "name", "type", "district", "address", "latitude", "longitude", "source_url")


def sql_text(value: str | None) -> str:
    if value is None or value.strip() == "":
        return "NULL"
    return "'" + value.strip().replace("'", "''") + "'"


def sql_services(raw: str) -> str:
    services = [item.strip() for item in raw.split("|") if item.strip()]
    if not services:
        return "'{}'::TEXT[]"
    return "ARRAY[" + ", ".join(sql_text(item) for item in services) + "]::TEXT[]"


def validate_row(index: int, row: dict[str, str], seen_slugs: set[str]) -> list[str]:
    errors = [f"dòng {index}: thiếu {field}" for field in REQUIRED_FIELDS if not row.get(field, "").strip()]
    if errors:
        return errors

    slug = row["slug"].strip()
    if not SLUG_PATTERN.fullmatch(slug):
        errors.append(f"dòng {index}: slug không hợp lệ '{slug}'")
    if slug in seen_slugs:
        errors.append(f"dòng {index}: slug bị trùng '{slug}'")
    seen_slugs.add(slug)

    if row["type"].strip() not in ALLOWED_TYPES:
        errors.append(f"dòng {index}: loại hình không hợp lệ '{row['type']}'")

    try:
        latitude = float(row["latitude"])
        longitude = float(row["longitude"])
    except ValueError:
        errors.append(f"dòng {index}: tọa độ không phải số")
    else:
        if not LATITUDE_RANGE[0] <= latitude <= LATITUDE_RANGE[1]:
            errors.append(f"dòng {index}: vĩ độ {latitude} nằm ngoài tỉnh Lâm Đồng")
        if not LONGITUDE_RANGE[0] <= longitude <= LONGITUDE_RANGE[1]:
            errors.append(f"dòng {index}: kinh độ {longitude} nằm ngoài tỉnh Lâm Đồng")

    ticket_price = row.get("ticket_price", "").strip()
    if ticket_price:
        try:
            if Decimal(ticket_price) < 0:
                errors.append(f"dòng {index}: giá vé âm")
        except InvalidOperation:
            errors.append(f"dòng {index}: giá vé không phải số")

    if not row["source_url"].strip().startswith("https://"):
        errors.append(f"dòng {index}: nguồn phải là đường dẫn https")
    return errors


def build_values(row: dict[str, str]) -> str:
    ticket_price = row.get("ticket_price", "").strip()
    return (
        "  (\n"
        f"    {sql_text(row['name'])},\n"
        f"    {sql_text(row['slug'])},\n"
        f"    {sql_text(row['type'])},\n"
        f"    {sql_text(row['district'])},\n"
        f"    {sql_text(row['address'])},\n"
        f"    ST_SetSRID(ST_MakePoint({float(row['longitude']):.7f}, {float(row['latitude']):.7f}), 4326),\n"
        f"    {sql_text(row.get('contact_phone'))},\n"
        f"    {sql_text(row.get('opening_hours'))},\n"
        f"    {ticket_price if ticket_price else 'NULL'},\n"
        f"    {sql_services(row.get('services', ''))},\n"
        f"    {sql_text(row.get('description'))},\n"
        f"    {sql_text(row.get('website'))},\n"
        f"    {sql_text(row['source_url'])},\n"
        "    'approved'\n"
        "  )"
    )


def main() -> int:
    with DATASET_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    errors: list[str] = []
    seen_slugs: set[str] = set()
    for index, row in enumerate(rows, start=2):
        errors.extend(validate_row(index, row, seen_slugs))
    if not rows:
        errors.append("bộ dữ liệu không có dòng nào")
    if errors:
        print("Dữ liệu điểm du lịch không hợp lệ:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    header = f"""-- Dữ liệu tham khảo điểm du lịch nông nghiệp tỉnh Lâm Đồng.
-- Sinh tự động bằng tools/build_tourism_seed.py từ
-- data/tourism/diem_du_lich_nong_nghiep_2026.csv ngày {date.today().isoformat()}.
-- Tọa độ, địa chỉ và giờ mở cửa lấy từ trang địa điểm công khai ghi ở cột
-- source_url; đây KHÔNG phải dữ liệu hành chính chính thức và có thể đã thay đổi.
-- Chạy lặp lại an toàn: cập nhật thông tin theo slug nhưng giữ nguyên trạng thái
-- kiểm duyệt, điểm đánh giá và lượt xem đang có trong cơ sở dữ liệu.
-- Yêu cầu schema có cột website/source_url (database/migrations/008).
"""
    body = (
        "BEGIN;\n\n"
        "INSERT INTO tourism_locations (\n"
        "  name, slug, type, district, address, geom, contact_phone, opening_hours,\n"
        "  ticket_price, services, description, website, source_url, status\n"
        ")\nVALUES\n"
        + ",\n".join(build_values(row) for row in rows)
        + "\nON CONFLICT (slug) DO UPDATE SET\n"
        "  name = EXCLUDED.name,\n"
        "  type = EXCLUDED.type,\n"
        "  district = EXCLUDED.district,\n"
        "  address = EXCLUDED.address,\n"
        "  geom = EXCLUDED.geom,\n"
        "  contact_phone = EXCLUDED.contact_phone,\n"
        "  opening_hours = EXCLUDED.opening_hours,\n"
        "  ticket_price = EXCLUDED.ticket_price,\n"
        "  services = EXCLUDED.services,\n"
        "  description = EXCLUDED.description,\n"
        "  website = EXCLUDED.website,\n"
        "  source_url = EXCLUDED.source_url;\n\n"
        "COMMIT;\n"
    )
    SEED_PATH.write_text(header + "\n" + body, encoding="utf-8", newline="\n")
    print(f"Đã ghi {len(rows)} điểm du lịch vào {SEED_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
