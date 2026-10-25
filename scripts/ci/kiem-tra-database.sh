#!/usr/bin/env bash
# Tạo database trống từ database/schema.sql, nạp toàn bộ seed, chạy migration tổng 014 (phải chạy lặp lại an toàn)
# rồi chạy tools/kiem-tra-database.sql: kết quả phải rỗng.
#
# Dùng trong CI và trên máy có PostgreSQL + PostGIS:
#   PGHOST=localhost PGUSER=postgres PGPASSWORD=... scripts/ci/kiem-tra-database.sh [tên_database]
set -euo pipefail
export PGOPTIONS="-c client_min_messages=warning"  # bỏ thông báo "already exists, skipping" của migration chạy lặp

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DB="${1:-ocop_kiem_tra}"
SEEDS=(seed_dev seed_tourism_locations seed_public_reference seed_ocop_2025_2026 seed_product_workflow seed_dehavi_demo seed_dehavi_media)

psql -v ON_ERROR_STOP=1 -q -d postgres -c "DROP DATABASE IF EXISTS \"$DB\"" -c "CREATE DATABASE \"$DB\""
run() { psql -v ON_ERROR_STOP=1 -q -d "$DB" -f "$1" >/dev/null; }

echo "==> schema.sql"
run "$ROOT/database/schema.sql"
for seed in "${SEEDS[@]}"; do
  echo "==> $seed.sql"
  run "$ROOT/database/$seed.sql"
done
echo "==> migrations/014_hoan_thien.sql (chạy 2 lần để kiểm tra idempotent)"
run "$ROOT/database/migrations/014_hoan_thien.sql"
run "$ROOT/database/migrations/014_hoan_thien.sql"

echo "==> tools/kiem-tra-database.sql"
DIFF="$(psql -v ON_ERROR_STOP=1 -t -A -d "$DB" -f "$ROOT/tools/kiem-tra-database.sql")"
if [ -n "$DIFF" ]; then
  echo "Database lệch so với repo:"
  echo "$DIFF"
  exit 1
fi
echo "Database khớp repo."
