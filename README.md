# Cổng thông tin OCOP và du lịch nông nghiệp Lâm Đồng

Dự án nhóm xây dựng cổng thông tin quảng bá sản phẩm OCOP, điểm du lịch nông
nghiệp và bản đồ số tỉnh Lâm Đồng.

## Công nghệ chính

- Backend: FastAPI và PostgreSQL/PostGIS.
- Frontend: Vue 3, Vue Router, Axios và Bootstrap/CSS.
- Bản đồ: Leaflet, GeoJSON và OSRM thông qua backend.

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

Các API đầu tiên:

- `GET /health`: kiểm tra tiến trình backend.
- `GET /api/v1/health/database`: kiểm tra kết nối PostgreSQL.
- `GET /api/v1/categories`: danh sách danh mục, hỗ trợ `page`, `page_size`, `search`, `sort`.
- `GET /api/v1/categories/{slug}`: chi tiết một danh mục.
- `GET /api/v1/products`: danh sách sản phẩm đã duyệt, hỗ trợ tìm kiếm, lọc và phân trang.
- `GET /api/v1/products/{slug}`: chi tiết sản phẩm đã duyệt.
- `POST /api/v1/auth/register`: đăng ký tài khoản với role `user`.
- `POST /api/v1/auth/login`: đăng nhập bằng JSON và nhận JWT access token.
- `GET /api/v1/auth/me`: xem tài khoản hiện tại bằng Bearer token.
- `PATCH /api/v1/auth/me`: cập nhật họ tên, số điện thoại hoặc ảnh đại diện.
- `POST /api/v1/subject-applications`: người dùng gửi hồ sơ đăng ký chủ thể.
- `GET/PUT /api/v1/subject-applications/me`: xem hoặc gửi lại hồ sơ của mình.
- `GET /api/v1/admin/subject-applications`: admin tìm kiếm và lọc hồ sơ.
- `PATCH /api/v1/admin/subject-applications/{id}/moderation`: admin duyệt hoặc từ chối.

JWT access token mặc định có hiệu lực 60 phút. Tạo `JWT_SECRET_KEY` riêng cho
mỗi môi trường, dài tối thiểu 32 ký tự; không commit khóa thật lên Git.

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

Để nạp bổ sung dữ liệu mẫu vào volume đang có mà không xóa dữ liệu, chạy:

```powershell
docker compose exec postgres sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /docker-entrypoint-initdb.d/002-seed-dev.sql'
```

Seed có tính lặp lại an toàn: chạy nhiều lần không tạo trùng danh mục, chủ thể
hoặc sản phẩm. Tài khoản gắn với dữ liệu mẫu bị khóa và không dùng để đăng nhập.

Sau khi cập nhật mã nguồn có migration mới, áp dụng lần lượt các file chưa chạy
trong `database/migrations`. Ví dụ với migration hồ sơ chủ thể:

```powershell
Get-Content .\database\migrations\002_subject_moderation.sql -Raw | docker compose exec -T postgres sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

Có thể mở cùng file trong Query Tool của pgAdmin và chạy một lần. Không xóa
volume PostgreSQL chỉ để áp dụng migration.

## Kiểm tra luồng đăng ký chủ thể

1. Đăng nhập bằng tài khoản `user`, mở `http://localhost:5173/dang-ky-chu-the`
   và gửi hồ sơ.
2. Đăng nhập bằng tài khoản `admin`, mở
   `http://localhost:5173/quan-tri/ho-so-chu-the`.
3. Duyệt hồ sơ để cấp role `subject`, hoặc từ chối kèm lý do để người dùng sửa
   và gửi lại.

Backend kiểm tra role trong database tại thời điểm gọi API. Việc sửa role trong
JWT hoặc tự hiện nút quản trị trên frontend không làm tăng quyền tài khoản.

## Kiểm tra nhanh module sản phẩm

Sau khi backend và frontend đã chạy, mở các địa chỉ:

- Danh sách sản phẩm: `http://localhost:5173/san-pham`.
- Chi tiết dữ liệu mẫu: `http://localhost:5173/san-pham/ca-phe-arabica-cau-dat-demo`.
- API danh sách: `http://localhost:8000/api/v1/products`.
- API chi tiết: `http://localhost:8000/api/v1/products/ca-phe-arabica-cau-dat-demo`.

Ví dụ lọc sản phẩm 5 sao thuộc danh mục đồ uống tại Đà Lạt:

```text
http://localhost:8000/api/v1/products?category=do-uong&star=5&district=Đà%20Lạt
```

API công khai không trả sản phẩm `pending`, `rejected` hoặc sản phẩm thuộc chủ
thể chưa được duyệt.

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
