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

Khởi động PostgreSQL/PostGIS và pgAdmin:

```powershell
docker compose up -d postgres pgadmin
```

## Backend tối thiểu

Từ thư mục `backend`:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Health check: `http://localhost:8000/health`.

Chạy kiểm thử:

```powershell
pytest -q
```

## Tài liệu nền

- Schema PostgreSQL/PostGIS: `database/schema.sql`.
- ERD: `database/ERD.md`.
- Hợp đồng REST API dự kiến: `docs/API.md`.
- Postman collection: `docs/postman/OCOP-Lam-Dong.postman_collection.json`.
