#!/usr/bin/env bash
# Build và khởi động lại bản chạy thật trên máy chủ. Chạy trong thư mục gốc của repo trên máy chủ.
# Cần file .env.production (mẫu: .env.production.example). Không xóa volume (giữ database và ảnh).
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/../.."
ENV_FILE="${ENV_FILE:-.env.production}"
COMPOSE=(docker compose --env-file "$ENV_FILE" -f docker-compose.prod.yml)

[ -f "$ENV_FILE" ] || { echo "Thiếu $ENV_FILE (sao chép từ .env.production.example rồi điền)"; exit 1; }

echo "==> Sao lưu database trước khi cập nhật"
scripts/deploy/sao-luu.sh || echo "Bỏ qua sao lưu (database chưa chạy?)"

echo "==> Build và khởi động"
"${COMPOSE[@]}" up -d --build --remove-orphans

echo "==> Chờ website phản hồi"
PORT="$(grep -E '^WEB_PORT=' "$ENV_FILE" | cut -d= -f2 || true)"
for _ in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1:${PORT:-80}/api/v1/products" >/dev/null 2>&1; then
    echo "Triển khai xong."
    exit 0
  fi
  sleep 4
done
echo "Website chưa phản hồi. Xem nhật ký: ${COMPOSE[*]} logs --tail=100"
exit 1
