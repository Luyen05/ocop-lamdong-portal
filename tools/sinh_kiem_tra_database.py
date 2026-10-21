"""Sinh lại tools/kiem-tra-database.sql từ một database tạo mới theo schema.sql.

Chạy mỗi khi thêm hoặc sửa migration (schema.sql đổi) để file kiểm tra khớp repo:

    # 1. Tạo database trống rồi nạp database/schema.sql (và các seed nếu muốn)
    # 2. Chạy:
    python tools/sinh_kiem_tra_database.py "postgresql://postgres:mat-khau@localhost:5432/ten_db_moi"

Script chỉ đọc cấu trúc (information_schema, pg_catalog), không ghi gì vào database.
"""

from __future__ import annotations

import sys
from pathlib import Path

import psycopg

# Liệt kê bảng, cột (kèm kiểu, NOT NULL, mặc định), ràng buộc (kèm định nghĩa), index (kèm định nghĩa),
# trigger và hàm set_updated_at trong schema public (bỏ bảng của PostGIS).
ACTUAL_OBJECTS_SQL = """select 'table', table_name from information_schema.tables where table_schema='public' and table_type='BASE TABLE' and table_name<>'spatial_ref_sys'
union all select 'column', table_name||'.'||column_name||' '||case when data_type='USER-DEFINED' then udt_name else data_type end||coalesce('('||character_maximum_length||')','')||case when data_type='numeric' then coalesce('('||numeric_precision||','||numeric_scale||')','') else '' end||case when is_nullable='NO' then ' not null' else '' end||coalesce(' default '||column_default,'') from information_schema.columns where table_schema='public' and table_name not in ('spatial_ref_sys','geometry_columns','geography_columns')
union all select 'constraint', conrelid::regclass::text||'.'||conname||' '||pg_get_constraintdef(c.oid) from pg_constraint c join pg_namespace n on n.oid=c.connamespace where n.nspname='public' and conrelid<>0 and conrelid::regclass::text<>'spatial_ref_sys'
union all select 'index', tablename||'.'||indexname||' '||regexp_replace(indexdef,'^CREATE (UNIQUE )?INDEX \\S+ ON public\\.\\S+ ','\\1') from pg_indexes where schemaname='public' and tablename<>'spatial_ref_sys'
union all select 'trigger', event_object_table||'.'||trigger_name||' '||action_timing||' '||event_manipulation from information_schema.triggers where trigger_schema='public'
union all select 'function', p.proname||' '||md5(regexp_replace(pg_get_functiondef(p.oid),'\\s+',' ','g')) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.proname='set_updated_at'"""

HEADER = """-- So sánh database đang chạy với cấu trúc chuẩn của repo (schema.sql + migration mới nhất):
-- bảng, cột (kiểu, NOT NULL, giá trị mặc định), ràng buộc (cả nội dung CHECK), index, trigger, hàm set_updated_at.
-- Cách dùng: mở file trong Query Tool của pgAdmin rồi chạy.
-- Kết quả:
--   'thua_ngoai_repo'   = có trong database nhưng repo không có (sửa tay hoặc công cụ khác tạo);
--   'thieu_so_voi_repo' = repo có nhưng database chưa có (cần chạy migration còn thiếu).
-- Rỗng nghĩa là database khớp hoàn toàn với repo.
-- File sinh tự động bằng tools/sinh_kiem_tra_database.py; sinh lại mỗi khi schema.sql thay đổi.
"""


def build_sql(rows: list[tuple[str, str]]) -> str:
    values = ",\n    ".join(f"('{kind}','{name.replace(chr(39), chr(39) * 2)}')" for kind, name in rows)
    return f"""{HEADER}WITH expected(kind, name) AS (
  VALUES
    {values}
),
actual(kind, name) AS (
{ACTUAL_OBJECTS_SQL}
)
SELECT 'thua_ngoai_repo' AS tinh_trang, a.kind AS loai, a.name AS doi_tuong
FROM actual a LEFT JOIN expected e USING (kind, name) WHERE e.name IS NULL
UNION ALL
SELECT 'thieu_so_voi_repo', e.kind, e.name
FROM expected e LEFT JOIN actual a USING (kind, name) WHERE a.name IS NULL
ORDER BY 1, 2, 3;
"""


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("Cách dùng: python tools/sinh_kiem_tra_database.py <postgresql-url-cua-database-tao-moi>")
    with psycopg.connect(sys.argv[1]) as connection:
        rows = sorted(set(connection.execute(ACTUAL_OBJECTS_SQL).fetchall()))
    output = Path(__file__).with_name("kiem-tra-database.sql")
    output.write_text(build_sql(rows), encoding="utf-8")
    print(f"Đã ghi {output} ({len(rows)} đối tượng).")


if __name__ == "__main__":
    main()
