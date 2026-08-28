# Cổng thông tin OCOP và du lịch nông nghiệp Lâm Đồng

Dự án nhóm xây dựng cổng thông tin quảng bá sản phẩm OCOP, điểm du lịch nông
nghiệp và bản đồ số tỉnh Lâm Đồng.

## Công nghệ chính

- Backend: FastAPI và PostgreSQL/PostGIS.
- Frontend: Vue 3, Vue Router, Axios và Bootstrap/CSS.
- Bản đồ: Leaflet, GeoJSON và OSRM thông qua backend.

## Trạng thái triển khai

Nhánh `main` được xây dựng tuần tự theo các commit nhỏ. Bản backend đầy đủ trước
khi tái cấu trúc được lưu tại nhánh
`codex/archive-working-backend-2026-08-21` để tham khảo, không merge nguyên nhánh
archive vào `main`.

## Thiết lập môi trường

1. Sao chép `.env.example` thành `.env`.
2. Thay tất cả giá trị `change-me` bằng thông tin chỉ dùng trên máy cá nhân.
3. Không commit `.env` hoặc Firebase service account.

Máy phát triển chỉ cần Git và Docker Desktop. Python, Node.js, npm và toàn bộ
dependency của dự án được cài trong Docker image.

Cấu hình Compose hiện tại dành cho phát triển local, có hot reload và Vite dev
server; không dùng trực tiếp cấu hình này để triển khai production.

Khởi động toàn bộ PostgreSQL/PostGIS, pgAdmin, FastAPI và Vue/Vite:

```powershell
docker compose build
docker compose up -d
docker compose ps
```

Các địa chỉ phát triển:

- Frontend: `http://localhost:5173`.
- Backend: `http://localhost:8000`.
- Health check: `http://localhost:8000/health`.
- Swagger: `http://localhost:8000/docs`.
- pgAdmin: `http://localhost:5050`.

Xem log theo service:

```powershell
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f postgres
```

Backend và frontend đều mount source code từ máy vào container để hỗ trợ hot
reload. Dependency frontend nằm trong volume `frontend_node_modules`, không tạo
`node_modules` trên máy host. Docker Compose tự tạo `DATABASE_URL` từ các biến
`POSTGRES_*` và sử dụng hostname nội bộ `postgres`.

Khi volume PostgreSQL còn trống, Docker tự chạy `database/schema.sql` rồi
`database/seed_dev.sql`. Các file trong `docker-entrypoint-initdb.d` không chạy
lại với volume đã có dữ liệu. Không xóa volume chỉ để nạp lại schema nếu chưa
sao lưu dữ liệu cần giữ.

## Kiểm thử trong Docker

Backend:

```powershell
docker compose exec backend python -m pytest -q
```

Frontend:

```powershell
docker compose exec frontend npm run type-check
docker compose exec frontend npm run build
```

## Cài thêm dependency

Backend: thêm package có phiên bản cố định vào `backend/requirements.txt`, sau
đó build lại service:

```powershell
docker compose build backend
docker compose up -d backend
```

Frontend: cài package bên trong container để đồng thời cập nhật `package.json`
và `package-lock.json` trên source được mount:

```powershell
docker compose exec frontend npm install <ten-package>
docker compose build frontend
docker compose up -d frontend
```

Sau khi `git pull`, nếu `frontend/package-lock.json` thay đổi, đồng bộ lại
volume thư viện rồi khởi động frontend:

```powershell
docker compose run --rm --no-deps frontend npm ci
docker compose up -d frontend
```

Không cài dependency thủ công trên máy host hoặc chỉ cài tạm trong container mà
không cập nhật file lock.

## Dừng môi trường

```powershell
docker compose down
```

Lệnh trên giữ volume PostgreSQL. Không dùng `docker compose down -v` nếu chưa
chủ động sao lưu và xác nhận có thể xóa toàn bộ dữ liệu local.

## Tài liệu nền

- Schema PostgreSQL/PostGIS: `database/schema.sql`.
- ERD: `database/ERD.md`.
- Hợp đồng REST API dự kiến: `docs/API.md`.
- Postman collection: `docs/postman/OCOP-Lam-Dong.postman_collection.json`.
- Hướng dẫn chạy và kế hoạch nhóm: `docs/HUONG_DAN_CHAY_VA_KE_HOACH_NHOM_OCOP_LAM_DONG.docx`.
