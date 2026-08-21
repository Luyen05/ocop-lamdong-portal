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

