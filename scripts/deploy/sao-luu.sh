#!/usr/bin/env bash
# Sao lưu database (pg_dump -Fc) và ảnh tải lên vào thư mục backups/, giữ KEEP bản gần nhất.
# Chạy định kỳ bằng cron, ví dụ mỗi đêm 2h:  0 2 * * * /opt/ocop/scripts/deploy/sao-luu.sh
# Nên chép thư mục backups/ sang nơi khác (ngoài máy chủ).
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/../.."
ENV_FILE="${ENV_FILE:-.env.production}"
KEEP="${KEEP:-14}"
COMPOSE=(docker compose --env-file "$ENV_FILE" -f docker-compose.prod.yml)
STAMP="$(date +%Y%m%d-%H%M%S)"
mkdir -p backups

"${COMPOSE[@]}" exec -T postgres sh -c 'pg_dump -Fc -U "$POSTGRES_USER" "$POSTGRES_DB"' > "backups/db-$STAMP.dump"
"${COMPOSE[@]}" exec -T backend tar -C /app/uploads -czf - . > "backups/uploads-$STAMP.tar.gz"
echo "Đã sao lưu: backups/db-$STAMP.dump, backups/uploads-$STAMP.tar.gz"

# Xóa bản cũ, chỉ giữ KEEP bản mới nhất mỗi loại.
for prefix in db uploads; do
  ls -1t backups/"$prefix"-* 2>/dev/null | tail -n +"$((KEEP + 1))" | xargs -r rm -f --
done
